# Project-wide STE-inspired v0.11.0 implementation plan

> **For agentic workers:** Use inline execution, bounded disjoint-file editing support under dispatching-parallel-agents, and one fresh final semantic review. No per-file agent chain.

**Goal:** Review all 42 current public Markdown guidance files, improve unclear English and Traditional Chinese instructions, and publish verified v0.11.0.
**Architecture:** Preserve contracts and frozen evidence. Separate language-edit ownership from version synchronization, verification and publication. Use existing tools, not a new STE compliance engine.
**Tech Stack:** Markdown, Python 3.11.9, existing pytest/Eval/package/release scripts, GitHub CLI/Actions.
**Spec:** `docs/superpowers/specs/2026-10-24-ste-project-release-design.md`, user approved.

## Global constraints

- Preserve normative force, conditions, stop rules, source honesty and execution maturity.
- Preserve code blocks, paths, identifiers, labels, canonical vocabulary, numeric limits and citations during prose editing.
- Preserve historical releases/records/plans, protocols, fixtures, generated report templates and old changelog sections.
- Preserve legacy evaluator results: 36-cell SHA-256 `6c7db3794be2f5b74107a27ae9dae5e385aa82cfabb98be691bf4b67b72b8757`.
- Never access private/ignored materials or submit the primary untracked backlog.
- No formal STE, model-effectiveness or clinical-validity claim.
- Version 0.11.0. Normal checked PRs only; no force, direct main push, admin bypass or protection edits.
- Existing release authority covers tag and Release after all gates. Stop on a new failure or material scope conflict.

## Review focus

1. A numbered action must retain the condition/authorization that governed it.
2. English and Chinese must retain the same action, certainty, quantity and stop behavior.
3. No old result or verifier threshold may change to accommodate prose.
4. Published version/hash claims must follow actual publication/download evidence.
5. Existing v0.10.0 assets and references remain historical truth, not replaceable outputs.

## Ownership and coverage inventory (42 files)

Group A (English public guides, 14 files): `README.md`, `CONTRIBUTING.md`,
`SECURITY.md`, `AGENTS.md`, `.github/pull_request_template.md`,
`docs/architecture.md`, `docs/glossary.md`, `docs/installation.md`,
`docs/learning-paths.md`, `docs/release.md`, `docs/repository-settings.md`,
and all three tracked Markdown examples. AGENTS and PR checklist may be
reviewed/retained to preserve the working agreement and attestation wording.

Group B (Chinese guides and bilingual checklists, 8 files): `README.zh-TW.md`,
`docs/installation.zh-TW.md`, `docs/glossary.zh-TW.md`,
`docs/learning-paths.zh-TW.md`, governance checklist EN/TW and recovery checklist EN/TW.

Group C (coordinator, 20 files): Skill entrypoint and nine Markdown references;
the eight operation READMEs (core, benchmark, compiler pipeline, effectiveness,
governance, recovery, OMOP connector, research headings); benchmark summary-schema
and effectiveness input-schema. Review unchanged UI metadata separately.

### Task 1: Baseline, coverage and prose edit

**Consumes:** Approved spec, tracked-file inventory and existing public text.
**Produces:** Ownership-isolated Markdown edits and a dated coverage table.

- [x] Complete unchanged baseline pytest before writers edit.
- [x] Read applicable STE references; use four passes: vocabulary, structure, grammar, safety/punctuation.
- [x] Edit only assigned files; record every file as edited or reviewed/retained with a reason.
- [x] Preserve generated blocks, fixed shapes and protected content exactly.
- [x] Compare English/Chinese meaning and run existing document/Skill/contract tests.
- [x] Add failing tests only if a real behavior change is required; prose for humans earns no wording-only tests.

### Task 2: Version preparation

**Files:** Current metadata, installer/packager, workflow version/notes pins, citation,
new changelog entries, current README navigation, version tests, `docs/releases/0.11.0.md`.
**Consumes:** Completed prose edit; no simultaneous writer ownership.
**Produces:** Synchronized local v0.11.0 candidate with honest publication status.

- [x] Update version expectations first and observe RED before version changes.
- [x] Change only version/date/current-note bindings in runtime/tooling.
- [x] Retain verified installation hashes for the currently published version until post-publication.
- [x] Run focused version/installer/package tests to GREEN.

### Task 3: Candidate verification and review

**Produces:** Reviewed commit, two identical builds, aggregate-only local evidence and complete coverage ledger.

- [x] Run full pytest; validate_skill; check_public_boundary; package_skill --check-reproducible.
- [x] Check core/compiler summaries and synthetic effectiveness/benchmark reports without rewriting them.
- [x] Verify legacy digest and opt-in heading tests.
- [x] Rebuild package twice and compare ZIP/manifest bytes and hashes; run artifact verifier and public-content review.
- [x] Review full diff and obtain one fresh semantic/bilingual review; resolve material findings with appropriate tests.
- [ ] Commit only scoped files, excluding all private/raw materials and unrelated backlog.

### Task 4: PR, main gates and publication

**Consumes:** Verified candidate and explicit user publication authority.
**Produces:** Normal PR/main integration, new annotated tag and published Release.

- [ ] Push feature, create/attach PR, require both platforms, compare-packages and CodeQL on exact head.
- [ ] Merge normally after CLEAN; fetch/fast-forward main and require main's own complete gates and zero relevant open alerts.
- [ ] Create/push annotated v0.11.0 at exact verified main; dispatch release workflow from main with that tag.
- [ ] Require all Release jobs/steps success; verify tag object and peeled commit.
- [ ] Download exactly ZIP/manifest; compare independent SHA-256 and local bytes; record actual immutability flag.

### Task 5: Published documentation and final handoff

- [ ] Update current public version/hash pointers only after actual download verification.
- [ ] Add dated publication evidence, run focused/full required checks and submit a normal post-publication PR.
- [ ] Wait PR/main gates, sync main and confirm old/new published assets unchanged.
- [ ] Report actual coverage, tests, release URL, hashes and unresolved risks without efficacy or STE-certification claims.

## Execution rulings

The user's explicit approval to apply STE throughout overrides another writing
skill's extra paragraph-by-paragraph confirmation cycle. Preserve all factual
and technical safeguards. Disjoint editing support is used only for independent
language-file groups; release/version work stays with the coordinator.
