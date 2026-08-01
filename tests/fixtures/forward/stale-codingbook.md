## Decision

Output depth: implementation specification

No. A synthetic codingbook dated 2021 documents only a historical, synthetic specification; it does not prove the current institutional data model or live schema. Implementation must wait for current, governed institutional evidence.

## Evidence table

| Claim | Source | Authority level | Publication date | Version or snapshot | Applicability | Limitations |
|---|---|---|---|---|---|---|
| The codingbook reflects a historical synthetic specification | Researcher-provided description | Institutional-document context | 2021 | 2021 codingbook | May inform initial logical requirements | Contents, approval status, local applicability, and currency are unverified |
| Historical documentation cannot verify the current environment | Institutional Adapter Contract | Institutional governance | Current skill reference | Current | Governs local-schema readiness | Requires institution-owned evidence and target-environment checks |

## Data contract

Before implementation, obtain:

- An owner-approved, versioned institutional Adapter and current approved data dictionary, including effective date and source owner.
- Domain mappings defining row grain, physical objects and fields, types, nullability, stable keys, deduplication rules, join cardinality, and coverage.
- Current code-system/value-set versions, local mappings, and handling of unmapped or obsolete codes.
- Time precision, timezone, interval, partial-date, censoring, and imputation semantics.
- Study-specific population, phenotype, windows, parameters, and output rules.
- Lineage, privacy classifications, disclosure controls, permitted outputs, and governance approval.
- Live target-environment metadata checks for object presence, types, nullability, key uniqueness, join multiplication or loss, date coverage, code compatibility, and refresh timestamp.
- Approved synthetic or de-identified fixtures covering inclusions, exclusions, duplicates, missing keys, malformed and boundary timestamps, unmapped codes, empty inputs, expected aggregates, and prohibited outputs.

Any difference between live metadata and the Adapter must be recorded, resolved by the source owner, and followed by renewed metadata and fixture testing.

## Code maturity

`conceptual`

```text
SPECIFICATION ONLY — NOT EXECUTABLE
```

## Validation gaps

- No approved current Adapter or dictionary version.
- No evidence that the 2021 synthetic codingbook maps to the institution.
- No live metadata comparison.
- No completed live metadata verification.
- No confirmed grain, keys, cardinalities, coverage, or refresh state.
- No verified terminology versions or local mappings.
- No approved fixtures or passing acceptance checks.
- No documented discrepancy review, governance approval, or result validation.

## Sources

- Researcher-provided description of the synthetic 2021 codingbook.
- `clinical-data-research-navigator/references/institutional-adapter-contract.md`.
