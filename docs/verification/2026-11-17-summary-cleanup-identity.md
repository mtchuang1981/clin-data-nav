# Summary cleanup identity assertions

Date: 2026-11-17 (Asia/Taipei). Base: `56146e9bb9f14fdb348e6afcebc3147eee38e591`.
Branch: `codex/windows-cleanup-identity`; this note records verification before
the local commit in an isolated worktree. No push, PR, merge, release or
security-setting change was performed during verification.

## Change and evidence

The Windows close-after-effect test's final broad temporary-name glob is
replaced by a test-only ownership assertion. An opt-in fixture records live
stage and backup metadata identities after prepare. The committed output must
retain the captured stage identity; the backup must be absent from the immediate
parent, and no other entry may retain either owned identity. Ordinary renames
and hardlink aliases are detected regardless of filename. Foreign objects are
not deleted, read for classification, or treated as owned solely by their names.

Missing capture, unavailable/zero identity, inaccessible metadata and missing or
replaced output fail closed. A non-output entry disappearing after enumeration
does not cause a retry; lstat does not follow symlinks. No raw HANDLE is opened
or retried by the helper. Existing stdout/stderr, input, sentinel and exactly-once
close checks remain in the original test and run in the new integration cases.

Only this target test uses the new fixture. Other cleanup globs, rollback and
subprocess tests remain unchanged. The package and production scripts are
unchanged. SHA-256 of scripts/evaluate_simulation_benchmark.py remains
`8d39edd0419fd7f63ac074af875d2d869e518becf001fda0cde95dc673f8a910`.

## TDD and verification

Python 3.11.9, pytest 9.1.1, Windows, fresh synthetic basetemp outside the repo.
Commands use `-X utf8 -B -m pytest -q -p no:cacheprovider --tb=short`.

| Check | Observed result |
| --- | --- |
| Unit RED | Collection failed for the missing helper |
| Unit GREEN | 14 passed |
| Integration RED | 9 failed under the old glob: foreign objects misclassified, original-name leak diagnosis mismatched, renamed real leaks missed |
| Focused GREEN | 27 passed, 274 deselected |
| Full benchmark module and new units | 296 passed, 5 skipped; 84.75 seconds; exit 0 |
| Full suite | 1,996 passed, 13 skipped; 165.94 seconds; exit 0 |
| scripts/validate_skill.py | exit 0 |
| scripts/check_public_boundary.py | exit 0 |
| scripts/package_skill.py --check-reproducible | exit 0 |
| git diff --check and scoped diff review | passed |
| Independent read-only review | no actionable findings; reviewer did not run another suite |

The new tests cover foreign lookalikes and same-name replacements, original and
renamed backup leaks, stage hardlink aliases, matching-content output substitution,
missing output/capture, zero or unreadable identities, vanished foreign entries,
and duplicate/inconsistent capture. Native integration reuses all three existing
close seams for foreign-object preservation and both real-backup leak variants.

Skipped tests require unavailable symlink/reparse permissions, Windows-incompatible
filename distinctions, or POSIX dir-fd semantics. They are not counted as passes.
No Ubuntu run or remote CI was performed for this unpushed change.

## Claim limits

This fixes a deterministically demonstrated test-oracle defect. It does not
retroactively establish the creator at earlier intermittent failures, erase
their results, or claim that every cleanup assertion has been converted.
Observation is limited to the immediate parent and the supported filesystem's
metadata identities. Cross-directory leaks, long-term inode reuse and changes
after the final scan are not proven absent; uncertainty is not converted to a pass.

Only new synthetic regressions and public source were used here. Raw external
diagnostic records remain local and are not included in this branch. The primary
checkout's existing uncommitted progress documents were preserved.
