"""Offline regression tests; no Gemini API key or paid calls required.

Run from the project directory: python -m unittest discover -s tests -v
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from facts_engine import merge_facts, validate_facts  # noqa: E402


def fact(area, key, value, entity=None):
    return {
        "area": area, "key": key, "value": value, "entity": entity,
        "detail": f"{key}: {value}", "source": "test", "date": "14 Nov", "unit": None,
    }


def sample():
    return [
        fact("schedule", "student_count", 120),
        fact("schedule", "team_size", 4),
        fact("schedule", "staff_count", 8),
        fact("schedule", "duration_hours", 4),
        fact("schedule", "prayer_break_minutes", 20),
        fact("judging", "judge_count", 15),
        fact("judging", "judge_honorarium", 4000),
        fact("judging", "judging_time_per_team", 20),
        fact("judging", "max_teams_per_judge", 4),
        fact("budget", "budget_limit", 400000),
        fact("budget", "budget_spent", 60000, "trophies"),
        fact("budget", "budget_spent", 15000, "banners"),
        fact("budget", "extra_cost", 30000, "photo booth"),
        fact("food", "food_price", 850, "biryani box"),
        fact("food", "food_price", 600, "sandwich box"),
        fact("food", "service_charge_percentage", 10),
        fact("venue", "venue_capacity", 160, "Hall 1"),
        fact("venue", "venue_price", 90000, "Hall 1"),
        fact("venue", "venue_capacity", 180, "Hall 2"),
        fact("venue", "venue_price", 110000, "Hall 2"),
        fact("venue", "venue_capacity", 250, "Hall 3"),
        fact("venue", "venue_price", 160000, "Hall 3"),
        fact("venue", "step_free_required", True),
        fact("venue", "venue_step_free", True, "Hall 2"),
        fact("venue", "venue_step_free", True, "Hall 3"),
        fact("venue", "venue_unavailable", True, "Hall 3"),
    ]


class PlannerTests(unittest.TestCase):
    def run_planner(self, facts):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            (work / "extracted_facts.json").write_text(
                json.dumps({"facts": facts}), encoding="utf-8"
            )
            process = subprocess.run(
                [sys.executable, str(ROOT / "planner.py")],
                cwd=work, capture_output=True, text=True, timeout=15,
                env=None,
            )
            return process

    def test_hackathon_venue_food_judging_budget(self):
        result = self.run_planner(sample())
        self.assertEqual(result.returncode, 0, result.stderr)
        for expected in (
            "Venue: Hall 2", "Rejected: Hall 3 - Venue unavailable",
            "Final food total: Rs 94,380", "Judging rounds: 2",
            "Basic timing check: PASS", "Total estimated cost: Rs 339,380",
            "Remaining budget: Rs 60,620",
        ):
            self.assertIn(expected, result.stdout)

    def test_missing_step_free_confirmation_blocks_venue(self):
        facts = [f for f in sample() if f.get("key") != "venue_step_free"]
        result = self.run_planner(facts)
        self.assertIn("No verified suitable venue found", result.stdout)
        self.assertIn("Complete budget cannot be calculated", result.stdout)

    def test_later_unavailability_false_reopens_venue(self):
        facts = sample() + [fact("venue", "venue_unavailable", False, "Hall 3")]
        result = self.run_planner(facts)
        self.assertNotIn("Rejected: Hall 3 - Venue unavailable", result.stdout)

    def test_budget_overrun_warning(self):
        facts = [f for f in sample() if f["key"] != "budget_limit"]
        facts.append(fact("budget", "budget_limit", 100000))
        result = self.run_planner(facts)
        self.assertIn("Status: OVER BUDGET", result.stdout)

    def test_newer_food_price_overrides_older_price(self):
        facts = sample() + [fact("food", "food_price", 550, "sandwich box")]
        result = self.run_planner(facts)
        self.assertIn("Remaining budget: Rs 68,485", result.stdout)
        self.assertNotIn("sandwich box Rs 600", result.stdout)

    def test_repeated_paid_expense_not_double_counted(self):
        facts = sample() + [fact("budget", "budget_spent", 60000, "TROPHIES")]
        result = self.run_planner(facts)
        self.assertIn("Already-paid expenses: Rs 75,000", result.stdout)

    def test_insufficient_judges_flags_problem(self):
        facts = [f for f in sample() if f["key"] != "judge_count"]
        facts.append(fact("judging", "judge_count", 5))
        result = self.run_planner(facts)
        self.assertIn("Judge count valid: NO", result.stdout)
        self.assertIn("WARNING: Judges cannot cover all teams", result.stdout)

    def test_missing_budget_does_not_invent_total(self):
        facts = [f for f in sample() if f["key"] != "budget_limit"]
        result = self.run_planner(facts)
        self.assertIn("Complete budget cannot be calculated", result.stdout)

    def test_bad_negative_quantity_is_rejected(self):
        facts = sample() + [fact("schedule", "student_count", -2)]
        result = self.run_planner(facts)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Negative values", result.stderr)


class FactEngineTests(unittest.TestCase):
    def test_boolean_types_are_checked(self):
        self.assertFalse(validate_facts([fact("venue", "venue_step_free", True, "Hall 2")]))
        self.assertTrue(validate_facts([fact("venue", "venue_step_free", "yes", "Hall 2")]))

    def test_normalize_old_model_key_names(self):
        merged = merge_facts([], [fact("schedule", "duration", 4)])
        self.assertEqual(merged[0]["key"], "duration_hours")

    def test_merge_replaces_expense_without_erasing_other_expenses(self):
        old = [fact("budget", "budget_spent", 60000, "Trophies"),
               fact("budget", "budget_spent", 15000, "Banners")]
        new = [fact("budget", "budget_spent", 65000, "trophies")]
        result = merge_facts(old, new)
        self.assertEqual(len(result), 2)
        self.assertEqual(sum(f["value"] for f in result), 80000)

    def test_unknown_value_allowed_without_guessing(self):
        self.assertFalse(validate_facts([fact("budget", "budget_limit", None)]))

    def test_non_numeric_value_rejected(self):
        self.assertTrue(validate_facts([fact("budget", "budget_limit", "many")]))


if __name__ == "__main__":
    unittest.main()
