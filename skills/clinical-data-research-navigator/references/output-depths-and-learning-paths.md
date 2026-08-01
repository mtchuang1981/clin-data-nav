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
fully answers the request. Ask one concise question only when the ambiguity
would materially change the deliverable. Print exactly one `Output depth: `
line and offer a deeper depth only as an optional follow-up.

## Quick Explanation

Required shape:

```text
Output depth: quick explanation
Plain-language answer: [direct answer]
Why it matters: [context]
Next step or uncertainty: [one safe follow-up or limit]
Sources: [governing authority actually reviewed]
```

Use for a beginner definition or comparison. Keep the answer direct; do not
pre-emptively add a research plan or implementation specification.

## Evidence Navigation

Required shape:

```text
Output depth: evidence navigation
Question or claim: [scope]
Ranked sources: [source — authority label — reason for rank]
Applicability: [setting or claim boundary]
Uncertainty or gap: [conflict, limitation, or unreviewed lead]
```

Use for source discovery or authority resolution. Search results and snippets
are leads, not reviewed evidence.

## Research Design

Required shape:

```text
Output depth: research design
PICO or estimand: [design-appropriate fields]
Data suitability: [fitness and limits]
Design or bias: [route and threats]
Analysis or diagnostics: [planned checks]
Uncertainty or handoff: [limits and optional next step]
```

Use for design framing without implying a complete SAP, causal result, or
executable institutional analysis.

## Implementation Specification

Required shape:

```text
Output depth: implementation specification
Evidence: [decision and governing artifact]
Complete data contract: [grain, keys, joins, coverage, types, time anchor,
terminology, missingness, precedence, lineage, and acceptance fixtures]
Code maturity: [one existing maturity label]
Validation gaps: [each unmet condition]
Execution gate: [met or unmet]
SPECIFICATION ONLY — NOT EXECUTABLE
```

Use for implementation-ready requests. The governing artifact, complete data
contract, and validation gaps remain mandatory. Without a versioned Adapter,
current metadata, parameters, and fixtures, retain the specification-only
marker and do not produce code-shaped placeholders.

## Learning Paths

### learn the terms

**Route:** CDISC → SDTM → ADaM → protocol/SAP → implementation evidence.

**First safe prompt:** “What is SDTM, and how does it relate to ADaM?”

**Expected depth:** `quick explanation`.

**Cannot prove:** A study's local mappings or implementation readiness.

**Next:** Use evidence navigation to locate governing and implementation
sources.

### assess the evidence

**Route:** research intent → PICO-informed fields → RWD fitness → RWE claim →
TTE readiness only when causal-comparative.

**First safe prompt:** “Which governing sources should I review before framing
a comparative RWD study?”

**Expected depth:** `evidence navigation`, then `research design` when framing
the study.

**Cannot prove:** Causal validity, data fitness, or a completed analysis.

**Next:** State the study question and design constraints.

### prepare an implementation

**Route:** public evidence → logical data contract → approved Adapter → live
metadata → fixtures → executable or validated status.

**First safe prompt:** “Prepare a logical derivation specification and list the
metadata required before implementation.”

**Expected depth:** `implementation specification`.

**Cannot prove:** An executable local program without approved current
metadata and passing fixtures.

**Next:** Supply the approved Adapter, live metadata verification, parameters,
and fixtures for execution-gate review.
