#!/usr/bin/env python3
"""State engine for the study-* skill family.

Reads the YAML-ish frontmatter of PLAN.md and sessions/session-*.md, and does
the deterministic work so the model does not have to: find the next session,
measure drift, project dates from a cadence, regenerate the machine-owned
regions of PLAN.md, and manage the ~/.study registry.

Only the standard library is used on purpose: this must run on any machine
that has python3, with nothing to install.

Frontmatter format (kept deliberately simple so this parser is enough):
    ---
    key: value        # optional trailing comment
    ---
Values are typed on read: null/true/false/integers/ISO dates/strings.
"""
import argparse
import datetime as dt
import json
import math
import os
import random
import re
import statistics
import sys
from pathlib import Path

REGISTRY_DIR = Path(os.environ.get("STUDY_HOME", Path.home() / ".study"))
WEEKDAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
PER_WEEK_DEFAULT = {
    1: [0], 2: [1, 3], 3: [0, 2, 4], 4: [0, 1, 3, 4],
    5: [0, 1, 2, 3, 4], 6: [0, 1, 2, 3, 4, 5], 7: [0, 1, 2, 3, 4, 5, 6],
}
LABELS = {
    "es": {
        "state": "Estado actual", "next": "Próxima sesión", "progress": "Progreso",
        "drift": "Deriva", "buffer": "Colchón restante", "projected": "Fin proyectado (ritmo real)",
        "planned_end": "Fin planificado", "last_eval": "Última evaluación", "on_track": "al día",
        "behind": "sesiones detrás del calendario", "ahead": "sesiones adelantado", "none": "ninguna",
        "sessions": "sesiones", "updated": "Actualizado",
        "cal_session": "Sesión", "cal_date": "Fecha prevista", "cal_block": "Bloque",
        "cal_topic": "Tema", "cal_status": "Estado", "cal_flags": "Hito",
        "flag_buffer": "colchón", "flag_checkpoint": "punto de control",
        "st_pending": "⬜ pendiente", "st_studied": "📖 abierta", "st_evaluated": "✅ evaluada", "st_closed": "🔒 cerrada",
    },
    "en": {
        "state": "Current state", "next": "Next session", "progress": "Progress",
        "drift": "Drift", "buffer": "Buffer left", "projected": "Projected end (real pace)",
        "planned_end": "Planned end", "last_eval": "Last evaluation", "on_track": "on track",
        "behind": "sessions behind schedule", "ahead": "sessions ahead", "none": "none",
        "sessions": "sessions", "updated": "Updated",
        "cal_session": "Session", "cal_date": "Planned date", "cal_block": "Block",
        "cal_topic": "Topic", "cal_status": "Status", "cal_flags": "Milestone",
        "flag_buffer": "buffer", "flag_checkpoint": "checkpoint",
        "st_pending": "⬜ pending", "st_studied": "📖 opened", "st_evaluated": "✅ evaluated", "st_closed": "🔒 closed",
    },
    "pt": {
        "state": "Estado atual", "next": "Próxima sessão", "progress": "Progresso",
        "drift": "Atraso", "buffer": "Folga restante", "projected": "Fim projetado (ritmo real)",
        "planned_end": "Fim planejado", "last_eval": "Última avaliação", "on_track": "em dia",
        "behind": "sessões atrasadas", "ahead": "sessões adiantadas", "none": "nenhuma",
        "sessions": "sessões", "updated": "Atualizado",
        "cal_session": "Sessão", "cal_date": "Data prevista", "cal_block": "Bloco",
        "cal_topic": "Tema", "cal_status": "Estado", "cal_flags": "Marco",
        "flag_buffer": "folga", "flag_checkpoint": "ponto de controle",
        "st_pending": "⬜ pendente", "st_studied": "📖 aberta", "st_evaluated": "✅ avaliada", "st_closed": "🔒 fechada",
    },
}


# ---------------------------------------------------------------- frontmatter
def _type(raw):
    v = raw.strip()
    if v == "" or v.lower() in ("null", "~", "none"):
        return None
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        return v
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    return v


def _untype(val):
    if val is None:
        return "null"
    if val is True:
        return "true"
    if val is False:
        return "false"
    return str(val)


def read_frontmatter(path):
    text = Path(path).read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block = text[3:end].strip("\n")
    data = {}
    for line in block.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, rest = line.partition(":")
        value = rest.split(" #", 1)[0]
        data[key.strip()] = _type(value)
    return data, text


def set_frontmatter(path, updates):
    """Rewrite only the lines of the given keys, preserving comments and order."""
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    end = text.find("\n---", 3)
    head, tail = text[: end + 4], text[end + 4:]
    lines = head.split("\n")
    seen = set()
    for i, line in enumerate(lines):
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key = line.split(":", 1)[0].strip()
        if key in updates:
            comment = ""
            if " #" in line:
                comment = "  #" + line.split(" #", 1)[1]
            lines[i] = f"{key}: {_untype(updates[key])}{comment}"
            seen.add(key)
    missing = [k for k in updates if k not in seen]
    if missing:
        insert_at = len(lines) - 1  # before the closing ---
        for k in missing:
            lines.insert(insert_at, f"{k}: {_untype(updates[k])}")
            insert_at += 1
    p.write_text("\n".join(lines) + tail, encoding="utf-8")


# -------------------------------------------------------------------- sessions
def load_plan(plan_path):
    plan_path = Path(plan_path).expanduser().resolve()
    plan_md = plan_path / "PLAN.md"
    if not plan_md.exists():
        die(f"PLAN.md not found in {plan_path}")
    meta, _ = read_frontmatter(plan_md)
    sessions = []
    for f in sorted((plan_path / "sessions").glob("session-*.md")):
        fm, _ = read_frontmatter(f)
        fm["_file"] = str(f)
        sessions.append(fm)
    sessions.sort(key=lambda s: s.get("session") or 0)
    return plan_path, meta, sessions


def today():
    override = os.environ.get("STUDY_TODAY")
    return dt.date.fromisoformat(override) if override else dt.date.today()


def d(s):
    return dt.date.fromisoformat(s) if s else None


def parse_cadence(spec):
    """'daily' | 'weekdays' | 'days:mon,wed,fri' | 'per_week:3'  -> sorted weekday indices."""
    spec = (spec or "").strip().lower()
    if spec in ("daily", "every day"):
        return list(range(7))
    if spec in ("weekdays", "mon-fri"):
        return list(range(5))
    if spec.startswith("days:"):
        return sorted({WEEKDAYS.index(x.strip()[:3]) for x in spec[5:].split(",") if x.strip()})
    if spec.startswith("per_week:"):
        n = max(1, min(7, int(spec.split(":", 1)[1])))
        return PER_WEEK_DEFAULT[n]
    die(f"Unknown cadence spec: {spec!r}. Use daily | weekdays | days:mon,wed,fri | per_week:N")


def cadence_dates(start, days, count):
    out, cur = [], start
    while len(out) < count:
        if cur.weekday() in days:
            out.append(cur)
        cur += dt.timedelta(days=1)
    return out


def compute_status(meta, sessions):
    t = today()
    total = len(sessions)
    closed = [s for s in sessions if s.get("status") == "closed"]
    open_ = [s for s in sessions if s.get("status") != "closed"]
    nxt = open_[0] if open_ else None
    behind = [s for s in open_ if d(s.get("planned_date")) and d(s["planned_date"]) < t]
    ahead = 0
    if nxt and d(nxt.get("planned_date")) and d(nxt["planned_date"]) > t:
        # sessions already closed whose planned_date is still in the future
        ahead = len([s for s in closed if d(s.get("planned_date")) and d(s["planned_date"]) > t])
    buffers = [s for s in sessions if s.get("is_buffer")]
    buffer_left = [s for s in buffers if s.get("status") != "closed"]

    days = parse_cadence(meta.get("cadence")) if meta.get("cadence") else list(range(7))
    planned_rate = len(days) / 7.0
    # actual_date is when study-next opened the session, not when it was closed.
    opened = [d(s["actual_date"]) for s in closed if d(s.get("actual_date"))]
    anchors = [x for x in opened + [d(meta.get("start_date"))] if x]
    window = min(21, (t - min(anchors)).days + 1) if anchors else 0  # young plans: no 21-day divisor
    recent = [x for x in opened if 0 <= (t - x).days < window]
    rate = len(recent) / window if window > 0 and len(recent) >= 2 else planned_rate
    remaining = len(open_)
    projected_end = (t + dt.timedelta(days=round(remaining / rate))) if rate > 0 and remaining else t
    planned_end = max((d(s["planned_date"]) for s in sessions if s.get("planned_date")), default=None)
    # Last activity = latest open, evaluation or close date: a session can stay open for days.
    activity = [d(s.get(k)) for s in sessions for k in ("actual_date", "eval_date", "closed_date") if s.get(k)]
    last_activity = max(activity) if activity else None
    last_eval = None
    evaluated = [s for s in sessions if s.get("eval_date")]
    if evaluated:
        le = max(evaluated, key=lambda s: s["eval_date"])
        last_eval = {"session": le["session"], "score": le.get("eval_score"),
                     "passed": le.get("eval_passed"), "date": le["eval_date"]}
    return {
        "today": t.isoformat(),
        "total": total,
        "closed": len(closed),
        "remaining": remaining,
        "next": {k: v for k, v in nxt.items()} if nxt else None,
        "behind_sessions": len(behind),
        "ahead_sessions": ahead,
        "buffer_total": len(buffers),
        "buffer_left": len(buffer_left),
        "planned_end": planned_end.isoformat() if planned_end else None,
        "projected_end": projected_end.isoformat() if remaining else None,
        "observed_rate_per_week": round(rate * 7, 2),
        "last_eval": last_eval,
        "last_activity": last_activity.isoformat() if last_activity else None,
        "days_since_last_activity": (t - last_activity).days if last_activity else None,
        "plan": {k: v for k, v in meta.items()},
    }


# -------------------------------------------------------------------- rendering
def L(meta):
    lang = (meta.get("language") or "en")[:2].lower()
    return LABELS.get(lang, LABELS["en"])


def render_state(meta, sessions):
    s = compute_status(meta, sessions)
    lb = L(meta)
    nxt = s["next"]
    if s["behind_sessions"]:
        drift = f"⚠️ {s['behind_sessions']} {lb['behind']}"
    elif s["ahead_sessions"]:
        drift = f"🚀 {s['ahead_sessions']} {lb['ahead']}"
    else:
        drift = f"✅ {lb['on_track']}"
    next_txt = (f"{nxt['session']:02d} — {nxt.get('slug','')} ({nxt.get('status')}, {nxt.get('planned_date')})"
                if nxt else "—")
    le = s["last_eval"]
    le_txt = (f"S{le['session']:02d}: {le['score']} ({'✓' if le['passed'] else '✗'}) {le['date']}"
              if le else lb["none"])
    rows = [
        (lb["next"], next_txt),
        (lb["progress"], f"{s['closed']}/{s['total']} {lb['sessions']}"),
        (lb["drift"], drift),
        (lb["buffer"], f"{s['buffer_left']}/{s['buffer_total']}"),
        (lb["planned_end"], s["planned_end"] or "—"),
        (lb["projected"], s["projected_end"] or "—"),
        (lb["last_eval"], le_txt),
        (lb["updated"], s["today"]),
    ]
    out = ["| | |", "|---|---|"] + [f"| **{k}** | {v} |" for k, v in rows]
    return "\n".join(out)


def render_calendar(meta, sessions):
    lb = L(meta)
    head = f"| {lb['cal_session']} | {lb['cal_date']} | {lb['cal_block']} | {lb['cal_topic']} | {lb['cal_flags']} | {lb['cal_status']} |"
    out = [head, "|---|---|---|---|---|---|"]
    for s in sessions:
        flags = []
        if s.get("is_buffer"):
            flags.append(lb["flag_buffer"])
        if s.get("is_checkpoint"):
            flags.append(lb["flag_checkpoint"])
        rel = os.path.relpath(s["_file"], Path(s["_file"]).parent.parent)
        st = lb.get(f"st_{s.get('status')}", s.get("status"))
        out.append(f"| [{s['session']:02d}]({rel}) | {s.get('planned_date') or '—'} | {'—' if s.get('block') is None else s['block']} "
                   f"| {s.get('title') or s.get('slug','')} | {', '.join(flags)} | {st} |")
    return "\n".join(out)


def replace_region(plan_path, region, content):
    p = Path(plan_path) / "PLAN.md"
    text = p.read_text(encoding="utf-8")
    begin, end = f"<!-- study:{region}:begin -->", f"<!-- study:{region}:end -->"
    if begin not in text or end not in text:
        die(f"Region markers for '{region}' not found in PLAN.md")
    pre, rest = text.split(begin, 1)
    _, post = rest.split(end, 1)
    p.write_text(f"{pre}{begin}\n{content}\n{end}{post}", encoding="utf-8")


def append_to_region(plan_path, region, line):
    p = Path(plan_path) / "PLAN.md"
    text = p.read_text(encoding="utf-8")
    end = f"<!-- study:{region}:end -->"
    if end not in text:
        die(f"Region marker for '{region}' not found in PLAN.md")
    pre, post = text.split(end, 1)
    pre = pre.rstrip("\n") + "\n" + line.rstrip("\n") + "\n"
    p.write_text(pre + end + post, encoding="utf-8")


# --------------------------------------------------------------------- registry
def registry_lines():
    f = REGISTRY_DIR / "plans"
    if not f.exists():
        return []
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.strip() and "\t" in line:
            slug, path = line.split("\t", 1)
            out.append((slug.strip(), path.strip()))
    return out


def registry_active():
    f = REGISTRY_DIR / "active"
    return f.read_text(encoding="utf-8").strip() if f.exists() else ""


def cmd_registry(args):
    REGISTRY_DIR.mkdir(parents=True, exist_ok=True)
    plans = registry_lines()
    active = registry_active()
    if args.action == "list":
        for slug, path in plans:
            print(f"{'*' if slug == active else ' '} {slug}\t{path}")
        return
    if args.action == "add":
        slug, path = args.slug, str(Path(args.path).expanduser().resolve())
        if any(s == slug for s, _ in plans):
            if not args.replace:
                die(f"Slug already registered: {slug} (use --replace to overwrite)")
            plans = [(s, path if s == slug else p) for s, p in plans]
            (REGISTRY_DIR / "plans").write_text("".join(f"{s}\t{p}\n" for s, p in plans), encoding="utf-8")
            print(f"replaced {slug} -> {path}")
            return
        with (REGISTRY_DIR / "plans").open("a", encoding="utf-8") as fh:
            fh.write(f"{slug}\t{path}\n")
        if not active:
            (REGISTRY_DIR / "active").write_text(slug + "\n", encoding="utf-8")
        print(f"registered {slug} -> {path}")
        return
    if args.action == "active":
        if args.slug:
            if not any(s == args.slug for s, _ in plans):
                die(f"Unknown slug: {args.slug}")
            (REGISTRY_DIR / "active").write_text(args.slug + "\n", encoding="utf-8")
        print(registry_active() or "")
        return
    if args.action == "resolve":
        want = args.slug or active
        if not plans:
            die("No plans registered. Run study-new first.", code=3)
        if not want:
            if len(plans) == 1:
                print(plans[0][1])
                return
            die("Several plans and none active. Choose one: " + ", ".join(s for s, _ in plans), code=2)
        for slug, path in plans:
            if slug == want:
                print(path)
                return
        die(f"Unknown slug: {want}", code=2)


# --------------------------------------------------------------------- commands
def cmd_sessions(args):
    _, _, sessions = load_plan(args.plan)
    print(json.dumps(sessions, ensure_ascii=False, indent=2))


def cmd_next(args):
    _, meta, sessions = load_plan(args.plan)
    s = compute_status(meta, sessions)
    out = {k: s[k] for k in ("today", "next", "behind_sessions", "ahead_sessions", "buffer_left", "remaining",
                             "last_activity", "days_since_last_activity")}
    out["horizon"] = meta.get("horizon")
    print(json.dumps(out,
                     ensure_ascii=False, indent=2))


def cmd_status(args):
    _, meta, sessions = load_plan(args.plan)
    print(json.dumps(compute_status(meta, sessions), ensure_ascii=False, indent=2))


def cmd_set(args):
    updates = {}
    for kv in args.pairs:
        if "=" not in kv:
            die(f"Expected key=value, got {kv!r}")
        k, v = kv.split("=", 1)
        k = k.strip()
        if re.fullmatch(r"\+\d+", v.strip()):  # "+N" increments the current integer (null counts as 0)
            current = read_frontmatter(args.file)[0].get(k)
            updates[k] = (current if isinstance(current, int) else 0) + int(v.strip()[1:])
        else:
            updates[k] = _type(v)
    set_frontmatter(args.file, updates)
    print(json.dumps(read_frontmatter(args.file)[0], ensure_ascii=False))


def cmd_project(args):
    plan_path, meta, sessions = load_plan(args.plan)
    days = parse_cadence(args.cadence or meta.get("cadence"))
    start = d(args.start) if args.start else today()
    first = args.from_session if args.from_session is not None else min((s["session"] for s in sessions), default=0)
    targets = [s for s in sessions if s["session"] >= first and s.get("status") != "closed"]
    for s, date in zip(targets, cadence_dates(start, days, len(targets))):
        set_frontmatter(s["_file"], {"planned_date": date.isoformat()})
    if args.cadence:
        set_frontmatter(plan_path / "PLAN.md", {"cadence": args.cadence})
    _, meta, sessions = load_plan(plan_path)
    replace_region(plan_path, "calendar", render_calendar(meta, sessions))
    replace_region(plan_path, "state", render_state(meta, sessions))
    print(f"projected {len(targets)} sessions from {start.isoformat()} with cadence {args.cadence or meta.get('cadence')}")


def cmd_refresh(args):
    plan_path, meta, sessions = load_plan(args.plan)
    replace_region(plan_path, "state", render_state(meta, sessions))
    replace_region(plan_path, "calendar", render_calendar(meta, sessions))
    print("PLAN.md state and calendar regions refreshed")


def cmd_today(args):
    print(today().isoformat())


# Only our own template placeholders; Blade/Jinja "{{ $x }}" is legitimate content.
PLACEHOLDER = re.compile(r"\{\{[a-z][a-z0-9_]*\}\}")


def find_issues(plan_path, meta, sessions):
    issues = []
    files = [plan_path / "PLAN.md", plan_path / "diagnostic.md"] + [Path(s["_file"]) for s in sessions]
    for f in (x for x in files if x.exists()):
        for m in PLACEHOLDER.finditer(f.read_text(encoding="utf-8", errors="ignore")):
            issues.append({"kind": "placeholder", "detail": f"{f.relative_to(plan_path)}: {m.group(0)}"})
    for s in sessions:
        if not s.get("planned_date"):
            issues.append({"kind": "missing_date", "detail": f"session {s['session']:02d}"})
        if s.get("is_buffer") and s.get("eval_type") not in (None, "none"):
            issues.append({"kind": "buffer_with_eval",
                           "detail": f"session {s['session']:02d} is a buffer with eval_type {s.get('eval_type')}"})
    raw = str(meta.get("milestones") or "")
    milestones = sorted(x.strip() for x in raw.split(",") if re.fullmatch(r"\d{4}-\d{2}-\d{2}", x.strip()))
    checkpoints = [s["planned_date"] for s in sessions if s.get("is_checkpoint") and s.get("planned_date")]
    prev = ""
    for ms in milestones:
        if not any(prev < c <= ms for c in checkpoints):
            issues.append({"kind": "milestone_without_checkpoint",
                           "detail": f"no checkpoint session planned in ({prev or 'start'}, {ms}]"})
        prev = ms
    return issues


def cmd_check(args):
    plan_path, meta, sessions = load_plan(args.plan)
    issues = find_issues(plan_path, meta, sessions)
    print(json.dumps({"ok": not issues, "issues": issues}, ensure_ascii=False, indent=2))
    sys.exit(1 if issues else 0)


def cmd_log(args):
    plan_path, _, _ = load_plan(args.plan)
    append_to_region(plan_path, "log", args.row)
    print("row appended to evaluation log")


LETTERS = "ABCDEFGHIJ"


def parse_key_spec(spec):
    """'4' = 4 options, 1 correct · '5:2' = 5 options, 2 correct · '-' = not a choice question."""
    if spec == "-":
        return None
    m = re.fullmatch(r"(\d+)(?::(\d+))?", spec)
    if not m:
        die(f"bad question spec '{spec}': use N, N:K or -", 2)
    n, k = int(m.group(1)), int(m.group(2) or 1)
    if not 2 <= n <= len(LETTERS) or not 1 <= k < n:
        die(f"bad question spec '{spec}': need 2 <= options <= {len(LETTERS)} and 1 <= correct < options", 2)
    return n, k


def answer_key(specs, rng):
    """Random correct positions with guard rails: no letter above its fair share + 1, no three
    single-answer questions in a row with the same letter."""
    qs = [parse_key_spec(s) for s in specs]
    choice = [q for q in qs if q]
    slots = sum(k for _, k in choice)
    cap = math.ceil(slots / statistics.median_low([n for n, _ in choice])) + 1 if choice else 0
    counts, key, run = {}, [], []
    for i, q in enumerate(qs, 1):
        if not q:
            key.append({"q": i, "options": 0, "correct": []})
            continue
        n, k = q
        pool = list(LETTERS[:n])
        picked = []
        for _ in range(k):
            avail = [x for x in pool if x not in picked]
            ok = [x for x in avail if counts.get(x, 0) < cap]
            if k == 1 and len(run) >= 2 and run[-1] == run[-2]:
                ok = [x for x in ok if x != run[-1]] or ok
            pick = rng.choice(ok or avail)
            picked.append(pick)
            counts[pick] = counts.get(pick, 0) + 1
        picked.sort()
        run.append(picked[0] if k == 1 else None)
        key.append({"q": i, "options": n, "correct": picked})
    return {"key": key, "counts": dict(sorted(counts.items()))}


def cmd_answer_key(args):
    rng = random.Random(args.seed) if args.seed is not None else random.SystemRandom()
    print(json.dumps(answer_key(args.specs, rng), ensure_ascii=False))


def die(msg, code=1):
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("registry", help="manage ~/.study (list | add <slug> <path> | active [slug] | resolve [slug])")
    r.add_argument("action", choices=["list", "add", "active", "resolve"])
    r.add_argument("slug", nargs="?")
    r.add_argument("path", nargs="?")
    r.add_argument("--replace", action="store_true", help="with add: overwrite the path of an existing slug")
    r.set_defaults(fn=cmd_registry)

    t = sub.add_parser("today", help="print today's date (honours STUDY_TODAY)")
    t.set_defaults(fn=cmd_today)

    for name, fn, help_ in (("sessions", cmd_sessions, "dump all session frontmatter as JSON"),
                            ("next", cmd_next, "next non-closed session + drift, as JSON"),
                            ("status", cmd_status, "full status as JSON"),
                            ("refresh", cmd_refresh, "regenerate state+calendar regions in PLAN.md"),
                            ("check", cmd_check, "validate the plan: placeholders, dates, milestones, buffers")):
        p = sub.add_parser(name, help=help_)
        p.add_argument("plan")
        p.set_defaults(fn=fn)

    s = sub.add_parser("set", help="update frontmatter keys of one file: set <file> key=value ...")
    s.add_argument("file")
    s.add_argument("pairs", nargs="+")
    s.set_defaults(fn=cmd_set)

    pj = sub.add_parser("project", help="(re)assign planned_date to non-closed sessions from a start date")
    pj.add_argument("plan")
    pj.add_argument("--start", help="YYYY-MM-DD (default: today)")
    pj.add_argument("--cadence", help="daily | weekdays | days:mon,wed,fri | per_week:N (default: PLAN.md)")
    pj.add_argument("--from-session", type=int, default=None, help="default: the lowest session number")
    pj.set_defaults(fn=cmd_project)

    lg = sub.add_parser("log", help="append a Markdown table row to the evaluation log region")
    lg.add_argument("plan")
    lg.add_argument("row")
    lg.set_defaults(fn=cmd_log)

    ak = sub.add_parser("answer-key", help="random positions for the correct options: answer-key 4 4 5:2 - ...")
    ak.add_argument("specs", nargs="+", help="per question: N options (1 correct), N:K (K correct), or - (open)")
    ak.add_argument("--seed", type=int, default=None, help="tests only")
    ak.set_defaults(fn=cmd_answer_key)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
