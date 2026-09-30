---
name: study-status
description: Show where the user stands in their study plan(s) — next session, progress, schedule drift, buffer left, pending concepts, last results, the projected end date at their real pace and whether the checkpoints still land before their milestones; list all plans and switch the active one; and replan cadence or deadline when life changes. Use whenever the user asks "cómo voy", "how am I doing", "what's my progress", "cuánto me falta", wants to see or switch between study plans, says their schedule or exam date changed, or asks to re-plan ("ahora solo puedo 2 veces por semana", "me adelantaron el examen").
---

# /study-status — where do I stand

Read-only, except for two things: switching the active plan, and `replan`.

`$ARGUMENTS`: empty (active plan) · `all` (list plans, offer to switch) · `<slug>` · `replan`.

## Step 0

```bash
SHARED="$HOME/.claude/skills/study-shared"; SS="$SHARED/scripts/study_state.py"
python3 $SS registry list
PLAN=$(python3 $SS registry resolve $SLUG) && python3 $SS status "$PLAN" && python3 $SS check "$PLAN"
```

## Default — summary

Turn the JSON into a short, honest picture in the plan's language (for `es`, neutral Spanish
with *tú*, no voseo):

- next session (number, title, status, planned date) · progress `closed/total`
- drift: on track / N behind / N ahead, and what that means for the horizon
- buffer left `x/y`
- **projected end at the real pace** (`projected_end`) vs the planned end. Say it even when it
  hurts; with fewer than two sessions opened it falls back to the planned pace, so say that too
- **milestones**: if `check` reports `milestone_without_checkpoint`, say which milestone will
  arrive without a checkpoint before it, and offer to pull the checkpoint forward (only with approval)
- concepts still pending (count, plus the three oldest from PLAN.md's `concepts` region)
- last evaluation

If `behind_sessions > 0`, add one line: *"`/study-next` will propose how to absorb it."*

## `all`

List every plan with `*` on the active one. Offer to switch: `python3 $SS registry active <slug>`.

## `replan`

Life changed. Read `$SHARED/references/recovery.md`, section *Replan*. Ask only two things
(`AskUserQuestion`): the new cadence, and whether the horizon changed (new date / roughly / none).
Then:

```bash
python3 $SS project "$PLAN" --cadence <new> --start $(python3 $SS today) --from-session <next.session>
python3 $SS set "$PLAN/PLAN.md" horizon=<h> target_date=<d|null> target_week=<w|null>
python3 $SS check "$PLAN"
```

Show the new calendar and the `check` result. If `horizon: fixed` and the sessions no longer fit
before `target_date`, enter the fixed-horizon policy (buffer → double → trim) with approval at
each step. **Never regenerate content here**: dates move, content stays.
