"""Tests for the DiscoveryAgent."""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agents.discovery import DiscoveryAgent, Topic


def _mark_as_drafted(data_dir: Path, topic_ids: set) -> None:
    """Simulate the downstream pipeline marking selected topics as drafted."""
    topics_file = data_dir / "topics.json"
    topics = json.loads(topics_file.read_text())
    for t in topics:
        if t["id"] in topic_ids:
            t["status"] = "drafted"
    topics_file.write_text(json.dumps(topics, indent=2))


class TestDiscoveryAgent(unittest.TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.data_dir = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_first_run_creates_topics_file_and_returns_five(self):
        agent = DiscoveryAgent(self.data_dir)
        selected = agent.run()
        self.assertEqual(len(selected), 5)
        # topics.json should exist and contain more than 5 entries (full pool).
        topics = json.loads((self.data_dir / "topics.json").read_text())
        self.assertGreater(len(topics), 5)

    def test_second_run_selects_different_topics(self):
        agent = DiscoveryAgent(self.data_dir)
        first_batch = agent.run()
        first_ids = {t["id"] for t in first_batch}

        # Simulate downstream pipeline marking these as drafted.
        _mark_as_drafted(self.data_dir, first_ids)

        second_batch = agent.run()
        second_ids = {t["id"] for t in second_batch}

        # No overlap: topics from the first run are "drafted", not available.
        self.assertTrue(first_ids.isdisjoint(second_ids))
        self.assertEqual(len(second_batch), 5)

    def test_available_pool_shrinks_each_run(self):
        """Each run reduces the available pool by 5 (or fewer at the tail)."""
        agent = DiscoveryAgent(self.data_dir)

        batch1 = agent.run()
        _mark_as_drafted(self.data_dir, {t["id"] for t in batch1})
        batch2 = agent.run()
        _mark_as_drafted(self.data_dir, {t["id"] for t in batch2})
        batch3 = agent.run()

        # Three consecutive batches, all size 5, no overlap.
        self.assertEqual(len(batch1), 5)
        self.assertEqual(len(batch2), 5)
        self.assertEqual(len(batch3), 5)
        all_ids = {t["id"] for t in batch1} | {t["id"] for t in batch2} | {t["id"] for t in batch3}
        self.assertEqual(len(all_ids), 15)

    def test_selected_topics_have_correct_status(self):
        agent = DiscoveryAgent(self.data_dir)
        selected = agent.run()
        selected_ids = {t["id"] for t in selected}

        topics = json.loads((self.data_dir / "topics.json").read_text())
        for t in topics:
            if t["id"] in selected_ids:
                self.assertEqual(t["status"], "selected")

    def test_generate_candidates_produces_topics(self):
        agent = DiscoveryAgent(self.data_dir)
        candidates = agent._generate_candidates()
        self.assertGreater(len(candidates), 0)
        self.assertIsInstance(candidates[0], Topic)


if __name__ == "__main__":
    unittest.main()
