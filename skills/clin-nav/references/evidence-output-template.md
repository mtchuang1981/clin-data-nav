# Evidence Output Template

Use exactly one template. The selected depth changes the response shape, not
authority, provenance, public/private-boundary, or execution-gate rules. Do
not list a source unless it was actually consulted.

## Common Header for Formal Deliverables

Keep this header compact and complete for evidence navigation, research design,
and implementation specification:

```text
Output depth: [one approved depth]
Decision: [direct answer or routing decision]
Confirmed facts: [facts supported by the request or reviewed sources]
Assumptions: [assumptions, or "None"]
Limitations: [known limits, or "None identified"]
Sources actually consulted: [reviewed sources, or "Current request only"]
```

## Quick Explanation

Write a short natural-language answer without a fixed header or headings. Give
the direct definition or comparison, why it matters in context, and one or two
material confusions or limits. Expand named acronyms. Cite only sources actually
consulted, and do not add an Evidence table, Data contract, or Code maturity
section unless the user asks for a deeper output.

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

If the user requests a machine-auditable record, attach the JSON ledger defined
in `evidence-ledger.md` as a separate repository-external artifact. The normal
response remains readable prose; the ledger does not replace the evidence table
or turn unreviewed sources into evidence.

Only for requested source-freshness or citation review records, attach the
optional companion defined in `evidence-audit.md` outside protected roots. It
records human review; its offline consistency result cannot prove source truth
or remove existing ledger gaps. Do not add it by default to ordinary answers.

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
Use the actionable gaps contract below with design-appropriate review criteria;
resolving a descriptive or bias gap does not require metadata or fixtures solely
because the gap is recorded. Physical execution gates apply only when seeking
an implementation maturity upgrade.

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

### Actionable gaps contract

For Implementation Validation gaps and Research Bias and validation gaps,
record each unmet condition using these five fields:

| Gap | Blocks | Next safe action | Responsible role | Completion evidence |
| --- | --- | --- | --- | --- |
| Actual unresolved condition and state | Deliverable, claim or maturity upgrade blocked | Safe authorized next step, or required new authorization | Responsible role; if the role is unknown, state pending confirmation | Versioned approval, check or review sufficient to close this gap |

Distinguish unknown, unavailable, not reviewed, known failure, pending approval,
and conflict. Do not invent ownership, metadata, or completed checks. Completion
evidence must not request private raw data or logs. After the table, state
**Work still possible**: what can safely be delivered now without closing these gaps.
For a maturity upgrade, rerun all relevant execution gates; resolving one gap
does not grant executable status or expand metadata-only authorization.
Research uses its design-appropriate review conditions, not an automatic
metadata/fixture requirement. Evidence navigation retains Conflicts and
unreviewed gaps with optional safe next steps, not this mandatory table.
Quick explanation has no added header or table requirement.
