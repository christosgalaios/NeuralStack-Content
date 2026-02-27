# CLAUDE.md — NeuralStack Autonomous Content Pipeline

## Project Overview

Fully autonomous, zero-cost multi-agent content system. Generates SEO-optimized
long-form technical articles + TikTok scripts, publishes to GitHub Pages via
GitHub Actions. Runs daily at 03:00 UTC with zero human interaction required.

## Architecture

**Pipeline flow** (`main.py`):
1. **DiscoveryAgent** — selects 5 unprocessed topics from pool (`status == "new"` or `"selected"`)
2. **ContentAgent** — generates ~1,300-word articles using template or optional Ollama LLM
3. **ValidationAgent** — checks word count (≥1,200), structure (H2/table/FAQ), rejects AI patterns & keyword stuffing
4. **DistributionAgent** — publishes HTML to `/articles/`, updates index/sitemap/RSS
5. **TikTokAgent** — generates 5 short-form video scripts per run

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
| `.github/workflows/autonomous.yml` | CI: tests → pipeline → commit |

## Current State (last updated: 2026-02-27)

- **Articles published**: 19 HTML files in `/articles/`
- **Topic pool**: 529 total (514 new, 15 published)
- **Categories**: 345 devtools_comparison, 159 compatibility, 10 foreign_news, 15 tutorial
- **Days of content remaining**: ~102 at 5 articles/day
- **TikTok scripts**: 15 generated across tutorial/myth_bust/hot_take formats
- **Tests**: 26 passing (discovery, content, validation, distribution, integration)
- **Pipeline status**: Fully operational, producing 5 articles + 5 TikTok scripts per run

## Monetization Setup

- **Affiliate links**: Cursor IDE, Datadog, Railway embedded in every article
  - Configurable via `NEURALSTACK_AFF{1,2,3}_{NAME,URL}` env vars
  - Links rendered as `<a rel="noopener sponsored">` in published HTML
- **AdSense**: Set `NEURALSTACK_ADSENSE_ID=ca-pub-XXXXX` to inject auto-ads
- **SEO meta**: Every article has description, canonical URL, viewport, robots tags

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

# Run from scripts/ directory
python scripts/run_pipeline.py

# Check topic pool status
python -c "
import json; from collections import Counter
t = json.loads(open('data/topics.json').read())
print(Counter(x['status'] for x in t))
"
```

## Known Issues / Technical Debt

- `performance.json` still carries a stale `"name 'POSTS_DIR' is not defined"` error from first-ever run
- Template-generated articles share identical boilerplate sections — keyword/category not woven into body text
- TikTok agent has no automated tests yet
- Older articles (pre-monetization) still have raw `{{AFFILIATE_TOOL}}` placeholders and old HTML template without SEO meta — they will not be regenerated unless manually triggered

## Conventions

- **Zero external dependencies** — standard library only for core pipeline
- **Branch**: develop on `claude/suggest-next-steps-msdrn`, push there
- **Commits**: descriptive multi-line messages, include session link
- **Tests**: `tests/test_*.py`, run with `python -m unittest discover -s tests`
- **No manual edits** to generated files (`index.html`, `sitemap.xml`, `feed.xml`, `articles/*.html`) — they are overwritten each pipeline run
