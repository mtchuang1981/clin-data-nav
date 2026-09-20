# OMOP v5.4 Read-Only Metadata Connector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an optional, fail-closed, metadata-only OMOP CDM v5.4 connector contract that lets ClinNav compare a private adapter's redacted structural summary with a pinned public OHDSI catalog without reading rows, executing SQL, or exposing institutional identifiers.

**Architecture:** Keep ClinNav public and instruction-first. Vendor one immutable public OHDSI v5.4.2 field-definition CSV outside the installable Skill, generate the packaged 13-table catalog deterministically, validate the two-operation MCP contract with standard-library Python, and expose a repository/packaged offline checker plus a callable test harness. The private adapter owns tbls, DSNs, raw schema JSON, authorization, and redaction; the public side receives only the closed summary and computes status.

**Tech Stack:** Python 3.11 standard library, JSON/JSON Schema 2020-12, YAML, pytest, Markdown, SHA-256, PowerShell, RTK, existing Skill validator/public-boundary/packaging scripts.

**Spec:** `docs/superpowers/specs/2026-09-20-omop-metadata-connector-design.md`

## Global Constraints

- Work only in branch `codex/omop-metadata-connector`; do not push, tag, publish, or change a GitHub Release in this plan.
- Do not read or modify the private `tmucrd-adapter`, connect to MCP, run tbls against a database, or inspect any institutional schema.
- Use only synthetic connector payloads in Git and CI. Never commit raw tbls output, DSNs, endpoints, local object names, database/schema/owner names, row counts, samples, or error text.
- Target `omop_cdm_version = "5.4"` and official OHDSI CommonDataModel release `v5.4.2` at commit `aa047a3c620b5c842b4370a0c965e2aa72203b1d`.
- Pin `inst/csv/OMOP_CDMv5.4_Field_Level.csv` at 130,164 bytes and SHA-256 `94006d0fac2a3911b5665ce421468fa99af23fb51a633148e5fe6045916ad950`; reject any other bytes before generation.
- Record the upstream license as Apache License 2.0 from that commit's `DESCRIPTION`; do not imply OHDSI endorsement.
- Use allowlist ID `omop-v54-core-research-v1`, allowlist version `1.0.0`, the 13 approved canonical tables, and the 178 standard columns derived from the pinned CSV.
- Do not add `jsonschema` or another runtime dependency. The JSON Schema is the portable contract; standard-library Python is the executable validator.
- Bound the public hard limit at 262,144 response bytes, 13 table results, 178 standard-column entries, 64 limitation codes, 32 mismatches per mismatch array, string length 128 unless a stricter field rule applies, and nesting depth 6.
- Canonical JSON is UTF-8 with sorted keys, separators `(',', ':')`, `ensure_ascii=False`, and one trailing LF. `summary_sha256` is the SHA-256 of the inspection object with that one key omitted.
- A metadata-only success may produce `compatible` or `compatible-with-deviations`, but it must never promote code to `executable` or `validated`.
- Preserve the existing 12-case response benchmark. Connector behavior gets a separate three-scenario synthetic contract catalog so earlier baseline/forward evidence is not reinterpreted.
- Add or update a failing test before each behavior change. Run the narrow RED test, implement the smallest change, then run GREEN.
- Use RTK when available; use `rtk proxy` or `rtk recall` if filtered output is insufficient for a security or release decision.

## Review Focus

- Fail closed on every omitted negative capability, unknown key/enum, duplicate or unsorted item, inconsistent count, stale timestamp, hash mismatch, partial scan, excessive payload, or prohibited text shape.
- Verify that no private or non-standard name can cross the adapter boundary, including through exception text, validation errors, stdout, fixtures, filenames, or logs.
- Keep upstream provenance reproducible: generated catalog bytes must be derived from the exact vendored CSV, not hand-edited.
- Keep call order and authorization explicit: no `inspect_omop_schema` call before safe capabilities, and no connector consideration for quick explanations or requests without current explicit authorization.
- Keep the installation boundary honest: normal Skill use remains instruction-only; Python is needed only for contributor checks or optional exported-response validation.
- Treat public OMOP structure as a reference, not proof of local population, vocabulary currency, data quality, study fitness, governance approval, or causal validity.

---

### Task 1: Pin and Generate the Public OMOP v5.4 Catalog

**Files:**
- Create: `vendor/ohdsi/omop-cdm-v5.4.2/OMOP_CDMv5.4_Field_Level.csv`
- Create: `vendor/ohdsi/omop-cdm-v5.4.2/SOURCE.json`
- Create: `scripts/render_omop_catalog.py`
- Create: `skills/clin-nav/references/omop-v5.4-core-catalog.json`
- Create: `tests/test_omop_catalog.py`
- Modify: `scripts/check_public_boundary.py`
- Modify: `tests/test_public_boundary.py`

**Interfaces:**

```python
# scripts/render_omop_catalog.py
def build_catalog(source: Path) -> dict[str, object]: ...
def render_catalog(source: Path) -> bytes: ...
def main(argv: list[str] | None = None) -> int: ...
```

The generator accepts only the pinned byte hash, decodes the upstream CSV as `cp1252`, validates the exact header, selects only the 13 approved tables, normalizes table/column names to uppercase, preserves allowlist table order and upstream column order, and maps upstream datatypes as follows:

```python
TYPE_FAMILIES = {
    "integer": "integer",
    "float": "decimal",
    "date": "date",
    "datetime": "datetime",
}
# case-insensitive varchar(...) -> "string"
```

The generated catalog has exact top-level keys `schema_version`, `catalog_id`, `omop_cdm_version`, `allowlist_id`, `allowlist_version`, `source`, and `tables`. Each table has exact keys `canonical_table_name` and `columns`; each column has `canonical_column_name`, `type_family`, `nullable`, `primary_key`, `foreign_key`, `foreign_table`, and `foreign_column`. Foreign targets use canonical public names or JSON `null`.

- [ ] **Step 1: Write the catalog and boundary tests first**

Add tests that require: exact source commit/path/hash/size; exact 13-table order; per-table column counts `18, 5, 17, 16, 23, 16, 23, 21, 7, 11, 5, 10, 6`; total 178 columns; only the closed type enum; canonical public FK targets; deterministic LF bytes; `--check` detects a changed output; and the public boundary permits only this exact vendored CSV path while continuing to reject any other CSV data artifact.

Run:

```text
rtk python -m pytest -q tests/test_omop_catalog.py tests/test_public_boundary.py
```

Expected: RED because the source, generator, catalog, and narrow allowlist do not exist.

- [ ] **Step 2: Acquire and verify the immutable public source**

Download only:

```text
https://raw.githubusercontent.com/OHDSI/CommonDataModel/aa047a3c620b5c842b4370a0c965e2aa72203b1d/inst/csv/OMOP_CDMv5.4_Field_Level.csv
```

Before moving it into `vendor/`, require the exact byte length and SHA-256 from Global Constraints. Create `SOURCE.json` with exact keys and values:

```json
{
  "license": "Apache License 2.0",
  "retrieved_on": "2026-09-20",
  "source_commit": "aa047a3c620b5c842b4370a0c965e2aa72203b1d",
  "source_path": "inst/csv/OMOP_CDMv5.4_Field_Level.csv",
  "source_repository": "https://github.com/OHDSI/CommonDataModel",
  "source_sha256": "94006d0fac2a3911b5665ce421468fa99af23fb51a633148e5fe6045916ad950",
  "source_size_bytes": 130164,
  "source_tag": "v5.4.2"
}
```

- [ ] **Step 3: Implement deterministic generation**

Implement `render_omop_catalog.py` with a fixed `ALLOWLIST` tuple and `EXPECTED_SOURCE_SHA256`. Reject an absent table, duplicate column, unknown datatype, malformed Yes/No flag, non-public FK target, changed source hash, or total other than 178. Write via `Path.write_bytes(render_catalog(...))`; `--check` compares bytes without rewriting.

Add only the exact path below to `DATA_ARTIFACT_ALLOWLIST`:

```python
"vendor/ohdsi/omop-cdm-v5.4.2/OMOP_CDMv5.4_Field_Level.csv"
```

- [ ] **Step 4: Generate and verify**

Run:

```text
rtk python scripts/render_omop_catalog.py
rtk python scripts/render_omop_catalog.py --check
rtk python -m pytest -q tests/test_omop_catalog.py tests/test_public_boundary.py
rtk python scripts/check_public_boundary.py
```

Expected: GREEN and deterministic generated bytes.

- [ ] **Step 5: Commit Task 1**

Review the diff, especially that the vendored file is the public upstream CSV and not a local export. Commit:

```text
git commit -m "feat: pin public OMOP v5.4 catalog"
```

---

### Task 2: Define the Closed Response Schema and Validator

**Files:**
- Create: `skills/clin-nav/references/omop-metadata-response.schema.json`
- Create: `skills/clin-nav/scripts/omop_metadata.py`
- Create: `tests/test_omop_metadata.py`
- Create: `tests/fixtures/omop_metadata/capabilities-safe.json`
- Create: `tests/fixtures/omop_metadata/inspection-compatible.json`

**Interfaces:**

```python
# skills/clin-nav/scripts/omop_metadata.py
def canonical_json_bytes(payload: Mapping[str, object], *, omit_key: str | None = None) -> bytes: ...
def validate_capabilities(payload: object) -> tuple[str, ...]: ...
def build_inspection_request(catalog: Mapping[str, object], *, max_response_bytes: int) -> dict[str, object]: ...
def validate_inspection(
    payload: object,
    *,
    catalog: Mapping[str, object],
    capabilities: Mapping[str, object],
    as_of: str,
    raw_size_bytes: int,
) -> tuple[str, ...]: ...
def classify_inspection(
    payload: Mapping[str, object],
    *,
    catalog: Mapping[str, object],
    capabilities: Mapping[str, object],
    as_of: str,
) -> dict[str, object]: ...
```

Capabilities use exactly these keys: `contract_version`, `adapter_id`, `adapter_version`, `metadata_read_only`, `row_access`, `sql_execution`, `raw_schema_export`, `supported_omop_cdm_versions`, `supported_allowlists`, `max_snapshot_age_seconds`, `tbls_inspection_available`, and `max_response_bytes`. `supported_allowlists` is a sorted unique array of `{allowlist_id, allowlist_version}` objects. The four safety booleans must be exactly `true, false, false, false`; inspection availability must be true; version/allowlist support and byte limits must cover the request.

Inspection uses the exact spec fields. A table result adds these closed mismatch objects:

```json
{
  "type_mismatches": [{
    "canonical_column_name": "MEASUREMENT_DATE",
    "expected_type_family": "date",
    "observed_type_family": "datetime"
  }],
  "nullability_mismatches": [{
    "canonical_column_name": "PERSON_ID",
    "expected_nullable": false,
    "observed_nullable": true
  }]
}
```

`primary_key_status` and `foreign_key_status` are one of `matches`, `missing`, `different`, `unknown`. `limitation_codes` is a sorted unique array from `snapshot-incomplete`, `metadata-permission-limited`, `tbls-normalization-limited`, and `constraint-metadata-limited`; there are no free-text fields.

- [ ] **Step 1: Add RED contract tests**

Use synthetic public names only. Cover: exact compatible payload; every missing capability and flipped safety boolean; missing table/column; type/nullability/PK/FK mismatch; nonzero unexpected counts; stale RFC 3339 timestamp; version/allowlist/catalog-hash mismatch; partial/failed scan; unknown keys/enums; duplicate or unsorted arrays; wrong table order; inconsistent totals; negative counts; prohibited keys such as `database_name`, `schema_name`, `comment`, `sql`, `error`, and `rows`; non-allowlisted names; long strings/arrays; excess nesting; canonical hash mismatch; and deterministic canonical bytes.

Run:

```text
rtk python -m pytest -q tests/test_omop_metadata.py
```

Expected: RED because the module/schema do not exist.

- [ ] **Step 2: Write the portable JSON Schema**

Use draft 2020-12, `$defs` for capabilities, allowlist support, inspection summary, table result, type mismatch, and nullability mismatch, and `additionalProperties: false` at every object. Add `maxLength`, `maxItems`, integer minima, exact enums, and the public name patterns. Do not claim the Schema alone enforces sort order, cross-field totals, freshness, or hashes; those remain semantic checks.

- [ ] **Step 3: Implement standard-library validation**

Return only stable codes such as `capability-unsafe`, `unsupported-version`, `response-too-large`, `unknown-key`, `noncanonical-name`, `unsorted-array`, `inconsistent-total`, `stale-snapshot`, and `summary-hash-mismatch`. Never put input values, paths, exception text, or raw content into an error code.

Classify only after zero validation errors, using this precedence:

```text
failed scan -> unavailable
partial scan -> unavailable
version mismatch -> version-mismatch
allowlist/catalog mismatch -> reference-mismatch
stale -> stale
standard table/column/type/nullability/PK/FK mismatch -> incompatible
nonzero unexpected counts -> compatible-with-deviations
otherwise -> compatible
```

Keep `invalid-response` as the caller's result whenever structural, size, canonicalization, or semantic validation returns errors.

- [ ] **Step 4: Verify Task 2**

Run:

```text
rtk python -m pytest -q tests/test_omop_metadata.py
rtk python scripts/validate_skill.py
rtk python scripts/render_omop_catalog.py --check
```

Expected: GREEN.

- [ ] **Step 5: Commit Task 2**

```text
git commit -m "feat: validate redacted OMOP metadata"
```

---

### Task 3: Add the Bounded Connector Harness and Offline Checker

**Files:**
- Create: `skills/clin-nav/scripts/omop_metadata_connector.py`
- Create: `skills/clin-nav/scripts/check_omop_metadata.py`
- Create: `scripts/check_omop_metadata.py`
- Create: `tests/test_omop_metadata_connector.py`
- Modify: `tests/test_omop_metadata.py`

**Interfaces:**

```python
# skills/clin-nav/scripts/omop_metadata_connector.py
BytesOperation = Callable[..., bytes]

def assess_connector(
    get_capabilities: BytesOperation,
    inspect_omop_schema: BytesOperation,
    *,
    catalog: Mapping[str, object],
    as_of: str,
    hard_max_bytes: int = 262_144,
) -> dict[str, object]: ...
```

The callables are an MCP-independent test seam: `get_capabilities()` returns raw UTF-8 JSON bytes and `inspect_omop_schema(request)` returns raw bytes. The harness checks byte length before decoding/parsing, validates capabilities, builds the fixed request, then and only then invokes inspection. It returns a content-free summary and never logs or persists raw bytes.

```text
python scripts/check_omop_metadata.py \
  --capabilities <external-json> \
  --input <external-json> \
  --as-of 2026-09-20T12:00:00+08:00
```

Both input files must be outside the repository or installed Skill. The packaged catalog is the default and cannot be overridden by a private/local catalog flag.

- [ ] **Step 1: Add RED call-order, byte-limit, and CLI tests**

Require: safe capabilities cause exactly two calls in order; unsafe/incomplete/oversized/malformed capabilities cause no inspection call; oversized inspection is rejected before parsing; adapter exceptions become `unavailable` without exposing exception text; request keys and catalog hash are exact; valid compatible/deviation/incompatible/stale cases produce deterministic safe summaries; both root and packaged CLIs match; internal input paths are rejected; and marker strings from malformed input never reach stdout/stderr.

Define exits:

```text
0 = compatible or compatible-with-deviations
3 = incompatible, stale, version-mismatch, reference-mismatch, or unavailable
2 = invalid-response, unsafe capabilities, malformed JSON, internal path, or size failure
```

Run:

```text
rtk python -m pytest -q tests/test_omop_metadata_connector.py tests/test_omop_metadata.py
```

Expected: RED.

- [ ] **Step 2: Implement the harness without MCP or tbls dependencies**

Parse bytes with strict UTF-8 and `json.loads`; use the validator from Task 2. Build a safe result with only `contract_version`, `status`, `observed_at`, `omop_cdm_version`, `allowlist_id`, `allowlist_version`, `reference_sha256`, aggregate mismatch/unexpected counts, `limitation_codes`, `summary_sha256`, and `validation_codes`. Include public standard names only in the in-memory detailed assessment, not default CLI stdout.

- [ ] **Step 3: Implement the packaged CLI and thin root wrapper**

Follow the existing evidence-ledger checker pattern. Use a fixed error line `OMOP metadata validation failed\n` only when JSON cannot be safely summarized. Never echo a path, input value, traceback, adapter identifier, or raw response. The root wrapper imports the packaged `main` and contains no business logic.

- [ ] **Step 4: Verify and commit Task 3**

Run:

```text
rtk python -m pytest -q tests/test_omop_metadata_connector.py tests/test_omop_metadata.py
rtk python scripts/check_public_boundary.py
rtk git diff --check
git commit -m "feat: add OMOP metadata contract checker"
```

---

### Task 4: Route ClinNav Through the Optional Connector Safely

**Files:**
- Create: `skills/clin-nav/references/omop-metadata-connector.md`
- Modify: `skills/clin-nav/SKILL.md`
- Modify: `skills/clin-nav/references/institutional-adapter-contract.md`
- Modify: `tests/test_skill_contract.py`
- Review without changing unless a test proves it necessary: `skills/clin-nav/agents/openai.yaml`

**Behavior contract:**

```text
quick explanation -> never consider connector
no explicit authorization in current request -> do not call connector
authorized local schema/mapping/metadata/readiness request -> get_capabilities first
unsafe/unavailable capabilities -> stop at logical contract and report gap
safe capabilities -> inspect fixed allowlist only
valid response -> report computed status, public-standard gaps, counts, timestamp, hash, limitations
all outcomes -> retain existing execution-maturity gate
```

- [ ] **Step 1: Add RED Skill contract tests**

Require `SKILL.md` and the new reference to state: current-request authorization; two-operation call order; no automatic discovery/install/retry; fixed request with no DSN/query/local names; content-free failure handling; quick-mode exclusion; public-standard-name-only reporting; and metadata-only cannot produce `executable`/`validated`. Assert `agents/openai.yaml` gains no private MCP dependency and keeps the existing implicit-invocation policy.

Run:

```text
rtk python -m pytest -q tests/test_skill_contract.py
```

Expected: RED.

- [ ] **Step 2: Write the connector reference**

Document purpose, authorization gate, operation contracts, exact allowlist, status precedence, response/size/hash checks, claim boundary, optional checker command, private adapter responsibilities, and aggregate-only logging. State that tbls runs only in the private adapter and that neither this repository nor its CI owns a DSN.

- [ ] **Step 3: Make the smallest Skill routing changes**

Add the optional route adjacent to the existing institutional adapter route; do not restructure unrelated evidence, RWE/TTE, SAS, or output-depth sections. Link the new reference in the resource-reading section. Update the institutional adapter contract so metadata verification may consume a valid redacted connector result but still requires study parameters and fixture checks for maturity promotion.

- [ ] **Step 4: Verify and commit Task 4**

Run:

```text
rtk python -m pytest -q tests/test_skill_contract.py tests/test_acceptance.py
rtk python scripts/validate_skill.py
git commit -m "feat: route optional OMOP metadata checks"
```

---

### Task 5: Add a Separate Synthetic Connector Scenario Catalog

**Files:**
- Create: `evals/omop-metadata-connector/cases.yaml`
- Create: `evals/omop-metadata-connector/README.md`
- Create: `tests/test_omop_metadata_eval_contract.py`
- Create: `tests/fixtures/omop_metadata/inspection-incompatible.json`
- Create: `tests/fixtures/omop_metadata/inspection-deviations.json`

**Scenario catalog:**

```yaml
schema_version: "1"
cases:
  - id: unauthorized-or-absent
    expected_calls: []
    expected_status: unavailable
    execution_maturity_ceiling: specification only
  - id: authorized-compatible-with-deviations
    expected_calls: [get_capabilities, inspect_omop_schema]
    expected_status: compatible-with-deviations
    execution_maturity_ceiling: implementation-ready
  - id: authorized-incompatible
    expected_calls: [get_capabilities, inspect_omop_schema]
    expected_status: incompatible
    execution_maturity_ceiling: specification only
```

`implementation-ready` is only a ceiling for this connector evidence and is not an automatic final maturity label.

- [ ] **Step 1: Add RED scenario-catalog tests**

Require exactly three unique cases and exact keys. Drive each authorized case through the Task 3 synthetic mock, and test the unauthorized case without invoking either callable. Assert no response contains `SELECT`, a synthetic private marker, non-standard names, or `executable`/`validated`. Assert the existing `evals/cases.yaml` remains exactly 12 cases with unchanged IDs.

Run:

```text
rtk python -m pytest -q tests/test_omop_metadata_eval_contract.py tests/test_eval_contract.py
```

Expected: RED.

- [ ] **Step 2: Add only synthetic fixtures and document interpretation**

Build the incompatible fixture solely from public allowlisted names. Build the deviations fixture with positive counts and no names. Explain that these are deterministic repository behavior contracts, not live MCP, database, clinical, or human-effectiveness evidence.

- [ ] **Step 3: Verify and commit Task 5**

Run:

```text
rtk python -m pytest -q tests/test_omop_metadata_eval_contract.py tests/test_eval_contract.py
rtk python scripts/check_public_boundary.py
git commit -m "test: add synthetic OMOP connector scenarios"
```

---

### Task 6: Document Setup, Ownership, and Claim Boundaries

**Files:**
- Modify: `README.md`
- Modify: `README.zh-TW.md`
- Modify: `docs/installation.md`
- Modify: `docs/installation.zh-TW.md`
- Modify: `docs/architecture.md`
- Create: `tests/test_omop_metadata_docs.py`

- [ ] **Step 1: Add RED documentation contract tests**

Require English/Traditional Chinese parity for: optional feature; public Skill versus private adapter ownership; explicit authorization; v5.4/v5.4.2 provenance; 13-table allowlist; tbls private-side role; no row/SQL access; offline checker example; external input files; and metadata-only claim boundary. Assert normal `npx skills add mtchuang1981/clin-data-nav` use still says Python is not required.

Run:

```text
rtk python -m pytest -q tests/test_omop_metadata_docs.py
```

Expected: RED.

- [ ] **Step 2: Update architecture and installation documentation**

Show this ownership flow in prose or a compact diagram:

```text
ClinNav request + explicit authorization
  -> private tmucrd-adapter get_capabilities
  -> private tbls schema inspection/redaction
  -> closed metadata summary
  -> public ClinNav validator/status
  -> logical mapping gaps; never automatic execution
```

Document adapter-owner conformance steps without an endpoint, server command, DSN, or private config example. The only public example files are synthetic. Explain that the packaged checker validates exported responses offline and is not required for ordinary Skill invocation.

- [ ] **Step 3: Verify and commit Task 6**

Run:

```text
rtk python -m pytest -q tests/test_omop_metadata_docs.py tests/test_skill_contract.py
rtk python scripts/validate_skill.py
git commit -m "docs: explain OMOP metadata connector"
```

---

### Task 7: Lock Packaging and the Public Boundary

**Files:**
- Modify: `tests/test_packaging.py`
- Modify: `tests/test_public_boundary.py`
- Modify if the test requires a narrow new rule: `scripts/check_public_boundary.py`

- [ ] **Step 1: Add RED package and leak-regression tests**

Require the ZIP to contain:

```text
references/omop-metadata-connector.md
references/omop-v5.4-core-catalog.json
references/omop-metadata-response.schema.json
scripts/omop_metadata.py
scripts/omop_metadata_connector.py
scripts/check_omop_metadata.py
```

Require it not to contain `vendor/`, test fixtures, `.tbls.yml`, DSNs, raw `schema.json`, endpoints, or the private adapter name as a dependency. Add synthetic temporary files showing the boundary scanner rejects `.tbls.yml`, `schema.json` under a connector/run directory, DSN-shaped secrets, and non-allowlisted CSV exports, while accepting the exact public upstream CSV.

Run:

```text
rtk python -m pytest -q tests/test_packaging.py tests/test_public_boundary.py
```

Expected: RED until package assertions and any narrowly needed scanner rules are complete.

- [ ] **Step 2: Implement only narrowly evidenced boundary rules**

Do not ban generic words such as `schema` or `metadata`. Match risky artifact paths/config keys precisely so public contract docs and synthetic fixtures remain legal. Confirm findings report path/rule only and never file content.

- [ ] **Step 3: Verify and commit Task 7**

Run:

```text
rtk python -m pytest -q tests/test_packaging.py tests/test_public_boundary.py
rtk python scripts/check_public_boundary.py
rtk python scripts/package_skill.py --check-reproducible
git commit -m "test: enforce OMOP connector public boundary"
```

---

### Task 8: Run Complete Verification and Prepare the Local Integration Commit

**Files:**
- Review all feature changes; create no release/version files.

- [ ] **Step 1: Run focused deterministic checks**

```text
rtk python scripts/render_omop_catalog.py --check
rtk python -m pytest -q tests/test_omop_catalog.py tests/test_omop_metadata.py tests/test_omop_metadata_connector.py tests/test_omop_metadata_eval_contract.py tests/test_omop_metadata_docs.py
```

- [ ] **Step 2: Run every repository gate**

```text
rtk python -m pytest -q
rtk python scripts/validate_skill.py
rtk python scripts/check_public_boundary.py
rtk python scripts/package_skill.py --check-reproducible
rtk git diff --check
```

Expected: zero failures and exit `0` from every command. If RTK output is incomplete or inconsistent with an exit code, recover full output with `rtk recall` or rerun that command through `rtk proxy` before deciding.

- [ ] **Step 3: Verify reproducible package contents and no boundary drift**

Build twice in separate temporary output directories, compare ZIP bytes and manifest bytes, and inspect the archive file list. Require identical hashes, only expected Skill files, no vendored CSV, no raw connector responses, and no private metadata. Confirm `git diff --numstat` shows no generated package binary tracked in the repository.

- [ ] **Step 4: Review the complete diff against the approved spec**

Run:

```text
rtk git status --short --branch
rtk git diff --stat
rtk git diff --check
rtk git log --oneline --decorate -10
```

Review each changed file for these failure modes: connector auto-invocation, free text in response contracts, private-name disclosure, hand-edited catalog data, metadata-only maturity promotion, a new runtime dependency, or alteration of the existing 12-case benchmark.

- [ ] **Step 5: Resolve only integration defects, then rerun all gates**

For any defect, add a failing regression test before the fix. Do not broaden scope into a live private conformance run, SQL generation, version bump, release notes, or publishing.

- [ ] **Step 6: Finish locally**

If Task commits already leave a clean worktree, do not create an empty squash commit. Record final HEAD and test outputs. The branch is ready for review/merge only; pushing, merging to `main`, accessing the private MCP, running private conformance, tagging, and releasing each require a separate explicit instruction.

## Completion Gate

Implementation is complete only when the immutable OHDSI source provenance is verified; the 13-table/178-column catalog regenerates byte-for-byte; both response types are closed and bounded; the callable harness enforces safe call order and pre-parse limits; the CLI emits no private content; the optional Skill route requires current explicit authorization; metadata-only results cannot become executable or validated; the separate three-case synthetic scenario catalog passes without modifying the existing 12-case benchmark; bilingual documentation preserves the instruction-only install boundary; the Skill package contains the contract/catalog/checker but not vendor/test/private artifacts; all required gates pass; and the feature branch is clean.

The final report must distinguish verified public contract behavior from an unperformed private adapter conformance run. It may claim deterministic validation against synthetic summaries and the pinned public OMOP v5.4.2 structure only. It must not claim local deployment compatibility, populated data, current vocabularies, data quality, study fitness, governance approval, clinical validity, causal validity, or patient benefit.
