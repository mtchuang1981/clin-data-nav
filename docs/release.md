# Release process

Release preparation is local and read-only until separate user approval for
GitHub publishing is given.

## Local preparation

1. Run the complete local verification set:

   ```bash
   python -m pytest -q
   python scripts/validate_skill.py
   python scripts/check_public_boundary.py
   python scripts/package_skill.py --check-reproducible
   ```

2. Confirm the version is synchronized in project metadata, installer,
   packager, citation, changelogs, READMEs, tests, and
   `docs/releases/X.Y.Z.md`.
3. Confirm `git status` is clean.
4. Generate the package and manifest with `python scripts/package_skill.py`.
5. Run `python scripts/verify_release.py artifacts` against those two files and
   manually review the public contents.

The packager canonicalizes UTF-8 text line endings to LF before hashing and
archiving; files containing a NUL byte or invalid UTF-8 retain their original
bytes. The manifest therefore records the bytes inside the ZIP, which may
intentionally differ from CRLF text bytes in a Windows checkout.

Stop here. Do not push, create or move a tag, dispatch a workflow, or create a
GitHub Release without separate explicit approval.

## Approved GitHub publication

After approval:

1. Push the verified commit to `main`.
2. Require the exact commit's Ubuntu and Windows `validate` matrix jobs to
   succeed with no skipped verification step.
3. Create an annotated `vX.Y.Z` tag at that commit and push only that new tag.
4. Manually dispatch `.github/workflows/release.yml` with the annotated tag.
   Read-only jobs revalidate the tag on Ubuntu and Windows, build and verify
   the ZIP and manifest, and upload a short-lived bundle containing those
   files, static Release notes, and transit checksums. The final writer job
   receives no source checkout or Python environment: it downloads that exact
   artifact ID, verifies the checksums, rechecks the remote annotated tag
   object and peeled commit, refuses an existing Release, and only then creates
   the Release.
5. Confirm the public Release points to the intended tag and contains exactly
   `clin-nav-X.Y.Z.zip` and `clin-nav-X.Y.Z.manifest.json`.
6. Download both assets and independently confirm the ZIP SHA-256 equals
   `archive_sha256` in the manifest.
7. Record the verified main commit, annotated tag object and peeled commit,
   validation and Release workflow URLs, public Release URL, asset IDs, sizes,
   and SHA-256 values in a new dated verification report under
   `docs/verification/`. Clearly separate verified public facts from external
   settings that remain disabled or unevaluated, then commit and push the
   report without moving the published tag or editing the Release.

Never force-move a published tag or rerun publication to overwrite an existing
Release. Prepare a new patch version instead.
