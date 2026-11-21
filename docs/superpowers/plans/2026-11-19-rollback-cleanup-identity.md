# Rollback cleanup identity implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline, task by task.

**Goal:** Prevent foreign-object false positives and renamed-stage false negatives in three standard in-process rollback tests.

**Architecture:** Extend the existing metadata-only test helper with explicit prior-output semantics and a shared final-state scan. Reuse the opt-in prepare fixture; preserve product behavior and other test families.

**Tech Stack:** Existing Python 3.11.9, pytest and standard library; no new dependency.

**Spec:** ../specs/2026-11-19-rollback-cleanup-identity-design.md, reflecting the selected next step from the reviewed audit.

## Constraints and review focus

No product/version/security change or raw diagnostics in Git. No subprocess or
POSIX-special conversion. Use only synthetic fixtures and fresh external temp
directories. Check prior-state/capture mismatch, missing or replaced output,
renamed leaks, foreign replacements and inspection races; never retry a HANDLE.

## Task 1: Rollback helper

Files: tests/summary_file_ownership.py; tests/test_summary_file_ownership.py.
Interface: `assert_rolled_back(output: Path, *, prior_output: bool) -> None`.

- [x] Add unit tests for both valid rollback states and foreign replacements;
  original/renamed stage leaks, aliases, invalid output identity/absence,
  mismatched/missing capture, metadata failures and enumeration races.
- [x] Observe RED for the missing method, then implement the rollback assertion
  and extract the common final-state scan without changing committed semantics.
- [x] Run all helper tests GREEN, recording platform skips separately.

## Task 2: Three-case integration

File: tests/test_simulation_benchmark.py. Add regressions using the original
three tests for foreign lookalikes/old-stage replacements, original/renamed stage
leaks and same-content restored-output substitution. Fault injections are test-only.

- [x] Observe RED at the original broad glob or missed renamed leak/wrong identity.
- [x] Add the existing summary_file_ownership fixture argument only to the three
  target tests; replace their final glob with explicit rollback assertions.
- [x] Run focused regressions and the full benchmark module, then full pytest,
  validate_skill.py, check_public_boundary.py and package_skill.py --check-reproducible.
- [x] Review the scoped diff and obtain one independent read-only review.
- [x] Record validation, source hash and remaining scope limits; preserve the
  verified local work for review without pushing or merging.

## Execution ledger

- Base: `ff0165f`; existing isolated worktree reused on
  `codex/rollback-cleanup-identity`. Public main was fetched and unchanged.
- Unit RED: 28 failures for the absent rollback method, 1 symlink skip;
  a single detailed failure confirmed AttributeError. Initial unit GREEN:
  42 passed, 1 skipped (including the existing committed-state tests).
- Integration RED: 14 failures under the old glob. Foreign objects failed at
  the broad assertion; renamed stages and wrong restored identities were missed.
- Initial focused GREEN: 60 passed, 1 skipped, 283 deselected.
- Before review follow-up: full benchmark module plus helper tests completed
  with 338 passed, 6 skipped, 110.41 seconds. This is not the final suite result.
- Independent review found one P2: a forbidden output could be enumerated then
  disappear and be skipped in the no-prior-output case. Added a deterministic
  regression, observed RED (DID NOT RAISE), and rejected disappearing output in
  both required-output and forbidden-output cases. Final focused GREEN:
  61 passed, 1 skipped, 283 deselected, 13.51 seconds. Reviewer confirmed resolution.
- Ruling: preserve the first full-module result as pre-follow-up evidence;
  final full pytest will cover every module test plus the added review regression,
  avoiding another redundant standalone module run.
- Ruling: fixture reuse is opt-in for complete-prepare standard rollbacks only.
  The five remaining globs and POSIX deliberate-alias policy remain unchanged.
- Final full suite: 2,039 passed, 14 skipped, 220.98 seconds, exit 0. See
  [closeout evidence](../../verification/2026-11-19-rollback-cleanup-identity.md).
- Ruling: update the existing optimization backlog in the same local change,
  recording these three cases and retaining the five subprocess/POSIX assertions
  plus historical causal limits. Private and human acceptance rows stay unchanged.
