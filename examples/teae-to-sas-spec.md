# SYNTH_STUDY_001 TEAE-to-SAS Specification

Output depth: implementation specification
Decision: Prepare a non-executable treatment-emergent adverse-event derivation specification, without SAS against unresolved physical inputs.
Confirmed facts: This request is a hypothetical safety-analysis example, not a real study or execution result.
Assumptions: The synthetic scenario supplies an approved dictionary for logical subject and adverse-event inputs; this hypothetical approved dictionary is not independently verified approval.
Limitations: Protocol parameters, terminology, live mappings and target-environment tests remain unverified.
Sources actually consulted: Current request only; SYNTH identifiers below denote fictional scenario artifacts, not documents actually reviewed.

## Governing evidence

The hypothetical protocol and SAP govern the emergence window and partial-date
rules. Official CDISC guidance and controlled terminology govern submission
structure, not the study-specific window. Lex Jansen indexes implementation
literature; it is not a standard or validation authority.

| Claim | Governing source to review | Authority | Applicability | Limitation |
| --- | --- | --- | --- | --- |
| Emergence window | SYNTH protocol and SAP | Study-specific | Safety population | Signed versions and rules not reviewed |
| Submission structure | Applicable CDISC guide | Official standard | Submission target | Version and applicability pending review |
| Coded values | Governing terminology release | Official terminology | Target variables | Must match submission plan |
| SAS technique | Specific paper indexed by Lex Jansen | Implementation evidence | Future technique review | Not searched or reviewed; performance not measured |

## Data contract

- Subject input: one record per synthetic subject, logical subject key, treatment
  start and safety-population role defined by the assumed dictionary.
- Event input: one record per adverse event with logical subject key, onset,
  worsening and coding facts; physical fields pending owner confirmation.
- Join: many events to one subject; reject unmatched events and multiplying joins.
- Parameters: emergence window, partial-date/ongoing-event rules and terminology
  version require approved values, not guesses. Precision, missingness and
  comparison precedence follow the signed SAP.
- Outputs: approved analysis roles and aggregate review findings; preserve lineage
  to protocol, SAP, dictionary and transformation versions.
- Acceptance cases: onset inside the window, pre-treatment resolution, worsening,
  partial dates and unmatched subjects, with expectations from the reviewed SAP.

## Code maturity

`dictionary-specified` under the synthetic dictionary assumption above.

## Validation gaps

| Gap | Blocks | Next safe action | Responsible role | Completion evidence |
| --- | --- | --- | --- | --- |
| Protocol/SAP rules not reviewed | Derivation | Request authorized version summary | Study owner | Approved versions and reviewed rules |
| CDISC/terminology applicability unknown | Submission mapping | Review governing public releases | Standards reviewer | Dated applicability record |
| Physical mappings unavailable | Local implementation | Obtain authorized Adapter summary outside Git | Data owner, pending confirmation | Versioned approved mapping |
| Live metadata not verified | Maturity upgrade | Request authorization before comparison | Adapter owner | Approved current comparison |
| Fixtures not run | Acceptance claim | Prepare synthetic cases, then test in authorized target | Implementation reviewer | Passing cases and independent review |

Work still possible: refine the logical contract and acceptance cases without
inventing fields, implementing SAS, or claiming a reviewed source.

## Execution gate

Unmet. Reassess all relevant execution gates after gaps close; one completed gap
or metadata-only check cannot grant execution authority.

SPECIFICATION ONLY — NOT EXECUTABLE
