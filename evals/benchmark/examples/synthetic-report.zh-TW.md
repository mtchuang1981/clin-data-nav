# 公開模擬基準測試報告—合成契約範例

## 識別資訊與範圍

本報告僅包含基準測試彙總事實；執行識別資訊用於重現，不代表已獨立驗證。
| 欄位 | 值 |
|---|---|
| `benchmark_id` | public-simulation-v0-5-0 |
| `schema_version` | 1 |
| `status` | benchmark-observed |
| `direction` | positive-signal |
| `synthetic_example` | true |
| `plan_sha256` | cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc |
| `catalog_sha256` | c1e34accddf2f2937ec82810cae7871d0006ad2c26d3b4a7d9de7e17caaab670 |
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

## 整體結果

狀態與方向是兩個分開的預先指定分類。
| 欄位 | 值 |
|---|---|
| `overall.control_pass_rate` | 0.666667 |
| `overall.control_passes` | 24 |
| `overall.difference` | 0.333333 |
| `overall.intervention_pass_rate` | 1.000000 |
| `overall.intervention_passes` | 36 |
| `overall.pairs` | 36 |

## 配對變化

每個計數均比較同一個案與重複次數下的對照及介入結果。
| 欄位 | 值 |
|---|---|
| `paired_counts.both_fail` | 0 |
| `paired_counts.both_pass` | 24 |
| `paired_counts.improved` | 12 |
| `paired_counts.worsened` | 0 |

## 輸出深度分層

分層依已驗證摘要中的標準輸出深度順序呈現。
| 欄位 | 值 |
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

## 個案穩定性

通過次數與穩定性標籤涵蓋三次重複，並依標準個案順序呈現。
| 欄位 | 值 |
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

## 禁止規則護欄

禁止規則違反數獨立呈現，並參與方向分類。
| 欄位 | 值 |
|---|---|
| `forbidden_violations.control` | 0 |
| `forbidden_violations.intervention` | 0 |

## 限制與下一步證據

這些結果僅涉及公開合成提示與確定性契約檢查。
模型中繼資料與執行證明均由外部回報，未經提供者驗證。
確定性規則無法衡量所有語意品質。
沒有具代表性的使用者執行可用性任務。
本報告不能推導出臨床效度、因果效度、病人結果或可部署性的主張。
`positive-signal` 不代表 `human-effective` 或 `evaluation-green`。
下一步證據是選用的獨立深度審查，以及另行取得授權後的代表性使用者評估。
