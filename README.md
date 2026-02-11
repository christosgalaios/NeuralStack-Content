## NeuralStack Autonomous Multi-Agent Content System

This repository contains a **zero-cost, fully autonomous, multi-agent content business**.  
It runs entirely on **Python**, orchestrated by **GitHub Actions**, and publishes a static site on **GitHub Pages**.

After initial setup, no human interaction is required: the system discovers topics, generates long-form SEO content, validates quality, and publishes to the web on a daily schedule.

---

## High-level architecture

- **Language**: Python (no paid APIs, no external SaaS)
- **Execution environment**: GitHub Actions (free tier)
- **Hosting**: GitHub Pages serving the `site` directory
- **Persistence**: Repository files (`/data`, `/site`, `/agents`)
- **Monetisation-ready**: Affiliate placeholders and AdSense-compatible layout

### Agent overview

- **`DiscoveryAgent` (`agents/discovery.py`)**
  - Generates low-competition, high-intent topics in three niches:
    - Developer tools comparisons
    - Micro-niche technical compatibility issues
    - Foreign (JP/CN) tech news inspired topics, adapted for global engineers  
      Foreign news topics are generated at the **idea level only**; no direct translation or reproduction of copyrighted articles is performed.
  - Uses deterministic heuristics (no external APIs, no scraping).
  - Appends new topics into `data/topics.json`, avoiding duplicates.
  - Marks a small subset of topics as **selected** each run to avoid topic explosion.

- **`ContentAgent` (`agents/content.py`)**
  - Converts selected topics into **long-form SEO articles**.
  - Uses a `SimpleLocalLLM` class:
    - Default implementation is **fully offline** and template-based, ensuring deterministic output.
    - Structured for easy replacement with a local model (e.g. **Ollama**) without changing agent code.
  - Ensures:
    - Strong E-E-A-T style introductions and explanations.
    - Real structure: `H2` sections, comparison table, FAQ section, and concluding guidance.
    - At least **1,200 words per article** by construction.
    - Inclusion of **affiliate placeholders**: `{{AFFILIATE_TOOL_1}}`, `{{AFFILIATE_TOOL_2}}`, `{{AFFILIATE_TOOL_3}}`.
  - Outputs in-memory `DraftArticle` objects for downstream agents.

- **`ValidationAgent` (`agents/validation.py`)**
  - Performs **static, offline validation** to avoid SEO penalties:
    - Checks for minimum word count.
    - Verifies presence of headings, table, and FAQ section.
    - Simple heuristics for human-like tone (rejects obvious machine-patterns).
    - Guards against naive **keyword stuffing**.
  - Enriches accepted content by:
    - Adding contextual explanations to reinforce expertise.
    - Injecting inline **citation-style annotations** (`[internal notes]`, `[field experience]`) near key sections.
  - Rejects low-quality drafts silently (they can be inspected in logs if needed).

- **`DistributionAgent` (`agents/distribution.py`)**
  - Publishes validated drafts as Markdown posts in `site/posts/`.
  - Adds minimal front matter for layout and metadata.
  - Regenerates:
    - `site/index.md` with an updated list of posts.
       - Each post includes a link and last-update timestamp.
    - `site/sitemap.xml` for search engines.
    - `site/feed.xml` (RSS) for syndication and email tooling.
  - Optionally creates **short-form video script stubs** (for Shorts/YouTube/etc.) in `data/video_scripts/`.
  - Updates `data/performance.json` with the most recently published files.

- **Pipeline Orchestrator (`main.py`)**
  - Ties all agents together in a **single, idempotent pipeline**:
    1. Ensures directories and baseline data files exist.
    2. Runs `DiscoveryAgent` to append and select new topics.
    3. Runs `ContentAgent` to generate draft articles for selected topics.
    4. Runs `ValidationAgent` to filter and enrich drafts.
    5. Runs `DistributionAgent` to publish posts and update the site.
  - Adds **structured logging** to both stdout and `data/pipeline.log`.
  - Maintains a run history in `data/performance.json`.
  - Implements **self-healing** behavior:
    - Any unhandled exception is caught.
    - The failure is recorded in `performance.json` and logs.
    - The workflow exits gracefully so that future runs can continue.

---

## Repository structure

```text
/agents
  discovery.py         # DiscoveryAgent: topic generation and selection
  content.py           # ContentAgent: article generation (local LLM ready)
  validation.py        # ValidationAgent: quality and SEO safety checks
  distribution.py      # DistributionAgent: publishing, sitemap, RSS

/data
  topics.json          # Persistent topic backlog and statuses
  performance.json     # Run history and basic performance telemetry

/site
  /posts               # Generated markdown posts (GitHub Pages content)
  index.md             # Landing page + list of posts
  sitemap.xml          # Generated sitemap for search engines
  feed.xml             # Generated RSS feed

/.github/workflows
  autonomous.yml       # Daily GitHub Actions workflow

main.py                # Pipeline entrypoint
README.md              # This document
```

The site is intentionally **static** and portable. You can serve the `site` directory with GitHub Pages, any static host, or behind a CDN.

---

## How the system works (end to end)

1. **GitHub Actions triggers the pipeline**
   - The workflow file `.github/workflows/autonomous.yml` runs:
     - On a **daily cron schedule** at 03:00 UTC.
     - On demand via **workflow_dispatch**.
   - The job:
     - Checks out the repository.
     - Sets up Python.
     - Runs `python main.py`.
     - Commits and pushes any changes back to the repository.

2. **Orchestration in `main.py`**
   - Initializes directories:
     - Creates `data/`, `site/`, and `site/posts/` if missing.
   - Ensures baseline data:
     - `data/topics.json` exists and is a valid JSON list.
     - `data/performance.json` exists with an initial structure.
     - `site/index.md` exists as a minimal landing page.
   - Configures logging:
     - Logs to `data/pipeline.log`.
     - Mirrors logs to stdout for GitHub Actions.

3. **Topic discovery (`DiscoveryAgent`)**
   - Generates a set of **candidate topics** in three categories:
     - `devtools_comparison`: e.g. `"VS Code vs Neovim for full-stack developers"`.
     - `compatibility`: e.g. `"Docker on Windows 11 ARM detailed compatibility guide"`.
     - `foreign_news`: e.g. `"Tokyo startups using ... for global engineers (translated summary)"`.
   - Attaches metadata:
     - `id`, `keyword`, `category`, `intent`, `difficulty_score`, `source`, `created_at`, `status`.
   - Merges candidates into `data/topics.json`, avoiding duplicated IDs.
   - Applies a small, deterministic filter:
     - Only a handful (e.g. 5) of low difficulty topics are **selected** per run.
     - Selected topics get `status = "selected"` for traceability.

4. **Content generation (`ContentAgent` + `SimpleLocalLLM`)**
   - For each selected topic:
     - Constructs a human-readable `title` and URL-friendly `slug`.
     - Calls `SimpleLocalLLM.generate_long_form_article(...)`.
   - The default `SimpleLocalLLM`:
     - Uses **carefully written templates** that:
       - Follow E-E-A-T style (experience, expertise, authoritativeness, trustworthiness).
       - Explain high-level mental models and real-world trade-offs.
       - Include a comparison table and FAQ section.
       - Embed **affiliate placeholders** near the end:
         - `{{AFFILIATE_TOOL_1}}`
         - `{{AFFILIATE_TOOL_2}}`
         - `{{AFFILIATE_TOOL_3}}`
     - Ensures the article meets the **1,200+ word requirement**:
       - Measures current length and appends additional explanatory paragraphs if needed.
   - Results are passed along as `DraftArticle` objects rather than being written directly to disk.

5. **Validation and enrichment (`ValidationAgent`)**
   - Applies multiple checks per draft:
     - **Length**: must be at least `MIN_WORDS` (`>= 1,200` words).
     - **Structure**:
       - Must contain at least one `##` heading.
       - Must include an FAQ section.
       - Must contain at least one table (Markdown `|` + `---`).
     - **Tone**:
       - Quick heuristics to detect obviously machine-like phrases (e.g., `"as an ai language model"`).
     - **SEO safety**:
       - Rejects drafts that repeat the exact keyword an unreasonable number of times (keyword stuffing heuristic).
   - If a draft fails:
     - It is **rejected** for this run and not published.
     - The pipeline continues processing other drafts.
   - For approved drafts:
     - Adds inline **citation-like hints** to key sections.
     - Inserts an additional contextual paragraph near the top to reinforce E-E-A-T.

6. **Publishing and distribution (`DistributionAgent`)**
   - For each approved draft:
     - Writes a Markdown file into `site/posts/` with:
       - Lightweight YAML front matter (`title`, `date`, `layout`).
       - The enriched content from `ValidationAgent`.
   - Regenerates:
     - `site/index.md`:
       - Lists recent posts with titles, links, and update timestamps.
       - Stays simple and AdSense-friendly (no popups or dark patterns).
     - `site/sitemap.xml`:
       - Uses a `{{BASE_URL}}` placeholder so you can replace it with your actual Pages URL.
       - Includes the root page and all post URLs.
     - `site/feed.xml`:
       - Basic RSS feed referencing the same `{{BASE_URL}}`.
   - Generates **short-form video script stubs** per article in `data/video_scripts/`:
     - Each stub outlines a hook, context, key idea, and CTA.
   - Updates `data/performance.json`:
     - Appends a run entry (status, counts, errors).
     - Stores paths of the latest published files.

7. **GitHub Actions commit step**
   - After `main.py` completes, the workflow checks for changes:
     - If `git status --porcelain` is non-empty, it:
       - Configures a bot user.
       - Commits changes with a standard message.
       - Pushes back to the repository.
   - GitHub Pages (configured separately) then serves updated content automatically.

---

## SEO safety guarantees

The system is designed to be **conservative and durable** for long-term Google indexing:

- **No keyword stuffing**
  - Articles are written in natural language around real developer workflows.
  - A simple heuristic prevents the exact topic keyword from being overused.

- **No scraped plagiarism**
  - All content is generated from **offline templates and logic** only.
  - No scraping or external content ingestion is performed anywhere in the pipeline.

- **No thin content**
  - Each article is at least **1,200 words**.
  - Structured sections, tables, and FAQs ensure genuine depth.

- **Real user intent**
  - Topics are geared toward:
    - Comparison decisions developers actually face.
    - Compatibility questions that block real work.
    - Translated tech insight that is contextualised for global engineers.
  - Sections explicitly address pain points and decision criteria.

- **Human-like tone**
  - Templates are written in a human editorial voice.
  - Validation excludes drafts containing obviously synthetic language markers.

---

## Monetisation model

This project is **monetisation-ready** but does not integrate ads or affiliates directly (to remain zero-cost and vendor-neutral). Instead, it prepares the content and layout so you can plug in monetisation later.

In a conservative default setup, **affiliate placeholders should only be populated once the site demonstrates consistent organic traffic**, reinforcing user-first intent and reducing spam risk.

### Affiliate placeholders

Within each article, the following placeholders are embedded in a dedicated section:

- `{{AFFILIATE_TOOL_1}}` — suggested primary tool partner.
- `{{AFFILIATE_TOOL_2}}` — observability or monitoring partner.
- `{{AFFILIATE_TOOL_3}}` — hosting, CI/CD, or security partner.

You can:

- Perform a **search-and-replace** across the `site/posts/` directory.
- Replace each placeholder with:
  - The tool name.
  - A short honest description.
  - An affiliate link (with UTM tags if needed).

Example replacement (conceptual):

```markdown
{{AFFILIATE_TOOL_1}} → [JetBrains IntelliJ IDEA](https://example.com/your-affiliate-link)
```

### AdSense-compatible layout

The generated site is intentionally minimal:

- No popups.
- No cloaking or content hiding.
- Pages are **Markdown only**, suitable for:
  - GitHub Pages Jekyll.
  - Any static site generator.

To integrate AdSense:

1. Enable GitHub Pages and confirm your public URL.
2. Apply for AdSense approval for that domain.
3. When AdSense provides the snippet:
   - Add the `<script>` snippet into a layout:
     - If using Jekyll:
       - Create `_layouts/post.html` and `_layouts/default.html`.
       - Insert the AdSense `<script>` in the `<head>` or right after `<body>`.
   - If you prefer fully static Markdown only:
     - Use a site generator (e.g. Jekyll or Hugo) upstream that embeds the AdSense markup.

The content itself already follows best practices for:

- Long-form articles.
- Clear headings and sections.
- Non-intrusive monetisation spots.

---

## Known risks and mitigation strategies

### Search engine volatility

- **Risk**: Search engine algorithms may change, reducing visibility for certain kinds of content or publishing patterns.
- **Mitigation**:
  - Conservative publishing cadence with a **hard cap** on how many new topics are selected and turned into articles each day.
  - Long-form, intent-driven content with genuine depth instead of volume-driven output.
  - Continuous topic diversification across devtools comparisons, compatibility guides, and foreign-tech-inspired insights.

### Over-generation and low-impact content

- **Risk**: Publishing too many similar or low-impact articles can dilute site quality and harm perceived authority.
- **Mitigation**:
  - `DiscoveryAgent` limits how many topics are marked `selected` each run (by default, **no more than 5 topics per run** are promoted for drafting).
  - `ValidationAgent` explicitly rejects drafts that fail structural, length, tone, or keyword-safety checks.
  - You can tighten or loosen this cap over time by adjusting the discovery filter while keeping the validation rules intact.

### Data corruption or inconsistent state

- **Risk**: Manual edits or interrupted runs could leave `topics.json` or `performance.json` in an invalid state.
- **Mitigation**:
  - `main.py` regenerates baseline files if they are missing.
  - JSON parsing is guarded with fallbacks to safe defaults.
  - You can restore from Git history if a file becomes corrupted.

### Local LLM integration risk

- **Risk**: A misconfigured local LLM (e.g. Ollama) might generate content that is off-brand, too repetitive, or policy-unsafe.
- **Mitigation**:
  - LLM usage is strictly optional; the default system remains fully functional without it.
  - `ValidationAgent` stays in the loop even when an LLM is plugged in.
  - You can test LLM changes locally before enabling them in the CI environment.

---

## Non-goals

This project intentionally does **not**:

- Chase trending news cycles or real-time hype.
- Auto-post to social media platforms or third-party communities.
- Optimise for virality, clickbait, or aggressive CTR tricks over depth and clarity.
- Perform outreach, cold email, or automated link-building campaigns.
- Act as a general-purpose content farm; it focuses on **slow, compounding technical insight**.

---

## Deployment guide

### 1. Create the GitHub repository

1. Push this project to a new GitHub repository.
2. Ensure the default branch (e.g. `main`) is protected as usual.

### 2. Enable GitHub Pages

1. Go to **Settings → Pages** in your repo.
2. Under **Source**, select:
   - **Branch**: `main` (or your default branch).
   - **Folder**: `/root` or `/docs` depending on your preference.
3. To serve from the `site` directory you have two options:
   - **Option A (recommended, simple)**:
     - Keep GitHub Pages serving from the repository root.
     - Add a minimal static site generator step later that copies or builds `site/` into the root.
   - **Option B (pure GitHub Pages)**:
     - Keep using `site/` as the authored source.
     - Add a CI step that synchronises `site/` into a `/docs` directory or root on each run.

For initial use, you can simply browse the `site/` folder directly via the GitHub file viewer or configure Pages to treat `/` as the site root and copy/serve from `site/` manually.

### 3. Configure the Actions workflow

The workflow file `.github/workflows/autonomous.yml` is already set up:

- Runs daily at 03:00 UTC.
- Uses only the free GitHub Actions minutes.
- Requires no secrets by default.

You can adjust the schedule by editing:

```yaml
on:
  schedule:
    - cron: "0 3 * * *"
```

### 4. Verify a manual run

Before relying on the schedule:

1. In GitHub, go to **Actions → Autonomous Content Pipeline**.
2. Click **Run workflow**.
3. Wait for completion.
4. Inspect:
   - `data/pipeline.log`
   - `data/performance.json`
   - `site/posts/` for new posts.
   - `site/index.md`, `site/sitemap.xml`, and `site/feed.xml`.

If everything looks good, the system will now run autonomously via the cron schedule.

---

## Integrating a local LLM (Ollama-ready)

The system is purposely written so that **LLM usage is optional** and can be enabled locally without breaking the zero-cost baseline.

### Where to plug in an LLM

- The class `SimpleLocalLLM` in `agents/content.py` provides:
  - `generate_long_form_article(keyword, category, intent) -> str`.
- The default implementation:
  - Is template-based.
  - Requires no network or extra libraries.

To use a local LLM instead:

1. Run a local model server (e.g. **Ollama**):
   - Install Ollama following its documentation.
   - Pull a suitable model (e.g. `ollama pull llama3`).
2. Replace the `generate_long_form_article` method with an HTTP call:

```python
import json
import urllib.request

def generate_long_form_article(self, keyword: str, category: str, intent: str) -> str:
    prompt = f"Write a 1500-word, E-E-A-T compliant article about: {keyword}. " \
             f"Category: {category}. Intent: {intent}. Include H2/H3 headings, " \
             f"a comparison table, an FAQ section, and insert affiliate placeholders " \
             f'{{{{AFFILIATE_TOOL_1}}}}, {{{{AFFILIATE_TOOL_2}}}}, {{{{AFFILIATE_TOOL_3}}}}.'

    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=json.dumps({"model": "llama3", "prompt": prompt}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        # Adjust parsing according to the specific server API.
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("response", "")
```

3. Keep the **ValidationAgent** as-is:
   - It will ensure that only structurally sound and safe content is published.

This design keeps the **core system functional without any LLM**, while making it trivial to integrate one locally whenever you are ready.

---

## Scaling and extension

The system is intentionally minimal but **highly extensible**.

### Scaling topic discovery

- Today, `DiscoveryAgent` uses curated heuristics.
- To scale:
  - You can add:
    - Ingestion from RSS feeds (e.g. JP/CN dev news) using built-in Python libraries.
    - Local LLM-based clustering of related topics.
  - You should continue to:
    - Store topics in `data/topics.json` with metadata and status.
    - Limit how many new topics are marked `selected` each day to prevent backlog explosion.

### Scaling content generation

- Add **multiple content templates** in `SimpleLocalLLM` and:
  - Rotate them per category (comparison, compatibility, foreign news).
  - Randomise small stylistic differences within E-E-A-T boundaries.
- With a local LLM:
  - Use the templates as **system prompts** and feed the current site content as context.

### Human-in-the-loop (optional)

Although the system is designed for **zero human interaction**, you can optionally:

- Review and edit generated posts via pull requests.
- Add an additional GitHub Action job that:
  - Lints, formats, or runs custom QA scripts on `site/posts/` before publishing.

### Metrics and performance

- The file `data/performance.json` is the central place for:
  - Run timestamps and statuses.
  - Counts of topics, drafts, and published articles.
  - Accumulated error messages.
- You can:
  - Ship this into a dashboard (e.g. using GitHub Actions artifacts or external tooling).
  - Add new fields such as:
    - Page view counts (if you later integrate simple analytics).
    - Estimated revenue per article.

---

## Local testing and development

You can run the entire pipeline locally before pushing.

### Requirements

- Python 3.9+ (no external packages required).

### Steps

1. Clone the repository.
2. From the project root, run:

```bash
python main.py
```

3. Inspect the results:
   - `data/topics.json` — new topics appended (and some marked `selected`).
   - `site/posts/` — one or more new Markdown posts.
   - `site/index.md` — updated with links to the new posts.
   - `site/sitemap.xml` and `site/feed.xml` — generated for the site.

You can then open the Markdown files locally or use any static site previewer to view them as HTML.

---

## Maintenance philosophy

This project is built with a **maintenance-first mindset**:

- All logic lives in **small, plain Python modules**.
- No databases, queues, or external services are required.
- The default configuration has:
  - **Zero infrastructure cost**.
  - **Deterministic behavior**.
  - A clear entrypoint (`main.py`) for debugging.

By keeping concerns separated into agents and maintaining simple data files, it is easy to reason about, extend, and audit the system over time.

