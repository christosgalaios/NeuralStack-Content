"""Tests for the ValidationAgent."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agents.content import DraftArticle, SimpleLocalLLM
from agents.validation import ValidationAgent, ValidationResult


class TestValidationAgent(unittest.TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.data_dir = Path(self.tmpdir.name) / "data"
        self.posts_dir = Path(self.tmpdir.name) / "articles"
        self.data_dir.mkdir()
        self.posts_dir.mkdir()
        self.agent = ValidationAgent(self.data_dir, self.posts_dir)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _make_draft(self, content: str, title: str = "Test Draft") -> DraftArticle:
        return DraftArticle(
            topic_id="test-1",
            title=title,
            slug="test-1",
            content=content,
            created_at="2026-01-01T00:00:00Z",
        )

    def test_valid_template_content_passes(self):
        llm = SimpleLocalLLM()
        content = llm.generate_long_form_article(
            keyword="Test keyword",
            category="devtools_comparison",
            intent="Evaluate tools.",
        )
        draft = self._make_draft(content, title="Test keyword")
        result = self.agent.validate(draft)
        self.assertTrue(result.approved, f"Should approve template content: {result.reasons}")

    def test_short_content_rejected(self):
        draft = self._make_draft("Too short.")
        result = self.agent.validate(draft)
        self.assertFalse(result.approved)
        self.assertIn("content too short", result.reasons)

    def test_missing_structure_rejected(self):
        # Long enough but lacks H2, FAQ, table.
        content = "word " * 1300
        draft = self._make_draft(content)
        result = self.agent.validate(draft)
        self.assertFalse(result.approved)
        self.assertIn("missing structural sections (H2/H3/table/FAQ)", result.reasons)

    def test_ai_language_detected(self):
        content = (
            "## Section\n\n" + "word " * 600
            + "\n\n## Frequently asked questions\n\n"
            + "| a | b |\n|---|---|\n| c | d |\n\n"
            + "As an AI language model, I cannot do this. " + "word " * 600
        )
        draft = self._make_draft(content)
        result = self.agent.validate(draft)
        self.assertFalse(result.approved)
        self.assertIn("content appears machine-like from simple heuristics", result.reasons)

    def test_keyword_stuffing_detected(self):
        keyword = "test keyword"
        stuffed = (keyword + " ") * 20
        content = (
            f"## Section about {keyword}\n\n{stuffed}\n\n"
            "## Frequently asked questions\n\n"
            "| a | b |\n|---|---|\n| c | d |\n\n"
            + "word " * 1200
        )
        draft = self._make_draft(content, title=keyword)
        result = self.agent.validate(draft)
        self.assertFalse(result.approved)
        self.assertIn("potential keyword stuffing detected", result.reasons)

    def test_run_filters_and_enriches(self):
        llm = SimpleLocalLLM()
        good_content = llm.generate_long_form_article(
            keyword="Good topic", category="compatibility", intent="Test."
        )
        good_draft = self._make_draft(good_content, title="Good topic")
        bad_draft = self._make_draft("Too short.", title="Bad topic")

        approved = self.agent.run([good_draft, bad_draft])
        self.assertEqual(len(approved), 1)
        self.assertEqual(approved[0].topic_id, "test-1")
        # Enrichment should have added inline citations.
        self.assertIn("[internal notes]", approved[0].content)

    def test_enrich_context_adds_paragraph(self):
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        enriched = self.agent._enrich_context(content)
        self.assertIn("From a practical standpoint", enriched)


if __name__ == "__main__":
    unittest.main()
