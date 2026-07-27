---
name: clinical-data-research-navigator
description: Use when a clinical-data, CDISC, ADaM, SDTM, SAS, SQL, R, EHR, claims, registry, OMOP, or TMUCRD question requires source navigation, terminology mapping, evidence ranking, a data contract, or an implementation specification.
---

# Clinical Data Research Navigator

## Core Principle

Route each claim to the correct authority, separate evidence from local schema,
and never label code executable without current metadata and tests.

## Code Maturity

Use exactly one label: `conceptual`, `dictionary-specified`, `parameterized`,
`executable`, or `validated`.

Without a versioned institutional adapter, live metadata verification, and
fixture tests, emit `SPECIFICATION ONLY — NOT EXECUTABLE`.
