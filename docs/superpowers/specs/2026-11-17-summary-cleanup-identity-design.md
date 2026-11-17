# Summary cleanup assertions based on file identity

Approved by the user on 2026-11-17 after the local synthetic comparison.
Scope: test infrastructure only; no product behavior, security setting, package
version, release artifact, or frozen benchmark result changes.

The existing Windows close-after-effect test uses a broad temporary-name glob.
A distinct synthetic object with a similar name can fail that assertion even
after both owned paths have been retired and references closed. A controlled
leak of the real backup must continue to fail.

## Approach

Exact generated names are cheaper to inspect but miss renamed owned objects.
Use captured file identities instead, as approved: record `(st_dev, st_ino)`
for the real stage and optional backup after prepare while ownership is live.
The successful output must retain the stage identity. Scan only the immediate
transaction parent without following symlinks: the backup identity must be
absent, and the stage identity must occur only at the output. Detect renamed
backups and stage hardlink aliases even without temporary-looking names.

Use a small test-only helper and opt-in fixture. Initially replace only the
known Windows close-after-effect test's final glob; other cleanup tests and
subprocess tests keep their assertions. Do not create a production tracing API.

## Failure policy

- Unknown/zero inode, unreadable metadata, missing output, duplicate role or
  inconsistent parent is a failure, never a filename-based fallback.
- A non-output entry disappearing between enumeration and lstat may be skipped;
  an output disappearing fails. Do not retry HANDLEs or perform cleanup.
- Preserve unrelated objects, including lookalikes and different-identity
  replacements at an old backup name. Read metadata only, never their contents.
- Keep existing stdout/stderr, input, sentinel and exactly-once close checks.
- The identity observation is bounded to this parent and supported filesystem;
  it does not prove global absence across directories or immutable inode reuse
  across time. Ambiguity must fail rather than silently pass.

## Validation

Failing regressions first. Cover genuine backup leaks at original and renamed
paths, unexpected stage aliases, output identity replacement, unknown or
unreadable metadata, missing tracking, disappearing foreign entries, and intact
foreign objects. Add native integration cases that exercise the original
close-after-effect checks with a deterministic foreign object and real injected
leaks. Run the full benchmark module, full suite, skill validator, public
boundary checker, reproducible packager and diff review.

Synthetic examples only. Raw external diagnostic records remain outside Git;
no real process identities, local traces or institution-specific data belong
in this change. No commit, push, PR or release is required in this round.
