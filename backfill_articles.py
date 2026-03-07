#!/usr/bin/env python3
"""
Backfill script: patches all existing articles with the new editorial design.

Adds: Google Fonts, favicon, breadcrumb nav, category badge, article-header,
article-meta, table of contents, article-body wrapper, tool callout,
and reading progress bar + script.

Safe to run multiple times — skips already-patched files.

Usage: python backfill_articles.py
"""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from agents.distribution import (
    _FONTS_LINK,
    _FAVICON,
    _add_heading_ids_and_toc,
    _infer_category,
    _tool_callout_html,
    BASE_URL,
)

ARTICLES_DIR = Path(__file__).parent / "articles"

_PROGRESS_SCRIPT = (
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


def _backfill_article(filepath: Path) -> bool:
    """Rebuild a single article HTML with the new template structure.

    Returns True if modified, False if skipped.
    """
    text = filepath.read_text(encoding="utf-8")

    # Already backfilled — skip
    if 'class="article-header"' in text and 'class="article-body"' in text:
        return False

    slug = filepath.stem

    # --- Extract metadata from existing HTML ---
    title_m = re.search(r"<title>(.+?)</title>", text)
    title = title_m.group(1).strip() if title_m else slug

    date_m = re.search(r'"datePublished":\s*"(\d{4}-\d{2}-\d{2})"', text)
    date_published = date_m.group(1) if date_m else "2026-03-07"

    desc_m = re.search(r'<meta name="description" content="([^"]*)"', text)
    description = desc_m.group(1) if desc_m else ""

    cat_name, cat_class = _infer_category(title)

    # --- Extract the <head> section and enhance it ---
    head_m = re.search(r'(<head>)(.*?)(</head>)', text, re.DOTALL)
    if not head_m:
        return False

    head_content = head_m.group(2)

    # Add Google Fonts + Favicon if missing
    if "fonts.googleapis.com" not in head_content:
        if '../assets/style.css' in head_content:
            head_content = head_content.replace(
                '  <link rel="stylesheet" href="../assets/style.css" />',
                f'{_FONTS_LINK}{_FAVICON}  <link rel="stylesheet" href="../assets/style.css" />',
            )
        else:
            # No stylesheet link at all — add everything before </head>
            head_content += (
                f'{_FONTS_LINK}{_FAVICON}'
                '  <link rel="stylesheet" href="../assets/style.css" />\n'
            )

    # --- Extract body content between <article> tags, or from <body> ---
    article_m = re.search(r'<article>(.*?)</article>', text, re.DOTALL)
    if article_m:
        article_inner = article_m.group(1).strip()
    else:
        # No <article> tag — extract content from <body> directly
        body_m = re.search(r'<body[^>]*>(.*?)</body>', text, re.DOTALL)
        if not body_m:
            return False
        article_inner = body_m.group(1).strip()
        # Remove any existing nav elements
        article_inner = re.sub(r'<nav[^>]*>.*?</nav>\s*', '', article_inner, flags=re.DOTALL)
        article_inner = re.sub(r'<div class="reading-progress"></div>\s*', '', article_inner)

    # Strip existing h1
    h1_m = re.search(r'<h1>(.*?)</h1>', article_inner)
    h1_text = h1_m.group(1).strip() if h1_m else title

    # Remove h1 from body content
    body_content = re.sub(r'\s*<h1>.*?</h1>\s*', '\n', article_inner, count=1).strip()

    # Remove existing article-meta div if present
    body_content = re.sub(
        r'\s*<div class="article-meta">.*?</div>\s*',
        '\n',
        body_content,
        count=1,
        flags=re.DOTALL,
    )

    # Separate related-articles section from body
    related_html = ""
    related_m = re.search(r'(<section class="related-articles">.*?</section>)', body_content, re.DOTALL)
    if related_m:
        related_html = related_m.group(1)
        body_content = body_content[:related_m.start()].strip()

    # Remove any existing tool-callout if present (from partial backfill)
    body_content = re.sub(
        r'\s*<aside class="tool-callout">.*?</aside>\s*',
        '',
        body_content,
        flags=re.DOTALL,
    )

    # Remove any existing TOC if present
    body_content = re.sub(
        r'\s*<details class="toc"[^>]*>.*?</details>\s*',
        '',
        body_content,
        flags=re.DOTALL,
    )

    # Remove article-body wrapper if partially applied
    body_content = re.sub(r'<div class="article-body">\s*', '', body_content)
    body_content = re.sub(r'\s*</div>\s*$', '', body_content)

    body_content = body_content.strip()

    # Add heading IDs and generate TOC
    body_with_ids, toc_html = _add_heading_ids_and_toc(body_content)

    # Estimate reading time
    word_count = len(body_with_ids.split())
    reading_min = max(1, round(word_count / 220))

    # Tool callout
    tool_callout = _tool_callout_html(slug)

    # --- Build the new breadcrumb nav ---
    new_nav = (
        f'  <div class="reading-progress"></div>\n'
        f'  <nav class="site-nav">'
        f'<a href="{BASE_URL}/">NeuralStack</a>'
        f'<span class="nav-sep">/</span>'
        f'<span class="nav-current">{title}</span>'
        f'</nav>\n'
    )

    # --- Build the new article block ---
    related_part = f"{related_html}\n" if related_html else ""
    new_article = (
        "<article>\n"
        '<header class="article-header">\n'
        f'  <span class="category-badge category-{cat_class}">{cat_name}</span>\n'
        f"  <h1>{h1_text}</h1>\n"
        '  <div class="article-meta">\n'
        '    <span>NeuralStack</span>\n'
        '    <span class="article-meta-dot">&#183;</span>\n'
        f'    <span>{date_published}</span>\n'
        '    <span class="article-meta-dot">&#183;</span>\n'
        f'    <span>{reading_min} min read</span>\n'
        '  </div>\n'
        '</header>\n'
        f"{toc_html}"
        f'<div class="article-body">\n{body_with_ids}\n</div>\n'
        f"{tool_callout}"
        f"{related_part}"
        "</article>\n"
    )

    # --- Reconstruct full HTML ---
    new_html = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        f"<head>{head_content}</head>\n"
        "<body>\n"
        f"{new_nav}"
        f"{new_article}"
        f"{_PROGRESS_SCRIPT}"
        "</body>\n"
        "</html>\n"
    )

    filepath.write_text(new_html, encoding="utf-8")
    return True


def main():
    if not ARTICLES_DIR.exists():
        print("No articles directory found.")
        return

    html_files = sorted(ARTICLES_DIR.glob("*.html"))
    print(f"Found {len(html_files)} articles to backfill.")

    modified = 0
    skipped = 0
    errors = 0

    for filepath in html_files:
        try:
            if _backfill_article(filepath):
                modified += 1
                print(f"  [OK] {filepath.name}")
            else:
                skipped += 1
                print(f"  [SKIP] {filepath.name} (already backfilled)")
        except Exception as e:
            errors += 1
            print(f"  [ERR] {filepath.name}: {e}")

    print(f"\nDone: {modified} modified, {skipped} skipped, {errors} errors.")


if __name__ == "__main__":
    main()
