# Release process

Release preparation is local and read-only until separate user approval for
GitHub publishing is given.

1. Run the full local verification set:

   ```bash
   python -m pytest -q
   python scripts/validate_skill.py
   python scripts/check_public_boundary.py
   python scripts/package_skill.py --check-reproducible
   ```

2. Confirm `git status` is clean.
3. Generate the package and manifest with `python scripts/package_skill.py`.
4. Perform a manual public-boundary review of the intended release artifacts.
5. Create an annotated `v<version>` tag from the verified release commit.
6. Push `main` and the tag without rewriting an existing published tag.
7. Create the GitHub Release from that tag and attach the matching
   `clinical-data-research-navigator-<version>.zip` and
   `clinical-data-research-navigator-<version>.manifest.json`.

Stop after step 4. Do not perform steps 5–7 (tagging, pushing, or creating a GitHub
Release) unless the user separately approves GitHub publishing.
