# v0.11.0 STE-inspired candidate verification — 2026-10-24

## Scope and boundary

The approved review covers 42 current public Markdown guidance files.
The [coverage ledger](2026-10-24-ste-project-coverage.md) records 39 edited and
three reviewed/retained files. UI metadata is retained unchanged.
English and Traditional Chinese use clarity principles, not a claim of formal STE certification.
No private Adapter, participant materials or new model campaign was accessed.

Baseline: `67682af339a1e4ba7f3eb81940bf89505cdd3235`.
Version metadata, installer/packager pins, workflow version/notes pins and their
current-version tests move to 0.11.0. Historical asset facts remain unchanged.
All changed existing Markdown fenced blocks were compared with the baseline and retained exactly.
No catalog, fixture, protocol, generated summary/report or heading alias map was changed.

## Local results

Official CPython 3.11.9 on Windows:

| Check | Observed result |
| --- | --- |
| Unchanged baseline `python -m pytest -q` | 1944 passed, 13 skipped, 177.94 seconds |
| Final candidate `python -m pytest -q` | 1944 passed, 13 skipped, 177.08 seconds |
| Focused metadata/installer/package/release/heading tests | 329 passed |
| `validate_skill.py` | Exit 0 |
| `check_public_boundary.py` | Exit 0 |
| `package_skill.py --check-reproducible` | Exit 0 |
| Core and compiler summary `--check` | Both exit 0 |
| Synthetic effectiveness and benchmark report `--check` | Both exit 0 |
| Supplemental Skill quick validation with explicit UTF-8 | Pass |
| Two builds and `compare_packages.py` | Identical ZIP and manifest bytes |
| `verify_release.py artifacts` | Exit 0 |
| `git diff --check` | Exit 0 |

Skips concern unavailable symlink/reparse privileges, case-distinct/trailing-space
paths and a POSIX-only directory cleanup contract. They are not claimed as Windows passes.
The 36-cell legacy aggregate digest remains
`6c7db3794be2f5b74107a27ae9dae5e385aa82cfabb98be691bf4b67b72b8757`.
The opt-in heading contract remains opt-in; default and historical scores are unchanged.

The first candidate run found stale version assertions, which were synchronized,
and a non-default test invocation problem. Adding `-X utf8` only to the parent
Python process made a subprocess reader expect UTF-8 while the child CLI used
the Windows system encoding. The same isolated test passed with the original
standard invocation and failed reproducibly with parent-only `-X utf8`.
The final full run used the approved standard command, as did the baseline.
No evaluator behavior or safety assertion was weakened. Mixed parent/child
encoding remains a limitation, not a product fix claimed by this release.

## Candidate artifacts

Both builds contain the same 25 public Skill members. Independent Windows
CertUtil SHA-256 results match the package comparison and manifest verification.

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| clin-nav-0.11.0.zip | 66640 | `1cf42f68f1ac960a2304579498f89ed359d59c789ce4c722159eff4c8fbb2e9b` |
| clin-nav-0.11.0.manifest.json | 3473 | `5dae33ec243bef00c1c6ad16375427472dc32608b70f43696616bb3b99fdfd3e` |

These are local candidate facts, not public asset verification.

## Review and pending publication

Independent read-only semantic/bilingual review found no Critical or Important
issue. Its one sentence-capitalization finding was corrected.
The dated security-support table is reserved for the post-publication current-pointer update.
The primary checkout's unrelated untracked backlog was not changed or staged.

Publication still requires checked PR integration, exact-main Windows/Ubuntu
validation and package comparison, CodeQL and relevant alert review, a new
annotated tag, successful release jobs, and downloaded public-asset comparison.
The earlier intermittent Windows cleanup anomaly remains unexplained and is not claimed fixed.
No model improvement, token savings, human usability, clinical validity or deployment fitness is established.
