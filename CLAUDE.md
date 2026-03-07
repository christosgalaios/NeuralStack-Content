# CLAUDE.md — NeuralStack Autonomous Content Pipeline

> **Purpose of this file**: Project brain for AI session continuity. Read this
> first to pick up the full state of the project. **Update this file after every
> significant change** (new features, bug fixes, state changes, resolved debt).

## Project Overview

Fully autonomous, zero-cost multi-agent content system. Generates SEO-optimized
long-form technical articles + TikTok scripts, publishes to GitHub Pages via
GitHub Actions. Runs daily at 03:00 UTC with zero human interaction required.

## Architecture

**Pipeline flow** (`main.py`):
1. **DiscoveryAgent** (`agents/discovery.py`) — selects 5 unprocessed topics from pool (`status == "new"` or `"selected"`)
2. **ContentAgent** (`agents/content.py`) — generates ~1,300-word articles using template or optional Ollama LLM
3. **ValidationAgent** (`agents/validation.py`) — checks word count (≥1,200), structure (H2/table/FAQ), rejects AI patterns & keyword stuffing
4. **DistributionAgent** (`agents/distribution.py`) — publishes HTML to `/articles/`, updates index/sitemap/RSS
5. **TikTokAgent** (`agents/tiktok.py`) — generates 5 short-form video scripts per run

**Topic lifecycle**: `new` → `selected` → `drafted` → `published`

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Pipeline orchestrator |
| `agents/discovery.py` | Topic pool generation and selection |
| `agents/content.py` | Article generation (template + Ollama) |
| `agents/validation.py` | Quality gate (word count, structure, tone) |
| `agents/distribution.py` | HTML publishing, sitemap, RSS, SEO meta |
| `agents/tiktok.py` | TikTok script generation |
| `agents/__init__.py` | Package exports for all agents |
| `data/topics.json` | Topic pool with status tracking |
| `data/performance.json` | Run history and metrics |
| `data/tiktok_scripts/` | Generated TikTok scripts (JSON) |
| `data/tiktok_topics.json` | TikTok topic pool |
| `.github/workflows/autonomous.yml` | CI: tests → pipeline → commit |
| `assets/style.css` | Site-wide CSS (tables, code, article layout) |

## Session Startup Checklist

Run these commands at the start of every session to pick up current state:

```bash
# 1. Quick health check — topic pool status
python -c "
import json; from collections import Counter
t = json.loads(open('data/topics.json').read())
print('Topics:', Counter(x['status'] for x in t))
print('Categories:', Counter(x['category'] for x in t))
"

# 2. Recent pipeline runs (last 3)
python -c "
import json
p = json.loads(open('data/performance.json').read())
for r in p['runs'][-3:]:
    print(f\"{r['timestamp']} | status={r['status']} | topics={r['generated_topics']} articles={r['generated_articles']} published={r['published_articles']}\")
"

# 3. Article count
ls articles/*.html | wc -l

# 4. Test status
python -m unittest discover -s tests -v 2>&1 | tail -5

# 5. Check current branch
git branch --show-current && git log --oneline -5
```

## Current State (last updated: 2026-03-07)

### Pipeline Health
- **Status**: Fully operational — CI runs daily at 03:00 UTC, 5 articles + 5 TikTok scripts per run
- **Last 3 CI runs**: 2026-03-05, 2026-03-06, 2026-03-07 — all success, 5/5/5 articles
- **Active branch**: `claude/tender-einstein-drx2N` — pending PR to main

### Content Stats
- **Articles published**: 59 HTML files in `/articles/`
- **Topic pool**: ~489 total (474 new, 55 published, 15 affiliate-priority at score 0.10)
- **Categories**: 345 devtools_comparison, 159 compatibility, 15 tutorial, 10 foreign_news
- **Days of content remaining**: ~95 at 5 articles/day
- **TikTok scripts**: 15 generated (5 topics × 3 formats)

### Test Coverage
- **70 tests passing** across 6 test files
- `tests/test_discovery.py` — 5 tests
- `tests/test_content.py` — 6 tests
- `tests/test_validation.py` — 7 tests
- `tests/test_distribution.py` — 7 tests
- `tests/test_pipeline.py` — 1 integration test
- `tests/test_tiktok.py` — **44 tests** (added 2026-03-07)

### Domain & SEO
- **Domain**: `neuralstackhello.co.uk` — registered, DNS via Cloudflare (propagating)
- **GitHub Pages**: configured for custom domain; HTTPS auto-enabled after DNS check
- **Search Console**: sitemap submitted, awaiting DNS propagation

## Monetization Setup

- **Affiliate links**: Cursor IDE, Datadog, Railway embedded in every article
  - Configurable via `NEURALSTACK_AFF{1,2,3}_{NAME,URL}` env vars
  - Links rendered as `<a rel="noopener sponsored">` in published HTML
- **Priority topics**: 15 affiliate-adjacent seeds (Cursor vs Copilot, Railway vs Heroku, Datadog vs Prometheus, etc.) have `difficulty_score=0.10` — selected before all generic content
- **AdSense**: Set `NEURALSTACK_ADSENSE_ID=ca-pub-XXXXX` to inject auto-ads
- **SEO per article**: description, canonical, og:title, og:description, og:type, og:url, JSON-LD TechArticle schema, RSS autodiscovery link

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEURALSTACK_BASE_URL` | `https://christosgalaios.github.io/NeuralStack-Content` | Base URL for sitemap/RSS |
| `NEURALSTACK_LLM_BACKEND` | `template` | Set to `ollama` for local LLM |
| `NEURALSTACK_OLLAMA_MODEL` | `llama3` | Ollama model name |
| `NEURALSTACK_ADSENSE_ID` | _(empty)_ | Google AdSense publisher ID |
| `NEURALSTACK_AFF1_NAME` | `Cursor IDE` | First affiliate tool name |
| `NEURALSTACK_AFF1_URL` | `https://www.cursor.com` | First affiliate link |
| `NEURALSTACK_AFF2_NAME` | `Datadog` | Second affiliate tool name |
| `NEURALSTACK_AFF2_URL` | `https://www.datadoghq.com` | Second affiliate link |
| `NEURALSTACK_AFF3_NAME` | `Railway` | Third affiliate tool name |
| `NEURALSTACK_AFF3_URL` | `https://railway.app` | Third affiliate link |

## Development Commands

```bash
# Run tests
python -m unittest discover -s tests -v

# Run full pipeline locally
python main.py

# Check topic pool status
python -c "
import json; from collections import Counter
t = json.loads(open('data/topics.json').read())
print(Counter(x['status'] for x in t))
"

# Quick markdown→HTML smoke test
python -c "
from agents.distribution import _md_to_html
print(_md_to_html('## Hello\n\n**bold** and *italic*\n\n- item one\n- item two'))
"
```

## Known Issues / Technical Debt

### P1 — Important
1. **15 affiliate-priority topics not yet published** — they have `difficulty_score=0.10` and will be picked in the next 3 CI runs. Monitor to confirm.
2. **Existing 59 articles still have raw markdown HTML** — they were published before the markdown→HTML fix. They will NOT be regenerated automatically (pipeline only publishes new articles). Options: run a one-off backfill script, or accept that only new articles benefit from the fix.
3. **No backfill for existing articles** — need a script to re-render existing articles through `_publish_article` with the new markdown converter.

### P2 — Nice to Have
4. **Internal linking between related articles** — no cross-links yet. A "Related articles" section at the bottom of each article would improve SEO authority flow and time-on-site.
5. **Topic pool imbalance** — 345/489 topics are `devtools_comparison`. Adding more tutorial and compatibility seeds would diversify output.
6. **RSS item descriptions** — currently hardcoded generic text. Should use article meta description.

## Suggested Next Steps (prioritized)

1. **Backfill existing articles** — write a one-off script that reads all 59 articles, regenerates them through `_publish_article`, and commits the result
2. **Add internal linking** — append "Related articles" section to each new article (match by overlapping keywords)
3. **Sign up for affiliate programs** — Cursor IDE, Datadog, Railway — replace default URLs with tracked referral links via repo secrets
4. **Enable AdSense** — set `NEURALSTACK_ADSENSE_ID` as a GitHub Actions secret
5. **Expand tutorial topic pool** — add 50+ "How to use [affiliate tool]" seeds

## Conventions

- **Zero external dependencies** — standard library only for core pipeline
- **Branch**: develop on `claude/tender-einstein-drx2N`, push there
- **Commits**: descriptive multi-line messages, include session link
- **Tests**: `tests/test_*.py`, run with `python -m unittest discover -s tests`
- **No manual edits** to generated files (`index.html`, `sitemap.xml`, `feed.xml`, `articles/*.html`) — they are overwritten each pipeline run
- **Update this file** after every significant change to keep future sessions accurate
