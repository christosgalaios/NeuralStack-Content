"""Tests for the DistributionAgent."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agents.content import DraftArticle
from agents.distribution import DistributionAgent, BASE_URL, _related_articles_html, _title_tokens


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


class TestRelatedArticles(unittest.TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.articles_dir = Path(self.tmpdir.name) / "articles"
        self.articles_dir.mkdir()

    def tearDown(self):
        self.tmpdir.cleanup()

    def _write_article(self, slug: str, title: str) -> None:
        html = f"<html><head><title>{title}</title></head><body><article>body</article></body></html>"
        (self.articles_dir / f"{slug}.html").write_text(html, encoding="utf-8")

    def test_returns_empty_when_no_articles(self):
        result = _related_articles_html("my-slug", "Docker on macOS", self.articles_dir, BASE_URL)
        self.assertEqual(result, "")

    def test_returns_empty_for_no_overlap(self):
        self._write_article("python-tutorial", "Python Tutorial for Beginners")
        result = _related_articles_html("docker-guide", "Docker on macOS", self.articles_dir, BASE_URL)
        self.assertEqual(result, "")

    def test_finds_related_articles_by_keyword_overlap(self):
        self._write_article("docker-on-macos", "Docker on macOS compatibility guide")
        self._write_article("podman-on-macos", "Podman on macOS compatibility guide")
        result = _related_articles_html("docker-on-linux", "Docker on Linux", self.articles_dir, BASE_URL)
        self.assertIn("Docker on macOS", result)
        self.assertIn("related-articles", result)

    def test_excludes_self(self):
        self._write_article("docker-on-macos", "Docker on macOS compatibility guide")
        result = _related_articles_html("docker-on-macos", "Docker on macOS", self.articles_dir, BASE_URL)
        # The only article is self — should return empty
        self.assertEqual(result, "")

    def test_respects_max_links(self):
        for i in range(10):
            self._write_article(f"docker-guide-{i}", f"Docker guide number {i} for engineers")
        result = _related_articles_html("docker-new", "Docker setup guide", self.articles_dir, BASE_URL, max_links=3)
        # Count <li> entries — should be at most 3
        self.assertLessEqual(result.count("<li>"), 3)

    def test_title_tokens_filters_stop_words(self):
        tokens = _title_tokens("VS Code vs Cursor IDE for full-stack developers")
        self.assertNotIn("vs", tokens)
        self.assertNotIn("for", tokens)
        self.assertIn("code", tokens)
        self.assertIn("cursor", tokens)
        self.assertIn("developers", tokens)


if __name__ == "__main__":
    unittest.main()
