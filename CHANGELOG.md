# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.1] - 2026-10-07

### Added

- `install.sh --panel` installs or updates the study panel; with the skills already installed it
  adds only the panel. `--uninstall --panel` removes it and `--check` reports it.
- The end of a plain install mentions the optional panel.

## [0.2.0] - 2026-10-07

### Added

- Optional study panel, `mods/study-companion` (Claude Code plugin, early-access mods API):
  - `/study-panel` opens a panel with progress, next session, drift, projected end, buffer,
    concepts to fix and the last evaluation, answered by `study_state.py` without the model;
  - buttons for the next step of the cycle (open, evaluate or close the session) and the full status;
  - the first study command of a session opens the panel once;
  - a status line shown only in study sessions;
  - a reminder after 7 days without studying.
- `.claude-plugin/marketplace.json` so the mod installs with `claude plugin install
  study-companion@study-skills`.

## [0.1.0] - 2026-09-30

First public release.

### Added

- Five commands: `/study-new`, `/study-next`, `/study-eval`, `/study-close` and `/study-status`,
  plus `study-shared` with the templates, references and scripts they use.
- `study_state.py`: stdlib-only state engine (registry, next session, drift, projected end at the
  real pace, calendar projection, plan validation with `check`, evaluation log).
- `verify_links.py`: every URL is checked before it is written into a plan.
- Optional videos per session from Platzi (title, duration and URL only) or a pasted course index.
- Answer positions drawn by `study_state.py answer-key`: no letter above its fair share and never
  three identical answers in a row.
- Two answer modes for evaluations: `--clicks` (dialogs, default up to 12 questions) and `--text`
  (one message, default for mocks and diagnostics).
- Language rules: files are written in the language the plan is requested in, the conversation
  follows the user, notes keep the user's own words, and Spanish is always neutral.
- `install.sh` with `--link`, `--force`, `--check` and `--uninstall`; `INSTALL.md` for agents.
- Offline test suite with synthetic fixtures.

[Unreleased]: https://github.com/kleyver14/study-skills/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/kleyver14/study-skills/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/kleyver14/study-skills/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/kleyver14/study-skills/releases/tag/v0.1.0
