---
name: study-new
description: Create a complete, operable study plan for ANY topic — a certification or exam, a technology or framework, a book or a course — with any duration and cadence. Interviews the user (goal, sources, deadline exact or vague, days per week, current level, practice access, video platform, follow-up, path, language), builds the syllabus from official sources or the user's material, runs a diagnostic or prerequisite check, and generates PLAN.md plus one file per session with verified readings, analogies, videos from the user's course platform, optional practice and evaluations. Use it whenever someone says they want to study, learn, prepare for an exam or certification, "armar un plan de estudio", "quiero aprender X", "tengo que certificarme", or asks how to organize their learning — even if they do not say "plan". Also use it to start a second plan alongside an existing one.
---

# /study-new — create a plan

You are about to build something a person will follow for weeks. Three things decide whether it
survives contact with real life: the syllabus comes from real sources and **every claim in it is
backed by a reading**; the schedule is a queue of sessions, not dates glued to files, so a missed
day breaks nothing; and every file is consistent with every other one. Everything below serves that.

`$ARGUMENTS` may contain the topic and anything else the user typed. Pre-fill from it and from the
conversation so far; confirm rather than re-ask.

## Step 0 — load the shared pieces

```bash
SHARED="$HOME/.claude/skills/study-shared"; SS="$SHARED/scripts/study_state.py"
```

Read now: `$SHARED/references/frontmatter.md` and `$SHARED/references/interview.md`.
Read before the diagnostic: `$SHARED/references/protocol.md`. The diagnostic follows its
*Answer positions* and *Delivery* rules like any evaluation.
Read before generating: `$SHARED/references/practice-levels.md`, `$SHARED/references/labels.md`
and, if the user declared a platform, `$SHARED/references/videos.md`.

## Step 1 — interview (4 screens + 3 conversational steps)

Follow `interview.md` exactly: `AskUserQuestion`, up to 4 questions per screen, plain text if the
tool is unavailable.

1. Screen 1: goal type · sources available.
2. **Proposed syllabus** (conversation): source cascade, iterate until approved. Nothing is
   generated before this. Apply interview.md's rules on retired or non-latest versions, missing
   weights, localized docs, and raw HTML for objective tables.
3. Screen 2: horizon (exact / roughly / none) · cadence and minutes · current level.
4. **Reality check** (conversation). A fixed horizon that does not fit makes the user choose.
5. Screen 3: practice access per area (plus how they authenticate, if a `live` area is remote) ·
   video platform · external follow-up and its dates.
6. Screen 4: path · language.
7. **Summary and confirmation.** Explicit yes → Step 3.

## Step 2 — diagnostic or prerequisite check

Per `interview.md`'s table. Ask for `?` marks. Report the score by area and the pattern first,
then decide the order: weakest area first if they know the topic; dependency order from zero,
with missing prerequisites becoming session 0. Write `diagnostic.md` in every case: the baseline
is what makes progress measurable later.

## Step 3 — generate

1. **Chunk the syllabus into sessions** sized by `session_minutes` (readings ≈ 40-60% of it).
   One theme per session, in the order Step 2 decided.
2. **Buffers**: 10-15% of the total, rounded up, minimum 1, **spread through the plan** (a buffer
   only at the end does not help a bad week 2). `is_buffer: true`, `eval_type: none`, no new
   readings or videos.
3. **Checkpoints**: the session before each milestone, or every 6-10 sessions if the user
   accepted internal ones. `eval_type`: `mock` for exams, `integrative` otherwise, `checkpoint`
   for mid-block controls **and for early milestones in a from-zero plan**. A final review day is
   `eval_type: session`.
4. **Videos**, if a platform was declared: follow `videos.md` (candidate courses → user approval
   → index → assignment). If Platzi blocks, carry on without videos and set
   `videos_status: unavailable`.
5. **Write the files** from `$SHARED/templates/`. Fill every `{{h_*}}`, `{{txt_*}}` and
   `{{tbl_*}}` from `labels.md` in the plan's language (do not translate them yourself), and every
   content placeholder with real content. For each session:
   - *why it matters*, tied to the user's goal;
   - the checklist;
   - **readings that cover every checklist item**: each item needs at least one reading that
     actually teaches it. An item with no reading is where evaluations fail;
   - **every claim backed by a reading**: before writing a statement in the checklist or the
     analogy ("tasks only the root user can do", "the five things…"), confirm it in the text of
     that session's reading. A link returning 200 proves the page exists, not that it says what
     you wrote. If you cannot back a claim, drop it;
   - **an analogy that names the confusion it resolves** (EC2 vs RDS patching, CloudTrail vs
     CloudWatch), specific to this topic, never filler;
   - videos per `videos.md`;
   - practice per the area's level; commands must run as-is, with no placeholders in code blocks;
   - the evaluation block from `labels.md` for its `eval_type`, with the threshold from PLAN.md.
   Write `milestones:` in PLAN.md's frontmatter if the user gave follow-up dates.
6. **Project, register, validate**:
   ```bash
   python3 $SS project "<path>" --start <start_date> --cadence <cadence>
   python3 $SS registry add <slug> "<path>"        # --replace when regenerating a plan
   python3 $SS refresh "<path>"
   python3 $SS check "<path>"
   ```
   `check` must come back `"ok": true`. A `milestone_without_checkpoint` means a checkpoint landed
   after its milestone: move it, re-project, check again.
7. Show the calendar from PLAN.md and end with: *"Run `/study-next` when you want to start."*
   (in the plan's language).

## Quality bar before you say it is done

- `check` is clean: no placeholders, no missing dates, every milestone preceded by a checkpoint.
- Every link in Sources and Readings came back `OK` (or was handled per its status) from
  `verify_links.py`.
- Every checklist item has a reading, and every claim is backed by one.
- Every session's analogy is specific to its topic.
- Content is in the user's language; file names, keys and markers are not translated.

Write in the plan's language. For `es`, neutral Spanish with *tú*: no voseo, no regionalisms
(`labels.md`). Keep the tone of someone who will still be there in week 3.
