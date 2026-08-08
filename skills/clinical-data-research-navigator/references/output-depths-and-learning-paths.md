# Output Depths and Learning Paths

Choose one output depth before responding. The choice changes the deliverable,
not the global authority, evidence, public/private-boundary, or execution-gate
rules.

## Selection Decision Table

| If the user asks for | Choose | Do not add by default |
|---|---|---|
| A definition, comparison, or first orientation | `quick explanation` | A source-ranking table, study-design plan, or implementation details. |
| Sources, standards, implementation literature, or conflict resolution | `evidence navigation` | A full study design or implementation-ready specification. |
| Study framing, PICO, estimand, RWD/RWE fitness, bias, or diagnostics | `research design` | An executable institutional program. |
| Mappings, derivations, validation rules, metadata, or implementation readiness | `implementation specification` | Executable code until the execution gate is met. |

Honor an explicit safe choice. Otherwise choose the least sufficient depth that
fully answers the request. Ask one concise question only when ambiguity would
materially change the deliverable. Print exactly one `Output depth: ` line and
offer a deeper depth only as an optional follow-up.

## Common Header

Use this compact header before the mode-specific sections:

```text
Output depth: [one approved depth]
Decision: [direct answer or routing decision]
Confirmed facts: [supported facts]
Assumptions: [assumptions, or "None"]
Limitations: [known limits]
Sources actually consulted: [reviewed sources, or "Current request only"]
```

Never list a planned, suggested, or merely discovered source as consulted.

## Quick Explanation

Required shape:

```text
## Direct answer
[plain-language definition or comparison]

## Why it matters
[brief contextual relevance]

## Common confusions or limits
- [one common confusion or limit]
- [optional second confusion or limit]
```

Use for a beginner definition or comparison. Keep the answer direct and short;
do not add an Evidence table, Data contract, Code maturity, research plan, or
implementation mapping.

## Evidence Navigation

Required shape:

```text
## Search scope
[claim, decision, and boundaries]

## Authority-ordered route
[governing sources first; discovery leads labelled]

## Evidence table
[source, authority, provenance, applicability, and limitation]

## Conflicts and unreviewed gaps
[conflicts, limitations, and sources not yet reviewed]
```

Use for source discovery or authority resolution. Search results and snippets
are leads, not reviewed evidence. Do not add a Data contract or Code maturity
section.

## Research Design

Required shape:

```text
## Primary intent and design route
[descriptive, predictive, causal-comparative, measurement, or phenotype route]

## Design fields and time anchors
[PICO-informed or design-appropriate fields, time zero, and follow-up where relevant]

## Data suitability and claim boundary
[fitness, intended use, and RWD/RWE boundary where relevant]

## Bias and validation gaps
[bias, confounding, missing-design, and validation gaps]

## Analysis or diagnostics
[planned methods and diagnostics]

## Handoff status
[optional downstream status when applicable]
```

Use for design framing without implying a complete SAP, causal result, or
executable institutional analysis. Do not add a full Data contract, Code
maturity, or Execution gate section.

## Implementation Specification

Required shape:

```text
## Governing evidence
[decision, governing artifact, and applicability]

## Data contract
[grain, keys, joins, coverage, types, time anchor, terminology, missingness,
precedence, lineage, and acceptance fixtures]

## Code maturity
[one existing maturity label]

## Validation gaps
[each unmet condition]

## Execution gate
[met or unmet]
SPECIFICATION ONLY — NOT EXECUTABLE
```

Use for implementation-ready requests. Without a versioned Adapter, current
metadata, parameters, and fixtures, retain the specification-only marker and
do not produce code-shaped placeholders.

## Learning Paths

### learn the terms

**Route:** CDISC → SDTM → ADaM → protocol/SAP → implementation evidence.

**Prerequisites:** A clinical-trial term or decision you want to understand.

**First safe prompt:** “What is SDTM, and how does it relate to ADaM?”
**Expected depth:** `quick explanation`.

**Cannot prove:** A study's local mappings or implementation readiness.

**Next:** Use evidence navigation to locate governing and implementation
sources.

### assess the evidence

**Route:** research intent → PICO-informed fields → RWD fitness → RWE claim →
TTE readiness only when causal-comparative.

**Prerequisites:** A scoped question, intended use, and known data-source type.

**First safe prompt:** “Which governing sources should I review before framing
a comparative RWD study?”
**Expected depth:** `evidence navigation`, then `research design` when framing
the study.

**Cannot prove:** Causal validity, data fitness, or a completed analysis.

**Next:** State the study question and design constraints.

### prepare an implementation

**Route:** public evidence → logical data contract → approved Adapter → live
metadata → fixtures → executable or validated status.

**Prerequisites:** A defined decision, governing evidence, and authorized
access to any institution-owned inputs outside this public repository.

**First safe prompt:** “Prepare a logical derivation specification and list the
metadata required before implementation.”
**Expected depth:** `implementation specification`.

**Cannot prove:** An executable local program without approved current
metadata and passing fixtures.

**Next:** Supply the approved Adapter, live metadata verification, parameters,
and fixtures for execution-gate review.
