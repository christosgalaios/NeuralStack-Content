#!/usr/bin/env python3
"""
Backfill existing article JSON files with:
1. References field (extracted from content + matched from title)
2. Cleaned HTML (remove fake citations, add inline doc links)
3. Regenerated article index
"""

import json
import re
import sys
from pathlib import Path

ARTICLES_DIR = Path("data/articles")

# Reference URLs for tools — same database as content.py
TOOL_REFERENCES = {
    "Cursor IDE": [
        {"title": "Cursor IDE — Official Site", "url": "https://cursor.sh"},
        {"title": "Cursor Documentation", "url": "https://docs.cursor.com"},
        {"title": "Cursor Pricing", "url": "https://cursor.sh/pricing"},
    ],
    "Cursor": [
        {"title": "Cursor IDE — Official Site", "url": "https://cursor.sh"},
        {"title": "Cursor Documentation", "url": "https://docs.cursor.com"},
        {"title": "Cursor Pricing", "url": "https://cursor.sh/pricing"},
    ],
    "GitHub Copilot": [
        {"title": "GitHub Copilot — Official Site", "url": "https://github.com/features/copilot"},
        {"title": "GitHub Copilot Documentation", "url": "https://docs.github.com/en/copilot"},
        {"title": "GitHub Copilot Plans", "url": "https://github.com/features/copilot/plans"},
    ],
    "Copilot": [
        {"title": "GitHub Copilot — Official Site", "url": "https://github.com/features/copilot"},
        {"title": "GitHub Copilot Documentation", "url": "https://docs.github.com/en/copilot"},
    ],
    "Windsurf": [
        {"title": "Windsurf — Official Site", "url": "https://codeium.com/windsurf"},
        {"title": "Windsurf Documentation", "url": "https://docs.codeium.com"},
    ],
    "VS Code": [
        {"title": "Visual Studio Code — Official Site", "url": "https://code.visualstudio.com"},
        {"title": "VS Code Documentation", "url": "https://code.visualstudio.com/docs"},
        {"title": "VS Code Marketplace", "url": "https://marketplace.visualstudio.com"},
    ],
    "Railway": [
        {"title": "Railway — Official Site", "url": "https://railway.app"},
        {"title": "Railway Documentation", "url": "https://docs.railway.app"},
        {"title": "Railway Pricing", "url": "https://railway.app/pricing"},
    ],
    "Heroku": [
        {"title": "Heroku — Official Site", "url": "https://www.heroku.com"},
        {"title": "Heroku Dev Center", "url": "https://devcenter.heroku.com"},
        {"title": "Heroku Pricing", "url": "https://www.heroku.com/pricing"},
    ],
    "Render": [
        {"title": "Render — Official Site", "url": "https://render.com"},
        {"title": "Render Documentation", "url": "https://docs.render.com"},
    ],
    "Fly.io": [
        {"title": "Fly.io — Official Site", "url": "https://fly.io"},
        {"title": "Fly.io Documentation", "url": "https://fly.io/docs/"},
    ],
    "Vercel": [
        {"title": "Vercel — Official Site", "url": "https://vercel.com"},
        {"title": "Vercel Documentation", "url": "https://vercel.com/docs"},
    ],
    "Netlify": [
        {"title": "Netlify — Official Site", "url": "https://www.netlify.com"},
        {"title": "Netlify Documentation", "url": "https://docs.netlify.com"},
    ],
    "Vultr": [
        {"title": "Vultr — Official Site", "url": "https://www.vultr.com"},
        {"title": "Vultr Documentation", "url": "https://docs.vultr.com"},
    ],
    "Datadog": [
        {"title": "Datadog — Official Site", "url": "https://www.datadoghq.com"},
        {"title": "Datadog Documentation", "url": "https://docs.datadoghq.com"},
        {"title": "Datadog Pricing", "url": "https://www.datadoghq.com/pricing/"},
    ],
    "Prometheus": [
        {"title": "Prometheus — Official Site", "url": "https://prometheus.io"},
        {"title": "Prometheus Documentation", "url": "https://prometheus.io/docs/"},
    ],
    "Grafana": [
        {"title": "Grafana Cloud — Official Site", "url": "https://grafana.com/products/cloud/"},
        {"title": "Grafana Documentation", "url": "https://grafana.com/docs/"},
    ],
    "New Relic": [
        {"title": "New Relic — Official Site", "url": "https://newrelic.com"},
        {"title": "New Relic Documentation", "url": "https://docs.newrelic.com"},
    ],
    "Dynatrace": [
        {"title": "Dynatrace — Official Site", "url": "https://www.dynatrace.com"},
        {"title": "Dynatrace Documentation", "url": "https://docs.dynatrace.com"},
    ],
    "Docker": [
        {"title": "Docker — Official Site", "url": "https://www.docker.com"},
        {"title": "Docker Documentation", "url": "https://docs.docker.com"},
        {"title": "Docker Hub", "url": "https://hub.docker.com"},
    ],
    "CUDA": [
        {"title": "NVIDIA CUDA Toolkit", "url": "https://developer.nvidia.com/cuda-toolkit"},
        {"title": "CUDA Documentation", "url": "https://docs.nvidia.com/cuda/"},
    ],
    "ROCm": [
        {"title": "ROCm Documentation", "url": "https://rocm.docs.amd.com"},
        {"title": "AMD ROCm GitHub", "url": "https://github.com/ROCm/ROCm"},
    ],
    "PyTorch": [
        {"title": "PyTorch — Official Site", "url": "https://pytorch.org"},
        {"title": "PyTorch Documentation", "url": "https://pytorch.org/docs/stable/"},
    ],
    "TensorRT": [
        {"title": "NVIDIA TensorRT", "url": "https://developer.nvidia.com/tensorrt"},
        {"title": "TensorRT Documentation", "url": "https://docs.nvidia.com/deeplearning/tensorrt/"},
    ],
    "ONNX": [
        {"title": "ONNX — Official Site", "url": "https://onnx.ai"},
        {"title": "ONNX GitHub", "url": "https://github.com/onnx/onnx"},
    ],
    "Prisma": [
        {"title": "Prisma — Official Site", "url": "https://www.prisma.io"},
        {"title": "Prisma Documentation", "url": "https://www.prisma.io/docs"},
    ],
    "PostgreSQL": [
        {"title": "PostgreSQL — Official Site", "url": "https://www.postgresql.org"},
        {"title": "PostgreSQL Documentation", "url": "https://www.postgresql.org/docs/"},
    ],
    "WSL": [
        {"title": "WSL Documentation", "url": "https://learn.microsoft.com/en-us/windows/wsl/"},
    ],
    "WSL2": [
        {"title": "WSL Documentation", "url": "https://learn.microsoft.com/en-us/windows/wsl/"},
    ],
    "Apple Silicon": [
        {"title": "Apple Developer — Apple Silicon", "url": "https://developer.apple.com/documentation/apple-silicon"},
    ],
    "Raspberry Pi": [
        {"title": "Raspberry Pi — Official Site", "url": "https://www.raspberrypi.com"},
        {"title": "Raspberry Pi Documentation", "url": "https://www.raspberrypi.com/documentation/"},
    ],
    "NixOS": [
        {"title": "NixOS — Official Site", "url": "https://nixos.org"},
        {"title": "NixOS Manual", "url": "https://nixos.org/manual/nixos/stable/"},
    ],
    "Docker Compose": [
        {"title": "Docker Compose Documentation", "url": "https://docs.docker.com/compose/"},
    ],
    "GitHub Codespaces": [
        {"title": "GitHub Codespaces Documentation", "url": "https://docs.github.com/en/codespaces"},
    ],
}

# Fake citation patterns to remove
FAKE_CITATIONS = [
    " [internal notes]",
    " [field experience]",
    "[internal notes]",
    "[field experience]",
]


def collect_references_for_title(title: str) -> list:
    """Match tools mentioned in the title to reference URLs."""
    refs = []
    seen_urls = set()
    title_lower = title.lower()

    for tool_name, tool_refs in TOOL_REFERENCES.items():
        if tool_name.lower() in title_lower:
            for ref in tool_refs:
                if ref["url"] not in seen_urls:
                    refs.append(ref)
                    seen_urls.add(ref["url"])

    # Add general references if we found fewer than 2 tool-specific ones
    if len(refs) < 2:
        general = [
            {"title": "ThoughtWorks Technology Radar", "url": "https://www.thoughtworks.com/radar"},
            {"title": "Stack Overflow Developer Survey", "url": "https://survey.stackoverflow.co"},
        ]
        for ref in general:
            if ref["url"] not in seen_urls:
                refs.append(ref)
                seen_urls.add(ref["url"])

    return refs


def extract_refs_from_html(html: str) -> list:
    """Extract any existing reference links from a References/Sources section."""
    refs = []
    parts = re.split(
        r'<h2[^>]*>.*?(?:References|Sources).*?</h2>',
        html, flags=re.IGNORECASE,
    )
    if len(parts) < 2:
        return refs
    ref_section = parts[1]
    next_h2 = re.search(r'<h2', ref_section)
    if next_h2:
        ref_section = ref_section[:next_h2.start()]
    for m in re.finditer(r'<a\s+href="(https?://[^"]+)"[^>]*>([^<]+)</a>', ref_section):
        url = m.group(1).strip()
        title = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        if url and title:
            refs.append({"title": title, "url": url})
    return refs


def clean_html(html: str) -> str:
    """Remove fake citations and enrich context from HTML content."""
    for citation in FAKE_CITATIONS:
        html = html.replace(citation, "")

    # Remove the generic "guardrails" paragraph that was injected by _enrich_context
    html = html.replace(
        "<p>From a practical standpoint, treat this guide as a set of guardrails "
        "rather than a script. You are encouraged to adapt the examples to the "
        "constraints of your own organisation, regulatory environment, and risk appetite.</p>",
        ""
    )

    # Clean up any double blank lines left behind
    html = re.sub(r'\n{3,}', '\n\n', html)

    return html


def backfill_article(filepath: Path) -> bool:
    """Update a single article JSON file. Returns True if modified."""
    data = json.loads(filepath.read_text(encoding="utf-8"))
    modified = False

    # 1. Clean HTML content
    if "content_html" in data:
        cleaned = clean_html(data["content_html"])
        if cleaned != data["content_html"]:
            data["content_html"] = cleaned
            modified = True

    # 2. Add references
    if "references" not in data or not data.get("references"):
        # Try to extract from existing HTML first
        refs = extract_refs_from_html(data.get("content_html", ""))
        # Then add tool-specific references from title
        title_refs = collect_references_for_title(data.get("title", ""))
        seen_urls = {r["url"] for r in refs}
        for ref in title_refs:
            if ref["url"] not in seen_urls:
                refs.append(ref)
                seen_urls.add(ref["url"])

        if refs:
            data["references"] = refs
            modified = True

    if modified:
        filepath.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )

    return modified


def rebuild_index():
    """Regenerate _index.json from all article JSON files."""
    articles = []
    for json_file in sorted(ARTICLES_DIR.glob("*.json")):
        if json_file.name.startswith("_"):
            continue
        try:
            article = json.loads(json_file.read_text(encoding="utf-8"))
            articles.append({
                "slug": article["slug"],
                "title": article["title"],
                "description": article["description"],
                "category": article["category"],
                "category_display": article.get("category_display", article["category"].title()),
                "date_published": article["date_published"],
                "reading_time_minutes": article["reading_time_minutes"],
                "tags": article.get("tags", []),
            })
        except Exception as e:
            print(f"  WARN: skipping {json_file.name}: {e}")

    articles.sort(key=lambda a: a["date_published"], reverse=True)
    index_path = ARTICLES_DIR / "_index.json"
    index_path.write_text(
        json.dumps(articles, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )
    return len(articles)


def main():
    if not ARTICLES_DIR.exists():
        print("ERROR: data/articles/ not found")
        sys.exit(1)

    json_files = [f for f in ARTICLES_DIR.glob("*.json") if not f.name.startswith("_")]
    print(f"Found {len(json_files)} article JSON files to process\n")

    updated = 0
    for filepath in sorted(json_files):
        was_modified = backfill_article(filepath)
        status = "UPDATED" if was_modified else "OK (no changes)"
        print(f"  {filepath.name}: {status}")
        if was_modified:
            updated += 1

    print(f"\nUpdated {updated}/{len(json_files)} articles")

    # Rebuild index
    count = rebuild_index()
    print(f"Rebuilt _index.json with {count} articles")


if __name__ == "__main__":
    main()
