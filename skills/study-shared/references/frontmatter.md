# Frontmatter, regions, registry and scripts

Read this before touching any plan file. Everything the `study-*` skills know about a plan's
state comes from here. If you improvise a field or hand-edit a regenerated block, the other
commands will disagree with you.

Paths below use `SHARED="$HOME/.claude/skills/study-shared"` and `SS="$SHARED/scripts/study_state.py"`.

## Where things live

```
<plan>/PLAN.md                          plan config in frontmatter + sections + regenerated regions
<plan>/sessions/session-NN-<slug>.md    one per session; its state lives in its frontmatter
<plan>/diagnostic.md                    only if a diagnostic or prerequisite check ran
<plan>/material/                        copies of files the user provided
<plan>/material/videos-index.json       video classes chosen for the plan (titles, durations, URLs only)
~/.study/plans                          registry: <slug><TAB><absolute path>, one per line
~/.study/active                         slug of the active plan
~/.study/cache/platzi/cursos.json       Platzi course catalog, reused for 7 days
```

`STUDY_HOME` overrides `~/.study` (tests use it). `STUDY_TODAY=YYYY-MM-DD` overrides "today".

**Always take today's date from the script**, `python3 $SS today`, never from `date`. Otherwise
tests with a simulated date, and anyone working after midnight in another timezone, write wrong dates.

## Session frontmatter

| Key | Type | Meaning |
|---|---|---|
| `session` | int | 0-based or 1-based position in the queue (0 = prerequisite session) |
| `slug`, `title` | str | slug is kebab-case; title is human, in the plan's language |
| `status` | enum | `pending` → `studied` → `evaluated` → `closed`. **studied = opened and delivered**, not learned |
| `planned_date` | date | projection; rewritten by `project` |
| `actual_date` | date/null | when `study-next` **opened** it (not when it closed) |
| `block` | int | checkpoint block it belongs to; 0 if the plan has no blocks or for prerequisites |
| `is_buffer` | bool | recovery/review session: no new content, `eval_type: none` |
| `is_checkpoint` | bool | closes a block; its eval is `checkpoint`, `mock` or `integrative` |
| `eval_type` | enum | `session` · `checkpoint` · `mock` · `integrative` · `none` |
| `eval_score` | str/null | score of the **last** attempt, e.g. `6/6` |
| `eval_passed` | bool/null | null until taken |
| `eval_attempts` | int | how many evaluations were taken (first + re-evaluations) |
| `eval_date` | date/null | date of the last attempt |
| `closed_date` | date/null | when `study-close` closed it |
| `practice_level` | enum | `live` · `sandbox` · `none`, decided per area in the interview |
| `video_minutes` | number | total of the Videos section; never added to the session time |

Transitions: `pending → studied` (study-next) · `studied → evaluated` (study-eval, on pass) ·
`evaluated → closed` (study-close). Sessions with `eval_type: none` go `studied → closed`.
A failed evaluation leaves `studied` with `eval_passed: false`.

## PLAN.md frontmatter

Plan configuration (see `templates/plan.md`). Thresholds and evaluation sizes live here so
`study-eval` reads them instead of hardcoding. Keys added in iteration 2:

- `milestones`: external dates (1:1s, reviews), comma-separated `YYYY-MM-DD`, or `null`.
  `check` verifies that each one has a checkpoint session planned before it.
- `video_platforms`: `platzi,manual` · `platzi` · `manual` · `none`.
- `videos_status`: `ok` · `unavailable` (the lookup was blocked; retry on request) · `none`.

`cadence` grammar: `daily` · `weekdays` · `days:mon,wed,fri` · `per_week:N`.

## Regions

Marked with HTML comments so headings can be in any language. Keep the marker lines verbatim
and write only between them.

| Region | File | Written by |
|---|---|---|
| `state` | PLAN.md | `study_state.py` (refresh/project). Never by hand |
| `calendar` | PLAN.md | `study_state.py` (refresh/project). Never by hand |
| `concepts` | PLAN.md | `study-eval` (rows and status changes) |
| `log` | PLAN.md | `study_state.py log`, called by `study-eval` |
| `videos` | session | `study-new`, or a retry after `videos_status: unavailable` |
| `eval-block` | session | `study-new` (from `labels.md`, per `eval_type`) |
| `result` | session | `study-eval`, one line per attempt |
| `notes` | session | `study-close`, in the user's own words |
| `weak` | session | `study-eval` **when the user misses the threshold**; rewritten by `study-close` |

## The state script

```bash
python3 $SS today                              # today's date (honours STUDY_TODAY)
python3 $SS registry list                      # all plans, * marks the active one
python3 $SS registry add <slug> <path> [--replace]
python3 $SS registry active [slug]             # get or set the active plan
python3 $SS registry resolve [slug]            # plan path; exit 2 = ambiguous, 3 = none

python3 $SS next   <plan>                      # JSON: next non-closed session, behind/ahead, buffer_left, horizon,
                                               #       last_activity, days_since_last_activity
python3 $SS status <plan>                      # JSON: everything, incl. projected_end at the real pace
python3 $SS sessions <plan>                    # JSON: all session frontmatter
python3 $SS check  <plan>                      # JSON {ok, issues}; exit 1 if any issue

python3 $SS set <file> status=studied actual_date=$(python3 $SS today)   # typed: null/true/false/int/str
python3 $SS project <plan> [--start DATE] [--cadence C] [--from-session N]
python3 $SS refresh <plan>                     # regenerate state + calendar regions
python3 $SS log <plan> "| 2026-09-22 | 07 | session | 8/10 | true | 1 | 3,5 |"
python3 $SS answer-key 4 4 5:2 -                # JSON: where each correct option goes (protocol.md)
```

- `project` only touches non-closed sessions. Without `--from-session` it starts at the lowest
  session number, so a session 0 gets a date too. It also refreshes state and calendar.
- `check` reports: `placeholder` (a `{{lower_snake}}` left in PLAN.md, diagnostic.md or a
  session; Blade/Jinja `{{ $x }}` is ignored), `missing_date`, `milestone_without_checkpoint`,
  `buffer_with_eval`. Run it after generating a plan and after every re-projection.
- `last_activity` is the latest `actual_date`, `eval_date` or `closed_date` across all sessions;
  use `days_since_last_activity` for "how long since they studied", never a single `actual_date`.
- Run `refresh` after any `set`.

## Verifying links

`python3 $SHARED/scripts/verify_links.py URL…` prints `STATUS CODE URL [-> FINAL_URL]`:

| Status | Meaning | What to do |
|---|---|---|
| `OK` | 2xx; no redirect, or only a cosmetic one | use it |
| `REDIRECT` | ends on a different page | write `FINAL_URL` if it is the same content under a new address; drop it if it is a different page |
| `RATE-LIMITED` | 429/503 after retries | unverified today: do not drop an official source for this alone; say it is unverified |
| `BLOCKED` | 401/403 | bot wall or login; same as above |
| `SPA?` | the host answers an invented path with the same title | a 200 proves nothing: confirm the page exists another way (sitemap, the site's own index, a specific title) or drop it |
| `BAD` | 404, 5xx, network error | drop it |

Exit code: 0 all OK · 1 any `BAD` · 2 no `BAD` but something is not `OK`.

## Platzi

`python3 $SHARED/scripts/platzi.py` implements the lookups in `references/videos.md`:
`catalog [--refresh]`, `course <slug>`, `summary <class-url>`. Exit code 3 = Platzi refused or
failed after retries: generate the plan without videos and set `videos_status: unavailable`.
