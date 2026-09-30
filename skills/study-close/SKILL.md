---
name: study-close
description: Close the current session of the user's active study plan after its evaluation — asks the user to explain the core ideas in their own words and writes those as the session's notes, rewrites what is still weak, marks the session closed, and when the session ends a block writes the block closure summary (coverage, results, concepts, drift) ready to copy. Use whenever the user says "cerremos la sesión", "listo por hoy", "terminé", "guarda los apuntes", "close this session", or wants to wrap up a study session or a study week/block.
---

# /study-close — close the session with the user's own words

Notes the model writes get read once. Notes in the learner's own words are the learning. This
command makes the user say the ideas back (the practice that works even with no environment to
touch) and records it where the next session, and the next Claude, will find it.

## Step 0

```bash
SHARED="$HOME/.claude/skills/study-shared"; SS="$SHARED/scripts/study_state.py"
PLAN=$(python3 $SS registry resolve) || exit
python3 $SS next "$PLAN"
```

The current session must be `evaluated`, or `studied` with `eval_type: none`. Otherwise point to
`/study-eval` (or `/study-next` if it is still `pending`).

## Step 1 — explain it back

Ask: *"In your own words, what are the 2-3 ideas from this session you would explain to a
colleague?"* One message, then wait. If an idea comes back wrong or vague, ask one follow-up on it.
Do not lecture: the point is their wording, corrected as little as possible.

## Step 2 — write

With the Edit tool, in the session file:

- `notes` region: the user's ideas, lightly edited for clarity, **kept in their voice**. Add at most
  one line per idea if something essential was missing, marked as yours.
- `weak` region: **rewrite it** (study-eval may have filled it after a failed attempt) with what is
  still not consolidated: failed or guessed concepts from this session's evaluations that are not
  `consolidated` in PLAN.md, plus anything the user says is still fuzzy. Each line: the concept,
  the correct idea in one sentence, the source link. These feed the next evaluations' review quota.

```bash
python3 $SS set "<session-file>" status=closed closed_date=$(python3 $SS today)
python3 $SS refresh "$PLAN"
```

## Step 3 — if `is_checkpoint: true`, close the block

Append under the *Block closures* heading of PLAN.md:

```
### Block N — closed <date from `python3 $SS today`>
- Covered: sessions a–b (<areas>)
- Checkpoint result: <score> (<type>)
- Concepts consolidated: … · still pending: …
- Drift: <on track | N sessions behind | ahead>; buffer left <x/y>
```

If `external_followup: true` in PLAN.md, also print that block as plain text and say it is ready to
paste wherever they report. **Do not publish it anywhere yourself.**

## Step 4 — hand off

Run `python3 $SS status "$PLAN"` and say in one line where they stand and what `/study-next` will
open. Speak in the plan's language. For `es`, neutral Spanish with *tú*: no voseo, no regionalisms
(`labels.md`).
