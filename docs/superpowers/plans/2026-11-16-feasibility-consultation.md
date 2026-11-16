# Feasibility consultation refinement

Scope approved in the current conversation on 2026-11-16: improve semantic
candidate review, bounded search completeness, coordinator decisions, tool
argument checks, progress visibility and concise consultation delivery.
This is local skill work, not publication, installation or private Adapter work.

## Design and execution plan

Preserve the existing four depths and all execution gates. Treat an initial
request to review how to handle an unresolved consultation as orientation,
using quick explanation with four concise content parts. Explicit requests
for counts specifications, mappings or executable readiness retain formal
implementation specification. Keep substantial guidance in one new reference.

- [x] Read existing governed pipeline design, implementation plan, skill,
  output contracts, agent metadata and relevant eval contracts.
- [x] Run a synthetic independent baseline before editing guidance.
- [x] Add failing package/reference and synthetic scenario-contract tests.
- [x] Add consultation routing and the one-hop reference; reconcile output
  and RWE references without replacing formal contracts or maturity labels.
- [x] Add a separate semantic-review scenario suite, preserving frozen evals.
- [x] Forward-test with an independent fresh-context agent; review actual
  decisions and omissions, not keyword matches. Record limits honestly.
- [x] Run repository-required verification and review the complete diff.

## Evidence and scope limits

The initial baseline correctly flagged semantic mismatch, zero-hit ambiguity,
mixed modalities and unread pages. Its observed failure against the approved
delivery goal was an unnecessarily long formal specification for a coordinator
orientation request. Semantic cases are regressions, not newly proven defects.
Five baseline and five forward samples across two synthetic prompts, plus a
formal-request check and a supplied tool-error record review, cannot establish
general effectiveness. See the dated local verification note for exact scope.

Public cases use fictional families, modalities, sites and identifiers only.
No original consultation, institution-specific mapping or private tool output
is stored. Tool-specific values belong to the approved Adapter contract;
ClinNav adds argument checking, not a duplicate registry or private compiler.
Agent metadata is reviewed and unchanged: its generic prompt still applies.
