# Feasibility Consultation Review

Use for an initial coordinator question such as "how should we handle this
consultation?", and for candidate-set review before a formal specification.
Keep the global authority, authorization, minimization and execution gates.
This reference does not authorize institutional access or implement an Adapter.

## Coordinator brief

For orientation without a requested formal contract, use quick explanation.
Deliver these four content parts in the user's language, using short prose or
a small decision list rather than the formal implementation headings:

1. **Handling decision:** what can move forward now, the immediate deliverable,
   and what the current evidence cannot establish.
2. **Material findings:** distinguish supplied/reviewed observations, inference
   and unknowns. Identify consulted sources naturally; distinguish historical
   tool results from a fresh check. Avoid reprinting full code lists or usage.
3. **Decisions to confirm:** group investigator choices into one concise batch.
   Each item names the decision, a proposed option where defensible, its effect,
   the responsible role (unconfirmed if unknown), and evidence needed to settle
   it. Recommendations remain proposals until confirmed. Separate these from
   data-owner checks and tool-verifiable questions; do not ask investigators to
   guess physical schema. Continue independent authorized work while waiting.
4. **Next deliverable:** name the review sheet, definition decisions or bounded
   specification that follows, the blocking dependency and a concrete action.
   Do not end with only "insufficient information" or a general offer to help.

This brief is not a fifth output depth or a replacement for a requested formal
specification. Explicit mapping, derivation, validation and execution-readiness
requests use the existing formal implementation shape. A count specification
request retains the default structured specification in rwe-question-routing.md.
When discussing code maturity, state one supported existing label and retain
SPECIFICATION ONLY — NOT EXECUTABLE while execution gates remain unmet.

## Clinical selection is separate from dictionary matching

For a candidate set, distinguish three decisions:

- **Dictionary validity:** identity, source/version, match route and whether a
  term is supported by the governed dictionary.
- **Research relevance:** whether the actual meaning fits the intended disease,
  organ involvement, modality, anatomy and study-specific boundaries.
- **Approval:** whether the clinical selection and institutional mapping have
  been reviewed by their responsible roles, with retained version and rationale.

Apply semantic review to candidates with empty as well as nonempty warnings.
A successful tool response or empty reasons does not establish relevance or
approval. Nonempty reasons require resolution, not automatic exclusion. A broad
disease family can include terms without the intended organ involvement.
Mixed modality/anatomy candidates require classification before inclusion.
When clinical scope is ambiguous, retain the candidate as unresolved and ask a
focused scope question instead of silently selecting or excluding it.

## Bounded search and coverage review

Use approved resolver inputs and output limits. Start with the requested
concept and precise terms; if a site is empty or expected variants are missing,
use a bounded synonym/modality/anatomy expansion within the authorized route.
Review false positives introduced by expansion. A broad hit is a candidate,
not an accepted concept; a zero hit is not proof of absent services or people.

Record terms/routes tried, site-level gaps, pages reviewed versus total, source
version, and unresolved false-positive and false-negative risks. Do not claim
complete coverage after reviewing one page or merely matching all sites. A
completeness claim needs an owner-approved catalog or other sufficient review
basis; otherwise state completeness unconfirmed. If further review would need
new access or excessive retrieval, stop expansion and give a bounded handoff
to the data owner; do not open a returned CSV or private dictionary by default.

Use only permitted summaries. Candidate-code counts are not cohort counts;
usage bands cannot be summed or converted into study counts. First/last usage
years do not demonstrate continuous capture or full historical coverage.

## Tool contract preflight

Use the current approved tool-specific input contract for site identifiers,
value types, term restrictions, paging and output bounds. Do not transfer
enumerations from a similarly named tool or hard-code institution-specific
values into this public Skill. If the contract is missing, record that gap.
Distinguish malformed arguments or a service error from a valid zero-result
response. An explicit input error can be corrected within the same authorized
scope; it is not evidence of data absence or permission to broaden access.
This rule does not relax connector-specific no-retry or capability rules.

## Progress and feasibility boundaries

Beside the single code-maturity label, describe progress in ordinary language
for study definitions, concept selections, data suitability and execution
evidence. Name completed work and remaining approvals; do not create a second
maturity scale or promote code because one dimension is complete.

Distinguish count feasibility (identifiable people/events), source-asset
usability (for example, stored/linkable images of suitable quality), and study
feasibility (population, comparator, time anchors, follow-up and outcomes fit
the intended analysis). Check each only to the extent needed by the request.
Passing one does not establish the others. In particular, counting scans among
already diagnosed cases does not establish early-prediction readiness.

For formal deliverables, carry confirmed decisions, provenance, remaining
checks and approvals into the existing contract and actionable gaps table.
Use institutional-adapter-contract.md for governed compilation; a declaration,
candidate review or local synthetic pass alone never grants execution.
