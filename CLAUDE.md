# CLAUDE.md — Autonomous Content Pipeline

> **Purpose of this file**: Project brain for AI session continuity. Read this
> first to pick up the full state of the project. **Update this file after every
> significant change** (new features, bug fixes, state changes, resolved debt).

## Project Overview

Fully autonomous, zero-cost content system. Generates SEO-optimized long-form
technical articles via a Python multi-agent pipeline, renders them through a
Next.js React frontend, and publishes to GitHub Pages. Runs daily at 03:00 UTC
with zero human interaction required.

## Architecture

### Two-stage build: Python pipeline → Next.js frontend

**Stage 1 — Python content pipeline** (`main.py`):
1. **DiscoveryAgent** (`agents/discovery.py`) — selects 5 unprocessed topics from pool
2. **ContentAgent** (`agents/content.py`) — generates ~1,300-word articles
3. **ValidationAgent** (`agents/validation.py`) — quality gate (word count, structure, tone)
4. **DistributionAgent** (`agents/distribution.py`) — publishes HTML + exports JSON data

**Stage 2 — Next.js frontend** (`frontend/`):
- Reads article JSON from `data/articles/` at build time
- Renders React pages with Tailwind CSS "Dark Tech" design system
- Static export (`next export`) → `frontend/out/` → deployed to GitHub Pages

**Topic lifecycle**: `new` → `selected` → `drafted` → `published`

### URL strategy
- `trailingSlash: false` generates `/articles/slug.html` files
- Preserves all existing URL patterns — zero SEO disruption
- `.nojekyll` file prevents GitHub Pages from ignoring `_next/` directory

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Pipeline orchestrator |
| `agents/discovery.py` | Topic pool generation and selection |
| `agents/content.py` | Article generation (template + Ollama) |
| `agents/validation.py` | Quality gate (word count, structure, tone) |
| `agents/distribution.py` | HTML publishing, JSON export, sitemap, RSS |
| `agents/__init__.py` | Package exports for all agents |
| `data/topics.json` | Topic pool with status tracking |
| `data/performance.json` | Run history and metrics |
| `data/articles/*.json` | Structured article data for Next.js |
| `data/articles/_index.json` | Article index for frontend |
| `frontend/src/lib/config.ts` | Brand name, URLs, affiliates, categories |
| `frontend/src/lib/articles.ts` | Article data loading for Next.js |
| `frontend/src/app/` | Next.js App Router pages |
| `frontend/src/components/` | React components (layout, cards, monetization, SEO) |
| `frontend/src/styles/globals.css` | Design system (dark/light themes) |
| `.github/workflows/autonomous.yml` | CI: tests → pipeline → Next.js build → deploy |

## Frontend Structure

```
frontend/src/
├── app/
│   ├── layout.tsx              # Root layout (header, footer, fonts)
│   ├── page.tsx                # Homepage (hero, articles, tools)
│   ├── articles/[slug]/page.tsx # Article pages (two-column, TOC, FAQ)
│   ├── category/[cat]/page.tsx  # Category listing pages
│   ├── tools/page.tsx          # Affiliate tools comparison
│   └── about/page.tsx          # About/trust page (E-E-A-T)
├── components/
│   ├── layout/                 # SiteHeader, SiteFooter
│   ├── cards/                  # ArticleCard, ToolCard, CategoryBadge
│   ├── article/                # ReadingProgress, TableOfContents
│   ├── monetization/           # AdSlot, ToolCallout
│   └── seo/                    # ArticleJsonLd
├── lib/
│   ├── config.ts               # All brand/affiliate/category config
│   └── articles.ts             # JSON data loading functions
└── styles/
    └── globals.css             # CSS custom properties, article styles
```

## Session Startup Checklist

```bash
# 1. Topic pool status
python -c "
import json; from collections import Counter
t = json.loads(open('data/topics.json').read())
print('Topics:', Counter(x['status'] for x in t))
"

# 2. Recent pipeline runs
python -c "
import json
p = json.loads(open('data/performance.json').read())
for r in p['runs'][-3:]:
    print(f\"{r['timestamp']} | {r['status']} | articles={r['published_articles']}\")
"

# 3. Article JSON count
ls data/articles/*.json | wc -l

# 4. Python tests
python -m unittest discover -s tests -v 2>&1 | tail -5

# 5. Frontend build check
cd frontend && npm run build 2>&1 | tail -5

# 6. Git status
git branch --show-current && git log --oneline -5
```

## Current State (last updated: 2026-03-10)

### Pipeline Health
- **Status**: Fully operational — daily CI at 03:00 UTC
- **Architecture**: Python pipeline → JSON data → Next.js static build → GitHub Pages

### Content Stats
- **Articles**: 11 JSON files in `data/articles/` (backfilled from HTML)
- **Topic pool**: ~489 total (474 new, 15 affiliate-priority at score 0.10)
- **Categories**: guide, review, comparison

### Test Coverage
- **38 tests passing** across 5 test files
- `tests/test_discovery.py` — 5 tests
- `tests/test_content.py` — 6 tests
- `tests/test_validation.py` — 7 tests
- `tests/test_distribution.py` — 14 tests (includes 7 JSON export tests)
- `tests/test_pipeline.py` — 1 integration test
- TikTok tests removed (feature removed)

### Frontend
- **Framework**: Next.js 15 + React 19 + Tailwind CSS v4
- **Design**: "Dark Tech" theme — near-black backgrounds, blue accent, green CTAs
- **Static export**: 20 pages generated successfully
- **Brand**: Parameterized as "TechPulse" (placeholder — will change)

### Domain & SEO
- **Domain**: `devguide.co.uk`
- **GitHub Pages**: custom domain with HTTPS
- **Structured data**: TechArticle, FAQPage, BreadcrumbList JSON-LD per article
- **Meta tags**: title, description, canonical, OpenGraph per page

## Monetization Setup

- **Affiliate links**: Cursor IDE, Datadog, Railway
  - Configured in `frontend/src/lib/config.ts` AFFILIATES array
  - Rendered as `<a rel="noopener sponsored">` with green CTA buttons
  - Tool cards on homepage, tools page, and article sidebar
- **AdSense**: Set `ADSENSE_ID` GitHub secret → renders ad slots on all pages
  - Slots: above-title, sidebar, in-article, in-feed, footer
- **SEO per article**: JSON-LD TechArticle + FAQPage schema, canonical URLs, OpenGraph

## Environment Variables

### Python Pipeline
| Variable | Default | Purpose |
|----------|---------|---------|
| `NEURALSTACK_BASE_URL` | `https://devguide.co.uk` | Base URL for sitemap/RSS |
| `NEURALSTACK_LLM_BACKEND` | `template` | Set to `ollama` for local LLM |

### Next.js Frontend (via GitHub Secrets)
| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_BASE_URL` | Site base URL |
| `NEXT_PUBLIC_ADSENSE_ID` | Google AdSense publisher ID |
| `NEXT_PUBLIC_SITE_NAME` | Brand name override |

## Development Commands

```bash
# Python tests
python -m unittest discover -s tests -v

# Run content pipeline
python main.py

# Frontend dev server
cd frontend && npm run dev

# Frontend production build
cd frontend && npm run build

# Preview static export
cd frontend/out && python -m http.server 8080
```

## Known Issues / Technical Debt

### P1 — Important
1. **Brand name TBD** — currently "TechPulse" placeholder. Change in `frontend/src/lib/config.ts`.
2. **Only 11 articles backfilled** — the original 59 HTML articles exist but only 11 were successfully exported to JSON format. Need to investigate and re-run backfill.

### P2 — Nice to Have
3. **Topic pool imbalance** — mostly `devtools_comparison`. More tutorial/compatibility seeds needed.
4. **RSS/sitemap from Next.js** — currently still generated by Python. Should move to Next.js for consistency.
5. **Light mode toggle** — CSS variables defined but no UI toggle component yet.

## Suggested Next Steps

1. **Choose final brand name** — update `config.ts`, CNAME, DNS
2. **Sign up for affiliate programs** — get tracked referral URLs for Cursor, Datadog, Railway
3. **Enable AdSense** — set `ADSENSE_ID` as GitHub Actions secret
4. **Fix backfill** — ensure all existing articles export to JSON
5. **Add sitemap/RSS generation** to Next.js build
6. **Expand topic pool** — add tutorial seeds for affiliate tools

## Conventions

- **Python pipeline**: zero external dependencies (stdlib only)
- **Frontend**: Next.js 15 App Router, Tailwind CSS v4, TypeScript
- **Tests**: `tests/test_*.py`, run with `python -m unittest discover -s tests`
- **Git**: descriptive commit messages
- **No manual edits** to `frontend/out/` — regenerated each build
- **All brand references** parameterized in `frontend/src/lib/config.ts`
- **Update this file** after every significant change
