# Changelog

## 0.7.1 - 2026-09-09

### Changed

- Return quick explanations as concise natural prose without a fixed output-depth
  header or mandatory section headings.
- Keep evidence navigation, research design, and implementation specification on
  their existing structured contracts, including completion conditions and
  execution boundaries.
- Express unknown institutional mappings as natural-language requirements marked
  for confirmation rather than SQL-shaped or physical-schema placeholders.

### Evaluation

- In the frozen ZIP comparison, the candidate passed all 18 quick-format cells
  and reduced paired median visible length by 47.46% without an observed safety
  violation.
- Preserve the automated `candidate-not-supported` result. Human review classified
  three formal-response misses as wording false negatives but did not rewrite the
  frozen scores or claim general model improvement.

### Limitations

- Results apply only to the fixed synthetic prompts, model, CLI, and run conditions.
  They do not establish human effectiveness, clinical validity, or deployment
  fitness.

## 0.7.0 - 2026-08-27

### Changed

- Route mixed-cue requests by their primary deliverable so literature,
  provenance, public-profile, phenotype, and optional causal-handoff requests
  select the intended response depth even when they mention code or
  optimization.
- Add positive completion slots for every response depth so required evidence,
  design, safety, and execution-boundary fields are stated explicitly.

### Evaluation

- Treat only headings reserved by another response depth as cross-depth
  violations; useful auxiliary headings remain allowed.
- Accept tested semantic equivalents and safe negated boundaries while still
  rejecting affirmative causal-validation and complete-SAP delivery claims.

### Limitations

- This release has not completed a new immutable 72-cell campaign or a human
  pilot. The prior normative campaign remains `mixed-or-null`; development
  preflight results do not establish human effectiveness, clinical validity,
  or deployment fitness.

## 0.6.0 - 2026-08-24

### Features

- Add a provider-neutral public simulation benchmark that freezes all 12
  deterministic Eval cases across control and intervention conditions for
  three repeats, producing a complete 72-cell external run plan.
- Bind the first normative campaign to the exact released `v0.5.0` Skill
  bundle while keeping plans, response indexes, raw responses, provider logs,
  and generated reports outside the repository.
- Reuse the existing deterministic evaluator for paired aggregation and
  bilingual reporting, and add structured community Issue Forms that remain
  outside formal benchmark aggregates.

### Limitations

- No real benchmark campaign or human pilot has been performed. Checked-in
  benchmark results are synthetic contract examples only and do not establish
  usability, clinical validity, causal validity, patient benefit, or fitness
  for deployment.

## 0.5.0 - 2026-08-16

### Changed

- Rename the single public Skill ID and explicit invocation from the previous
  identity to `clin-nav` and `$clin-nav`, while preserving the existing
  clinical routing, authority, output-depth, and safety behavior.
- Add a green-capable effectiveness-recovery contract with six deterministic
  states, four content-free CLI checks, aligned guidance, and fail-closed
  public-boundary enforcement. The affected batch remains
  `excluded-from-effectiveness-analysis`.

### Packaging

- Prepare reproducible `clin-nav-0.5.0.zip` and
  `clin-nav-0.5.0.manifest.json` release artifacts and install to the
  `clin-nav` directory.

### Limitations

- The rename does not establish human effectiveness. No real replacement pilot was performed; observed `evaluation-green` remains pending; and power analysis remains deferred.

## 0.4.0 - 2026-08-10

### Features

- Add the human-effectiveness evaluation framework with strict synthetic-data
  contracts: balanced assignments, task-pack commitment, blinded agreement and
  unlock safeguards, paired analysis, controlled deviations and limitations,
  and aggregate-only bilingual reports.
- Preserve PICO, RWD, RWE, and target trial emulation (TTE) documentation
  continuity alongside the protocol, input schema, quick start, and public
  repository boundaries.

### Validation

- Verify deterministic package and effectiveness-framework contracts with the
  official Python 3.11.9 runtime across supported platforms.
- Enforce canonical LF checkouts for reproducible package bytes and recover
  bilingual reports transactionally if publication replacement fails.

### Limitations

- The framework is available for approved future use, but no human pilot was
  conducted and the Skill is not proven effective. All examples remain
  synthetic and aggregate-only.

## 0.3.0 - 2026-08-08

### Features

- Add four explicit output depths so each response uses the least intensive
  safe shape that fully answers the request.
- Add aligned bilingual beginner navigation with a glossary, guided learning
  paths, a compact first-success flow, and stage-specific installation help.

### Validation

- Expand the offline Eval evidence to 12 catalog cases, each with one scored
  baseline/forward fixture pair across the four output depths.
- Require Ubuntu and Windows package candidates to have byte-identical ZIP and
  manifest files before validation or Release workflows can continue.
- Update official GitHub Actions to pinned Node.js 24-capable releases while
  retaining least-privilege workflow boundaries.

### Documentation

- Improve citation, Skill UI, security, product-boundary, and repository-setting
  metadata without claiming unverified external state.

### Fixed

- Canonicalize UTF-8 text line endings before hashing and archiving so Windows
  and POSIX checkouts produce the same package bytes for equivalent content.

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
