# ClinNav local installation follow-up

The user requested the next step after the consultation refinement. The
installed public Skill was synchronized to the verified local repo candidate
at `C:\Users\TMU\.agents\skills\clin-nav`. This is a local development
candidate, not a new published release or verification of host-loaded content.

## Preflight and backup

The exact selected directory was a regular directory, not a symlink or
junction. Comparison found five changed files, one new consultation reference
and no installed-only custom files (excluding Python caches). The previous
copy was archived before replacement. The package and backup are retained in
the ignored local directory `dist/local-sync-20261116/`.

Package SHA-256:
`495e2b959a2831b32b677edcbff8c395e49526cec3e21871976d945019ef09ad`

Manifest SHA-256:
`3d460bd7079f42944c542ae763361813eeba030e1a340c2eb5331984f8a2bcc7`

These bind this reviewed local candidate only; they are not official release
hashes. Package metadata remains 0.11.0. No published artifact was replaced.

## Permission incident and bounded correction

The initial elevated installer could not read the sandbox-created temporary
manifest: WinError 5 occurred before installation mutation. The temporary
directory ACL contained SYSTEM, Administrators and OWNER RIGHTS only.
Rebuilding under the repo's ordinary dist directory produced byte-identical
ZIP and manifest, accessible to the installing process. The existing strict
installer then completed with exit 0.

The installed directory initially retained an owner-restricted ACL; a sandbox
read failed with WinError 5. Its parent already granted the sandbox group
read/execute access. This is consistent with the installer's staged directory
retaining temporary-directory permissions when moved into place. This local
observation does not establish the behavior of every runtime/platform.

As a scoped operational workaround, inheritance was enabled only for the
selected ClinNav tree (`icacls ... /inheritance:e /T`); 30 objects processed,
zero failed. No parent permissions or unrelated installations were changed.
The installer source was not modified. A permanent installer fix would need
a separate failing Windows permission-inheritance regression and an explicit
cross-platform installation-permission contract; that remains open.

## Post-install checks

- All 26 installed files match the source's canonical package bytes.
- The new consultation reference exists and is readable from the sandbox.
- `verify_installation.py --comparison bytes`, using the exact local candidate
  manifest outside the source repository: exit 0,
  `manifest-files-byte-identical`; 26 matched, zero different/missing/extra.
- The verifier reports `loaded_version: not-verified`. No host restart or
  loaded-version claim was made.
- The earlier refinement's full test evidence remains in
  `2026-11-16-feasibility-consultation.md`; this follow-up changes no program
  or Skill content and does not claim a new full-suite run.

No private MCP calls, patient data, repository push or release publication
were involved. The old installation backup remains available locally.
