#!/usr/bin/env bash
# Install the study-* skills into Claude Code's personal skills folder.
# Usage: ./install.sh [--link] [--force] [--panel] [--uninstall] [--check]
#   --panel  also install (or update, or with --uninstall remove) the optional study panel
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
BACKUP_ROOT="${STUDY_HOME:-$HOME/.study}/backup"
SKILLS=(study-shared study-new study-next study-eval study-close study-status)
PANEL="study-companion@study-skills"
# Claude Code reads a folder marketplace in place: keep the panel where deleting the download cannot break it.
PANEL_HOME="${STUDY_HOME:-$HOME/.study}/panel"

mode=copy force=0 panel=0
for arg in "$@"; do
    case "$arg" in
        --link) mode=link ;;
        --force) force=1 ;;
        --panel) panel=1 ;;
        --uninstall) mode=uninstall ;;
        --check) mode=check ;;
        -h|--help) sed -n 2,4p "$0" | sed 's/^# //'; exit 0 ;;
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

# The version travels inside study-shared, so the installed copy knows its own.
installed_version() { cat "$DEST/study-shared/VERSION" 2>/dev/null || echo "unknown (0.2.0 or older)"; }
folder_version() { cat "$REPO/skills/study-shared/VERSION"; }

panel_version() {
    claude plugin list 2>/dev/null | grep -A4 "$PANEL" | sed -n 's/.*Version: *//p' | head -n 1
}

has_claude() {
    command -v claude >/dev/null || {
        echo "panel: the 'claude' command was not found; install Claude Code, then run ./install.sh --panel" >&2
        return 1
    }
}

panel_installed() {
    claude plugin list 2>/dev/null | grep -q "$PANEL"
}

# Copy the panel to PANEL_HOME, register it there, then install it or bring it up to date.
install_panel() {
    has_claude || return 0
    rm -rf "$PANEL_HOME"
    mkdir -p "$PANEL_HOME/mods"
    cp -R "$REPO/.claude-plugin" "$PANEL_HOME/"
    cp -R "$REPO/mods/study-companion" "$PANEL_HOME/mods/"
    rm -rf "$PANEL_HOME/mods/study-companion/.claude-plugin/types"
    claude plugin marketplace add "$PANEL_HOME" >/dev/null
    claude plugin marketplace update study-skills >/dev/null
    if panel_installed; then
        claude plugin update "$PANEL"
    else
        claude plugin install "$PANEL"
    fi
    echo "panel: ready in new sessions; open it with /study-panel"
}

case "$mode" in
    check)
        check_python
        if [ -f "$DEST/study-shared/SKILL.md" ]; then
            verify
            echo "installed version: $(installed_version)"
        else
            echo "skills: not installed in $DEST"
        fi
        echo "this folder: $(folder_version)"
        if command -v claude >/dev/null && panel_installed; then
            echo "panel: installed ($(panel_version))"
        else
            echo "panel: not installed (optional: ./install.sh --panel)"
        fi ;;
    uninstall)
        for s in "${SKILLS[@]}"; do
            if [ -L "$DEST/$s" ] || [ -d "$DEST/$s" ]; then rm -rf "$DEST/$s"; echo "removed $DEST/$s"; fi
        done
        if [ "$panel" -eq 1 ] && has_claude; then
            if panel_installed; then claude plugin uninstall "$PANEL"; fi
            claude plugin marketplace remove study-skills >/dev/null 2>&1 || true
            rm -rf "$PANEL_HOME"
        fi
        if [ "$panel" -eq 1 ]; then echo "Your plans and the rest of ~/.study were not touched."; else echo "Your plans and ~/.study were not touched."; fi ;;
    copy|link)
        check_python
        mkdir -p "$DEST"
        existing=()
        for s in "${SKILLS[@]}"; do
            if [ -e "$DEST/$s" ] || [ -L "$DEST/$s" ]; then existing+=("$s"); fi
        done
        if [ "${#existing[@]}" -gt 0 ] && [ "$force" -eq 0 ]; then
            if [ "$panel" -eq 1 ]; then
                echo "skills already installed in $DEST; left as they are (--force replaces them)."
                install_panel
                exit 0
            fi
            echo "already installed in $DEST: ${existing[*]}" >&2
            echo "run again with --force to replace them (a backup is kept in $BACKUP_ROOT)." >&2
            exit 1
        fi
        if [ "${#existing[@]}" -gt 0 ]; then
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
        echo "version: $(installed_version)"
        if [ "$panel" -eq 1 ]; then install_panel; fi
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
        if [ "$panel" -eq 0 ]; then
            echo "Optional: a study panel with your progress and buttons (/study-panel): ./install.sh --panel"
        fi
        ;;
esac
