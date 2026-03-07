import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Tuple

from .content import DraftArticle

# Words to ignore when computing keyword overlap for related-article matching.
_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "of", "for", "in", "on", "to", "with",
    "vs", "is", "it", "at", "by", "up", "from", "how", "step", "guide",
    "detailed", "comparison", "review", "inside", "using", "best", "which",
    "should", "you", "use", "your", "what", "why", "when", "do",
})

# Resolve base URL once at import time.
BASE_URL = os.getenv(
    "NEURALSTACK_BASE_URL",
    "https://christosgalaios.github.io/NeuralStack-Content",
)

# Optional: set NEURALSTACK_ADSENSE_ID to inject AdSense auto-ads.
ADSENSE_ID = os.getenv("NEURALSTACK_ADSENSE_ID", "")

# Affiliate configuration
AFF1_NAME = os.getenv("NEURALSTACK_AFF1_NAME", "Cursor IDE")
AFF1_URL = os.getenv("NEURALSTACK_AFF1_URL", "https://www.cursor.com")
AFF2_NAME = os.getenv("NEURALSTACK_AFF2_NAME", "Datadog")
AFF2_URL = os.getenv("NEURALSTACK_AFF2_URL", "https://www.datadoghq.com")
AFF3_NAME = os.getenv("NEURALSTACK_AFF3_NAME", "Railway")
AFF3_URL = os.getenv("NEURALSTACK_AFF3_URL", "https://railway.app")

_TOOL_DESCRIPTIONS = {
    "Cursor IDE": "AI-first code editor that accelerates your workflow with intelligent completions and inline chat.",
    "Datadog": "Full-stack observability platform for monitoring your cloud infrastructure and applications.",
    "Railway": "Deploy code from GitHub in seconds \u2014 simple, powerful cloud hosting for developers.",
}

# ---------------------------------------------------------------------------
# Google Fonts + Favicon (shared across all pages)
# ---------------------------------------------------------------------------

_FONTS_LINK = (
    '  <link rel="preconnect" href="https://fonts.googleapis.com" />\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
    '  <link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1'
    '&amp;family=Plus+Jakarta+Sans:ital,wght@0,300..800;1,300..800'
    '&amp;family=JetBrains+Mono:wght@400;500&amp;display=swap" rel="stylesheet" />\n'
)

_FAVICON = (
    "  <link rel=\"icon\" href=\"data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E"
    "%3Crect width='100' height='100' rx='16' fill='%231A1615'/%3E"
    "%3Ctext x='50' y='68' font-family='serif' font-size='60' font-weight='bold' "
    "fill='%23F59E0B' text-anchor='middle'%3EN%3C/text%3E%3C/svg%3E\" />\n"
)


# ---------------------------------------------------------------------------
# Markdown → HTML converter (zero external dependencies)
# ---------------------------------------------------------------------------

def _inline_md(text: str) -> str:
    """Convert inline markdown to HTML (bold, italic, code, links)."""
    text = re.sub(r'\*\*([^*\n]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*([^*\n]+)\*', r'<em>\1</em>', text)
    text = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', text)
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


# ---------------------------------------------------------------------------
# Helpers: strip tags, heading IDs, TOC, category inference, tool callouts
# ---------------------------------------------------------------------------

def _strip_tags(html: str) -> str:
    """Remove HTML tags, keeping text content."""
    return re.sub(r'<[^>]+>', '', html)


def _add_heading_ids_and_toc(html_body: str) -> Tuple[str, str]:
    """Add id attributes to h2 tags and generate a table of contents.

    Returns (modified_html, toc_html). toc_html is empty if fewer than
    2 headings are found.
    """
    headings = re.findall(r'<h2>(.*?)</h2>', html_body)
    if len(headings) < 2:
        return html_body, ""

    toc_items: List[str] = []
    seen_slugs: set = set()

    for heading_html in headings:
        plain = _strip_tags(heading_html)
        slug = re.sub(r'[^a-z0-9]+', '-', plain.lower().strip()).strip('-')
        base_slug = slug
        counter = 1
        while slug in seen_slugs:
            slug = f"{base_slug}-{counter}"
            counter += 1
        seen_slugs.add(slug)

        html_body = html_body.replace(
            f'<h2>{heading_html}</h2>',
            f'<h2 id="{slug}">{heading_html}</h2>',
            1,
        )
        toc_items.append(f'    <li><a href="#{slug}">{plain}</a></li>')

    toc_html = (
        '<details class="toc" open>\n'
        '  <summary class="toc-title">In this article</summary>\n'
        '  <ol>\n'
        + '\n'.join(toc_items) + '\n'
        '  </ol>\n'
        '</details>\n'
    )
    return html_body, toc_html


def _infer_category(title: str) -> Tuple[str, str]:
    """Return (display_name, css_class) for the article category."""
    t = title.lower()
    if any(x in t for x in [' vs ', ' versus ', 'comparison', 'compared', 'ranked']):
        return ('Comparison', 'comparison')
    if 'compatibility' in t:
        return ('Compatibility', 'compatibility')
    if any(x in t for x in ['tutorial', 'how to', 'getting started', 'step-by-step']):
        return ('Tutorial', 'tutorial')
    if any(x in t for x in ['review', 'hands-on', 'deep dive']):
        return ('Review', 'review')
    if any(x in t for x in ['translated', 'summary', 'global engineers']):
        return ('News', 'news')
    return ('Guide', 'guide')


def _tool_callout_html(slug: str) -> str:
    """Generate a tool recommendation callout, rotating through affiliates."""
    affiliates = [
        (AFF1_NAME, AFF1_URL),
        (AFF2_NAME, AFF2_URL),
        (AFF3_NAME, AFF3_URL),
    ]
    idx = abs(hash(slug)) % len(affiliates)
    name, url = affiliates[idx]
    desc = _TOOL_DESCRIPTIONS.get(name, f"Check out {name} for your next project.")

    return (
        '<aside class="tool-callout">\n'
        '  <span class="tool-callout-badge">Recommended</span>\n'
        f'  <h4>{name}</h4>\n'
        f'  <p>{desc}</p>\n'
        f'  <a href="{url}" class="tool-callout-cta" target="_blank" '
        f'rel="noopener sponsored">Try {name} &rarr;</a>\n'
        '</aside>\n'
    )


def _tools_section_html() -> str:
    """Generate the recommended tools section for the index page."""
    affiliates = [
        (AFF1_NAME, AFF1_URL),
        (AFF2_NAME, AFF2_URL),
        (AFF3_NAME, AFF3_URL),
    ]
    cards: List[str] = []
    for name, url in affiliates:
        desc = _TOOL_DESCRIPTIONS.get(name, "")
        cards.append(
            f'        <a href="{url}" class="tool-card" target="_blank" rel="noopener sponsored">\n'
            f'          <span class="tool-card-name">{name}</span>\n'
            f'          <span class="tool-card-desc">{desc}</span>\n'
            f'          <span class="tool-card-cta">Try it free &rarr;</span>\n'
            f'        </a>'
        )

    return (
        '    <section class="tools-section">\n'
        '      <h2 class="section-heading">Recommended Tools</h2>\n'
        '      <div class="tools-grid">\n'
        + '\n'.join(cards) + '\n'
        '      </div>\n'
        '    </section>\n'
    )


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

        # Add heading IDs and generate table of contents
        body, toc_html = _add_heading_ids_and_toc(body)

        related_html = _related_articles_html(
            draft.slug, draft.title, self.articles_dir, BASE_URL
        )

        canonical = f"{BASE_URL}/articles/{filename}"
        description = (
            f"In-depth technical guide: {draft.title}. Practical trade-offs, "
            f"implementation patterns, and recommendations for production engineers."
        )

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

        word_count = len(body.split())
        reading_min = max(1, round(word_count / 220))

        cat_name, cat_class = _infer_category(draft.title)

        tool_callout = _tool_callout_html(draft.slug)

        progress_script = (
            "<script>\n"
            "(function(){\n"
            "  var bar=document.querySelector('.reading-progress');\n"
            "  if(!bar)return;\n"
            "  window.addEventListener('scroll',function(){\n"
            "    var h=document.documentElement;\n"
            "    var pct=h.scrollTop/(h.scrollHeight-h.clientHeight)*100;\n"
            "    bar.style.width=Math.min(pct,100)+'%';\n"
            "  });\n"
            "})();\n"
            "</script>\n"
        )

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
            f"{_FONTS_LINK}"
            f"{_FAVICON}"
            '  <link rel="stylesheet" href="../assets/style.css" />\n'
            f'  <script type="application/ld+json">\n{jsonld}\n  </script>\n'
            f"{adsense_tag}"
            "</head>\n"
            "<body>\n"
            '  <div class="reading-progress"></div>\n'
            f'  <nav class="site-nav">'
            f'<a href="{BASE_URL}/">NeuralStack</a>'
            f'<span class="nav-sep">/</span>'
            f'<span class="nav-current">{draft.title}</span>'
            f'</nav>\n'
            "<article>\n"
            '<header class="article-header">\n'
            f'  <span class="category-badge category-{cat_class}">{cat_name}</span>\n'
            f"  <h1>{draft.title}</h1>\n"
            '  <div class="article-meta">\n'
            '    <span>NeuralStack</span>\n'
            '    <span class="article-meta-dot">&#183;</span>\n'
            f'    <span>{date_published}</span>\n'
            '    <span class="article-meta-dot">&#183;</span>\n'
            f'    <span>{reading_min} min read</span>\n'
            '  </div>\n'
            '</header>\n'
            f"{toc_html}"
            f'<div class="article-body">\n{body}\n</div>\n'
            f"{tool_callout}"
            f"{related_html}"
            "</article>\n"
            f"{progress_script}"
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
            description = ""
            # Extract title from <title> tag
            m = re.search(r"<title>(.+?)</title>", text)
            if m:
                title = m.group(1).strip()
            # Extract meta description
            m = re.search(r'<meta name="description" content="([^"]*)"', text)
            if m:
                description = m.group(1).strip()
            posts.append(
                {
                    "title": title,
                    "slug": file.stem,
                    "path": f"articles/{file.name}",
                    "description": description,
                    "date": datetime.fromtimestamp(
                        file.stat().st_mtime, tz=timezone.utc
                    ).isoformat().replace("+00:00", "Z"),
                }
            )
        return posts

    def _update_index(self, posts: List[dict]) -> None:
        index = self.root_dir / "index.html"
        article_count = len(posts)

        # Count unique categories from topic pool for stats display
        categories_count = 0
        topics_file = self.data_dir / "topics.json"
        if topics_file.exists():
            try:
                topics = json.loads(topics_file.read_text(encoding="utf-8"))
                categories_count = len({t.get("category", "") for t in topics if t.get("category")})
            except Exception:
                pass

        description = (
            f"Practical technical guides for engineers who ship. "
            f"{article_count} in-depth articles on developer tooling, compatibility, "
            f"and modern engineering workflows \u2014 updated daily."
        )

        sorted_posts = sorted(posts, key=lambda p: p["date"], reverse=True)
        featured_posts = sorted_posts[:6]
        archive_posts = sorted_posts[6:]

        # Featured cards
        featured_html = ""
        if featured_posts:
            cards: List[str] = []
            for post in featured_posts:
                cat_name, cat_class = _infer_category(post["title"])
                excerpt = post.get("description", "")[:140]
                if len(post.get("description", "")) > 140:
                    excerpt += "..."
                date_short = post["date"][:10]
                cards.append(
                    f'        <article class="article-card">\n'
                    f'          <span class="category-badge category-{cat_class}">{cat_name}</span>\n'
                    f'          <h3 class="article-card-title"><a href="{post["path"]}">{post["title"]}</a></h3>\n'
                    f'          <p class="article-card-excerpt">{excerpt}</p>\n'
                    f'          <div class="article-card-meta"><span class="article-date">{date_short}</span></div>\n'
                    f'        </article>'
                )
            featured_html = '\n'.join(cards)

        # Archive list
        archive_section = ""
        if archive_posts:
            items: List[str] = []
            for post in archive_posts:
                date_short = post["date"][:10]
                items.append(
                    f'        <li class="article-item">'
                    f'<a href="{post["path"]}">{post["title"]}</a>'
                    f' <span class="article-date">{date_short}</span>'
                    f'</li>'
                )
            archive_section = (
                '    <section>\n'
                '      <h2 class="section-heading">All Articles</h2>\n'
                '      <ul class="article-list">\n'
                + '\n'.join(items) + '\n'
                '      </ul>\n'
                '    </section>\n'
            )

        # Tools section
        tools_html = _tools_section_html()

        # No-articles fallback
        if not posts:
            main_content = (
                '    <main>\n'
                '      <h2 class="section-heading">Latest Articles</h2>\n'
                '      <p>No articles have been published yet. Check back tomorrow.</p>\n'
                '    </main>\n'
            )
        else:
            main_content = (
                '    <main>\n'
                '      <section>\n'
                '        <h2 class="section-heading">Latest Articles</h2>\n'
                '        <div class="article-grid">\n'
                f'{featured_html}\n'
                '        </div>\n'
                '      </section>\n'
                f'{tools_html}'
                f'{archive_section}'
                '    </main>\n'
            )

        html = (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '  <meta charset="utf-8" />\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1" />\n'
            '  <title>NeuralStack \u2014 Technical Guides for Engineers</title>\n'
            f'  <meta name="description" content="{description}" />\n'
            f'  <meta property="og:title" content="NeuralStack \u2014 Technical Guides for Engineers" />\n'
            f'  <meta property="og:description" content="{description}" />\n'
            '  <meta property="og:type" content="website" />\n'
            f'  <meta property="og:url" content="{BASE_URL}/" />\n'
            f'  <link rel="canonical" href="{BASE_URL}/" />\n'
            '  <meta name="robots" content="index, follow" />\n'
            f'  <link rel="alternate" type="application/rss+xml" title="NeuralStack RSS" href="{BASE_URL}/feed.xml" />\n'
            f"{_FONTS_LINK}"
            f"{_FAVICON}"
            '  <link rel="stylesheet" href="assets/style.css" />\n'
            "</head>\n"
            "<body>\n"
            '  <header class="site-header">\n'
            '    <div class="site-header-inner">\n'
            '      <h1>Neural<span class="logo-accent">Stack</span></h1>\n'
            f'      <p class="tagline">Practical technical guides for engineers who ship.</p>\n'
            '      <div class="header-stats">\n'
            f'        <div class="stat"><span class="stat-number">{article_count}</span><span class="stat-label">Articles</span></div>\n'
            f'        <div class="stat"><span class="stat-number">{categories_count}</span><span class="stat-label">Categories</span></div>\n'
            '        <div class="stat"><span class="stat-number">Daily</span><span class="stat-label">Updates</span></div>\n'
            '      </div>\n'
            '    </div>\n'
            '  </header>\n'
            '  <div class="content-wrap">\n'
            f'{main_content}'
            '  </div>\n'
            '  <footer class="site-footer">\n'
            '    <div class="site-footer-inner">\n'
            '      <div class="footer-brand">\n'
            '        <p class="footer-logo">Neural<span class="logo-accent">Stack</span></p>\n'
            '        <p class="footer-tagline">Autonomous technical content, published daily.</p>\n'
            '      </div>\n'
            '      <div class="footer-links">\n'
            f'        <a href="{BASE_URL}/feed.xml">RSS Feed</a>\n'
            f'        <a href="{BASE_URL}/sitemap.xml">Sitemap</a>\n'
            '      </div>\n'
            '    </div>\n'
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
        """Create a short-form video script outline."""
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{draft.slug}-short-script.md"
        outline = (
            f"# Short video script for: {draft.title}\n\n"
            "## Hook (3\u20135 seconds)\n"
            "- State the core pain point in a single sharp sentence.\n\n"
            "## Context (5\u201310 seconds)\n"
            "- Mention who this is for and when it matters.\n\n"
            "## Key idea (10\u201320 seconds)\n"
            "- Summarise one concrete insight from the article.\n\n"
            "## Call to action (3\u20135 seconds)\n"
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
