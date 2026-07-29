# Changelog

## 0.2.2 - 2026-07-29

### Fixed

- Make fresh Python 3.11 editable installation deterministic by declaring the
  setuptools package boundary.
- Make atomic installer platform tests portable across Windows and POSIX hosts
  without adding an overwrite fallback.
- Run the complete validation set on Ubuntu and Windows and add a fail-closed,
  manually dispatched GitHub Release workflow.

### Documentation

- Add prerequisites, terminal-versus-Codex command boundaries, an update
  command, and a 60-second first-success path in both READMEs.
- Distinguish the 11-case Eval catalog from the three scored fixture pairs.

## 0.2.1 - 2026-07-29

### Documentation

- Add a bilingual quick start using
  `npx skills add mtchuang1981/clin-data-nav`.
- Clarify that the `npx` path is project-local and retain the versioned,
  manifest-verified GitHub Release workflow as the verified manual option.

### Validation

- Extend the README contract test to cover the quick-start command,
  project-local installation boundary, Skill discovery, and explicit
  invocation.

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
