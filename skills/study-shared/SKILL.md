---
name: study-shared
description: Shared resources for the study-* skill family (study-new, study-next, study-eval, study-close, study-status) — templates, labels, the state and lookup scripts, and the protocol references they all follow. Not user-invocable; it exists so the other skills know where their pieces live.
user-invocable: false
---

# study-shared

Everything the `study-*` skills have in common lives here, once.

```
study-shared/
├── DESIGN.md                 the approved spec (Spanish). Source of truth when in doubt
├── scripts/
│   ├── study_state.py        state engine: today, registry, next/status, check, set, project, refresh, log,
│   │                         answer-key
│   ├── verify_links.py       every URL goes through this before it is written into a plan
│   └── platzi.py             Platzi course catalog, course index and class summary (videos)
├── templates/
│   ├── plan.md               PLAN.md: frontmatter config + regenerated regions
│   ├── session.md            one per session; state in frontmatter
│   └── diagnostic.md         baseline record
└── references/
    ├── frontmatter.md        fields, transitions, region owners, script usage  ← read first, always
    ├── interview.md          the 4-screen interview, source rules, diagnostic by level
    ├── protocol.md           evaluation types, re-evaluation, grading, concepts lifecycle, what gets written
    ├── recovery.md           drift policy by horizon, buffer, doubling, trimming, replan, milestones
    ├── practice-levels.md    live / sandbox / none; commands that run as-is
    ├── videos.md             videos per session: Platzi lookup, pasted index, rules
    └── labels.md             fixed template text in es / en / pt
```

Resolve the paths from any skill with:

```bash
SHARED="$HOME/.claude/skills/study-shared"
SS="$SHARED/scripts/study_state.py"
```

Conventions the whole family depends on:

- **State lives in frontmatter; PLAN.md regions are regenerated.** Region owners are listed in
  `references/frontmatter.md`; nobody else writes between those markers.
- **Structure in English, content in the plan's language.** File names, frontmatter keys and
  markers are identifiers; headings and fixed prose come from `references/labels.md`.
- **Dates come from `python3 $SS today`**, never from `date`.
- **Spanish means neutral Spanish** (*tú*, no voseo, no regionalisms), in plans and in replies.
  The rule and its examples are at the top of `references/labels.md`.
