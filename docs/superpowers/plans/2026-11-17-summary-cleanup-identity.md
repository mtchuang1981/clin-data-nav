# Summary cleanup identity implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan inline, task by task. Steps use checkboxes for tracking.

**Goal:** Distinguish foreign temporary-looking objects from genuine owned-file leaks in the Windows close-after-effect test.

**Architecture:** A metadata-only test helper records live stage/backup identities; an opt-in fixture captures them after prepare. Only the target test's final assertion changes. Product transaction code remains unchanged.

**Tech Stack:** Python 3.11.9, pytest, standard library; existing supported interpreter, no dependency installation.

**Spec:** ../specs/2026-11-17-summary-cleanup-identity-design.md (approved 2026-11-17).

## Global constraints

Synthetic tests only; preserve existing pending documents in the primary checkout.
Do not copy raw diagnostic logs into Git. No security changes, trace sessions,
product changes, version bump, frozen-result rewrite, push or publication.
Use metadata identities; no retry of closed HANDLEs and no glob deletion.

## Review focus

Renamed leaks still fail; hardlink stage aliases still fail; foreign replacements
are preserved; unreadable/unknown identity fails; existing handle/sentinel checks
remain active. Parent scanning is immediate and does not follow symlinks.

## Task 1: Identity assertion helper

Files: create tests/summary_file_ownership.py and tests/test_summary_file_ownership.py.

Interface: `SummaryFileOwnership.capture(role: str, path: Path) -> None` records
one stage and optional backup. `assert_committed(output: Path) -> None` checks
the output's captured stage identity and absence of owned leaks in its parent.

- [x] Add failing unit tests for success, foreign lookalikes/replacements,
  original/renamed backup leaks, stage aliases, output replacement/missing,
  unknown identity, unreadable metadata, vanished entries and missing capture.
- [x] Observe RED for the missing helper, then implement the minimal helper.
- [x] Observe GREEN; no explicit owned-HANDLE opens, deletion or platform API dependency.

## Task 2: Native integration and verification

File: tests/test_simulation_benchmark.py. Add an opt-in fixture wrapping prepare;
retain all previous handle, sentinel, input and output checks. Replace only the
target test's final broad glob with `assert_committed(output)`.

- [x] Add failing foreign-object integration cases for backup/stage/parent
  close seams; add original/renamed real-backup leak controls.
- [x] Observe RED at the old glob for foreign objects, then integrate the helper.
- [x] Run focused cases and the full benchmark module, then full pytest and all
  repository verification scripts. Preserve any fresh failures.
- [x] Review diff and obtain independent read-only review; fix verified issues.
- [x] Record checks, limitations and unchanged product-source hash in a concise
  synthetic-only verification note. Leave the scoped work uncommitted for review.

## Execution ledger

- Baseline: supported Python 3.11.9 and source base `56146e9`; the preceding
  bounded synthetic diagnostic ran the unmodified close test's three seams
  successfully. Existing unrelated pending documents stayed in the primary checkout.
- Task 1 RED: new unit module failed collection for the absent helper, as expected.
  GREEN: 14 unit cases passed.
- Task 2 RED: 9 integration failures. Foreign objects failed at the old glob;
  renamed true backups escaped that glob. Original-name leak cases failed with
  the old assertion rather than the new owned-identity diagnostic.
- Focused GREEN: 27 passed, 274 deselected. Full module plus units:
  296 passed, 5 skipped, 84.75 seconds. Skips are platform/permission limits.
- Skill, public-boundary and reproducible-package checks exited 0.
- Independent read-only review found no actionable issue. Final full suite:
  1,996 passed, 13 skipped, 165.94 seconds, exit 0. See the
  [verification note](../../verification/2026-11-17-summary-cleanup-identity.md).
- Ruling: keep the change opt-in to the known Windows close test; other broad
  cleanup assertions remain unchanged. Extending the helper to rollback or
  subprocess capture needs its own evidence and semantics, rather than a global
  fixture that could disturb existing fault-injection tests.
- Ruling: record metadata identities after prepare while ownership is live and
  inspect entries with lstat, not a reused raw HANDLE. Missing/ambiguous identity
  fails the test; no name-based fallback or retry is introduced.
- Follow-up: after the verified changes were left uncommitted for review, the
  user requested the next step. Prepare a scoped local commit; remote push,
  publication and merging are not part of that local commit step.
