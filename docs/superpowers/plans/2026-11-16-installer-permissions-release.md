# Installer permissions and v0.11.1 implementation plan

Goal: fix destination-policy inheritance before publication, retain consultation
improvements, then publish a new immutable patch release through normal PR/CI.
Spec: docs/superpowers/specs/2026-11-16-installer-permissions-design.md.

- [x] Inspect installer, local incident, release process and remote version.
- [x] Reuse current approved workspace on codex/clin-nav-0.11.1; a fresh worktree
  would omit the approved uncommitted consultation changes. No unrelated changes.
- [x] Add native Windows tests for new and overwrite installs with restricted
  staging and destination-inherited readers; observe RED before implementation.
- [x] Add pre-extraction destination DACL preparation and fail-before-publication
  tests, preserving rollback, native rename and non-Windows behavior.
- [x] Run supported Python 3.11 checks and native Windows regression; independent
  read-only code review before release. No private sources or data.
- [x] Synchronize current metadata/docs/tests/workflow to 0.11.1; preserve
  historical releases, hashes, frozen benchmark inputs and action pins.
- [x] Full pytest, skill validation, public boundary, reproducible package,
  release artifact verifier and diff review; commit only reviewed scoped files.
- [ ] Push branch, create PR, require CI, merge normally, require merged-commit
  CI/CodeQL; annotated new tag; main-dispatched release workflow; verify downloads.
- [ ] Record public release evidence and submit its normal report PR.

User approval covers this work and publication; no repeated permission question
is needed for the same scope. OS sandbox escalation remains independent.
