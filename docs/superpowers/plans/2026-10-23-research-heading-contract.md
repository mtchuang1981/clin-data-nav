# Research heading contract implementation plan

> **For agentic workers:** Use superpowers:executing-plans for inline implementation and one final review.

**Goal:** Accept the five approved heading pairs only under an explicitly selected new contract.
**Architecture:** A shared JSON reference supplies aliases to the existing evaluator; default legacy paths remain independent of it.
**Tech Stack:** Python 3.11, JSON, Markdown, existing pytest/Evals and packager.
**Spec:** `docs/superpowers/specs/2026-10-23-research-heading-contract-design.md` (user-approved compatibility scope).

## Global constraints

Preserve legacy output and all 36 aggregate results. No threshold, public
methodology, UI policy, version, private input, historical benchmark, shared
branch or release changes. This is local implementation only.

## Review focus

1. Aliases in prose/code must not supply sections.
2. A translated research section in another output depth must remain forbidden.
3. Chinese headings must not conceal missing content or unsafe claims.
4. Default benchmark calls must remain legacy without loading new data.
5. Corrupt/unknown contracts must not silently downgrade to legacy.

### Task 1: Evaluator and synthetic regression tests

**Files:** `scripts/evaluate_response.py`, new `tests/test_research_heading_contract.py`, new shared JSON reference, new `tests/fixtures/research_headings/omop-phenotype.zh-TW.md`.
**Interfaces:** `evaluate_response(case, rubric, response, *, heading_contract="legacy-v1")`; CLI `--heading-contract`. Existing `Evaluation` dataclass and old CLI payload unchanged.

- [x] Add tests first for Chinese/mixed headings, strict structural negatives, cross-depth aliases, unchanged content/safety rules, fail-closed errors and legacy digest.
- [x] Observe the new-contract tests fail before implementation.
- [x] Implement the minimal opt-in loader/matcher and CLI selection.
- [x] Run the focused evaluator suites; compare all 36 legacy results against pre-change SHA-256 `6c7db3794be2f5b74107a27ae9dae5e385aa82cfabb98be691bf4b67b72b8757`.

### Task 2: Skill and usage documentation

**Files:** `skills/clin-nav/SKILL.md`, both output references, new `evals/research-headings/README.md`.
**Interfaces:** Only the explicitly selected contract permits the JSON aliases; default headings stay English. No new catalog schema or benchmark route.

- [x] Describe opt-in behavior and link the shared reference without duplicating its alias map.
- [x] Review unchanged `agents/openai.yaml`, catalogs, rubric and fixtures.
- [x] Document CLI usage, legacy replay and format/semantic/safety claim boundaries.

### Task 3: Final verification and local handoff

**Files:** new dated aggregate-only verification record.
**Interfaces:** Existing required gates and generated summary checks; no external/private system.

- [x] Run full pytest, validate_skill, check_public_boundary, reproducible packaging, core/compiler summaries and diff check.
- [x] Obtain one fresh read-only whole-change review and resolve material findings.
- [x] Record observed results without model or clinical-effectiveness claims.
- [x] Preserve main and its unrelated untracked backlog; no merge, push, tag or Release.

Results: `docs/verification/2026-10-23-research-heading-contract.md`.
The approved default/opt-in design required no scope changes or deferred review findings.
