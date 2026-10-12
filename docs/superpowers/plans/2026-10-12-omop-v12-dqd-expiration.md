# OMOP Connector 1.2 DQD Expiration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for native execution, or superpowers:subagent-driven-development if the user chooses delegation. Execute task-by-task after plan approval. Steps use checkbox syntax.

**Goal:** Support explicitly authorized, non-expiring DQD attestations for the same strongly bound snapshot without relaxing metadata freshness or structural verdicts.

**Architecture:** Extend the existing packaged validator, assessment harness, and CLI with explicit contract 1.2. Carry a separate DQD age policy in capabilities and the hashed inspection summary. Preserve the default 1.0 and all existing 1.0/1.1 behaviors.

**Tech Stack:** Python 3.11 standard library, pytest, portable JSON Schema, RTK; no new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-11-omop-v12-dqd-expiration-design.md` (written approval 2026-10-12).

## Global Constraints

- Read the spec and this plan before editing; use an isolated `codex/omop-v12-dqd-expiration` branch/worktree at execution time.
- Default `CONTRACT_VERSION` stays `1.0`; `EVIDENCE_CONTRACT_VERSION` stays `1.1`. Add `DQD_POLICY_CONTRACT_VERSION = "1.2"` rather than renaming old constants.
- `max_dqd_evidence_age_seconds` is required in 1.2 capabilities and inspection: `null` or an integer from 1 through 31,536,000, never bool/float/string.
- `max_snapshot_age_seconds` keeps its finite range and meaning. The deployment retains 86,400 seconds; do not hardcode that as the only permitted public value.
- `allow_nonexpiring_dqd=False` and `--allow-nonexpiring-dqd` are explicit consumer consent, not a policy override.
- Keep six public MCP request fields, 262,144-byte hard limit, closed objects, canonical hashing, unchanged catalog and exact 79-requirement FK set.
- No private source/config/rows/schema/diagnostics, live MCP access, DQD execution, raw response in Git, fallback, retries, or conversion of old summaries.
- No Skill version bump, benchmark rerun, historical report rewrite, tag, release, release asset change, or push. Preserve unrelated `docs/optimization-backlog.md`.

## Review Focus

- JSON duplicate keys or non-finite values must not bypass policy validation; test in Task 2.
- An omitted policy is not the same as explicit `null`; test in Task 1.
- `True == 1` and `False == 0` must not bypass integer validation; test in Task 1.
- The installed packaged CLI and repository wrapper must produce identical safe outputs/exits; test in Task 2.
- An old passing digest copied into a fresh summary is only an attestation, not independent proof of current content; document in Task 3 and require private audit at handoff.

## File Map

- `skills/clin-nav/scripts/omop_metadata.py`: closed validation, policy selection, DQD classification.
- `skills/clin-nav/scripts/omop_metadata_connector.py`: pre-inspection consent and bounded safe output.
- `skills/clin-nav/scripts/check_omop_metadata.py`: packaged CLI arguments/exit behavior; repository `scripts/check_omop_metadata.py` remains a thin wrapper.
- `skills/clin-nav/references/omop-metadata-response.schema.json`: version-specific field and enum rules.
- New `tests/test_omop_metadata_v12.py`: synthetic 1.2 fixtures/helpers and contract tests; new `tests/test_omop_metadata_v12_cli.py`: wrapper/packaged CLI and consent tests.
- Existing `tests/test_omop_metadata.py` and `tests/test_omop_metadata_v11.py`: old-version regressions and semantic schema assertions.
- Connector reference and `docs/installation.md`, `docs/installation.zh-TW.md`: usage and private handoff.

## Task 1: Versioned Contract and Independent Evidence Classification

**Interfaces:** Preserve `validate_capabilities(payload, *, contract_version="1.0")`, `validate_inspection(payload, *, catalog, capabilities, as_of, raw_size_bytes: int)`, `classify_inspection(payload, *, catalog, capabilities, as_of)`, and `build_inspection_request(catalog, *, max_response_bytes, contract_version="1.0")`. Their accepted version set expands to 1.2; old-version results do not acquire new fields.

- [ ] Create synthetic `sample_v12(limit=None, *, checked_at="2025-09-20T11:30:00+08:00") -> tuple[dict, dict]` in the new test module. Load existing synthetic 1.0 fixtures, add the existing 1.1 strong-binding/evidence fields with `"a" * 64`, add the new policy to both responses, derive the exact FK-set hash with `expected_fk_check_set`, and rehash using `canonical_json_bytes`. Fix `AS_OF="2026-09-20T12:00:00+08:00"`; retain fresh fixture `observed_at`.
- [ ] Add failing tests with these names and assertions:

| Test | Required assertion |
| --- | --- |
| `test_v12_null_policy_preserves_strong_attestation` | valid contract; DQD `accepted-attestation`; result policy `None` |
| `test_v12_finite_age_boundary` | limit 3,600; age 3,599/3,600 accepted, 3,601 `stale` |
| `test_v12_metadata_age_is_independent` | metadata age 86,401 -> structural `stale`, no accepted DQD result |
| `test_v12_invalid_policy_types_and_missing_key` | `True`, `False`, 0, -1, 1.0, `"86400"`, [], {}, 31,536,001 invalid; missing -> `missing-key` |
| `test_v12_policy_mismatch_and_hash_tamper` | different valid policies -> `evidence-age-policy-mismatch`; unhashed edit -> `summary-hash-mismatch` |
| `test_v12_null_does_not_repair_evidence` | missing/weak/78-of-79/wrong set/one failed -> unavailable/weak-binding/incomplete-coverage/incomplete-coverage/failed-checks |
| `test_v12_binding_reference_and_time_fail_closed` | different snapshot digest, reference mismatch, future time, checked-after-observed -> `invalid-response` |
| `test_v12_constraints_remain_independent` | all 13 missing FK declarations remain `incompatible`, count 13, even with accepted DQD and DuckDB limitation code |
| `test_legacy_versions_reject_policy_fields` | extra policy rejected by 1.0/1.1; their original outputs remain unchanged |

- [ ] Run `rtk proxy python -m pytest -q tests/test_omop_metadata_v12.py`; record expected RED from unsupported 1.2 and closed-key rejection, not import or syntax errors.
- [ ] Implement 1.2-only key sets, type checks, policy equality and hash coverage in `omop_metadata.py`. Add closed `evidence-age-policy-mismatch` and `evidence-time-order-invalid` codes. Preserve existing 1.1 evidence decision precedence; in 1.2 skip only the age check for null policy. Accept the existing 1.1 evidence fields and limitation enums also in 1.2.
- [ ] Update portable schema to distinguish 1.0, 1.1, 1.2: require new policy only in 1.2, reject it in legacy versions, require evidence/binding for both evidence versions. Adjust existing schema tests to assert version semantics rather than obsolete two-version enum or conditional positions; do not weaken legacy runtime tests.
- [ ] Add `test_v12_schema_policy_shape_matches_validator`: inspect required fields, nullable integer bounds, closed objects and version-specific rules. Use existing test dependencies only; equality between two payload fields remains a Python semantic check.
- [ ] Run all OMOP metadata tests; require GREEN and unchanged legacy fixture bytes. Review diff and commit only Task 1 files with `feat: add OMOP 1.2 independent DQD age contract`.

## Task 2: Consent Gate, Safe Aggregates and CLI

**Interfaces:** Extend `assess_connector(get_capabilities, inspect_omop_schema, *, catalog, as_of, hard_max_bytes=HARD_MAX_RESPONSE_BYTES, contract_version="1.0", allow_nonexpiring_dqd: bool=False) -> dict[str, object]`. Validate consent before calling inspection; do not put local consent into the MCP request. `classify_inspection` remains a pure classifier; authorization belongs to the assessment harness.

- [ ] Add `test_v12_null_policy_requires_explicit_consent`: with null capabilities and default consent, assert exact controlled `unavailable` result with `nonexpiring-dqd-not-authorized`, requested version 1.2, and zero inspection calls; with `True`, assert one call and the unchanged six-field request.
- [ ] Add `test_consent_argument_is_boolean_and_version_scoped`: non-bool values or `True` for 1.0/1.1 return content-free `invalid-response` with `invalid-nonexpiring-dqd-option` before either operation. For finite 1.2 policy, consent never disables the finite age gate.
- [ ] Add `test_v12_unsupported_and_unsafe_capabilities_stop`: unavailable/unsafe/wrong-version responses cause no inspection/fallback/retry; all failures retain requested version and no private marker text.
- [ ] Add `test_v12_partial_invalid_and_stale_outputs_are_redacted`: no policy, summary hash, aggregates, or accepted evidence on invalid/partial/failed/stale outcomes. Retain the existing permitted limitation codes for partial/failed scans.
- [ ] Add `test_v12_json_parsing_remains_closed`: duplicate keys, NaN, Infinity, malformed bytes, over-limit responses, unknown fields and synthetic free-text markers fail closed.
- [ ] Add subprocess tests in `tests/test_omop_metadata_v12_cli.py` for both entry points with external temporary inputs: explicit null opt-in -> compatible/exit 0; absent consent -> unavailable/exit 3; 13 FK differences -> incompatible/exit 3; invalid response or flag/version combination -> exit 2. No raw identifiers or response objects appear in stdout/stderr.
- [ ] Run targeted tests and record RED: missing API option/CLI flag and rejected 1.2; preserve original tests.
- [ ] Extend the harness handshake and consent gate, and `_safe_summary` to report the effective policy and existing evidence status only for valid reportable 1.2 outcomes. Preserve 1.0 capability invocation without version kwargs. Unsupported explicit versions stop, never downgrade.
- [ ] Add 1.2 to CLI choices and `--allow-nonexpiring-dqd` with `store_true`. Reject flag use for 1.0/1.1 through the existing content-free parser error. Forward consent to the harness; preserve all exit mappings and external-input path protection.
- [ ] Run targeted and legacy OMOP tests; require GREEN, including both packaged/wrapper CLI outputs. Review diff and commit Task 2 files with `feat: require consent for nonexpiring DQD evidence`.

## Task 3: Documentation, Private Handoff and Public Verification

**Interfaces:** Consume the contract and CLI from Tasks 1/2. Deliver public documentation and deterministic verification; no private code or live calls.

- [ ] Add a documentation contract test in the 1.2 test module requiring `max_dqd_evidence_age_seconds`, explicit `--contract-version 1.2 --allow-nonexpiring-dqd`, unchanged metadata freshness, original check time, snapshot invalidation, and attestation-not-independent-proof wording in the connector reference; require both installation guides to explain opt-in and the separate verdicts. Run it and record RED.
- [ ] Update the connector reference and bilingual installation sections with finite/null examples and policy reporting. Explain why non-expiring DQD is not permanent quality certification. Review `SKILL.md`, `agents/openai.yaml`, and relevant Eval references; leave them unchanged unless they contradict the new opt-in instructions. No new mandatory private dependency.
- [ ] Include the private handoff checklist: explicit 1.2 support; policy echoed and hashed; metadata limit retained; current consistent-snapshot binding established each inspection; old evidence not reused for changed snapshots; uncertain identity -> null evidence; catalog/check-logic changes invalidate evidence; original `checked_at` retained; private audit stays outside Git. Do not claim these controls are implemented privately.
- [ ] Run `rtk proxy python -m pytest -q`; require 0 failures and explain environment-specific skips.
- [ ] Run `rtk proxy python scripts/validate_skill.py`, `rtk proxy python scripts/check_public_boundary.py`, `rtk proxy python scripts/package_skill.py --check-reproducible`, `rtk proxy python scripts/render_omop_catalog.py --check`, and `rtk git diff --check`; require exit 0 for each. Recover unfiltered output if RTK exit/output disagree.
- [ ] Inspect the full diff and tracked file list: only intended public code/docs/synthetic fixtures, no raw responses/private data, no public catalog drift, no version/CHANGELOG/release asset change. Perform final review using the user-selected execution workflow; fix behavioral findings with failing tests first.
- [ ] Record aggregate-only verification in `docs/verification/2026-10-12-omop-v12-dqd-expiration.md`: commands/results, policy and claim boundary, pending private acceptance. Commit intended files; do not push, tag, or release. Local merge remains a separate finishing decision after tests/review.

## Later Private Acceptance (Separate Authorization)

- [ ] Private owner implements and audits the handoff independently; this public plan does not authorize reading or modifying that repository.
- [ ] Once both ends support 1.2 and current read-only access is authorized, call capabilities first, validate boundaries and null policy with consent, then request one fresh six-field inspection. Keep redacted JSON outside repository/installed Skill; no 1.1 conversion.
- [ ] Use the existing offline checker with `--contract-version 1.2 --allow-nonexpiring-dqd` and current RFC 3339 `--as-of`. Require current metadata, exact coverage/hash, matching strong bindings, zero failures, and explicit null policy. Report DQD `accepted-attestation` separately from structural verdict/exit; incompatible structure remains exit 3.
- [ ] If unsupported, incomplete, invalid, weak, or mismatched, stop without retry/override. Public acceptance cannot independently prove the private binding mechanism; retain operator audit evidence privately.

## Plan Review and Execution Choice

The user has approved the written spec, not this implementation plan. Review this
plan and choose native or subagent-driven execution before modifying product code.
Native execution is recommended for the three tightly coupled public tasks and
the user's cost-conservative preference; use one independent final review rather
than a fresh implementer/reviewer for every task. No agents start during planning.
