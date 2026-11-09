"""Unit tests for CLI parsing, JSON export, and Markdown generation."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import NamedTemporaryFile

from techspecs.cli import build_parser, main
from techspecs.collectors import collect_specs
from techspecs.reporters import generate_json_report, generate_markdown_report
from techspecs.scoring import evaluate_specs


class TestCLI(unittest.TestCase):
    def test_parser(self):
        parser = build_parser()
        args = parser.parse_args(["-b", "--json"])
        self.assertTrue(args.benchmark)
        self.assertTrue(args.json)

    def test_json_generation(self):
        specs = collect_specs()
        report = evaluate_specs(specs)
        json_output = generate_json_report(report)
        data = json.loads(json_output)
        self.assertIn("overall_score", data)
        self.assertIn("rating_tier", data)
        self.assertIn("components", data)
        self.assertIn("workloads", data)
        self.assertIn("baselines_comparison", data)
        self.assertIn("specifications", data)

    def test_markdown_generation(self):
        specs = collect_specs()
        report = evaluate_specs(specs)
        md_output = generate_markdown_report(report)
        self.assertIn("# Hardware Specification & Power Score Audit", md_output)
        self.assertIn("Overall Power Verdict", md_output)
        self.assertIn("Baseline Comparisons", md_output)

    def test_cli_markdown_file_write(self):
        with NamedTemporaryFile(suffix=".md", delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            ret = main(["-m", str(tmp_path)])
            self.assertEqual(ret, 0)
            self.assertTrue(tmp_path.is_file())
            content = tmp_path.read_text(encoding="utf-8")
            self.assertIn("# Hardware Specification & Power Score Audit", content)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


if __name__ == "__main__":
    unittest.main()
