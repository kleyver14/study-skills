# Videos per session — study-new (and a retry on request)

Each content session can point to the course and the class that teach its topic, next to the
official readings. Spec: `DESIGN.md` §12. This file is the operating guide.

**What the user decided, and why it matters for how you write this section:**

- **The session's time estimate counts readings only.** Videos show their own duration.
- **Optional, but not throwaway.** For some people the audiovisual material is the main way they
  learn. Curate videos with the same care as readings and show them at the same level, never as
  a footnote.
- **Looked up once, when the plan is created.**

## When it runs

Only if the interview's platform question (question 7) was answered with Platzi and/or another
platform. `video_platforms: none` → write `_{txt_no_platform}_` in every Videos region and stop.

## Platzi

`P="python3 $HOME/.claude/skills/study-shared/scripts/platzi.py"`

1. **Catalog.** `$P catalog` returns every course as `{slug, url}`, cached for 7 days.
2. **Candidates.** Pick courses whose slug fits the plan's topic, then open the most promising few
   with `$P course <slug>` to read title, description, level and the class list.
   **Never decide from slugs alone**: slugs often do not match the real title (a class slugged
   `instalacion-de-platzistore-con-mongodb` is titled *Configuración de Autenticación en Proyectos
   Mongo y TypeORM*), and a keyword filter pulls in noise (`estrategiamarca` matches "iam").
3. **User approval.** Propose **one main course** and **at most two complementary ones** that
   cover gaps, as you did with the syllabus: *"I'll use X as the main course, and Y for the
   topics X does not cover. OK?"* Prefer one coherent course (same teacher, same thread) over a
   patchwork.
4. **Index.** Save the approved courses' classes to `<plan>/material/videos-index.json`:
   `{"platform": "platzi", "courses": [{slug, title, url, level, classes: [{n, title, duration,
   minutes, url}]}]}`. Titles, durations and URLs only.
5. **Assignment.** For each content session, choose the classes that cover its checklist,
   preferring the main course. When a title is not enough to decide (a session on CloudTrail,
   CloudWatch and Config where no title says CloudWatch), read the class summary with
   `$P summary <class-url>` **to decide, and do not write it anywhere**.
6. **Honest coverage.** State what the videos cover and what they do not. If no class fits a
   topic, write `_{txt_no_video_for_topic}_` rather than padding with a near miss.

Budget: roughly 5-20 requests to Platzi per plan. Never walk the ~32,000 class pages.

### Facts that shape this (verified 2026-09-23)

- One request to a course page returns the full index: number, real title and duration of every
  class, plus the course level.
- A class page's `meta description` is **the course's** description, not the class's. What is
  specific to a class is its title and the written summary below the video.
- Platzi sits behind Cloudflare Bot Management, which answers 403 intermittently. The same URL
  can fail and then work.

## Another platform (pasted index)

Ask the user to copy the index their course page shows (Udemy "Course content", Coursera
syllabus, an internal LMS) and paste it. Read it tolerantly: sections, classes, durations and
URLs when present. Assign it to sessions exactly as in step 5. Nothing is fetched. Save it to
the same `videos-index.json` with `"platform": "<name>"`. When there are no URLs, cite the class
by section and number.

## What goes into each session

- Frontmatter `video_minutes`: the sum of the chosen classes' minutes.
- Header line: `video_line` from `labels.md` (`· Videos ~41 min (optional)`).
- Videos region: `txt_videos_intro`, the table (class number and title, course, duration, link)
  and the coverage line, all from `labels.md`.
- Buffer sessions: no new videos.

## Rules

1. **Never copy platform content.** Only title, duration and URL. Summaries are read to decide
   and never written to any file. Platzi's terms do not mention bots or AI, but they forbid
   copying or reproducing their content in whole or in part.
2. **Identify honestly.** `platzi.py` sends its own User-Agent; do not route around it or
   pretend to be a browser.
3. **Few requests, cached.** `platzi.py` already pauses between requests.
4. **If the platform blocks, the plan still gets generated.** `platzi.py` exits with code 3 after
   its retries. Then write `_{txt_videos_unavailable}_` in the Videos regions, set
   `videos_status: unavailable`, tell the user, and carry on. If they later ask to "add the
   videos", run only this lookup again. It is not a general refresh command.
5. **URLs come from the course page fetched that same day**: no separate per-class verification.
6. **Videos age.** Official documentation stays the source of truth. If a video contradicts a
   reading, the reading wins and the session says so.
