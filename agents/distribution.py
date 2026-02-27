import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import List

from .content import DraftArticle

# Resolve base URL once at import time.  Set NEURALSTACK_BASE_URL in your
# environment or GitHub Actions secrets; falls back to a sensible default.
BASE_URL = os.getenv(
    "NEURALSTACK_BASE_URL",
    "https://christosgalaios.github.io/NeuralStack-Content",
)

# Optional: set NEURALSTACK_ADSENSE_ID to inject AdSense auto-ads.
# Leave unset to skip ad injection entirely.
ADSENSE_ID = os.getenv("NEURALSTACK_ADSENSE_ID", "")


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

        body = self._md_links_to_html(draft.content)
        canonical = f"{BASE_URL}/articles/{filename}"

        adsense_tag = ""
        if ADSENSE_ID:
            adsense_tag = (
                f'  <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_ID}"'
                f' crossorigin="anonymous"></script>\n'
            )

        html = (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '  <meta charset="utf-8" />\n'
            '  <meta name="viewport" content="width=device-width, initial-scale=1" />\n'
            f"  <title>{draft.title}</title>\n"
            f'  <meta name="description" content="In-depth technical guide: {draft.title}. Practical trade-offs, implementation patterns, and recommendations for production engineers." />\n'
            f'  <link rel="canonical" href="{canonical}" />\n'
            '  <meta name="robots" content="index, follow" />\n'
            '  <link rel="stylesheet" href="../assets/style.css" />\n'
            f"{adsense_tag}"
            "</head>\n"
            "<body>\n"
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
                    "date": datetime.utcfromtimestamp(file.stat().st_mtime).isoformat() + "Z",
                }
            )
        return posts

    def _update_index(self, posts: List[dict]) -> None:
        index = self.root_dir / "index.html"
        items = []
        for post in sorted(posts, key=lambda p: p["date"], reverse=True):
            items.append(
                f'    <li><a href="{post["path"]}">{post["title"]}</a>'
                f' <span style="font-size: 0.8em; color: #666;">(updated {post["date"]})</span></li>'
            )
        items_html = "\n".join(items) if items else '    <li>No articles have been published yet. Check back tomorrow.</li>'

        html = (
            "<!DOCTYPE html>\n"
            "<html>\n"
            "<head>\n"
            "  <meta charset=\"utf-8\" />\n"
            "  <title>Technical Knowledge Base</title>\n"
            "  <link rel=\"stylesheet\" href=\"assets/style.css\" />\n"
            "</head>\n"
            "<body>\n"
            "  <h1>Technical Knowledge Base</h1>\n"
            "  <p>In-depth technical guides and compatibility documentation.</p>\n"
            "  <h2>Articles</h2>\n"
            "  <ul>\n"
            f"{items_html}\n"
            "  </ul>\n"
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
                f"    <lastmod>{datetime.utcnow().date().isoformat()}</lastmod>\n"
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

