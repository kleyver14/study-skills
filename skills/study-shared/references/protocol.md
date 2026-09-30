# Evaluation protocol — study-eval (and study-new for the diagnostic)

Thresholds and sizes come from the plan's `PLAN.md` frontmatter. Read them; do not hardcode.
What follows is the behaviour around those numbers. Every rule is here once; the `SKILL.md`
files point to it.

## Types

| Type | When | Covers | Size | Threshold key |
|---|---|---|---|---|
| diagnostic | in study-new | per declared level | 20-25 | — (measures, does not pass/fail) |
| session | after each content session, including a final review day | ~80% today's topic + ~20% review quota | `session_minutes ÷ minutes_per_question`, clamped to `[eval_session_min, eval_session_max]` | `threshold_session` |
| re-evaluation | after a failed session or checkpoint eval | only the weak concepts of that session | 2 questions per weak concept, min 4, max 10 | `threshold_session` |
| checkpoint | sessions with `is_checkpoint` and no exam, or early in a from-zero plan | cumulative since the previous checkpoint | 2× session size | `threshold_checkpoint` |
| mock | `goal_type: exam` only | everything, mirroring the real exam: count, time, weights, question types | same as the exam | `threshold_mock_first`, then `threshold_mock_final` sustained on two consecutive mocks |
| integrative | no exam; closes a block | apply the block | a practical exercise when the topic allows; else 30-40 questions | `threshold_integrative` |

**Mocks take the real exam's duration**, even if that exceeds `session_minutes`. Say so in the
session. If the exam does not publish its question count or weights, choose them, and say in
the plan that the number is the plan's choice, not an official figure.

## Format follows the goal

`exam` → mirror the exam's formats (single choice, multiple response, whatever it uses):
training the format is part of the goal. Otherwise add comprehension formats: *explain in
your own words*, *what is wrong with this snippet*, *write the command/route/query that…*.

## Question quality

What keeps this from generating plausible garbage:

1. **Anchor every question in a source of the session.** If you cannot point to where the
   answer comes from, do not ask it.
2. One defensible answer (or exactly N for multiple response), with distractors someone with
   incomplete knowledge would genuinely pick.
3. Never the same question twice for a concept: change the scenario, not the option order.
4. If grading reveals a question was ambiguous or wrong, **void it and say so**. A voided
   question leaves the denominator.

## Answer positions — hard rule

Where the correct option sits is **never your choice**. Models put the right answer in the same
slot again and again (a real 8-question quiz had 7 answers on B), and after four in a row the
learner answers the pattern instead of the question.

1. Before writing the options, draw the key from the script, one spec per question in order:
   ```bash
   python3 $SS answer-key 4 4 4 5:2 4 -      # N options (1 correct) · N:K (K correct) · - open question
   ```
   It returns the letter(s) each correct answer must occupy: random, no letter above its fair
   share + 1, and never three single-answer questions in a row on the same letter.
2. Write each question with its correct option(s) **exactly at those letters**, then place the
   distractors in the remaining slots. Do not reorder afterwards.
3. Before delivering, check the questions against the key once. If one does not match, fix
   the question, not the key.
4. Options must not give the answer away: similar length and form, the correct one is not
   systematically the longest or the most qualified, and "all of the above" appears only if the
   real exam uses it.
5. Keep the key in the conversation until grading. Never write it to a file beforehand.

## Delivery — clicks or text

Two answer modes. The answer key rule above applies to both.

| Mode | When | Why |
|---|---|---|
| **clicks** | default for **12 questions or fewer** (session, re-evaluation, most checkpoints) | 2-4 dialogs; clicking beats typing `1. A` and multi-select is native |
| **text** | default for **more than 12** (mocks, diagnostics, long checkpoints) | one message: the user sees the whole test, can review and change answers before sending, like the real exam; 20+ dialogs tire |

The user overrides it with `--clicks` or `--text` on `/study-eval`, or by saying so in words. A
flag or request holds for that evaluation only. The diagnostic in study-new uses the same
default (text, since it has 20-25 questions) unless the user asks for clicks.

### Clicks

Choice questions go through `AskUserQuestion`.

- **Batches of up to 3 questions, plus 1 guess question**, in one call (the tool takes 4). The
  guess question is multi-select: *"Which ones did you answer by guessing?"* (in the questions'
  language) with *"None"* **first**, then one option per question in the batch (`Q1`, `Q2`,
  `Q3`). That is how `?` is marked here. *None* is always there, so a batch never has more
  than 3 questions.
- **A guess question left blank means nothing was guessed.** Take it as *None*, say so in one
  line at grading, and never re-ask it in a later batch: each guess question covers only its own
  batch.
- Question `header`: the global number, with the abbreviation of the questions' language
  (`Q7` in English, `P7` in Spanish or Portuguese). Option `label`: the letter and the option text
  (`B. Amazon S3 Glacier`); if the text is long, the letter plus a short form in the label and
  the full text in `description`, **the same way for every option** of that question.
- Multiple response (`N:K`): `multiSelect: true`, and say in the question text how many to pick.
- Never mark an option as recommended, never use `preview`, never put hints in `description`.
- The tool shows at most **4 options**. A question with 5 or more options, and every open item
  (explain back, find the bug, write the command), is asked in plain text after the batches, and
  the user answers in text with `?` for guesses.
- The tool always adds a free-text *Other*. If the user writes there, grade what they wrote.
- Number questions globally across batches. Show nothing about correctness between batches:
  grading starts only when every batch is answered.
- For a `mock`, state the time limit first. The user times the whole run; batches do not pause it.
- If `AskUserQuestion` is not available (another client), use text mode and say why.

### Text

One message: every question numbered, options lettered, open items last. Close with *"Answer
with the letter or text, one per line (`1. A`); mark guesses with `?`."* For multiple response,
say how many to pick and accept `3. B, D`.

## Grading

1. Ask for `?` on guesses up front (the guess question in each batch, or `?` in text answers).
2. **Scoring rule for `?`:** a guessed-right answer **counts as correct for the score and the
   threshold**, and **as an error for concept tracking**. Report guessed-right answers
   separately. Every `?` creates or updates a row in *Concepts to fix*, even when it was right.
3. Report first: **score, breakdown by area and the pattern you see**. Not the error list.
4. Then errors **one at a time, simplest to most complex**, waiting for the user between each.
   Each gets an analogy if it helps, the source link, and a practice check if the area's level
   allows (see *Commands in corrections* below). Ten corrections dumped at once get read once
   and forgotten.
5. **Verify before asserting** anything not already in the session's sources.

## Below the threshold

The session stays `studied` with `eval_passed: false`, and study-eval immediately writes the
session's **`weak` region**: one line per failed or guessed concept, with the correct idea in
one sentence and the source link. That region is what `study-next` reviews and what the
re-evaluation asks about. Without it the review has nothing to work with.

**Re-evaluation.** New questions only on the `weak` items: 2 per concept, minimum 4, maximum 10,
threshold `threshold_session`. Recommend taking it **at the start of the next study sitting**,
not right after the review: right after the review it measures short-term memory. If the user
wants it right away, do it and note that in the result. On pass → `evaluated`.

## Concepts to fix — lifecycle

```
pending → explained → confirmed×1 → consolidated
```

- Born `pending` on a wrong answer or on any `?`. Moves to `explained` once corrected one-on-one.
- Re-asked in **every** later evaluation, inside the review quota.
- Correct without `?` → one step up. With `?`, or wrong → back to `explained`.
- **At most one step per evaluation**, even if the concept is asked twice in the same one.
- Two consecutive correct evaluations → `consolidated`: it leaves the quota.
- Review quota fill order: non-consolidated concepts first; any remaining slots go to topics from
  earlier sessions picked at random (implicit spaced repetition).

Each row: concept · error made · session where it is taught · status · last change date.

## Commands in corrections

When a correction includes a practice command:

- It must **run as-is**. Resolve the user's identity or resource names first (for AWS:
  `aws sts get-caller-identity`) and write the real values into the command.
- **Never put a placeholder inside an executable code block.** `<your-user>` breaks shells:
  `<` and `>` are redirections, and the desktop app's Run button executes the block literally.
  If a value truly cannot be known, show it as inline code in CAPITALS (`USER_NAME`) outside
  the block, and say what to replace.
- Follow `practice-levels.md`: on a shared or production environment, read-only commands only.

## What study-eval writes, in one go

1. Session frontmatter: `eval_score` (this attempt), `eval_passed`, `eval_date`, `eval_attempts`
   incremented, and `status: evaluated` on pass.
2. The session's `result` region: **one line per attempt**, e.g. `Intento 1 · 2026-09-23 · 5/8 ·
   no aprobó · fallados: 2, 5, 7` then `Intento 2 · … · 6/6 · aprobó`. The first score survives
   here and in the log; the frontmatter holds the last one.
3. On a failed attempt: the `weak` region (see above).
4. A row in PLAN.md's `log` region via `study_state.py log`. For a re-evaluation the type column
   is `<eval_type> re-eval`, e.g. `session re-eval`.
5. Rows and status changes in PLAN.md's `concepts` region.
6. `study_state.py refresh`.

Doing all of it together is what keeps the files from disagreeing.
