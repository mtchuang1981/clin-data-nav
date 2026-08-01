# Evidence Output Template

Use one template only. Start every response with exactly one `Output depth: `
line. Keep confirmed facts, assumptions, limitations, and sources distinct;
cite only sources actually reviewed. The selected depth changes the response
shape, not authority, provenance, public/private-boundary, or execution-gate
requirements.

## Quick Explanation

```text
Output depth: quick explanation
Plain-language answer: [direct definition or comparison]
Why it matters: [user-context relevance]
Next step or uncertainty: [one safe follow-up or limit]
Sources: [governing authority actually reviewed]
```

## Evidence Navigation

```text
Output depth: evidence navigation
Question or claim: [scope]
Ranked sources: [source — authority label — why it applies]
Applicability: [population, setting, or implementation boundary]
Uncertainty or gap: [conflict, missing review, or limitation]
```

## Research Design

```text
Output depth: research design
PICO or estimand: [design-appropriate fields]
Data suitability: [fitness and boundaries]
Design or bias: [design route, confounding, and missing-design risks]
Analysis or diagnostics: [planned checks, not an executable analysis]
Uncertainty or handoff: [limits and optional downstream status]
```

## Research question and study-design routing

For intervention or exposure questions, record the population, intervention or
exposure, comparator, outcomes, time zero, follow-up, setting, data source,
intended use, and target estimand when causal. Distinguish RWD from RWE, report
TTE readiness only for causal comparative questions, and state optional
`build-rwe-sap` status as available, unavailable, or incompatible.

## Implementation Specification

```text
Output depth: implementation specification
Evidence: [decision and governing artifact]
Data contract: [logical roles, grain, keys, joins, coverage, types, time anchors,
code systems, terminology, missingness, precedence, lineage, and acceptance fixtures]
Code maturity: [one existing maturity label]
Validation gaps: [each unmet approval, metadata, parameter, fixture, or review]
Execution gate: [met or unmet]
SPECIFICATION ONLY — NOT EXECUTABLE
```

Include implementation or pseudocode only when the execution gate permits it.
Otherwise preserve logical placeholders and do not emit SQL-, SAS-, or R-shaped
code that could be mistaken for a physical institutional object.
