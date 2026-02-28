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

**Dead code** (not used by main pipeline, kept for reference):
- `scripts/run_pipeline.py` — alternate entry point that uses a different agent set
- `scripts/llm_client.py` — Ollama client (functionality already in `agents/content.py`)
- `scripts/generate_article.py` — standalone article generator

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
| `data/tiktok_scripts/` | Generated TikTok scripts (JSON, 15 total) |
| `data/tiktok_topics.json` | TikTok topic pool |
| `.github/workflows/autonomous.yml` | CI: tests → pipeline → commit |
| `NEXT_STEPS.md` | **OUTDATED** — written when pipeline was broken; most P0/P1 items now resolved |

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

## Current State (last updated: 2026-02-28)

### Pipeline Health
- **Status**: Working locally, **but daily CI still produces 0 articles**
- **Root cause**: Fixes are on branch `claude/suggest-next-steps-msdrn` but have not been merged to `main` yet. The CI workflow (`.github/workflows/autonomous.yml`) runs on the default branch.
- **Last successful local run**: 2026-02-27T21:41 — produced 5 articles + 5 TikTok scripts
- **CI runs** (Feb 10–Feb 27): 23 runs, all 0/0/0 — the discovery agent was broken on `main`

### Content Stats
- **Articles published**: 19 HTML files in `/articles/`
- **Topic pool**: 529 total (514 new, 15 published)
- **Categories**: 345 devtools_comparison, 159 compatibility, 10 foreign_news, 15 tutorial
- **Days of content remaining**: ~102 at 5 articles/day
- **TikTok scripts**: 15 generated (5 topics × 3 formats: tutorial/myth_bust/hot_take)

### Test Coverage
- **26 tests passing** across 5 test files
- `tests/test_discovery.py` — 5 tests (pool generation, selection, dedup, status)
- `tests/test_content.py` — 6 tests (drafts, slugify, template structure/words/keyword)
- `tests/test_validation.py` — 7 tests (word count, structure, AI language, stuffing, enrichment)
- `tests/test_distribution.py` — 7 tests (HTML output, index, sitemap, RSS, performance, video stub)
- `tests/test_pipeline.py` — 1 integration test (end-to-end pipeline)
- **Missing**: TikTok agent tests (0 coverage for `agents/tiktok.py` — 43KB, largest agent)

### Branches
- `claude/suggest-next-steps-msdrn` — active development branch (all fixes live here)
- `main` / `master` — behind, still has broken discovery agent for CI

## Monetization Setup

- **Affiliate links**: Cursor IDE, Datadog, Railway embedded in every new article
  - Configurable via `NEURALSTACK_AFF{1,2,3}_{NAME,URL}` env vars
  - Links rendered as `<a rel="noopener sponsored">` in published HTML
- **AdSense**: Set `NEURALSTACK_ADSENSE_ID=ca-pub-XXXXX` to inject auto-ads
- **SEO meta**: Every new article has description, canonical URL, viewport, robots tags

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
```

## Known Issues / Technical Debt

### P0 — Blocking
1. **CI is still broken on `main`** — the fixed discovery agent, monetization, TikTok agent, and expanded topic pool all live on `claude/suggest-next-steps-msdrn` and have not been merged. Daily CI runs produce 0 articles.

### P1 — Important
2. **`datetime.utcnow()` deprecated** — used in 6 files (`main.py`, `agents/discovery.py`, `agents/content.py`, `agents/distribution.py`, `agents/tiktok.py`, `scripts/generate_article.py`). Should be `datetime.now(timezone.utc)`. Will warn in Python 3.12+.
3. **No TikTok agent tests** — `agents/tiktok.py` is 43KB with zero test coverage. Needs `tests/test_tiktok.py`.
4. **Old articles have broken affiliate placeholders** — 4+ articles still contain `{{AFFILIATE_TOOL_1}}` etc. from pre-monetization era. Files: `github-pages-docs.html`, `docker-on-windows-11-arm-detailed-compatibility-guide.html`, and likely others.

### P2 — Nice to Have
5. **`performance.json` has stale error** — the `"name 'POSTS_DIR' is not defined"` error from the very first run (Feb 10) is still in the global errors array. 23 zero-output runs also pollute the history.
6. **Template articles are boilerplate** — all template-generated articles share identical structure and phrasing. Keyword/category is not woven into body text. Need category-specific templates.
7. **Dead code in `scripts/`** — `run_pipeline.py`, `llm_client.py`, `generate_article.py` are unused by the main pipeline. They reference agents that no longer exist (`agents/research.py`, `agents/writer.py`, `agents/validator.py`).
8. **`NEXT_STEPS.md` is outdated** — most P0/P1 items from that file have been resolved. Should be deleted or replaced with this file.

## Suggested Next Steps (prioritized)

1. **Merge fixes to `main`** — create PR from `claude/suggest-next-steps-msdrn` → `main` to unblock daily CI
2. **Fix `datetime.utcnow()` deprecation** — replace with `datetime.now(timezone.utc)` across all files
3. **Add TikTok agent tests** — basic coverage for script generation, topic selection, format validation
4. **Fix old article affiliate placeholders** — either regenerate affected articles or find/replace placeholders
5. **Clean up `performance.json`** — remove stale error, optionally prune the 23 zero-output runs
6. **Remove dead code** — delete `scripts/` directory or consolidate useful parts
7. **Delete `NEXT_STEPS.md`** — superseded by this file
8. **Category-specific templates** — create distinct templates for devtools_comparison, compatibility, foreign_news, tutorial

## Conventions

- **Zero external dependencies** — standard library only for core pipeline
- **Branch**: develop on `claude/suggest-next-steps-msdrn`, push there
- **Commits**: descriptive multi-line messages, include session link
- **Tests**: `tests/test_*.py`, run with `python -m unittest discover -s tests`
- **No manual edits** to generated files (`index.html`, `sitemap.xml`, `feed.xml`, `articles/*.html`) — they are overwritten each pipeline run
- **Update this file** after every significant change to keep future sessions accurate
