# STE-inspired public guidance coverage — 2026-10-24

Scope: all 42 current public Markdown guidance files listed in the approved
[design](../superpowers/specs/2026-10-24-ste-project-release-design.md).
This is a writing-principles review, not formal ASD-STE100 certification.
English and Traditional Chinese retain the same rules and safety boundaries.
Technical terms, fixed labels and protected evidence take precedence over mechanical simplification.

| File | Disposition | Review focus / reason |
| --- | --- | --- |
| README.md | edited | Clear product limits and conditional instructions |
| README.zh-TW.md | edited | Same boundaries in natural Traditional Chinese |
| CONTRIBUTING.md | edited | Separate environment, test and stop actions |
| SECURITY.md | edited | Separate reporting and incident-response actions |
| AGENTS.md | reviewed/retained | Clear working agreement; avoid policy drift |
| .github/pull_request_template.md | reviewed/retained | Preserve explicit attestations |
| docs/architecture.md | edited | Separate private-owner and release-job actions |
| docs/glossary.md | edited | Separate definitions from limits |
| docs/glossary.zh-TW.md | edited | Clarify definitions and time-zero conditions |
| docs/installation.md | edited | Single-action steps and bounded recovery |
| docs/installation.zh-TW.md | edited | Conditions before install/recovery actions |
| docs/learning-paths.md | edited | Clear stop and promotion conditions |
| docs/learning-paths.zh-TW.md | edited | Equivalent depth and safety limits |
| docs/release.md | edited | Separate checks, publication and evidence recording |
| docs/repository-settings.md | edited | State prerequisites before setting changes |
| examples/omop-phenotype-to-sql-spec.md | edited | Separate contract and maturity limits |
| examples/synthetic-institutional-mapping.md | edited | Keep stop/correction/retest under the discrepancy condition |
| examples/teae-to-sas-spec.md | edited | Separate evidence, contract and execution gate |
| skills/clin-nav/SKILL.md | edited | Shorter routing and safety clauses; authorization scope preserved |
| skills/clin-nav/references/retrieval-playbook.md | edited | Vertical provenance list and explicit review gaps |
| skills/clin-nav/references/rwe-question-routing.md | edited | Separate scoping, investigator confirmation and execution authority |
| skills/clin-nav/references/evidence-ledger.md | edited | Separate review state, unknown identifiers and exit meanings |
| skills/clin-nav/references/evidence-audit.md | edited | Vertical closed-field and size-limit lists |
| skills/clin-nav/references/evidence-output-template.md | edited | Separate artifact, safety and gap-closing conditions |
| skills/clin-nav/references/institutional-adapter-contract.md | edited | Separate provenance, authorization and maturity conditions |
| skills/clin-nav/references/omop-metadata-connector.md | edited | Separate structural/DQD results and invalidation conditions |
| skills/clin-nav/references/output-depths-and-learning-paths.md | edited | Conditional clarification and explicit completion actions |
| skills/clin-nav/references/tmucrd-public-profile.md | reviewed/retained | Clear dated public-source/non-schema boundary; preserve citation identities |
| evals/README.md | edited | Separate framework existence from observed effectiveness |
| evals/compiler-pipeline/README.md | edited | Separate keyword result from semantic review |
| evals/research-headings/README.md | edited | Separate API shape and caller record duty |
| evals/omop-metadata-connector/README.md | edited | Separate aggregate deviations from absent private names |
| evals/benchmark/README.md | edited | Separate session requirements, results and claim boundaries |
| evals/benchmark/summary-schema.md | edited | Separate identity, digest and provenance constraints |
| evals/effectiveness/README.md | edited | Ordered rescore process without condition-key access |
| evals/effectiveness/input-schema.md | edited | Separate field and chronological constraints |
| evals/effectiveness/governance/README.md | edited | Vertical stop conditions and external storage boundary |
| evals/effectiveness/governance/checklist.md | edited | Separate readiness and authorization |
| evals/effectiveness/governance/checklist.zh-TW.md | edited | Equivalent role and authority boundaries |
| evals/effectiveness/recovery/README.md | edited | Ordered incident restart actions and independent authority |
| evals/effectiveness/recovery/checklist.md | edited | Separate restart, preparation and recovery actions |
| evals/effectiveness/recovery/checklist.zh-TW.md | edited | Equivalent recruitment and recovery conditions |

Additional review: `skills/clin-nav/agents/openai.yaml` retained unchanged.
No new UI metadata feature, icon, implicit-invocation setting or product policy was added.

Historical releases, dated verification records, old plans, protocols, fixture
answers and generated report blocks are excluded from prose rewriting.
Current version/date bindings are updated separately, not treated as language changes.
Published v0.10.0 asset facts stay current until a newer release is actually verified.

Frozen legacy result digest remains a verification requirement:
`6c7db3794be2f5b74107a27ae9dae5e385aa82cfabb98be691bf4b67b72b8757`.
No claim of improved model answers, token savings, human usability or clinical validity follows from these edits.
