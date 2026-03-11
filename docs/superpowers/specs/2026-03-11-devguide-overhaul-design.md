# Dev Guide Overhaul — Design Spec

**Date:** 2026-03-11
**Status:** Approved
**Goal:** Transform Dev Guide from an aggressive affiliate-pushing site into a
trustworthy, content-first developer resource with organic monetization, broader
topic coverage, cleaner code, and a distinctive visual identity.

---

## 1. Affiliate De-escalation — Contextual Only

### Problem
Every page pushes Cursor/Railway/Datadog regardless of content relevance. Header
has a permanent "Try Cursor IDE" CTA. Article pages show the same affiliate
callout twice (in-content + sidebar). Homepage has a dedicated tools section.
This feels spammy and undermines trust.

### Changes

#### Frontend Removals
- **SiteHeader.tsx** — Remove `AFFILIATES[0]` CTA button. Header becomes: logo +
  nav links (Articles, Tools, About) + optional RSS icon.
- **page.tsx (homepage)** — Remove "Recommended Developer Tools" section (the
  3-card ToolCard grid). Homepage becomes content-first: hero, categories,
  featured articles, archive.
- **articles/[slug]/page.tsx** — Remove sidebar ToolCallout. Keep only the single
  in-content ToolCallout, but wrap it in a relevance check.

#### Relevance Matching System

**Define Affiliate type** in `frontend/src/lib/config.ts`:

```typescript
export interface Affiliate {
  name: string;
  url: string;
  description: string;
  tagline: string;
}

export const AFFILIATES: Affiliate[] = [ /* existing array */ ];

export const AFFILIATE_RELEVANCE: Record<string, string[]> = {
  "Cursor IDE": ["code-editor", "ai-coding", "ide", "developer-tools", "copilot", "vscode", "cursor"],
  "Datadog": ["monitoring", "observability", "logging", "debugging", "apm", "production", "datadog"],
  "Railway": ["deployment", "hosting", "cloud", "ci-cd", "infrastructure", "paas", "railway"],
};
```

**Add helper function** to `frontend/src/lib/articles.ts`:

```typescript
import { AFFILIATES, AFFILIATE_RELEVANCE, type Affiliate } from "./config";

export function getRelevantAffiliate(article: Article): Affiliate | null {
  const text = `${article.title} ${article.description} ${article.category}`.toLowerCase();
  for (const aff of AFFILIATES) {
    const keywords = AFFILIATE_RELEVANCE[aff.name] || [];
    if (keywords.some((kw) => text.includes(kw))) return aff;
  }
  return null;
}
```

**Update article page** (`articles/[slug]/page.tsx`): Replace direct use of
`article.affiliate.*` with `getRelevantAffiliate(article)`. If null, render no
callout. The Python pipeline still bakes `affiliate` into JSON — the frontend
simply ignores it and runs its own relevance check instead.

**Remove unused ToolCard import** from `page.tsx` (homepage) after removing the
tools section.

#### What Stays
- Footer "Tools We Recommend" links — standard, expected location
- `/tools` page — dedicated, user-initiated
- Single in-content ToolCallout — only when article is genuinely relevant

---

## 2. Content Broadening — Full-Stack Dev Topics

### Problem
Topic pool is 64% `devtools_comparison`, creating a monotonous content library.
Only 31 tutorials (5.6%). Published articles are heavily tool-focused. The site
reads like an affiliate catalog, not a developer resource.

### Changes

#### Add ~150-200 New Topic Seeds
Add to `data/topics.json` with `status: "new"`.

**Topic JSON schema** (each entry must match existing format):
```json
{
  "id": "tutorial-react-server-components",
  "keyword": "React Server Components complete guide",
  "category": "tutorial",
  "intent": "Learn how to use React Server Components effectively.",
  "difficulty_score": 0.35,
  "source": "seed-fullstack-broadening",
  "created_at": "2026-03-11T00:00:00Z",
  "status": "new"
}
```

Valid categories: `tutorial`, `guide`, `comparison`, `compatibility`, `review`.

**Target category distribution** (of new seeds):
- ~30% tutorial — React, Next.js, Node.js, Python, databases, testing, Docker
- ~25% guide — architecture patterns, best practices, workflows, security
- ~20% comparison — broader matchups (databases, frameworks, testing libs)
- ~15% compatibility — keep strong SEO performance
- ~10% review — broader tool reviews

**Topic areas:**
- Frontend: React hooks, Next.js App Router, TypeScript patterns, CSS techniques
- Backend: Node.js APIs, Python FastAPI/Django, Go basics, authentication
- Databases: PostgreSQL optimization, MongoDB vs SQL, Redis caching, migrations
- DevOps: Docker best practices, GitHub Actions, Kubernetes intro, CI/CD patterns
- Testing: Jest vs Vitest, E2E with Playwright, TDD workflows, mocking strategies
- Architecture: microservices, serverless, event-driven, API design patterns
- Security: OWASP basics, auth patterns, secrets management, CORS

#### What Doesn't Change
- Existing topics stay in pool (not deleted)
- Pipeline code unchanged — DiscoveryAgent already selects from unprocessed topics
- The broader pool naturally dilutes the devtools_comparison skew

---

## 3. Cleanup — Migrate RSS to Next.js and Remove Python RSS

### Problem
Python pipeline generates RSS in `_update_rss()` in `agents/distribution.py`.
Next.js does NOT currently generate RSS — the frontend only has `<link>` tags
pointing to `/feed.xml`. We need to add Next.js RSS generation FIRST, then
remove the Python version.

### Changes

#### Step 1: Add Next.js RSS Generation
Create `frontend/src/app/feed.xml/route.ts` — a Next.js route handler that:
- Reads all articles from `getAllArticles()`
- Generates valid RSS 2.0 XML
- Uses `SITE_NAME`, `BASE_URL` from config
- Exports as a static route via `export const dynamic = "force-static"`

#### Step 2: Remove Python RSS
- Delete `_update_rss()` method from `agents/distribution.py`
- Remove the `self._update_rss(posts_meta)` call in the `run()` method (line ~952)
- Remove any RSS-related imports/constants used only by this method
- Remove `test_rss_uses_real_base_url` test from `tests/test_distribution.py`
- The Next.js route handler at `feed.xml/route.ts` replaces the Python-generated
  `feed.xml` that was previously written to the output directory during pipeline runs

---

## 4. Frontend Identity — Clean & Professional

### Problem
No real logo (just a blue square with letter "D"), no favicon files, generic dark
theme with no distinctive character. Looks like a template site.

### Changes

#### Logo
Create an SVG logo: blue gradient rounded square (#3B82F6 → #60A5FA) containing
code bracket icon `</>` (Option B — code brackets). Wordmark "Dev Guide" in
Inter 700 next to it. The header logo should include subtle modern animations
(gentle hover glow, smooth transitions) using 21st.dev-style design patterns for
a polished, contemporary feel.

Files to create:
- `frontend/public/logo.svg` — full logo (icon + text)
- `frontend/public/icon.svg` — icon only (for favicon, uses SVG favicon)

**Favicon strategy:** Use SVG favicon (`icon.svg`) as primary — supported by all
modern browsers. Add a simple inline fallback in layout.tsx for older browsers.
No binary `.ico` or `.png` files needed — avoids external tooling dependency.

```html
<link rel="icon" href="/icon.svg" type="image/svg+xml" />
<link rel="apple-touch-icon" href="/icon.svg" />
```

#### Layout Updates
- `app/layout.tsx` — Replace inline SVG data URI favicon with `<link>` tags
  pointing to `/icon.svg`.

#### Header Redesign (SiteHeader.tsx)
- Replace text logo with SVG logo component
- Remove affiliate CTA button
- Rename "Home" nav link to "Articles" (both desktop AND mobile menu)
- Add subtle separator before RSS/theme toggle area
- Cleaner spacing and typography
- Logo links to `/` (replaces explicit "Home" link)

#### Homepage Redesign (page.tsx)
- Remove "Recommended Developer Tools" section
- Refine hero: tighter copy ("Developer intelligence, distilled."), pill badge
  ("Updated daily"), stats row
- Content-first layout: hero → category pills → featured articles → archive
- Cleaner visual hierarchy with more whitespace

#### Visual Refinements (globals.css)
- Subtler card hover effects (reduce glow intensity)
- Refine article page typography (better heading sizes, paragraph spacing)
- Improve code block styling
- Add subtle gradient accents to section dividers

#### Favicon in Layout
Replace current inline SVG data URI in `layout.tsx` with:
```html
<link rel="icon" href="/icon.svg" type="image/svg+xml" />
<link rel="apple-touch-icon" href="/icon.svg" />
```

---

## Scope Boundaries

### In Scope
- Affiliate placement changes (frontend only)
- Relevance matching system (frontend config + helper)
- Topic pool expansion (data file)
- Next.js RSS route handler creation
- Python RSS removal (backend cleanup, after Next.js replacement is in)
- Logo, favicon creation
- Header, homepage, article page visual refinements
- CSS polish

### Out of Scope
- Light/dark mode toggle (future work)
- Python pipeline code changes beyond RSS removal
- New page types or routes
- AdSense configuration
- Domain/DNS changes
- Analytics/tracking
- SEO schema changes (existing JSON-LD stays)

---

## File Change Summary

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/lib/config.ts` | Edit | Add AFFILIATE_RELEVANCE map |
| `frontend/src/lib/articles.ts` | Edit | Add getRelevantAffiliate() helper |
| `frontend/src/components/layout/SiteHeader.tsx` | Edit | Remove CTA, add SVG logo |
| `frontend/src/app/page.tsx` | Edit | Remove tools section, refine hero |
| `frontend/src/app/articles/[slug]/page.tsx` | Edit | Remove sidebar callout, add relevance check |
| `frontend/src/app/layout.tsx` | Edit | Replace favicon, add manifest link |
| `frontend/src/styles/globals.css` | Edit | Visual refinements |
| `frontend/public/logo.svg` | Create | Full logo SVG |
| `frontend/public/icon.svg` | Create | Icon-only SVG (favicon) |
| `frontend/src/app/feed.xml/route.ts` | Create | Next.js RSS route handler |
| `agents/distribution.py` | Edit | Remove _update_rss() and its call in run() |
| `tests/test_distribution.py` | Edit | Remove test_rss_uses_real_base_url |
| `data/topics.json` | Edit | Add ~150-200 new topic seeds |

---

## Success Criteria

1. No affiliate callouts on articles that don't match any affiliate tool
2. Header has no CTA button — clean navigation only
3. Homepage is content-first with no tools section
4. Relevant articles still show a single, contextual callout
5. Topic pool has diverse full-stack coverage across all categories
6. Python RSS generation removed, no test failures
7. Real logo and favicon render correctly across browsers
8. Site looks polished and professional, not template-generic
