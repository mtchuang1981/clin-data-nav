# File identity checks for subprocess cleanup

The user requested this follow-up to PR #21. The scope is the three audited
subprocess assertions. The existing rollback design supplies the file identity
rules. Both remaining POSIX-specific cases retain their separate contracts.

Use a test-only launcher that calls the existing CLI main in a separate Python
process. Observe transaction construction and capture stage and backup metadata
after prepare. Write a fresh, bounded JSON observation to an exclusive file in
a separate temporary directory. Keep the CLI status streams and exit code.

- Add foreign lookalike regressions to the three cases and observe failure with
  the old glob. Add a synthetic retained and renamed backup regression.
- For success, require exactly one construction with both identities captured.
  Match the backup to the prior output and use the existing committed-state scan.
- For the two early rejections, require no construction and no captured identities.
  Retain evidence and output integrity checks, including the intentional hardlink.
- Reject missing or malformed observations and capture failures. Keep the
  fault injection limited to the synthetic test launcher.
- Run the focused tests and all repository checks. Record local results and
  retain scope for later POSIX work.

## Observed results

- The original three glob assertions each rejected a synthetic foreign file.
  All three controls without the foreign file passed.
- The instrumented child calls the evaluator's CLI main and keeps its status
  streams and exit code. The existing direct script tests still exercise startup.
- A synthetic fault suppresses backup deletion and renames that same backup to
  an ordinary name after the evaluator returns. Its captured identity matches
  the prior output, and the parent's ownership assertion detects the residual.
- Both preflight rejections produce a zero-construction observation. The reader
  rejects missing or malformed observations, construction mismatches, zero
  inodes, and identical stage/backup identities.
- Final Windows suite on Python 3.11.9: 2,049 passed, 14 skipped.
  Skill validation, public boundary and reproducible packaging passed.

The observation covers construction of the evaluator's summary transaction and,
for success, the captured stage and backup identities in the output directory.
The injected backup is synthetic. Ubuntu CI is pending.
