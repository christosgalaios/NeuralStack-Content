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
        devtools = [
            "VS Code",
            "JetBrains Fleet",
            "Neovim",
            "Cursor IDE",
            "Zed editor",
            "GitHub Copilot CLI",
        ]
        comparisons = [
            "vs",
            "comparison",
            "for Python backend",
            "for Rust developers",
            "for data scientists",
        ]

        compatibility_seeds = [
            "Docker on Windows 11 ARM",
            "WSL2 GPU passthrough",
            "PyTorch with ROCm",
            "TensorRT with ONNX",
            "PostgreSQL with Prisma",
        ]

        foreign_news_hooks = [
            "Japan dev community reaction",
            "Chinese open source ecosystem",
            "Tokyo startups using",
            "Shanghai AI labs testing",
            "CN cloud provider partnership",
        ]

        topics: List[Topic] = []
        now = datetime.utcnow().isoformat() + "Z"

        # DevTools comparisons
        for a in devtools:
            for b in devtools:
                if a == b:
                    continue
                keyword = f"{a} vs {b} for full-stack developers"
                topic_id = f"devtools-{a.replace(' ', '').lower()}-{b.replace(' ', '').lower()}"
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

        # Micro-niche compatibility
        for base in compatibility_seeds:
            keyword = f"{base} detailed compatibility guide"
            topic_id = f"compat-{base.replace(' ', '').replace('/', '').lower()}"
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

        return topics

    def run(self) -> List[Dict[str, Any]]:
        existing = self._load_existing_topics()
        existing_ids = {t.get("id") for t in existing}

        candidates = self._generate_candidates()

        new_topics: List[Dict[str, Any]] = []
        for topic in candidates:
            if topic.id in existing_ids:
                continue
            new_topics.append(asdict(topic))
            existing.append(asdict(topic))

        # Heuristic filter for "low competition" style:
        # keep only a small number of new topics per run to avoid explosion.
        new_topics = sorted(new_topics, key=lambda t: t["difficulty_score"])[:5]
        # Update status for the selected ones only (rest remain in backlog for future runs).
        for t in existing:
            if t["id"] in {nt["id"] for nt in new_topics}:
                t["status"] = "selected"

        self._save_topics(existing)
        return new_topics


__all__ = ["DiscoveryAgent", "Topic"]

