# Governed Compiler Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native execution, or superpowers:subagent-driven-development if selected by the user. Implement task-by-task only after plan review and execution-method selection. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Route optional governed compilation safely, without inventing local code or weakening existing execution gates, and publish verified v0.10.0 artifacts.

**Architecture:** Add a pure, narrow capability-declaration validator to the packaged Skill. Keep pipeline semantics in the institutional reference, route conditionally from SKILL.md, and retain all existing metadata, parameter, fixture, authorization, and disclosure gates. No compiler, execution client, or private adapter is implemented here.

**Tech Stack:** Existing Python 3.11, pytest, PyYAML, bounded input helpers, repository evaluators, RTK, and the established GitHub release workflow; no new dependency.

**Spec:** `docs/superpowers/specs/2026-10-19-governed-compiler-pipeline-design.md` (written approval 2026-10-19).

## Execution scope update — 2026-10-19

The user subsequently selected **local candidate only; publication paused**.
This overrides the original publication authorization below: do not merge main,
push, create a tag or publish a Release in this round. Tasks 1–4 are complete;
Task 5 is locally complete after independent review, one regression-tested fix,
1885 passed / 13 skipped and reproducible package verification. Task 6 is deferred. Preserve the
unexplained Windows cleanup failure as an unresolved publication blocker.
The aggregate verification record documents actual checks and claim limits.

## Global Constraints

- Keep `adapter_schema_version: "1"`, generic institutional contract revision `1.2`, capability `version: "1"`, and package version `0.10.0` independent. Do not fabricate a prior public generic contract 1.1.
- Preserve OMOP defaults, 1.0/1.1/1.2 closed shapes, six-field inspection requests, catalog, DQD decisions, structural verdicts, and exit codes.
- No private adapter source, schema, dictionaries, tool discovery, live MCP operations, real-data execution, DQD reruns, or private artifacts in Git.
- Use only synthetic examples. No local codes from memory; no hand-written substitute code or edits to a compiled program.
- Fixture success alone never promotes maturity. Apply every existing execution gate and exact specification/program binding.
- Preserve `docs/optimization-backlog.md` and unrelated work. Do not move published tags, overwrite releases, weaken CI, or rerun/reinterpret frozen benchmarks.
- User has authorized GitHub publication after verification. The plan review is not another request for publication authority.

## Review Focus

1. An absent capability differs from explicit null or an incomplete declaration: absence retains legacy routing; malformed declarations fail closed (Task 2).
2. Python booleans, duplicate operations, unknown keys, and oversized strings must not satisfy a declaration (Task 2).
3. Tool outputs or a tested digest from another program cannot override missing metadata, authorization, unresolved concepts, or disclosure controls (Tasks 3/4).
4. Feasibility scoping does not permit pre-approval execution; a proposed index event requires confirmation, and unsupported analysis must not be replaced by code (Tasks 3/4).
5. The intermittent Windows cleanup failure and remote Actions updates must not be hidden by selective retries or stale local tracking information (Tasks 1/5/6).

## File Map

- New `skills/clin-nav/scripts/compiler_pipeline.py`: declaration validation only, no I/O, tool calls, code generation, or maturity promotion.
- New `tests/test_compiler_pipeline.py`: synthetic valid/invalid declarations and controlled diagnostics.
- `skills/clin-nav/references/institutional-adapter-contract.md`: sole semantic contract, synthetic manifest and walkthroughs.
- `skills/clin-nav/SKILL.md`, `references/rwe-question-routing.md`, and `references/evidence-output-template.md`: concise conditional routing and reportable gaps; avoid duplicated pipeline rules.
- `tests/test_skill_contract.py`, `tests/test_eval_contract.py`, `tests/test_response_evaluator.py`, `evals/cases.yaml`, `tests/fixtures/baseline/<new-case-id>.md`, `tests/fixtures/forward/<new-case-id>.md`, and `evals/README.md`: current-catalog regression coverage and generated summary; historical benchmark inputs remain frozen.
- `skills/clin-nav/agents/openai.yaml`: review for consistency; preserve fields unless an actual contradiction requires a narrow change.
- Release metadata, installer, packager, citation, bilingual README/install guides/changelogs, `.github/workflows/release.yml`, release tests and new `docs/releases/0.10.0.md`: synchronized package version and truthful capability descriptions.
- `docs/verification/2026-10-19-governed-compiler-pipeline.md`: aggregate-only local verification; new dated publication report after release.
- Existing benchmark cleanup implementation/tests: diagnostic scope in Task 1, with a separate bugfix only if root cause is established.

## Task 1: Reconcile Histories and Establish a Release-Safe Baseline

**Files:** Read the spec, `AGENTS.md`, `docs/release.md`, `scripts/evaluate_simulation_benchmark.py`, and the relevant tests. Only change benchmark code/tests if diagnosis demonstrates a defect; do not preselect a fix.

**Interfaces:** Preserve existing benchmark CLI, transaction/handle ownership rules, evidence formats, and exit codes. Produce a verified integration baseline or an explicit release blocker.

- [ ] Fetch `origin/main`, record both full SHAs and their merge base, and inspect remote changes. The design observed local `585a7ed` after its document commit and remote `1fe592c`; recheck rather than assuming they remain current.
- [ ] Use the worktree skill to create/reuse isolation and branch `codex/governed-compiler-pipeline`. Safely merge the current remote main into the isolated local history, retaining both local OMOP commits and remote Actions pins/tests. No reset, force-push, or unrelated cleanup.
- [ ] Run baseline full pytest with official Python 3.11.9. The existing available executable is `.worktrees/v0.7.1-output-contract/dist/py311-venv/Scripts/python.exe` under the primary repository; verify availability/version and use an absolute path from an isolated worktree.
- [ ] Investigate the recorded failure `tests/test_simulation_benchmark.py::test_windows_summary_close_after_effect_is_never_retried[parent]`: full suite left a backup temporary file; one isolated rerun passed. Preserve both observations; do not call it fixed or known harmless.
- [ ] Compare the isolated test, its three close-seam variants, the surrounding cleanup tests, then the full file in the same environment. Trace `_SummaryTransaction` cleanup ownership and parent/backup handle close order. Add only synthetic bounded diagnostics outside Git if required; do not retry an ambiguously closed raw HANDLE or delete unrelated temporary files.
- [ ] If a code/test defect is established, add a deterministic failing regression before a minimal fix and commit that fix separately. If evidence is insufficient, record the unresolved cause and keep release blocked; obtain direction before expanding into a benchmark architecture rewrite.
- [ ] Require full baseline pytest and the four repository gates to pass before feature work. Record commands, real exit codes, environment skips, and the integration SHA. A passing isolated retry does not erase a failed full-suite run.

## Task 2: Validate Only the Optional Capability Declaration

**Files:** Create `skills/clin-nav/scripts/compiler_pipeline.py` and `tests/test_compiler_pipeline.py`.

**Interfaces:** Produce `validate_compiler_pipeline_capability(payload: object) -> tuple[str, ...]`. It accepts the capability object, not an entire manifest, and returns an empty tuple for a valid declaration. No parsing, file opening, network, adapter invocation, or execution-readiness assessment.

**Closed shape and bounds:** Exactly `version`, `operations`, `spec_format`, `fixture`, `scope`. Require an ordinary dictionary; strings must be ordinary strings and collections ordinary lists. `version` is `"1"`; operations are exactly the four distinct logical names, order independent. `spec_format` is a 1–128-character ASCII identity matching `[A-Za-z0-9][A-Za-z0-9._:/@+-]*`; its governed owner must establish version meaning and compatibility separately. Fixture is `synthetic` or `approved-deidentified`. Scope has 1–16 distinct labels, each 1–64 characters matching `[a-z][a-z0-9]*(?:-[a-z0-9]+)*`. No arbitrary nested data.

**Diagnostics:** Sorted, unique tuples drawn only from `invalid-type`, `missing-key`, `unknown-key`, `unsupported-version`, `invalid-value`, `duplicate-value`, `limit-exceeded`. Never echo input values, unknown key names, or exception details. Malformed objects do not raise uncontrolled exceptions. Missing declaration in a manifest is handled by legacy routing; passing explicit null to this helper is invalid.

- [ ] Add a synthetic complete declaration and tests named `test_complete_pipeline_is_valid`, `test_operation_order_is_not_execution_order`, `test_unknown_duplicate_and_missing_operations_fail`, `test_closed_shape_and_exact_types`, `test_string_and_collection_boundaries`, and `test_diagnostics_never_echo_synthetic_private_marker`.
- [ ] Assert all four operations are required; bool/numeric versions, tuples, explicit null, extra keys, duplicate scopes, control characters, empty/over-limit identifiers, and unsupported fixture/version values fail. Assert scope/spec-format boundaries at the limit and one character/item beyond it.
- [ ] Run `rtk proxy python -m pytest -q tests/test_compiler_pipeline.py` and observe RED for the absent implementation, not a broken test harness.
- [ ] Implement the exact pure interface and bounded checks. Inspect collection lengths before traversing them. Do not add a generic manifest parser, CLI, JSON loader, or a runtime maturity engine.
- [ ] Require GREEN, stable diagnostic ordering, and no modification of inputs. Check the absence of I/O/tool dependencies, review diff, and commit only this deliverable.

## Task 3: Route Governed Compilation and Feasibility Safely

**Files:** Modify the three Skill/reference files in the file map and `tests/test_skill_contract.py`; review output template and agent metadata. Consume Task 2's declaration semantics without creating another copy of the rules.

**Interfaces:** Keep existing output depths, common formal header, maturity labels, actionable gap slots, optional SAP handoff, and metadata-only access boundary. A capability declaration selects a possible route, not permission to run it.

- [ ] Add failing contract tests for: optional route with unchanged absent-capability behavior; every-code provenance and unresolved logical parameters; scope mismatch stopping at the logical contract; exact spec/program digest binding; unavailable/failed/skipped fixtures not passing; preservation of metadata and authorization gates; output minimization before model ingestion; feasibility/index proposal boundaries.
- [ ] Run targeted tests to establish RED before editing Skill guidance. Preserve original regression assertions; do not loosen existing unknown-schema restrictions to accommodate the pipeline.
- [ ] Add the optional capability section after `Code maturity` in the institutional reference. Include the synthetic declaration, local tool mapping prerequisites, four operations, complete binding/invalidation chain, independent versions, disclosure/minimization, and gate-dependent maturity table from the approved spec.
- [ ] Add the synthetic adults/class-A-versus-class-B 2020–2022 walkthrough. Explicitly supply approved dictionary/parameters, current metadata, authorized synthetic runtime, expected fixture results, and matching digests before reporting `executable`. Its no-runtime variant remains `parameterized`; it never reports real patient counts or performs analysis.
- [ ] Insert concise conditional pipeline routing in the execution gate, logical concept-set provenance in the data-contract section, and the three proposed failure modes. Never hand-write/edit institutional program code for an in-scope governed route. Unsupported or malformed capabilities do not trigger improvised execution.
- [ ] Add `Feasibility-count requests` after intent classification. Separate specification from permission, ask investigator-only ambiguities, mark unstated index dates as proposals, apply disclosure controls, and route out-of-scope analysis separately without claiming all methodological discussion requires approval.
- [ ] Ensure the implementation template can report capability status, each unmet gate, and local artifact/digest references without exposing private content. Retain natural-language unresolved mappings and the specification-only marker. Keep `SKILL.md` below 500 lines and preserve unrelated UI/invocation settings.
- [ ] Require targeted tests and `python scripts/validate_skill.py` to pass; review references, agent metadata, and full diff. Commit the public routing change.

## Task 4: Current-Catalog Regression Cases and Bounded Behavior Probes

**Files:** `evals/cases.yaml`, `tests/test_eval_contract.py`, `tests/test_response_evaluator.py`, paired `tests/fixtures/baseline/<new-case-id>.md` and `tests/fixtures/forward/<new-case-id>.md`, the generated block in `evals/README.md`, and aggregate verification record. Raw model answers/probe artifacts remain repository-external. Hand-authored synthetic fixture answers are not observed model responses.

**Interfaces:** Reuse `scripts/evaluate_response.py` and existing catalog schema/rubric. Do not change historical benchmark scoring, thresholds, release bindings, frozen prompts/results, or the interpretation of earlier regex false negatives.

- [ ] Add current-catalog synthetic cases for: complete pipeline/all gates; fixture unavailable; mismatched tested digest despite a pass claim; missing metadata/authority despite a pass claim; out-of-scope feasibility analysis with an unconfirmed index proposal; and absent capability/unknown schema legacy behavior.
- [ ] Each case specifies its expected depth, minimum semantic requirements, and concrete forbidden actions. Pair satisfactory synthetic fixture answers with negative variants so the evaluator demonstrably rejects missing gates, invented code, unauthorized real-data execution, and false maturity claims. Add these assertions before new fixtures/rules; observe RED then GREEN.
- [ ] Prefer case-specific patterns and the existing evaluator. Do not build a second scoring engine or treat keyword matches as semantic or safety proof. Review any flagged answer in context and preserve the automatic result; no post-hoc threshold tuning.
- [ ] Regenerate the current Eval summary with the existing renderer, then require `python scripts/render_eval_summary.py --check`. Do not regenerate frozen historical benchmark evidence.
- [ ] Run one bounded behavioral probe using a fixed combined-pressure synthetic scenario, five fresh samples without the new guidance and five with it. Freeze the scenario and review criteria before sampling; use the same available model/settings, no tools/network/private data, and separate sessions. Scenario pressures request hand-written fallback code, fixture-pass promotion without metadata/authorization, and automatic opening of a private artifact; the synthetic facts also declare the available governed route.
- [ ] Preserve each observed result, including safe baseline refusals. Compare actual routing, maturity, unmet gates, and handling of private artifacts. Never manufacture a failing baseline. If no baseline failure appears, do not claim a demonstrated behavioral improvement or add speculative prohibitions; distinguish a new documented interface from measured benefit.
- [ ] Use only an available, authorized fresh-session runner; record model/settings and aggregate counts. If unavailable, stop and report behavioral verification as blocked rather than launching another campaign or substituting regex success. If dangerous behavior occurs, add a failing regression and correct only supported guidance defects before repeating a predefined probe.
- [ ] Commit only synthetic catalog/tests and aggregate evidence, not provider logs or raw answers. This is a ten-answer Skill probe, not a restart of the historical 72-cell campaign or human effectiveness assessment.

## Task 5: Prepare and Verify the v0.10.0 Candidate

**Files:** `pyproject.toml`, `scripts/install_local.py`, `scripts/package_skill.py`, `CITATION.cff`, `README.md`, `README.zh-TW.md`, `CHANGELOG.md`, `CHANGELOG.zh-TW.md`, relevant installation sections, `.github/workflows/release.yml`, new `docs/releases/0.10.0.md`, and their existing release/metadata/packaging tests.

**Interfaces:** Preserve existing installer/packager/verifier APIs, release writer isolation, immutable dispatch SHA, annotated-tag verification, artifact checksum verification, and cross-platform byte equality.

- [ ] Add/update failing version assertions for 0.10.0 and new artifact names before modifying version constants. Use `rg` to identify all current-release references. Distinguish mutable current-candidate documentation from immutable historical reports, artifact hashes, examples, and links; no blind repository-wide replacement.
- [ ] Synchronize current version locations, workflow's version/notes paths, bilingual changelogs and static release notes using the actual Taiwan release-preparation date. Preserve the newly merged Actions pins and tests. Do not claim the candidate is the current verified public release before publication.
- [ ] Describe generic pipeline routing/declaration checks separately from OMOP 1.1/1.2 changes carried since v0.9.0. Explicitly state that no private compiler, private tool mapping, institutional conformance, human effectiveness, or real-data execution was verified by this release.
- [ ] Run full `python -m pytest -q`, `python scripts/validate_skill.py`, `python scripts/check_public_boundary.py`, `python scripts/package_skill.py --check-reproducible`, and `git diff --check`. Explain skips; no ignored failure, repeated-until-green assertion, or manual dismissal replaces diagnosis.
- [ ] Run applicable generated checks: `render_eval_summary.py --check`, `render_omop_catalog.py --check`, and existing effectiveness/benchmark synthetic report renderer checks with their documented paths. The historical report bytes/results must remain unchanged.
- [ ] Run required checks with official Python 3.11.9. Build with `package_skill.py --output-dir dist/v0.10.0-a` and `--output-dir dist/v0.10.0-b`; compare both ZIP and manifest byte-for-byte. For each directory run `python scripts/verify_release.py artifacts --archive <directory>/clin-nav-0.10.0.zip --manifest <directory>/clin-nav-0.10.0.manifest.json`. Independently inspect archive contents and hashes; keep candidate output untracked.
- [ ] Review the whole branch and final artifact with one independent reviewer under the user-selected execution method. Correct demonstrated findings with failing tests first. Record exact commands/results, probe boundaries, pending private acceptance, and package hashes in the aggregate-only verification report.
- [ ] Require intended commits clean in isolation and leave the unrelated primary-checkout backlog untouched. Commit candidate version/release metadata separately. If any gate remains unresolved, stop before main publication or tags.

## Task 6: Integrate, Publish, and Independently Verify

**Files:** New publication verification report; no mutation of previous release reports or assets.

**Interfaces:** Follow `docs/release.md` and `scripts/verify_release.py`. This task consumes the reviewed exact candidate commit and its package, not uncommitted work or a moving tag ref.

- [ ] Recheck remote main for intervening changes, integrate without force, and rerun affected/full verification if the candidate changes. Merge locally and verify the final commit before pushing main. Preserve all unrelated files.
- [ ] Establish a supported GitHub authenticated write path through existing tools/CLI. If `gh` still returns 401, request user-assisted supported sign-in; never copy tokens from another application's store, print credentials, or silently change global auth settings. Approval infrastructure failure must be resolved through the normal review path.
- [ ] Push main, then wait for the exact commit's Windows/Ubuntu validation, package comparison, and CodeQL results. Inspect real job/step conclusions, not an aggregate icon. On a failure or unresolved high finding, keep the release blocked and diagnose; do not dismiss or weaken tests to publish.
- [ ] Verify `v0.10.0` does not already exist remotely. Create a new annotated tag using the exact static release notes and reviewed main commit; push only that tag. If occupied, stop for a new version decision instead of moving it.
- [ ] Dispatch the existing release workflow from main with that tag and require every validation/build/publication step to succeed. Keep repository code out of the final writer job and retain its exact uploaded-artifact binding/checksums.
- [ ] Verify the public release tag's object and peeled commit, exactly two assets `clin-nav-0.10.0.zip` and `clin-nav-0.10.0.manifest.json`, asset IDs/sizes, and actual downloaded bytes. Independently verify the manifest and archive SHA-256 with the existing verifier.
- [ ] Record exact main/tag SHAs, workflow/release URLs, asset facts and hashes in a new dated public verification report. Commit/push that report separately without moving the published tag. Distinguish source-document contract completion from private operational readiness.

## Plan Self-Review and Execution Choice

The plan maps every spec section to a task: version/shape (2/3/5), routing,
scope and authorization (3/4), chain/maturity/minimization (3/4), baseline and
integration (1/6), tests and claims (2–5), and public publication (5/6).
The validator is deliberately not a compiler or maturity engine. The unresolved
Windows cleanup failure is a blocker, not an assumed fix.

Recommended execution: **Native**, task-by-task in this session, with the
bounded ten-answer probe and one independent whole-branch final review.
The tightly coupled contract/routing/tests do not justify a fresh implementer
and reviewer for every task. Subagent-driven execution is an alternative if
the user prefers its higher per-task review cost.

Review this plan and select the execution method before product changes.
No agents, probe sessions, private tools, Git push, tag, or release are started
during this planning stage.
