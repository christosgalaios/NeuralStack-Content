"""
TikTok Viral Content Generator — autonomous, zero-cost, fully offline.

Generates complete short-form video scripts optimised for TikTok virality.
Works entirely from curated templates and deterministic heuristics so the
pipeline runs in CI at no cost, just like the article agents.

Optionally forwards to a local Ollama model when NEURALSTACK_LLM_BACKEND=ollama.
"""

import hashlib
import json
import os
import random
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class TikTokScript:
    """A single ready-to-film TikTok video script."""
    id: str
    topic: str
    format_name: str              # e.g. "hot_take", "myth_bust", "tutorial"
    hook: str                     # First 1-3 seconds — the make-or-break line
    script_segments: List[Dict[str, str]]  # [{timing, text, visual_direction}]
    caption: str                  # Post caption / description
    hashtags: List[str]
    sound_suggestion: str         # Trending sound category / mood
    cta: str                      # Call to action
    estimated_duration_sec: int
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Viral format library — each format is a proven TikTok content pattern
# ---------------------------------------------------------------------------

VIRAL_FORMATS = {
    "hot_take": {
        "label": "Hot Take / Unpopular Opinion",
        "hook_templates": [
            "Unpopular opinion: {topic} is completely overrated.",
            "I'm gonna get hate for this, but {topic}...",
            "Nobody talks about the dark side of {topic}.",
            "Hot take: {topic} is NOT what you think.",
            "Stop doing {topic} wrong — here's the truth.",
        ],
        "structure": [
            {"timing": "0-3s", "role": "hook", "direction": "Face close to camera. Bold text overlay."},
            {"timing": "3-10s", "role": "setup", "direction": "Step back. Explain the mainstream take you disagree with."},
            {"timing": "10-25s", "role": "argument", "direction": "Walk and talk or use B-roll. 2-3 punchy reasons."},
            {"timing": "25-35s", "role": "proof", "direction": "Show evidence: screen recording, stat, or side-by-side."},
            {"timing": "35-45s", "role": "flip", "direction": "Acknowledge the counter-argument briefly — builds trust."},
            {"timing": "45-55s", "role": "cta", "direction": "Direct to camera. Ask for comments. Controversial question."},
        ],
        "sound_mood": "intense / dramatic buildup",
        "cta_templates": [
            "Comment your hottest {topic} take — let's debate.",
            "Am I wrong? Drop your opinion below.",
            "Follow for more takes that actually matter.",
        ],
    },
    "myth_bust": {
        "label": "Myth Busting",
        "hook_templates": [
            "STOP believing this about {topic}.",
            "This {topic} myth is ruining your workflow.",
            "Everyone gets {topic} wrong — here's proof.",
            "3 {topic} myths that are holding you back.",
            "The biggest lie about {topic}, debunked.",
        ],
        "structure": [
            {"timing": "0-3s", "role": "hook", "direction": "Big text: 'MYTH vs REALITY'. Dramatic zoom."},
            {"timing": "3-12s", "role": "myth_statement", "direction": "State the myth clearly. Use finger-count or list."},
            {"timing": "12-30s", "role": "debunk", "direction": "Break it down with evidence. Screen share or whiteboard."},
            {"timing": "30-40s", "role": "reality", "direction": "Show what actually works. Quick demo if possible."},
            {"timing": "40-50s", "role": "cta", "direction": "Ask: which myth surprised you most? Follow for part 2."},
        ],
        "sound_mood": "revelation / suspenseful then upbeat",
        "cta_templates": [
            "Which myth surprised you? Comment below.",
            "Save this before it gets buried in your feed.",
            "Part 2? Follow so you don't miss it.",
        ],
    },
    "tutorial": {
        "label": "Quick Tutorial / How-To",
        "hook_templates": [
            "Learn {topic} in under 60 seconds.",
            "Here's a {topic} trick nobody taught you.",
            "The fastest way to {topic} — watch this.",
            "{topic} tutorial that actually makes sense.",
            "You're overcomplicating {topic}. Do this instead.",
        ],
        "structure": [
            {"timing": "0-3s", "role": "hook", "direction": "Show end result first. Text: 'Here's how'."},
            {"timing": "3-8s", "role": "context", "direction": "Quick 1-sentence setup: who this is for."},
            {"timing": "8-15s", "role": "step_1", "direction": "Step 1 with screen recording or demo."},
            {"timing": "15-25s", "role": "step_2", "direction": "Step 2. Keep transitions snappy."},
            {"timing": "25-35s", "role": "step_3", "direction": "Step 3. Show the result building."},
            {"timing": "35-45s", "role": "result", "direction": "Final result reveal. Satisfying moment."},
            {"timing": "45-55s", "role": "cta", "direction": "Follow for more tutorials. Drop a comment."},
        ],
        "sound_mood": "upbeat / productivity lo-fi",
        "cta_templates": [
            "Save this for later — you'll need it.",
            "Follow for daily {topic} tips.",
            "What tutorial should I make next? Comment.",
        ],
    },
    "storytime": {
        "label": "Storytime / Personal Experience",
        "hook_templates": [
            "The time {topic} completely changed my perspective...",
            "I wasted 6 months on {topic} before I learned this.",
            "Story time: how {topic} almost cost me everything.",
            "Nobody warned me about this {topic} trap.",
            "What happened when I went all-in on {topic}...",
        ],
        "structure": [
            {"timing": "0-3s", "role": "hook", "direction": "Lean into camera. Start mid-story for tension."},
            {"timing": "3-12s", "role": "setup", "direction": "Set the scene. When, where, what you were doing."},
            {"timing": "12-25s", "role": "conflict", "direction": "The problem / mistake / unexpected twist."},
            {"timing": "25-40s", "role": "turning_point", "direction": "What changed. The insight or discovery."},
            {"timing": "40-50s", "role": "lesson", "direction": "The takeaway. What you'd tell your past self."},
            {"timing": "50-60s", "role": "cta", "direction": "Ask: has this happened to you? Share your story."},
        ],
        "sound_mood": "emotional / storytelling ambient",
        "cta_templates": [
            "Has this happened to you? Tell me in the comments.",
            "Follow for more real stories — no fluff.",
            "Like if you learned this the hard way too.",
        ],
    },
    "listicle": {
        "label": "Things You Didn't Know / Listicle",
        "hook_templates": [
            "5 {topic} facts that will blow your mind.",
            "Things about {topic} they don't teach you.",
            "3 {topic} secrets most people never discover.",
            "You're sleeping on these {topic} features.",
            "The top {topic} tricks pros use daily.",
        ],
        "structure": [
            {"timing": "0-3s", "role": "hook", "direction": "Number count on screen. Fast zoom."},
            {"timing": "3-12s", "role": "item_1", "direction": "Item 1 — quick hit. Visual proof or demo."},
            {"timing": "12-22s", "role": "item_2", "direction": "Item 2 — slightly more surprising."},
            {"timing": "22-32s", "role": "item_3", "direction": "Item 3 — the one that gets shared."},
            {"timing": "32-42s", "role": "bonus", "direction": "Bonus item — 'but wait, there's more' energy."},
            {"timing": "42-50s", "role": "cta", "direction": "Which one was new to you? Comment the number."},
        ],
        "sound_mood": "energetic / countdown beats",
        "cta_templates": [
            "Which number was new to you? Comment below.",
            "Share this with someone who needs to know.",
            "Follow for part 2 — I have 5 more.",
        ],
    },
    "pov": {
        "label": "POV / Relatable Skit",
        "hook_templates": [
            "POV: you just discovered {topic} for the first time.",
            "POV: your boss asks you to explain {topic}.",
            "POV: {topic} finally clicks after months of struggling.",
            "POV: you realise {topic} was the answer all along.",
        ],
        "structure": [
            {"timing": "0-3s", "role": "hook", "direction": "POV text overlay. Relatable facial expression."},
            {"timing": "3-10s", "role": "setup", "direction": "Act out the before state. Frustration or confusion."},
            {"timing": "10-20s", "role": "discovery", "direction": "The moment of realisation. Transition effect."},
            {"timing": "20-35s", "role": "payoff", "direction": "Show the better way. Confidence and satisfaction."},
            {"timing": "35-45s", "role": "cta", "direction": "Break character. Talk directly. Follow CTA."},
        ],
        "sound_mood": "trending audio / comedic timing beat",
        "cta_templates": [
            "Tag someone who needs this realisation.",
            "Follow if this was you last week.",
            "Duet this with your reaction.",
        ],
    },
    "before_after": {
        "label": "Before / After Transformation",
        "hook_templates": [
            "My {topic} workflow: before vs after.",
            "{topic} beginner vs {topic} pro — the difference is insane.",
            "I upgraded my {topic} setup and the results speak for themselves.",
            "What {topic} looks like after 1 year of practice.",
        ],
        "structure": [
            {"timing": "0-3s", "role": "hook", "direction": "Split screen preview or 'wait for it' text."},
            {"timing": "3-12s", "role": "before", "direction": "Show the messy / slow / painful before state."},
            {"timing": "12-15s", "role": "transition", "direction": "Sharp cut or wipe transition. Sound effect."},
            {"timing": "15-30s", "role": "after", "direction": "Satisfying after state. Clean, fast, impressive."},
            {"timing": "30-40s", "role": "breakdown", "direction": "Quick explanation of what changed."},
            {"timing": "40-50s", "role": "cta", "direction": "Want the full breakdown? Follow + comment."},
        ],
        "sound_mood": "transformation / glow-up trending audio",
        "cta_templates": [
            "Want the full breakdown? Comment 'HOW'.",
            "Follow for more transformations like this.",
            "Save this for your own glow-up.",
        ],
    },
}


# ---------------------------------------------------------------------------
# Topic seeds specifically optimised for TikTok tech content
# ---------------------------------------------------------------------------

TIKTOK_TOPIC_SEEDS = [
    # Dev life & culture
    "switching from Windows to Linux as a developer",
    "why senior devs hate unnecessary meetings",
    "the mass layoffs in tech and how to survive",
    "working from home vs return-to-office as a developer",
    "developer burnout and how to actually fix it",
    "the mass layoffs in tech and what nobody tells you",
    "why coding bootcamps don't tell you the full truth",
    "the one skill that separates junior from senior developers",
    # Tools & productivity
    "VS Code extensions that feel like cheating",
    "terminal commands every developer should know",
    "Git tricks that will save your career one day",
    "AI coding assistants and whether they actually help",
    "the best free developer tools in 2026",
    "Docker explained so simply your manager could understand",
    "Linux commands that make you look like a hacker",
    "keyboard shortcuts that 10x your coding speed",
    # Languages & frameworks
    "Python vs JavaScript for your first language",
    "why Rust is taking over systems programming",
    "React vs Vue vs Svelte in 60 seconds",
    "the programming language that pays the most in 2026",
    "TypeScript tricks that feel illegal",
    "why Go is quietly winning the backend race",
    # Career & money
    "how to mass-apply to developer jobs the smart way",
    "developer salary negotiation secrets",
    "side projects that actually make money as a developer",
    "freelancing as a developer — the truth nobody shares",
    "the tech interview process is broken — here's why",
    "remote developer jobs that pay six figures",
    # AI & trending tech
    "building your first AI app with zero experience",
    "the AI tools replacing developers — should you worry",
    "how to use ChatGPT to code 10x faster",
    "open source AI models you can run on your laptop",
    "the rise of AI agents and what it means for your job",
    "machine learning explained in 60 seconds",
    # Security & privacy
    "your phone is tracking you — here's how to stop it",
    "password managers and why you need one yesterday",
    "the easiest way hackers get into your accounts",
    "two-factor authentication mistakes everyone makes",
]

# Hashtag bank organised by category for natural mixing
HASHTAG_BANK = {
    "core": [
        "#tech", "#coding", "#programming", "#developer", "#software",
        "#learntocode", "#coder", "#webdev", "#devlife", "#techtok",
    ],
    "viral_boosters": [
        "#fyp", "#foryou", "#foryoupage", "#viral", "#trending",
        "#blowthisup", "#xyzbca",
    ],
    "engagement": [
        "#learnontiktok", "#edutok", "#todayilearned", "#lifehack",
        "#didyouknow", "#howto", "#tutorial",
    ],
    "niche_tech": [
        "#python", "#javascript", "#webdevelopment", "#linux", "#opensource",
        "#ai", "#machinelearning", "#cybersecurity", "#startup", "#react",
        "#rust", "#golang", "#docker", "#git", "#vscode",
    ],
    "career": [
        "#techjobs", "#remotework", "#careertok", "#salarytransparency",
        "#jobsearch", "#freelancer", "#sidehustle",
    ],
}


# ---------------------------------------------------------------------------
# TikTok Discovery Agent
# ---------------------------------------------------------------------------

class TikTokDiscoveryAgent:
    """
    Generates TikTok-optimised topic ideas by crossing seed topics with
    viral formats. Fully deterministic, zero-cost.
    """

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.tiktok_file = self.data_dir / "tiktok_topics.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.tiktok_file.exists():
            self.tiktok_file.write_text("[]", encoding="utf-8")

    def _load_existing(self) -> List[Dict[str, Any]]:
        try:
            return json.loads(self.tiktok_file.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save(self, topics: List[Dict[str, Any]]) -> None:
        self.tiktok_file.write_text(json.dumps(topics, indent=2), encoding="utf-8")

    def _make_id(self, topic: str, fmt: str) -> str:
        raw = f"tiktok-{fmt}-{topic}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def run(self, max_new: int = 10) -> List[Dict[str, Any]]:
        existing = self._load_existing()
        existing_ids = {t.get("id") for t in existing}

        # Deterministic seed based on current date so each day yields fresh combos
        day_seed = int(datetime.utcnow().strftime("%Y%m%d"))
        rng = random.Random(day_seed)

        # Shuffle topics and formats to get variety each day
        topics_pool = list(TIKTOK_TOPIC_SEEDS)
        formats_pool = list(VIRAL_FORMATS.keys())
        rng.shuffle(topics_pool)
        rng.shuffle(formats_pool)

        new_topics: List[Dict[str, Any]] = []
        for topic_seed in topics_pool:
            if len(new_topics) >= max_new:
                break
            for fmt in formats_pool:
                topic_id = self._make_id(topic_seed, fmt)
                if topic_id in existing_ids:
                    continue
                entry = {
                    "id": topic_id,
                    "topic": topic_seed,
                    "format": fmt,
                    "status": "new",
                    "created_at": datetime.utcnow().isoformat() + "Z",
                }
                new_topics.append(entry)
                existing.append(entry)
                existing_ids.add(topic_id)
                break  # one format per topic per run

            if len(new_topics) >= max_new:
                break

        # Mark selected
        selected_ids = {t["id"] for t in new_topics}
        for t in existing:
            if t["id"] in selected_ids:
                t["status"] = "selected"

        self._save(existing)
        return new_topics


# ---------------------------------------------------------------------------
# Script Generator
# ---------------------------------------------------------------------------

class TikTokScriptGenerator:
    """
    Generates complete, ready-to-film TikTok scripts from a topic + format.
    Template-based by default; optionally forwards to Ollama.
    """

    def _pick_hook(self, fmt_key: str, topic: str, rng: random.Random) -> str:
        templates = VIRAL_FORMATS[fmt_key]["hook_templates"]
        template = rng.choice(templates)
        return template.format(topic=topic)

    def _pick_cta(self, fmt_key: str, topic: str, rng: random.Random) -> str:
        templates = VIRAL_FORMATS[fmt_key]["cta_templates"]
        template = rng.choice(templates)
        return template.format(topic=topic)

    def _build_segments(self, fmt_key: str, topic: str, hook: str, cta: str) -> List[Dict[str, str]]:
        fmt = VIRAL_FORMATS[fmt_key]
        segments: List[Dict[str, str]] = []

        for slot in fmt["structure"]:
            role = slot["role"]

            if role == "hook":
                text = hook
            elif role == "cta":
                text = cta
            elif role == "setup":
                text = self._generate_setup(topic, fmt_key)
            elif role == "argument":
                text = self._generate_argument(topic)
            elif role == "proof":
                text = self._generate_proof(topic)
            elif role == "flip":
                text = self._generate_flip(topic)
            elif role == "myth_statement":
                text = self._generate_myth_statement(topic)
            elif role == "debunk":
                text = self._generate_debunk(topic)
            elif role == "reality":
                text = self._generate_reality(topic)
            elif role == "context":
                text = self._generate_context(topic)
            elif role.startswith("step_"):
                step_num = role.split("_")[1]
                text = self._generate_step(topic, int(step_num))
            elif role == "result":
                text = self._generate_result(topic)
            elif role == "conflict":
                text = self._generate_conflict(topic)
            elif role == "turning_point":
                text = self._generate_turning_point(topic)
            elif role == "lesson":
                text = self._generate_lesson(topic)
            elif role.startswith("item_"):
                item_num = role.split("_")[1]
                text = self._generate_list_item(topic, int(item_num))
            elif role == "bonus":
                text = self._generate_bonus(topic)
            elif role == "discovery":
                text = self._generate_discovery(topic)
            elif role == "payoff":
                text = self._generate_payoff(topic)
            elif role == "before":
                text = self._generate_before(topic)
            elif role == "transition":
                text = "[SHARP CUT — transition effect + sound effect]"
            elif role == "after":
                text = self._generate_after(topic)
            elif role == "breakdown":
                text = self._generate_breakdown(topic)
            else:
                text = f"[{role}: talk about {topic}]"

            segments.append({
                "timing": slot["timing"],
                "role": role,
                "text": text,
                "visual_direction": slot["direction"],
            })

        return segments

    # --- Content generators for each segment role ---

    def _generate_setup(self, topic: str, fmt_key: str) -> str:
        setups = {
            "hot_take": (
                f"Everyone on this app keeps saying {topic} is amazing, that "
                f"it's the future, that you absolutely need it. But let me tell "
                f"you what actually happens when you use it in the real world."
            ),
            "storytime": (
                f"So a few months ago I decided to go all-in on {topic}. "
                f"I had seen all the hype, read the tutorials, and thought "
                f"I was ready. Spoiler: I was not ready."
            ),
        }
        return setups.get(fmt_key, (
            f"Here's the thing about {topic} that most people completely miss. "
            f"Whether you're a beginner or experienced, this matters."
        ))

    def _generate_argument(self, topic: str) -> str:
        return (
            f"First — the learning curve for {topic} is way steeper than people admit. "
            f"Second — the ecosystem is fragmented and the docs assume you already know everything. "
            f"Third — the alternatives that nobody talks about are genuinely competitive now."
        )

    def _generate_proof(self, topic: str) -> str:
        return (
            f"Look at this — [show screen recording or stat]. "
            f"When you actually benchmark {topic} against the alternatives, "
            f"the gap is nowhere near as big as the influencers claim."
        )

    def _generate_flip(self, topic: str) -> str:
        return (
            f"Now, to be fair — {topic} does have genuine strengths. "
            f"If you're in a specific niche where it shines, absolutely use it. "
            f"But for the majority of people watching this? There are better options."
        )

    def _generate_myth_statement(self, topic: str) -> str:
        return (
            f"Myth number one: you need years of experience for {topic}. "
            f"Myth number two: {topic} is only for big companies. "
            f"Myth number three: the expensive option is always the best for {topic}."
        )

    def _generate_debunk(self, topic: str) -> str:
        return (
            f"Let's break these down. The experience myth? Most people overestimate "
            f"the barrier to entry for {topic}. The fundamentals take weeks, not years. "
            f"The 'big companies only' myth? Some of the best {topic} implementations "
            f"come from solo developers and small teams."
        )

    def _generate_reality(self, topic: str) -> str:
        return (
            f"The reality is — {topic} is accessible to anyone willing to put "
            f"in focused practice. Start small, build projects, and you'll outperform "
            f"90% of people who just watch tutorials without doing the work."
        )

    def _generate_context(self, topic: str) -> str:
        return (
            f"This is for anyone who's been wanting to get into {topic} "
            f"but keeps getting overwhelmed by all the options."
        )

    def _generate_step(self, topic: str, step_num: int) -> str:
        steps = {
            1: f"Step one: open up your setup and start with the absolute basics of {topic}. Don't overthink it.",
            2: f"Step two: now apply it to a real problem. This is where {topic} starts clicking.",
            3: f"Step three: clean it up and make it production-ready. This is where beginners stop and pros keep going.",
        }
        return steps.get(step_num, f"Step {step_num}: continue building with {topic}.")

    def _generate_result(self, topic: str) -> str:
        return (
            f"And that's it. You just did {topic} in under a minute. "
            f"See how simple that was? Now imagine what you can build with this."
        )

    def _generate_conflict(self, topic: str) -> str:
        return (
            f"Then everything went sideways. The thing about {topic} that nobody "
            f"warns you about is the hidden complexity. What looked simple on the "
            f"surface had layers of problems underneath."
        )

    def _generate_turning_point(self, topic: str) -> str:
        return (
            f"But then I found the one thing that changed everything. "
            f"Instead of fighting against {topic}, I started working with it differently. "
            f"I simplified. I focused on fundamentals instead of fancy tricks."
        )

    def _generate_lesson(self, topic: str) -> str:
        return (
            f"If I could go back and tell myself one thing about {topic}, "
            f"it would be this: stop chasing perfection and start shipping. "
            f"The people who succeed aren't smarter — they just iterate faster."
        )

    def _generate_list_item(self, topic: str, item_num: int) -> str:
        items = {
            1: f"Number one — most people don't know that {topic} has a hidden feature that saves hours of work. Seriously, look this up.",
            2: f"Number two — there's a free alternative for {topic} that the expensive tools don't want you to know about.",
            3: f"Number three — the biggest mistake with {topic} is starting too complicated. The pros keep it dead simple.",
        }
        return items.get(item_num, f"Number {item_num} — another key insight about {topic}.")

    def _generate_bonus(self, topic: str) -> str:
        return (
            f"Bonus: if you combine this {topic} knowledge with one other "
            f"skill, you become basically unstoppable. I'll tell you which "
            f"skill in part 2 — make sure you're following."
        )

    def _generate_discovery(self, topic: str) -> str:
        return (
            f"[Transition effect] That moment when {topic} suddenly makes sense. "
            f"Everything you struggled with before — it all clicks into place. "
            f"This is the 'aha' moment everyone talks about."
        )

    def _generate_payoff(self, topic: str) -> str:
        return (
            f"Now look at the difference. What used to take hours with {topic} "
            f"takes minutes. What used to be confusing is now second nature. "
            f"This is the power of actually understanding the fundamentals."
        )

    def _generate_before(self, topic: str) -> str:
        return (
            f"Before: struggling with {topic}. Slow, messy, full of errors. "
            f"Spending hours on things that should take minutes. "
            f"We've all been there."
        )

    def _generate_after(self, topic: str) -> str:
        return (
            f"After: clean, fast, professional. {topic} working exactly how it should. "
            f"Same person, same project — completely different result."
        )

    def _generate_breakdown(self, topic: str) -> str:
        return (
            f"What changed? Three things: I learned the right fundamentals of {topic}, "
            f"I stopped copying tutorials without understanding them, "
            f"and I built real projects instead of toy examples."
        )

    def _select_hashtags(self, topic: str, fmt_key: str, rng: random.Random) -> List[str]:
        """Pick a natural-looking mix of hashtags (8-12 total)."""
        tags: List[str] = []

        # Always include core tech tags
        tags.extend(rng.sample(HASHTAG_BANK["core"], min(3, len(HASHTAG_BANK["core"]))))

        # Add viral boosters
        tags.extend(rng.sample(HASHTAG_BANK["viral_boosters"], min(2, len(HASHTAG_BANK["viral_boosters"]))))

        # Add engagement tags
        tags.extend(rng.sample(HASHTAG_BANK["engagement"], min(2, len(HASHTAG_BANK["engagement"]))))

        # Add niche tags based on topic keywords
        topic_lower = topic.lower()
        relevant_niche = [
            tag for tag in HASHTAG_BANK["niche_tech"]
            if tag.lstrip("#") in topic_lower
        ]
        if relevant_niche:
            tags.extend(relevant_niche[:2])
        else:
            tags.extend(rng.sample(HASHTAG_BANK["niche_tech"], min(2, len(HASHTAG_BANK["niche_tech"]))))

        # Add career tags if topic is career-related
        career_keywords = ["job", "salary", "freelanc", "career", "interview", "remote", "hire", "layoff"]
        if any(kw in topic_lower for kw in career_keywords):
            tags.extend(rng.sample(HASHTAG_BANK["career"], min(2, len(HASHTAG_BANK["career"]))))

        # Deduplicate while preserving order
        seen = set()
        unique_tags = []
        for tag in tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        return unique_tags[:12]

    def _generate_caption(self, topic: str, hook: str, fmt_key: str) -> str:
        """Generate a TikTok caption that drives engagement."""
        captions = [
            f"{hook} Full breakdown in this video. Save for later.",
            f"Talking about {topic} because someone needed to say it. Agree or disagree?",
            f"The honest truth about {topic} that nobody is telling you.",
            f"{topic} — explained in a way that actually makes sense.",
            f"I wish someone told me this about {topic} sooner.",
        ]
        rng = random.Random(hash(topic + fmt_key))
        return rng.choice(captions)

    def _estimate_duration(self, fmt_key: str) -> int:
        """Estimate video duration in seconds from the format structure."""
        structure = VIRAL_FORMATS[fmt_key]["structure"]
        last_slot = structure[-1]["timing"]
        # Parse the end time from "XX-YYs" format
        end_str = last_slot.split("-")[-1].rstrip("s")
        try:
            return int(end_str)
        except ValueError:
            return 60

    def generate(self, topic: str, fmt_key: str, topic_id: str) -> TikTokScript:
        """Generate a complete TikTok script for a given topic and format."""
        rng = random.Random(hash(topic + fmt_key))
        fmt = VIRAL_FORMATS[fmt_key]

        hook = self._pick_hook(fmt_key, topic, rng)
        cta = self._pick_cta(fmt_key, topic, rng)
        segments = self._build_segments(fmt_key, topic, hook, cta)
        hashtags = self._select_hashtags(topic, fmt_key, rng)
        caption = self._generate_caption(topic, hook, fmt_key)
        duration = self._estimate_duration(fmt_key)

        return TikTokScript(
            id=topic_id,
            topic=topic,
            format_name=fmt_key,
            hook=hook,
            script_segments=segments,
            caption=caption,
            hashtags=hashtags,
            sound_suggestion=fmt["sound_mood"],
            cta=cta,
            estimated_duration_sec=duration,
            created_at=datetime.utcnow().isoformat() + "Z",
            metadata={
                "format_label": fmt["label"],
                "word_count": sum(len(seg["text"].split()) for seg in segments),
            },
        )

    def generate_with_ollama(self, topic: str, fmt_key: str, topic_id: str) -> Optional[TikTokScript]:
        """
        Optionally use a local Ollama model for richer, more creative scripts.
        Returns None on any failure so the caller can fall back to templates.
        """
        model = os.getenv("NEURALSTACK_OLLAMA_MODEL", "llama3")
        fmt = VIRAL_FORMATS[fmt_key]

        prompt = (
            "You are a viral TikTok content strategist for tech creators.\n\n"
            f"Topic: {topic}\n"
            f"Format: {fmt['label']}\n"
            f"Target duration: 45-60 seconds\n\n"
            "Generate a complete TikTok video script with:\n"
            "1. A killer hook (first 3 seconds) that stops the scroll\n"
            "2. Timed segments with spoken text and visual directions\n"
            "3. A strong call-to-action that drives comments\n"
            "4. A post caption\n"
            "5. 8-12 relevant hashtags\n\n"
            "Return ONLY valid JSON matching this structure:\n"
            '{"hook": "...", "segments": [{"timing": "0-3s", "text": "...", '
            '"visual": "..."}], "caption": "...", "hashtags": ["#..."], '
            '"cta": "...", "sound_mood": "..."}\n'
        )

        try:
            body = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
            req = urllib.request.Request(
                "http://localhost:11434/api/generate",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = resp.read().decode("utf-8")

            data = json.loads(raw)
            response_text = data.get("response", "")
            script_data = json.loads(response_text)

            segments = [
                {
                    "timing": seg.get("timing", ""),
                    "role": "llm_generated",
                    "text": seg.get("text", ""),
                    "visual_direction": seg.get("visual", ""),
                }
                for seg in script_data.get("segments", [])
            ]

            return TikTokScript(
                id=topic_id,
                topic=topic,
                format_name=fmt_key,
                hook=script_data.get("hook", ""),
                script_segments=segments,
                caption=script_data.get("caption", ""),
                hashtags=script_data.get("hashtags", []),
                sound_suggestion=script_data.get("sound_mood", fmt["sound_mood"]),
                cta=script_data.get("cta", ""),
                estimated_duration_sec=60,
                created_at=datetime.utcnow().isoformat() + "Z",
                metadata={"source": "ollama", "model": model},
            )
        except Exception:
            return None


# ---------------------------------------------------------------------------
# Script Validator
# ---------------------------------------------------------------------------

class TikTokValidator:
    """
    Validates TikTok scripts for quality and virality signals.
    """

    def validate(self, script: TikTokScript) -> Dict[str, Any]:
        issues: List[str] = []
        score = 100  # Start perfect, deduct for issues

        # 1. Hook must exist and be punchy (under 15 words)
        if not script.hook:
            issues.append("missing hook")
            score -= 30
        elif len(script.hook.split()) > 20:
            issues.append("hook too long — should be under 15 words for impact")
            score -= 10

        # 2. Must have at least 3 segments
        if len(script.script_segments) < 3:
            issues.append("too few segments — needs at least 3 for proper pacing")
            score -= 20

        # 3. Duration should be 15-90 seconds (TikTok sweet spot)
        if script.estimated_duration_sec < 15:
            issues.append("too short — under 15 seconds won't perform well")
            score -= 15
        elif script.estimated_duration_sec > 90:
            issues.append("too long — over 90 seconds loses retention")
            score -= 10

        # 4. Must have hashtags
        if len(script.hashtags) < 3:
            issues.append("too few hashtags — aim for 8-12")
            score -= 10

        # 5. Must have a CTA
        if not script.cta:
            issues.append("missing call-to-action")
            score -= 15

        # 6. Caption should exist
        if not script.caption:
            issues.append("missing caption")
            score -= 10

        # 7. Total word count sanity check (should be speakable in duration)
        total_words = sum(len(seg["text"].split()) for seg in script.script_segments)
        words_per_second = total_words / max(script.estimated_duration_sec, 1)
        if words_per_second > 4:  # Speaking too fast
            issues.append("script too dense — may be hard to deliver naturally")
            score -= 5

        return {
            "approved": score >= 60,
            "score": max(score, 0),
            "issues": issues,
        }


# ---------------------------------------------------------------------------
# Output Writer
# ---------------------------------------------------------------------------

class TikTokOutputWriter:
    """
    Writes generated scripts as both JSON (machine-readable) and Markdown
    (human-readable / teleprompter-friendly).
    """

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _slugify(self, text: str) -> str:
        slug = "".join(c.lower() if c.isalnum() else "-" for c in text)
        while "--" in slug:
            slug = slug.replace("--", "-")
        return slug.strip("-")[:60]

    def write_json(self, script: TikTokScript) -> Path:
        """Write the full script data as JSON."""
        path = self.output_dir / f"{self._slugify(script.topic)}-{script.format_name}.json"
        path.write_text(json.dumps(asdict(script), indent=2), encoding="utf-8")
        return path

    def write_markdown(self, script: TikTokScript) -> Path:
        """Write a human-readable teleprompter-style script."""
        slug = self._slugify(script.topic)
        path = self.output_dir / f"{slug}-{script.format_name}.md"

        lines = [
            f"# TikTok Script: {script.topic}",
            f"**Format:** {script.metadata.get('format_label', script.format_name)}",
            f"**Duration:** ~{script.estimated_duration_sec}s",
            f"**Sound/Music:** {script.sound_suggestion}",
            "",
            "---",
            "",
            "## HOOK (first 3 seconds — this is EVERYTHING)",
            "",
            f"> {script.hook}",
            "",
            "---",
            "",
            "## FULL SCRIPT",
            "",
        ]

        for seg in script.script_segments:
            lines.append(f"### [{seg['timing']}] — {seg['role'].upper()}")
            lines.append("")
            lines.append(f"**Say:** {seg['text']}")
            lines.append("")
            lines.append(f"*Camera/Visual:* {seg['visual_direction']}")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## POST DETAILS",
            "",
            f"**Caption:** {script.caption}",
            "",
            f"**Hashtags:** {' '.join(script.hashtags)}",
            "",
            f"**CTA:** {script.cta}",
            "",
        ])

        path.write_text("\n".join(lines), encoding="utf-8")
        return path


# ---------------------------------------------------------------------------
# Main orchestrator agent
# ---------------------------------------------------------------------------

class TikTokAgent:
    """
    Top-level agent that discovers topics, generates scripts, validates them,
    and writes output. Plug this into the main pipeline.
    """

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.output_dir = self.data_dir / "tiktok_scripts"
        self.discovery = TikTokDiscoveryAgent(data_dir)
        self.generator = TikTokScriptGenerator()
        self.validator = TikTokValidator()
        self.writer = TikTokOutputWriter(self.output_dir)

    def run(self, max_scripts: int = 5) -> List[Dict[str, Any]]:
        """
        Full autonomous run:
        1. Discover topics
        2. Generate scripts (Ollama if available, else templates)
        3. Validate
        4. Write approved scripts to disk
        Returns metadata about published scripts.
        """
        import logging
        logger = logging.getLogger(__name__)

        # 1. Discover
        topics = self.discovery.run(max_new=max_scripts)
        logger.info("TikTok discovery found %d new topics.", len(topics))

        if not topics:
            logger.info("No new TikTok topics to process.")
            return []

        use_ollama = os.getenv("NEURALSTACK_LLM_BACKEND", "").lower() == "ollama"
        results: List[Dict[str, Any]] = []

        for topic_entry in topics:
            topic = topic_entry["topic"]
            fmt_key = topic_entry["format"]
            topic_id = topic_entry["id"]

            # 2. Generate
            script: Optional[TikTokScript] = None
            if use_ollama:
                script = self.generator.generate_with_ollama(topic, fmt_key, topic_id)
                if script:
                    logger.info("Generated TikTok script via Ollama: %s", topic)

            if script is None:
                script = self.generator.generate(topic, fmt_key, topic_id)
                logger.info("Generated TikTok script via template: %s", topic)

            # 3. Validate
            validation = self.validator.validate(script)
            if not validation["approved"]:
                logger.warning(
                    "TikTok script rejected (score=%d): %s — %s",
                    validation["score"], topic, "; ".join(validation["issues"]),
                )
                continue

            # 4. Write
            json_path = self.writer.write_json(script)
            md_path = self.writer.write_markdown(script)

            results.append({
                "id": topic_id,
                "topic": topic,
                "format": fmt_key,
                "score": validation["score"],
                "json_path": str(json_path),
                "md_path": str(md_path),
                "hook": script.hook,
                "hashtags": script.hashtags,
                "duration_sec": script.estimated_duration_sec,
            })

            logger.info(
                "Published TikTok script: %s [%s] (score=%d)",
                topic, fmt_key, validation["score"],
            )

        # Update discovery file statuses
        existing = self.discovery._load_existing()
        published_ids = {r["id"] for r in results}
        for t in existing:
            if t["id"] in published_ids:
                t["status"] = "published"
        self.discovery._save(existing)

        logger.info("TikTok pipeline complete: %d scripts published.", len(results))
        return results


__all__ = [
    "TikTokAgent",
    "TikTokScript",
    "TikTokDiscoveryAgent",
    "TikTokScriptGenerator",
    "TikTokValidator",
    "TikTokOutputWriter",
    "VIRAL_FORMATS",
    "TIKTOK_TOPIC_SEEDS",
    "HASHTAG_BANK",
]
