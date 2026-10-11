# OMOP Connector 1.2: Independent DQD Evidence Expiration

Date: 2026-10-11

Status: conversational design approved; written specification awaiting review.
This document is a proposal, not an implemented contract or live acceptance.

## Purpose and approved intent

The user requests non-expiring DQD foreign-key evidence because database refresh
intervals are unpredictable. Elapsed time alone must not invalidate evidence
for the same strongly bound snapshot. This does not mean a database permanently
passes DQD or that evidence remains applicable after its underlying inputs change.

Separate metadata observation freshness from DQD evidence expiration. Retain the
current metadata limit, complete coverage, zero failures, strong binding, closed
response validation, and independent structural compatibility decision.

## Existing behavior and root cause

The public implementation currently supports default 1.0 and explicit 1.1.
`validate_capabilities` accepts `max_snapshot_age_seconds` as a positive integer
from 1 through 31,536,000. Both the metadata `observed_at` age and DQD `checked_at`
age use this same capability field. Consequently, changing that field relaxes
both gates; `null` and an arbitrarily large sentinel are not valid settings.

The 1.1 summary binds evidence to `snapshot_binding_sha256`, a pinned public
catalog digest, and the exact public FK requirement-set digest. The public checker
validates these attestations but cannot independently inspect a private snapshot.
No private adapter source, configuration, or diagnostic material was inspected
to prepare this specification.

## Chosen approach and alternatives

Use an explicit 1.2 contract with a separate DQD age policy. Keep 1.0 as the
default, and preserve 1.0 and 1.1 inputs, outputs, verdicts, and exit codes.

Rejected alternatives:

- Increasing the shared limit or using a large sentinel: also accepts older
  metadata observations and obscures policy intent.
- Removing the age check for all versions: silently changes existing consumers
  and reinterprets historical 1.1 evidence.

No automatic downgrade, retry, or conversion from old response files is allowed.

## Public contract 1.2

### Capabilities and inspection

Add the required field `max_dqd_evidence_age_seconds` to 1.2 capabilities and
the top-level 1.2 inspection summary. Its value must agree in both responses:

| Value | Meaning |
| --- | --- |
| `null` | DQD evidence has no elapsed-time expiration |
| Integer from 1 through 31,536,000 | DQD evidence expires after that many seconds |

Booleans, zero, negative values, floats, strings, missing fields, and oversized
integers are invalid. Versions 1.0 and 1.1 continue to reject this extra field.
The inspection policy field is included in canonical `summary_sha256`, byte
limits, and the closed JSON Schema. A capabilities/inspection policy mismatch
is `invalid-response`, with a closed validation code
`evidence-age-policy-mismatch` and no response-derived details.

Keep `max_snapshot_age_seconds` mandatory, finite, and unchanged in meaning.
The private deployment retains its current 86,400-second metadata setting;
24 hours is a deployment policy, not a new universal contract constant.

The MCP inspection request still has exactly the existing six public fields.
Explicit `contract_version: "1.2"` selects the new wire shape. Unsupported 1.2
is `unavailable`; it does not cause a second 1.1 request.

### Consumer authorization and reporting

Add local `allow_nonexpiring_dqd=False` to the connector assessment API and
`--allow-nonexpiring-dqd` to the offline checker. Selecting 1.2 alone does not
authorize a server to disable expiry. If 1.2 capabilities declare `null` without
this consumer opt-in, stop before inspection and return `unavailable` with the
closed code `nonexpiring-dqd-not-authorized`. The option is invalid for 1.0/1.1;
it is not a CLI override of an adapter's finite policy.

For a valid, reportable 1.2 outcome, include the effective
`max_dqd_evidence_age_seconds` in the aggregate result so acceptance cannot be
mistaken for proof of recent checks. Preserve the existing DQD statuses;
`accepted-attestation` means acceptance under the explicitly reported policy.
Do not add a status claiming independently verified private content.

### DQD decision rules

1. Validate the complete response, canonical hash, version, reference, current
   observation, time ordering, and binding before assigning an evidence status.
2. Reject malformed or future timestamps even under a non-expiring policy.
   In 1.2, `checked_at` must also be no later than `observed_at`.
3. When the DQD policy is finite, retain the 1.1 evidence decision order using
   the new DQD limit. The exact age boundary remains valid; only age greater
   than the limit is `stale`.
4. When the DQD policy is `null`, omit only the DQD elapsed-time check.
5. Missing evidence is `unavailable`; incomplete exact FK coverage remains
   `incomplete-coverage`; any failed check remains `failed-checks`; size/mtime
   binding remains `weak-binding`. Only full, zero-failure, strong-binding
   evidence can be `accepted-attestation`.
6. Never modify `foreign_key_status`, structural status, mismatch counts, or
   checker exit code based on the DQD verdict or a limitation code.

An expired metadata observation still produces structural `stale`, regardless
of the DQD policy. Partial/failed scans and invalid responses retain the existing
content-free failure boundary. No accepted DQD result is emitted for those failures.

## Private adapter responsibilities and handoff

The public change documents private responsibilities; it does not implement,
read, or modify the private adapter in this repository.

- Support explicit 1.2 capabilities and the matching closed inspection shape.
- Configure `max_dqd_evidence_age_seconds: null` while retaining a finite
  metadata limit; never reinterpret a 1.1 request.
- At each fresh inspection, establish which snapshot is currently inspected
  and compare its strong binding with the stored DQD evidence binding.
- Content hashing must identify the same consistent snapshot used by the scan
  and DQD checks. An immutable identifier must be non-reusable and governed;
  a label, file size, or modification time is not strong binding.
- A digest copied from the old evidence into a new summary does not demonstrate
  current-snapshot identity. If identity cannot be established, return a null
  DQD evidence object rather than reuse unverified evidence.
- Recompute DQD when data or relevant schema change, ETL changes produce a new
  snapshot, the public catalog/check set changes, or the private check logic or
  execution environment changes in a way that invalidates the evidence.
- Preserve the original `checked_at`; never refresh timestamps to obtain a pass.
- Keep private binding provenance and per-check audit evidence outside Git.
  No rows, SQL, physical identifiers, or private diagnostic text enter responses.

The checker verifies declared bindings and public check identities, not private
hash production, ETL history, check-engine correctness, or immutable storage.
Those remain auditable private-operator responsibilities. Non-expiring evidence
is applicable to the named snapshot, not to all later database states.

## Implementation scope

Future public implementation will narrowly update the packaged validator,
connector assessment API, offline CLI, portable response schema, connector
reference, synthetic fixtures/tests, and relevant bilingual setup guidance.
Review Skill routing, agents configuration, and Evals for consistency; change
them only when required to explain explicit selection and the claim boundary.

Do not bump the Skill version, change research/output contracts, rewrite prior
verification reports, rerun benchmarks, or alter release assets. Private adapter
development is a separate handoff requiring its own authorization. No push, tag,
release, live private access, or DQD execution is part of this design stage.

## Test and acceptance requirements

Use synthetic fixtures and RED-GREEN-REFACTOR before any behavior change.

- 1.0/1.1 retain their exact closed shapes, shared age decisions, defaults,
  failure outputs, and exits; reject 1.2-only fields and flags.
- 1.2 finite age: below/equal/above boundary, correct types, independent metadata
  and DQD ages, and unchanged structural exit mapping.
- 1.2 null age: old strong evidence can be accepted with fresh metadata and
  explicit authorization; without authorization, inspection is never called.
- Weak/missing/mismatched bindings, stale metadata, failed/partial scans,
  future/ill-ordered times, changed references, incomplete coverage, and failed
  checks never become accepted merely because expiry is disabled.
- Policy mismatches, missing/unknown fields, tampered hashes, prohibited values,
  oversized responses, and free-text diagnostics fail closed.
- Invalid capabilities stop before inspection; unsupported 1.2 never retries.
- Packaged and repository entry points agree; schema and Python validators
  enforce the same version-specific fields and limits.
- Full pytest, Skill validation, public-boundary check, reproducible packaging,
  catalog regeneration check, and `git diff --check` pass after implementation.

Only after both implementations are ready and current read-only access is
authorized, request a new repository-external redacted 1.2 summary. Validate it
with explicit non-expiring consent, report structure and DQD separately, and
retain raw artifacts outside Git. Do not convert existing 1.1 files into 1.2.

## Risks and claim boundary

Worst failure: old passing DQD evidence is applied to changed data indefinitely.
Prevent it through current-snapshot strong-binding attestation, fail-closed
missing evidence, explicit consumer consent, and private auditable invalidation.
Fresh metadata alone cannot prove unchanged data.

Second-order risk: consumers treat non-expiring acceptance as current data-quality
certification. Report the policy explicitly and retain the point-in-time
attestation wording. Dual version-specific contracts add maintenance cost;
centralize policy selection without changing old-version branches.

Acceptance establishes only that a closed adapter attestation meets the public
contract for a named snapshot. It does not prove independent private-content
verification, clinical correctness, study fitness, governance approval, or
execution readiness. DQD never substitutes for declared database constraints.

## Review checkpoint

Approve this written specification before preparing the implementation plan.
Implementation begins only after that plan is reviewed and an execution method
is selected. The conversational approval authorizes this specification, not
private adapter changes or release actions.
