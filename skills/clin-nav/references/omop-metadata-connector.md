# Optional OMOP Metadata Connector

## Purpose and boundary

Use this optional, read-only route only to compare a private Adapter's redacted
OMOP CDM v5.4 structural summary with the pinned public catalog. It improves a
logical mapping checklist and reports validation gaps; it does not read rows,
execute SQL, establish study fitness, or authorize an analysis.

The connector is considered only when the current request is for a local
schema, mapping, metadata, or implementation-readiness deliverable and the
user explicitly authorizes read-only metadata access in the current request.
Naming an institution, mentioning OMOP, or having an Adapter available is not
authorization. Do not automatically discover, install, or retry a connector.

## Optional 1.1 DQD foreign-key evidence

Version `1.0` remains the default and its wire shape, structural status, and
checker exit codes are unchanged. Request `1.1` explicitly with
`--contract-version 1.1` for an offline check, or with
`assess_connector(..., contract_version="1.1")` in a governed integration.
The 1.1 capability call requests that same version; an unsupported version is
`unavailable`, with no 1.0 fallback or automatic retry.

Version 1.1 requires `dqd_foreign_key_evidence` in the inspection summary.
It may be `null` when evidence is absent, or a closed object containing only
binding kind, a digest of the snapshot binding (for strong binding), check
time, public catalog digest, digest of the exact checked public FK requirement
set, and aggregate expected/checked/failed check counts. The public FK set is
the sorted list of every catalog FK edge from the 13 allowlisted source tables,
including references to public standard target tables outside the allowlist.
It currently contains 79 requirements. Hash the canonical JSON object
`{"checks": [sorted public FK edge identifiers]}` using the same UTF-8,
sorted-key, compact, trailing-LF rule as `summary_sha256`. Merely reporting
13 checked tables or 79 checked items is not sufficient: the exact set digest
must match. All 1.1 fields are covered by `summary_sha256` and size limits.
The 1.1 summary also carries `snapshot_binding_sha256`; the evidence digest
must equal it. This equality checks that both attestations name the same
snapshot token, but does not let the public checker prove how the private
token was produced. For weak binding both digests are `null`.

The separate `dqd_foreign_key_evidence_status` is one of
`accepted-attestation`, `weak-binding`, `stale`, `incomplete-coverage`,
`failed-checks`, or `unavailable`. Strong binding requires a content SHA-256 or
an immutable snapshot-ID digest; size and modification time are only
`weak-binding`. `accepted-attestation` means the *declared* binding and exact
coverage pass public contract checks; the public checker cannot independently
inspect the private snapshot or prove the adapter's attestation. Private
operators must retain auditable binding and per-requirement DQD results outside
this repository. DQD checks are point-in-time referential-integrity evidence,
not a database-enforced FK constraint. They never rewrite
`foreign_key_status`, structural `status`, or checker exit code. An
`incompatible` structure remains exit 3 even with accepted DQD evidence.

Before a private 1.1 trial, resolve any 1.0 `snapshot-incomplete` or partial
scan at the private source and produce a new, complete redacted summary.
Changing contract version cannot turn an incomplete scan into a pass. The
public repository neither diagnoses private scan internals nor stores raw DQD
results, local identifiers, rows, or private diagnostic text. Report structural
compatibility and evidence status as two distinct outcomes.

## Optional 1.2 independent DQD expiration

Version `1.2` is explicit opt-in; it does not replace the default `1.0` or
reinterpret `1.1` evidence. Unsupported 1.2 is `unavailable`, without fallback
or retries. The same two operations and six public inspection request fields
remain in use.

Capabilities and the top-level inspection summary must both carry
`max_dqd_evidence_age_seconds`. The values must agree and the summary field is
covered by canonical `summary_sha256`, closed validation, and byte limits:

- `null`: no elapsed-time expiry for the same strongly bound snapshot.
- Integer from 1 through 31,536,000: a separate finite DQD evidence age limit.

Missing is not null. Booleans, floats, strings, zero, negatives and larger
integers are invalid. Policy disagreement is `invalid-response` with
`evidence-age-policy-mismatch`. Legacy contracts reject the extra field.

`max_snapshot_age_seconds` still limits metadata `observed_at` freshness; it
remains finite. For example, keep 86,400 seconds for metadata even when DQD
expiry is disabled. Non-expiring evidence cannot rescue stale metadata, a
partial scan, weak binding, incomplete exact coverage or failed checks. Future
times are invalid; `checked_at` must be no later than `observed_at` in 1.2.

Explicit local consent is also required for a null policy. Use
`assess_connector(..., contract_version="1.2", allow_nonexpiring_dqd=True)`
or the offline checker below. Without consent, stop after capabilities with
`unavailable` / `nonexpiring-dqd-not-authorized`, before inspection. Consent is
invalid for 1.0/1.1 and never overrides a finite adapter policy.

```text
python scripts/check_omop_metadata.py --capabilities <external-capabilities.json> --input <external-inspection.json> --as-of <RFC-3339-timestamp> --contract-version 1.2 --allow-nonexpiring-dqd
```

For valid reportable 1.2 summaries, output the effective
`max_dqd_evidence_age_seconds` alongside `dqd_foreign_key_evidence_status`.
`accepted-attestation` under a null policy is acceptance of point-in-time
evidence for the named snapshot, not proof of a recent rerun, permanent data
quality or independently verified private content. Structural status and
checker exits stay independent: missing declared FKs remain incompatible / 3.

### Private 1.2 implementation handoff

The private owner must implement and audit the following outside this repository:

1. Explicit 1.2 capabilities and matching policy in the hashed closed summary;
   keep old-version behavior and finite metadata freshness unchanged.
2. Establish the identity of the current consistent snapshot at each inspection.
   Compare its content hash or governed immutable-ID digest with the DQD evidence.
   Copying an old digest into a newly timestamped summary is not verification.
3. If current identity cannot be established, return null DQD evidence rather
   than reuse unverified results. File size/mtime remain weak binding.
4. New data/relevant schema, a changed ETL-produced snapshot, public catalog/FK
   set changes, or material private check-logic/environment changes invalidate
   the old evidence. Recompute DQD; never rewrite the original `checked_at`.
5. Retain binding provenance and per-requirement results privately. Return only
   closed aggregates; never rows, SQL, physical names or private diagnostic text.

The public checker validates the adapter's declaration and exact public check
identity; it cannot independently verify private hashing, storage immutability
or check-engine correctness. Private implementation and live acceptance are
separate work, not accomplished by changing the public contract.

### DuckDB cyclic-FK declaration limitation (1.1 and 1.2)

An adapter may explicitly include `duckdb-cyclic-fk-ddl-limited` in the existing
`limitation_codes` array when it has established that its DuckDB version cannot
declare the cyclic foreign-key requirements of the public OMOP catalog. The
code is an adapter-reported platform limitation, not an independently verified
backend diagnosis. ClinNav does not infer it from missing FK metadata. Version
1.0 continues to reject this code as an unknown enum; existing 1.0 codes remain
valid in both versions.

DuckDB supports ordinary foreign keys, but its current documentation states
that `ALTER TABLE ADD CONSTRAINT` is unsupported. OMOP v5.4 includes reciprocal
`CONCEPT.VOCABULARY_ID` to `VOCABULARY.VOCABULARY_ID` and
`VOCABULARY.VOCABULARY_CONCEPT_ID` to `CONCEPT.CONCEPT_ID` references. These facts
explain a cyclic-DDL limitation; they do not establish that every missing FK is
caused by a cycle, or that every DuckDB dataset is unusable. The private owner
must retain version-specific supporting evidence and reevaluate the limitation
when backend capabilities change.

Sources: [DuckDB foreign keys](https://duckdb.org/docs/current/sql/constraints),
[DuckDB ALTER TABLE limitations](https://duckdb.org/docs/current/sql/statements/alter_table),
and [OHDSI OMOP CDM v5.4](https://ohdsi.github.io/CommonDataModel/cdm54.html).

The code is also accepted in explicit 1.2, without changing its meaning.
The new code uses the same sorted, unique, bounded array and `summary_sha256`
coverage as other limitation codes. It permits no private diagnostics or extra
fields. It never changes `foreign_key_status`, structural `status`, mismatch
counts, DQD evidence status, or checker exit codes. For example, a complete
summary may report `incompatible`, this limitation code, and
`dqd_foreign_key_evidence_status: accepted-attestation` together, with exit 3.
This means declared constraints differ while the separate point-in-time DQD
attestation satisfies the evidence contract. Neither result proves study
fitness, automatic execution readiness, or governance approval. Incomplete,
stale, invalid, or otherwise mismatched summaries retain their existing gates
and failure-output restrictions; the code cannot waive them.

## Two-operation contract

Call `get_capabilities` first and inspect its closed, bounded response before
any other connector operation. It must declare the read-only boundary, no row
access, no SQL execution, no raw-schema export, OMOP `5.4`, the supported
allowlist, a maximum snapshot age, and a maximum response size.

If capabilities are unsafe, incomplete, unavailable, denied, malformed, or
outside their declared bounds, do not call `inspect_omop_schema`. Stop at the
logical contract, retain the validation gap, and report a content-free
controlled status only.

After safe capabilities, call `inspect_omop_schema` with the fixed allowlist
`omop-v54-core-research-v1` at version `1.0.0`, OMOP CDM version `5.4`, the
public catalog SHA-256, contract version, and the accepted response-size limit.
No DSN, query, credential, database name, schema name, or local object name
may be sent. Do not add user filters or substitute a local catalog.

The fixed allowlist is:

`PERSON`, `OBSERVATION_PERIOD`, `VISIT_OCCURRENCE`, `CONDITION_OCCURRENCE`,
`DRUG_EXPOSURE`, `PROCEDURE_OCCURRENCE`, `MEASUREMENT`, `OBSERVATION`,
`DEATH`, `CDM_SOURCE`, `VOCABULARY`, `CONCEPT`, and `CONCEPT_RELATIONSHIP`.

## Validate before reporting

Enforce the declared and public byte limits before decoding or parsing. Reject
responses that fail the closed response contract, canonical JSON and
`summary_sha256` check, allowlist/reference hash match, version check,
timestamp/freshness check, or internal count and ordering checks. Never expose
raw bytes, error text, stack traces, adapter identifiers, physical names, or
the rejected response.

For a valid response, compute one status using this precedence:

1. `failed` or `partial` scan: `unavailable`.
2. Returned or supported version mismatch: `version-mismatch`.
3. Allowlist identity/version or catalog hash mismatch: `reference-mismatch`.
4. Expired observation timestamp: `stale`.
5. Standard table, column, type, nullability, primary-key, or foreign-key
   difference: `incompatible`.
6. Nonzero controlled unexpected-object counts: `compatible-with-deviations`.
7. Otherwise: `compatible`.

Any structural, size, canonicalization, redaction, or semantic failure is
`invalid-response`; a missing, denied, interrupted, or failed operation is
`unavailable`. Do not retry either condition automatically.

A valid result may report the computed status, public standard names only for
gaps, aggregate mismatch and unexpected-object counts, observed timestamp,
public catalog hash, and controlled limitation codes. It must not report any
non-standard object name or a full private response.

## Failure output boundary

For `unavailable` from a `failed` or `partial` inspection, and for
`invalid-response`, output only a controlled status plus contract-approved
limitation code(s) or validation code(s). Do not report response-derived public
gaps, counts, observed timestamp, reference hash, summary hash, or any other
response field. Only a validated non-failure status may use the approved summary
fields above.

## Claim and execution boundary

The connector is metadata-only. It can confirm only redacted structural facts
observed at one time; it cannot prove data population, vocabulary currency,
quality, study fitness, governance approval, clinical validity, or causal
validity. A metadata-only result cannot produce `executable` or `validated`.
Retain the institutional Adapter, study-parameter, and target-environment
fixture requirements in the execution-maturity gate for every outcome.

For an optional offline validation of already-exported redacted responses held
outside this repository and the installed Skill, run:

```text
python scripts/check_omop_metadata.py --capabilities <external-capabilities.json> --input <external-inspection.json> --as-of <RFC-3339-timestamp>
```

This checker does not discover, install, or contact a connector.

## Private Adapter and logging responsibilities

tbls runs only inside the private Adapter. The private owner controls tbls
configuration, DSNs, credentials, network access, raw schema exports,
authorization, redaction, retention, and detailed diagnostics. Neither this
repository nor its CI owns a DSN, connector endpoint, or private metadata.

Public logs are aggregate-only: controlled outcome codes, public identifiers,
counts, timestamps, and hashes. Do not persist, log, or commit raw responses,
private diagnostics, local names, queries, credentials, rows, samples, or
error text.
