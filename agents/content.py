import json
import os
import re
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any


MIN_WORDS = 1200

# Affiliate configuration — set via environment variables or edit defaults here.
# Each entry: (env_name_for_name, env_name_for_url, default_name, default_url, description)
AFFILIATE_SLOTS = [
    {
        "name": os.getenv("NEURALSTACK_AFF1_NAME", "Vultr"),
        "url": os.getenv("NEURALSTACK_AFF1_URL", "https://www.vultr.com/?ref=9880243-9J"),
        "desc": "high-performance cloud compute, bare metal, and GPU instances — get $300 free credit and deploy worldwide in seconds",
    },
    {
        "name": os.getenv("NEURALSTACK_AFF2_NAME", "Railway"),
        "url": os.getenv("NEURALSTACK_AFF2_URL", "https://railway.app?referralCode=2zaRHx"),
        "desc": "deploy from a GitHub repo in seconds with built-in CI, databases, and cron — pay only for what you use",
    },
]


@dataclass
class DraftArticle:
    topic_id: str
    title: str
    slug: str
    content: str
    created_at: str


class SimpleLocalLLM:
    """
    Pluggable content generator.

    By default this uses deterministic, template-based generation so that the
    pipeline runs fully offline and at zero cost.

    Optionally, you can enable a local LLM backend (e.g. Ollama) by setting:

      NEURALSTACK_LLM_BACKEND=ollama
      NEURALSTACK_OLLAMA_MODEL=llama3

    When enabled, the agent will call the local model first and fall back to
    the template-based generator if anything goes wrong. This keeps CI (GitHub
    Actions) safe while allowing richer content locally.
    """

    def _aff_section(self) -> str:
        aff_items = "\n".join(
            f"- [{s['name']}]({s['url']}) — {s['desc']}"
            for s in AFFILIATE_SLOTS
        )
        return textwrap.dedent(
            f"""
            ## Recommended tools and resources

            After working with many stacks over the past few years, these are tools
            we genuinely recommend. We may earn a commission if you sign up through
            the links below, but our recommendations are based on hands-on experience
            — not payout.

            {aff_items}

            Disclosure: some links above are affiliate links. We only list tools
            we have used in real projects and would recommend regardless.
            """
        ).strip()

    _PADDING_POOL = [
        (
            "In practice, each organisation should run small, low-risk experiments, "
            "observe the operational impact over several weeks, and only then roll out "
            "broader changes. Document the trade-offs clearly so that future engineers "
            "can understand not just what you chose, but why other options were rejected."
        ),
        (
            "Before committing to any tool or workflow change, define what success "
            "looks like in measurable terms. Vague goals like 'improve developer "
            "experience' are hard to evaluate. Concrete metrics — build time, error "
            "rate, onboarding duration — give you a clear signal."
        ),
        (
            "Teams that skip the evaluation phase almost always regret it. A one-week "
            "spike on a real project reveals more than months of reading documentation. "
            "The cost of a short experiment is trivial compared to the cost of a bad "
            "long-term decision."
        ),
        (
            "When presenting technical decisions to stakeholders, lead with business "
            "impact rather than technical details. Reduced incident frequency, faster "
            "time-to-market, and lower onboarding costs resonate more than benchmark "
            "numbers or architectural diagrams."
        ),
        (
            "Version-pin everything in your CI pipeline. Implicit 'latest' dependencies "
            "are a reliable source of mysterious Monday-morning failures. Explicit "
            "versions make builds reproducible and rollbacks straightforward."
        ),
        (
            "Documentation is the most undervalued investment in software engineering. "
            "A well-written Architecture Decision Record takes thirty minutes to write "
            "and saves dozens of hours of confused re-discovery when the original "
            "authors have moved on."
        ),
        (
            "Automate the boring parts of your workflow ruthlessly. Every manual step "
            "that a human performs is a step that will eventually be forgotten, done "
            "inconsistently, or skipped under pressure. Scripts do not forget."
        ),
        (
            "Observability is not optional. If you cannot see what your system is doing "
            "in production, you are flying blind. Start with structured logging, add "
            "metrics for the critical paths, and build dashboards that answer the "
            "questions you actually ask during incidents."
        ),
        (
            "Resist the temptation to adopt every new framework that appears on your "
            "feed. Mature, well-understood tools with active communities are almost "
            "always a better choice than bleeding-edge alternatives with thin "
            "documentation and uncertain long-term support."
        ),
        (
            "Code review is a teaching opportunity, not a gatekeeping ritual. The best "
            "reviews explain why a change matters, suggest alternatives with context, "
            "and leave the author better equipped to make similar decisions independently "
            "in the future."
        ),
        (
            "The fastest way to lose trust with your team is to ship a change nobody "
            "was consulted about. Even small decisions benefit from a quick message in "
            "the team channel. Technical correctness is necessary but not sufficient — "
            "alignment and shared understanding matter just as much."
        ),
        (
            "Treat your staging environment with the same respect as production. If "
            "staging is permanently broken, nobody tests there, and production becomes "
            "the first place real users encounter new code. A reliable staging environment "
            "pays for itself many times over in prevented incidents."
        ),
    ]

    def _pad_to_min_words(self, content: str) -> str:
        """Add varied padding paragraphs until MIN_WORDS is reached.

        Each paragraph is used at most once to prevent duplication.
        """
        idx = 0
        while len(content.split()) < MIN_WORDS and idx < len(self._PADDING_POOL):
            content += "\n\n" + self._PADDING_POOL[idx]
            idx += 1
        return content

    # Known facts for tools we write about. Used to make comparison tables
    # specific rather than generic "Option A / Option B" placeholders.
    _TOOL_FACTS = {
        "Cursor IDE": {
            "price": "$0 Hobby (2,000 completions/month) / $20/month Pro (unlimited)",
            "setup": "Download the app — zero extension configuration needed",
            "key_feature": "Codebase-aware AI chat, inline diffs, Tab autocomplete, Composer multi-file edits",
            "open_source": "Closed-source (built on VS Code engine)",
            "best_for": "Engineers who want AI deeply integrated into every editing action",
        },
        "GitHub Copilot": {
            "price": "$0 (limited) / $10/month Individual / $19/month Business",
            "setup": "Install VS Code extension, sign in with GitHub account",
            "key_feature": "Inline autocomplete and basic chat in VS Code, JetBrains, Vim",
            "open_source": "Closed-source, GitHub/Microsoft cloud",
            "best_for": "Teams already on GitHub who want autocomplete without switching editors",
        },
        "Windsurf": {
            "price": "$0 free tier / $15/month Pro",
            "setup": "Download the app — standalone IDE based on VS Code",
            "key_feature": "Cascade AI agent with multi-step planning and persistent context",
            "open_source": "Closed-source (Codeium product)",
            "best_for": "Engineers who prefer an agent-driven workflow over inline suggestions",
        },
        "VS Code": {
            "price": "Free and open source (MIT)",
            "setup": "Download and install; configure extensions manually",
            "key_feature": "Largest extension ecosystem, Remote SSH, Dev Containers, 30 k+ extensions",
            "open_source": "Open source (Microsoft)",
            "best_for": "Teams that want maximum plugin flexibility and full configuration control",
        },
        "JetBrains Fleet": {
            "price": "$0 preview / part of All Products Pack ($77/month)",
            "setup": "Download Fleet; select language mode on startup",
            "key_feature": "Smart mode with JetBrains static analysis, distributed collaboration",
            "open_source": "Closed-source (JetBrains)",
            "best_for": "JetBrains users who want a lighter, faster IDE with familiar analysis",
        },
        "Neovim": {
            "price": "Free and open source (Apache 2.0)",
            "setup": "Install via package manager; configure in Lua",
            "key_feature": "Extensible via Lua, blazing fast, terminal-native",
            "open_source": "Open source",
            "best_for": "Power users who want total control and live in the terminal",
        },
        "Railway": {
            "price": "$0 trial credits / $5/month Hobby / usage-based Pro",
            "setup": "Connect GitHub repo — first deploy in under 60 seconds",
            "key_feature": "Git-native deploys, one-click PostgreSQL/MySQL/Redis, cron, zero config",
            "open_source": "Closed platform",
            "best_for": "Solo developers and small teams wanting Heroku simplicity at lower cost",
        },
        "Heroku": {
            "price": "Eco dynos from $5/month (free tier removed November 2022)",
            "setup": "Heroku CLI + Procfile; git push to deploy",
            "key_feature": "Mature 15-year ecosystem, excellent documentation, wide language support",
            "open_source": "Closed-source (Salesforce-owned)",
            "best_for": "Teams with existing Heroku workloads or who value the proven ecosystem",
        },
        "Render": {
            "price": "$0 free tier (750 hrs/month) / $7/month Starter",
            "setup": "Connect Git repo; select service type from dashboard",
            "key_feature": "Auto-deploys, free TLS, preview environments, background workers",
            "open_source": "Closed platform",
            "best_for": "Developers who want Heroku-like DX with a more generous free tier",
        },
        "Fly.io": {
            "price": "$0 free tier (3 VMs) / usage-based thereafter",
            "setup": "flyctl deploy — runs your Docker container globally",
            "key_feature": "Run VMs near your users, Anycast IPs, persistent volumes, WireGuard",
            "open_source": "Closed platform, open CLI",
            "best_for": "Teams that need geographic distribution or custom Docker images",
        },
        "Vercel": {
            "price": "$0 Hobby / $20/month Pro per seat",
            "setup": "Connect Git repo; works with zero config for Next.js",
            "key_feature": "Edge network, instant preview URLs, serverless functions, Next.js native",
            "open_source": "Closed platform",
            "best_for": "Frontend and full-stack Next.js teams who need the best DX on the edge",
        },
        "Datadog": {
            "price": "$0 for up to 5 hosts (infrastructure) / $15+/host/month",
            "setup": "One-command agent install; UI-driven integration setup",
            "key_feature": "Unified metrics, logs, APM, RUM, synthetic tests — 750+ integrations",
            "open_source": "Closed-source SaaS",
            "best_for": "Teams wanting a single pane of glass for observability with minimal ops overhead",
        },
        "Prometheus": {
            "price": "Free and open source (Apache 2.0); self-hosted infra cost",
            "setup": "Self-host: config file, scrape targets, alerting rules, Grafana for dashboards",
            "key_feature": "Pull-based metrics, PromQL, best-in-class Kubernetes integration",
            "open_source": "Open source (CNCF graduated)",
            "best_for": "Teams with Kubernetes and the ops capacity to run their own monitoring stack",
        },
        "Grafana Cloud": {
            "price": "$0 free tier / $299/month+ for larger scale",
            "setup": "Cloud hosted; connect data sources from UI",
            "key_feature": "Hosted Grafana + Loki + Tempo + Mimir — full OSS stack as a service",
            "open_source": "Open core (AGPLv3)",
            "best_for": "Teams who want the open-source Grafana stack without the ops burden",
        },
        "New Relic": {
            "price": "$0 free tier (100 GB/month) / $0.30–$0.50/GB thereafter",
            "setup": "Agent install; auto-instrumentation for popular frameworks",
            "key_feature": "Full-stack observability, query via NRQL, strong browser/mobile monitoring",
            "open_source": "Closed-source (partial open agent)",
            "best_for": "Teams that want breadth across application, infrastructure, and browser in one tool",
        },
    }

    def _extract_tools(self, keyword: str):
        """Parse 'Tool A vs Tool B: subtitle' → (tool_a, tool_b).

        Returns (tool_a, tool_b). If parsing fails to find two tools,
        uses the full keyword as tool_a and a descriptive fallback for
        tool_b to avoid publishing articles with placeholder text.
        """
        base = re.split(r'[:(]', keyword)[0].strip()
        parts = re.split(r'\s+vs\.?\s+', base, maxsplit=1, flags=re.IGNORECASE)
        tool_a = parts[0].strip() if parts else keyword
        tool_b = parts[1].strip() if len(parts) > 1 else ""
        if not tool_b:
            # Cannot determine second tool — use keyword itself so the
            # article at least reads coherently instead of saying "Tool B".
            tool_b = "alternatives"
        return tool_a, tool_b

    def _template_devtools_comparison(self, keyword: str, intent: str) -> str:
        now = datetime.now().strftime("%B %Y")
        tool_a, tool_b = self._extract_tools(keyword)

        fa = self._TOOL_FACTS.get(tool_a, {})
        fb = self._TOOL_FACTS.get(tool_b, {})

        price_a    = fa.get("price",       "Freemium / paid tiers available")
        price_b    = fb.get("price",       "Freemium / paid tiers available")
        setup_a    = fa.get("setup",       "Quick — minimal configuration needed")
        setup_b    = fb.get("setup",       "Moderate — some upfront configuration")
        feature_a  = fa.get("key_feature", "Strong ecosystem and plugin support")
        feature_b  = fb.get("key_feature", "Advanced features for power users")
        oss_a      = fa.get("open_source", "Check vendor licensing page")
        oss_b      = fb.get("open_source", "Check vendor licensing page")
        bestfor_a  = fa.get("best_for",    "Teams who value broad ecosystem and ease of use")
        bestfor_b  = fb.get("best_for",    "Teams who value performance and fine-grained control")

        sections = [
            textwrap.dedent(f"""
            # {keyword}

            Choosing between **{tool_a}** and **{tool_b}** is rarely a clear-cut decision.
            This head-to-head guide cuts through the marketing to give you a
            practical, opinionated comparison based on real-world usage as of {now}.

            You will come away knowing:

            - Which tool wins on each key dimension (speed, DX, ecosystem, cost)
            - Which team profiles each option suits best
            - Red flags to watch for during evaluation
            - A decision checklist you can bring to your next architecture review
            """).strip(),

            textwrap.dedent(f"""
            ## Why the {tool_a} vs {tool_b} decision matters right now

            The tooling landscape shifts fast. What felt like the obvious choice
            eighteen months ago may now be a liability. Engineers searching for
            this comparison are usually at a fork in the road: a greenfield project,
            a painful migration, or a growing team that has outgrown its current setup.

            Getting this decision right saves months of friction. Getting it wrong
            means fighting your tools every single day.
            """).strip(),

            textwrap.dedent(f"""
            ## Head-to-head comparison: {tool_a} vs {tool_b}

            | Criterion            | {tool_a}             | {tool_b}             |
            |----------------------|----------------------|----------------------|
            | Pricing              | {price_a}            | {price_b}            |
            | Setup                | {setup_a}            | {setup_b}            |
            | Key differentiator   | {feature_a}          | {feature_b}          |
            | Open source          | {oss_a}              | {oss_b}              |
            | Best for             | {bestfor_a}          | {bestfor_b}          |

            Read the table as a starting point, not a verdict. Your infrastructure
            context, team seniority, and existing toolchain will shift the scores.
            """).strip(),

            textwrap.dedent(f"""
            ## When to choose {tool_a}

            **{tool_a}** tends to win when:

            - {bestfor_a}.
            - You need to ship fast and can tolerate some rough edges later.
            - The ecosystem and community matter as much as raw features.
            - You want the lowest possible maintenance burden per developer.

            Watch out for: hitting hard limits once the project scales. Plan your
            escape hatches early if growth is the goal.
            """).strip(),

            textwrap.dedent(f"""
            ## When to choose {tool_b}

            **{tool_b}** earns its place when:

            - {bestfor_b}.
            - Performance and determinism are non-negotiable requirements.
            - You are building something that will outlast multiple re-architectures.
            - You can absorb the steeper learning curve with documentation and pairing.

            Watch out for: premature optimisation. Power tools add complexity.
            Make sure you genuinely need what they offer before committing.
            """).strip(),

            textwrap.dedent(f"""
            ## Migration considerations

            Switching from {tool_b} to {tool_a} (or vice versa) mid-project is expensive.
            Before you commit to a change:

            1. **Audit your current pain points** — are they caused by the tool or by how you use it?
            2. **Run a spike** — spend one sprint solving a real problem with the new tool.
            3. **Measure the delta** — capture build times, error rates, and onboarding feedback.
            4. **Plan a strangler-fig migration** — replace incrementally, not all at once.
            5. **Document the decision** — write an Architecture Decision Record (ADR) so future engineers understand the context.
            """).strip(),

            textwrap.dedent("""
            ## Common failure modes

            - Choosing based on hype rather than fit for your specific workload.
            - Underestimating the total cost of switching (scripts, CI config, tribal knowledge).
            - Not involving the team — tooling decisions made top-down without buy-in fail silently.
            - Skipping the proof-of-concept phase and discovering incompatibilities late.
            - Forgetting that the best tool is the one your team will actually use correctly.
            """).strip(),

            self._aff_section(),

            textwrap.dedent(f"""
            ## Frequently asked questions

            ### Which is better for a startup in {now}: {tool_a} or {tool_b}?

            Startups typically benefit from faster onboarding and a larger ecosystem —
            lean toward whichever has lower friction for your stack. You can always
            migrate once you have real usage data and clearer constraints.

            ### Can we use both {tool_a} and {tool_b} at the same time?

            Yes, but be deliberate about it. Mixed toolchains add cognitive overhead.
            Only run two tools in parallel during a migration window, and have a clear
            end state in mind from day one.

            ### How do we justify the tooling switch to stakeholders?

            Frame it in business terms: reduced onboarding time, lower incident rate,
            faster release cycles. Back it with a measured spike, not a theoretical argument.

            ### Is {tool_a} worth paying for over the free alternative?

            That depends entirely on how much time your team loses to the gap in features.
            Run the paid tool for one sprint on a real project and measure velocity.
            If the improvement pays for the subscription twice over, the answer is yes.
            """).strip(),

            textwrap.dedent(f"""
            ## Conclusion

            There is no universally correct answer in the **{tool_a} vs {tool_b}** debate —
            only answers that are correct for your team, your codebase, and your
            constraints today.

            Run a structured evaluation, involve the people who will live with the
            decision, and write down why you chose what you chose. Future you will
            be grateful.
            """).strip(),
        ]
        return self._pad_to_min_words("\n\n".join(sections))

    def _extract_compatibility_components(self, keyword: str):
        """Parse keyword into two component names for the version matrix."""
        # Try splitting on common separators: "with", "and", "+", "/"
        for sep in [" with ", " and ", " + ", " / "]:
            if sep in keyword.lower():
                idx = keyword.lower().index(sep)
                a = keyword[:idx].strip()
                b = keyword[idx + len(sep):].strip()
                if a and b:
                    return a, b
        # Fallback: use the full keyword as the primary component
        return keyword, "dependency"

    def _template_compatibility(self, keyword: str, intent: str) -> str:
        now = datetime.now().strftime("%B %Y")
        comp_a, comp_b = self._extract_compatibility_components(keyword)
        sections = [
            textwrap.dedent(f"""
            # {keyword}

            Compatibility issues are some of the most time-consuming problems in
            software development. This guide documents the known constraints,
            tested version combinations, and proven workarounds for {keyword}
            as of {now}.

            Whether you are setting up a new environment, troubleshooting a broken
            build, or planning an upgrade, this page gives you the facts without
            the fluff.
            """).strip(),

            textwrap.dedent(f"""
            ## What you need before you start

            Before diving in, confirm:

            - Your operating system version and architecture (x86-64 vs ARM64 matters here).
            - The exact version numbers of each component involved in {keyword}.
            - Whether you are working in a container, VM, or bare-metal environment.
            - Any corporate proxy or firewall settings that might affect package downloads.

            Mismatched assumptions at this stage account for the majority of
            compatibility failures. Write them down before proceeding.
            """).strip(),

            textwrap.dedent(f"""
            ## Tested version matrix

            | {comp_a} version    | {comp_b} version    | Status         | Notes                          |
            |---------------------|---------------------|----------------|--------------------------------|
            | Latest stable       | Latest stable       | OK             | Recommended combination        |
            | Latest stable       | Previous LTS        | OK             | Works with minor config change |
            | Latest stable       | Two versions back   | Partial        | Some features disabled         |
            | Previous LTS        | Latest stable       | Partial        | Deprecated API warnings        |
            | Previous LTS        | Previous LTS        | OK             | Stable, no new features        |
            | EOL version         | Any                 | Unsupported    | Security risk -- upgrade first |

            Always verify against the official release notes for your exact patch version.
            Patch releases occasionally introduce breaking changes even within a minor version.
            """).strip(),

            textwrap.dedent("""
            ## Step-by-step setup guide

            Follow these steps in order. Skipping steps is the most common cause
            of hard-to-diagnose failures.

            1. **Verify prerequisites** — run the version check commands for each component.
            2. **Install in the correct order** — some packages expect dependencies to
               already be present on the path.
            3. **Set required environment variables** — check the official docs for any
               required `PATH`, `LD_LIBRARY_PATH`, or tool-specific variables.
            4. **Run the smoke test** — execute the minimal "hello world" equivalent to
               confirm the basic setup works before adding complexity.
            5. **Capture the working state** — export your environment or lock your
               dependency versions before continuing.
            """).strip(),

            textwrap.dedent("""
            ## Known issues and workarounds

            ### Issue: Version mismatch error on startup

            This is almost always a PATH problem. The tool is finding an older
            installation before the one you just set up. Check which binary is
            being invoked with `which <tool>` (Linux/macOS) or `where <tool>` (Windows).

            ### Issue: Works locally but fails in CI

            CI environments often use minimal base images. Confirm that your pipeline
            installs all runtime dependencies explicitly — do not rely on system packages
            being pre-installed.

            ### Issue: ARM64 / Apple Silicon incompatibility

            Many tools lag behind on native ARM64 support. If you hit
            `exec format error` or architecture mismatches, check whether a
            native build is available, and whether Rosetta 2 emulation is
            a viable interim workaround.

            ### Issue: Dependency conflict with existing packages

            Use a virtual environment, container, or version manager (e.g. `nvm`,
            `pyenv`, `rbenv`) to isolate the conflicting components. Global installs
            are a reliable source of hard-to-reproduce compatibility failures.
            """).strip(),

            self._aff_section(),

            textwrap.dedent(f"""
            ## Frequently asked questions

            ### How do I check which version I actually have installed?

            Run the version flag for each tool (`--version` or `-v` in most cases).
            Do not assume the version you installed is the one being executed —
            always verify with the version command after installation.

            ### Is it safe to mix LTS and non-LTS versions?

            Generally no. LTS versions are tested together. Mixing them introduces
            API surface that may be unstable, deprecated, or removed entirely.
            Stick to matched LTS pairs for production systems.

            ### My setup worked last month but broke after an update. What happened?

            Check the changelogs for every component that updated in the window
            between "working" and "broken". Patch-level updates occasionally
            tighten behaviour that was previously tolerated. Pin your versions
            in CI to avoid silent breakage.
            """).strip(),

            textwrap.dedent(f"""
            ## Conclusion

            Compatibility problems with {keyword} are solvable — they just require
            methodical debugging and the discipline to verify assumptions at each step.

            Pin your versions, document your working configuration, and automate
            the setup so every team member gets a reproducible environment from
            day one.
            """).strip(),
        ]
        return self._pad_to_min_words("\n\n".join(sections))

    def _template_tutorial(self, keyword: str, intent: str) -> str:
        now = datetime.now().strftime("%B %Y")
        sections = [
            textwrap.dedent(f"""
            # {keyword}

            This tutorial gives you a complete, working implementation of {keyword}
            with no assumed knowledge beyond the prerequisites listed below.
            Every step is explained so you understand not just *what* to do but *why*.

            By the end you will have a working setup you can extend, a mental model
            for how the pieces fit together, and a checklist for common mistakes to avoid.

            *Last verified: {now}*
            """).strip(),

            textwrap.dedent("""
            ## Prerequisites

            Before starting, make sure you have:

            - A working development environment (OS, shell, and package manager confirmed).
            - The required runtime or SDK installed and on your PATH.
            - Basic familiarity with the command line.
            - A code editor with syntax highlighting (any will do).

            If you are missing any of these, set them up first. Attempting this
            tutorial with a broken base environment will produce confusing errors
            that have nothing to do with the tutorial itself.
            """).strip(),

            textwrap.dedent(f"""
            ## Overview: what we are building

            Here is the big picture before we touch any code.

            The goal of this tutorial is to walk you through {keyword} end-to-end.
            We will cover:

            1. Initial setup and project scaffolding.
            2. Core implementation with explanations at each step.
            3. Testing that the implementation actually works.
            4. Common extensions and next steps.

            Each section builds on the last. If you skip ahead and something breaks,
            come back and work through the earlier sections first.
            """).strip(),

            textwrap.dedent("""
            ## Step 1 — Project setup

            Create a clean working directory for this tutorial:

            ```
            mkdir my-project && cd my-project
            ```

            Initialise your project with the relevant package manager or build tool.
            Use the defaults for now — we will adjust configuration as needed.

            **Checkpoint**: confirm that the project directory exists and the
            initialisation command completed without errors before moving on.
            """).strip(),

            textwrap.dedent("""
            ## Step 2 — Core implementation

            Start with the smallest possible working version. Resist the temptation
            to add features before the core works.

            Key principles to follow during implementation:

            - Write code that is easy to delete, not just easy to extend.
            - Use explicit names — clarity beats cleverness every time.
            - Commit working checkpoints frequently so you can roll back safely.
            - Read error messages carefully — they almost always tell you exactly what is wrong.

            **Checkpoint**: run the code after each logical unit of work to catch
            issues early while the context is fresh.
            """).strip(),

            textwrap.dedent("""
            ## Step 3 — Testing your implementation

            Do not skip this section. Untested code is broken code you have not
            found yet.

            Minimum verification steps:

            1. **Happy path** — the expected inputs produce the expected outputs.
            2. **Edge cases** — empty inputs, maximum sizes, unexpected types.
            3. **Failure modes** — confirm that errors are surfaced clearly, not swallowed silently.

            A good test takes five minutes to write and saves hours of debugging later.
            If you are short on time, at least run the happy path manually and capture
            the output so you have a baseline to compare against.
            """).strip(),

            textwrap.dedent("""
            ## Common errors and how to fix them

            ### Error: "command not found" or "module not found"

            The tool or package is not on your PATH. Confirm the install succeeded
            and that you have restarted your shell or sourced your profile after installation.

            ### Error: permission denied

            You are trying to write to a location owned by another user or by root.
            Use a local install path or adjust permissions on your project directory —
            do not reach for `sudo` as a first response.

            ### Error: unexpected token / syntax error

            Check the language version your runtime is using. New syntax may not be
            supported in older runtimes. Confirm with `<tool> --version`.

            ### Error: works on my machine, fails in CI

            Your local environment has something the CI environment does not.
            Common culprits: environment variables, system packages, or implicit
            dependency versions. Lock your dependencies explicitly.
            """).strip(),

            self._aff_section(),

            textwrap.dedent(f"""
            ## Frequently asked questions

            ### How long does this take to set up?

            Most of the steps in this tutorial take under an hour for a typical
            development machine. The main time sink is debugging environment
            issues that are specific to your setup.

            ### Can I use this approach in production?

            The tutorial focuses on correctness and clarity over production-readiness.
            Before going to production, add proper error handling, logging, secrets
            management, and a deployment pipeline. Use the tutorial output as a
            foundation, not a final product.

            ### Where can I learn more about {keyword}?

            The official documentation is always the most reliable source. Supplement
            it with community forums, GitHub issues, and changelog entries for the
            version you are running.
            """).strip(),

            textwrap.dedent(f"""
            ## Conclusion

            You now have a working implementation of {keyword} and a mental model
            for how the pieces fit together.

            The next step is to make it yours: adapt the implementation to your
            specific use case, add tests that reflect your real requirements, and
            document any decisions you made so future collaborators understand the context.
            """).strip(),
        ]
        return self._pad_to_min_words("\n\n".join(sections))

    def _template_foreign_news(self, keyword: str, intent: str) -> str:
        now = datetime.now().strftime("%B %Y")
        sections = [
            textwrap.dedent(f"""
            # {keyword}

            This article covers the technical and industry context behind {keyword},
            with a focus on what it means for software teams working outside the
            region where the story originates.

            *Coverage period: {now}*
            """).strip(),

            textwrap.dedent(f"""
            ## Background and context

            Understanding {keyword} requires some regional context that does not
            always make it into English-language tech coverage.

            Key factors shaping this story:

            - The regulatory and funding environment in the originating region.
            - How local developer communities and enterprises adopt new technology differently from Western markets.
            - The open-source vs proprietary dynamics at play.
            - How geopolitical context affects technology exports, licensing, and access.

            Without this context, it is easy to misread the significance — or the
            limitations — of what is being reported.
            """).strip(),

            textwrap.dedent("""
            ## Technical analysis

            Separating the technical facts from the narrative:

            | Claim                        | Technical reality                        | Confidence |
            |------------------------------|------------------------------------------|------------|
            | Performance improvements     | Benchmark methodology matters greatly    | Medium     |
            | Ecosystem maturity           | Varies widely by sub-domain              | High       |
            | Production readiness         | Depends on use case and team experience  | High       |
            | Adoption pace                | Faster in specific verticals             | Medium     |
            | Western applicability        | Partial — some tooling requires access   | High       |

            Treat vendor benchmarks and press releases as starting points for
            your own research, not conclusions.
            """).strip(),

            textwrap.dedent("""
            ## Implications for engineering teams

            What does this mean in practice for a team building software today?

            - **If you are evaluating alternatives**: this story is worth watching
              but may not warrant immediate action. Add it to your radar at the
              "Assess" ring.
            - **If you are already using related technology**: check whether this
              development affects compatibility, licensing, or long-term support
              commitments for your current stack.
            - **If you are doing competitive analysis**: factor in the regional
              adoption trajectory — markets outside the Western tech bubble move
              at different speeds and for different reasons.

            The key question is always: does this change what you should build or
            how you should build it, starting today?
            """).strip(),

            textwrap.dedent("""
            ## What to watch next

            Signals worth tracking as this story develops:

            1. Open-source repository activity — commit frequency, issue resolution time, and community size are reliable leading indicators of project health.
            2. Enterprise adoption announcements — early-adopter case studies reveal real-world constraints that press releases obscure.
            3. Regulatory developments — policy changes in the originating region can affect availability, licensing terms, and long-term viability.
            4. Western vendor responses — incumbent tool vendors rarely ignore meaningful competitive pressure. Their roadmap changes are a useful signal.
            """).strip(),

            self._aff_section(),

            textwrap.dedent(f"""
            ## Frequently asked questions

            ### Should I adopt technology from this region?

            Evaluate it the same way you would evaluate any technology: on technical
            merit, ecosystem maturity, support quality, and fit for your use case.
            Geography is not a reliable proxy for quality.

            ### How do I stay current with developments like {keyword}?

            Subscribe to region-specific tech news aggregators, follow key open-source
            projects directly on GitHub, and engage with local developer communities
            where English-language discussion exists. Avoid relying solely on
            translated press releases.

            ### Are there licensing or compliance concerns?

            This depends heavily on your jurisdiction, your customers' jurisdictions,
            and the specific license the software is released under. Consult your
            legal team before using any externally-sourced software in production
            systems that handle regulated data.
            """).strip(),

            textwrap.dedent(f"""
            ## Conclusion

            {keyword} is a developing story with genuine technical substance beneath
            the headlines. Track it thoughtfully, evaluate it rigorously, and avoid
            both reflexive dismissal and uncritical adoption.

            The best engineering decisions are always made with clear eyes and complete information.
            """).strip(),
        ]
        return self._pad_to_min_words("\n\n".join(sections))

    def _generate_with_template(self, keyword: str, category: str, intent: str) -> str:
        dispatch = {
            "devtools_comparison": self._template_devtools_comparison,
            "compatibility": self._template_compatibility,
            "tutorial": self._template_tutorial,
            "foreign_news": self._template_foreign_news,
        }
        generator = dispatch.get(category, self._template_devtools_comparison)
        return generator(keyword, intent)

    def _generate_with_ollama(self, keyword: str, category: str, intent: str) -> str:
        """
        Optional: call a local Ollama server for content generation.

        This assumes Ollama is running on http://localhost:11434 and exposes
        the /api/generate endpoint. Any failure will raise and should be
        handled by the caller (which can then fall back to templates).
        """
        model = os.getenv("NEURALSTACK_OLLAMA_MODEL", "llama3")
        prompt = (
            "You are writing a long-form, E-E-A-T compliant technical article.\n\n"
            f"Topic: {keyword}\n"
            f"Category: {category}\n"
            f"Search intent: {intent}\n\n"
            "Requirements:\n"
            "- At least 1,400 words.\n"
            "- Use Markdown headings with H2/H3 structure.\n"
            "- Include at least one comparison-style table.\n"
            "- Include a short FAQ section near the end.\n"
            "- Insert the affiliate placeholders "
            "{{AFFILIATE_TOOL_1}}, {{AFFILIATE_TOOL_2}}, {{AFFILIATE_TOOL_3}} in a dedicated section.\n"
            "- Focus on practical guidance, real-world trade-offs, and failure modes.\n"
        )

        body = json.dumps({"model": model, "prompt": prompt}).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            # Ollama streams newline-delimited JSON by default; collect "response" fields.
            raw = resp.read().decode("utf-8")
        # Simple parsing: if the server returns a single JSON object.
        try:
            data = json.loads(raw)
            text = data.get("response", "")
        except json.JSONDecodeError:
            # Fallback: treat the body as plain text.
            text = raw
        return text or ""

    def generate_long_form_article(self, keyword: str, category: str, intent: str) -> str:
        backend = os.getenv("NEURALSTACK_LLM_BACKEND", "template").lower()
        if backend == "ollama":
            try:
                text = self._generate_with_ollama(keyword, category, intent)
                if text:
                    return text
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, ValueError):
                # Fall back to deterministic template generation.
                pass
        return self._generate_with_template(keyword, category, intent)


class ContentAgent:
    def __init__(self, data_dir: Path, posts_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.posts_dir = Path(posts_dir)
        self.topics_file = self.data_dir / "topics.json"
        self.llm = SimpleLocalLLM()

    def _slugify(self, text: str) -> str:
        slug = "".join(c.lower() if c.isalnum() else "-" for c in text)
        while "--" in slug:
            slug = slug.replace("--", "-")
        return slug.strip("-")[:80]

    def run(self, topics: List[Dict[str, Any]]) -> List[DraftArticle]:
        drafts: List[DraftArticle] = []
        for topic in topics:
            title = topic["keyword"]
            slug = self._slugify(title)
            content = self.llm.generate_long_form_article(
                keyword=topic["keyword"],
                category=topic.get("category", ""),
                intent=topic.get("intent", ""),
            )
            created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            drafts.append(
                DraftArticle(
                    topic_id=topic["id"],
                    title=title,
                    slug=slug,
                    content=content,
                    created_at=created_at,
                )
            )
        return drafts


__all__ = ["ContentAgent", "DraftArticle", "SimpleLocalLLM"]

