# Installation — instructions for the agent

> If you are an agent (Claude Code) and were handed this repo to install, follow these steps in
> order. If you are a person, the [README](README.md) has the same, shorter. Talk to the user in
> their language throughout.

## What gets installed

Six skill folders in `~/.claude/skills/`:
`study-shared`, `study-new`, `study-next`, `study-eval`, `study-close`, `study-status`.
No dependencies or packages are installed, no settings are changed, and nothing leaves the local
disk. The user's plans live wherever they choose; the plan registry lives in `~/.study/`.

## Requirements (check them before installing)

1. **Claude Code** (terminal, desktop app, or web with a local repo). The skills use the
   `AskUserQuestion` tool: they are not meant for Cursor, Codex or `~/.agents/skills/`.
2. **Python 3.9 or newer** as `python3`, standard library only:
   ```bash
   python3 --version
   ```
3. **bash** for `install.sh` (macOS and Linux ship it; on Windows, use WSL or Git Bash).

If one is missing, tell the user and stop.

## Steps

1. Clone the repo if it is not on disk yet (the user picks the folder):
   ```bash
   git clone https://github.com/kleyver14/study-skills.git study-skills
   cd study-skills
   ```
2. Check for an existing installation:
   ```bash
   ls -d ~/.claude/skills/study-* 2>/dev/null
   ```
   If anything shows up, **ask the user** before replacing it. With their approval, use
   `--force`: the script moves the previous version to `~/.study/backup/skills-<date>/`, it does
   not delete it.
3. Install. Choose the mode with the user:
   - **Copy** (default): independent from the repo.
     ```bash
     ./install.sh
     ```
   - **Link** (`--link`): symlinks into the repo; a `git pull` updates the skills. Useful if the
     user will modify them or wants to follow updates. Do not move or delete the repo afterwards.
     ```bash
     ./install.sh --link
     ```
4. Verify. The script already does it at the end; to repeat it:
   ```bash
   ./install.sh --check
   ```
   It must list the six skills with `ok` and end with `study_state.py runs: ok`.
5. Optional, recommended when installed with `--link` or after changing anything:
   ```bash
   cd tests && python3 -m unittest test_study_state test_verify_links test_platzi
   ```
   It runs offline (a local HTTP server and synthetic fixtures).
6. Tell the user, in their language:
   - to **open a new Claude Code session** (skills load at startup) and start with `/study-new`,
     or just with "I want to build a study plan for …";
   - the five commands and the cycle `/study-next` → study → `/study-eval` → `/study-close`
     (the README's *Usage* table);
   - **how evaluations are answered**: `/study-eval --clicks` to click the options,
     `/study-eval --text` for every question in one message. Without a flag: clicks up to 12
     questions, text for mocks and diagnostics. Saying it in words works too;
   - **languages**: the plan's files are written in the language the plan is requested in (or
     the one they ask for explicitly), and the conversation follows whatever language they write
     in. Spanish, English and Portuguese have fixed texts; other languages get English labels or a
     one-time translation.

## Update

- Installed with `--link`: `git pull` in the repo, nothing else.
- Installed as a copy: `git pull`, then `./install.sh --force`.

Existing plans are not modified by an update.

The installed version is in the repo's `VERSION` file (`./install.sh --check` prints it), and
[CHANGELOG.md](CHANGELOG.md) lists what changed in each one. Tell the user what changed.

## Uninstall

```bash
./install.sh --uninstall
```

Removes only the six `study-*` folders. It does **not** touch the user's plans or `~/.study/`; if
the user wants those gone too, they delete them themselves.

## Manual installation (without `install.sh`)

```bash
mkdir -p ~/.claude/skills
cp -R skills/study-* ~/.claude/skills/
python3 ~/.claude/skills/study-shared/scripts/study_state.py today
```

The last command must print today's date (`YYYY-MM-DD`).

## Environment variables (optional)

| Variable | Purpose |
|---|---|
| `CLAUDE_SKILLS_DIR` | Install somewhere other than `~/.claude/skills` (`install.sh`) |
| `STUDY_HOME` | Use another folder instead of `~/.study` for the registry and cache |
| `STUDY_TODAY` | Pin "today" to `YYYY-MM-DD` (tests) |
