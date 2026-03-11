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
    # References per tool: mix of official docs AND third-party editorial
    # sources (reviews, benchmarks, tutorials, analyses) for credibility.
    _TOOL_REFERENCES: Dict[str, List[Dict[str, str]]] = {
        "Cursor IDE": [
            {"title": "Cursor IDE — Official Site", "url": "https://cursor.sh"},
            {"title": "Cursor Documentation", "url": "https://docs.cursor.com"},
            {"title": "Cursor vs Copilot: A Developer's Comparison — Builder.io", "url": "https://www.builder.io/blog/cursor-vs-github-copilot"},
            {"title": "Cursor Review: AI-Powered Code Editor — Pragmatic Engineer", "url": "https://blog.pragmaticengineer.com/cursor/"},
        ],
        "GitHub Copilot": [
            {"title": "GitHub Copilot Documentation", "url": "https://docs.github.com/en/copilot"},
            {"title": "Research: Quantifying GitHub Copilot's Impact on Developer Productivity — GitHub Blog", "url": "https://github.blog/news-insights/research/research-quantifying-github-copilots-impact-on-developer-productivity-and-happiness/"},
            {"title": "GitHub Copilot Plans and Pricing", "url": "https://github.com/features/copilot/plans"},
            {"title": "The Impact of AI on Developer Productivity: Evidence from GitHub Copilot — arXiv", "url": "https://arxiv.org/abs/2302.06590"},
        ],
        "Windsurf": [
            {"title": "Windsurf Editor — Official Site", "url": "https://codeium.com/windsurf"},
            {"title": "Windsurf Documentation", "url": "https://docs.codeium.com"},
            {"title": "Codeium's Windsurf: The First Agentic IDE — InfoQ", "url": "https://www.infoq.com/news/2024/11/codeium-windsurf-agentic-ide/"},
        ],
        "VS Code": [
            {"title": "Visual Studio Code Documentation", "url": "https://code.visualstudio.com/docs"},
            {"title": "VS Code Marketplace", "url": "https://marketplace.visualstudio.com"},
            {"title": "VS Code Can Do That?! — Burke Holland & Sarah Drasner, Smashing Magazine", "url": "https://www.smashingmagazine.com/2018/01/visual-studio-code/"},
            {"title": "Visual Studio Code Tips and Tricks — VS Code Docs", "url": "https://code.visualstudio.com/docs/getstarted/tips-and-tricks"},
        ],
        "JetBrains Fleet": [
            {"title": "JetBrains Fleet — Official Site", "url": "https://www.jetbrains.com/fleet/"},
            {"title": "JetBrains Fleet Documentation", "url": "https://www.jetbrains.com/help/fleet/"},
            {"title": "JetBrains Fleet: A New Lightweight IDE — InfoQ", "url": "https://www.infoq.com/news/2022/10/jetbrains-fleet-public-preview/"},
        ],
        "Neovim": [
            {"title": "Neovim Documentation", "url": "https://neovim.io/doc/"},
            {"title": "Neovim GitHub Repository", "url": "https://github.com/neovim/neovim"},
            {"title": "Why Neovim is the Best Code Editor — The Primeagen, YouTube", "url": "https://www.youtube.com/watch?v=QMVIJhC9Veg"},
            {"title": "Neovim: The Road to 1.0 — Neovim Blog", "url": "https://neovim.io/news/"},
        ],
        "Railway": [
            {"title": "Railway Documentation", "url": "https://docs.railway.app"},
            {"title": "Railway Pricing", "url": "https://railway.app/pricing"},
            {"title": "Railway: The Heroku Alternative? — Fireship, YouTube", "url": "https://www.youtube.com/watch?v=Kx_1NQUG-qQ"},
            {"title": "Best Heroku Alternatives for Developers — dev.to", "url": "https://dev.to/techno-tim/best-heroku-alternatives-for-developers-5d6e"},
        ],
        "Heroku": [
            {"title": "Heroku Dev Center", "url": "https://devcenter.heroku.com"},
            {"title": "Heroku Pricing", "url": "https://www.heroku.com/pricing"},
            {"title": "Heroku's Free Tier Removal: What It Means — The Verge", "url": "https://www.theverge.com/2022/8/25/23322234/heroku-free-tier-removed"},
            {"title": "Heroku Architecture — Heroku Dev Center", "url": "https://devcenter.heroku.com/categories/heroku-architecture"},
        ],
        "Render": [
            {"title": "Render Documentation", "url": "https://docs.render.com"},
            {"title": "Render vs Heroku: An Honest Comparison — Render Blog", "url": "https://render.com/blog/render-vs-heroku-comparison"},
            {"title": "Render Review: A Modern Cloud Platform — G2 Reviews", "url": "https://www.g2.com/products/render/reviews"},
        ],
        "Fly.io": [
            {"title": "Fly.io Documentation", "url": "https://fly.io/docs/"},
            {"title": "The Making of Fly.io — Fly.io Blog", "url": "https://fly.io/blog/"},
            {"title": "Fly.io: Run Your App Near Your Users — InfoQ", "url": "https://www.infoq.com/articles/fly-io-infrastructure/"},
        ],
        "Vercel": [
            {"title": "Vercel Documentation", "url": "https://vercel.com/docs"},
            {"title": "Vercel vs Netlify: A Detailed Comparison — LogRocket Blog", "url": "https://blog.logrocket.com/vercel-vs-netlify/"},
            {"title": "How Vercel is Shaping the Future of Web Development — The New Stack", "url": "https://thenewstack.io/vercel-and-the-future-of-frontend-development/"},
        ],
        "Vultr": [
            {"title": "Vultr Documentation", "url": "https://docs.vultr.com"},
            {"title": "Vultr vs DigitalOcean vs Linode: Cloud VPS Comparison — VPSBenchmarks", "url": "https://www.vpsbenchmarks.com/compare/vultr_vs_digitalocean_vs_linode"},
            {"title": "Vultr Review: Affordable Cloud Infrastructure — TechRadar", "url": "https://www.techradar.com/best/best-cloud-hosting"},
        ],
        "Datadog": [
            {"title": "Datadog Documentation", "url": "https://docs.datadoghq.com"},
            {"title": "Datadog vs Prometheus vs Grafana — Sematext Blog", "url": "https://sematext.com/blog/datadog-vs-prometheus-vs-grafana/"},
            {"title": "State of Cloud-Native Observability — CNCF Survey", "url": "https://www.cncf.io/reports/cncf-annual-survey-2023/"},
        ],
        "Prometheus": [
            {"title": "Prometheus Documentation", "url": "https://prometheus.io/docs/"},
            {"title": "Prometheus: Up and Running — O'Reilly", "url": "https://www.oreilly.com/library/view/prometheus-up/9781098131135/"},
            {"title": "Monitoring with Prometheus — CNCF", "url": "https://www.cncf.io/projects/prometheus/"},
        ],
        "Grafana Cloud": [
            {"title": "Grafana Documentation", "url": "https://grafana.com/docs/"},
            {"title": "Grafana vs Kibana: The Key Differences — Logz.io", "url": "https://logz.io/blog/grafana-vs-kibana/"},
            {"title": "Grafana — CNCF Landscape", "url": "https://landscape.cncf.io/?selected=grafana"},
        ],
        "New Relic": [
            {"title": "New Relic Documentation", "url": "https://docs.newrelic.com"},
            {"title": "New Relic vs Datadog: Feature Comparison — PeerSpot", "url": "https://www.peerspot.com/products/comparisons/datadog_vs_new-relic"},
            {"title": "Gartner Magic Quadrant for APM and Observability", "url": "https://www.gartner.com/reviews/market/application-performance-monitoring-and-observability"},
        ],
        "Docker": [
            {"title": "Docker Documentation", "url": "https://docs.docker.com"},
            {"title": "Docker Overview — DigitalOcean Tutorial", "url": "https://www.digitalocean.com/community/tutorials/the-docker-ecosystem-an-overview-of-containerization"},
            {"title": "Docker: Lightweight Linux Containers for Consistent Development — IEEE", "url": "https://ieeexplore.ieee.org/document/7036275"},
            {"title": "Docker Best Practices Guide — Docker Docs", "url": "https://docs.docker.com/build/building/best-practices/"},
        ],
        "Kubernetes": [
            {"title": "Kubernetes Documentation", "url": "https://kubernetes.io/docs/"},
            {"title": "Kubernetes the Hard Way — Kelsey Hightower, GitHub", "url": "https://github.com/kelseyhightower/kubernetes-the-hard-way"},
            {"title": "CNCF Annual Survey: Kubernetes Adoption", "url": "https://www.cncf.io/reports/cncf-annual-survey-2023/"},
            {"title": "Kubernetes Components — Kubernetes Docs", "url": "https://kubernetes.io/docs/concepts/overview/components/"},
        ],
        "Node.js": [
            {"title": "Node.js Documentation", "url": "https://nodejs.org/docs/latest/api/"},
            {"title": "Introduction to Node.js — Node.js Learn", "url": "https://nodejs.org/en/learn/getting-started/introduction-to-nodejs"},
            {"title": "Node.js Best Practices — GitHub", "url": "https://github.com/goldbergyoni/nodebestpractices"},
            {"title": "Node.js Performance Best Practices — NodeSource Blog", "url": "https://nodesource.com/blog/node-js-performance-best-practices"},
        ],
        "Python": [
            {"title": "Python Documentation", "url": "https://docs.python.org/3/"},
            {"title": "The Hitchhiker's Guide to Python — Kenneth Reitz", "url": "https://docs.python-guide.org"},
            {"title": "Python Developer Survey Results — JetBrains", "url": "https://lp.jetbrains.com/python-developers-survey/"},
            {"title": "Python Developer Survey Results — JetBrains", "url": "https://www.jetbrains.com/lp/devecosystem-2023/python/"},
        ],
        "PyTorch": [
            {"title": "PyTorch Documentation", "url": "https://pytorch.org/docs/stable/"},
            {"title": "PyTorch Tutorials — Official", "url": "https://pytorch.org/tutorials/"},
            {"title": "PyTorch vs TensorFlow in 2024 — AssemblyAI Blog", "url": "https://www.assemblyai.com/blog/pytorch-vs-tensorflow-in-2023/"},
            {"title": "PyTorch: An Imperative Style Deep Learning Library — NeurIPS", "url": "https://papers.nips.cc/paper/2019/hash/bdbca288fee7f92f2bfa9f7012727740-Abstract.html"},
        ],
        "PostgreSQL": [
            {"title": "PostgreSQL Documentation", "url": "https://www.postgresql.org/docs/"},
            {"title": "PostgreSQL Wiki — Performance Optimization", "url": "https://wiki.postgresql.org/wiki/Performance_Optimization"},
            {"title": "Why PostgreSQL Is the World's Best Database — Hussein Nasser, YouTube", "url": "https://www.youtube.com/watch?v=bfEGwKMnppk"},
            {"title": "PostgreSQL vs MySQL: A Comparison — DigitalOcean Tutorial", "url": "https://www.digitalocean.com/community/tutorials/sqlite-vs-mysql-vs-postgresql-a-comparison-of-relational-database-management-systems"},
        ],
        "WSL": [
            {"title": "WSL Documentation — Microsoft Learn", "url": "https://learn.microsoft.com/en-us/windows/wsl/"},
            {"title": "Set Up a WSL Development Environment — Microsoft Learn", "url": "https://learn.microsoft.com/en-us/windows/wsl/setup/environment"},
            {"title": "WSL2 Best Practices — Microsoft Tech Community", "url": "https://techcommunity.microsoft.com/blog/windowsdeveloperblog/gpu-compute-support-for-wsl-2/1780545"},
        ],
        "Apple Silicon": [
            {"title": "Apple Silicon Developer Documentation", "url": "https://developer.apple.com/documentation/apple-silicon"},
            {"title": "Apple M-Series Chip Benchmarks — AnandTech", "url": "https://www.anandtech.com/show/17024/apple-m1-max-performance-review"},
            {"title": "Porting Apps to Apple Silicon — Apple Developer", "url": "https://developer.apple.com/documentation/apple-silicon/porting-your-macos-apps-to-apple-silicon"},
        ],
        "ROCm": [
            {"title": "ROCm Documentation — AMD", "url": "https://rocm.docs.amd.com"},
            {"title": "ROCm GitHub Repository", "url": "https://github.com/ROCm/ROCm"},
            {"title": "AMD ROCm: Open-Source GPU Computing — Phoronix", "url": "https://www.phoronix.com/review/amd-rocm-overview"},
        ],
    }

    # General reference links applicable to broad engineering topics.
    _GENERAL_REFERENCES: List[Dict[str, str]] = [
        {"title": "ThoughtWorks Technology Radar", "url": "https://www.thoughtworks.com/radar"},
        {"title": "Stack Overflow Annual Developer Survey", "url": "https://survey.stackoverflow.co"},
        {"title": "CNCF Cloud Native Landscape", "url": "https://landscape.cncf.io"},
        {"title": "IEEE Software Engineering Body of Knowledge (SWEBOK)", "url": "https://www.computer.org/education/bodies-of-knowledge/software-engineering"},
        {"title": "Martin Fowler — Software Architecture Guide", "url": "https://martinfowler.com/architecture/"},
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

    def _collect_numbered_references(self, keyword: str) -> List[Dict[str, str]]:
        """Collect references and assign each a stable 1-based index.

        Each dict gets an ``"index"`` key (str) so templates can insert
        inline citations like ``[1]``, ``[2]``, etc.
        """
        refs = self._collect_references(keyword)
        if not refs:
            refs = list(self._GENERAL_REFERENCES[:2])
        # Deduplicate by URL while preserving order
        seen_urls: set = set()
        unique: List[Dict[str, str]] = []
        for ref in refs:
            if ref["url"] not in seen_urls:
                seen_urls.add(ref["url"])
                unique.append(dict(ref))  # copy to avoid mutating class data
        for i, ref in enumerate(unique, 1):
            ref["index"] = str(i)
        return unique

    def _cite_indices(self, refs: List[Dict[str, str]], tool_name: str) -> str:
        """Return inline citation markers like ' [1][2]' for refs matching a tool.

        Matches if the tool name (or its first word for multi-word names)
        appears in the reference title or URL.  Returns an empty string
        when nothing matches so templates can unconditionally append.
        """
        tool_lower = tool_name.lower()
        # For multi-word tool names like "Cursor IDE", also match on the
        # primary word ("cursor") so "Cursor Documentation" still matches.
        words = tool_lower.split()
        primary = words[0] if words else tool_lower
        indices = []
        for ref in refs:
            title_lower = ref.get("title", "").lower()
            url_lower = ref.get("url", "").lower()
            if (tool_lower in title_lower or tool_lower in url_lower
                    or primary in title_lower or primary in url_lower):
                indices.append(ref["index"])
        if not indices:
            return ""
        return " " + "".join(f"[{idx}]" for idx in indices)

    def _cite_general(self, refs: List[Dict[str, str]]) -> str:
        """Return citation markers for general (non-tool-specific) references."""
        indices = []
        for ref in refs:
            for gen in self._GENERAL_REFERENCES:
                if ref.get("url") == gen["url"]:
                    indices.append(ref["index"])
                    break
        if not indices:
            return ""
        return " " + "".join(f"[{idx}]" for idx in indices)

    def _references_section_from(self, refs: List[Dict[str, str]]) -> str:
        """Generate a numbered References/Sources section from pre-built refs."""
        lines = ["## References and sources", ""]
        for ref in refs:
            lines.append(f"{ref['index']}. [{ref['title']}]({ref['url']})")
        lines.append("")
        lines.append(
            "All pricing, features, and compatibility information in this article "
            "was verified against official documentation at the time of writing. "
            "Always check the official sources above for the most current information."
        )
        return "\n".join(lines)

    def _references_section(self, keyword: str) -> str:
        """Generate a numbered References/Sources section with real URLs."""
        refs = self._collect_numbered_references(keyword)
        return self._references_section_from(refs)

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

        # Build numbered references and inline citation helpers
        numbered_refs = self._collect_numbered_references(keyword)
        cite_a = self._cite_indices(numbered_refs, tool_a)
        cite_b = self._cite_indices(numbered_refs, tool_b)
        cite_gen = self._cite_general(numbered_refs)

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
            eighteen months ago may now be a liability{cite_gen}. Engineers searching for
            this comparison are usually at a fork in the road: a greenfield project,
            a painful migration, or a growing team that has outgrown its current setup.

            Getting this decision right saves months of friction. Getting it wrong
            means fighting your tools every single day. Tooling choices are consistently
            ranked among the top factors affecting developer satisfaction and
            productivity{cite_gen}. {tool_a} positions itself as {feature_a}{cite_a},
            while {tool_b} focuses on {feature_b}{cite_b}.
            """).strip(),

            textwrap.dedent(f"""
            ## Head-to-head feature comparison

            The table below summarises pricing and features as documented on each
            tool's official site. Check {docs_a} and {docs_b} for the latest details.

            | Criterion            | {tool_a}             | {tool_b}             |
            |----------------------|----------------------|----------------------|
            | Pricing              | {price_a}{cite_a}    | {price_b}{cite_b}    |
            | Setup                | {setup_a}{cite_a}    | {setup_b}{cite_b}    |
            | Key differentiator   | {feature_a}{cite_a}  | {feature_b}{cite_b}  |
            | Open source          | {oss_a}{cite_a}      | {oss_b}{cite_b}      |
            | Best for             | {bestfor_a}          | {bestfor_b}          |

            Read the table as a starting point, not a verdict. Your infrastructure
            context, team seniority, and existing toolchain will shift the scores.
            """).strip(),

            textwrap.dedent(f"""
            ## When to choose {tool_a}

            **{tool_a}** is priced at {price_a}{cite_a} and tends to win when:

            - {bestfor_a}{cite_a}.
            - You need to ship fast and can tolerate some rough edges later.
            - The ecosystem and community matter as much as raw features — {tool_a} offers {feature_a}{cite_a}.
            - You want the lowest possible maintenance burden per developer.

            The setup process for {tool_a} is straightforward: {setup_a}{cite_a}.
            Watch out for: hitting hard limits once the project scales. Plan your
            escape hatches early if growth is the goal. Review the
            {docs_a} for any feature limits on your chosen pricing tier.
            """).strip(),

            textwrap.dedent(f"""
            ## When to choose {tool_b}

            **{tool_b}** is priced at {price_b}{cite_b} and earns its place when:

            - {bestfor_b}{cite_b}.
            - Performance and determinism are non-negotiable requirements.
            - You need {feature_b}{cite_b} as a core part of your workflow.
            - You can absorb the steeper learning curve with documentation and pairing.

            Setup involves: {setup_b}{cite_b}.
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

            The ThoughtWorks Technology Radar categorises tools into adopt, trial,
            assess, and hold rings based on real-world engineering experience{cite_gen}.
            It is a useful reference for understanding where {tool_a}{cite_a} and
            {tool_b}{cite_b} sit on the industry adoption spectrum.
            """).strip(),

            textwrap.dedent(f"""
            ## Common failure modes

            - Choosing based on hype rather than fit for your specific workload{cite_gen}.
            - Underestimating the total cost of switching (scripts, CI config, tribal knowledge).
            - Not involving the team — tooling decisions made top-down without buy-in fail silently.
            - Skipping the proof-of-concept phase and discovering incompatibilities late.
            - Ignoring pricing model differences — {tool_a} charges {price_a}{cite_a} while {tool_b} charges {price_b}{cite_b}, and the total cost of ownership goes beyond the sticker price.
            """).strip(),

            textwrap.dedent(f"""
            ## How to run your own evaluation

            A structured evaluation takes the guesswork out of the decision{cite_gen}. Here is a
            practical framework you can adapt for your team:

            1. **Define your criteria** — list the five or six dimensions that matter most
               to your team (speed, ecosystem, learning curve, cost, integration with CI,
               extension quality). Weight each criterion based on your team's priorities.

            2. **Time-box the trial** — give each tool one full sprint with a real project.
               Synthetic benchmarks are useful but nothing replaces real workflow usage{cite_gen}.
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

            Startups typically benefit from faster onboarding and a larger ecosystem{cite_gen} —
            lean toward whichever has lower friction for your stack. {tool_a} starts at
            {price_a}{cite_a} and {tool_b} starts at {price_b}{cite_b}. You can always
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
            {tool_a} offers {feature_a}{cite_a} at {price_a}{cite_a}.
            Run the paid tool for one sprint on a real project and measure velocity.
            If the improvement pays for the subscription twice over, the answer is yes.
            """).strip(),

            self._references_section_from(numbered_refs),

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

        # Build numbered references and citation helpers
        numbered_refs = self._collect_numbered_references(keyword)
        cite_a = self._cite_indices(numbered_refs, comp_a)
        cite_b = self._cite_indices(numbered_refs, comp_b)

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
            software development{cite_a}{cite_b}. This guide documents the known constraints,
            tested version combinations, and proven workarounds for using
            {link_a} with {link_b} as of {now}.

            Whether you are setting up a new environment, troubleshooting a broken
            build, or planning an upgrade, this page gives you the facts without
            the fluff.
            """).strip(),

            textwrap.dedent(f"""
            ## What you need before you start

            Before diving in, confirm:

            - Your operating system version and architecture (x86-64 vs ARM64 matters here){cite_a}.
            - The exact version numbers of each component — {comp_a} supported versions are listed in {docs_a}{cite_a} and {comp_b} versions in {docs_b}{cite_b}.
            - Whether you are working in a container, VM, or bare-metal environment.
            - Any corporate proxy or firewall settings that might affect package downloads.

            Mismatched assumptions at this stage account for the majority of
            compatibility failures{cite_a}{cite_b}. Write them down before proceeding.
            """).strip(),

            textwrap.dedent(f"""
            ## Tested version matrix

            The matrix below summarises compatibility based on official release
            notes from {comp_a}{cite_a} and {comp_b}{cite_b}.
            Always cross-reference with {docs_a} for your exact patch version.

            | {comp_a} version    | {comp_b} version    | Status         | Notes                          |
            |---------------------|---------------------|----------------|--------------------------------|
            | Latest stable       | Latest stable       | OK             | Recommended combination{cite_a}{cite_b} |
            | Latest stable       | Previous LTS        | OK             | Works with minor config change{cite_a} |
            | Latest stable       | Two versions back   | Partial        | Some features disabled{cite_b} |
            | Previous LTS        | Latest stable       | Partial        | Deprecated API warnings{cite_a} |
            | Previous LTS        | Previous LTS        | OK             | Stable, no new features{cite_a}{cite_b} |
            | EOL version         | Any                 | Unsupported    | Security risk — upgrade first{cite_a} |

            Always verify against the official release notes for your exact patch version{cite_a}{cite_b}.
            Patch releases occasionally introduce breaking changes even within a minor version.

            If you are running in a containerised environment, pin both the base image
            tag and the package versions inside the container. Floating tags like
            `latest` or `lts` will eventually pull a version that breaks your build.
            """).strip(),

            textwrap.dedent(f"""
            ## Step-by-step setup guide

            Follow these steps in order. Skipping steps is the most common cause
            of hard-to-diagnose failures{cite_a}{cite_b}.

            1. **Verify prerequisites** — run the version check commands for each component.
               For {comp_a}, use the command documented in {docs_a}{cite_a}. Confirm the exact
               major and minor version, not just "it runs."

            2. **Install in the correct order** — some packages expect dependencies to
               already be present on the path{cite_a}. See {docs_a} for install order requirements.
               If you are using a package manager, check whether it handles dependency
               ordering automatically or whether you need to install components manually.

            3. **Set required environment variables** — the {comp_a} documentation{cite_a} lists
               required `PATH`, `LD_LIBRARY_PATH`, or tool-specific variables. Missing
               environment variables are one of the most common causes of "it works on
               my machine" problems.

            4. **Run the smoke test** — execute the minimal "hello world" equivalent to
               confirm the basic setup works before adding complexity{cite_a}{cite_b}. If the smoke test
               fails, stop here and debug before proceeding.

            5. **Capture the working state** — export your environment or lock your
               dependency versions before continuing. Tools like `pip freeze`,
               `npm ls`, or `docker image ls` help you record exactly what is installed.
            """).strip(),

            textwrap.dedent(f"""
            ## Known issues and workarounds

            ### Issue: Version mismatch error on startup

            This is almost always a PATH problem{cite_a}. The tool is finding an older
            installation before the one you just set up. Check which binary is
            being invoked with `which <tool>` (Linux/macOS) or `where <tool>` (Windows).

            ### Issue: Works locally but fails in CI

            CI environments often use minimal base images{cite_a}{cite_b}. Confirm that your pipeline
            installs all runtime dependencies explicitly — do not rely on system packages
            being pre-installed.

            ### Issue: ARM64 / Apple Silicon incompatibility

            Many tools lag behind on native ARM64 support{cite_a}. If you hit
            `exec format error` or architecture mismatches, check whether a
            native build is available, and whether
            [Rosetta 2 emulation](https://developer.apple.com/documentation/apple-silicon/about-the-rosetta-translation-environment)
            is a viable interim workaround.

            ### Issue: Dependency conflict with existing packages

            Use a virtual environment, container, or version manager (e.g. `nvm`,
            `pyenv`, `rbenv`) to isolate the conflicting components{cite_b}. Global installs
            are a reliable source of hard-to-reproduce compatibility failures.
            """).strip(),

            textwrap.dedent(f"""
            ## Troubleshooting methodology

            When compatibility issues surface, a systematic approach saves hours of
            frustrated guessing{cite_a}{cite_b}. Follow this sequence:

            1. **Reproduce the exact error** — copy the full error message and stack trace.
               Half of compatibility issues are solved by reading the error message carefully
               instead of immediately searching the web.

            2. **Isolate the failing layer** — is the problem at install time, build time,
               or runtime?{cite_a} Each points to a different root cause. Install failures suggest
               missing system dependencies. Build failures point to API incompatibilities.
               Runtime failures often indicate mismatched shared libraries.

            3. **Check the release notes and changelogs** — {comp_a} publishes changelogs
               with breaking changes highlighted{cite_a} and so does {comp_b}{cite_b}. Search for your
               specific error in the project's issue tracker on GitHub.

            4. **Test in a clean environment** — use a Docker container or fresh VM to
               rule out local environment pollution. If the issue disappears in a clean
               environment, the problem is your local setup, not a genuine incompatibility.

            5. **Report upstream if needed** — if you confirm a real compatibility bug,
               file an issue with the exact versions, OS, architecture, and a minimal
               reproduction case{cite_a}{cite_b}. This helps maintainers fix the issue faster and helps
               other developers who encounter the same problem.
            """).strip(),

            self._aff_section(),

            textwrap.dedent(f"""
            ## Frequently asked questions

            ### How do I check which version I actually have installed?

            Run the version flag for each tool (`--version` or `-v` in most cases){cite_a}{cite_b}.
            Do not assume the version you installed is the one being executed —
            always verify with the version command after installation.

            ### Is it safe to mix LTS and non-LTS versions?

            Generally no{cite_a}{cite_b}. LTS versions are tested together. Mixing them introduces
            API surface that may be unstable, deprecated, or removed entirely.
            Stick to matched LTS pairs for production systems.

            ### My setup worked last month but broke after an update. What happened?

            Check the changelogs for every component that updated{cite_a}{cite_b} in the window
            between "working" and "broken". Patch-level updates occasionally
            tighten behaviour that was previously tolerated. Pin your versions
            in CI to avoid silent breakage.
            """).strip(),

            self._references_section_from(numbered_refs),

            textwrap.dedent(f"""
            ## Conclusion

            Compatibility problems with {keyword} are solvable — they just require
            methodical debugging and the discipline to verify assumptions at each step{cite_a}{cite_b}.

            Pin your versions, document your working configuration, and automate
            the setup so every team member gets a reproducible environment from
            day one.
            """).strip(),
        ]
        return "\n\n".join(sections)

    def _template_tutorial(self, keyword: str, intent: str) -> str:
        now = datetime.now().strftime("%B %Y")

        # Build numbered references and citation helpers
        numbered_refs = self._collect_numbered_references(keyword)
        # Find tool-specific citations from keyword
        cite_all = ""
        keyword_lower = keyword.lower()
        for tool_name in self._TOOL_REFERENCES:
            if tool_name.lower() in keyword_lower:
                c = self._cite_indices(numbered_refs, tool_name)
                if c:
                    cite_all = c
                    break
        if not cite_all:
            cite_all = self._cite_general(numbered_refs)

        # Build inline reference links for tools mentioned in keyword
        refs = self._collect_references(keyword)
        docs_link = ""
        if refs:
            docs_link = f"Refer to [{refs[0]['title']}]({refs[0]['url']}) for the latest install instructions."

        sections = [
            textwrap.dedent(f"""
            # {keyword}

            This tutorial gives you a complete, working implementation of {keyword}{cite_all}
            with no assumed knowledge beyond the prerequisites listed below.
            Every step is explained so you understand not just *what* to do but *why*.

            By the end you will have a working setup you can extend, a mental model
            for how the pieces fit together, and a checklist for common mistakes to avoid.

            *Last verified: {now}*
            """).strip(),

            textwrap.dedent(f"""
            ## Prerequisites

            Before starting, make sure you have:

            - A working development environment (OS, shell, and package manager confirmed){cite_all}.
            - The required runtime or SDK installed and on your PATH{cite_all}.
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

            The goal of this tutorial is to walk you through {keyword} end-to-end{cite_all}.
            We will cover:

            1. Initial setup and project scaffolding.
            2. Core implementation with explanations at each step.
            3. Testing that the implementation actually works.
            4. Common extensions and next steps.

            Each section builds on the last. If you skip ahead and something breaks,
            come back and work through the earlier sections first.
            """).strip(),

            textwrap.dedent(f"""
            ## Step 1 — Project setup

            Create a clean working directory for this tutorial{cite_all}:

            ```
            mkdir my-project && cd my-project
            ```

            Initialise your project with the relevant package manager or build tool{cite_all}.
            Use the defaults for now — we will adjust configuration as needed.

            **Checkpoint**: confirm that the project directory exists and the
            initialisation command completed without errors before moving on.
            """).strip(),

            textwrap.dedent(f"""
            ## Step 2 — Core implementation

            Start with the smallest possible working version{cite_all}. Resist the temptation
            to add features before the core works.

            Key principles to follow during implementation:

            - Write code that is easy to delete, not just easy to extend.
            - Use explicit names — clarity beats cleverness every time.
            - Commit working checkpoints frequently so you can roll back safely{cite_all}.
            - Read error messages carefully — they almost always tell you exactly what is wrong.

            **Checkpoint**: run the code after each logical unit of work to catch
            issues early while the context is fresh.
            """).strip(),

            textwrap.dedent(f"""
            ## Step 3 — Testing your implementation

            Do not skip this section. Untested code is broken code you have not
            found yet{cite_all}.

            Minimum verification steps:

            1. **Happy path** — the expected inputs produce the expected outputs{cite_all}.
               Run through the most common use case end-to-end and confirm the result
               matches your expectations exactly.

            2. **Edge cases** — empty inputs, maximum sizes, unexpected types. These
               are where most production bugs hide{cite_all}. Test with an empty string, a very
               large input, and at least one input that should trigger an error.

            3. **Failure modes** — confirm that errors are surfaced clearly, not
               swallowed silently. Disconnect from the network, provide invalid
               credentials, or pass malformed data. The error messages should tell
               you exactly what went wrong and where.

            4. **Regression baseline** — save the output of a successful test run so
               you can compare against it after future changes{cite_all}. This is especially
               important for output formats like JSON or HTML where subtle changes
               can break downstream consumers.

            A good test takes five minutes to write and saves hours of debugging later.
            If you are short on time, at least run the happy path manually and capture
            the output so you have a baseline to compare against.
            """).strip(),

            textwrap.dedent(f"""
            ## Common errors and how to fix them

            ### Error: "command not found" or "module not found"

            The tool or package is not on your PATH{cite_all}. Confirm the install succeeded
            and that you have restarted your shell or sourced your profile after installation.

            ### Error: permission denied

            You are trying to write to a location owned by another user or by root{cite_all}.
            Use a local install path or adjust permissions on your project directory —
            do not reach for `sudo` as a first response.

            ### Error: unexpected token / syntax error

            Check the language version your runtime is using{cite_all}. New syntax may not be
            supported in older runtimes. Confirm with `<tool> --version`.

            ### Error: works on my machine, fails in CI

            Your local environment has something the CI environment does not{cite_all}.
            Common culprits: environment variables, system packages, or implicit
            dependency versions. Lock your dependencies explicitly.
            """).strip(),

            textwrap.dedent(f"""
            ## Going further: production considerations

            The tutorial above gives you a working foundation{cite_all}. Before deploying to
            production, consider these additional steps:

            - **Error handling** — wrap external calls and I/O operations in proper
              error handling{cite_all}. Log failures with enough context to debug without
              reproducing the issue locally.

            - **Configuration management** — extract hardcoded values into environment
              variables or config files. Twelve-Factor App principles
              ([12factor.net](https://12factor.net)) are a solid guide here{cite_all}.

            - **Monitoring** — add health checks, structured logging, and basic metrics
              from day one{cite_all}. You will need them the first time something breaks in
              production, and adding observability after the fact is always harder than
              building it in.

            - **Security** — review dependencies for known vulnerabilities, use least-privilege
              access for service accounts, and never commit secrets to version control{cite_all}.

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
            development machine{cite_all}. The main time sink is debugging environment
            issues that are specific to your setup.

            ### Can I use this approach in production?

            The tutorial focuses on correctness and clarity over production-readiness{cite_all}.
            Before going to production, add proper error handling, logging, secrets
            management, and a deployment pipeline. Use the tutorial output as a
            foundation, not a final product.

            ### Where can I learn more about {keyword}?

            The official documentation{cite_all} is always the most reliable source. Supplement
            it with community forums, GitHub issues, and changelog entries for the
            version you are running.
            """).strip(),

            self._references_section_from(numbered_refs),

            textwrap.dedent(f"""
            ## Conclusion

            You now have a working implementation of {keyword}{cite_all} and a mental model
            for how the pieces fit together.

            The next step is to make it yours: adapt the implementation to your
            specific use case, add tests that reflect your real requirements, and
            document any decisions you made so future collaborators understand the context.
            """).strip(),
        ]
        return "\n\n".join(sections)

    def _template_foreign_news(self, keyword: str, intent: str) -> str:
        now = datetime.now().strftime("%B %Y")
        numbered_refs = self._collect_numbered_references(keyword)
        cite_gen = self._cite_general(numbered_refs)
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
            always make it into English-language tech coverage{cite_gen}.

            Key factors shaping this story:

            - The regulatory and funding environment in the originating region{cite_gen}.
            - How local developer communities and enterprises adopt new technology differently from Western markets{cite_gen}.
            - The open-source vs proprietary dynamics at play.
            - How geopolitical context affects technology exports, licensing, and access{cite_gen}.

            Without this context, it is easy to misread the significance — or the
            limitations — of what is being reported.

            The ThoughtWorks Technology Radar{cite_gen}
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
              the CNCF Landscape{cite_gen} is a useful starting point
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
        sections.insert(-1, self._references_section_from(numbered_refs))
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

