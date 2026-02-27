"""Tests for the DistributionAgent."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agents.content import DraftArticle
from agents.distribution import DistributionAgent, BASE_URL


class TestDistributionAgent(unittest.TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        self.data_dir = self.root / "data"
        self.articles_dir = self.root / "articles"
        self.data_dir.mkdir()
        self.articles_dir.mkdir()
        # Create a minimal performance.json.
        perf = {"runs": [], "articles_published": 0, "last_run": None, "errors": []}
        (self.data_dir / "performance.json").write_text(json.dumps(perf))

    def tearDown(self):
        self.tmpdir.cleanup()

    def _make_draft(self, slug: str = "test-article", title: str = "Test Article") -> DraftArticle:
        return DraftArticle(
            topic_id="topic-1",
            title=title,
            slug=slug,
            content="<h1>Hello</h1>\n<p>Body text here.</p>",
            created_at="2026-01-01T00:00:00Z",
        )

    def test_publish_article_creates_html(self):
        agent = DistributionAgent(self.data_dir, self.root, self.articles_dir)
        draft = self._make_draft()
        path = agent._publish_article(draft)
        self.assertTrue(path.exists())
        content = path.read_text()
        self.assertIn("<title>Test Article</title>", content)
        self.assertIn("<article>", content)

    def test_run_publishes_and_updates_index(self):
        agent = DistributionAgent(self.data_dir, self.root, self.articles_dir)
        drafts = [self._make_draft("article-one", "Article One")]
        published = agent.run(drafts)
        self.assertEqual(len(published), 1)

        # Index should exist and list the article.
        index = (self.root / "index.html").read_text()
        self.assertIn("Article One", index)

    def test_sitemap_uses_real_base_url(self):
        agent = DistributionAgent(self.data_dir, self.root, self.articles_dir)
        agent.run([self._make_draft()])
        sitemap = (self.root / "sitemap.xml").read_text()
        self.assertNotIn("{{BASE_URL}}", sitemap)
        self.assertIn(BASE_URL, sitemap)

    def test_rss_uses_real_base_url(self):
        agent = DistributionAgent(self.data_dir, self.root, self.articles_dir)
        agent.run([self._make_draft()])
        feed = (self.root / "feed.xml").read_text()
        self.assertNotIn("{{BASE_URL}}", feed)
        self.assertIn(BASE_URL, feed)

    def test_video_script_stub_created(self):
        agent = DistributionAgent(self.data_dir, self.root, self.articles_dir)
        agent.run([self._make_draft("my-slug", "My Title")])
        script = self.data_dir / "video_scripts" / "my-slug-short-script.md"
        self.assertTrue(script.exists())
        self.assertIn("My Title", script.read_text())

    def test_run_with_no_drafts(self):
        agent = DistributionAgent(self.data_dir, self.root, self.articles_dir)
        published = agent.run([])
        self.assertEqual(len(published), 0)
        # Index should still be created (with "no articles" message).
        index = (self.root / "index.html").read_text()
        self.assertIn("No articles have been published yet", index)

    def test_performance_summary_updated(self):
        agent = DistributionAgent(self.data_dir, self.root, self.articles_dir)
        agent.run([self._make_draft()])
        perf = json.loads((self.data_dir / "performance.json").read_text())
        self.assertIn("latest_published_files", perf)
        self.assertEqual(len(perf["latest_published_files"]), 1)


if __name__ == "__main__":
    unittest.main()
