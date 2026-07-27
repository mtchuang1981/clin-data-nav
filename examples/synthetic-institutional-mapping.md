# SYNTH_INSTITUTION Encounter Mapping

## Decision

Map the logical encounter role only through approved
`SYNTH_ADAPTER_001`. Do not produce executable institutional code until the
Adapter, live metadata, and fixtures agree.

## Evidence table

| Claim | Source | Authority level | Publication date | Version or snapshot | Applicability | Limitations |
|---|---|---|---|---|---|---|
| Encounter grain | `SYNTH_DICTIONARY_001` | Institutional dictionary | `SYNTH_EFFECTIVE_DATE` | `SYNTH_DICTIONARY_VERSION` | `SYNTH_ENCOUNTER` | Requires live metadata comparison |
| Allowed join | `SYNTH_ADAPTER_001` | Institutional Adapter | `SYNTH_EFFECTIVE_DATE` | `SYNTH_ADAPTER_VERSION` | Encounter-to-person mapping | Cardinality must pass fixtures |
| Output constraint | `SYNTH_GOVERNANCE_RULE_001` | Institutional governance | `SYNTH_EFFECTIVE_DATE` | `SYNTH_RULE_VERSION` | Research output | Approval scope must be confirmed |

## Data contract

- Logical object: `SYNTH_ENCOUNTER`.
- Grain: one synthetic row per approved encounter occurrence.
- Primary key: `SYNTH_ENCOUNTER_KEY`.
- Person key: `SYNTH_PERSON_KEY`.
- Allowed join: many `SYNTH_ENCOUNTER` rows to one `SYNTH_PERSON` row.
- Cardinality check: every non-null `SYNTH_PERSON_KEY` matches at most one
  `SYNTH_PERSON` row; joining must not multiply encounter rows.
- Time precision: `SYNTH_ENCOUNTER_START` and `SYNTH_ENCOUNTER_END` have
  day-level precision unless `SYNTH_ADAPTER_001` explicitly approves a more
  precise value.
- Coverage: use `SYNTH_COVERAGE_START` through `SYNTH_COVERAGE_END` for
  `SYNTH_SITE_SCOPE`; treat values outside or missing from that snapshot as
  unknown, not absent.
- Sensitivity label: `SYNTH_RESTRICTED`.
- Output constraint: allow approved aggregate results only; prohibit
  row-level identifiers and direct-identifier output.
- Lineage: trace every output to `SYNTH_ADAPTER_001`,
  `SYNTH_DICTIONARY_001`, and the transformation version.

Live metadata discrepancy check:

1. Compare approved catalog metadata with `SYNTH_ADAPTER_001`.
2. Check object presence, key uniqueness, types, nullability, date precision,
   coverage snapshot, and many-to-one cardinality.
3. Stop if any value differs.
4. Record the discrepancy and obtain owner approval for a revised Adapter.
5. Re-run all synthetic fixtures before promotion.

## Code maturity

`dictionary-specified`

```text
SPECIFICATION ONLY — NOT EXECUTABLE
```

## Validation gaps

- Supply the current approved `SYNTH_ADAPTER_001`.
- Verify the live metadata snapshot and resolve every discrepancy.
- Confirm date precision and coverage with the source owner.
- Run unique-key, orphan-key, row-multiplication, boundary-date, and prohibited
  output fixtures.

## Sources

List the approved synthetic contract identifiers:
`SYNTH_ADAPTER_001`, `SYNTH_DICTIONARY_001`, and
`SYNTH_GOVERNANCE_RULE_001`.
