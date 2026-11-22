# POSIX cleanup assertions

This follow-up uses the existing rollback identity design and the two POSIX
contracts preserved through PR #22.

1. Add unrelated lookalikes to both tests and verify the old globs reject them.
2. For the partial prepare failure, capture the stage identity before the
   injected dup failure. Verify rollback retires that identity and preserves
   the original output identity.
3. For native POSIX rollback, capture both identities after prepare. Require
   the restored backup at the output and the original stage at the intentional
   hardlink. Check their link counts and retirement of the generated stage path.
4. Run the focused tests on Windows and Ubuntu WSL, then run the repository
   validation commands. Record test and platform coverage in this plan.

## Verification

- Both old assertions failed in Ubuntu WSL when an unrelated synthetic file
  matched the glob. Both passed with the identity assertions on Python 3.12.3.
  The Ubuntu checkout used a local Git bundle so the release tags were available
  to the fixture. The native case ran on the Linux temporary filesystem.
- The Windows single-process suite hit a host-specific Git environment issue.
  An existing test temporarily sets an inherited empty `GIT_CONFIG_VALUE_0`.
  Restoring the empty value in Python on this host removes it from the child
  process environment. The next Git call then returns 128. A two-test run and
  a direct Python/Git experiment reproduced this independently of the POSIX
  assertions. Run that existing test in a separate process for verification.
- The Windows split run completed with 2,048 passed, 14 skipped and one
  deselected. The deselected test passed in its own process, for 2,049 passes
  overall. The native POSIX case was skipped on Windows and passed on Ubuntu.
- Skill validation, the public boundary check, reproducible packaging and the
  diff check passed locally.
- [PR #23](https://github.com/mtchuang1981/clin-data-nav/pull/23) merged as
  `be635e47077fa724a996ad579614ca08023dbf5f`. The merge commit passed
  2,060 Windows tests with 3 skipped and 2,028 Ubuntu tests with 35 skipped.
  Package comparison and both CodeQL analyses passed.
  [Validation](https://github.com/mtchuang1981/clin-data-nav/actions/runs/44983301169)
  · [CodeQL](https://github.com/mtchuang1981/clin-data-nav/actions/runs/44983301226)
