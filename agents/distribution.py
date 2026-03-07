import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict

from .content import DraftArticle

# Words to ignore when computing keyword overlap for related-article matching.
_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "of", "for", "in", "on", "to", "with",
    "vs", "is", "it", "at", "by", "up", "from", "how", "step", "guide",
    "detailed", "comparison", "review", "inside", "using", "best", "which",
    "should", "you", "use", "your", "what", "why", "when", "do",
})

# Resolve base URL once at import time.  Set NEURALSTACK_BASE_URL in your
# environment or GitHub Actions secrets; falls back to a sensible default.
BASE_URL = os.getenv(
    "NEURALSTACK_BASE_URL",
    "https://christosgalaios.github.io/NeuralStack-Content",
)

# Optional: set NEURALSTACK_ADSENSE_ID to inject AdSense auto-ads.
# Leave unset to skip ad injection entirely.
ADSENSE_ID = os.getenv("NEURALSTACK_ADSENSE_ID", "")


# ---------------------------------------------------------------------------
# Markdown → HTML converter (zero external dependencies)
# ---------------------------------------------------------------------------

def _inline_md(text: str) -> str:
    """Convert inline markdown to HTML (bold, italic, code, links)."""
    # Bold (must precede italic)
    text = re.sub(r'\*\*([^*\n]+)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*([^*\n]+)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', text)
    # Markdown links → HTML anchors with affiliate rel
    text = re.sub(
        r'\[([^\]]+)\]\((https?://[^\)]+)\)',
        r'<a href="\2" target="_blank" rel="noopener sponsored">\1</a>',
        text,
    )
    return text


def _md_to_html(text: str) -> str:
    """
    Convert a markdown document to HTML.

    Handles: headings (h1-h3), bold, italic, inline code, fenced code blocks,
    pipe tables, unordered lists, links, and paragraphs.

    If the content already looks like HTML (first non-empty line starts with '<')
    it is returned unchanged so that legacy HTML drafts continue to work.
    """
    first_line = text.lstrip().split('\n')[0].strip()
    if first_line.startswith('<'):
        return text  # already HTML — don't double-convert

    lines = text.split('\n')
    output: List[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # ── Fenced code blocks ────────────────────────────────────────────
        if line.strip().startswith('```'):
            lang = line.strip()[3:].strip() or 'text'
            code_lines: List[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith('```'):
                code_lines.append(lines[i])
                i += 1
            code = '\n'.join(code_lines)
            code = code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            output.append(f'<pre><code class="language-{lang}">{code}</code></pre>')
            i += 1
            continue

        # ── Pipe tables ───────────────────────────────────────────────────
        if line.strip().startswith('|') and '|' in line:
            table_lines: List[str] = []
            while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip():
                table_lines.append(lines[i])
                i += 1
            rows = []
            for tl in table_lines:
                # Skip separator rows like |---|---|
                if re.match(r'^\|[\s\-|:]+\|$', tl.strip()):
                    continue
                cells = [c.strip() for c in tl.strip().strip('|').split('|')]
                rows.append(cells)
            if rows:
                parts = ['<table>',
                         '<thead><tr>' + ''.join(f'<th>{_inline_md(c)}</th>' for c in rows[0]) + '</tr></thead>']
                if len(rows) > 1:
                    parts.append('<tbody>')
                    for row in rows[1:]:
                        parts.append('<tr>' + ''.join(f'<td>{_inline_md(c)}</td>' for c in row) + '</tr>')
                    parts.append('</tbody>')
                parts.append('</table>')
                output.append('\n'.join(parts))
            continue

        # ── ATX headings ──────────────────────────────────────────────────
        m = re.match(r'^(#{1,3})\s+(.+)$', line)
        if m:
            level = len(m.group(1))
            content = _inline_md(m.group(2))
            output.append(f'<h{level}>{content}</h{level}>')
            i += 1
            continue

        # ── Unordered lists ───────────────────────────────────────────────
        if re.match(r'^[-*]\s+', line):
            items: List[str] = []
            while i < len(lines) and re.match(r'^[-*]\s+', lines[i]):
                items.append(f'<li>{_inline_md(lines[i][2:].strip())}</li>')
                i += 1
            output.append('<ul>\n' + '\n'.join(items) + '\n</ul>')
            continue

        # ── Blank line ────────────────────────────────────────────────────
        if not line.strip():
            output.append('')
            i += 1
            continue

        # ── Paragraph (accumulate until a block boundary) ─────────────────
        para: List[str] = []
        while i < len(lines):
            ln = lines[i]
            if (not ln.strip()
                    or re.match(r'^#{1,3}\s', ln)
                    or ln.strip().startswith('|')
                    or ln.strip().startswith('```')
                    or re.match(r'^[-*]\s+', ln)):
                break
            para.append(ln)
            i += 1
        if para:
            output.append(f'<p>{_inline_md(" ".join(para))}</p>')

    return '\n'.join(output)


def _title_tokens(title: str) -> frozenset:
    """Lower-case, stop-word-filtered word set for a title string."""
    return frozenset(
        w for w in re.sub(r"[^a-z0-9 ]", " ", title.lower()).split()
        if w not in _STOP_WORDS and len(w) > 2
    )


def _related_articles_html(
    current_slug: str,
    current_title: str,
    articles_dir: Path,
    base_url: str,
    max_links: int = 4,
) -> str:
    """
    Scan published articles and return an HTML 'Related articles' section
    containing up to `max_links` links to articles with the highest keyword
    overlap with the current article's title.

    Returns an empty string if no related articles are found.
    """
    if not articles_dir.exists():
        return ""

    current_tokens = _title_tokens(current_title)
    if not current_tokens:
        return ""

    scored: List[Dict] = []
    for html_file in articles_dir.glob("*.html"):
        if html_file.stem == current_slug:
            continue
        # Extract title from <title> tag
        text = html_file.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r"<title>(.+?)</title>", text)
        if not m:
            continue
        title = m.group(1).strip()
        overlap = len(current_tokens & _title_tokens(title))
        if overlap > 0:
            scored.append({
                "title": title,
                "path": f"articles/{html_file.name}",
                "overlap": overlap,
            })

    if not scored:
        return ""

    top = sorted(scored, key=lambda x: x["overlap"], reverse=True)[:max_links]
    items = "\n".join(
        f'    <li><a href="{base_url}/{r["path"]}">{r["title"]}</a></li>'
        for r in top
    )
    return (
        '\n<section class="related-articles">\n'
        "  <h2>Related articles</h2>\n"
        f"  <ul>\n{items}\n  </ul>\n"
        "</section>\n"
    )


class DistributionAgent:
    """
    Responsible for publishing validated articles to the static site,
    and keeping supporting artefacts like sitemap and RSS feed up to date.
    """

    def __init__(self, data_dir: Path, root_dir: Path, articles_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.root_dir = Path(root_dir)
        self.articles_dir = Path(articles_dir)

    @staticmethod
    def _md_links_to_html(text: str) -> str:
        """Convert markdown-style [text](url) links to <a> tags with rel=noopener."""
        return re.sub(
            r'\[([^\]]+)\]\((https?://[^\)]+)\)',
            r'<a href="\2" target="_blank" rel="noopener sponsored">\1</a>',
            text,
        )

    def _publish_article(self, draft: DraftArticle) -> Path:
        self.articles_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{draft.slug}.html"
        path = self.articles_dir / filename

        body = _md_to_html(draft.content)
        related_html = _related_articles_html(
            draft.slug, draft.title, self.articles_dir, BASE_URL
        )
        body = body + related_html
        canonical = f"{BASE_URL}/articles/{filename}"
        description = f"In-depth technical guide: {draft.title}. Practical trade-offs, implementation patterns, and recommendations for production engineers."

        adsense_tag = ""
        if ADSENSE_ID:
            adsense_tag = (
                f'  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_ID}"'
                f' crossorigin="anonymous"></script>\n'
            )

        date_published = draft.created_at[:10]
        date_modified = datetime.now(timezone.utc).date().isoformat()

        jsonld = json.dumps({
            "@context": "https://schema.org",
            "@type": "TechArticle",
            "headline": draft.title,
            "description": description,
            "datePublished": date_published,
            "dateModified": date_modified,
            "author": {"@type": "Organization", "name": "NeuralStack"},
            "publisher": {
                "@type": "Organization",
                "name": "NeuralStack",
                "url": BASE_URL,
            },
            "mainEntityOfPage": {"@type": "WebPage", "@id": canonical},
        }, indent=2)

        html = (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '  <meta charset="utf-8" />\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1" />\n'
            f"  <title>{draft.title}</title>\n"
            f'  <meta name="description" content="{description}" />\n'
            f'  <meta property="og:title" content="{draft.title}" />\n'
            f'  <meta property="og:description" content="{description}" />\n'
            '  <meta property="og:type" content="article" />\n'
            f'  <meta property="og:url" content="{canonical}" />\n'
            f'  <link rel="canonical" href="{canonical}" />\n'
            '  <meta name="robots" content="index, follow" />\n'
            f'  <link rel="alternate" type="application/rss+xml" title="NeuralStack RSS" href="{BASE_URL}/feed.xml" />\n'
            '  <link rel="stylesheet" href="../assets/style.css" />\n'
            f'  <script type="application/ld+json">\n{jsonld}\n  </script>\n'
            f"{adsense_tag}"
            "</head>\n"
            "<body>\n"
            f'  <nav class="site-nav"><a href="{BASE_URL}/">&#8592; All articles</a></nav>\n'
            f"<article>\n{body}\n</article>\n"
            "</body>\n"
            "</html>\n"
        )

        path.write_text(html, encoding="utf-8")
        return path

    def _load_posts_metadata(self) -> List[dict]:
        posts: List[dict] = []
        if not self.articles_dir.exists():
            return posts
        for file in sorted(self.articles_dir.glob("*.html")):
            text = file.read_text(encoding="utf-8")
            title = file.stem
            # Try to extract a <title> if present.
            marker_start = "<title>"
            marker_end = "</title>"
            if marker_start in text and marker_end in text:
                start_idx = text.index(marker_start) + len(marker_start)
                end_idx = text.index(marker_end, start_idx)
                title = text[start_idx:end_idx].strip()
            posts.append(
                {
                    "title": title,
                    "slug": file.stem,
                    "path": f"articles/{file.name}",
                    "date": datetime.fromtimestamp(
                        file.stat().st_mtime, tz=timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                }
            )
        return posts

    def _update_index(self, posts: List[dict]) -> None:
        index = self.root_dir / "index.html"
        article_count = len(posts)

        if posts:
            items = []
            for post in sorted(posts, key=lambda p: p["date"], reverse=True):
                date_short = post["date"][:10]
                items.append(
                    f'    <li class="article-item">'
                    f'<a href="{post["path"]}">{post["title"]}</a>'
                    f' <span class="article-date">{date_short}</span>'
                    f'</li>'
                )
            items_html = "\n".join(items)
        else:
            items_html = '    <li>No articles have been published yet. Check back tomorrow.</li>'

        description = (
            f"Practical technical guides for engineers who ship. "
            f"{article_count} in-depth articles on developer tooling, compatibility, "
            f"and modern engineering workflows — updated daily."
        )

        html = (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '  <meta charset="utf-8" />\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1" />\n'
            '  <title>NeuralStack — Technical Guides for Engineers</title>\n'
            f'  <meta name="description" content="{description}" />\n'
            f'  <meta property="og:title" content="NeuralStack — Technical Guides for Engineers" />\n'
            f'  <meta property="og:description" content="{description}" />\n'
            '  <meta property="og:type" content="website" />\n'
            f'  <meta property="og:url" content="{BASE_URL}/" />\n'
            f'  <link rel="canonical" href="{BASE_URL}/" />\n'
            '  <meta name="robots" content="index, follow" />\n'
            f'  <link rel="alternate" type="application/rss+xml" title="NeuralStack RSS" href="{BASE_URL}/feed.xml" />\n'
            '  <link rel="stylesheet" href="assets/style.css" />\n'
            "</head>\n"
            "<body>\n"
            '  <header class="site-header">\n'
            '    <h1>NeuralStack</h1>\n'
            f'    <p class="tagline">Practical technical guides for engineers who ship &mdash; {article_count} articles, updated daily.</p>\n'
            '  </header>\n'
            '  <main>\n'
            '    <h2>Latest Articles</h2>\n'
            '    <ul class="article-list">\n'
            f"{items_html}\n"
            '    </ul>\n'
            '  </main>\n'
            '  <footer class="site-footer">\n'
            f'    <p><a href="{BASE_URL}/feed.xml">RSS feed</a> &bull; Updated daily by the autonomous pipeline.</p>\n'
            '  </footer>\n'
            "</body>\n"
            "</html>\n"
        )
        index.write_text(html, encoding="utf-8")

    def _update_sitemap(self, posts: List[dict]) -> None:
        sitemap = self.root_dir / "sitemap.xml"
        base_url = BASE_URL
        urls = [f"{base_url}/"]
        urls += [f"{base_url}/{p['path']}" for p in posts]

        entries = []
        for url in urls:
            entries.append(
                "  <url>\n"
                f"    <loc>{url}</loc>\n"
                f"    <lastmod>{datetime.now(timezone.utc).date().isoformat()}</lastmod>\n"
                "    <changefreq>daily</changefreq>\n"
                "    <priority>0.7</priority>\n"
                "  </url>"
            )

        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + "\n".join(entries)
            + "\n</urlset>\n"
        )
        sitemap.write_text(xml, encoding="utf-8")

    def _update_rss(self, posts: List[dict]) -> None:
        feed = self.root_dir / "feed.xml"
        base_url = BASE_URL
        items = []
        for post in sorted(posts, key=lambda p: p["date"], reverse=True):
            items.append(
                "  <item>\n"
                f"    <title>{post['title']}</title>\n"
                f"    <link>{base_url}/{post['path']}</link>\n"
                f"    <guid>{base_url}/{post['path']}</guid>\n"
                f"    <pubDate>{post['date']}</pubDate>\n"
                "    <description>Long-form technical guide generated by the autonomous pipeline.</description>\n"
                "  </item>"
            )

        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            "<rss version=\"2.0\">\n"
            " <channel>\n"
            "  <title>NeuralStack Autonomous Tech Insights</title>\n"
            f"  <link>{base_url}/</link>\n"
            "  <description>Daily long-form content on developer tooling and compatibility.</description>\n"
            + "\n".join(items)
            + "\n </channel>\n</rss>\n"
        )
        feed.write_text(xml, encoding="utf-8")

    def _update_performance_summary(self, published_paths: List[Path]) -> None:
        perf_file = self.data_dir / "performance.json"
        if not perf_file.exists():
            return
        try:
            data = json.loads(perf_file.read_text(encoding="utf-8"))
        except Exception:
            return
        data.setdefault("latest_published_files", [])
        data["latest_published_files"] = [str(p) for p in published_paths]
        perf_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _prepare_video_script_stub(self, draft: DraftArticle, output_dir: Path) -> None:
        """
        Optional: create a short-form video script outline that can later be used
        to record YouTube Shorts or similar content.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{draft.slug}-short-script.md"
        outline = (
            f"# Short video script for: {draft.title}\n\n"
            "## Hook (3–5 seconds)\n"
            "- State the core pain point in a single sharp sentence.\n\n"
            "## Context (5–10 seconds)\n"
            "- Mention who this is for and when it matters.\n\n"
            "## Key idea (10–20 seconds)\n"
            "- Summarise one concrete insight from the article.\n\n"
            "## Call to action (3–5 seconds)\n"
            "- Invite viewers to read the full guide on the site.\n"
        )
        path.write_text(outline, encoding="utf-8")

    def run(self, approved_drafts: List[DraftArticle]) -> List[Path]:
        published_paths: List[Path] = []
        for draft in approved_drafts:
            post_path = self._publish_article(draft)
            published_paths.append(post_path)
            self._prepare_video_script_stub(draft, self.data_dir / "video_scripts")

        posts_meta = self._load_posts_metadata()
        self._update_index(posts_meta)
        self._update_sitemap(posts_meta)
        self._update_rss(posts_meta)
        self._update_performance_summary(published_paths)
        return published_paths


__all__ = ["DistributionAgent"]
