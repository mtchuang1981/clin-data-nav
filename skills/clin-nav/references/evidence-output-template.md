# Evidence Output Template

Use exactly one template. The selected depth changes the response shape, not
authority, provenance, public/private-boundary, or execution-gate rules. Do
not list a source unless it was actually consulted.

## Common Header

Keep this header compact and complete at every depth:

```text
Output depth: [one approved depth]
Decision: [direct answer or routing decision]
Confirmed facts: [facts supported by the request or reviewed sources]
Assumptions: [assumptions, or "None"]
Limitations: [known limits, or "None identified"]
Sources actually consulted: [reviewed sources, or "Current request only"]
```

## Quick Explanation

```text
## Direct answer
[plain-language definition or comparison]

## Why it matters
[brief relevance to the user's context]

## Common confusions or limits
- [one common confusion or limit]
- [optional second confusion or limit]
```

Keep this response short. Do not add an Evidence table, Data contract, or Code
maturity section unless the user asks for a deeper output.

## Evidence Navigation

```text
## Search scope
[decision, claim, and boundaries]

## Authority-ordered route
[governing sources first; discovery leads clearly labelled]

## Evidence table
[source, authority level, provenance, applicability, and limitation]

## Conflicts and unreviewed gaps
[conflicts, limits, and sources not yet reviewed]
```

Search results and snippets are leads, not reviewed evidence. Do not add a
Data contract or Code maturity section.

## Research Design

```text
## Primary intent and design route
[descriptive, predictive, causal-comparative, measurement, or phenotype route]

## Design fields and time anchors
[PICO-informed or design-appropriate fields, time zero, follow-up, and outcome where relevant]

## Data suitability and claim boundary
[data source, intended use, RWD fitness, and RWE boundary where relevant]

## Bias and validation gaps
[bias, confounding, missing-design, and validation gaps]

## Analysis or diagnostics
[planned methods and diagnostics, not an executable analysis]

## Handoff status
[optional downstream status when applicable]
```

Report TTE readiness only for causal-comparative questions. This depth may
state logical data needs but must not add a full Data contract, Code maturity,
or Execution gate section or imply a complete SAP, causal result, or program.

### Research question and study-design routing

For intervention or exposure questions, record population, intervention or
exposure, comparator, outcomes, time zero, follow-up, setting, data source,
intended use, and target estimand when causal. Distinguish RWD from RWE and
state optional `build-rwe-sap` status as available, unavailable, or incompatible
only when relevant.

## Implementation Specification

```text
## Governing evidence
[decision, governing artifact, and applicability]

## Data contract
[logical roles, grain, keys, joins, coverage, types, time anchors, code systems,
terminology, missingness, precedence, lineage, and acceptance fixtures]

## Code maturity
[exactly one existing maturity label]

## Validation gaps
[each unmet approval, metadata, parameter, fixture, or review]

## Execution gate
[met or unmet; include implementation only when permitted]
SPECIFICATION ONLY — NOT EXECUTABLE
```

Without the required Adapter, current metadata, parameters, and fixtures,
retain the specification-only marker and do not emit SQL-, SAS-, R-, or
Python-shaped placeholders that could be mistaken for physical objects.
