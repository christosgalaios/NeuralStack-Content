import json
from dataclasses import dataclass, asdict
from datetime import datetime
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
        ]

        topics: List[Topic] = []
        now = datetime.utcnow().isoformat() + "Z"

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

