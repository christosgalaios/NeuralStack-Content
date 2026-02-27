"""Tests for the ContentAgent."""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agents.content import ContentAgent, DraftArticle, SimpleLocalLLM, MIN_WORDS


class TestSimpleLocalLLM(unittest.TestCase):
    def test_template_generation_meets_min_words(self):
        llm = SimpleLocalLLM()
        text = llm.generate_long_form_article(
            keyword="Test keyword",
            category="devtools_comparison",
            intent="Evaluate which tool to adopt.",
        )
        word_count = len(text.split())
        self.assertGreaterEqual(word_count, MIN_WORDS)

    def test_template_generation_contains_required_structure(self):
        llm = SimpleLocalLLM()
        text = llm.generate_long_form_article(
            keyword="Docker vs Podman",
            category="devtools_comparison",
            intent="Compare container runtimes.",
        )
        self.assertIn("## ", text)
        self.assertIn("## Frequently asked questions", text)
        self.assertIn("|", text)  # table
        self.assertIn("{{AFFILIATE_TOOL_1}}", text)

    def test_template_includes_keyword(self):
        llm = SimpleLocalLLM()
        keyword = "PyTorch with ROCm detailed compatibility guide"
        text = llm.generate_long_form_article(
            keyword=keyword, category="compatibility", intent="Check compatibility."
        )
        self.assertIn(keyword, text)


class TestContentAgent(unittest.TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.data_dir = Path(self.tmpdir.name) / "data"
        self.articles_dir = Path(self.tmpdir.name) / "articles"
        self.data_dir.mkdir()
        self.articles_dir.mkdir()

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_run_produces_drafts(self):
        agent = ContentAgent(self.data_dir, self.articles_dir)
        topics = [
            {
                "id": "test-topic-1",
                "keyword": "Testing topic one",
                "category": "devtools_comparison",
                "intent": "Test intent.",
            }
        ]
        drafts = agent.run(topics)
        self.assertEqual(len(drafts), 1)
        self.assertIsInstance(drafts[0], DraftArticle)
        self.assertEqual(drafts[0].topic_id, "test-topic-1")

    def test_run_with_empty_topics(self):
        agent = ContentAgent(self.data_dir, self.articles_dir)
        drafts = agent.run([])
        self.assertEqual(len(drafts), 0)

    def test_slugify(self):
        agent = ContentAgent(self.data_dir, self.articles_dir)
        self.assertEqual(agent._slugify("Hello World!"), "hello-world")
        self.assertEqual(agent._slugify("VS Code vs Neovim"), "vs-code-vs-neovim")


if __name__ == "__main__":
    unittest.main()
