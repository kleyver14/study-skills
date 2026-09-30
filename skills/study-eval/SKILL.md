---
name: study-eval
description: Build, deliver and grade an evaluation for the current session of the user's active study plan (from study-new) — session quiz, re-evaluation after a failed one, checkpoint, full mock exam or integrative exercise — following the plan's protocol: questions anchored in the session's sources, "?" marks for guesses, score and pattern first, then errors corrected one at a time, concepts tracked until consolidated. Use whenever the user says "hazme la evaluación", "evalúame", "quiz me", "test me", asks for a mock exam / simulacro / practice test, or wants to check what they learned in a study session. Answer mode: `--clicks` (choose options in AskUserQuestion dialogs) or `--text` (all questions in one message, answers typed); by default clicks up to 12 questions and text above that (mocks, diagnostics), e.g. `/study-eval mock --clicks`. Also honour "con clics" / "en texto" said in words.
argument-hint: "[mock|checkpoint|integrative|diagnostic] [--clicks|--text]"
---

# /study-eval — evaluate the current session

An evaluation here is not a quiz for its own sake. Its job is to find what the user believes that
is wrong and fix it one idea at a time. Everything in the protocol (the `?` marks, the pattern
before the list, one correction at a time, re-asking until consolidated) exists because that is
how a misconception actually gets replaced.

`$ARGUMENTS` may force a type (`mock`, `checkpoint`, `integrative`, `diagnostic`) and an answer
mode, in any order:

| Flag | Answer mode |
|---|---|
| *(none)* | **auto**: clicks for 12 questions or fewer, text above that |
| `--clicks` | `AskUserQuestion` dialogs, whatever the size |
| `--text` | one message with every question; the user types `1. A` and `?` for guesses |

The same choice said in words ("con clics", "en texto", "all at once") counts as the flag.

## Step 0

```bash
SHARED="$HOME/.claude/skills/study-shared"; SS="$SHARED/scripts/study_state.py"
PLAN=$(python3 $SS registry resolve) || exit
TODAY=$(python3 $SS today)
python3 $SS next "$PLAN"          # the current session is the first non-closed one
```

Read `$SHARED/references/protocol.md` in full, every time: it is short and it is the contract.
Read thresholds and sizes from PLAN.md's frontmatter (`threshold_*`, `eval_session_min/max`,
`minutes_per_question`, `session_minutes`).

Decline gracefully if the session is `pending` (*"open it first with `/study-next`"*) or has
`eval_type: none` (*"review sessions have no evaluation: `/study-close` when you are done"*).

## Step 1 — build it

- Type: the session's `eval_type`, unless `$ARGUMENTS` forces one. A `studied` session with
  `eval_passed: false` gets a **re-evaluation**: new questions only on its `weak` items, sized per
  protocol.md (2 per concept, min 4, max 10). If the review just happened, recommend doing it at
  the start of the next sitting; if the user wants it now, do it and note that in the result.
- Size and review quota per protocol.md; fill the quota from PLAN.md's `concepts` region.
- Format follows `goal_type`: mirror the real exam for `exam`; add explain-back, find-the-bug and
  write-the-command items otherwise.
- **Anchor every question in a source of the session.** Never reuse a scenario already used for
  the same concept (check the `result` region and the log).
- **Draw the answer key before writing any option** (`python3 $SS answer-key …`, protocol.md,
  *Answer positions*). Correct options go exactly where the key says. This is not optional:
  the correct answer's position is never yours to choose.
- **Deliver in the answer mode** resolved above (protocol.md, *Delivery*). Clicks: batches of up
  to 3 questions plus the multi-select guess question, numbered globally; open items and
  questions with more than 4 options go in plain text after the batches. Text: everything in one
  message. Say the mode in one line when you start, and that the other one exists
  (*"Choices to click; `--text` gets them all in one message"*). For a `mock`, state the time
  limit (the real exam's) and ask them to time it.

## Step 2 — grade

1. Score, **breakdown by area, and the pattern**. Guessed-right answers count as correct for the
   score and threshold, and are reported separately (they count as errors for concepts).
2. Void any question you now see was ambiguous or wrong; say so; drop it from the denominator.
3. Errors **one at a time, simplest first**, waiting for the user between each: analogy if it
   helps, the source, a practice check if the area's level allows. **Practice commands must run
   as-is**: resolve identities first and never put `<placeholders>` in a code block
   (protocol.md, *Commands in corrections*). Verify any fact that is not already in the sources.
4. Pass or fail against PLAN.md's threshold for this type.

## Step 3 — write, all together

```bash
python3 $SS set "<session-file>" eval_score="6/6" eval_passed=true eval_date=$TODAY eval_attempts=+1 status=evaluated   # status only on pass; "+1" increments
python3 $SS log "$PLAN" "| $TODAY | 07 | session re-eval | 6/6 | true | 0 | — |"   # type: <eval_type>, plus " re-eval" when it is one
python3 $SS refresh "$PLAN"
```

Then, with the Edit tool:
- the session's `result` region: **add** a line for this attempt (never overwrite the earlier ones);
- **on a failed attempt, the `weak` region**: one line per failed or guessed concept, with the
  correct idea in one sentence and the source link. This is what study-next reviews;
- PLAN.md's `concepts` region: new rows for new misses and for every `?`; status moves per the
  lifecycle, **at most one step per evaluation**.

Language: files in the plan's language, conversation in the user's (`language.md`). Questions
and options in the plan's language unless the user asks otherwise for this evaluation.
