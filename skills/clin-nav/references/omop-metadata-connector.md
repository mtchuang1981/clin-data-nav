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
