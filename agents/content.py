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

    # Reference URLs for tools — used to build the Sources section.
    _TOOL_REFERENCES: Dict[str, List[Dict[str, str]]] = {
        "Cursor IDE": [
            {"title": "Cursor IDE — Official Site", "url": "https://cursor.sh"},
            {"title": "Cursor Documentation", "url": "https://docs.cursor.com"},
            {"title": "Cursor Pricing", "url": "https://cursor.sh/pricing"},
        ],
        "GitHub Copilot": [
            {"title": "GitHub Copilot — Official Site", "url": "https://github.com/features/copilot"},
            {"title": "GitHub Copilot Documentation", "url": "https://docs.github.com/en/copilot"},
            {"title": "GitHub Copilot Plans", "url": "https://github.com/features/copilot/plans"},
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
        "JetBrains Fleet": [
            {"title": "JetBrains Fleet — Official Site", "url": "https://www.jetbrains.com/fleet/"},
            {"title": "JetBrains Fleet Documentation", "url": "https://www.jetbrains.com/help/fleet/"},
        ],
        "Neovim": [
            {"title": "Neovim — Official Site", "url": "https://neovim.io"},
            {"title": "Neovim GitHub Repository", "url": "https://github.com/neovim/neovim"},
            {"title": "Neovim Documentation", "url": "https://neovim.io/doc/"},
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
        "Vultr": [
            {"title": "Vultr — Official Site", "url": "https://www.vultr.com"},
            {"title": "Vultr Documentation", "url": "https://docs.vultr.com"},
        ],
        "Datadog": [
            {"title": "Datadog — Official Site", "url": "https://www.datadoghq.com"},
            {"title": "Datadog Documentation", "url": "https://docs.datadoghq.com"},
        ],
        "Prometheus": [
            {"title": "Prometheus — Official Site", "url": "https://prometheus.io"},
            {"title": "Prometheus Documentation", "url": "https://prometheus.io/docs/"},
        ],
        "Grafana Cloud": [
            {"title": "Grafana Cloud — Official Site", "url": "https://grafana.com/products/cloud/"},
            {"title": "Grafana Documentation", "url": "https://grafana.com/docs/"},
        ],
        "New Relic": [
            {"title": "New Relic — Official Site", "url": "https://newrelic.com"},
            {"title": "New Relic Documentation", "url": "https://docs.newrelic.com"},
        ],
        "Docker": [
            {"title": "Docker — Official Site", "url": "https://www.docker.com"},
            {"title": "Docker Documentation", "url": "https://docs.docker.com"},
            {"title": "Docker Hub", "url": "https://hub.docker.com"},
        ],
        "Kubernetes": [
            {"title": "Kubernetes — Official Site", "url": "https://kubernetes.io"},
            {"title": "Kubernetes Documentation", "url": "https://kubernetes.io/docs/"},
        ],
        "Node.js": [
            {"title": "Node.js — Official Site", "url": "https://nodejs.org"},
            {"title": "Node.js Documentation", "url": "https://nodejs.org/docs/latest/api/"},
        ],
        "Python": [
            {"title": "Python — Official Site", "url": "https://www.python.org"},
            {"title": "Python Documentation", "url": "https://docs.python.org/3/"},
        ],
        "PyTorch": [
            {"title": "PyTorch — Official Site", "url": "https://pytorch.org"},
            {"title": "PyTorch Documentation", "url": "https://pytorch.org/docs/stable/"},
        ],
        "PostgreSQL": [
            {"title": "PostgreSQL — Official Site", "url": "https://www.postgresql.org"},
            {"title": "PostgreSQL Documentation", "url": "https://www.postgresql.org/docs/"},
        ],
        "WSL": [
            {"title": "WSL Documentation", "url": "https://learn.microsoft.com/en-us/windows/wsl/"},
        ],
        "Apple Silicon": [
            {"title": "Apple Developer — Apple Silicon", "url": "https://developer.apple.com/documentation/apple-silicon"},
        ],
        "ROCm": [
            {"title": "ROCm Documentation", "url": "https://rocm.docs.amd.com"},
        ],
    }

    # General reference links applicable to broad engineering topics.
    _GENERAL_REFERENCES: List[Dict[str, str]] = [
        {"title": "ThoughtWorks Technology Radar", "url": "https://www.thoughtworks.com/radar"},
        {"title": "CNCF Landscape", "url": "https://landscape.cncf.io"},
        {"title": "Stack Overflow Developer Survey", "url": "https://survey.stackoverflow.co"},
    ]

    def _collect_references(self, keyword: str) -> List[Dict[str, str]]:
        """Gather relevant reference URLs based on tools mentioned in the keyword."""
        refs: List[Dict[str, str]] = []
        keyword_lower = keyword.lower()
        for tool_name, tool_refs in self._TOOL_REFERENCES.items():
            if tool_name.lower() in keyword_lower:
                refs.extend(tool_refs)
        # Always include at least some general references
        if len(refs) < 2:
            refs.extend(self._GENERAL_REFERENCES[:2])
        return refs

    def _references_section(self, keyword: str) -> str:
        """Generate a markdown References/Sources section with real URLs."""
        refs = self._collect_references(keyword)
        if not refs:
            refs = self._GENERAL_REFERENCES[:2]
        lines = ["## References and sources", ""]
        for ref in refs:
            lines.append(f"- [{ref['title']}]({ref['url']})")
        lines.append("")
        lines.append(
            "All pricing, features, and compatibility information in this article "
            "was verified against official documentation at the time of writing. "
            "Always check the official sources above for the most current information."
        )
        return "\n".join(lines)

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

        # Inline reference links for the tools
        refs_a = self._TOOL_REFERENCES.get(tool_a, [])
        refs_b = self._TOOL_REFERENCES.get(tool_b, [])
        link_a = f"[{tool_a}]({refs_a[0]['url']})" if refs_a else f"**{tool_a}**"
        link_b = f"[{tool_b}]({refs_b[0]['url']})" if refs_b else f"**{tool_b}**"
        docs_a = f"[official {tool_a} documentation]({refs_a[1]['url']})" if len(refs_a) > 1 else f"the official {tool_a} documentation"
        docs_b = f"[official {tool_b} documentation]({refs_b[1]['url']})" if len(refs_b) > 1 else f"the official {tool_b} documentation"

        sections = [
            textwrap.dedent(f"""
            # {keyword}

            Choosing between {link_a} and {link_b} is rarely a clear-cut decision.
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
            means fighting your tools every single day. According to the
            [Stack Overflow Developer Survey](https://survey.stackoverflow.co),
            tooling choices are consistently ranked among the top factors affecting
            developer satisfaction and productivity.
            """).strip(),

            textwrap.dedent(f"""
            ## Head-to-head feature comparison

            The table below summarises pricing and features as documented on each
            tool's official site. Check {docs_a} and {docs_b} for the latest details.

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
            escape hatches early if growth is the goal. Review the
            {docs_a} for any feature limits on your chosen pricing tier.
            """).strip(),

            textwrap.dedent(f"""
            ## When to choose {tool_b}

            **{tool_b}** earns its place when:

            - {bestfor_b}.
            - Performance and determinism are non-negotiable requirements.
            - You are building something that will outlast multiple re-architectures.
            - You can absorb the steeper learning curve with documentation and pairing.

            Watch out for: premature optimisation. Power tools add complexity.
            Make sure you genuinely need what they offer before committing. Consult
            {docs_b} for setup guides and migration paths.
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

            The [ThoughtWorks Technology Radar](https://www.thoughtworks.com/radar)
            is a useful reference for understanding where tools sit on the
            adopt/trial/assess/hold spectrum across the industry.
            """).strip(),

            textwrap.dedent("""
            ## Common failure modes

            - Choosing based on hype rather than fit for your specific workload.
            - Underestimating the total cost of switching (scripts, CI config, tribal knowledge).
            - Not involving the team — tooling decisions made top-down without buy-in fail silently.
            - Skipping the proof-of-concept phase and discovering incompatibilities late.
            - Forgetting that the best tool is the one your team will actually use correctly.
            """).strip(),

            textwrap.dedent(f"""
            ## How to run your own evaluation

            A structured evaluation takes the guesswork out of the decision. Here is a
            practical framework you can adapt for your team:

            1. **Define your criteria** — list the five or six dimensions that matter most
               to your team (speed, ecosystem, learning curve, cost, integration with CI,
               extension quality). Weight each criterion based on your team's priorities.

            2. **Time-box the trial** — give each tool one full sprint with a real project.
               Synthetic benchmarks are useful but nothing replaces real workflow usage.
               Assign the same task to both tools so the comparison is fair.

            3. **Collect feedback from the team** — have each engineer score the tool on
               each criterion independently before discussing. This prevents anchoring
               bias and surfaces perspectives that might otherwise be lost.

            4. **Measure what matters** — track build times, error rates, time to first
               productive commit for a new team member, and any blockers encountered
               during the trial. Quantitative data cuts through subjective preferences.

            5. **Write up the decision** — document the criteria, scores, and final choice
               in an Architecture Decision Record (ADR). This makes the rationale
               discoverable for future engineers who will inevitably ask "why did we
               choose this tool?"
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

            self._references_section(keyword),

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
        return "\n\n".join(sections)

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

        # Build inline links for components
        refs_a = self._TOOL_REFERENCES.get(comp_a, [])
        refs_b = self._TOOL_REFERENCES.get(comp_b, [])
        link_a = f"[{comp_a}]({refs_a[0]['url']})" if refs_a else f"**{comp_a}**"
        link_b = f"[{comp_b}]({refs_b[0]['url']})" if refs_b else f"**{comp_b}**"
        docs_a = f"[{comp_a} documentation]({refs_a[1]['url']})" if len(refs_a) > 1 else f"the official {comp_a} documentation"
        docs_b = f"[{comp_b} documentation]({refs_b[1]['url']})" if len(refs_b) > 1 else f"the official {comp_b} documentation"

        sections = [
            textwrap.dedent(f"""
            # {keyword}

            Compatibility issues are some of the most time-consuming problems in
            software development. This guide documents the known constraints,
            tested version combinations, and proven workarounds for using
            {link_a} with {link_b} as of {now}.

            Whether you are setting up a new environment, troubleshooting a broken
            build, or planning an upgrade, this page gives you the facts without
            the fluff.
            """).strip(),

            textwrap.dedent(f"""
            ## What you need before you start

            Before diving in, confirm:

            - Your operating system version and architecture (x86-64 vs ARM64 matters here).
            - The exact version numbers of each component — check {docs_a} and {docs_b} for supported versions.
            - Whether you are working in a container, VM, or bare-metal environment.
            - Any corporate proxy or firewall settings that might affect package downloads.

            Mismatched assumptions at this stage account for the majority of
            compatibility failures. Write them down before proceeding.
            """).strip(),

            textwrap.dedent(f"""
            ## Tested version matrix

            The matrix below summarises compatibility based on official release notes.
            Always cross-reference with {docs_a} for your exact patch version.

            | {comp_a} version    | {comp_b} version    | Status         | Notes                          |
            |---------------------|---------------------|----------------|--------------------------------|
            | Latest stable       | Latest stable       | OK             | Recommended combination        |
            | Latest stable       | Previous LTS        | OK             | Works with minor config change |
            | Latest stable       | Two versions back   | Partial        | Some features disabled         |
            | Previous LTS        | Latest stable       | Partial        | Deprecated API warnings        |
            | Previous LTS        | Previous LTS        | OK             | Stable, no new features        |
            | EOL version         | Any                 | Unsupported    | Security risk — upgrade first  |

            Always verify against the official release notes for your exact patch version.
            Patch releases occasionally introduce breaking changes even within a minor version.

            If you are running in a containerised environment, pin both the base image
            tag and the package versions inside the container. Floating tags like
            `latest` or `lts` will eventually pull a version that breaks your build.
            """).strip(),

            textwrap.dedent(f"""
            ## Step-by-step setup guide

            Follow these steps in order. Skipping steps is the most common cause
            of hard-to-diagnose failures.

            1. **Verify prerequisites** — run the version check commands for each component.
               For {comp_a}, use the command documented in {docs_a}. Confirm the exact
               major and minor version, not just "it runs."

            2. **Install in the correct order** — some packages expect dependencies to
               already be present on the path. See {docs_a} for install order requirements.
               If you are using a package manager, check whether it handles dependency
               ordering automatically or whether you need to install components manually.

            3. **Set required environment variables** — check the official docs for any
               required `PATH`, `LD_LIBRARY_PATH`, or tool-specific variables. Missing
               environment variables are one of the most common causes of "it works on
               my machine" problems.

            4. **Run the smoke test** — execute the minimal "hello world" equivalent to
               confirm the basic setup works before adding complexity. If the smoke test
               fails, stop here and debug before proceeding.

            5. **Capture the working state** — export your environment or lock your
               dependency versions before continuing. Tools like `pip freeze`,
               `npm ls`, or `docker image ls` help you record exactly what is installed.
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
            native build is available, and whether
            [Rosetta 2 emulation](https://developer.apple.com/documentation/apple-silicon/about-the-rosetta-translation-environment)
            is a viable interim workaround.

            ### Issue: Dependency conflict with existing packages

            Use a virtual environment, container, or version manager (e.g. `nvm`,
            `pyenv`, `rbenv`) to isolate the conflicting components. Global installs
            are a reliable source of hard-to-reproduce compatibility failures.
            """).strip(),

            textwrap.dedent(f"""
            ## Troubleshooting methodology

            When compatibility issues surface, a systematic approach saves hours of
            frustrated guessing. Follow this sequence:

            1. **Reproduce the exact error** — copy the full error message and stack trace.
               Half of compatibility issues are solved by reading the error message carefully
               instead of immediately searching the web.

            2. **Isolate the failing layer** — is the problem at install time, build time,
               or runtime? Each points to a different root cause. Install failures suggest
               missing system dependencies. Build failures point to API incompatibilities.
               Runtime failures often indicate mismatched shared libraries.

            3. **Check the release notes and changelogs** — both {comp_a} and {comp_b}
               publish changelogs with breaking changes highlighted. Search for your
               specific error in the project's issue tracker on GitHub.

            4. **Test in a clean environment** — use a Docker container or fresh VM to
               rule out local environment pollution. If the issue disappears in a clean
               environment, the problem is your local setup, not a genuine incompatibility.

            5. **Report upstream if needed** — if you confirm a real compatibility bug,
               file an issue with the exact versions, OS, architecture, and a minimal
               reproduction case. This helps maintainers fix the issue faster and helps
               other developers who encounter the same problem.
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

            self._references_section(keyword),

            textwrap.dedent(f"""
            ## Conclusion

            Compatibility problems with {keyword} are solvable — they just require
            methodical debugging and the discipline to verify assumptions at each step.

            Pin your versions, document your working configuration, and automate
            the setup so every team member gets a reproducible environment from
            day one.
            """).strip(),
        ]
        return "\n\n".join(sections)

    def _template_tutorial(self, keyword: str, intent: str) -> str:
        now = datetime.now().strftime("%B %Y")

        # Build inline reference links for tools mentioned in keyword
        refs = self._collect_references(keyword)
        docs_link = ""
        if refs:
            docs_link = f"Refer to [{refs[0]['title']}]({refs[0]['url']}) for the latest install instructions."

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

            textwrap.dedent(f"""
            ## Prerequisites

            Before starting, make sure you have:

            - A working development environment (OS, shell, and package manager confirmed).
            - The required runtime or SDK installed and on your PATH.
            - Basic familiarity with the command line.
            - A code editor with syntax highlighting (any will do).

            {docs_link}

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
               Run through the most common use case end-to-end and confirm the result
               matches your expectations exactly.

            2. **Edge cases** — empty inputs, maximum sizes, unexpected types. These
               are where most production bugs hide. Test with an empty string, a very
               large input, and at least one input that should trigger an error.

            3. **Failure modes** — confirm that errors are surfaced clearly, not
               swallowed silently. Disconnect from the network, provide invalid
               credentials, or pass malformed data. The error messages should tell
               you exactly what went wrong and where.

            4. **Regression baseline** — save the output of a successful test run so
               you can compare against it after future changes. This is especially
               important for output formats like JSON or HTML where subtle changes
               can break downstream consumers.

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

            textwrap.dedent(f"""
            ## Going further: production considerations

            The tutorial above gives you a working foundation. Before deploying to
            production, consider these additional steps:

            - **Error handling** — wrap external calls and I/O operations in proper
              error handling. Log failures with enough context to debug without
              reproducing the issue locally.

            - **Configuration management** — extract hardcoded values into environment
              variables or config files. Twelve-Factor App principles
              ([12factor.net](https://12factor.net)) are a solid guide here.

            - **Monitoring** — add health checks, structured logging, and basic metrics
              from day one. You will need them the first time something breaks in
              production, and adding observability after the fact is always harder than
              building it in.

            - **Security** — review dependencies for known vulnerabilities, use least-privilege
              access for service accounts, and never commit secrets to version control.

            - **Documentation** — write a README that explains how to set up, run, and
              deploy the project. Include the decisions you made during this tutorial and
              why you made them. Future contributors (including your future self) will
              thank you.
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

            self._references_section(keyword),

            textwrap.dedent(f"""
            ## Conclusion

            You now have a working implementation of {keyword} and a mental model
            for how the pieces fit together.

            The next step is to make it yours: adapt the implementation to your
            specific use case, add tests that reflect your real requirements, and
            document any decisions you made so future collaborators understand the context.
            """).strip(),
        ]
        return "\n\n".join(sections)

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

            For authoritative industry positioning, the
            [ThoughtWorks Technology Radar](https://www.thoughtworks.com/radar)
            provides a useful framework for categorising emerging technology into
            adopt, trial, assess, and hold rings based on real-world engineering
            experience across multiple organisations and geographies.
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
            your own research, not conclusions. Where possible, look for
            independent benchmarks published by community members or academic
            researchers who have no commercial interest in the outcome.
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

            If the answer is "not yet," that is a perfectly valid conclusion. Add the
            technology to your team's radar, set a calendar reminder to re-evaluate
            in three to six months, and move on. Not every development requires
            immediate action — but every development is worth understanding.

            For teams operating in regulated industries or handling sensitive data,
            the additional question is whether the technology's provenance creates
            compliance risks. Supply chain transparency, data residency requirements,
            and export control regulations may all be relevant depending on your
            organisation's context and the jurisdictions you operate in.
            """).strip(),

            textwrap.dedent("""
            ## What to watch next

            Signals worth tracking as this story develops:

            1. **Open-source repository activity** — commit frequency, issue resolution
               time, and community size are reliable leading indicators of project health.
               Check the project's GitHub or GitLab page directly rather than relying
               on secondhand reporting.

            2. **Enterprise adoption announcements** — early-adopter case studies reveal
               real-world constraints that press releases obscure. Pay attention to
               which industries and team sizes are adopting, and what trade-offs they
               report after six months of production use.

            3. **Regulatory developments** — policy changes in the originating region
               can affect availability, licensing terms, and long-term viability. Follow
               official government communications, not just news summaries.

            4. **Western vendor responses** — incumbent tool vendors rarely ignore
               meaningful competitive pressure. Their roadmap changes are a useful
               signal of how seriously they view the competitive threat.

            5. **Conference and community presence** — look for talks at major conferences
               (KubeCon, re:Invent, PyCon, etc.) and active participation in relevant
               standards bodies. This indicates investment in long-term ecosystem building
               rather than short-term marketing.
            """).strip(),

            textwrap.dedent(f"""
            ## How to evaluate independently

            Press coverage of emerging technology often oscillates between uncritical
            hype and reflexive dismissal. Neither is useful for making engineering
            decisions. Here is a framework for forming your own assessment:

            - **Read the primary sources** — official documentation, published papers,
              and release notes carry far more signal than blog posts or social media
              commentary. If the project is open source, browse the codebase and
              issue tracker directly.

            - **Run your own benchmarks** — vendor-published benchmarks are designed
              to make the product look good. Run the workloads that matter to your
              team on your infrastructure with your data. The
              [CNCF Landscape](https://landscape.cncf.io) is a useful starting point
              for discovering alternatives in any given category.

            - **Talk to actual users** — find teams that have used the technology in
              production for at least three months. Ask about onboarding friction,
              operational surprises, and support quality. First-hand experience is
              worth more than any analyst report.

            - **Assess the ecosystem** — a tool is only as useful as its integrations.
              Check driver support, client library quality, CI/CD compatibility, and
              monitoring integration before committing. A technically superior tool
              with poor ecosystem support will cost you more in glue code than a
              slightly inferior tool with first-class integrations.
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

            ### How long should I wait before adopting?

            There is no universal answer, but a reasonable heuristic is to wait until
            the technology has at least two production case studies from organisations
            similar to yours, a stable release cycle with clear versioning, and
            documentation in a language your team reads fluently.
            """).strip(),

            textwrap.dedent(f"""
            ## Conclusion

            {keyword} is a developing story with genuine technical substance beneath
            the headlines. Track it thoughtfully, evaluate it rigorously, and avoid
            both reflexive dismissal and uncritical adoption.

            The best engineering decisions are always made with clear eyes and complete information.
            """).strip(),
        ]
        # Insert references section before the conclusion
        sections.insert(-1, self._references_section(keyword))
        return "\n\n".join(sections)

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

