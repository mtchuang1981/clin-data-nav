# CodeQL Default Setup Evidence

- **Evidence recorded:** 2026-08-09 (`Asia/Taipei`)
- **Repository:** `mtchuang1981/clin-data-nav`
- **Scanned main commit:**
  `0aff8038bb52457e9868fab9ea9a43dda9b4235c`
- **Authorization:** explicit user approval to enable CodeQL default setup

This report records a historical API observation after the approved external
setting change. GitHub remains the authority for current state. Zero findings
do not prove that the repository is secure.

## Configuration

- state: `configured`;
- languages: `actions`, `python`;
- query suite: `default`;
- threat model: `remote`;
- runner type: `standard`; and
- schedule: `weekly`.

## Initial scan

The initial dynamic run was `31269886134`:

`https://github.com/mtchuang1981/clin-data-nav/actions/runs/31269886134`

- `Analyze (actions)` job `93133943497`: success;
- `Analyze (python)` job `93133943498`: success;
- Actions analysis `1590243272`: 17 rules and zero results; and
- Python analysis `1590243578`: 43 rules and zero results.

The final API re-read observed zero open code-scanning alerts and zero job
annotations, warnings, or failures. These observations apply only to the
identified commit, configuration, query versions, and scan time.

## Branch protection

No branch-protection setting was changed. CodeQL is not currently required.
The existing strict required contexts remain:

- `test (ubuntu-latest)`;
- `test (windows-latest)`; and
- `compare-packages`.

## Publication boundary

No tag or GitHub Release was changed. The annotated `v0.3.0` tag, Release,
ZIP, manifest, asset identities, and SHA-256 values remain governed by
`2026-08-09-v0.3.0-publication.md`.
