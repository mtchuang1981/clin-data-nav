# SYNTH_STUDY_001 TEAE-to-SAS Specification

## Decision

Use the `SYNTH_STUDY_001` protocol and SAP as the study-specific authority for
the treatment-emergence rule. Use CDISC implementation guidance and governed
controlled terminology as official authority for the submission structure.
Use Lex Jansen only as secondary implementation evidence.

Deliver a non-executable derivation specification at maturity
`dictionary-specified`.

## Evidence table

| Claim | Source | Authority level | Publication date | Version or snapshot | Applicability | Limitations |
|---|---|---|---|---|---|---|
| Treatment-emergence window | `SYNTH_PROTOCOL_001` and `SYNTH_SAP_001` | Study-specific | `SYNTH_2026_DATE` | `SYNTH_APPROVED_VERSION` | `SYNTH_STUDY_001` safety population | Owner approval must be confirmed |
| Submission variables | Applicable CDISC implementation guide | Official standard | Confirm from source | Confirm governed version | Target deliverable | Does not define the study window |
| Coded values | Applicable controlled terminology release | Official terminology | Confirm from source | `SYNTH_CT_VERSION_SLOT` | Target variables | Release must match the submission plan |
| SAS technique | Reviewed Lex Jansen paper | Secondary implementation evidence | Confirm paper year | `SYNTH_PAPER_SNAPSHOT` | Pseudocode review | Not a standard or validation authority |

## Data contract

Inputs:

- `SYNTH_ADSL`: one row per `USUBJID`; provide treatment start and safety
  population flag according to `SYNTH_SAP_001`.
- `SYNTH_ADAE`: one row per adverse-event record; provide subject identifier,
  event start, treatment-emergence input facts, coding fields, and required
  analysis identifiers.
- `SYNTH_PARAMETERS`: provide the approved emergence window, partial-date rule,
  ongoing-event rule, and controlled-terminology version.

Join `SYNTH_ADAE` to `SYNTH_ADSL` by the approved synthetic subject key with an
expected many-to-one cardinality. Reject unmatched event rows and subject-key
multiplication.

Derivation pseudocode:

```text
for each SYNTH_ADAE record:
  require exactly one matching SYNTH_ADSL subject
  derive the comparison dates using SYNTH_SAP_001 partial-date rules
  evaluate onset or worsening within SYNTH_PARAMETERS.emergence_window
  assign the governed treatment-emergence value
  retain an auditable reason for the assignment
```

Acceptance cases:

| Case | Synthetic condition | Expected result |
|---|---|---|
| `SYNTH_CASE_PRE` | Event ends before treatment and does not worsen | Not treatment-emergent |
| `SYNTH_CASE_ONSET` | Event begins inside the approved window | Treatment-emergent |
| `SYNTH_CASE_WORSE` | Pre-existing event worsens after treatment | Apply the SAP worsening rule |
| `SYNTH_CASE_PARTIAL` | Event date is incomplete | Apply the approved partial-date rule |
| `SYNTH_CASE_UNMATCHED` | No matching subject | Reject and report |

## Code maturity

`dictionary-specified`

```text
SPECIFICATION ONLY — NOT EXECUTABLE
```

Do not promote until `SYNTH_PROTOCOL_001`, `SYNTH_SAP_001`, terminology,
physical mappings, and target-environment fixtures are approved.

## Validation gaps

- Confirm the signed protocol and SAP versions.
- Confirm the CDISC guide and controlled-terminology release.
- Supply physical mappings through an approved Adapter.
- Verify live metadata and many-to-one cardinality.
- Run the five synthetic acceptance cases and independent derivation review.

## Sources

List the reviewed `SYNTH_STUDY_001` documents, official CDISC sources,
controlled-terminology release, and the specific Lex Jansen paper with its
conference year and limitations.
