# The interview — study-new

Goal: collect only what changes the output, in four `AskUserQuestion` screens plus three
conversational steps. The tool always adds an "Other" option for free text. If
`AskUserQuestion` is not available, ask the same questions in plain text with the options listed.

The user may already have said things in the conversation (topic, deadline, "I know some of
this"). Pre-fill from that and confirm instead of re-asking.

## Screen 1 — goal and sources

1. **What do you want to learn, and what for?** → `goal_type`
   exam/certification · master a tool or technology · a book or course · other
2. **Is there an official guide? Do you have your own material?**
   official guide exists (I'll find it) · I have links/files/images · both · neither

## Conversational — proposed syllabus (nothing is generated before approval)

Build the syllabus from the source cascade, show it as areas → subtopics (with official weights
when they exist), and iterate until the user approves.

### Source cascade

1. **Official**: exam blueprint, canonical docs, published syllabus. Find it, extract from it,
   cite it. For objective tables, **download the raw HTML** (curl or the fetch tool's raw mode):
   summarised fetches drop rows.
2. **Provided**: the user's links, files and images. Verify the links and copy the files into
   `material/`. Provided material **joins** the official syllabus; it does not replace it.
3. **Built**: from your own knowledge, marked `built` in Sources and validated more carefully.

### Rules while building it

- **Every URL goes through `verify_links.py`** before it is written anywhere. Act on its status
  as `frontmatter.md` describes (`REDIRECT` → write the final URL or drop it; `SPA?` → confirm
  another way or drop it; `RATE-LIMITED`/`BLOCKED` → keep an official source but mark it unverified).
- **Retired version.** If the official source shows that the exam or edition the user named is
  retired or replaced, build against the current one, **say so before generating**, and ask the
  user to confirm what they actually booked.
- **Not the latest version.** If the user asked for a version that is not the newest (Laravel 12
  when 13 exists), build for the one they asked for and mention that a newer one exists.
- **No published weights or question count.** Use the share of sub-objectives as a proxy, or
  choose a number, and label it as the plan's choice, not an official figure.
- **Documentation in the plan's language.** If an official localized version exists (for AWS,
  `docs.aws.amazon.com/es_es/...` for Spanish), prefer it, linking to the exact section with its
  anchor. Fall back to the original language when there is none.
- **Sources table.** When dozens of pages come from the same site, you may group them in one row
  (`docs.aws.amazon.com/IAM/* — 14 pages, verified 2026-09-23`).

## Screen 2 — time and level

3. **By when?** → `horizon`
   an exact date (`fixed`) · roughly, like "about 3 months" (`flexible` → target week) · no date (`open`)
4. **Which days or how many times a week, and how long per session?** → `cadence`, `session_minutes`
   daily · weekdays · 3×/week · 2×/week, plus free text for specific days and minutes
5. **Where do you start?** → diagnostic mode (table below)
   from zero · I know some parts · I already work with this

## Conversational — reality check

available = sessions the cadence yields inside the horizon (for `open`, just report the count).
needed ≈ syllabus items × minutes each ÷ `session_minutes`, plus 10-15% buffer.
Say plainly: surplus (room to go deeper), fits, or shortfall (offer to trim the syllabus, raise
the cadence or extend the horizon). For `fixed`, do not generate a plan that does not fit: make
the user choose. Mocks take the real exam's duration, even beyond `session_minutes`.

## Screen 3 — practice, videos and follow-up

6. **Which of these do you have real access to, for practice?** Multi-select over the approved
   areas, plus "none of it". The tool allows 4 options per question: group areas into up to 4
   affinity groups, or split them across two questions. → `practice_level` per area (see
   `practice-levels.md`). **Shortcut for local tools:** for a framework or language that installs
   locally for free, ask instead "can you install it on your machine?"; yes → `live` everywhere.
   - **If any `live` area is a remote or cloud environment, also ask how they authenticate**
     (for AWS: IAM user, or IAM Identity Center / SSO role). It decides which practice commands
     apply to them.
7. **Do you have access to a video course platform?** Multi-select: Platzi · another one (you
   paste the course index) · none. → `video_platforms`; "none" means no video lookup. See `videos.md`.
8. **Does anyone track your progress, or do you have report dates?** *(not required)*
   yes, on these dates · no, personal commitment. Yes → write the dates to `milestones:` and use
   them to define blocks. No → propose internal checkpoints every 6-10 sessions purely for
   pacing, which the user can decline.

If screen 3 would exceed 4 questions, move question 8 to screen 4.

## Screen 4 — location and language

9. **Where should I save it?** Propose `~/estudio/<slug>/` (or `~/study/<slug>/` for English
   speakers) and `./<slug>/`; accept any path.
10. **Language of the plan?** Default: the language the user is speaking right now.

## Conversational — summary and confirmation

One screen with everything decided: goal, sources (with kinds), syllabus size, horizon, cadence,
sessions available vs needed, buffer count, diagnostic mode, practice level per area, how they
authenticate, video platforms and the proposed courses, milestones and checkpoints, path,
language. Generate only after an explicit yes.

## Diagnostic by declared level

| Declared | What runs | Effect on order |
|---|---|---|
| already works with it | full diagnostic, 20-25 questions across all areas, weighted | weakest area first; failures seed *Concepts to fix* |
| knows some parts | ask which areas; diagnose only those | those areas by weakness, the rest by dependency |
| from zero | **no topic quiz**; prerequisite check instead | missing prerequisites become session(s) 0, or a warning if the gap is large; order by dependency |
| reports scores already taken | record them (mode `external`) | same as "already works with it" |

**Prerequisite check format:** 3 questions per prerequisite, with `?` marks like any evaluation.
A prerequisite fails with 2 or more wrong or guessed answers.

A written baseline always ends up in `diagnostic.md`, even from zero (*0 on the topic;
prerequisites: X ✓ Y ✗*). If someone declares a high level and scores under 50%, say so plainly
and propose treating those areas as from zero. Users overestimate their level: the numbers
decide, not the declaration.

**Checkpoint type for early milestones.** In a from-zero plan, a milestone that falls before most
of the content has been studied gets a `checkpoint`, not a `mock`: a full mock on day 5 measures
nothing useful yet.
