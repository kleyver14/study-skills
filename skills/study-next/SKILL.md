---
name: study-next
description: Open the next pending study session of the user's active plan (created with study-new) — shows the topic, what to study, the analogy, verified readings, videos and optional practice, measures schedule drift and triggers recovery if behind. Use whenever the user wants to study, asks "what's next", "qué estudio hoy", "sigamos con el plan", "retomemos", says they missed some days, or wants to continue learning something they have a plan for — even if they do not name the plan.
---

# /study-next — open the next session

The plan is a queue, not a calendar. You open the first session that is not closed, whatever
today's date is. A missed day means the queue did not move: there is nothing to "catch up"
except the dates, which you re-project.

`$ARGUMENTS` may be a plan slug, to open a plan that is not the active one.

## Step 0

```bash
SHARED="$HOME/.claude/skills/study-shared"; SS="$SHARED/scripts/study_state.py"
PLAN=$(python3 $SS registry resolve $ARGUMENTS) || exit   # exit 2: ambiguous → ask which; 3: none → suggest /study-new
TODAY=$(python3 $SS today)
python3 $SS next "$PLAN"
```

Read `$SHARED/references/frontmatter.md` if you have not this session. Read
`$SHARED/references/recovery.md` only when `behind_sessions > 0` or `ahead_sessions > 0`.
Take dates from `$TODAY`, never from `date`.

## Step 1 — drift first

From the JSON: `behind_sessions`, `ahead_sessions`, `buffer_left`, `horizon`.

- **behind > 0** → apply `recovery.md` for the plan's horizon. Flexible/open: re-project and say it
  in one line, quoting the new planned end. Fixed: propose buffer → double → trim, show the
  resulting calendar, apply only on approval. **After any re-projection run `python3 $SS check
  "$PLAN"`** and handle milestones as recovery.md says.
- **ahead > 0** → say so; offer to pull forward, go deeper, or finish early. Change nothing unless asked.
- **The next session is a buffer and there is no drift** → offer to skip it (`set … status=closed`)
  or use it for review. The buffer is a reserve; it is not consumed by default.

## Step 2 — a long pause gets a warm-up

If `days_since_last_activity` in the Step 0 JSON is 7 or more, offer a 5-10 minute warm-up before
the new session. Use that field, read **before** marking anything: it is the latest open,
evaluation or close date across all sessions, whereas a single `actual_date` only says when a
session was opened (it can stay open for days through a failed evaluation and its re-evaluation).
The warm-up covers the previous session's 2-3 core ideas from its `notes`
region, or two quick questions on them. Offer it; do not impose it.

## Step 3 — act on the session's `status`

- `pending`:
  1. **If the session body still has unfilled template content** (`{{…}}`, `check` reports
     `placeholder`, or sections with no real content), do **not** mark it `studied`: say it is
     incomplete and offer to complete it with study-new's rules (verified links, backed claims,
     a specific analogy).
  2. Otherwise **mark it first, then compose the reply**, so the state you quote is already true:
     ```bash
     python3 $SS set "<file>" status=studied actual_date=$TODAY && python3 $SS refresh "$PLAN"
     ```
  3. Present the session: topic, why it matters, checklist, the analogy verbatim (it was written
     for this exact confusion), readings with times, **videos with the same weight as the
     readings** (their duration shown, what they cover and what they do not), practice for its
     level. Do not re-verify links: they were verified when the plan was created.
  4. Close with *"When you are ready, `/study-eval`. Mark guesses with `?`."* (in the plan's language).
- `studied`, `eval_passed: null` → *"You opened this on <actual_date>. Ready to evaluate?"* Offer a
  quick recap of the checklist if they want it. Do not deliver the whole session again.
- `studied`, `eval_passed: false` → review the items in the session's `weak` region **one at a
  time**, then hand over to `/study-eval` for the re-evaluation, recommending it at the start of the
  next sitting (`protocol.md`). If the `weak` region still holds the template's hint text (plans
  made before iteration 2), rebuild it first from the `result` region and PLAN.md's concepts.
- `evaluated` → *"This one is evaluated and passed. `/study-close` to write your notes and move on."*
- `eval_type: none` and `studied` → there is no evaluation; offer `/study-close` directly.

## Practice that fails

If the user reports that a `live` command failed for permissions, treat it as data: note it in the
session's `weak` region, downgrade that area's `practice_level` in the remaining sessions
(`set … practice_level=sandbox` or `none`), and stop proposing that access
(`$SHARED/references/practice-levels.md`).

Speak in the plan's language (`language:` in PLAN.md). For `es`, neutral Spanish with *tú*: no
voseo, no regionalisms (`labels.md`).
