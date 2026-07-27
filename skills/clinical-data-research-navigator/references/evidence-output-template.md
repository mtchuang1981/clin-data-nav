# Evidence Output Template

Use this exact section order for clinical-data navigation and implementation
specifications.

## Decision

State the answer, governing authority, execution outcome, and the single code
maturity label. Distinguish confirmed facts from assumptions.

## Evidence table

| Claim | Source | Authority level | Publication date | Version or snapshot | Applicability | Limitations |
|---|---|---|---|---|---|---|
| `SYNTH_CLAIM` | `SYNTH_SOURCE` | `SYNTH_AUTHORITY` | `SYNTH_DATE` | `SYNTH_SNAPSHOT` | `SYNTH_SCOPE` | `SYNTH_LIMITATION` |

Include one row per material claim. Cite only sources actually reviewed.

## Data contract

Define the population, logical input roles, grain, keys, join cardinality,
coverage, types, time precision, code systems, parameter slots, output
constraints, lineage, and acceptance fixtures. Preserve placeholders for all
unverified institutional values.

## Code maturity

Choose exactly one of `conceptual`, `dictionary-specified`, `parameterized`,
`executable`, or `validated`. If the execution gate is unmet, include:

```text
SPECIFICATION ONLY — NOT EXECUTABLE
```

## Validation gaps

List every missing approval, version, mapping, parameter, live metadata check,
fixture, edge case, or result review that blocks the next maturity level.

## Sources

List stable citations or owner-approved document identifiers. Include access
dates for changing web sources and versions or snapshots where available.
