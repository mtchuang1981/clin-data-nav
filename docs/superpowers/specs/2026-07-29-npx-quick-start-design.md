# npx Quick Start Design

**Date:** 2026-07-29

## Goal

Make the shortest supported installation path immediately visible to new users
while preserving the existing versioned, checksum-verified Release workflow.

## Recommended documentation flow

Add aligned `Quick start` and `快速開始` sections near the beginning of
`README.md` and `README.zh-TW.md`. The primary command is:

```bash
npx skills add mtchuang1981/clin-data-nav
```

The surrounding text must explain that:

- the command is run from the project root where the Skill should be available;
- the default installation is project-local under `.agents/skills`;
- `/skills` can be used to confirm discovery;
- `$clinical-data-research-navigator` explicitly invokes the installed Skill;
- users should review third-party Skills before use because they run with the
  agent's permissions.

## Installation choices

The `npx` path is the recommended quick start because it discovers the single
Skill in the repository and performs the project-local installation
automatically.

The existing GitHub Release instructions remain complete and are relabeled as
the verified manual installation path. They are the preferred option when a
user needs a pinned release, manifest inspection, SHA-256 verification,
offline transfer, or installation in the personal `$HOME/.agents/skills`
directory.

The README must not imply that the `npx` command installs globally or verifies
the published Release manifest. Keeping this boundary explicit prevents a
convenient installation path from being mistaken for the deterministic release
workflow.

## Scope

- Update only `README.md`, `README.zh-TW.md`, and focused documentation contract
  tests.
- Keep the English and Traditional Chinese section order and meaning aligned.
- Do not change Skill runtime behavior, packaging contents, version numbers, or
  Release assets.
- Do not add a second installer or duplicate the `skills` CLI.

## Verification

Add a documentation contract test before editing the READMEs. It must require
the exact `npx` command in both files, the project-local installation boundary,
the verification and invocation commands, and the retained verified manual
installation headings.

After the documentation change, run all four repository checks:

```bash
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```
