import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any


@dataclass
class Topic:
    id: str
    keyword: str
    category: str
    intent: str
    difficulty_score: float
    source: str
    created_at: str
    status: str = "new"  # new | drafted | published


class DiscoveryAgent:
    """
    Heuristic keyword discovery agent.

    This implementation is deliberately self-contained and uses no external APIs.
    It combines curated seed terms into long-tail, low-competition style phrases
    focused on:
      - DevTools comparisons
      - Micro-niche technical compatibility
      - Foreign tech news adaptation (JP/CN -> EN)
    """

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.topics_file = self.data_dir / "topics.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.topics_file.exists():
            self.topics_file.write_text("[]", encoding="utf-8")

    def _load_existing_topics(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.topics_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save_topics(self, topics: List[Dict[str, Any]]) -> None:
        self.topics_file.write_text(json.dumps(topics, indent=2), encoding="utf-8")

    def _generate_candidates(self) -> List[Topic]:
        # --- DevTools comparisons (permutations → many combinations) ---
        devtools = [
            "VS Code", "JetBrains Fleet", "Neovim", "Cursor IDE",
            "Zed editor", "GitHub Copilot CLI", "Sublime Text",
            "Helix editor", "Lapce", "Nova by Panic",
        ]
        audiences = [
            "full-stack developers",
            "Python backend engineers",
            "Rust developers",
            "data scientists",
            "DevOps engineers",
            "mobile developers",
            "frontend React developers",
        ]

        # --- Compatibility guides (combinatorial: technology × environment) ---
        compat_tech = [
            "Docker", "Podman", "PyTorch", "TensorFlow", "PostgreSQL",
            "MySQL 8", "Redis 7", "MongoDB 7", "Elasticsearch 8",
            "Node.js 22", "Bun runtime", "Deno 2", ".NET 9", "Go 1.23",
        ]
        compat_env = [
            "on Windows 11 ARM", "on Apple Silicon M3", "with WSL2 GPU passthrough",
            "with ROCm on AMD GPUs", "with CUDA 12.4", "on Raspberry Pi 5",
            "inside GitHub Codespaces", "on NixOS", "with Prisma ORM",
            "with Docker Compose v2", "with Kubernetes 1.30",
        ]

        # --- Foreign tech news hooks ---
        foreign_news_hooks = [
            "Japan dev community reaction",
            "Chinese open source ecosystem",
            "Tokyo startups using",
            "Shanghai AI labs testing",
            "CN cloud provider partnership",
            "Korean fintech engineering",
            "Shenzhen hardware-software integration",
            "Japanese enterprise Rust adoption",
            "Alibaba Cloud open source push",
            "ByteDance internal tooling",
        ]

        # --- How-to / tutorial guides (high search intent) ---
        howto_seeds = [
            "set up a CI/CD pipeline with GitHub Actions",
            "deploy a Python app to Railway from scratch",
            "configure Nginx reverse proxy with SSL",
            "set up PostgreSQL replication for high availability",
            "migrate from Heroku to self-hosted Docker",
            "monitor a Node.js app with Prometheus and Grafana",
            "set up Tailscale VPN for a dev team",
            "containerise a legacy Django app",
            "configure VS Code remote development over SSH",
            "automate database backups with cron and S3",
            "set up a monorepo with Turborepo",
            "deploy a static site with Cloudflare Pages",
            "configure ESLint and Prettier for a team",
            "set up Python type checking with mypy in CI",
            "build a CLI tool with Python and Click",
            # Affiliate-adjacent tutorials (Vultr + Railway only)
            "deploy a full-stack app to Railway with a PostgreSQL database",
            "set up Railway environment variables and secrets for production",
            "migrate a Node.js app from Heroku to Railway in under an hour",
            "connect a custom domain to a Railway deployment",
            "set up a Vultr VPS with Ubuntu and secure it for production",
            "deploy a Flask API on Vultr with Gunicorn and Nginx",
            "set up automated backups on Vultr object storage",
            "deploy a Redis cache on Vultr for a web application",
        ]

        topics: List[Topic] = []
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # DevTools comparisons — for each audience, pick ordered pairs
        for a in devtools:
            for b in devtools:
                if a >= b:  # avoid duplicates (A vs B == B vs A)
                    continue
                for audience in audiences:
                    keyword = f"{a} vs {b} for {audience}"
                    topic_id = (
                        f"devtools-{a.replace(' ', '').lower()}"
                        f"-{b.replace(' ', '').lower()}"
                        f"-{audience.replace(' ', '').lower()}"
                    )
                    topics.append(
                        Topic(
                            id=topic_id,
                            keyword=keyword,
                            category="devtools_comparison",
                            intent="Evaluate which tool to adopt for a specific workflow.",
                            difficulty_score=0.35,
                            source="heuristic-devtools",
                            created_at=now,
                        )
                    )

        # Micro-niche compatibility — cross tech × environment
        for tech in compat_tech:
            for env in compat_env:
                keyword = f"{tech} {env} compatibility guide"
                topic_id = (
                    f"compat-{tech.replace(' ', '').replace('.', '').lower()}"
                    f"-{env.replace(' ', '').replace('.', '').lower()}"
                )
                topics.append(
                    Topic(
                        id=topic_id,
                        keyword=keyword,
                        category="compatibility",
                        intent="Understand whether a stack combination is safe and supported.",
                        difficulty_score=0.28,
                        source="heuristic-compatibility",
                        created_at=now,
                    )
                )

        # Foreign tech news adaptation
        for hook in foreign_news_hooks:
            keyword = f"{hook} for global engineers (translated summary)"
            topic_id = f"news-{hook.replace(' ', '').replace('/', '').lower()}"
            topics.append(
                Topic(
                    id=topic_id,
                    keyword=keyword,
                    category="foreign_news",
                    intent="Learn what is happening in JP/CN tech ecosystems.",
                    difficulty_score=0.32,
                    source="heuristic-foreign-news",
                    created_at=now,
                )
            )

        # How-to / tutorial guides — high commercial intent
        for seed in howto_seeds:
            keyword = f"How to {seed} (step-by-step guide)"
            topic_id = f"howto-{seed.replace(' ', '-').lower()[:60]}"
            topics.append(
                Topic(
                    id=topic_id,
                    keyword=keyword,
                    category="tutorial",
                    intent="Follow a practical, step-by-step guide to accomplish a specific task.",
                    difficulty_score=0.30,
                    source="heuristic-howto",
                    created_at=now,
                )
            )

        # High-priority affiliate topics — score 0.10 so they are always
        # selected before generic content (lower score = selected first).
        # Only Vultr and Railway are actual affiliate partners.
        affiliate_seeds = [
            # Vultr — affiliate (cloud compute, VPS, bare metal, GPU)
            ("Vultr vs DigitalOcean: cloud hosting comparison for developers",
             "comparison", "Decide which cloud provider to use.", "priority-vultr-vs-digitalocean"),
            ("Vultr vs Linode: which cloud provider is better for developers in 2026",
             "comparison", "Compare Vultr and Linode for developer workloads.", "priority-vultr-vs-linode"),
            ("Vultr vs AWS Lightsail: simple cloud hosting comparison",
             "comparison", "Compare Vultr and AWS Lightsail for simplicity.", "priority-vultr-vs-aws-lightsail"),
            ("Vultr vs Hetzner: budget cloud hosting comparison for 2026",
             "comparison", "Compare affordable cloud providers.", "priority-vultr-vs-hetzner"),
            ("Best cheap VPS hosting for developers in 2026",
             "comparison", "Find the most affordable VPS for dev workloads.", "priority-best-cheap-vps-2026"),
            ("How to deploy a Django app on Vultr with Docker and Nginx",
             "guide", "Deploy a production Django app on Vultr.", "priority-vultr-django-deploy"),
            ("How to set up a Kubernetes cluster on Vultr from scratch",
             "guide", "Run Kubernetes on Vultr cloud.", "priority-vultr-k8s-setup"),
            ("Vultr GPU instances for machine learning: complete setup guide",
             "guide", "Run ML workloads on Vultr GPU instances.", "priority-vultr-gpu-ml-guide"),
            ("How to deploy a Node.js app on Vultr with PM2 and Nginx",
             "guide", "Deploy a production Node.js app on Vultr.", "priority-vultr-nodejs-deploy"),
            ("How to host WordPress on Vultr with Nginx and free SSL",
             "guide", "Set up WordPress hosting on Vultr.", "priority-vultr-wordpress-hosting"),
            ("Vultr bare metal vs cloud compute: when to use each",
             "comparison", "Choose between Vultr bare metal and cloud.", "priority-vultr-baremetal-vs-cloud"),
            ("Best cloud hosting for startups in 2026: Vultr vs AWS vs DigitalOcean",
             "comparison", "Choose cloud hosting for a startup.", "priority-best-cloud-startups-2026"),
            ("How to set up Docker on a Vultr VPS in 5 minutes",
             "guide", "Quick Docker setup on Vultr.", "priority-vultr-docker-setup"),
            ("Vultr review: affordable cloud infrastructure for developers",
             "review", "Evaluate Vultr for development workloads.", "priority-vultr-review-2026"),
            ("How to provision Vultr infrastructure with Terraform",
             "guide", "Automate Vultr infrastructure with IaC.", "priority-vultr-terraform-guide"),
            # Railway — affiliate (PaaS, deployment, hosting)
            ("Railway vs Heroku: the definitive platform comparison for 2026",
             "comparison", "Decide which PaaS to use for deployment.", "priority-railway-vs-heroku"),
            ("Railway vs Render vs Fly.io: cloud hosting comparison for developers",
             "comparison", "Decide which hosting platform to use.", "priority-railway-vs-render-fly"),
            ("Railway review: best Heroku alternative for Python and Node apps",
             "review", "Decide whether to migrate to Railway.", "priority-railway-review"),
            ("How to deploy a Python app to Railway from scratch (step-by-step guide)",
             "guide", "Deploy a Python app to Railway.", "priority-railway-python-deploy"),
            ("Railway vs Vercel vs Netlify: which platform for full-stack apps",
             "comparison", "Choose the right deployment platform.", "priority-railway-vs-vercel-netlify"),
            ("How to deploy a Next.js app on Railway with a PostgreSQL database",
             "guide", "Deploy full-stack Next.js on Railway.", "priority-railway-nextjs-deploy"),
            ("How to set up PostgreSQL on Railway for production apps",
             "guide", "Run production Postgres on Railway.", "priority-railway-postgres-setup"),
            ("How to deploy Docker containers on Railway",
             "guide", "Deploy containerised apps on Railway.", "priority-railway-docker-deploy"),
            ("Best platforms to deploy a side project in 2026",
             "comparison", "Find the easiest hosting for side projects.", "priority-best-side-project-hosting-2026"),
            ("How to migrate from Heroku to Railway: step-by-step guide",
             "guide", "Migrate apps from Heroku to Railway.", "priority-heroku-to-railway-migration"),
            ("Railway vs AWS for small teams: simplicity vs flexibility",
             "comparison", "Compare Railway and AWS for small teams.", "priority-railway-vs-aws-small-teams"),
            ("How to run scheduled cron jobs on Railway",
             "guide", "Set up background jobs on Railway.", "priority-railway-cron-jobs"),
            ("How to deploy a monorepo on Railway",
             "guide", "Deploy monorepo projects on Railway.", "priority-railway-monorepo-deploy"),
            # Cross-reference (Vultr + Railway together)
            ("Railway vs Vultr: PaaS vs IaaS for web app deployment",
             "comparison", "Understand when to use PaaS vs IaaS.", "priority-railway-vs-vultr"),
            ("Best cloud hosting stack for indie developers in 2026",
             "guide", "Build an affordable cloud stack.", "priority-best-cloud-stack-indie-2026"),
        ]
        for keyword, category, intent, slug in affiliate_seeds:
            topics.append(
                Topic(
                    id=slug,
                    keyword=keyword,
                    category=category,
                    intent=intent,
                    difficulty_score=0.10,
                    source="heuristic-affiliate-priority",
                    created_at=now,
                )
            )

        return topics

    def run(self) -> List[Dict[str, Any]]:
        existing = self._load_existing_topics()
        existing_ids = {t.get("id") for t in existing}

        candidates = self._generate_candidates()

        # Add any brand-new candidates to the pool (first run seeds all topics).
        for topic in candidates:
            if topic.id not in existing_ids:
                existing.append(asdict(topic))
                existing_ids.add(topic.id)

        # Select from unprocessed topics in the pool.
        # "new" = never touched; "selected" = picked previously but never drafted.
        available = [t for t in existing if t.get("status") in ("new", "selected")]
        selected = sorted(available, key=lambda t: t["difficulty_score"])[:5]

        selected_ids = {t["id"] for t in selected}
        for t in existing:
            if t["id"] in selected_ids:
                t["status"] = "selected"

        self._save_topics(existing)
        return selected


__all__ = ["DiscoveryAgent", "Topic"]

