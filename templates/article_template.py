from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class ArticleSection:
    """Represents a single H2 section in the article."""

    heading: str
    body_paragraphs: List[str]


@dataclass
class ArticleMeta:
    """Top-level metadata used for rendering an article."""

    title: str
    description: str
    created_at: datetime


def render_article_html(meta: ArticleMeta, sections: List[ArticleSection]) -> str:
    """
    Render a long-form technical article as pure HTML.

    - No JavaScript.
    - Deterministic, consistent structure.
    - Compatible with GitHub Pages static hosting.
    """
    head_html = (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head>\n"
        '  <meta charset="utf-8" />\n'
        f"  <title>{meta.title}</title>\n"
        '  <meta name="description" content="'
        f"{meta.description}"
        '" />\n'
        '  <link rel="stylesheet" href="../assets/style.css" />\n'
        "</head>\n"
    )

    header_html = (
        "<body>\n"
        "  <article>\n"
        f"    <header>\n"
        f"      <h1>{meta.title}</h1>\n"
        f"      <p><small>Last updated {meta.created_at.isoformat()}Z</small></p>\n"
        f"      <p>{meta.description}</p>\n"
        "    </header>\n"
    )

    sections_html_parts: List[str] = []
    for section in sections:
        sections_html_parts.append("    <section>\n")
        sections_html_parts.append(f"      <h2>{section.heading}</h2>\n")
        for para in section.body_paragraphs:
            sections_html_parts.append(f"      <p>{para}</p>\n")
        sections_html_parts.append("    </section>\n")

    footer_html = (
        "    <footer>\n"
        "      <hr />\n"
        "      <p><small>This article is part of the NeuralStack technical knowledge base.</small></p>\n"
        "    </footer>\n"
        "  </article>\n"
        "</body>\n"
        "</html>\n"
    )

    return head_html + header_html + "".join(sections_html_parts) + footer_html


__all__ = ["ArticleMeta", "ArticleSection", "render_article_html"]

