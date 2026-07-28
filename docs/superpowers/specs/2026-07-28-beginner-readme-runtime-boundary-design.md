# Beginner README and Runtime Boundary Design

**Date:** 2026-07-28

## Goal

Help readers with no prior CDISC knowledge understand the terms in the README,
and make clear that using the installed Skill does not require Python.

## Beginner explanation

Both READMEs will add a short beginner section based on current CDISC primary
sources:

- CDISC is the standards organization and standards ecosystem.
- SDTM standardizes how collected or received study data are organized and
  formatted for exchange and review.
- ADaM defines analysis datasets and metadata that support reproducible
  analysis and traceability to SDTM.

The section will show this simplified mental model:

```text
Collected or received study data
→ SDTM: standardized tabulation and review
→ ADaM: analysis-ready data and derivations
→ statistical analyses, tables, figures, and listings
```

The README must state that this is not a mandatory pipeline for every question.
EHR, claims, registry, OMOP, and other real-world data requests may use
different source models. The Skill determines which standards apply instead of
forcing every dataset into SDTM or ADaM.

## Python boundary

The installed Skill consists of Markdown, YAML, and reference material. Codex
or ChatGPT can use it without Python.

Python 3.11 remains a contributor dependency for repository tests,
deterministic packaging, and the strict source-checkout installer. PowerShell
Release installation remains Python-free. POSIX Release installation will use
native checksum tools for verification; Python may be mentioned only as an
optional alternative, not a runtime requirement.

## Documentation structure

- Place the beginner explanation before the supported-question list.
- Rename the Python setup heading so it is visibly contributor-only.
- Add a dedicated runtime-requirement section before contributor setup.
- Keep English and Traditional Chinese structures aligned.
- Link definitions directly to official CDISC pages.

## Verification

Add a README contract test before editing the READMEs. It must require the
beginner headings, the three terms, the no-Python runtime statement, the
contributor-only Python heading, and a POSIX installation block without a
mandatory `python -c` checksum command.
