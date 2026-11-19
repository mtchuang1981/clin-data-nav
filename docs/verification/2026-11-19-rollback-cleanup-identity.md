# Identity assertions for standard in-process rollback

Date: 2026-11-19 (Asia/Taipei). Base: `ff0165fdb5285c425b0a4f7fcef47be26d26b48c`.
Branch: `codex/rollback-cleanup-identity`. This note records local implementation
verification before any push, PR, merge or publication for this change.

## Scope and behavior

Extend the test-only SummaryFileOwnership helper with explicit rollback states.
With prior output, require the captured backup identity at output. Without prior
output, require lstat-based absence, including rejecting dangling links. In both
cases reject the original stage identity or unexpected owned aliases in the
immediate parent, regardless of filename. Preserve unrelated different-identity
objects, including replacements at an old stage name.

Only these existing complete-prepare tests switch their final glob assertion:

- test_backup_cleanup_failure_rolls_back_before_success_notification
- test_pre_finish_failure_removes_a_newly_created_summary
- test_close_failures_during_precommit_rollback_do_not_mask_fixed_error

The opt-in prepare fixture is reused; committed-state and rollback-state checks
share the final-state scan. Existing fixed CLI errors, input/output bytes and
close counters remain in place. Metadata errors, zero identity, missing capture,
wrong prior-state flags and missing/replaced required output fail closed.
Disappearing non-output entries may be skipped once. An output observed during
enumeration cannot be ignored when it subsequently disappears, including when
the expected final state is absence.

The three subprocess globs and two POSIX-related globs remain unchanged.
In particular, the POSIX test intentionally retaining an unexpected same-inode
alias is not converted. No production scanning, deletion, delay or HANDLE retry
is introduced. The product, package version, release bindings and workflows
are unchanged. SHA-256 of scripts/evaluate_simulation_benchmark.py remains
`8d39edd0419fd7f63ac074af875d2d869e518becf001fda0cde95dc673f8a910`.

## TDD, review and final checks

Windows, Python 3.11.9, pytest 9.1.1, fresh synthetic basetemp outside the repo.
Pytest commands use `-X utf8 -B -m pytest -q -p no:cacheprovider --tb=short`.

| Check | Observed result |
| --- | --- |
| Initial unit RED | 28 failed for missing assert_rolled_back; 1 symlink skip; detailed case confirmed AttributeError |
| Initial unit GREEN | 42 passed, 1 skipped |
| Integration RED | 14 failed: foreign-object false positives; original-name diagnostic mismatch; renamed-stage and wrong restored-identity false negatives |
| Initial focused GREEN | 60 passed, 1 skipped, 283 deselected |
| Module and helper tests before review follow-up | 338 passed, 6 skipped; 110.41 seconds; exit 0 |
| Review regression RED | A forbidden output enumerated then removed failed to raise |
| Final focused GREEN | 61 passed, 1 skipped, 283 deselected; 13.51 seconds |
| Final full suite | 2,039 passed, 14 skipped; 220.98 seconds; exit 0 |
| scripts/validate_skill.py | exit 0 |
| scripts/check_public_boundary.py | exit 0 |
| scripts/package_skill.py --check-reproducible | exit 0 |
| Scoped diff, unchanged-source and local-link checks | passed |

One independent read-only review found the enumerated-then-disappearing output
gap (P2). A deterministic regression reproduced it before the fix; the reviewer
confirmed resolution without additional findings. The reviewer did not run
another full suite. The final full suite includes every module test and this
new regression; the earlier standalone module result is explicitly pre-follow-up.

The 30 added helper cases cover rollback state, foreign lookalikes/replacements,
original/renamed stage leaks and hardlink aliases, same-content wrong output,
capture mismatch, metadata failures and inspection races. Fourteen integration
cases reuse the three original tests for foreign objects, genuine injected stage
leaks and restored-output substitution. Existing committed-state tests still run.

Skipped cases need unavailable symlink/reparse privileges, nonportable filename
semantics or POSIX dir-fd behavior; they are not passes. No remote CI or native
POSIX-special fault-injection run was performed for this local implementation.

## Evidence boundaries

Fault injections demonstrate test-oracle behavior, not naturally occurring
product leaks or the complete cause of historical failures. The observation is
limited to the immediate parent and supported filesystem metadata. It does not
prove cross-directory retirement, immutable long-term inode identities or
absence of changes after inspection. The remaining five globs need separate
subprocess/POSIX designs; do not apply the fixture globally or change production
cleanup to satisfy these assertions. Only public source and synthetic fixtures
are included; raw diagnostic records remain local.
