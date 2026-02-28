"""Integration test: run the full pipeline in an isolated temp directory."""

import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


class TestFullPipeline(unittest.TestCase):
    def test_pipeline_produces_articles(self):
        """A fresh pipeline run should discover topics, generate articles,
        validate them, and publish HTML files."""
        with TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            data_dir = root / "data"
            articles_dir = root / "articles"
            data_dir.mkdir()
            articles_dir.mkdir()

            # --- Discovery ---
            from agents.discovery import DiscoveryAgent

            discovery = DiscoveryAgent(data_dir)
            topics = discovery.run()
            self.assertGreater(len(topics), 0, "Discovery should return topics")

            # --- Content ---
            from agents.content import ContentAgent

            content_agent = ContentAgent(data_dir, articles_dir)
            drafts = content_agent.run(topics)
            self.assertEqual(len(drafts), len(topics))

            # --- Validation ---
            from agents.validation import ValidationAgent

            validator = ValidationAgent(data_dir, articles_dir)
            approved = validator.run(drafts)
            self.assertGreater(len(approved), 0, "At least one draft should pass validation")

            # --- Distribution ---
            perf = {"runs": [], "articles_published": 0, "last_run": None, "errors": []}
            (data_dir / "performance.json").write_text(json.dumps(perf))

            from agents.distribution import DistributionAgent

            dist = DistributionAgent(data_dir, root, articles_dir)
            published = dist.run(approved)
            self.assertGreater(len(published), 0)

            for p in published:
                self.assertTrue(p.exists(), f"Published file should exist: {p}")
                html = p.read_text()
                self.assertIn("<article>", html)

            # Index, sitemap, and feed should exist.
            self.assertTrue((root / "index.html").exists())
            self.assertTrue((root / "sitemap.xml").exists())
            self.assertTrue((root / "feed.xml").exists())

            # Sitemap should not contain raw placeholder.
            sitemap = (root / "sitemap.xml").read_text()
            self.assertNotIn("{{BASE_URL}}", sitemap)


if __name__ == "__main__":
    unittest.main()
