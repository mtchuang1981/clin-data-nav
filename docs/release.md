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
5. Run `python scripts/verify_release.py artifacts` against those two files.
   Manually review the public contents.

The packager canonicalizes UTF-8 text line endings to LF before hashing and
archiving. Files containing a NUL byte or invalid UTF-8 retain their original
bytes. The manifest therefore records the bytes inside the ZIP, which may
intentionally differ from CRLF text bytes in a Windows checkout.

Stop here. Do not push, create or move a tag, dispatch a workflow, or create a
GitHub Release without separate explicit approval.

## Approved GitHub publication

After approval:

1. Submit the verified branch through a pull request to `main`.
   Merge only after the required PR checks pass. Do not bypass branch protection
   or use an admin merge option.
2. Require the exact merged commit's Ubuntu and Windows `validate` matrix jobs,
   cross-platform package comparison, and CodeQL to succeed.
   Confirm that no verification step was skipped.
3. Create an annotated `vX.Y.Z` tag at that commit.
   Push only that new tag.
4. Manually dispatch `.github/workflows/release.yml` from `main` with the
   annotated tag. Wait for every Release job to succeed.
5. Confirm the public Release points to the intended tag and contains exactly
   `clin-nav-X.Y.Z.zip` and `clin-nav-X.Y.Z.manifest.json`.
6. Download both assets.
   Independently confirm the ZIP SHA-256 equals
   `archive_sha256` in the manifest.
7. Record the verified main commit, annotated tag object and peeled commit,
   validation and Release workflow URLs, public Release URL, asset IDs, sizes,
   and SHA-256 values in a new dated verification report under
   `docs/verification/`. Clearly separate verified public facts from external
   settings that remain disabled or unevaluated.
8. After approval, commit and push the report branch.
   Submit the report through a normal pull request.
   Merge only after the required checks pass. Do not move the published tag or
   edit the Release.

Never force-move a published tag or rerun publication to overwrite an existing
Release. Prepare a new patch version instead.

### Workflow verification mechanisms

Every job that executes repository code checks out only the dispatch event's
immutable `github.sha`. The supplied tag selects no source code.
It is used only for verification and publication identity.

The read-only jobs perform these checks and build operations:

1. Require the tag to peel to the checked-out commit.
2. Revalidate on Ubuntu and Windows.
3. Build the ZIP and manifest.
4. Verify those two files.
5. Upload a short-lived bundle containing the files, static Release notes,
   and transit checksums.

The final writer job receives no source checkout or Python environment.
It performs these operations in order:

1. Download the bundle by its exact artifact ID.
2. Verify the transit checksums.
3. Refuse an existing Release.
4. Recheck the remote annotated tag object and peeled commit.
5. Create the Release only after these checks succeed.
