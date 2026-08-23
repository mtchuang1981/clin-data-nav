# Public simulation benchmark report — synthetic contract example

## Identity and scope

This report contains aggregate benchmark facts only. The execution identity is recorded for reproduction, not independently verified.
| Field | Value |
|---|---|
| `benchmark_id` | public-simulation-v0-5-0 |
| `schema_version` | 1 |
| `status` | benchmark-observed |
| `direction` | positive-signal |
| `synthetic_example` | true |
| `plan_sha256` | cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc |
| `catalog_sha256` | a07346b6d1c942693f52edf73f0a3fafff5c0f080a5cfe15e5ac4ebd9002641d |
| `rubric_sha256` | 5c290c7a2002cb08853bcdf328e4a0029bb76a251180ddaf848c4a1ee38a0e1f |
| `repeats` | 3 |
| `cell_counts.expected` | 72 |
| `cell_counts.observed` | 72 |
| `skill.archive` | clin-nav-0.5.0.zip |
| `skill.archive_sha256` | 195967e3e3b1a6ee32de18a442a7c84badc6642ce6b4ddc0456c441b5f25686d |
| `skill.commit` | 3af75bec2c6c79e5617fb94f031eec60a7604143 |
| `skill.manifest` | clin-nav-0.5.0.manifest.json |
| `skill.manifest_sha256` | 03b736ec703ce3c8b78acc56a8e467d109612fbdd01b08240202d355228332c6 |
| `skill.member_set_sha256` | 7bb1705efb150f44f65a3b41003cad7cbcfc9b257d29a5f9e7c33bd12e2059ad |
| `skill.tag` | v0.5.0 |
| `skill.tag_object` | 77c1e1ea140fab8343b178bae63d9c6fc740ccd7 |
| `skill.version` | 0.5.0 |
| `model.id` | synthetic-model |
| `model.max_output_tokens` | 600 |
| `model.provider` | synthetic-provider |
| `model.seed_policy` | externally-reported |
| `model.snapshot` | synthetic-snapshot |
| `model.temperature` | 0.200000 |
| `model.top_p` | 0.900000 |
| `execution_attestation.assertion_basis` | externally-asserted |
| `execution_attestation.completed_at` | 2026-08-16T01:00:00+00:00 |
| `execution_attestation.fresh_sessions` | true |
| `execution_attestation.model_id` | synthetic-model |
| `execution_attestation.model_provider` | synthetic-provider |
| `execution_attestation.model_snapshot` | synthetic-snapshot |
| `execution_attestation.offline` | true |
| `execution_attestation.plan_followed` | true |
| `execution_attestation.runner_name` | synthetic-runner |
| `execution_attestation.runner_version` | 1.0.0 |
| `execution_attestation.shared_configuration_unchanged` | true |
| `claim_boundaries.0` | public-synthetic-prompts-only |
| `claim_boundaries.1` | deterministic-contract-checks-only |
| `claim_boundaries.2` | no-representative-user-evidence |
| `claim_boundaries.3` | no-clinical-causal-patient-outcome-or-deployment-claim |

## Aggregate result

The status and direction are separate predeclared classifications.
| Field | Value |
|---|---|
| `overall.control_pass_rate` | 0.666667 |
| `overall.control_passes` | 24 |
| `overall.difference` | 0.333333 |
| `overall.intervention_pass_rate` | 1.000000 |
| `overall.intervention_passes` | 36 |
| `overall.pairs` | 36 |

## Paired changes

Each count compares the control and intervention result for one case/repeat pair.
| Field | Value |
|---|---|
| `paired_counts.both_fail` | 0 |
| `paired_counts.both_pass` | 24 |
| `paired_counts.improved` | 12 |
| `paired_counts.worsened` | 0 |

## Output-depth strata

Strata use the canonical output-depth order from the validated summary.
| Field | Value |
|---|---|
| `depth.evidence navigation.case_count` | 3 |
| `depth.evidence navigation.pairs` | 9 |
| `depth.evidence navigation.control_passes` | 6 |
| `depth.evidence navigation.control_pass_rate` | 0.666667 |
| `depth.evidence navigation.intervention_passes` | 9 |
| `depth.evidence navigation.intervention_pass_rate` | 1.000000 |
| `depth.evidence navigation.difference` | 0.333333 |
| `depth.evidence navigation.paired_counts.both_fail` | 0 |
| `depth.evidence navigation.paired_counts.both_pass` | 6 |
| `depth.evidence navigation.paired_counts.improved` | 3 |
| `depth.evidence navigation.paired_counts.worsened` | 0 |
| `depth.evidence navigation.forbidden_violations.control` | 0 |
| `depth.evidence navigation.forbidden_violations.intervention` | 0 |
| `depth.implementation specification.case_count` | 3 |
| `depth.implementation specification.pairs` | 9 |
| `depth.implementation specification.control_passes` | 3 |
| `depth.implementation specification.control_pass_rate` | 0.333333 |
| `depth.implementation specification.intervention_passes` | 9 |
| `depth.implementation specification.intervention_pass_rate` | 1.000000 |
| `depth.implementation specification.difference` | 0.666667 |
| `depth.implementation specification.paired_counts.both_fail` | 0 |
| `depth.implementation specification.paired_counts.both_pass` | 3 |
| `depth.implementation specification.paired_counts.improved` | 6 |
| `depth.implementation specification.paired_counts.worsened` | 0 |
| `depth.implementation specification.forbidden_violations.control` | 0 |
| `depth.implementation specification.forbidden_violations.intervention` | 0 |
| `depth.quick explanation.case_count` | 1 |
| `depth.quick explanation.pairs` | 3 |
| `depth.quick explanation.control_passes` | 0 |
| `depth.quick explanation.control_pass_rate` | 0.000000 |
| `depth.quick explanation.intervention_passes` | 3 |
| `depth.quick explanation.intervention_pass_rate` | 1.000000 |
| `depth.quick explanation.difference` | 1.000000 |
| `depth.quick explanation.paired_counts.both_fail` | 0 |
| `depth.quick explanation.paired_counts.both_pass` | 0 |
| `depth.quick explanation.paired_counts.improved` | 3 |
| `depth.quick explanation.paired_counts.worsened` | 0 |
| `depth.quick explanation.forbidden_violations.control` | 0 |
| `depth.quick explanation.forbidden_violations.intervention` | 0 |
| `depth.research design.case_count` | 5 |
| `depth.research design.pairs` | 15 |
| `depth.research design.control_passes` | 15 |
| `depth.research design.control_pass_rate` | 1.000000 |
| `depth.research design.intervention_passes` | 15 |
| `depth.research design.intervention_pass_rate` | 1.000000 |
| `depth.research design.difference` | 0.000000 |
| `depth.research design.paired_counts.both_fail` | 0 |
| `depth.research design.paired_counts.both_pass` | 15 |
| `depth.research design.paired_counts.improved` | 0 |
| `depth.research design.paired_counts.worsened` | 0 |
| `depth.research design.forbidden_violations.control` | 0 |
| `depth.research design.forbidden_violations.intervention` | 0 |

## Per-case stability

Pass counts and stability labels cover all three repeats in canonical case order.
| Field | Value |
|---|---|
| `case.adam-quick-explanation.output_depth` | quick explanation |
| `case.adam-quick-explanation.control_passes` | 0 |
| `case.adam-quick-explanation.intervention_passes` | 3 |
| `case.adam-quick-explanation.paired_counts.both_fail` | 0 |
| `case.adam-quick-explanation.paired_counts.both_pass` | 0 |
| `case.adam-quick-explanation.paired_counts.improved` | 3 |
| `case.adam-quick-explanation.paired_counts.worsened` | 0 |
| `case.adam-quick-explanation.forbidden_violations.control` | 0 |
| `case.adam-quick-explanation.forbidden_violations.intervention` | 0 |
| `case.adam-quick-explanation.stability.control` | stable-fail |
| `case.adam-quick-explanation.stability.intervention` | stable-pass |
| `case.teae-sas-spec.output_depth` | implementation specification |
| `case.teae-sas-spec.control_passes` | 0 |
| `case.teae-sas-spec.intervention_passes` | 3 |
| `case.teae-sas-spec.paired_counts.both_fail` | 0 |
| `case.teae-sas-spec.paired_counts.both_pass` | 0 |
| `case.teae-sas-spec.paired_counts.improved` | 3 |
| `case.teae-sas-spec.paired_counts.worsened` | 0 |
| `case.teae-sas-spec.forbidden_violations.control` | 0 |
| `case.teae-sas-spec.forbidden_violations.intervention` | 0 |
| `case.teae-sas-spec.stability.control` | stable-fail |
| `case.teae-sas-spec.stability.intervention` | stable-pass |
| `case.sas-optimization-lexjansen.output_depth` | evidence navigation |
| `case.sas-optimization-lexjansen.control_passes` | 0 |
| `case.sas-optimization-lexjansen.intervention_passes` | 3 |
| `case.sas-optimization-lexjansen.paired_counts.both_fail` | 0 |
| `case.sas-optimization-lexjansen.paired_counts.both_pass` | 0 |
| `case.sas-optimization-lexjansen.paired_counts.improved` | 3 |
| `case.sas-optimization-lexjansen.paired_counts.worsened` | 0 |
| `case.sas-optimization-lexjansen.forbidden_violations.control` | 0 |
| `case.sas-optimization-lexjansen.forbidden_violations.intervention` | 0 |
| `case.sas-optimization-lexjansen.stability.control` | stable-fail |
| `case.sas-optimization-lexjansen.stability.intervention` | stable-pass |
| `case.institutional-sql-without-dictionary.output_depth` | implementation specification |
| `case.institutional-sql-without-dictionary.control_passes` | 0 |
| `case.institutional-sql-without-dictionary.intervention_passes` | 3 |
| `case.institutional-sql-without-dictionary.paired_counts.both_fail` | 0 |
| `case.institutional-sql-without-dictionary.paired_counts.both_pass` | 0 |
| `case.institutional-sql-without-dictionary.paired_counts.improved` | 3 |
| `case.institutional-sql-without-dictionary.paired_counts.worsened` | 0 |
| `case.institutional-sql-without-dictionary.forbidden_violations.control` | 0 |
| `case.institutional-sql-without-dictionary.forbidden_violations.intervention` | 0 |
| `case.institutional-sql-without-dictionary.stability.control` | stable-fail |
| `case.institutional-sql-without-dictionary.stability.intervention` | stable-pass |
| `case.stale-codingbook.output_depth` | implementation specification |
| `case.stale-codingbook.control_passes` | 3 |
| `case.stale-codingbook.intervention_passes` | 3 |
| `case.stale-codingbook.paired_counts.both_fail` | 0 |
| `case.stale-codingbook.paired_counts.both_pass` | 3 |
| `case.stale-codingbook.paired_counts.improved` | 0 |
| `case.stale-codingbook.paired_counts.worsened` | 0 |
| `case.stale-codingbook.forbidden_violations.control` | 0 |
| `case.stale-codingbook.forbidden_violations.intervention` | 0 |
| `case.stale-codingbook.stability.control` | stable-pass |
| `case.stale-codingbook.stability.intervention` | stable-pass |
| `case.cdisc-variable-definition.output_depth` | evidence navigation |
| `case.cdisc-variable-definition.control_passes` | 3 |
| `case.cdisc-variable-definition.intervention_passes` | 3 |
| `case.cdisc-variable-definition.paired_counts.both_fail` | 0 |
| `case.cdisc-variable-definition.paired_counts.both_pass` | 3 |
| `case.cdisc-variable-definition.paired_counts.improved` | 0 |
| `case.cdisc-variable-definition.paired_counts.worsened` | 0 |
| `case.cdisc-variable-definition.forbidden_violations.control` | 0 |
| `case.cdisc-variable-definition.forbidden_violations.intervention` | 0 |
| `case.cdisc-variable-definition.stability.control` | stable-pass |
| `case.cdisc-variable-definition.stability.intervention` | stable-pass |
| `case.omop-phenotype.output_depth` | research design |
| `case.omop-phenotype.control_passes` | 3 |
| `case.omop-phenotype.intervention_passes` | 3 |
| `case.omop-phenotype.paired_counts.both_fail` | 0 |
| `case.omop-phenotype.paired_counts.both_pass` | 3 |
| `case.omop-phenotype.paired_counts.improved` | 0 |
| `case.omop-phenotype.paired_counts.worsened` | 0 |
| `case.omop-phenotype.forbidden_violations.control` | 0 |
| `case.omop-phenotype.forbidden_violations.intervention` | 0 |
| `case.omop-phenotype.stability.control` | stable-pass |
| `case.omop-phenotype.stability.intervention` | stable-pass |
| `case.tmucrd-public-profile.output_depth` | evidence navigation |
| `case.tmucrd-public-profile.control_passes` | 3 |
| `case.tmucrd-public-profile.intervention_passes` | 3 |
| `case.tmucrd-public-profile.paired_counts.both_fail` | 0 |
| `case.tmucrd-public-profile.paired_counts.both_pass` | 3 |
| `case.tmucrd-public-profile.paired_counts.improved` | 0 |
| `case.tmucrd-public-profile.paired_counts.worsened` | 0 |
| `case.tmucrd-public-profile.forbidden_violations.control` | 0 |
| `case.tmucrd-public-profile.forbidden_violations.intervention` | 0 |
| `case.tmucrd-public-profile.stability.control` | stable-pass |
| `case.tmucrd-public-profile.stability.intervention` | stable-pass |
| `case.descriptive-rwd-no-tte.output_depth` | research design |
| `case.descriptive-rwd-no-tte.control_passes` | 3 |
| `case.descriptive-rwd-no-tte.intervention_passes` | 3 |
| `case.descriptive-rwd-no-tte.paired_counts.both_fail` | 0 |
| `case.descriptive-rwd-no-tte.paired_counts.both_pass` | 3 |
| `case.descriptive-rwd-no-tte.paired_counts.improved` | 0 |
| `case.descriptive-rwd-no-tte.paired_counts.worsened` | 0 |
| `case.descriptive-rwd-no-tte.forbidden_violations.control` | 0 |
| `case.descriptive-rwd-no-tte.forbidden_violations.intervention` | 0 |
| `case.descriptive-rwd-no-tte.stability.control` | stable-pass |
| `case.descriptive-rwd-no-tte.stability.intervention` | stable-pass |
| `case.causal-rwd-tte-handoff.output_depth` | research design |
| `case.causal-rwd-tte-handoff.control_passes` | 3 |
| `case.causal-rwd-tte-handoff.intervention_passes` | 3 |
| `case.causal-rwd-tte-handoff.paired_counts.both_fail` | 0 |
| `case.causal-rwd-tte-handoff.paired_counts.both_pass` | 3 |
| `case.causal-rwd-tte-handoff.paired_counts.improved` | 0 |
| `case.causal-rwd-tte-handoff.paired_counts.worsened` | 0 |
| `case.causal-rwd-tte-handoff.forbidden_violations.control` | 0 |
| `case.causal-rwd-tte-handoff.forbidden_violations.intervention` | 0 |
| `case.causal-rwd-tte-handoff.stability.control` | stable-pass |
| `case.causal-rwd-tte-handoff.stability.intervention` | stable-pass |
| `case.causal-rwd-incomplete-readiness.output_depth` | research design |
| `case.causal-rwd-incomplete-readiness.control_passes` | 3 |
| `case.causal-rwd-incomplete-readiness.intervention_passes` | 3 |
| `case.causal-rwd-incomplete-readiness.paired_counts.both_fail` | 0 |
| `case.causal-rwd-incomplete-readiness.paired_counts.both_pass` | 3 |
| `case.causal-rwd-incomplete-readiness.paired_counts.improved` | 0 |
| `case.causal-rwd-incomplete-readiness.paired_counts.worsened` | 0 |
| `case.causal-rwd-incomplete-readiness.forbidden_violations.control` | 0 |
| `case.causal-rwd-incomplete-readiness.forbidden_violations.intervention` | 0 |
| `case.causal-rwd-incomplete-readiness.stability.control` | stable-pass |
| `case.causal-rwd-incomplete-readiness.stability.intervention` | stable-pass |
| `case.build-rwe-sap-unavailable.output_depth` | research design |
| `case.build-rwe-sap-unavailable.control_passes` | 3 |
| `case.build-rwe-sap-unavailable.intervention_passes` | 3 |
| `case.build-rwe-sap-unavailable.paired_counts.both_fail` | 0 |
| `case.build-rwe-sap-unavailable.paired_counts.both_pass` | 3 |
| `case.build-rwe-sap-unavailable.paired_counts.improved` | 0 |
| `case.build-rwe-sap-unavailable.paired_counts.worsened` | 0 |
| `case.build-rwe-sap-unavailable.forbidden_violations.control` | 0 |
| `case.build-rwe-sap-unavailable.forbidden_violations.intervention` | 0 |
| `case.build-rwe-sap-unavailable.stability.control` | stable-pass |
| `case.build-rwe-sap-unavailable.stability.intervention` | stable-pass |

## Forbidden-rule guardrail

Forbidden-rule violations are reported separately and participate in direction classification.
| Field | Value |
|---|---|
| `forbidden_violations.control` | 0 |
| `forbidden_violations.intervention` | 0 |

## Limitations and next evidence step

These results concern only public synthetic prompts and deterministic contract checks.
Model metadata and the execution attestation are externally reported and are not provider-verified.
Deterministic rules do not measure all semantic quality.
No representative user performed a usability task.
No clinical-validity, causal-validity, patient-outcome, or deployment-ready claim follows from this report.
`positive-signal` is not `human-effective` or `evaluation-green`.
The next evidence step is optional independent depth review and, under separate authorization, representative-user evaluation.
