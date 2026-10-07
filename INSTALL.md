# Installation — instructions for the agent

> If you are an agent (Claude Code) and were handed this repo to install or update, follow these
> steps in order. If you are a person, the [README](README.md) has the same, shorter. Talk to the
> user in their language throughout.

## What gets installed

- Six skill folders in `~/.claude/skills/`: `study-shared`, `study-new`, `study-next`,
  `study-eval`, `study-close`, `study-status`.
- Optionally, the study panel: a Claude Code plugin kept in `~/.study/panel/`.

No dependencies or packages are installed and nothing leaves the local disk. The user's plans
live wherever they choose; the plan registry lives in `~/.study/`.

## Requirements (check them before installing)

1. **Claude Code** (terminal, desktop app, or web with a local repo). The skills use the
   `AskUserQuestion` tool: they are not meant for Cursor, Codex or `~/.agents/skills/`.
2. **Python 3.9 or newer** as `python3`, standard library only:
   ```bash
   python3 --version
   ```
3. **bash** for `install.sh` (macOS and Linux ship it; on Windows, use WSL or Git Bash).

If one is missing, tell the user and stop.

## Step 0 — get the files and see what is there

1. Clone the repo if it is not on disk yet (the user picks the folder):
   ```bash
   git clone https://github.com/kleyver14/study-skills.git study-skills
   cd study-skills
   ```
2. From that folder:
   ```bash
   ./install.sh --check
   ```
   It answers three things:
   - `skills: not installed` → follow **First installation**;
   - `installed version: …` and `this folder: …` → follow **Update** (an older version, or
     `unknown (0.2.0 or older)`) or tell the user they are already up to date (same version);
   - `panel: installed (…)` or `panel: not installed`.

## First installation

1. Choose the mode with the user:
   - **Copy** (default): independent from this folder.
     ```bash
     ./install.sh
     ```
   - **Link** (`--link`): symlinks into this folder, for users who will modify the skills or
     follow the repo with `git pull`. Do not move or delete the folder afterwards.
     ```bash
     ./install.sh --link
     ```
2. **Offer the study panel, and ask first.** It adds `/study-panel`, a panel with the plan's
   state and buttons for the next step, and a status line shown only in study sessions. The
   skills work fully without it. With their yes:
   ```bash
   ./install.sh --panel
   ```
   It needs the `claude` command, and copies the panel to `~/.study/panel/`, so deleting this
   folder afterwards does not break it. (`./install.sh --panel` on the first run installs the
   skills and the panel together.)
3. The script verifies itself at the end: six skills with `ok` and `study_state.py runs: ok`.
   Optional, recommended with `--link` or after changing anything:
   ```bash
   cd tests && python3 -m unittest test_study_state test_verify_links test_platzi
   ```
4. Tell the user, in their language:
   - to **open a new Claude Code session** (skills and the panel load at startup) and start
     with `/study-new`, or just with "I want to build a study plan for …";
   - the five commands and the cycle `/study-next` → study → `/study-eval` → `/study-close`
     (the README's *Usage* table), and `/study-panel` if they installed the panel;
   - **how evaluations are answered**: `/study-eval --clicks` to click the options,
     `/study-eval --text` for every question in one message. Without a flag: clicks up to 12
     questions, text for mocks and diagnostics. Saying it in words works too;
   - **languages**: the plan's files are written in the language the plan is requested in (or
     the one they ask for explicitly), and the conversation follows whatever language they write
     in. Spanish, English and Portuguese have fixed texts; other languages get English labels or a
     one-time translation.

## Update

1. Tell the user the installed version and this folder's version (from `--check`), and what
   changed in between: the [CHANGELOG.md](CHANGELOG.md) entries newer than the installed one
   (all of them up to 0.2.0 when it says `unknown`). Ask before updating.
2. With their yes, replace the skills, and update the panel too if `--check` says it is
   installed:
   ```bash
   ./install.sh --force --panel     # panel installed
   ./install.sh --force             # no panel
   ```
   `--force` moves the previous skills to `~/.study/backup/skills-<date>/`; nothing is deleted.
   If the panel is not installed, this is also the moment to offer it (step 2 of First
   installation).
3. Installed with `--link` from a git clone: `git pull` updates the skills by itself; run
   `./install.sh --panel` only if the panel is installed.
4. Existing plans are never modified by an update. Tell the user to open a **new** session:
   sessions already open keep the version they started with.

## Uninstall

```bash
./install.sh --uninstall           # the six skills
./install.sh --uninstall --panel   # the skills and the panel
```

The user's plans and the plan registry in `~/.study/` are not touched; if the user wants those
gone too, they delete them themselves.

## Manual installation (without `install.sh`)

```bash
mkdir -p ~/.claude/skills
cp -R skills/study-* ~/.claude/skills/
python3 ~/.claude/skills/study-shared/scripts/study_state.py today
```

The last command must print today's date (`YYYY-MM-DD`). The panel has no manual path: it needs
`./install.sh --panel`.

## Environment variables (optional)

| Variable | Purpose |
|---|---|
| `CLAUDE_SKILLS_DIR` | Install somewhere other than `~/.claude/skills` (`install.sh`) |
| `STUDY_HOME` | Use another folder instead of `~/.study` for the registry, cache and panel |
| `STUDY_TODAY` | Pin "today" to `YYYY-MM-DD` (tests) |
