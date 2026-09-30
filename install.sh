#!/usr/bin/env bash
# Install the study-* skills into Claude Code's personal skills folder.
# Usage: ./install.sh [--link] [--force] [--uninstall] [--check]
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
BACKUP_ROOT="${STUDY_HOME:-$HOME/.study}/backup"
SKILLS=(study-shared study-new study-next study-eval study-close study-status)

mode=copy force=0
for arg in "$@"; do
    case "$arg" in
        --link) mode=link ;;
        --force) force=1 ;;
        --uninstall) mode=uninstall ;;
        --check) mode=check ;;
        -h|--help) sed -n 2,3p "$0" | sed 's/^# //'; exit 0 ;;
        *) echo "unknown option: $arg" >&2; exit 2 ;;
    esac
done

check_python() {
    if ! command -v python3 >/dev/null; then
        echo "error: python3 not found. The skills need Python 3.9 or newer." >&2; exit 1
    fi
    python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' || {
        echo "error: $(python3 --version) is too old; the skills need Python 3.9 or newer." >&2; exit 1; }
}

verify() {
    local missing=0
    for s in "${SKILLS[@]}"; do
        if [ -f "$DEST/$s/SKILL.md" ]; then echo "  ok  $s"; else echo "  --  $s (missing)"; missing=1; fi
    done
    [ "$missing" -eq 0 ] || { echo "error: installation incomplete in $DEST" >&2; exit 1; }
    python3 "$DEST/study-shared/scripts/study_state.py" today >/dev/null
    echo "study_state.py runs: ok"
}

case "$mode" in
    check)
        check_python; verify ;;
    uninstall)
        for s in "${SKILLS[@]}"; do
            if [ -L "$DEST/$s" ] || [ -d "$DEST/$s" ]; then rm -rf "$DEST/$s"; echo "removed $DEST/$s"; fi
        done
        echo "Your plans and ~/.study were not touched." ;;
    copy|link)
        check_python
        mkdir -p "$DEST"
        existing=()
        for s in "${SKILLS[@]}"; do
            if [ -e "$DEST/$s" ] || [ -L "$DEST/$s" ]; then existing+=("$s"); fi
        done
        if [ "${#existing[@]}" -gt 0 ]; then
            if [ "$force" -eq 0 ]; then
                echo "already installed in $DEST: ${existing[*]}" >&2
                echo "run again with --force to replace them (a backup is kept in $BACKUP_ROOT)." >&2
                exit 1
            fi
            backup="$BACKUP_ROOT/skills-$(date +%Y%m%d-%H%M%S)"
            mkdir -p "$backup"
            for s in "${existing[@]}"; do mv "$DEST/$s" "$backup/"; done
            echo "previous version moved to $backup"
        fi
        for s in "${SKILLS[@]}"; do
            if [ "$mode" = link ]; then ln -s "$REPO/skills/$s" "$DEST/$s"; else cp -R "$REPO/skills/$s" "$DEST/$s"; fi
        done
        echo "installed (${mode}) in $DEST:"
        verify
        cat <<'USAGE'

Open a new Claude Code session, then:
  /study-new      create a plan (or just say "I want to study ...")
  /study-next     open the next session
  /study-eval     evaluate it; answer mode:
                    --clicks  choose options in dialogs (default up to 12 questions)
                    --text    all questions in one message (default for mocks and diagnostics)
                    e.g. /study-eval mock --clicks
  /study-close    close the session with your own notes
  /study-status   progress, projected end, switch plan, replan

Files are written in the language you ask in; the conversation follows yours.
USAGE
        ;;
esac
