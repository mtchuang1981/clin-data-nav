# OMOP 1.1 DuckDB Limitation Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans with test-driven-development and one final read-only whole-branch review. Steps use checkbox syntax.

**Goal:** Integrate the existing opt-in 1.1 contract and report a DuckDB cyclic-FK declaration limitation without changing compatibility decisions.

**Architecture:** Extend the existing closed `limitation_codes` only for 1.1. The adapter explicitly attests the limitation; the public checker validates its shape and summary hash, not the backend diagnosis. DQD evidence and declared FK compatibility remain independent.

**Tech Stack:** Python 3.11 standard library, pytest, JSON Schema, RTK.

**Spec:** User-approved bounded design (2026-10-08) below, supplementing `docs/superpowers/specs/2026-09-20-omop-metadata-connector-design.md`.

## Approved Design and Global Constraints

- Accept `duckdb-cyclic-fk-ddl-limited` in 1.1 only, in the existing sorted, unique, bounded `limitation_codes` array.
- Preserve 1.0 inputs, outputs, statuses and exit codes, including rejection of unknown codes.
- Do not infer the code from missing FKs or silently add it to responses.
- The code never rewrites `foreign_key_status`, structural status, DQD evidence status, or exit codes.
- Preserve closed fields, summary hashing, scan completeness, freshness and failure-output boundaries.
- Use synthetic inputs only; do not read or modify private adapter code, metadata or responses.
- Integrate existing `codex/omop-connector-1-1` commits with local main; preserve unrelated untracked files.
- Commit and merge locally only: no push, tag, release, version bump, or release assets.

## Review Focus

- Unknown/duplicated/unsorted limitation codes must remain invalid, including with accepted evidence.
- A limit code cannot hide PK/type/column differences or an incomplete scan.
- Hash tampering and free-text diagnostics remain rejected.
- The schema and executable validator must agree on version-specific accepted codes.
- The platform assertion is adapter-reported, not proof that all FK differences arise from a cycle.

## Task 1: Version-Specific Limitation Contract

**Files:** `tests/test_omop_metadata_v11.py`, `skills/clin-nav/scripts/omop_metadata.py`, `skills/clin-nav/references/omop-metadata-response.schema.json`, `skills/clin-nav/references/omop-metadata-connector.md`.

**Interfaces:** `validate_inspection(...)` validates version-specific codes; existing `classify_inspection(...)` and `assess_connector(...)` pass validated codes through unchanged. No new fields or parameters.

- [ ] Add synthetic tests for explicit 1.1 code acceptance, unchanged incompatible/exit 3 with accepted DQD evidence, 1.0 rejection, no inference, independent non-FK errors, missing evidence, failure redaction, and hash/array/closed-code checks.
- [ ] Run the new tests: expect RED with `unknown-enum` for the new 1.1 code.
- [ ] Extend only the 1.1 enum in Python and portable schema. Preserve the base 1.0 enum through a version conditional.
- [ ] Document code provenance, current DuckDB limitations, and independent structural/evidence decisions; do not claim a blanket lack of FK support.
- [ ] Run all OMOP tests: expect GREEN; review diff and commit.

## Task 2: Verification, Review and Local Integration

**Files:** aggregate-only verification note under `docs/verification/`; no raw response artifacts.

**Interfaces:** consumes Task 1 and the existing 1.1 branch; delivers local main containing both, with no external writes.

- [ ] Run full pytest and `validate_skill.py`, `check_public_boundary.py`, `package_skill.py --check-reproducible`, `render_omop_catalog.py --check`, and `git diff --check`; require exit 0 in the clean isolated worktree.
- [ ] Review the entire range against main using one independent read-only reviewer; resolve Important/Critical findings with failing tests first.
- [ ] Record aggregate results and limitations; commit only intended files.
- [ ] Fast-forward local main, rerun required checks and report any preexisting local-residue failures separately. Never delete `.tmp/` or relax scanner rules to obtain green results.
- [ ] Keep the worktree recoverable if main has residue-related failures; report exact local/remote divergence. No push or release.
