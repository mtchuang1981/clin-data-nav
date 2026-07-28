# Changelog

## 0.2.0 - 2026-07-28

### Features

- Add PICO-informed question framing and explicit descriptive, predictive,
  causal-comparative, measurement, and implementation routing.
- Distinguish RWD from analysis-derived RWE and add a target trial emulation
  readiness gate for causal comparative questions.
- Define the optional `build-rwe-sap` compatibility, handoff, degraded
  operation, and execution-gate contract without bundling a second Skill.

### Documentation

- Explain CDISC, SDTM, and ADaM for readers new to clinical-data standards.
- Clarify that installed Skill use does not require Python and make POSIX
  Release installation verification Python-free.
- Document the bilingual RWE, TTE, and optional `build-rwe-sap` workflow.

### Validation

- Expand the offline behaviour catalog from 7 to 11 cases, including
  descriptive RWD, TTE handoff, incomplete causal readiness, and unavailable
  optional-Skill scenarios.

## 0.1.1 - 2026-07-28

### Features

- Add a traceable Lex Jansen retrieval contract for SAS optimization,
  including paper-level provenance, code reuse terms, clean-room fallback,
  no-network reporting, and target-environment performance validation.

### Documentation

- Add a Traditional Chinese README.
- Document installation from GitHub Release with SHA-256 verification,
  source-checkout installation, Skill discovery, explicit invocation, and
  representative clinical-data prompts.
