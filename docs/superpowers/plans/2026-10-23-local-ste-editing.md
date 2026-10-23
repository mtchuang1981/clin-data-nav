# Local STE-inspired editing plan

> **For agentic workers:** Use superpowers:executing-plans for this bounded local edit. Steps use checkbox syntax for tracking.

**Goal:** Make four approved English instruction passages easier to follow without weakening their contracts.

**Architecture:** Edit Markdown only. Separate conditions, actions and explanatory mechanisms. Retain technical identifiers and use existing validators and Evals.

**Tech Stack:** Markdown, existing pytest and packaging scripts, official Python 3.11.9.

**Spec:** The user-approved local-edit scope below, following the 2026-10-23 applicability review.

## Approved scope and approaches

The user selected local STE-inspired editing rather than a mechanical repository-wide rewrite. Start with installation troubleshooting, then the release instructions, governed compiler paragraph and SAS evidence fields. The alternative of strict vocabulary replacement risks changing normative strength and technical identifiers, so it is excluded. This is not STE certification.

The separately identified process correction is explicit: update main through a normally checked PR, not a direct owner push. Do not change GitHub settings or workflows in this task.

## Global constraints

- Preserve `must`, `should` and `may` strength, authorization, scope and maturity gates.
- Preserve commands, paths, anchors, JSON fields, output labels and evidence fields.
- No version bump, public API change, benchmark rerun or historical score revision.
- No private Adapter, schema, consultations or participant materials.
- No merge, push, tag or Release in this task. Keep unrelated backlog untouched.
- Review `agents/openai.yaml`, Evals and referenced contracts when editing SKILL.md.

## Review focus

- A valid declaration must not authorize tools or private reads.
- Fixture success must not bypass current metadata or execution gates.
- Unsupported pipelines must remain logical specifications without substitute code.
- Unavailable retrieval must not become a claim of a reviewed source.
- Installation recovery must not mix Release assets or overwrite unresolved targets.

### Task 1: Human-facing operating instructions

**Files:** `docs/installation.md`, `docs/release.md`.

**Interfaces:** Existing installation anchors/commands and trusted Release asset identities remain unchanged. The release document consumes the already-established normal-PR practice.

- [x] Inspect the unchanged source and run the initial suite. Because editing overlapped the initial full run, do not claim it as pristine baseline evidence.
- [x] Split diagnosis and recovery into ordered actions, with failure conditions before retries.
- [x] Separate approved publication steps from workflow mechanisms and explicitly require a normal PR without admin bypass.
- [x] Run existing documentation and release tests. Do not add wording-only tests for human prose.

### Task 2: Agent-facing instructions and evidence checklist

**Files:** `skills/clin-nav/SKILL.md`, `skills/clin-nav/references/retrieval-playbook.md`.

**Interfaces:** Same institutional-adapter contract and evaluator; unchanged UI metadata, Eval catalogs and fixed output labels.

- [x] Run a bounded public-synthetic baseline consumer probe before edits.
- [x] Put pipeline applicability and authorization before the numbered sequence.
- [x] Convert the SAS evidence fields to a vertical checklist without dropping fields.
- [x] Compare candidate consumer answers with baseline; report regression or inconclusive findings honestly, not an effectiveness gain.
- [x] Run full pytest, validate_skill, check_public_boundary and package_skill --check-reproducible.
- [x] Run generated Eval summary checks, review complete diff and obtain one fresh whole-change review.
- [x] Leave the local branch ready for handoff; no shared-branch mutation or publication.

Results are recorded in `docs/verification/2026-10-23-ste-local-editing.md`.
Delivery is a local commit only. Merge, push and publication remain separate.

## Verification boundary

This is a wording-preservation change, not a new behavioral rule. Deterministic gates and bounded synthetic probes do not prove improved model behavior, STE compliance or clinical validity. If probes reveal a safety regression, stop rather than weakening rules or changing thresholds.
