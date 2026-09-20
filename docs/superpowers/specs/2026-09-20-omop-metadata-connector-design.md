# OMOP v5.4 Read-Only Metadata Connector Design

Status: approved design

Date: 2026-09-20

## Purpose

Add an optional, contract-first bridge between the public `clin-nav` Skill and
the private `tmucrd-adapter` MCP server. The bridge lets ClinNav test and
improve schema routing against current OMOP CDM v5.4 structure without reading
patient data, executing SQL, exposing credentials, or copying private schema
material into this public repository.

The connector is a testing and metadata-verification aid. A successful
connection does not establish data fitness, cohort availability, scientific
validity, or permission to execute an analysis.

## Approved Decisions

- Use a contract-based MCP bridge rather than raw tbls pass-through.
- Limit the private adapter to read-only schema metadata.
- Start with an explicit OMOP table allowlist.
- Target OMOP CDM v5.4 and pin the public catalog to the official v5.4.2
  release provenance.
- Keep raw `tbls` JSON, DSNs, credentials, physical schema identifiers, and
  private metadata outside the public repository.
- Return canonical public OMOP object names, but report non-standard objects
  only by controlled difference type and count.
- Use the private connector only after explicit authorization in the current
  request. Do not install, discover, or call it merely because ClinNav was
  invoked.
- Keep connector success separate from the existing execution-maturity gate.

## Goals

1. Verify the presence and structural compatibility of a small, public OMOP
   v5.4 research subset at an observed time.
2. Give ClinNav enough governed metadata to improve logical-to-OMOP mapping
   checklists and validation-gap reporting.
3. Detect missing standard tables or columns and normalized type,
   nullability, primary-key, and foreign-key differences.
4. Make stale, mismatched, malformed, excessive, or over-disclosing metadata
   fail closed.
5. Test all public behavior with synthetic fixtures and a mock MCP boundary.

## Non-Goals

- Query execution, SQL generation against TMUCRD, cohort counts, data samples,
  value profiling, or row access.
- Reading or modifying the private `tmucrd-adapter` source repository in this
  workstream.
- Publishing actual database, schema, owner, view, local extension, index,
  constraint, or trigger names.
- Returning comments, default expressions, error stacks, source values,
  coverage, refresh facts, or vocabulary contents from the private system.
- Inferring the OMOP version from table appearance. The adapter must declare
  the configured version.
- Promoting metadata-only results to `executable` or `validated`.
- Adding a hard private-MCP dependency to `agents/openai.yaml` or changing
  implicit Skill invocation policy.

## Public and Private Boundary

The public repository may contain:

- an official-source-derived OMOP v5.4.2 catalog for the approved subset;
- the table allowlist and public standard field names;
- MCP request and response contracts;
- response JSON Schema, canonicalization, and validation logic;
- synthetic fixtures, mock responses, Evals, and aggregate-only records;
- installation and governed-setup instructions without real endpoints.

The private environment owns:

- the `tmucrd-adapter` service and its authorization;
- DSNs, credentials, network routes, and actual database/schema identifiers;
- the `tbls` configuration and raw `schema.json`;
- actual non-standard object names and vendor-specific definitions;
- private logs, metadata snapshots, and any conformance output containing
  institutional details.

Neither the public Skill nor its CI connects to the private MCP or a database.

## Public OMOP v5.4 Catalog

The initial allowlist ID is `omop-v54-core-research-v1` and contains these
canonical public tables:

1. `PERSON`
2. `OBSERVATION_PERIOD`
3. `VISIT_OCCURRENCE`
4. `CONDITION_OCCURRENCE`
5. `DRUG_EXPOSURE`
6. `PROCEDURE_OCCURRENCE`
7. `MEASUREMENT`
8. `OBSERVATION`
9. `DEATH`
10. `CDM_SOURCE`
11. `VOCABULARY`
12. `CONCEPT`
13. `CONCEPT_RELATIONSHIP`

The catalog is generated from the official OHDSI CommonDataModel v5.4.2
release, not copied from a local database. Generation records the upstream
release tag, source file identity, retrieval date, and SHA-256. A generated
catalog change requires a reviewed upstream-provenance change; hand-edited
standard fields are rejected by reproducibility tests.

Public sources:

- <https://github.com/OHDSI/CommonDataModel/releases/tag/v5.4.2>
- <https://ohdsi.github.io/CommonDataModel/cdm54.html>

## Connector Operations

The logical connector has exactly two read-only operations. MCP server/tool
prefixes are environment-specific; the contract names are stable.

### `get_capabilities`

The response contains only:

- `contract_version`;
- opaque `adapter_id` and semantic `adapter_version`;
- `metadata_read_only: true`;
- `row_access: false`;
- `sql_execution: false`;
- `raw_schema_export: false`;
- supported OMOP CDM versions;
- supported allowlist IDs and versions;
- maximum snapshot age;
- whether tbls-backed inspection is available;
- maximum response bytes.

ClinNav rejects the connector when any negative capability is omitted, has an
unexpected type, or conflicts with the required read-only boundary.

### `inspect_omop_schema`

The request contains:

- `contract_version`;
- `omop_cdm_version: "5.4"`;
- `allowlist_id: "omop-v54-core-research-v1"`;
- `allowlist_version`;
- the public catalog SHA-256;
- the caller's maximum accepted response size.

It never contains a DSN, credential, database name, schema name, query, local
object name, or user-supplied filter.

The adapter runs tbls inside its governed environment, retains the raw schema
there, applies the allowlist and redaction rules, and returns only the closed
summary contract.

## Summary Contract

The top-level response contains:

- `contract_version`;
- `adapter_version`;
- `omop_cdm_version`;
- `allowlist_id` and `allowlist_version`;
- the echoed public `reference_sha256`;
- RFC 3339 `observed_at`;
- semantic `tbls_version`;
- `scan_status`: `complete`, `partial`, or `failed`;
- canonical `summary_sha256`;
- `unexpected_table_count` and `unexpected_column_count`;
- controlled `limitation_codes`;
- exactly one table result for each allowlisted table.

Each table result contains only:

- `canonical_table_name`;
- `presence`: `present`, `missing`, or `unknown`;
- `standard_column_total`;
- sorted `present_standard_columns` and `missing_standard_columns`;
- type mismatches using canonical standard column names and normalized type
  families;
- nullability mismatches using canonical standard column names;
- `primary_key_status` and `foreign_key_status`;
- `unexpected_column_count`.

Normalized type families are a closed enum such as `integer`, `string`,
`date`, `datetime`, `decimal`, `boolean`, and `binary`. Vendor-specific type
text is not returned.

The response has no free-text fields. Unknown keys, unknown enums, duplicates,
unsorted canonical lists, non-allowlisted names, invalid timestamps, negative
counts, or inconsistent totals make the complete response invalid.

## Redaction and Exfiltration Controls

- Canonical allowlisted OMOP names may appear because they are public.
- Non-standard table, column, view, index, constraint, and trigger names never
  appear; only controlled counts do.
- Local aliases, database/schema/owner names, comments, defaults, SQL, error
  text, stack traces, row counts, samples, min/max values, coverage dates, and
  refresh timestamps are prohibited.
- Response table count, standard-column count, string length, array length,
  nesting depth, and total bytes are bounded before semantic evaluation.
- The JSON Schema sets `additionalProperties: false` at every object level.
- Canonical JSON uses UTF-8, sorted keys, stable allowlist order, no insignificant
  whitespace, and a trailing newline before SHA-256 calculation.
- Public logs record only outcome codes, public identifiers, counts, and hashes.
  They never record a raw private response.
- Public CI uses synthetic fixtures only and has no MCP endpoint or credentials.

## ClinNav Validation and Status

The adapter reports inspection facts, not compatibility. ClinNav computes one
status after structural validation:

| Status | Meaning |
|---|---|
| `compatible` | Complete, current, version/hash matched, with no standard-structure mismatch |
| `compatible-with-deviations` | Complete and current, but permitted non-standard counts are nonzero |
| `incompatible` | Required standard objects, normalized types, nullability, PK, or FK differ |
| `stale` | `observed_at` exceeds the capability-declared maximum age |
| `version-mismatch` | Requested, declared, or returned OMOP version differs |
| `reference-mismatch` | Allowlist identity/version or public catalog hash differs |
| `invalid-response` | Closed-schema, size, canonicalization, or internal-consistency validation fails |
| `unavailable` | MCP or required operation is absent, denied, interrupted, or reports failure |

`partial` never becomes compatible. A stale, mismatched, invalid, or unavailable
response is not relaxed into a best-effort comparison.

## Skill Routing and Output Behavior

ClinNav considers the connector only for a local schema, mapping, metadata,
or implementation-readiness request. Before a live private call, the current
request must explicitly authorize read-only metadata access. Merely invoking
`$clin-nav`, naming TMUCRD, or having the MCP installed is insufficient.

When authorized and valid, ClinNav may use the result to:

- distinguish confirmed present standard inputs from validation gaps;
- prepare a logical-to-OMOP mapping checklist;
- identify public standard fields that require local remediation;
- refine tests and synthetic fixtures;
- record the observed timestamp, connector contract, and public catalog hash.

It must not expose the full private response in the answer. It reports the
computed status, approved aggregate counts, relevant public standard names,
limitations, and the execution gate.

Metadata-only success can satisfy part of live metadata verification. It does
not supply study parameters, concept sets, code mappings, data fitness,
governance approval, or passing fixtures. The result therefore cannot by
itself be `executable` or `validated`; unresolved requirements remain explicit.

## Failure Handling

1. Validate capabilities before requesting inspection.
2. Reject unsupported version, allowlist, or response limits before the call.
3. Enforce the byte limit before JSON parsing.
4. Apply structural, redaction, canonicalization, freshness, and semantic
   checks in that order.
5. On failure, emit only a controlled status and validation-gap codes.
6. Do not retry authorization failures, malformed responses, or version/hash
   mismatches automatically.
7. Do not write the response to the repository. Optional private diagnostics
   remain under the adapter owner's governed retention policy.

## Public Repository Changes

Implementation is expected to add or update:

- `skills/clin-nav/references/omop-metadata-connector.md`;
- a versioned public v5.4 catalog and response JSON Schema;
- a packaged validator/canonicalizer under `skills/clin-nav/scripts/`;
- repository-side test entry points without duplicating business logic;
- `SKILL.md`, `agents/openai.yaml` review, Evals, synthetic fixtures, and
  bilingual setup documentation;
- architecture and public-boundary checks covering the optional connector.

The exact file decomposition belongs in the implementation plan. Existing
evidence, RWE/TTE, and output-depth behavior remains unchanged unless a test
demonstrates that connector routing requires a narrow correction.

## Test Strategy

Follow RED-GREEN-REFACTOR. No private MCP, schema, or live database is used in
tests.

### Contract and validator tests

- exact synthetic compatible response;
- missing table and missing standard column;
- normalized type, nullability, PK, and FK mismatch;
- permitted unexpected-object counts without names;
- stale timestamp;
- OMOP version, allowlist, and catalog-hash mismatch;
- partial and failed scans;
- unknown keys/enums, duplicate/unsorted items, inconsistent counts;
- prohibited local names, free text, SQL-shaped content, and error stacks;
- excessive payload, arrays, strings, and nesting;
- deterministic canonicalization and SHA-256.

### Routing and response tests

- MCP absent or not authorized: keep the existing logical contract path;
- capabilities incomplete or unsafe: do not call inspection;
- compatible metadata: improve the mapping checklist without SQL;
- incompatible metadata: list public-standard gaps and stop promotion;
- private or non-standard names never appear in output;
- metadata-only success never yields `executable` or `validated`;
- quick explanations do not trigger the connector.

### Integration boundary

A synthetic mock implements both logical operations. CI verifies request
shape, call ordering, bounded response handling, status calculation, and
output redaction. An optional private conformance run may be documented for
the adapter owner, but its raw response and logs stay outside Git. Only a
reviewed aggregate of public identifiers, counts, statuses, and hashes may be
recorded publicly.

## Acceptance Criteria

The feature is acceptable when:

1. every public test uses synthetic data;
2. the public catalog is reproducibly tied to OHDSI v5.4.2 provenance;
3. valid compatible and incompatible synthetic responses are classified
   deterministically;
4. malformed or over-disclosing responses fail closed;
5. non-standard names cannot enter the public output path;
6. absence of the private MCP preserves existing ClinNav behavior;
7. metadata-only results never cross the execution gate;
8. the packaged Skill includes the contract, catalog, validator, and relevant
   routing instructions;
9. repository validation, public-boundary scan, deterministic packaging, and
   the full test suite pass;
10. no private adapter code, schema, endpoint, credential, or raw response is
    read or committed.

## Claim Boundary

This work may support only the statement that, under the declared connector
contract and at the recorded observation time, a redacted metadata summary was
structurally compared with the pinned public OMOP v5.4 catalog.

It does not establish that tables are populated, values are correct, mappings
are clinically valid, vocabularies are current, study variables are available,
data are fit for a particular analysis, governance approval exists, or an
analysis is executable, validated, causal, clinically effective, or beneficial
to patients.
