# Design — the `study-*` skill family

> Specification approved in conversation on 2026-09-11. It is the source of truth for building
> the skills. If anything in the implementation contradicts this document, the document wins, or
> the document is updated first.

## 1. Purpose

Let anyone build and run a study plan on **any topic**, with **any duration and cadence**, with
the same discipline as a real AWS CLF-C02 plan put together by hand: a syllabus taken from
verified sources, sessions with material and practice, evaluations with a threshold, errors
corrected one at a time, notes in the user's own words, and progress tracking that any future
session can read.

That plan was the **reference example**, not the mould. The templates contain nothing specific
to AWS.

## 2. Scope decisions

| Decision | Value | Consequence |
|---|---|---|
| Audience | Anyone, alone or in a team | Installed in `~/.claude/skills/` with `install.sh` |
| Platform | **Claude Code only** (terminal, desktop, web) | Uses `AskUserQuestion`. Not installable in `~/.agents/skills/` for Cursor/Codex |
| Lifecycle | Generates **and** runs | A family of commands, not a single generator skill |
| Sources | Cascade: official → provided by the user → built and validated | URLs are never made up; every link is verified before it is written |
| Integrations | **Local files only** | No Jira or Slack. Closure summaries are left ready to copy |
| Plan location | The skill proposes paths and the user can type their own | Central registry in `~/.study/` |
| Unit of time | **The session, not the day** | Free cadence; file names carry no date |
| External follow-up | **Optional** | Without external milestones, the skill proposes internal checkpoints the user can decline |
| Horizon | Exact, approximate ("unos 3 meses", "about 3 months") or none | Fixed end · flexible end with a target week · open end |
| Language | Structure in English; content in the plan language (inferred from the request, see `references/language.md`) | `PLAN.md`, `sessions/`, `session-NN-…` are stable identifiers |
| Videos | Platzi + manual paste; optional but not dismissable | Session time counts readings only. See §12 |

## 3. Architecture

### 3.1 Skill family

```
study-new      interview → validated syllabus → diagnostic by level → generates the plan
study-next     opens the next pending session; measures drift; triggers recovery
study-eval     builds and grades evaluations following the protocol
study-close    closes the session with notes; closes blocks
study-status   state, drift, projection; switch the active plan; replan
study-shared   templates + references. Not user-invocable
```

Same pattern as `sdd-*`: each `SKILL.md` is short and loads only what its command needs; the
templates and references live once, in `study-shared`.

The `SKILL.md` files are written in **English** (house style). Everything generated for the user
goes in the plan language.

### 3.2 Plan registry

```
~/.study/
├── plans      one line per plan:   <slug><TAB><absolute path>
└── active     the slug of the active plan (one line)
```

Plain text, no dependencies. `study-next` and `study-status` read it; `study-new` writes it;
`study-status` can change `active`. If there are several plans and `active` is empty, ask.

### 3.3 Session frontmatter — single source of truth for state

```yaml
---
session: 7                    # integer, 1-based
slug: eloquent-relaciones     # short, kebab-case, in the plan language
status: pending               # pending | studied | evaluated | closed
planned_date: 2026-09-22      # projection; rewritten on re-projection
actual_date: null             # date it was opened (status becomes studied)
block: 1                      # block or checkpoint it belongs to; 0 if none
is_buffer: false              # buffer session
is_checkpoint: false          # closes a block or checkpoint
eval_type: session            # session | checkpoint | mock | integrative | none
eval_score: null              # "8/10"
eval_passed: null             # true | false | null
eval_attempts: 0              # first attempt + re-evaluations
eval_date: null
closed_date: null              # written by study-close
practice_level: live          # live | sandbox | none
video_minutes: 0              # sum of the Videos section (§12); not part of the session time
---
```

Meaning of `status`:
- `pending` — not opened yet.
- `studied` — opened and the material was delivered. It does **not** mean learned.
- `evaluated` — the evaluation was passed (or does not apply).
- `closed` — notes written.

The *Current state* section of `PLAN.md` is **regenerated** from these headers every time a
command writes. It is never edited by hand.

## 4. `study-new` — create a plan

### 4.1 Interview

With `AskUserQuestion`, up to 4 questions per screen, always with the free "Other" option. If
the tool is not available, the same is asked in plain text.

**Screen 1 — Goal and sources**
1. What do you want to learn, and what for? → goal type: `exam` · `tool` · `course` · `other`.
2. Is there an official guide? Do you have your own material? → activates the source cascade.

**Conversational step — Proposed syllabus.** The skill builds the syllabus from the sources,
shows it with areas, subtopics and (if they exist) official weights, and **iterates it with the
user until they approve it**. Nothing is generated before this.

**Screen 2 — Time and level**
3. By when? → exact date (`fixed`) · approximate (`flexible`, target week) · no date (`open`).
4. Which days or how many times a week, and how long per session? → cadence and session size.
5. Are you starting from zero, do you know some of it, or do you already work with this? →
   decides the type of diagnostic.

**Conversational step — Reality check.** Available sessions = cadence × horizon. Needed
sessions = estimate from the syllabus size. The skill says whether there is surplus, it fits,
or it falls short, and in the last case proposes trimming the syllabus, raising the cadence or
extending the horizon. With an `open` end this step only reports how many sessions there will be.

**Screen 3 — Practice and follow-up**
6. Which of these do you have real access to, for practice? → options = areas of the approved
   syllabus, plus "none of it", multi-select. `AskUserQuestion` allows 4 options per question:
   if the syllabus has more than 4 areas, they are grouped into up to 4 affinity groups or split
   across several questions on the same screen. Defines `practice_level` per area.
7. Do you have access to a course platform? → Platzi · another one (you paste the index) · none.
   Multi-select. Activates the video lookup (§12); "none" looks up nothing.
8. Does anyone track your progress, or do you have report dates? (*not required*) → external
   milestones, or proposed internal checkpoints (which can be declined).

**Screen 4 — Location**
9. Where should I save it? → proposes `~/study/<slug>/` (or the plan language's word for it), `./<slug>/`, and accepts a free path.

**The plan language is not asked.** It is inferred from the user's request: an explicit request
wins ("the files in English", "en español"); otherwise the language of the request itself; only
if it is genuinely unclear (no text, mixed languages, only a proper name) is it asked, on this
screen. It is confirmed in the summary screen. The conversation follows the language of the
user's latest message; files stay in the plan language; `study-close` notes keep the user's own
words, untranslated; Spanish is always neutral Spanish (*tú*, no voseo). Detail in
`references/language.md`.

**Conversational step — Summary and confirmation.** One screen with everything decided,
including one line with the plan language (*"Files in: English"*) so the user can change it.
Generation starts only on a "yes".

**Derived without asking:** buffer (10-15% of the sessions, rounded up, minimum 1), default
thresholds, date projection, evaluation size.

**Deliberately not asked:** learning style, level of detail, evaluation format. A good default
is worth more than one more question.

### 4.2 Source cascade

1. **Official** — if the goal is `exam` or `tool`, the skill looks for the official guide (exam
   blueprint, canonical documentation, course syllabus). It extracts from it and cites it.
2. **Provided** — links, files and images the user hands over. Links are verified; files are
   copied to `<path>/material/`. They are **added** to the official syllabus, they do not
   replace it.
3. **Built** — if there is neither official nor provided material, the skill proposes a syllabus
   from its own knowledge and marks it as *built*. It is validated with the user before moving on.

**Hard rule:** no link is written without verifying that it responds (HTTP 200 or equivalent).
Verified links carry their verification date in `PLAN.md`. If a resource cannot be verified, it
is left out and the user is told.

### 4.3 Diagnostic by level

| Declared level | Action | Effect on the plan |
|---|---|---|
| I already work with this | Full diagnostic: 20-25 questions across the whole syllabus, weighted by area | **Weakest first.** Seeds *Concepts to fix* |
| I know some of it, partially | Ask which areas they know; diagnostic on those only | Those areas by weakness; the rest in dependency order |
| From zero | **No topic diagnostic.** Prerequisite check | Missing prerequisites → session(s) 0 at the start, or a warning if the gap is large. Dependency order |

A **written baseline** always ends up in `diagnostic.md`: result by area, or
*"0 on the topic; prerequisites: X ✓, Y ✗"*.

If the user declares a high level and the diagnostic comes in under 50%, the skill says so
plainly and proposes treating those areas as from zero.

The diagnostic asks for `?` marks on guesses, like every evaluation.

### 4.4 Generation

With the syllabus approved, and time, level, access and path known, the skill:
1. Chunks the syllabus into sessions according to session size and the decided order.
2. Inserts buffer sessions spread through the plan (not all at the end).
3. Sets `is_checkpoint` on the sessions that close a block or checkpoint.
4. If a platform was declared, looks up courses, shows them for approval and distributes their
   classes across the sessions (§12). If the platform blocks, it carries on without videos.
5. Projects `planned_date` by cadence from the start date.
6. Generates `PLAN.md`, `sessions/*.md`, `diagnostic.md` if applicable, `material/` if applicable.
7. Registers in `~/.study/plans` and sets `active`.
8. Shows the resulting calendar.

## 5. Generated structure

```
<path>/
├── PLAN.md
├── diagnostic.md            only if there was a diagnostic or prerequisite check
├── material/                copies of what the user provided
└── sessions/
    ├── session-01-<slug>.md
    ├── session-02-<slug>.md
    └── ...
```

**Flat folder.** Rescheduling a session means changing `planned_date`, never moving a file.
Grouping by block or week comes from the calendar in `PLAN.md`.

### 5.1 `PLAN.md`

Sections, in this order:
1. **Current state** (regenerated) — next session, progress `N/M`, drift, buffer left,
   projected end, last result.
2. **How to use this** — the user's routine and the `study-*` commands.
3. **Calendar** — table session → planned date → block → milestone. Visually grouped.
4. **Approved syllabus** — areas and subtopics with the session where each is covered; weights
   if they exist.
5. **Baseline** — diagnostic summary; link to `diagnostic.md`.
6. **Concepts to fix** — table with a lifecycle (§6.5).
7. **Protocol parameters** — editable sizes and thresholds; the skill reads them from here.
8. **Evaluation log** — one row per evaluation.
9. **Block closures** — appended over time.
10. **Sources** — each with its kind (official/provided/built) and verification date.
11. **Appendix — final checklist** — every topic in one list for the final review.

### 5.2 `session-NN-<slug>.md`

Frontmatter (§3.3) and then:
- **Topic** and **why it matters** (one or two lines, tied to the user's goal).
- **What to study** — checklist.
- **How to think about it** — an analogy or mental model that targets the typical confusion of
  the topic.
- **Readings** — table resource · verified link · estimated time; total at the bottom.
- **Videos** — if a platform was declared (§12). Optional but at the same level as the
  readings: their own duration shown, what they cover and what they do not. They do not add to
  the session time.
- **Practice** — according to `practice_level` (§8). Optional; it never blocks.
- **Evaluation** — type, threshold, the instruction to mark `?`, and an empty *Result* section.
- **Notes — what I understood** — empty; written by `study-close` in the user's own words.
- **What is still weak** — empty; written by `study-close`.

Buffer sessions: `is_buffer: true`, topic "Review and recovery", content = review notes and
pending concepts; no new readings.

### 5.3 `diagnostic.md`

Date, declared level, questions with the correct answer and the user's answer (with `?` if they
guessed), result by area, and **the ordering decision** the skill made and why.

## 6. Evaluation protocol

### 6.1 Types

| Type | When | On what | Size | Default threshold |
|---|---|---|---|---|
| Diagnostic | In `study-new` | By level (§4.3) | 20-25 | Not applicable |
| Session | At the end of each content session | ~80% today's topic + ~20% review | ~1 question per 6-8 min of study; min 5, max 15 | 80% |
| Checkpoint | In `is_checkpoint` sessions | Cumulative since the previous checkpoint | 2× the session one | 80% |
| Mock | `exam` only | Everything, imitating the real exam | Same as the exam | 70% the first one; **85% sustained over two in a row** before booking |
| Integrative | Only when there is no exam; closes a block | Applying what the block covered | A practical exercise if the topic allows it; otherwise 30-40 questions | 80% |

Sizes and thresholds live in *Protocol parameters* in `PLAN.md`. The skill reads them from there.

### 6.2 Format by goal

- `exam`: questions **imitate the exam format** (multiple choice, multiple response, whatever it
  uses). Training the format is part of the goal.
- Everything else: besides multiple choice, comprehension formats: *explain it in your own
  words*, *what is wrong in this snippet*, *write the command/path/query that…*.

### 6.3 Question quality

1. Every question is **anchored in a source** of the session. No citable source, no question.
2. Only one defensible answer (or exactly N in multiple response). Distractors that someone with
   incomplete knowledge would really choose.
3. Never the same question twice for a concept: change the scenario.
4. If, when grading, a question turns out ambiguous or wrong, it is **voided and the user is told**.

### 6.4 Grading mechanics

1. Ask for `?` marks on guesses. Correct answers marked `?` **count as errors** for study
   purposes and are reported separately.
2. Deliver the **score, breakdown by area and pattern** first. Not the list of errors.
3. Errors **one at a time, from simplest to most complex**, waiting for a reply between each.
   Each one with an analogy if it helps, a link to the source, and a practical check if the
   area's level allows it.
4. **Verify before stating** any fact that is not in the session's sources.
5. **Below the threshold there is no moving on.** The session stays `studied` with
   `eval_passed: false`. `study-next` offers a review of what failed and a **short
   re-evaluation with new questions** on that only. Once passed, the session becomes `evaluated`.

### 6.5 Concepts to fix — lifecycle

```
pending → explained → confirmed×1 → consolidated
```

- Born **pending** on a failure (or on a correct answer marked `?`). Becomes **explained** once
  corrected.
- Re-asked in **every** later evaluation, inside the review quota.
- Correct without `?` → one step up. With `?` or wrong → back to **explained**.
- **Two correct in a row** → consolidated. It leaves the quota.
- The review quota is filled: non-consolidated concepts first; the rest with topics from earlier
  sessions at random (implicit spaced repetition).

Each entry stores: concept, error made, session where it is taught, state, dates.

### 6.6 What `study-eval` writes

In a single operation: frontmatter (`eval_score` of the last attempt, `eval_passed`,
`eval_date`, `eval_attempts` incremented), one line per attempt in the *Result* region, **the
`weak` region when the threshold is not reached**, a row in the *Log* of `PLAN.md` (type
`<eval_type> re-eval` if it is a re-evaluation), additions and changes in *Concepts to fix*, and
*Current state*. Detail in §13.

## 7. Session cycle and recovery

### 7.1 `study-next`

1. Resolves the active plan (§3.2).
2. Reads the frontmatter of every session; takes the **first one not `closed`**. It does not
   use today's date to choose.
3. **Measures drift**: that session's `planned_date` vs today. Behind → §7.5. Ahead → says so and
   offers to move forward.
4. If the session is a buffer and there is no delay → offers to skip it or use it for review.
   The buffer is not spent on its own.
5. By `status`:
   - `pending` → presents the full session; sets `studied`, `actual_date` = today.
   - `studied`, not evaluated → offers to evaluate (*"you already opened this on <date>"*).
   - `studied`, `eval_passed: false` → offers review + short re-evaluation.
   - `evaluated` → offers to close.
   - If `eval_type: none` (buffer sessions), there is no evaluation: from `studied` it offers
     to close directly.
6. Optional `<slug>` argument to operate on a plan that is not the active one.

### 7.2 `study-eval`

Without an argument: evaluates the current session with the type its frontmatter indicates.
With an argument it forces the type: `mock`, `checkpoint`, `integrative`, `diagnostic`.
Follows §6.

### 7.3 `study-close`

On the session in `evaluated`:
1. Asks the user to **explain the 2-3 core ideas in their own words**. With that it writes
   *Notes — what I understood*. This is the Feynman step and, for areas without an environment,
   the practice.
2. Writes *What is still weak* with the evaluation's errors plus whatever the user adds.
3. Sets `closed`.
4. If `is_checkpoint`: writes the **block closure** in `PLAN.md` — coverage, result,
   consolidated and pending concepts, drift — and leaves the text ready to copy if the milestone
   was external. It publishes nothing.
5. Regenerates *Current state*.

### 7.4 `study-status`

Read-only except for switching the active plan. Shows: active plan, next session, progress,
drift, buffer left, pending concepts, last evaluations, **projected end at the real pace**.
`study-status all` lists plans and lets the user change `active`.
`study-status replan` → §7.6.

### 7.5 Recovery when behind

Detected in `study-next`. Policy by horizon:

**`flexible` or `open`:** re-projects dates and says so in one line. Fixed external milestones do
not move; it warns what will have been covered by that date.

**`fixed`:** proposes, in order, showing the resulting calendar, and applies only with approval:
1. **Use the buffer** while there is some left.
2. **Double up** — two sessions on one date, only if both are light (by reading time).
3. **Trim** — merge or slim down the lightest ones. Shows what is lost before touching anything.

If that is not enough: says so and offers to raise the cadence or move the date.

### 7.6 Replan

`study-status replan`: asks again only for cadence and horizon, recalculates the projection,
and if the end is `fixed` and it does not fit, goes into §7.5. **It does not regenerate
content**: it moves dates and, if needed, trims.

### 7.7 Write table

| Command | Frontmatter | `PLAN.md` | `~/.study/` |
|---|---|---|---|
| `study-new` | creates | creates | `plans`, `active` |
| `study-next` | `status`, `actual_date`, `planned_date` if it re-projects | Current state; Calendar if it re-projects | — |
| `study-eval` | `eval_*` | Log; Concepts to fix; Current state | — |
| `study-close` | `status: closed` | Current state; Block closures | — |
| `study-status` | — | Calendar on replan | `active` if it changes |

## 8. Practice — three levels

Chosen per **area** according to declared access, not per topic. Optional per session: the
session is complete without it and it does not affect the threshold.

| Level | When | What it generates |
|---|---|---|
| `live` | Real access to the area | Exercises against the user's environment, commented so the output teaches. **Read-only** if the environment is shared or production; free if it is the learner's disposable local project. They must run as-is (§13) |
| `sandbox` | No access, but a free or local alternative exists and is **verifiable** | Free tier, official playground, local emulator, online console |
| `none` | Nothing to touch, or a conceptual topic | *Explain it to me in your own words* + worked examples with real output taken from the official source |

If a `live` command fails for permissions, the skill treats it as **data**: it notes it in the
session, downgrades the area to `sandbox` or `none`, and does not propose access to that again.
If a command has a cost (APIs that charge per request), the user is warned before it is suggested.

## 9. Cross-cutting rules

1. **Never make up** URLs, exam facts, prices or service names. Verify, or say it could not be
   verified.
2. **Errors one at a time**, from simplest to most complex, waiting for a reply.
3. **Notes in the user's own words**, not generic summaries.
4. **State in frontmatter**; `PLAN.md` is regenerated, not edited by hand.
5. **Nothing is published** outside the local disk.
6. **Degradation**: if `AskUserQuestion` is not available, ask in plain text with the same
   options.
7. **Language**: structure in English, content in the plan language, conversation in the
   language of the user's latest message, `SKILL.md` in English (`references/language.md`).

## 10. Out of scope (deliberate)

Pausing or archiving plans · syncing between machines · notifications or reminders ·
publishing to Jira or Slack · support for Cursor/Codex · several users on the same plan ·
what §12.8 excludes (YouTube, video refresh, learning preference).
They get added if they are needed, not before.

## 11. Distribution

- The repo ships `install.sh`, which copies (or links, with `--link`) the six `study-*` folders
  into `~/.claude/skills/`. `INSTALL.md` explains the same steps so an agent can follow them.
- It is installed only in `~/.claude/skills/` (Claude Code). It does not apply to
  `~/.agents/skills/`.

## 12. Videos per session

> Approved in conversation on 2026-09-23. Built together with iteration 2.

### 12.1 Purpose

That each session, besides its official readings, points to **which course and which video
class** serve that topic, chosen by comparing the session's topic with the content of each class.

### 12.2 Decisions

| Decision | Value |
|---|---|
| Time | The session estimate counts **readings only**. Videos carry their own duration, shown |
| Weight | Optional but **not dismissable**: for some people audiovisual material is the main thing. They are curated with the same care as the readings and shown at the same level |
| Timing | Looked up **when the plan is created** (`study-new`) and written into each session |
| Platforms v1 | **Platzi** (automatic lookup) + **manual paste** of the index of any other one |
| Learning preference | Not asked: every session shows videos and readings at the same level |

### 12.3 Interview

Question 7 of Screen 3 (§4.1): *Do you have access to a course platform?* → Platzi · another one
(you paste the index) · none. Multi-select. "None" looks up nothing.

### 12.4 Platzi flow

After the syllabus is approved and the sessions are chunked:

1. **Catalogue.** Download `https://platzi.com/sitemap-cursos.xml` (~1,600 courses). Cached in
   `~/.study/cache/platzi/` with a date; reused if it is less than 7 days old.
2. **Candidates.** The model picks courses from the catalogue by the plan's topic and opens the
   page of the best ones (title, description, level) to decide. **They are shown to the user for
   approval**, like the syllabus: one **main** course and at most **two complementary** ones that
   fill gaps.
3. **Indexes.** One request per approved course. The course page lists each class with number,
   real title and duration (link `href="/cursos/<curso>/<clase>/"` with text `N Título MM:SS min`).
   Saved in `<plan>/material/videos-index.json`: only number, title, duration, URL and course.
4. **Assignment.** The model assigns classes to each content session according to its checklist.
   If a title is not enough to decide, it reads that class's **written summary** (public, below
   the video) and **does not store it**. The main course is preferred; complementary ones only
   fill gaps.
5. **Honest coverage.** Each session says what the videos cover and what they do not. If no
   video fits a topic, it says so instead of filling in with a similar one.

Budget: between 5 and 20 requests to Platzi per plan. Never download the ~32,000 classes.

Facts verified on 2026-09-23 that shape the design:
- The `meta description` of a class page is **the course's**, not the class's. What is specific
  to the class is the title and the summary in the page body.
- URL slugs **do not match** the real title (classes are renamed without changing the URL).
  Matching is done on real titles, never by filtering slugs by keyword.

### 12.5 Manual paste (any other platform)

The user copies the index shown on their course page (Udemy, Coursera, an internal course) and
pastes it. The model interprets it tolerantly (sections, classes, durations and URLs if present)
and assigns it the same way as in 12.4, step 4. Nothing is queried outside. It is saved in the
same `videos-index.json` with a `platform` field that records the origin.

### 12.6 Videos section in the session

- Session header: `Lectura ~N min · Videos ~M min (opcional)` (in the plan language; in English,
  `Reading ~N min · Videos ~M min (optional)`).
- Frontmatter: `video_minutes: M` (sum of durations; it enters no time calculation).
- Table: class (number + title), course, duration, link.
- Coverage line: *Covers: … · Not covered: … → stick to the reading*.
- `study-next` presents the videos **with the same weight** as the readings, not as a footnote.
- Buffer sessions carry no new videos.

### 12.7 Rules

1. **Never copy content from the platform.** Only title, duration and URL. Summaries are read to
   decide and are not written to any file. Platzi's terms do not mention bots or AI, but they
   forbid copying or reproducing its content in whole or in part.
2. **Identify honestly.** The skill's own User-Agent; never disguised as a browser.
3. **Few requests and a cache.** A 2-3 s pause between requests.
4. **If the platform blocks, the plan still comes out.** Platzi uses Cloudflare Bot Management,
   which returns intermittent 403s. Retry twice with a pause; if it is still blocked, generate
   the plan without videos and note it in `PLAN.md`. Asking later "agrega los videos" ("add the
   videos") retries only that lookup; it is not a general refresh command.
5. **URLs come from the course page queried that same day**: they need no further per-class
   verification.
6. **Videos age.** The official documentation remains the source of truth; if a video
   contradicts the reading, the reading wins and the session warns about it.

### 12.8 What it does not do (deliberate)

YouTube or other video APIs (they require a per-person API key; left for later) · a video
refresh command · asking for learning preference · playing the video · storing summaries or
descriptions from the platforms.

### 12.9 Files touched

`study-shared/scripts/platzi.py` (catalogue with cache + a course's index, standard library
only) · `study-shared/references/videos.md` (new) · `study-shared/templates/session.md`
(Videos section, `video_minutes`) · `study-shared/references/frontmatter.md` ·
`study-shared/references/interview.md` · `study-new/SKILL.md` (question and lookup step) ·
`study-next/SKILL.md` (presentation with the same weight as the readings).

## 13. Iteration 2 — protocol, practice and quality decisions

> Taken on 2026-09-23 from the iteration 1 tests and the real use of an AWS CLF-C02 plan. The
> operational detail lives in `references/`; the reasons stay here.

### 13.1 Evaluation

| Topic | Decision | Why |
|---|---|---|
| Re-evaluation | 2 questions per weak concept (min 4, max 10), threshold `threshold_session` | "Short" was not a size; each session resolved it differently |
| When to re-evaluate | Recommended at the start of the next session, not right after the review | Right after measures short-term memory |
| Attempt history | `eval_score` = last; `eval_attempts` = count; one line per attempt in *Result*; the log keeps them all | The re-eval overwrote the first score |
| Concept steps | At most one per evaluation | Getting it right twice in the same evaluation is not retention |
| Correct answers marked `?` | Correct for the score and the threshold; an error for concept tracking; every `?` creates a row | It was ambiguous and each session counted it differently |
| `weak` region | Written by `study-eval` on a fail; rewritten by `study-close` on close | `study-next` reviewed a region nobody filled |
| Position of the correct answer | Drawn by `study_state.py answer-key` before writing the options: no letter above its fair share + 1 and never three identical in a row | In a real evaluation 7 of 8 answers were B and the user started answering the pattern |
| Delivery | `--clicks` (`AskUserQuestion`: batches of 3 + "which did you guess?") or `--text` (everything in one message). By default clicks up to 12 questions and text above that; questions with 5+ options and open questions always in text | Clicks remove friction in short evaluations; in 65-question mocks they would be 22 dialogs with no way back, and the real exam lets you review before submitting |

### 13.2 Practice

- `live` distinguishes a **shared or production environment** (read-only) from a **disposable
  local project** (may be modified): the old rule made framework practice useless.
- **Commands run as-is.** Identity is resolved beforehand, and there are never placeholders like
  `<tu-usuario>` in an executable block: zsh takes them as a redirection and the desktop app's
  Run button fails.
- The interview asks **how the learner authenticates** in remote environments (IAM user or
  Identity Center role): commands "on your user" do not apply to someone who comes in through a
  role.

### 13.3 Quality of the content `study-new` generates

- **Every claim in the checklist and the analogy is backed by a reading of the session.** A 200
  from `verify_links.py` proves the page exists, not what it says. Real case: a session claimed
  that changing the support plan was a root-only task, and that is no longer on the official list.
- **Every checklist item has at least one reading** that covers it: two of three errors in a real
  evaluation fell on items without a reading.
- **Localized docs** in the plan language when they exist, with an anchor to the exact section.
- **Milestones against the calendar:** `study_state.py check` validates that every external
  milestone (`milestones:`) has a checkpoint before it. It runs when the plan is generated and
  after every re-projection, because re-projecting can push a checkpoint past its milestone.
- Retired exam version → build against the current one and confirm with the user. Requested
  version that is not the latest → build for the requested one and warn. No official count or
  weights → choose them and declare them as the plan's choice.

| Topic | Decision | Why |
|---|---|---|
| Plan language | Not asked. Inferred from the request (explicit request wins; otherwise the request's language; ask only if genuinely unclear) and confirmed in the summary screen. Conversation follows the user's latest message; files stay in the plan language; `study-close` notes keep the user's words untranslated; Spanish is neutral (*tú*, no voseo). Detail in `references/language.md` | People often study for an exam taken in English while chatting in another language, and a separate language question was one more screen for something the request already says |

### 13.4 Mechanics

- **Dates from `python3 study_state.py today`**, never from `date`: it honours `STUDY_TODAY` in
  tests and avoids time zone errors.
- `check` detects its own placeholders without confusing them with Blade/Jinja, missing dates,
  milestones without a checkpoint, and buffers with an evaluation.
- `verify_links.py` follows redirects (including 308), retries on 429 and distinguishes
  `REDIRECT`, `RATE-LIMITED`, `BLOCKED` and `SPA?` from `BAD`: before, it accepted redirects to
  another page and made-up routes on SPA sites.
- Localized templates: fixed texts come from `references/labels.md` (es/en/pt) instead of being
  translated by hand in each plan.
- In `study-next`: the session is marked first and the reply comes after; an incomplete session
  is not marked `studied`; optional warm-up after 7 days without activity
  (`days_since_last_activity`, which takes the most recent date among opening, evaluation and
  closing: a session can stay open for several days); links are not re-verified.

## 14. Reference

The real AWS CLF-C02 plan that gave rise to this family is the reference example for *content
quality* (analogies, commented commands, verified readings, protocol). It is **not** a reference
for structure: it uses folders per week and dates in file names, which this design replaces with
flat sessions and state in frontmatter.
