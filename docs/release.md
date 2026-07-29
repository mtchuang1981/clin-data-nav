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

Stop here. Do not push, create or move a tag, dispatch a workflow, or create a
GitHub Release without separate explicit approval.

## Approved GitHub publication

After approval:

1. Push the verified commit to `main`.
2. Require the exact commit's Ubuntu and Windows `validate` matrix jobs to
   succeed with no skipped verification step.
3. Create an annotated `vX.Y.Z` tag at that commit and push only that new tag.
4. Manually dispatch `.github/workflows/release.yml` with the annotated tag.
   The workflow revalidates the tag on Ubuntu and Windows, rebuilds the assets,
   verifies the ZIP and manifest, and grants write permission only to its final
   publish job.
5. Confirm the public Release points to the intended tag and contains exactly
   `clinical-data-research-navigator-X.Y.Z.zip` and
   `clinical-data-research-navigator-X.Y.Z.manifest.json`.
6. Download both assets and independently confirm the ZIP SHA-256 equals
   `archive_sha256` in the manifest.

Never force-move a published tag or rerun publication to overwrite an existing
Release. Prepare a new patch version instead.
