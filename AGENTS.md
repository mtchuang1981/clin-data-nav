# Repository Working Agreement

## Read First
Read the approved design and current implementation plan before editing.

## Public Boundary
Do not read or copy private TMUCRD adapters, codingbooks, data dictionaries,
internal guides, physical schema, linkage rules, PII classifications, or
version-specific metadata into this repository.

## Development
Add or update a failing test before changing behavior. Use only synthetic
institutional examples. Keep the installable skill under
skills/clinical-data-research-navigator/.

## Required Verification
Run python -m pytest -q, python scripts/validate_skill.py,
python scripts/check_public_boundary.py, and
python scripts/package_skill.py --check-reproducible.

## External Actions
Do not create or push a GitHub repository, publish a release, change the
license, or access a private system without explicit user approval.
