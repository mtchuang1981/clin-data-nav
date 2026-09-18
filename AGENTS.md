# Repository Working Agreement

## Read First
Read the approved design and current implementation plan before editing.

## Public Boundary
Do not read or copy private TMUCRD adapters, codingbooks, data dictionaries,
internal guides, physical schema, linkage rules, PII classifications, or
version-specific metadata into this repository.
Do not read or commit human participant data, condition keys, human answer text,
study assignment files, consent records, or repository-external human task packs.

## Development
Add or update a failing test before changing behavior. Use only synthetic
institutional examples. Keep the installable skill under
skills/clin-nav/.
When modifying SKILL.md, also review agents/openai.yaml, Evals, and references.
Before completion, review git diff.

## RTK
When RTK is available in the local environment, prefix shell commands with
`rtk` to reduce routine test, Git, build, and CI output. If RTK is unavailable,
run the command directly rather than installing it implicitly. If a filtered
result is unexpectedly empty, inconsistent with its exit code, truncated, or
insufficient for a security or release decision, recover the complete output
with `rtk recall` when available or rerun it with `rtk proxy <command>`. Treat
deterministic exit codes, hashes, and repository verifiers—not output
filtering—as the source of truth.

## Required Verification
Run python -m pytest -q, python scripts/validate_skill.py,
python scripts/check_public_boundary.py, and
python scripts/package_skill.py --check-reproducible.

## External Actions
Do not create or push a GitHub repository, publish a release, change the
license, or access a private system without explicit user approval.
