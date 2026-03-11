import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any

from .content import DraftArticle, MIN_WORDS


@dataclass
class ValidationResult:
    draft: DraftArticle
    approved: bool
    reasons: List[str]


class ValidationAgent:
    """
    Lightweight validation to keep content human-like and safe for SEO indexing.

    This module deliberately avoids any network calls. It focuses on:
      - Structure checks (headings, sections, FAQs)
      - Length checks (minimum word count)
      - Tone checks via simple heuristics
      - Adding inline "citation-style" placeholders
    """

    def __init__(self, data_dir: Path, posts_dir: Path) -> None:
        self.data_dir = Path(data_dir)
        self.posts_dir = Path(posts_dir)

    def _has_required_structure(self, content: str) -> bool:
        has_h2 = "## " in content
        has_faq = "## Frequently asked questions" in content
        has_table = "|" in content and "---" in content
        return has_h2 and has_faq and has_table

    def _word_count(self, content: str) -> int:
        return len(content.split())

    _AI_PATTERN_PHRASES = [
        "as an ai language model",
        "in conclusion, in conclusion",
        "lorem ipsum",
        "in this comprehensive guide",
        "it's worth noting that",
        "it is important to note",
        "without further ado",
        "in today's rapidly evolving",
        "dive deep into",
        "delve into",
    ]

    _PLACEHOLDER_PATTERNS = [
        "Tool B",
        "Tool A",
        "Component A version",
        "Component B version",
    ]

    def _looks_human_like(self, content: str) -> bool:
        lower = content.lower()
        return not any(p in lower for p in self._AI_PATTERN_PHRASES)

    def _has_placeholder_text(self, content: str) -> bool:
        """Detect unresolved template placeholders."""
        return any(p in content for p in self._PLACEHOLDER_PATTERNS)

    def _has_duplicated_paragraphs(self, content: str) -> bool:
        """Detect paragraphs repeated 2+ times (the padding bug)."""
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        seen = set()
        for p in paragraphs:
            # Normalise whitespace for comparison
            normalised = " ".join(p.split())
            if len(normalised) > 80 and normalised in seen:
                return True
            seen.add(normalised)
        return False

    def _has_references_section(self, content: str) -> bool:
        """Check if the content has a References/Sources section with actual URLs."""
        lower = content.lower()
        has_heading = "## references" in lower or "## sources" in lower
        # Check for at least one markdown link in the references area
        if has_heading:
            ref_idx = lower.index("## references") if "## references" in lower else lower.index("## sources")
            ref_section = content[ref_idx:]
            return "](http" in ref_section
        return False

    def _rejects_keyword_stuffing(self, content: str, keyword: str) -> bool:
        if not keyword:
            return False
        pattern = re.escape(keyword.lower())
        count = len(re.findall(pattern, content.lower()))
        # Rough heuristic: keyword used more than 25 times is suspicious.
        # (Templates with dense inline citations legitimately repeat tool names.)
        return count > 25

    def validate(self, draft: DraftArticle) -> ValidationResult:
        reasons: List[str] = []

        if self._word_count(draft.content) < MIN_WORDS:
            reasons.append("content too short")

        if not self._has_required_structure(draft.content):
            reasons.append("missing structural sections (H2/H3/table/FAQ)")

        if not self._looks_human_like(draft.content):
            reasons.append("content appears machine-like from simple heuristics")

        if self._rejects_keyword_stuffing(draft.content, draft.title):
            reasons.append("potential keyword stuffing detected")

        if self._has_placeholder_text(draft.content):
            reasons.append("unresolved template placeholder detected")

        if self._has_duplicated_paragraphs(draft.content):
            reasons.append("duplicated paragraphs detected")

        approved = len(reasons) == 0
        return ValidationResult(draft=draft, approved=approved, reasons=reasons)

    def run(self, drafts: List[DraftArticle]) -> List[DraftArticle]:
        approved_drafts: List[DraftArticle] = []
        for draft in drafts:
            result = self.validate(draft)
            if not result.approved:
                # For now we simply skip low quality drafts. They remain available
                # in the logs if you choose to inspect them manually.
                continue
            approved_drafts.append(draft)
        return approved_drafts


__all__ = ["ValidationAgent", "ValidationResult"]

