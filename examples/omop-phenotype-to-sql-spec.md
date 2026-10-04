# SYNTH_PHENOTYPE_001 OMOP-to-SQL Specification

Output depth: implementation specification
Decision: Translate the hypothetical phenotype into a logical mapping checklist, without SQL or invented Concept IDs.
Confirmed facts: This is a synthetic mapping request; no institution's schema or vocabulary has been supplied.
Assumptions: The phenotype will be governed by a versioned research protocol and clinically reviewed concept set.
Limitations: Concept set, windows, mappings, current metadata and fixtures are missing.
Sources actually consulted: Current request only; artifacts below are planned review targets, not consulted sources.

## Governing evidence

Keep vocabulary-governed standard concepts, approved local-code mappings and
the research phenotype rule separate. Public OMOP definitions do not establish
an institutional schema or a clinically valid phenotype.

| Claim | Governing source to review | Authority | Applicability | Limitation |
| --- | --- | --- | --- | --- |
| Standard concept meaning | Official OMOP/OHDSI documentation | Official implementation standard | Selected vocabulary release | Concept set/version absent |
| Local mapping | SYNTH Adapter contract | Institutional | Intended source roles | Approval/live verification absent |
| Research inclusion/exclusion | SYNTH phenotype protocol | Study-specific | Hypothetical population | Clinical review pending |

## Data contract

- Logical roles: person, observation period, qualifying event and exclusion event.
- Grain, keys, allowed joins and date semantics: pending owner confirmation;
  no physical names inferred from these roles.
- Concept set/vocabulary version: require clinically reviewed versioned input;
  never substitute numeric identifiers or model-memory codes.
- Time anchors: index, lookback, minimum observation and exclusion windows
  need protocol values; unknowns remain natural-language requirements.
- Mapping: source codes use only an approved mapping version; preserve unmapped
  status rather than treating it as a negative event.
- Missingness/coverage: assess observation gaps and incomplete event capture;
  zero recorded events do not prove absence of disease.
- Outputs/lineage: approved aggregates tied to protocol, concept set, mapping
  and transformation versions; no row-level identifiers.
- Acceptance: positive, negative, boundary-window, unmapped-code and zero-result
  synthetic cases with protocol-derived expectations.

## Code maturity

`conceptual`; the concept set and required parameters are absent.

## Validation gaps

| Gap | Blocks | Next safe action | Responsible role | Completion evidence |
| --- | --- | --- | --- | --- |
| Concept set/version unknown | Phenotype specification | Request versioned reviewed summary | Clinical/vocabulary reviewer | Approved set and applicability review |
| Protocol approval pending | Inclusion/exclusion | Resolve windows and observation needs | Research owner | Signed protocol decisions |
| Local mappings unavailable | Physical implementation | Obtain authorized Adapter summary | Data owner, pending confirmation | Approved contract outside Git |
| Current metadata not verified | Maturity upgrade | Seek authorization before comparison | Adapter owner | Current comparison and discrepancy resolution |
| Fixtures not run | Acceptance claim | Prepare edge cases for authorized testing | Implementation reviewer | Passing declared checks |

Work still possible: refine logical event roles and clinical acceptance cases,
without SQL-shaped placeholders or a claim of phenotype validation.

## Execution gate

Unmet. Reassess all relevant execution gates before promotion; concept-set
approval or metadata-only results cannot independently permit SQL.

SPECIFICATION ONLY — NOT EXECUTABLE
