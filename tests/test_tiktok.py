"""Tests for the TikTok agent (agents/tiktok.py)."""

import json
import unittest
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from agents.tiktok import (
    TikTokDiscoveryAgent,
    TikTokScript,
    TikTokScriptGenerator,
    TikTokValidator,
    TikTokOutputWriter,
    TikTokAgent,
    VIRAL_FORMATS,
)


def _make_script(**overrides) -> TikTokScript:
    """Return a minimal valid TikTokScript; overrides replace any field."""
    defaults = dict(
        id="abc123",
        topic="VS Code vs Cursor",
        format_name="hot_take",
        hook="Unpopular opinion: VS Code is completely overrated.",
        script_segments=[
            {"timing": "0-3s", "role": "hook", "text": "Unpopular opinion: VS Code is completely overrated.", "visual_direction": "Face close to camera."},
            {"timing": "3-10s", "role": "setup", "text": "Everyone uses VS Code but here's why I switched.", "visual_direction": "Step back."},
            {"timing": "10-25s", "role": "argument", "text": "Cursor AI completes whole functions in seconds.", "visual_direction": "Walk and talk."},
            {"timing": "25-35s", "role": "proof", "text": "Here's a real example from my codebase.", "visual_direction": "Screen recording."},
            {"timing": "35-45s", "role": "flip", "text": "VS Code plugins can partially replicate this.", "visual_direction": "Acknowledge counter."},
            {"timing": "45-55s", "role": "cta", "text": "Comment your hottest VS Code vs Cursor take — let's debate.", "visual_direction": "Direct to camera."},
        ],
        caption="Cursor vs VS Code — the debate nobody wants to have #devtools",
        hashtags=["#vscode", "#cursor", "#devtools", "#coding", "#ai", "#programmer", "#tech", "#software"],
        sound_suggestion="intense / dramatic buildup",
        cta="Comment your hottest VS Code vs Cursor take — let's debate.",
        estimated_duration_sec=55,
        created_at="2026-03-07T00:00:00Z",
        metadata={"format_label": "Hot Take / Unpopular Opinion", "word_count": 40},
    )
    defaults.update(overrides)
    return TikTokScript(**defaults)


class TestTikTokDiscoveryAgent(unittest.TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.data_dir = Path(self.tmpdir.name) / "data"
        self.agent = TikTokDiscoveryAgent(self.data_dir)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_creates_tiktok_topics_file_on_init(self):
        """tiktok_topics.json should be created if it didn't exist."""
        self.assertTrue((self.data_dir / "tiktok_topics.json").exists())

    def test_run_returns_list_of_topics(self):
        topics = self.agent.run(max_new=5)
        self.assertIsInstance(topics, list)
        self.assertGreater(len(topics), 0)

    def test_run_respects_max_new(self):
        topics = self.agent.run(max_new=3)
        self.assertLessEqual(len(topics), 3)

    def test_run_topics_have_required_fields(self):
        topics = self.agent.run(max_new=3)
        for t in topics:
            self.assertIn("id", t)
            self.assertIn("topic", t)
            self.assertIn("format", t)
            self.assertIn("status", t)
            self.assertIn("created_at", t)

    def test_run_topics_marked_selected(self):
        topics = self.agent.run(max_new=3)
        for t in topics:
            self.assertEqual(t["status"], "selected")

    def test_run_no_duplicate_topics_across_runs(self):
        """Successive runs should not repeat the same topic+format combos."""
        first = self.agent.run(max_new=5)
        second = self.agent.run(max_new=5)
        first_ids = {t["id"] for t in first}
        second_ids = {t["id"] for t in second}
        self.assertEqual(len(first_ids & second_ids), 0, "Duplicate topic IDs across runs")

    def test_run_saves_topics_to_file(self):
        self.agent.run(max_new=3)
        saved = json.loads((self.data_dir / "tiktok_topics.json").read_text())
        self.assertGreater(len(saved), 0)

    def test_run_formats_come_from_viral_formats(self):
        topics = self.agent.run(max_new=10)
        for t in topics:
            self.assertIn(t["format"], VIRAL_FORMATS)


class TestTikTokScriptGenerator(unittest.TestCase):
    def setUp(self):
        self.gen = TikTokScriptGenerator()

    def test_generate_returns_tiktokscript(self):
        script = self.gen.generate("VS Code vs Cursor", "hot_take", "id-001")
        self.assertIsInstance(script, TikTokScript)

    def test_generate_hook_is_non_empty(self):
        script = self.gen.generate("Docker on Windows", "tutorial", "id-002")
        self.assertTrue(script.hook)

    def test_generate_cta_is_non_empty(self):
        script = self.gen.generate("GitHub Actions", "myth_bust", "id-003")
        self.assertTrue(script.cta)

    def test_generate_has_at_least_three_segments(self):
        for fmt in list(VIRAL_FORMATS.keys())[:4]:
            with self.subTest(fmt=fmt):
                script = self.gen.generate("Python vs Go", fmt, "id-x")
                self.assertGreaterEqual(len(script.script_segments), 3)

    def test_generate_segments_have_required_keys(self):
        script = self.gen.generate("Kubernetes", "tutorial", "id-004")
        for seg in script.script_segments:
            self.assertIn("timing", seg)
            self.assertIn("role", seg)
            self.assertIn("text", seg)
            self.assertIn("visual_direction", seg)

    def test_generate_has_hashtags(self):
        script = self.gen.generate("Terraform", "hot_take", "id-005")
        self.assertGreater(len(script.hashtags), 0)

    def test_generate_has_caption(self):
        script = self.gen.generate("AWS vs GCP", "myth_bust", "id-006")
        self.assertTrue(script.caption)

    def test_generate_estimated_duration_positive(self):
        script = self.gen.generate("React vs Vue", "storytime", "id-007")
        self.assertGreater(script.estimated_duration_sec, 0)

    def test_generate_is_deterministic_for_same_inputs(self):
        """Same topic + format should produce the same hook every time."""
        s1 = self.gen.generate("Linux vs macOS", "hot_take", "id-008")
        s2 = self.gen.generate("Linux vs macOS", "hot_take", "id-008")
        self.assertEqual(s1.hook, s2.hook)

    def test_generate_all_formats(self):
        """Generator should not raise for any format in the library."""
        for fmt in VIRAL_FORMATS:
            with self.subTest(fmt=fmt):
                script = self.gen.generate("Test Topic", fmt, "id-" + fmt)
                self.assertIsInstance(script, TikTokScript)


class TestTikTokValidator(unittest.TestCase):
    def setUp(self):
        self.validator = TikTokValidator()

    def test_valid_script_is_approved(self):
        result = self.validator.validate(_make_script())
        self.assertTrue(result["approved"])
        self.assertGreaterEqual(result["score"], 60)

    def test_missing_hook_penalised(self):
        # Empty hook deducts 30 pts from 100; score (70) still clears the 60
        # approval threshold, but the issue must be recorded.
        result = self.validator.validate(_make_script(hook=""))
        self.assertIn("missing hook", result["issues"])
        self.assertLessEqual(result["score"], 70)

    def test_missing_hook_and_other_issues_rejected(self):
        # Pile up enough deductions so the script is outright rejected.
        result = self.validator.validate(
            _make_script(hook="", cta="", caption="", hashtags=[])
        )
        self.assertFalse(result["approved"])

    def test_missing_cta_penalised(self):
        result = self.validator.validate(_make_script(cta=""))
        self.assertIn("missing call-to-action", result["issues"])

    def test_missing_caption_penalised(self):
        result = self.validator.validate(_make_script(caption=""))
        self.assertIn("missing caption", result["issues"])

    def test_too_few_hashtags_penalised(self):
        result = self.validator.validate(_make_script(hashtags=["#one", "#two"]))
        self.assertIn("too few hashtags — aim for 8-12", result["issues"])

    def test_too_few_segments_penalised(self):
        short_segs = [
            {"timing": "0-3s", "role": "hook", "text": "Hook.", "visual_direction": "Face."},
            {"timing": "3-10s", "role": "setup", "text": "Setup.", "visual_direction": "Step back."},
        ]
        result = self.validator.validate(_make_script(script_segments=short_segs))
        self.assertIn("too few segments — needs at least 3 for proper pacing", result["issues"])

    def test_standard_format_too_short_penalised(self):
        result = self.validator.validate(_make_script(estimated_duration_sec=10))
        self.assertIn("too short — under 15 seconds won't perform well", result["issues"])

    def test_standard_format_too_long_penalised(self):
        result = self.validator.validate(_make_script(estimated_duration_sec=100))
        self.assertIn("too long — over 90 seconds loses retention", result["issues"])

    def test_score_never_negative(self):
        # Strip everything to provoke max deductions
        bad = _make_script(hook="", cta="", caption="", hashtags=[], script_segments=[
            {"timing": "0-3s", "role": "hook", "text": "x", "visual_direction": "y"},
            {"timing": "3-10s", "role": "setup", "text": "x", "visual_direction": "y"},
        ], estimated_duration_sec=1)
        result = self.validator.validate(bad)
        self.assertGreaterEqual(result["score"], 0)

    def test_short_format_duration_boundaries(self):
        """Scripts using a known short format should be validated by short-clip rules."""
        # Find a short format
        short_fmt = next(k for k, v in VIRAL_FORMATS.items() if v.get("short"))
        result_ok = self.validator.validate(_make_script(format_name=short_fmt, estimated_duration_sec=7))
        result_too_long = self.validator.validate(_make_script(format_name=short_fmt, estimated_duration_sec=12))
        self.assertNotIn("short format should stay under 10 seconds for maximum impact", result_ok["issues"])
        self.assertIn("short format should stay under 10 seconds for maximum impact", result_too_long["issues"])


class TestTikTokOutputWriter(unittest.TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.output_dir = Path(self.tmpdir.name) / "tiktok_scripts"
        self.writer = TikTokOutputWriter(self.output_dir)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_creates_output_dir(self):
        self.assertTrue(self.output_dir.exists())

    def test_write_json_creates_file(self):
        path = self.writer.write_json(_make_script())
        self.assertTrue(path.exists())

    def test_write_json_is_valid_json(self):
        path = self.writer.write_json(_make_script())
        data = json.loads(path.read_text())
        self.assertIn("hook", data)
        self.assertIn("script_segments", data)

    def test_write_markdown_creates_file(self):
        path = self.writer.write_markdown(_make_script())
        self.assertTrue(path.exists())

    def test_write_markdown_contains_hook(self):
        script = _make_script()
        path = self.writer.write_markdown(script)
        content = path.read_text()
        self.assertIn(script.hook, content)

    def test_write_markdown_contains_hashtags(self):
        script = _make_script()
        path = self.writer.write_markdown(script)
        content = path.read_text()
        self.assertIn(script.hashtags[0], content)

    def test_slugify_removes_special_chars(self):
        slug = self.writer._slugify("VS Code vs Cursor: A Real Comparison!")
        self.assertNotIn(":", slug)
        self.assertNotIn("!", slug)
        self.assertNotIn(" ", slug)

    def test_slugify_truncates_long_strings(self):
        slug = self.writer._slugify("x" * 100)
        self.assertLessEqual(len(slug), 60)


class TestTikTokAgent(unittest.TestCase):
    def setUp(self):
        self.tmpdir = TemporaryDirectory()
        self.data_dir = Path(self.tmpdir.name) / "data"
        self.agent = TikTokAgent(self.data_dir)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_run_returns_list(self):
        results = self.agent.run(max_scripts=3, produce_videos=False)
        self.assertIsInstance(results, list)

    def test_run_produces_scripts(self):
        results = self.agent.run(max_scripts=3, produce_videos=False)
        self.assertGreater(len(results), 0)

    def test_run_results_have_required_fields(self):
        results = self.agent.run(max_scripts=3, produce_videos=False)
        for r in results:
            self.assertIn("id", r)
            self.assertIn("topic", r)
            self.assertIn("format", r)
            self.assertIn("score", r)
            self.assertIn("hook", r)
            self.assertIn("hashtags", r)
            self.assertIn("duration_sec", r)

    def test_run_writes_json_files(self):
        self.agent.run(max_scripts=2, produce_videos=False)
        json_files = list((self.data_dir / "tiktok_scripts").glob("*.json"))
        self.assertGreater(len(json_files), 0)

    def test_run_writes_markdown_files(self):
        self.agent.run(max_scripts=2, produce_videos=False)
        md_files = list((self.data_dir / "tiktok_scripts").glob("*.md"))
        self.assertGreater(len(md_files), 0)

    def test_run_scores_are_valid(self):
        results = self.agent.run(max_scripts=3, produce_videos=False)
        for r in results:
            self.assertGreaterEqual(r["score"], 0)
            self.assertLessEqual(r["score"], 100)

    def test_second_run_produces_different_topics(self):
        first = self.agent.run(max_scripts=3, produce_videos=False)
        second = self.agent.run(max_scripts=3, produce_videos=False)
        first_ids = {r["id"] for r in first}
        second_ids = {r["id"] for r in second}
        self.assertEqual(len(first_ids & second_ids), 0)


if __name__ == "__main__":
    unittest.main()
