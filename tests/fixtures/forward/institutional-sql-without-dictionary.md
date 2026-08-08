Output depth: implementation specification
Decision: Provide a logical cohort specification, not SQL against an unknown schema.
Confirmed facts: The request concerns adults with a qualifying medication exposure; no local objects or codes were supplied.
Assumptions: None about adulthood, medication qualification, physical mappings, joins, or dates.
Limitations: The versioned data dictionary, approved Adapter, live metadata verification, parameters, and fixtures are absent.
Sources actually consulted: The current synthetic request and the project institutional Adapter contract.

## Governing evidence

The requester defines only the high-level cohort. Institution-approved
definitions and current implementation artifacts must govern local mappings.

## Data contract

Logical inputs are person facts, qualifying medication events, governed
terminology mappings, and observation coverage. Define grain, stable keys,
join cardinality, adult threshold and time anchor, exposure window, event
semantics, terminology version, missingness, deduplication, precedence,
coverage, lineage, permitted outputs, and acceptance fixtures.

Mapping checklist:

- approved logical input roles and grain;
- stable linkage keys and join cardinalities;
- adult definition and time anchor;
- medication event definition and governed value set;
- observation coverage and refresh snapshot;
- missing, partial, duplicate, and conflicting-record rules; and
- expected zero, boundary, unmapped-code, and join-multiplication fixtures.

## Code maturity

`conceptual`

## Validation gaps

Obtain the versioned data dictionary, approved Adapter version, current source
ownership, exact parameters, code-system releases, physical mappings, live
metadata verification, disclosure review, and passing synthetic fixtures.

## Execution gate

Unmet. SPECIFICATION ONLY — NOT EXECUTABLE. No SQL-shaped placeholder is
supplied because it could be mistaken for an institutional implementation.
