from __future__ import annotations

from datetime import datetime
from pathlib import Path

from templates.article_template import ArticleMeta, ArticleSection, render_article_html


def _find_project_root(start: Path) -> Path:
    """
    Best-effort project root detection so this script can live in a
    subdirectory (e.g. /scripts) while still writing to /articles.
    """
    current = start.resolve()
    for parent in [current, *current.parents]:
        if (parent / ".git").exists() or (parent / "README.md").exists():
            return parent
    return start


PROJECT_ROOT = _find_project_root(Path(__file__).parent)
ARTICLES_DIR = PROJECT_ROOT / "articles"


def slugify(text: str) -> str:
    slug = "".join(c.lower() if c.isalnum() else "-" for c in text)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:80] or "article"


def generate_article(slug: str, title: str, description: str) -> Path:
    """
    Generate a single long-form technical article as pure HTML into /articles/.

    The structure is deterministic and suitable for GitHub Pages:
      - Output path: articles/<slug>.html
      - No JavaScript
      - Uses a fixed, reusable template
    """
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

    created_at = datetime.utcnow()
    meta = ArticleMeta(title=title, description=description, created_at=created_at)

    sections = [
        ArticleSection(
            heading="Context and problem statement",
            body_paragraphs=[
                "This document explains a concrete technical problem and how to approach it "
                "in a production environment. The focus is on clarity, explicit trade-offs, "
                "and decisions that are defensible in front of senior engineers.",
                "Rather than chasing trends, we describe the constraints, moving parts, and "
                "failure modes that matter when the system is under load or evolving quickly.",
            ],
        ),
        ArticleSection(
            heading="Architecture and design considerations",
            body_paragraphs=[
                "Good architecture starts from use cases and operational constraints. Before "
                "picking tools, make sure you understand data flows, latency expectations, "
                "availability requirements, and ownership boundaries.",
                "Write down what 'good enough' looks like for this system over the next 12–18 "
                "months. This prevents accidental over-engineering while still leaving room "
                "for the system to grow without constant rewrites.",
            ],
        ),
        ArticleSection(
            heading="Implementation guidelines",
            body_paragraphs=[
                "Implement the smallest viable slice that exercises the critical paths: how "
                "data enters the system, how it is processed, and how results are exposed. ",
                "Keep configuration in version control, favour small, composable modules, and "
                "invest early in basic observability so that on-call engineers can understand "
                "what is happening during incidents.",
            ],
        ),
        ArticleSection(
            heading="Operational concerns and monitoring",
            body_paragraphs=[
                "From day one, decide how you will detect and respond to failure. This includes "
                "basic health checks, log aggregation, and simple dashboards that show high-level "
                "system health without requiring deep dives into raw metrics.",
                "Document standard operating procedures for common failure scenarios so that "
                "engineers can respond quickly and consistently.",
            ],
        ),
        ArticleSection(
            heading="Summary and next steps",
            body_paragraphs=[
                "A sustainable solution balances delivery speed with operational simplicity. "
                "Even if you start with a minimal implementation, make sure the path toward "
                "hardening and scaling is clear.",
                "As a next step, identify one or two metrics that correlate strongly with user "
                "experience, and instrument them clearly. This will help you make informed trade-offs "
                "as you iterate on the system.",
            ],
        ),
    ]

    html = render_article_html(meta, sections)
    output_path = ARTICLES_DIR / f"{slug}.html"
    output_path.write_text(html, encoding="utf-8")
    return output_path


if __name__ == "__main__":
    # Example usage: generates a deterministic article path that you can inspect in /articles/.
    example_title = "Example technical article template"
    example_description = "A demonstration of the reusable HTML article layout used by NeuralStack."
    example_slug = slugify(example_title)
    path = generate_article(example_slug, example_title, example_description)
    print(f"Generated article at: {path}")

