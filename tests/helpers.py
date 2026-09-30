"""Shared helpers for the study-* script tests: build a minimal plan in a temp dir."""
import os
import subprocess
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/study-shared/scripts"
SS = SCRIPTS / "study_state.py"

PLAN = """---
slug: demo
language: es
horizon: flexible
start_date: 2026-09-14
cadence: weekdays
milestones: {milestones}
---

# Demo

<!-- study:state:begin -->
<!-- study:state:end -->

<!-- study:calendar:begin -->
<!-- study:calendar:end -->

<!-- study:log:begin -->
| Date | Session | Type | Score | Passed | Guessed | Failed |
|---|---|---|---|---|---|---|
<!-- study:log:end -->
"""

SESSION = """---
session: {n}
slug: s{n}
title: Session {n}
status: {status}
planned_date: {planned}
actual_date: {actual}
block: {block}
is_buffer: {buffer}
is_checkpoint: {checkpoint}
eval_type: {eval_type}
---

# Session {n}
{body}
"""


def make_plan(sessions, milestones="null"):
    """sessions: list of dicts with SESSION fields; returns (plan_path, env)."""
    root = Path(tempfile.mkdtemp(prefix="study-test-"))
    plan = root / "plan"
    (plan / "sessions").mkdir(parents=True)
    (plan / "PLAN.md").write_text(PLAN.format(milestones=milestones), encoding="utf-8")
    for s in sessions:
        d = dict(status="pending", planned="null", actual="null", block=1, buffer="false",
                 checkpoint="false", eval_type="session", body="Content.")
        d.update(s)
        (plan / "sessions" / f"session-{d['n']:02d}-s{d['n']}.md").write_text(SESSION.format(**d), encoding="utf-8")
    env = dict(os.environ, STUDY_HOME=str(root / "home"), STUDY_TODAY="2026-09-23")
    return plan, env


def run(args, env, check=True):
    r = subprocess.run(["python3", str(SS)] + [str(a) for a in args], capture_output=True, text=True, env=env)
    if check and r.returncode != 0:
        raise AssertionError(f"exit {r.returncode}: {r.stderr}")
    return r
