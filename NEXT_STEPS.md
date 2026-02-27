## Next Steps for NeuralStack-Content

### Critical: Pipeline is stuck — 0 articles published since launch

The most urgent issue: **the daily pipeline has been running for 17+ days but has published 0 articles**.

`data/performance.json` shows 23 runs, all reporting `generated_topics: 0, generated_articles: 0, published_articles: 0`. The root cause is a topic exhaustion bug in `DiscoveryAgent`:

1. The first run (Feb 10) generated all 40 hardcoded topic candidates and added them to `topics.json`, but **that run failed** (`name 'POSTS_DIR' is not defined`) before any articles were created.
2. Only 5 topics were marked `"selected"` during that failed run. They were never drafted because the pipeline crashed.
3. Every subsequent run calls `_generate_candidates()`, finds all 40 IDs already exist in `topics.json`, produces an empty `new_topics` list, and exits with nothing to do.

**Fix options:**
- Reset the 5 `"selected"` topics back to `"new"` and change `DiscoveryAgent.run()` to pick from the existing backlog (topics with status `"new"`) rather than only from newly-added topics.
- Add a backlog-selection pass: if no new candidates are available, promote up to N existing `"new"` topics to `"selected"` and return them.
- Expand the seed lists in `_generate_candidates()` so that future runs can discover genuinely new topics.

---

### Consolidate the two divergent pipelines

The repo has **two independent content pipelines** that don't share code:

| Pipeline | Entry point | Agents | LLM |
|---|---|---|---|
| Original | `main.py` | `agents/{discovery,content,validation,distribution}.py` | Template-based (offline) |
| Newer | `scripts/run_pipeline.py` | `agents/{research,writer,validator}.py` + `scripts/llm_client.py` | Ollama (requires local model) |

The newer pipeline also has **import issues**: `agents/research.py` does `from llm_client import call_ollama`, but `llm_client.py` lives in `scripts/`, so this import fails unless `scripts/` is on `sys.path`. The `scripts/run_pipeline.py` adds the project root to `sys.path` but not the `scripts/` directory.

**Recommendation:** Merge the two into a single pipeline. Use the original agent structure as the backbone and integrate Ollama support through the existing `SimpleLocalLLM` class (which already has an Ollama fallback path in `agents/content.py`).

---

### Add tests

There are **zero tests** in the repository. Every agent is pure Python with no external dependencies, making them straightforward to test.

Priority test targets:
- `DiscoveryAgent`: verify deduplication, selection cap, topic status transitions
- `ValidationAgent`: verify word count, structure checks, keyword stuffing detection, tone heuristics
- `ContentAgent` / `SimpleLocalLLM`: verify template output meets minimum word count and contains required sections
- `DistributionAgent`: verify HTML output, sitemap generation, RSS feed generation
- `main.py` end-to-end: run the full pipeline against a temp directory and verify artifacts

---

### Replace `{{BASE_URL}}` placeholders

`sitemap.xml` and `feed.xml` contain literal `{{BASE_URL}}` strings. These should be replaced with the actual GitHub Pages URL, either:
- At generation time via an environment variable (e.g. `NEURALSTACK_BASE_URL`)
- As a post-processing step in the CI workflow

---

### Add dependency management

There is no `requirements.txt` or `pyproject.toml`. While the core pipeline uses only stdlib, the Ollama path and any future dependencies need to be tracked. A minimal `pyproject.toml` would also let you add a `[project.scripts]` entry point and define test dependencies (e.g., `pytest`).

---

### Fix deprecated `datetime.utcnow()`

Multiple files use `datetime.utcnow()`, which is deprecated in Python 3.12+. Replace with:
```python
from datetime import datetime, timezone
datetime.now(timezone.utc)
```

Affected files: `agents/discovery.py`, `agents/content.py`, `agents/distribution.py`, `main.py`.

---

### Expand topic discovery beyond static seeds

`DiscoveryAgent._generate_candidates()` produces a fixed set of ~40 topics from hardcoded lists. Once all are consumed, the pipeline is permanently idle. Options to make discovery sustainable:

- **Date-aware seeds**: incorporate the current month/year into topic phrasing so each run produces fresh candidates (e.g., "VS Code vs Cursor IDE for full-stack developers in 2026")
- **Combinatorial expansion**: add more tools, frameworks, and comparison dimensions to the seed lists
- **RSS ingestion**: read from curated RSS feeds (Hacker News, dev.to, etc.) to surface new keywords
- **Topic rotation**: allow previously published topics to be revisited after N months with updated content

---

### Improve content differentiation

Every template-generated article currently uses **identical structure and phrasing** regardless of topic or category. The only variable is the keyword inserted into the title and a few interpolation points. This creates near-duplicate content across articles.

Improvements:
- Create category-specific templates (comparison, compatibility guide, news summary)
- Vary section order, heading wording, and example scenarios per article
- When Ollama is available, use the template as a structural prompt rather than the final output

---

### Wire up GitHub Pages properly

The README describes a `site/` directory for GitHub Pages, but the actual `DistributionAgent` now writes to `articles/`. The `index.html` at the repo root links to `articles/`. Decide on one layout and configure GitHub Pages accordingly:
- If serving from repo root: keep `index.html` + `articles/` + `assets/` at the root (current state)
- If serving from `site/`: update `DistributionAgent` to write there and configure Pages to serve `/site`

---

### Summary of priorities

| Priority | Item | Effort |
|---|---|---|
| P0 | Fix topic exhaustion so the pipeline actually publishes articles | Small |
| P0 | Fix the import error in `agents/research.py` | Small |
| P1 | Consolidate the two pipeline code paths | Medium |
| P1 | Add basic tests for all agents | Medium |
| P1 | Replace `{{BASE_URL}}` with real URL | Small |
| P2 | Add `pyproject.toml` with dependencies and scripts | Small |
| P2 | Fix deprecated `datetime.utcnow()` calls | Small |
| P2 | Expand topic seeds for long-term sustainability | Medium |
| P3 | Category-specific content templates | Medium |
| P3 | Decide and configure GitHub Pages layout | Small |
