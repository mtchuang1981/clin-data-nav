## Decision

Output depth: implementation specification

Prepare a synthetic logical TEAE derivation only. The study protocol and SAP
govern the study-specific definition; the applicable official standard and
controlled terminology govern standardized representation.

## Evidence table

| Decision | Governing evidence | Limitation |
|---|---|---|
| Event emergence window | Approved protocol and SAP | No hypothetical date window is promoted to a study rule |
| Standardized representation | Applicable official standard | Confirm the version used by the study |

## Data contract

Logical grain is one adverse-event occurrence per subject. Required concepts
include stable subject and event keys, treatment exposure interval, event
onset and end precision, baseline status, terminology version, missing-date
precedence, lineage to inputs, and acceptance fixtures for boundary dates,
partial dates, no exposure, duplicates, and conflicting records.

## Code maturity

Code maturity: `conceptual`.

SPECIFICATION ONLY — NOT EXECUTABLE. No SAS program is supplied before the
approved Adapter, metadata, parameters, and fixtures pass the execution gate.

## Validation gaps

Confirm the approved study definition, treatment-emergence window, imputation
rules, terminology snapshot, physical mappings, and expected fixture results.

## Sources

- Approved protocol and SAP, when supplied.
- Applicable official standard and controlled terminology, version to be
  confirmed.
