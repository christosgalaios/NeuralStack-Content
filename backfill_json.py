"""One-off script to backfill JSON data files for all existing HTML articles."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from agents.distribution import (
    DistributionAgent, _md_to_html, _add_heading_ids_and_toc,
    _strip_tags, _title_tokens, _infer_category, _TOOL_DESCRIPTIONS,
    BASE_URL, AFF1_NAME, AFF1_URL, AFF2_NAME, AFF2_URL,
)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ARTICLES_DIR = BASE_DIR / "articles"
JSON_DIR = DATA_DIR / "articles"


def backfill():
    JSON_DIR.mkdir(parents=True, exist_ok=True)

    affiliates = [
        (AFF1_NAME, AFF1_URL),
        (AFF2_NAME, AFF2_URL),
    ]

    html_files = sorted(ARTICLES_DIR.glob("*.html"))
    print(f"Found {len(html_files)} articles to backfill.")

    for html_file in html_files:
        slug = html_file.stem
        json_path = JSON_DIR / f"{slug}.json"

        text = html_file.read_text(encoding="utf-8", errors="ignore")

        # Extract title
        title = slug
        m = re.search(r"<title>(.+?)</title>", text)
        if m:
            title = m.group(1).strip()

        # Extract description
        description = ""
        m = re.search(r'<meta name="description" content="([^"]*)"', text)
        if m:
            description = m.group(1).strip()
        if not description:
            description = (
                f"In-depth technical guide: {title}. Practical trade-offs, "
                f"implementation patterns, and recommendations for production engineers."
            )

        # Extract article body HTML
        body_html = ""
        m = re.search(r'<div class="article-body">\n?(.*?)\n?</div>', text, re.DOTALL)
        if m:
            body_html = m.group(1).strip()

        # Extract TOC entries from existing h2 ids
        toc_entries = []
        for h2m in re.finditer(r'<h2 id="([^"]+)">(.+?)</h2>', body_html):
            toc_entries.append({"id": h2m.group(1), "text": _strip_tags(h2m.group(2))})

        # Category
        cat_name, cat_class = _infer_category(title)

        # Dates
        date_published = ""
        m = re.search(r'"datePublished":\s*"([^"]+)"', text)
        if m:
            date_published = m.group(1)[:10]
        if not date_published:
            date_published = datetime.fromtimestamp(
                html_file.stat().st_mtime, tz=timezone.utc
            ).date().isoformat()

        date_modified = datetime.now(timezone.utc).date().isoformat()

        # Word count and reading time
        word_count = len(_strip_tags(body_html).split())
        reading_min = max(1, round(word_count / 220))

        # Affiliate
        idx = abs(hash(slug)) % len(affiliates)
        aff_name, aff_url = affiliates[idx]
        aff_desc = _TOOL_DESCRIPTIONS.get(aff_name, f"Check out {aff_name}.")

        # Related slugs
        related_slugs = []
        current_tokens = _title_tokens(title)
        if current_tokens:
            scored = []
            for other in html_files:
                if other.stem == slug:
                    continue
                other_text = other.read_text(encoding="utf-8", errors="ignore")
                om = re.search(r"<title>(.+?)</title>", other_text)
                if not om:
                    continue
                overlap = len(current_tokens & _title_tokens(om.group(1).strip()))
                if overlap > 0:
                    scored.append((other.stem, overlap))
            for s, _ in sorted(scored, key=lambda x: x[1], reverse=True)[:4]:
                related_slugs.append(s)

        # Tags
        tokens = _title_tokens(title)
        tags = sorted(list(tokens) + [cat_class.replace("_", "-")])

        # FAQ extraction
        faq_items = []
        parts = re.split(r'<h2[^>]*>.*?FAQ.*?</h2>', body_html, flags=re.IGNORECASE)
        if len(parts) >= 2:
            faq_section = parts[1]
            next_h2 = re.search(r'<h2', faq_section)
            if next_h2:
                faq_section = faq_section[:next_h2.start()]
            pattern = r'<strong>([^<]+\?)\s*</strong>\s*(.+?)(?=<strong>|<h[23]|$)'
            for fm in re.finditer(pattern, faq_section, re.DOTALL):
                answer = _strip_tags(fm.group(2)).strip()
                if answer:
                    faq_items.append({"question": fm.group(1).strip(), "answer": answer})

        data = {
            "slug": slug,
            "title": title,
            "description": description,
            "content_html": body_html,
            "category": cat_class,
            "category_display": cat_name,
            "date_published": date_published,
            "date_modified": date_modified,
            "reading_time_minutes": reading_min,
            "word_count": word_count,
            "toc": toc_entries,
            "related_slugs": related_slugs,
            "affiliate": {
                "name": aff_name,
                "url": aff_url,
                "description": aff_desc,
            },
            "faq": faq_items,
            "tags": tags,
        }

        json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  Exported: {slug}.json ({word_count} words, {len(toc_entries)} sections)")

    # Generate index
    agent = DistributionAgent(DATA_DIR, BASE_DIR, ARTICLES_DIR)
    agent._export_article_index()
    print(f"\nGenerated _index.json with {len(html_files)} articles.")


if __name__ == "__main__":
    backfill()
