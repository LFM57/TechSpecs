"""Unit tests for reference baselines and comparisons."""

from __future__ import annotations

import unittest
from techspecs.scoring import REFERENCE_BASELINES, compare_against_baselines


class TestBaselines(unittest.TestCase):
    def test_baselines_integrity(self):
        self.assertGreaterEqual(len(REFERENCE_BASELINES), 6)
        scores = [b.score for b in REFERENCE_BASELINES]
        # Should be strictly increasing
        self.assertEqual(scores, sorted(scores))

    def test_compare_against_baselines(self):
        comps = compare_against_baselines(28.8)
        self.assertEqual(len(comps), len(REFERENCE_BASELINES))

        # Check comparison against entry laptop (~28.5)
        entry_comp = next(c for c in comps if c.baseline_id == "entry_laptop")
        self.assertIn("Matches", entry_comp.summary)

        # Check comparison against budget netbook (~14.5)
        budget_comp = next(c for c in comps if c.baseline_id == "budget_netbook")
        self.assertGreater(budget_comp.delta_score, 0)

        # Check comparison against apex workstation (~98.0)
        apex_comp = next(c for c in comps if c.baseline_id == "apex_workstation")
        self.assertLess(apex_comp.delta_score, 0)


if __name__ == "__main__":
    unittest.main()
