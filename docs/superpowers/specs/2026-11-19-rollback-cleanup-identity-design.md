# Identity assertions for three in-process rollback tests

The user selected this next step on 2026-11-19 after the bounded synthetic
audit recommended fixing three in-process rollback cases first. This records
that reviewed scope; subprocess ownership collection and POSIX special contracts
remain separate. No product, security-setting, package-version or release change.

## Selected approach

Extend the existing test-only SummaryFileOwnership helper, rather than narrowing
filename patterns. Filename matching cannot distinguish a foreign lookalike
from a renamed owned stage. Capture the actual stage and optional backup after
prepare as before; add `assert_rolled_back(output, *, prior_output: bool)`.
The explicit prior-state argument must agree with captured backup presence.

With prior output, the final output must retain the captured backup identity.
Without prior output, the output must be absent according to lstat, including
rejecting a dangling symlink. In both cases the owned stage must be absent from
the immediate parent, and no unexpected entry may retain either owned identity.
Preserve foreign objects, including different-identity replacements at old names.

Share final-state scanning with assert_committed while preserving all its
existing guarantees. Missing capture, unreadable/zero identity, a disappearing
required output or an output appearing in the absence case must fail closed.
An unrelated entry disappearing during inspection may be skipped without retry.
No explicit raw-HANDLE operations, content-based classification, deletion or delay.

## Integration boundary

Opt in only these complete-prepare rollback tests:

- test_backup_cleanup_failure_rolls_back_before_success_notification
- test_pre_finish_failure_removes_a_newly_created_summary
- test_close_failures_during_precommit_rollback_do_not_mask_fixed_error

Retain their current stdout/stderr, input/output bytes, final absence, and
exactly-once close checks. Do not attach the fixture globally. The POSIX test
that intentionally preserves an unexpected same-inode alias is unchanged;
these assertions do not ask production code to scan for and delete aliases.
Other rollback, partial-prepare and subprocess cases are not converted.

## Proof and limitations

Write failing unit and integration regressions first. Preserve foreign lookalikes
and old-stage-name replacements; reject original/renamed stage leaks, surviving
hardlink aliases, same-content wrong output identity and wrong prior-state flags.
Test metadata failures and enumeration races. Run the benchmark module, full
suite, skill validation, public boundary, reproducible package and diff checks.

Synthetic injections prove assertion behavior, not naturally occurring product
leaks or the complete cause of historical failures. Identity observations remain
bounded to the immediate parent and filesystem metadata; no global absence,
cross-directory lifetime or immutable long-term inode identity is claimed.
Raw diagnostics stay local. Leave the verified work local for review; no push,
merge or publication is part of this implementation step.
