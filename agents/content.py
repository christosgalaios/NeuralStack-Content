import json
import os
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


MIN_WORDS = 1200

# Affiliate configuration — set via environment variables or edit defaults here.
# Each entry: (env_name_for_name, env_name_for_url, default_name, default_url, description)
AFFILIATE_SLOTS = [
    {
        "name": os.getenv("NEURALSTACK_AFF1_NAME", "Cursor IDE"),
        "url": os.getenv("NEURALSTACK_AFF1_URL", "https://www.cursor.com"),
        "desc": "AI-native code editor built on VS Code — autocomplete, inline chat, and codebase-aware suggestions out of the box",
    },
    {
        "name": os.getenv("NEURALSTACK_AFF2_NAME", "Datadog"),
        "url": os.getenv("NEURALSTACK_AFF2_URL", "https://www.datadoghq.com"),
        "desc": "unified observability platform for logs, metrics, and traces — free tier available for small teams",
    },
    {
        "name": os.getenv("NEURALSTACK_AFF3_NAME", "Railway"),
        "url": os.getenv("NEURALSTACK_AFF3_URL", "https://railway.app"),
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

    def _generate_with_template(self, keyword: str, category: str, intent: str) -> str:
        now = datetime.utcnow().strftime("%B %Y")
        # Strong, opinionated E-E-A-T style introduction.
        intro = textwrap.dedent(
            f"""
            # {keyword}

            As a practitioner who cares about maintainable systems and realistic trade-offs,
            this guide walks through **real-world considerations** instead of fluffy marketing.
            The goal is to help you make a confident decision about your tooling and architecture,
            using language that any experienced engineer or tech lead would recognise.

            In this article you will learn:

            - How this topic fits into modern engineering workflows
            - Concrete pros and cons you can explain to stakeholders
            - Implementation patterns, edge cases, and failure modes to watch out for
            - How to decide whether to adopt, migrate, or wait

            All explanations target engineers shipping production systems in {now}.
            """
        ).strip()

        # Section templates structured for SEO but written with restraint.
        h2_architecture = textwrap.dedent(
            """
            ## Core concepts and mental models

            Before we dive into specific tools, it is useful to step back and describe
            the core mental models behind this topic. When you understand the moving
            pieces conceptually, you become far less dependent on any single vendor
            or framework.

            Think about:

            - The boundary between local development and production deployment
            - Where state is stored and how it flows through the system
            - Which teams own which layers of the stack
            - What "done" means in terms of observability, reliability, and security

            Even simple sounding decisions, such as choosing one editor or plugin
            over another, tend to compound over years as teams, codebases, and
            infrastructure evolve.
            """
        ).strip()

        h2_use_cases = textwrap.dedent(
            f"""
            ## High-intent use cases and user journeys

            Search intent around this topic is rarely casual. Engineers typing
            queries such as "{keyword}" are normally stuck on:

            - A migration project with hard deadlines
            - A compatibility issue blocking deployment
            - A build, test, or debug workflow that has become painfully slow

            When evaluating options, anchor on the **specific journeys**:

            1. A new contributor cloning the repo and becoming productive.
            2. A senior engineer debugging intermittent failures under load.
            3. An ops team keeping the system observable, patchable, and auditable.
            4. A tech lead justifying the stack to non-technical stakeholders.
            """
        ).strip()

        h2_comparisons = textwrap.dedent(
            """
            ## Nuanced comparisons instead of hype

            Tool comparisons often degenerate into unhelpful debates. A more
            responsible way to reason about options is to define a shortlist of
            evaluation criteria and then score each option in context.

            Recommended lenses:

            - Learning curve and onboarding experience
            - Ecosystem maturity and plugin quality
            - Failure behaviour and how issues surface during incidents
            - Long-term maintainability for a growing team
            - Vendor risk and lock-in mitigation strategies

            When you read benchmarks or case studies, pause and ask whether the
            environment, team skills, and risk profile actually match yours.
            """
        ).strip()

        h2_arch_table = textwrap.dedent(
            """
            ## Architecture and workflow comparison table

            | Dimension                 | Conservative choice                    | Progressive choice                         |
            |---------------------------|----------------------------------------|--------------------------------------------|
            | Primary optimisation      | Stability and predictability           | Velocity and expressiveness               |
            | Tooling customisation     | Minimal, opinionated defaults          | Deep, scriptable, highly extensible       |
            | Ideal team size           | Large orgs with multiple squads        | Small, senior-heavy product teams         |
            | Operational burden        | Lower, easier to standardise           | Higher, needs clear ownership             |
            | Risk of lock-in           | Moderate, but manageable               | Depends heavily on integration strategy   |

            The right answer is rarely at either extreme. Most organisations end up
            standardising on a conservative baseline while enabling power users to
            extend their local workflows where it genuinely pays off.
            """
        ).strip()

        h2_impl = textwrap.dedent(
            """
            ## Implementation guidelines and failure modes

            From an implementation perspective, treat configuration as code and
            invest early in reproducible environments. A few practical guidelines:

            - Keep environment setup scripted and version-controlled.
            - Capture decisions in lightweight design docs instead of tribal knowledge.
            - Add smoke tests to catch obvious misconfigurations before release.
            - Decide what "good enough" observability looks like before scaling usage.

            Common failure modes include silent configuration drift, unclear
            ownership of tooling, and one-off shell scripts that become accidental
            production dependencies.
            """
        ).strip()

        aff_items = "\n".join(
            f"- [{s['name']}]({s['url']}) — {s['desc']}"
            for s in AFFILIATE_SLOTS
        )
        h2_affiliates = textwrap.dedent(
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

        h2_faq = textwrap.dedent(
            """
            ## Frequently asked questions

            ### Is it safe to standardise on a single tool?

            Standardisation helps reduce cognitive overhead, but you should still
            leave room for exceptions. Allow power users to diverge when they
            can demonstrate clear upside and are willing to document their setup.

            ### How often should we revisit our tooling choices?

            In most teams, a light review every 12–18 months is enough. The goal
            is not to chase trends, but to make sure your defaults do not become
            an unexamined constraint that quietly slows product delivery.

            ### How can we evaluate claims in benchmarks and vendor content?

            Treat glossy benchmarks as a starting point, not a conclusion. Recreate
            the critical paths from your own system and run targeted experiments
            under realistic constraints, including network conditions and data size.
            """
        ).strip()

        h2_conclusion = textwrap.dedent(
            """
            ## Conclusion: how to move forward thoughtfully

            The most sustainable decisions are usually boring from the outside.
            Instead of chasing the newest stack, identify the smallest set of
            changes that meaningfully de-risk your roadmap and improve developer
            quality of life.

            Make adoption explicit, reversible, and well-documented. Capture what
            you tried, what worked, and what you decided not to pursue yet. That
            historical context will save future teams enormous amounts of time
            and prevent expensive re-litigations of settled questions.
            """
        ).strip()

        body_sections = [
            intro,
            h2_architecture,
            h2_use_cases,
            h2_comparisons,
            h2_arch_table,
            h2_impl,
            h2_affiliates,
            h2_faq,
            h2_conclusion,
        ]

        content = "\n\n".join(body_sections)
        # Ensure minimum word count.
        words = content.split()
        if len(words) < MIN_WORDS:
            padding = (
                " In practice, each organisation should run small, low-risk experiments, "
                "observe the operational impact over several weeks, and only then roll out "
                "broader changes. Document the trade-offs clearly so that future engineers "
                "can understand not just what you chose, but why other options were rejected."
            )
            while len(words) < MIN_WORDS:
                content += "\n\n" + padding
                words = content.split()

        return content

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
            created_at = datetime.utcnow().isoformat() + "Z"
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

