import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from helpers import make_plan, run  # noqa: E402


class Today(unittest.TestCase):
    def test_today_honours_study_today(self):
        _, env = make_plan([{"n": 1}])
        self.assertEqual(run(["today"], env).stdout.strip(), "2026-09-23")


class Project(unittest.TestCase):
    def test_default_from_session_includes_session_zero(self):
        plan, env = make_plan([{"n": 0}, {"n": 1}])
        run(["project", plan, "--start", "2026-09-14"], env)
        text = (plan / "sessions" / "session-00-s0.md").read_text()
        self.assertIn("planned_date: 2026-09-14", text)


class Calendar(unittest.TestCase):
    def test_block_zero_is_rendered_as_zero(self):
        plan, env = make_plan([{"n": 0, "block": 0, "planned": "2026-09-14"}, {"n": 1, "planned": "2026-09-15"}])
        run(["refresh", plan], env)
        cal = (plan / "PLAN.md").read_text().split("study:calendar:begin")[1]
        row = [l for l in cal.splitlines() if l.startswith("| [00]")][0]
        self.assertEqual(row.split("|")[3].strip(), "0")


class Registry(unittest.TestCase):
    def test_add_replace_updates_path(self):
        plan, env = make_plan([{"n": 1}])
        run(["registry", "add", "demo", plan], env)
        self.assertNotEqual(run(["registry", "add", "demo", plan], env, check=False).returncode, 0)
        other = plan.parent / "moved"
        other.mkdir()
        run(["registry", "add", "demo", other, "--replace"], env)
        self.assertEqual(run(["registry", "resolve", "demo"], env).stdout.strip(), str(other.resolve()))


class Check(unittest.TestCase):
    def healthy(self, **extra):
        sessions = [
            {"n": 1, "planned": "2026-09-14"},
            {"n": 2, "planned": "2026-09-15", "checkpoint": "true", "eval_type": "checkpoint"},
            {"n": 3, "planned": "2026-09-16", "buffer": "true", "eval_type": "none"},
        ]
        return make_plan(sessions, **extra)

    def issues(self, plan, env):
        r = run(["check", plan], env, check=False)
        return r.returncode, json.loads(r.stdout)

    def test_healthy_plan_passes(self):
        plan, env = self.healthy(milestones="2026-09-18")
        code, out = self.issues(plan, env)
        self.assertEqual((code, out["ok"], out["issues"]), (0, True, []))

    def test_placeholder_is_reported_but_blade_is_not(self):
        plan, env = self.healthy()
        f = plan / "sessions" / "session-01-s1.md"
        f.write_text(f.read_text() + "\n{{why_it_matters}}\nBlade: {{ $user->name }}\n")
        code, out = self.issues(plan, env)
        kinds = [i["kind"] for i in out["issues"]]
        self.assertEqual(code, 1)
        self.assertEqual(kinds.count("placeholder"), 1)

    def test_missing_date(self):
        plan, env = make_plan([{"n": 1}])
        _, out = self.issues(plan, env)
        self.assertIn("missing_date", [i["kind"] for i in out["issues"]])

    def test_milestone_without_checkpoint_before_it(self):
        plan, env = self.healthy(milestones="2026-09-14")
        _, out = self.issues(plan, env)
        self.assertIn("milestone_without_checkpoint", [i["kind"] for i in out["issues"]])

    def test_buffer_with_eval(self):
        plan, env = make_plan([{"n": 1, "planned": "2026-09-14", "buffer": "true", "eval_type": "session"}])
        _, out = self.issues(plan, env)
        self.assertIn("buffer_with_eval", [i["kind"] for i in out["issues"]])


class SetIncrement(unittest.TestCase):
    def test_plus_n_increments_from_null_and_from_int(self):
        plan, env = make_plan([{"n": 1}])
        f = plan / "sessions" / "session-01-s1.md"
        run(["set", f, "eval_attempts=+1"], env)
        run(["set", f, "eval_attempts=+1"], env)
        self.assertIn("eval_attempts: 2", f.read_text())


class LastActivity(unittest.TestCase):
    """Warm-up bug (2026-09-24): a session opened on 09-17 but evaluated on 09-23 is recent activity."""

    def activity(self, plan, env):
        return json.loads(run(["next", plan], env).stdout)

    def test_eval_date_counts_as_activity(self):
        plan, env = make_plan([{"n": 1, "status": "closed", "actual": "2026-09-17", "planned": "2026-09-17"},
                               {"n": 2, "planned": "2026-09-24"}])
        run(["set", plan / "sessions" / "session-01-s1.md", "eval_date=2026-09-23"], env)
        env["STUDY_TODAY"] = "2026-09-24"
        out = self.activity(plan, env)
        self.assertEqual((out["last_activity"], out["days_since_last_activity"]), ("2026-09-23", 1))

    def test_closed_date_counts_as_activity(self):
        plan, env = make_plan([{"n": 1, "status": "closed", "actual": "2026-09-10", "planned": "2026-09-10"},
                               {"n": 2, "planned": "2026-09-24"}])
        run(["set", plan / "sessions" / "session-01-s1.md", "closed_date=2026-09-20"], env)
        env["STUDY_TODAY"] = "2026-09-24"
        self.assertEqual(self.activity(plan, env)["days_since_last_activity"], 4)

    def test_no_activity_yet_is_null(self):
        plan, env = make_plan([{"n": 1, "planned": "2026-09-24"}])
        out = self.activity(plan, env)
        self.assertEqual((out["last_activity"], out["days_since_last_activity"]), (None, None))


class AnswerKey(unittest.TestCase):
    def key(self, *specs):
        return json.loads(run(["answer-key", *specs], dict(os.environ)).stdout)

    def test_no_letter_dominates_and_no_run_of_three(self):
        for _ in range(200):
            out = self.key(*["4"] * 8)
            letters = [q["correct"][0] for q in out["key"]]
            self.assertLessEqual(max(out["counts"].values()), 3)
            self.assertFalse(any(a == b == c for a, b, c in zip(letters, letters[1:], letters[2:])))

    def test_positions_vary_between_evaluations(self):
        seen = {tuple(q["correct"][0] for q in self.key(*["4"] * 8)["key"]) for _ in range(20)}
        self.assertGreater(len(seen), 15)

    def test_mixed_specs(self):
        out = self.key("4", "5:2", "-", "3")
        self.assertEqual([q["options"] for q in out["key"]], [4, 5, 0, 3])
        self.assertEqual(len(out["key"][1]["correct"]), 2)
        self.assertEqual(out["key"][2]["correct"], [])
        self.assertTrue(set(out["key"][1]["correct"]) <= set("ABCDE"))
        self.assertIn(out["key"][3]["correct"][0], "ABC")

    def test_long_mock_stays_near_even(self):
        out = self.key(*["4"] * 65)
        self.assertLessEqual(max(out["counts"].values()), 18)  # fair share 17 + 1

    def test_bad_spec_is_rejected(self):
        r = run(["answer-key", "4", "4:4"], dict(os.environ), check=False)
        self.assertEqual(r.returncode, 2)


class StatusShape(unittest.TestCase):
    def test_status_keys_unchanged(self):
        plan, env = make_plan([{"n": 1, "planned": "2026-09-14"}])
        keys = set(json.loads(run(["status", plan], env).stdout))
        self.assertTrue({"today", "total", "closed", "remaining", "next", "behind_sessions", "ahead_sessions",
                         "buffer_total", "buffer_left", "planned_end", "projected_end",
                         "observed_rate_per_week", "last_eval", "plan"} <= keys)


if __name__ == "__main__":
    unittest.main()
