"""Render deterministic bilingual effectiveness aggregate reports."""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
if __package__ in {None, ""}:
    sys.path.insert(0, str(ROOT))

from scripts.effectiveness_analysis import (
    CONTROLLED_COUNT_KEYS,
    CONTROLLED_REVIEW_KEYS,
    CONTROLLED_REVIEW_STATUSES,
    PROTOCOL_DEVIATION_CATEGORIES,
    STUDY_LIMITATION_CATEGORIES,
)


LANGUAGES = ("en", "zh-TW")
REPORT_ERROR = "effectiveness report rendering failed\n"
REPORT_RECOVERY_ERROR = (
    "effectiveness report recovery required; bilingual backups preserved"
)

TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "study_id",
        "synthetic_example",
        "protocol_commit",
        "environment",
        "minimum_practical_difference",
        "participant_flow",
        "primary",
        "safety",
        "secondary",
        "agreement",
        "power_scenarios",
        "protocol_deviations",
        "limitations",
    }
)
ENVIRONMENT_KEYS = frozenset(
    {
        "skill_version",
        "skill_commit",
        "codex_surface",
        "model",
        "reasoning_effort",
        "service_tier",
        "python_version",
        "platform",
        "study_started_at",
        "study_ended_at",
        "task_commitment_sha256",
        "task_commitment_verified",
        "assignment_version",
        "bootstrap_seed",
        "bootstrap_resamples",
    }
)
PARTICIPANT_FLOW_KEYS = frozenset(
    {
        "assigned",
        "completed",
        "beginners",
        "professionals",
        "abandonments",
        "timeouts",
        "technical_failures",
        "primary_complete_pairs",
        "interpretation_status",
    }
)
PRIMARY_KEYS = frozenset(
    {
        "control_successes",
        "control_total",
        "control_success_rate",
        "intervention_successes",
        "intervention_total",
        "intervention_success_rate",
        "paired_risk_difference",
        "confidence_interval",
        "complete_pairs",
        "paired_distribution",
    }
)
PAIRED_DISTRIBUTION_KEYS = frozenset(
    {"minus_one", "minus_half", "zero", "plus_half", "plus_one"}
)
SAFETY_KEYS = frozenset({"events", "total", "rate", "exact_interval"})
SECONDARY_KEYS = frozenset(
    {
        "paired_time_seconds",
        "paired_quality_points",
        "paired_nasa_tlx_points",
        "paired_confidence_change",
        "paired_understanding_change",
        "intervention_sus",
        "timeout_rate",
        "technical_failure_rate",
        "criterion_results",
    }
)
PAIRED_METRIC_KEYS = frozenset(
    {"complete_pairs", "mean_difference", "median_difference", "confidence_interval"}
)
CRITERION_KEYS = frozenset(
    {
        "criterion_id",
        "control_met",
        "control_applicable",
        "control_rate",
        "intervention_met",
        "intervention_applicable",
        "intervention_rate",
    }
)
AGREEMENT_KEYS = frozenset(
    {
        "answers_rated",
        "raw_binary_agreement",
        "binary_kappa",
        "raw_ordinal_agreement",
        "ordinal_weighted_kappa",
        "critical_disagreements",
        "adjudications",
        "status",
    }
)
POWER_KEYS = frozenset(
    {
        "scenario_id",
        "minimum_difference",
        "control_rate",
        "paired_discordance",
        "attrition_rate",
        "two_sided_alpha",
        "target_power",
        "analysis_method",
        "required_complete_pairs",
        "required_recruits",
        "status",
    }
)


def render_report(summary: dict, language: str) -> str:
    """Render one aggregate report after closed-schema validation."""
    if language not in LANGUAGES:
        raise ValueError("report language must be en or zh-TW")
    _validate_summary(summary)
    if language == "en":
        return _render_english(summary)
    return _render_traditional_chinese(summary)


def _render_english(summary: dict) -> str:
    environment = summary["environment"]
    flow = summary["participant_flow"]
    overall = summary["primary"]["overall"]
    beginner = summary["primary"]["beginner"]
    professional = summary["primary"]["professional"]
    conservative = summary["primary"]["conservative_missingness"]
    safety = summary["safety"]
    secondary = summary["secondary"]
    agreement = summary["agreement"]
    example_label = " — synthetic example" if summary["synthetic_example"] else ""
    interval_article = "an illustrative" if summary["synthetic_example"] else "a"
    lines = [
        f"# Effectiveness pilot aggregate report{example_label}",
        "",
        "## Executive summary",
        "",
        (
            "This exploratory product evaluation summarizes safety-gated task "
            "performance. It does not prove clinical validity, causal validity, or "
            "patient-outcome validity."
        ),
        "Its objective is to compare the same model and surface with and without the pinned Skill.",
        _synthetic_notice(summary, "en"),
        "",
        "## Methods",
        "",
        f"- Protocol commit: `{summary['protocol_commit']}`.",
        f"- Study period: {environment['study_started_at']} to {environment['study_ended_at']}.",
        (
            f"- Model/Skill environment: {environment['codex_surface']}; model "
            f"{environment['model']}; reasoning {environment['reasoning_effort']}; "
            f"service tier {environment['service_tier']}; Skill "
            f"{environment['skill_version']} at `{environment['skill_commit']}`; "
            f"Python {environment['python_version']} on {environment['platform']}."
        ),
        f"- Assignment version: {environment['assignment_version']}.",
        (
            f"- Task commitment: {_verified(environment['task_commitment_verified'], 'en')} "
            f"(`{environment['task_commitment_sha256']}`)."
        ),
        (
            f"- Participant-cluster bootstrap: seed {environment['bootstrap_seed']}, "
            f"{environment['bootstrap_resamples']} resamples; the same method provides "
            "95% intervals for continuous paired secondary outcomes."
        ),
        "- Quality criteria are secondary and never determine primary task success; a zero applicable denominator is reported as not estimable.",
        "",
        "## Participant flow",
        "",
        (
            f"Assigned {flow['assigned']} participants; completed {flow['completed']}; "
            f"{flow['beginners']} beginners and {flow['professionals']} professionals. "
            f"Abandonments: {flow['abandonments']}; timeouts: {flow['timeouts']}; "
            f"technical failures: {flow['technical_failures']}. Primary complete pairs: "
            f"{flow['primary_complete_pairs']}. Interpretation status: "
            f"`{flow['interpretation_status']}`."
        ),
        "",
        "## Primary outcome",
        "",
        (
            f"Control: {overall['control_successes']}/{overall['control_total']} "
            f"({_pct(overall['control_success_rate'], 1)}); intervention: "
            f"{overall['intervention_successes']}/{overall['intervention_total']} "
            f"({_pct(overall['intervention_success_rate'], 1)}). The paired risk "
            f"difference was {_pct(overall['paired_risk_difference'], 1)} "
            f"(intervention minus control), with {interval_article} 95% interval of "
            f"[{_pct(overall['confidence_interval'][0], 1)}, "
            f"{_pct(overall['confidence_interval'][1], 1)}], based on "
            f"{overall['complete_pairs']} complete pairs."
        ),
        (
            "The predeclared minimum practical difference is an absolute "
            f"{_points(summary['minimum_practical_difference'], 1)} (the 20-point "
            "minimum difference); it is not a "
            "relative improvement and the pilot point estimate is not used alone for power."
        ),
        "",
        "## Stratified results",
        "",
        _stratum_line("Beginners", flow["beginners"], beginner),
        _stratum_line("Professionals", flow["professionals"], professional),
        "These strata are exploratory and are not powered confirmatory comparisons.",
        "",
        "## Safety",
        "",
        _safety_line("Control", safety["control"]),
        _safety_line("Intervention", safety["intervention"]),
        "Critical safety events are reported separately and cannot be offset by quality or speed.",
        "",
        "## Secondary outcomes",
        "",
        _secondary_lines(secondary, "en"),
        "",
        "### Criterion results",
        "",
        "| Criterion | Control met/applicable | Control rate | Intervention met/applicable | Intervention rate |",
        "|---|---:|---:|---:|---:|",
        *[
            (
                f"| {row['criterion_id']} | {row['control_met']}/{row['control_applicable']} "
                f"| {_criterion_rate(row['control_rate'], 'en')} | "
                f"{row['intervention_met']}/{row['intervention_applicable']} | "
                f"{_criterion_rate(row['intervention_rate'], 'en')} |"
            )
            for row in secondary["criterion_results"]
        ],
        "",
        "## Rater agreement",
        "",
        (
            f"Original pre-adjudication ratings covered {agreement['answers_rated']} answers. "
            f"Raw binary agreement was {_pct(agreement['raw_binary_agreement'], 1)} "
            f"(Cohen kappa: {_kappa(agreement['binary_kappa'], 'en')}); raw ordinal agreement "
            f"was {_pct(agreement['raw_ordinal_agreement'], 1)} (linear weighted kappa: "
            f"{_kappa(agreement['ordinal_weighted_kappa'], 'en')}). Critical disagreements: "
            f"{agreement['critical_disagreements']}; adjudications: "
            f"{agreement['adjudications']}; pre-unlock status: `{agreement['status']}`."
        ),
        "",
        "## Missing data and sensitivity",
        "",
        (
            f"The complete-case primary analysis used {overall['complete_pairs']} participant "
            f"pairs. The conservative missingness analysis used {conservative['complete_pairs']} "
            f"pairs and estimated {_pct(conservative['paired_risk_difference'], 1)} with a "
            f"95% interval [{_pct(conservative['confidence_interval'][0], 1)}, "
            f"{_pct(conservative['confidence_interval'][1], 1)}]."
        ),
        "",
        "## Power-analysis scenarios",
        "",
        "| Scenario | Control rate | Paired discordance | Attrition | Alpha | Target power | Method | Required complete pairs | Required recruits | Status |",
        "|---|---:|---:|---:|---:|---:|---|---:|---:|---|",
        *[_power_row(row) for row in summary["power_scenarios"]],
        "",
        (
            f"Every scenario uses the predeclared {_points(summary['minimum_practical_difference'], 1)} "
            "plus conservative discordance, heterogeneity, failure, and attrition inputs; "
            "no confirmatory sample size is invented before the post-pilot design decision."
        ),
        "",
        "## Protocol deviations",
        "",
        *_controlled_review_lines(
            summary["protocol_deviations"], "protocol_deviations", "en"
        ),
        "",
        "## Limitations",
        "",
        *_controlled_review_lines(summary["limitations"], "limitations", "en"),
        "- Negative and neutral findings must use this same structure and must not be suppressed.",
        "",
    ]
    return "\n".join(_flatten(lines))


def _render_traditional_chinese(summary: dict) -> str:
    environment = summary["environment"]
    flow = summary["participant_flow"]
    overall = summary["primary"]["overall"]
    beginner = summary["primary"]["beginner"]
    professional = summary["primary"]["professional"]
    conservative = summary["primary"]["conservative_missingness"]
    safety = summary["safety"]
    secondary = summary["secondary"]
    agreement = summary["agreement"]
    example_label = "—合成範例" if summary["synthetic_example"] else ""
    interval_label = "示例性 95%" if summary["synthetic_example"] else "95%"
    lines = [
        f"# 效果評估先導研究彙總報告{example_label}",
        "",
        "## 摘要",
        "",
        "本探索性產品評估彙整通過安全門檻的任務表現；不能證明臨床效度、因果效度或病人結果效度。",
        "目標是在相同模型與操作介面下，比較有無使用固定版本 Skill 的差異。",
        _synthetic_notice(summary, "zh-TW"),
        "",
        "## 方法",
        "",
        f"- 研究規格 commit：`{summary['protocol_commit']}`。",
        f"- 研究期間：{environment['study_started_at']} 至 {environment['study_ended_at']}。",
        (
            f"- 模型／Skill 環境：{environment['codex_surface']}；模型 "
            f"{environment['model']}；推理強度 {environment['reasoning_effort']}；服務層級 "
            f"{environment['service_tier']}；Skill {environment['skill_version']}（commit "
            f"`{environment['skill_commit']}`）；{environment['platform']} 上的 Python "
            f"{environment['python_version']}。"
        ),
        f"- 分派版本：{environment['assignment_version']}。",
        (
            f"- 任務承諾：{_verified(environment['task_commitment_verified'], 'zh-TW')} "
            f"（`{environment['task_commitment_sha256']}`）。"
        ),
        (
            f"- 參與者叢集 bootstrap：seed {environment['bootstrap_seed']}、"
            f"{environment['bootstrap_resamples']} 次重抽；連續型配對次要結果的 95% 區間採相同方法。"
        ),
        "- 品質準則屬於次要結果，絕不決定主要任務成功；適用分母為零時標示為無法估計。",
        "",
        "## 參與者流程",
        "",
        (
            f"分派 {flow['assigned']} 人；完成 {flow['completed']} 人；初學者 "
            f"{flow['beginners']} 人、專業者 {flow['professionals']} 人。中途退出："
            f"{flow['abandonments']}；逾時：{flow['timeouts']}；技術失敗："
            f"{flow['technical_failures']}。主要分析完整配對：{flow['primary_complete_pairs']}。"
            f"解讀狀態：`{flow['interpretation_status']}`。"
        ),
        "",
        "## 主要結果",
        "",
        (
            f"對照組：{overall['control_successes']}/{overall['control_total']} "
            f"（{_pct(overall['control_success_rate'], 1)}）；介入組："
            f"{overall['intervention_successes']}/{overall['intervention_total']} "
            f"（{_pct(overall['intervention_success_rate'], 1)}）。配對風險差為 "
            f"{_pct(overall['paired_risk_difference'], 1)}（介入減對照），{interval_label} 區間為 "
            f"[{_pct(overall['confidence_interval'][0], 1)}, "
            f"{_pct(overall['confidence_interval'][1], 1)}]，完整配對 "
            f"{overall['complete_pairs']} 人。"
        ),
        (
            f"預先指定的最小實務差異為絕對 {_points_zh(summary['minimum_practical_difference'], 1)}；"
            "不是相對改善，也不會只用先導研究點估計進行檢定力規劃。"
        ),
        "",
        "## 分層結果",
        "",
        _stratum_line_zh("初學者", flow["beginners"], beginner),
        _stratum_line_zh("專業者", flow["professionals"], professional),
        "兩個分層皆屬探索性，不能視為具確認性檢定力的比較。",
        "",
        "## 安全性",
        "",
        _safety_line_zh("對照組", safety["control"]),
        _safety_line_zh("介入組", safety["intervention"]),
        "重大安全事件獨立呈現，不得由品質或速度抵銷。",
        "",
        "## 次要結果",
        "",
        _secondary_lines(secondary, "zh-TW"),
        "",
        "### 評分準則結果",
        "",
        "| 準則 | 對照達成／適用 | 對照率 | 介入達成／適用 | 介入率 |",
        "|---|---:|---:|---:|---:|",
        *[
            (
                f"| {row['criterion_id']} | {row['control_met']}/{row['control_applicable']} "
                f"| {_criterion_rate(row['control_rate'], 'zh-TW')} | "
                f"{row['intervention_met']}/{row['intervention_applicable']} | "
                f"{_criterion_rate(row['intervention_rate'], 'zh-TW')} |"
            )
            for row in secondary["criterion_results"]
        ],
        "",
        "## 評分者一致性",
        "",
        (
            f"原始裁定前評分涵蓋 {agreement['answers_rated']} 份答案。二元原始一致率為 "
            f"{_pct(agreement['raw_binary_agreement'], 1)}（Cohen kappa："
            f"{_kappa(agreement['binary_kappa'], 'zh-TW')}）；序位原始一致率為 "
            f"{_pct(agreement['raw_ordinal_agreement'], 1)}（線性加權 kappa："
            f"{_kappa(agreement['ordinal_weighted_kappa'], 'zh-TW')}）。重大事件歧見："
            f"{agreement['critical_disagreements']}；裁定：{agreement['adjudications']}；"
            f"解盲前狀態：`{agreement['status']}`。"
        ),
        "",
        "## 缺失資料與敏感度分析",
        "",
        (
            f"完整案例主要分析使用 {overall['complete_pairs']} 個參與者配對。保守缺失值分析使用 "
            f"{conservative['complete_pairs']} 個配對，估計值為 "
            f"{_pct(conservative['paired_risk_difference'], 1)}，95% 區間 "
            f"[{_pct(conservative['confidence_interval'][0], 1)}, "
            f"{_pct(conservative['confidence_interval'][1], 1)}]。"
        ),
        "",
        "## 樣本數情境",
        "",
        "| 情境 | 對照率 | 配對不一致率 | 流失率 | alpha | 目標檢定力 | 方法 | 所需完整配對 | 所需招募 | 狀態 |",
        "|---|---:|---:|---:|---:|---:|---|---:|---:|---|",
        *[_power_row(row) for row in summary["power_scenarios"]],
        "",
        (
            f"所有情境均使用預先指定的 {_points_zh(summary['minimum_practical_difference'], 1)}，"
            "並納入保守的配對不一致、異質性、失敗與流失假設；在先導研究後的設計決策前，"
            "不虛構確認性樣本數。"
        ),
        "",
        "## 規格偏離",
        "",
        *_controlled_review_lines(
            summary["protocol_deviations"], "protocol_deviations", "zh-TW"
        ),
        "",
        "## 限制",
        "",
        *_controlled_review_lines(summary["limitations"], "limitations", "zh-TW"),
        "- 負向或中性結果必須使用相同結構發布，不得隱匿。",
        "",
    ]
    return "\n".join(_flatten(lines))


def _validate_summary(summary: object) -> None:
    if not isinstance(summary, dict) or set(summary) != TOP_LEVEL_KEYS:
        raise ValueError("summary must match the closed aggregate schema")
    if summary.get("schema_version") != "1":
        raise ValueError("summary schema_version must be 1")
    _safe_text(summary.get("study_id"), "study_id")
    _safe_text(summary.get("protocol_commit"), "protocol_commit")
    if type(summary.get("synthetic_example")) is not bool:
        raise ValueError("synthetic_example must be boolean")
    _finite(summary.get("minimum_practical_difference"), "minimum practical difference")
    if summary["minimum_practical_difference"] != 0.20:
        raise ValueError("minimum practical difference must be 0.20")

    environment = _closed_mapping(summary.get("environment"), ENVIRONMENT_KEYS, "environment")
    for key in ENVIRONMENT_KEYS - {
        "task_commitment_verified",
        "bootstrap_seed",
        "bootstrap_resamples",
    }:
        _safe_text(environment.get(key), f"environment {key}")
    if type(environment.get("task_commitment_verified")) is not bool:
        raise ValueError("task commitment verification state must be boolean")
    _integer(environment.get("bootstrap_seed"), "bootstrap seed")
    _integer(environment.get("bootstrap_resamples"), "bootstrap resamples")

    flow = _closed_mapping(summary.get("participant_flow"), PARTICIPANT_FLOW_KEYS, "participant flow")
    for key in PARTICIPANT_FLOW_KEYS - {"interpretation_status"}:
        _integer(flow.get(key), f"participant flow {key}", minimum=0)
    _safe_text(flow.get("interpretation_status"), "interpretation status")
    if (
        flow["assigned"] != flow["beginners"] + flow["professionals"]
        or flow["completed"] > flow["assigned"]
        or flow["primary_complete_pairs"] > flow["assigned"]
    ):
        raise ValueError("participant flow denominators are inconsistent")

    primary = _closed_mapping(
        summary.get("primary"),
        frozenset({"overall", "beginner", "professional", "conservative_missingness"}),
        "primary",
    )
    for label, result in primary.items():
        _validate_primary(result, f"primary {label}")
    safety = _closed_mapping(
        summary.get("safety"), frozenset({"control", "intervention"}), "safety"
    )
    for label, result in safety.items():
        row = _closed_mapping(result, SAFETY_KEYS, f"safety {label}")
        _integer(row.get("events"), f"safety {label} events", minimum=0)
        _integer(row.get("total"), f"safety {label} total", minimum=1)
        _probability(row.get("rate"), f"safety {label} rate")
        _interval(row.get("exact_interval"), f"safety {label} interval")
        if row["events"] > row["total"] or not math.isclose(
            row["rate"], row["events"] / row["total"], abs_tol=1e-12
        ):
            raise ValueError(f"safety {label} rate is inconsistent")

    secondary = _closed_mapping(summary.get("secondary"), SECONDARY_KEYS, "secondary")
    for key in (
        "paired_time_seconds",
        "paired_quality_points",
        "paired_nasa_tlx_points",
        "paired_confidence_change",
        "paired_understanding_change",
    ):
        row = _closed_mapping(secondary.get(key), PAIRED_METRIC_KEYS, key)
        _integer(row.get("complete_pairs"), f"{key} complete pairs", minimum=1)
        _finite(row.get("mean_difference"), f"{key} mean")
        _finite(row.get("median_difference"), f"{key} median")
        _interval(row.get("confidence_interval"), f"{key} interval")
    sus = _closed_mapping(
        secondary.get("intervention_sus"),
        frozenset({"participants", "mean", "median"}),
        "intervention SUS",
    )
    _integer(sus.get("participants"), "SUS participants", minimum=1)
    _finite(sus.get("mean"), "SUS mean")
    _finite(sus.get("median"), "SUS median")
    for key in ("timeout_rate", "technical_failure_rate"):
        row = _closed_mapping(
            secondary.get(key), frozenset({"events", "assigned_tasks", "rate"}), key
        )
        _integer(row.get("events"), f"{key} events", minimum=0)
        _integer(row.get("assigned_tasks"), f"{key} assigned tasks", minimum=1)
        _probability(row.get("rate"), f"{key} rate")
        if row["events"] > row["assigned_tasks"] or not math.isclose(
            row["rate"], row["events"] / row["assigned_tasks"], abs_tol=1e-12
        ):
            raise ValueError(f"{key} rate is inconsistent")
    criteria = secondary.get("criterion_results")
    if not isinstance(criteria, list) or not criteria:
        raise ValueError("criterion results must be a non-empty list")
    for index, criterion in enumerate(criteria):
        row = _closed_mapping(criterion, CRITERION_KEYS, f"criterion {index}")
        _safe_text(row.get("criterion_id"), f"criterion {index} id")
        for key in (
            "control_met",
            "control_applicable",
            "intervention_met",
            "intervention_applicable",
        ):
            _integer(row.get(key), f"criterion {index} {key}", minimum=0)
        if (
            row["control_met"] > row["control_applicable"]
            or row["intervention_met"] > row["intervention_applicable"]
        ):
            raise ValueError(f"criterion {index} rates are inconsistent")
        _validate_optional_rate(
            row["control_rate"],
            row["control_met"],
            row["control_applicable"],
            f"criterion {index} control rate",
        )
        _validate_optional_rate(
            row["intervention_rate"],
            row["intervention_met"],
            row["intervention_applicable"],
            f"criterion {index} intervention rate",
        )

    agreement = _closed_mapping(summary.get("agreement"), AGREEMENT_KEYS, "agreement")
    for key in ("answers_rated", "critical_disagreements", "adjudications"):
        _integer(agreement.get(key), f"agreement {key}", minimum=0)
    for key in ("raw_binary_agreement", "raw_ordinal_agreement"):
        _probability(agreement.get(key), f"agreement {key}")
    for key in ("binary_kappa", "ordinal_weighted_kappa"):
        value = agreement.get(key)
        if value is not None:
            _finite(value, f"agreement {key}")
            if not -1.0 <= value <= 1.0:
                raise ValueError(
                    f"agreement {key} must be between -1 and 1"
                )
    if agreement.get("status") not in {
        "eligible-for-locked-unlock",
        "recalibrate-and-rescore-before-unlock",
    }:
        raise ValueError("agreement status is invalid")
    if (
        agreement["answers_rated"] <= 0
        or agreement["critical_disagreements"] > agreement["answers_rated"]
        or agreement["adjudications"] > agreement["answers_rated"]
    ):
        raise ValueError("agreement denominators are inconsistent")
    eligible = agreement["raw_binary_agreement"] >= 0.80 and all(
        agreement[key] is None or agreement[key] >= 0.60
        for key in ("binary_kappa", "ordinal_weighted_kappa")
    )
    expected_status = (
        "eligible-for-locked-unlock"
        if eligible
        else "recalibrate-and-rescore-before-unlock"
    )
    if agreement["status"] != expected_status:
        raise ValueError("agreement status is inconsistent with recomputed eligibility")

    scenarios = summary.get("power_scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError("power scenarios must be a non-empty list")
    for index, scenario in enumerate(scenarios):
        row = _closed_mapping(scenario, POWER_KEYS, f"power scenario {index}")
        _safe_text(row.get("scenario_id"), f"power scenario {index} id")
        _safe_text(row.get("analysis_method"), f"power scenario {index} method")
        for key in (
            "minimum_difference",
            "control_rate",
            "paired_discordance",
            "attrition_rate",
            "two_sided_alpha",
            "target_power",
        ):
            _probability(row.get(key), f"power scenario {index} {key}")
        if row["minimum_difference"] != summary["minimum_practical_difference"]:
            raise ValueError("power scenario minimum difference is inconsistent")
        if (
            row.get("status") != "deferred-until-post-pilot"
            or row.get("required_complete_pairs") is not None
            or row.get("required_recruits") is not None
        ):
            raise ValueError("pre-pilot power scenarios must remain explicitly deferred")
    _validate_controlled_summary(
        summary.get("protocol_deviations"),
        "protocol deviations",
        PROTOCOL_DEVIATION_CATEGORIES,
    )
    _validate_controlled_summary(
        summary.get("limitations"),
        "limitations",
        STUDY_LIMITATION_CATEGORIES,
    )


def _validate_primary(value: object, label: str) -> None:
    row = _closed_mapping(value, PRIMARY_KEYS, label)
    for key in (
        "control_successes",
        "control_total",
        "intervention_successes",
        "intervention_total",
        "complete_pairs",
    ):
        _integer(row.get(key), f"{label} {key}", minimum=0)
    for key in (
        "control_success_rate",
        "intervention_success_rate",
    ):
        _probability(row.get(key), f"{label} {key}")
    _finite(row.get("paired_risk_difference"), f"{label} paired risk difference")
    _interval(row.get("confidence_interval"), f"{label} interval")
    distribution = _closed_mapping(
        row.get("paired_distribution"), PAIRED_DISTRIBUTION_KEYS, f"{label} distribution"
    )
    for key in PAIRED_DISTRIBUTION_KEYS:
        _integer(distribution.get(key), f"{label} distribution {key}", minimum=0)
    if (
        row["control_total"] <= 0
        or row["intervention_total"] <= 0
        or row["complete_pairs"] <= 0
        or row["control_successes"] > row["control_total"]
        or row["intervention_successes"] > row["intervention_total"]
        or not math.isclose(
            row["control_success_rate"],
            row["control_successes"] / row["control_total"],
            abs_tol=1e-12,
        )
        or not math.isclose(
            row["intervention_success_rate"],
            row["intervention_successes"] / row["intervention_total"],
            abs_tol=1e-12,
        )
        or sum(distribution.values()) != row["complete_pairs"]
    ):
        raise ValueError(f"{label} denominators are inconsistent")
    condition_difference = (
        row["intervention_success_rate"] - row["control_success_rate"]
    )
    distribution_difference = (
        -distribution["minus_one"]
        - 0.5 * distribution["minus_half"]
        + 0.5 * distribution["plus_half"]
        + distribution["plus_one"]
    ) / row["complete_pairs"]
    if not (
        math.isclose(
            row["paired_risk_difference"], condition_difference, abs_tol=1e-12
        )
        and math.isclose(
            row["paired_risk_difference"], distribution_difference, abs_tol=1e-12
        )
    ):
        raise ValueError(f"{label} paired risk difference is inconsistent")


def _secondary_lines(secondary: dict, language: str) -> list[str]:
    labels = (
        ("paired_time_seconds", "Time (seconds)", "時間（秒）"),
        ("paired_quality_points", "Quality (points)", "品質（分）"),
        ("paired_nasa_tlx_points", "NASA-TLX (points)", "NASA-TLX（分）"),
        ("paired_confidence_change", "Confidence change", "信心變化"),
        ("paired_understanding_change", "Understanding change", "理解程度變化"),
    )
    rows = []
    for key, english, chinese in labels:
        value = secondary[key]
        label = english if language == "en" else chinese
        if language == "en":
            rows.append(
                f"- {label}: {value['complete_pairs']} complete pairs; mean difference "
                f"{_signed(value['mean_difference'])}; median difference "
                f"{_signed(value['median_difference'])}; 95% interval "
                f"[{_signed(value['confidence_interval'][0])}, "
                f"{_signed(value['confidence_interval'][1])}]."
            )
        else:
            rows.append(
                f"- {label}：{value['complete_pairs']} 個完整配對；平均差異 "
                f"{_signed(value['mean_difference'])}；中位數差異 "
                f"{_signed(value['median_difference'])}；95% 區間 "
                f"[{_signed(value['confidence_interval'][0])}, "
                f"{_signed(value['confidence_interval'][1])}]。"
            )
    sus = secondary["intervention_sus"]
    timeout = secondary["timeout_rate"]
    technical = secondary["technical_failure_rate"]
    if language == "en":
        rows.extend(
            [
                f"- Intervention SUS: {sus['participants']} participants; mean {_one(sus['mean'])}; median {_one(sus['median'])}.",
                f"- Timeout rate: {timeout['events']}/{timeout['assigned_tasks']} ({_pct(timeout['rate'], 1)}).",
                f"- Technical-failure rate: {technical['events']}/{technical['assigned_tasks']} ({_pct(technical['rate'], 1)}).",
            ]
        )
    else:
        rows.extend(
            [
                f"- 介入條件 SUS：{sus['participants']} 人；平均 {_one(sus['mean'])}；中位數 {_one(sus['median'])}。",
                f"- 逾時率：{timeout['events']}/{timeout['assigned_tasks']}（{_pct(timeout['rate'], 1)}）。",
                f"- 技術失敗率：{technical['events']}/{technical['assigned_tasks']}（{_pct(technical['rate'], 1)}）。",
            ]
        )
    return rows


def _stratum_line(label: str, participants: int, result: dict) -> str:
    return (
        f"- {label}: {participants} participants; control "
        f"{result['control_successes']}/{result['control_total']} "
        f"({_pct(result['control_success_rate'], 1)}), intervention "
        f"{result['intervention_successes']}/{result['intervention_total']} "
        f"({_pct(result['intervention_success_rate'], 1)}), paired difference "
        f"{_points(result['paired_risk_difference'], 2)}."
    )


def _stratum_line_zh(label: str, participants: int, result: dict) -> str:
    return (
        f"- {label}：{participants} 人；對照 {result['control_successes']}/"
        f"{result['control_total']}（{_pct(result['control_success_rate'], 1)}），介入 "
        f"{result['intervention_successes']}/{result['intervention_total']}"
        f"（{_pct(result['intervention_success_rate'], 1)}），配對差異 "
        f"{_points_zh(result['paired_risk_difference'], 2)}。"
    )


def _safety_line(label: str, result: dict) -> str:
    return (
        f"- {label}: {result['events']}/{result['total']} "
        f"({_pct(result['rate'], 1)}); exact 95% interval "
        f"[{_pct(result['exact_interval'][0], 1)}, {_pct(result['exact_interval'][1], 1)}]."
    )


def _safety_line_zh(label: str, result: dict) -> str:
    return (
        f"- {label}：{result['events']}/{result['total']}（{_pct(result['rate'], 1)}）；"
        f"精確 95% 區間 [{_pct(result['exact_interval'][0], 1)}, "
        f"{_pct(result['exact_interval'][1], 1)}]。"
    )


def _power_row(row: dict) -> str:
    return (
        f"| {row['scenario_id']} | {_pct(row['control_rate'], 1)} | "
        f"{_pct(row['paired_discordance'], 1)} | {_pct(row['attrition_rate'], 1)} | "
        f"{row['two_sided_alpha']:.2f} | {_pct(row['target_power'], 1)} | "
        f"{row['analysis_method']} | {row['status']} | {row['status']} | {row['status']} |"
    )


def _synthetic_notice(summary: dict, language: str) -> str:
    if summary["synthetic_example"]:
        return (
            "This is an illustrative synthetic example, not observed pilot evidence."
            if language == "en"
            else "這是示例性合成範例，不是實際觀察到的先導研究證據。"
        )
    return (
        "This report contains aggregate results only."
        if language == "en"
        else "本報告僅包含彙總結果。"
    )


CONTROLLED_CATEGORY_LABELS = {
    "en": {
        "eligibility": "Eligibility",
        "assignment": "Assignment",
        "orientation": "Orientation",
        "fresh-conversation": "Fresh conversation",
        "time-limit": "Time limit",
        "rest-period": "Rest period",
        "environment-consistency": "Environment consistency",
        "task-pack-integrity": "Task-pack integrity",
        "rating-procedure": "Rating procedure",
        "data-lock-or-unlock": "Data lock or unlock",
        "small-exploratory-sample": "Small exploratory sample",
        "synthetic-task-generalizability": "Synthetic-task generalizability",
        "controlled-environment-generalizability": "Controlled-environment generalizability",
        "participant-completion-below-threshold": "Participant completion below threshold",
        "technical-failure": "Technical failure",
        "task-pack-leakage": "Task-pack leakage",
        "environment-batch-change": "Environment batch change",
        "low-rater-agreement": "Low rater agreement",
        "protocol-deviation-present": "Protocol deviation present",
        "no-clinical-validity-inference": "No clinical-validity inference",
    },
    "zh-TW": {
        "eligibility": "納入條件",
        "assignment": "分派",
        "orientation": "導覽",
        "fresh-conversation": "全新對話",
        "time-limit": "時限",
        "rest-period": "休息期間",
        "environment-consistency": "環境一致性",
        "task-pack-integrity": "任務包完整性",
        "rating-procedure": "評分程序",
        "data-lock-or-unlock": "資料鎖定或解盲",
        "small-exploratory-sample": "小型探索性樣本",
        "synthetic-task-generalizability": "合成任務推廣性",
        "controlled-environment-generalizability": "受控環境推廣性",
        "participant-completion-below-threshold": "參與者完成數低於門檻",
        "technical-failure": "技術失敗",
        "task-pack-leakage": "任務包外洩",
        "environment-batch-change": "環境批次變更",
        "low-rater-agreement": "評分者一致性偏低",
        "protocol-deviation-present": "存在規格偏離",
        "no-clinical-validity-inference": "不得推論臨床效度",
    },
}


def _controlled_review_lines(value: dict, kind: str, language: str) -> list[str]:
    status = value["review_status"]
    items = value["items"]
    if not items:
        if language == "en":
            subject = (
                "no protocol deviations"
                if kind == "protocol_deviations"
                else "no controlled limitations"
            )
            return [f"Review status: `reviewed-none`; {subject} were recorded."]
        subject = "未記錄規格偏離" if kind == "protocol_deviations" else "未記錄受控限制"
        return [f"審查狀態：`reviewed-none`；{subject}。"]
    prefix = (
        f"Review status: `{status}`."
        if language == "en"
        else f"審查狀態：`{status}`。"
    )
    labels = CONTROLLED_CATEGORY_LABELS[language]
    punctuation = "." if language == "en" else "。"
    separator = ": " if language == "en" else "："
    return [
        prefix,
        *[
            f"- {labels[item['category_id']]}{separator}{item['count']}{punctuation}"
            for item in items
        ],
    ]


def _verified(value: bool, language: str) -> str:
    if language == "en":
        return "verified" if value else "not verified"
    return "已驗證" if value else "未驗證"


def _flatten(values: list[object]) -> list[str]:
    flattened: list[str] = []
    for value in values:
        if isinstance(value, list):
            flattened.extend(str(item) for item in value)
        else:
            flattened.append(str(value))
    return flattened


def _closed_mapping(value: object, keys: frozenset[str], label: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"{label} must match its closed schema")
    return value


def _validate_controlled_summary(
    value: object, label: str, categories: tuple[str, ...]
) -> None:
    review = _closed_mapping(value, CONTROLLED_REVIEW_KEYS, label)
    status = review.get("review_status")
    if status not in CONTROLLED_REVIEW_STATUSES:
        raise ValueError(f"{label} review status is invalid")
    items = review.get("items")
    if not isinstance(items, list):
        raise ValueError(f"{label} items must be a list")
    if status == "reviewed-none" and items:
        raise ValueError(f"{label} reviewed-none requires no items")
    if status == "reviewed-with-findings" and not items:
        raise ValueError(f"{label} reviewed-with-findings requires items")
    positions = {category_id: index for index, category_id in enumerate(categories)}
    observed: list[str] = []
    for index, item in enumerate(items):
        row = _closed_mapping(item, CONTROLLED_COUNT_KEYS, f"{label} item {index}")
        category_id = row.get("category_id")
        if category_id not in positions:
            raise ValueError(f"{label} item {index} category is invalid")
        _integer(row.get("count"), f"{label} item {index} count", minimum=1)
        observed.append(category_id)
    if len(observed) != len(set(observed)):
        raise ValueError(f"{label} categories must be unique")
    if [positions[item] for item in observed] != sorted(
        positions[item] for item in observed
    ):
        raise ValueError(f"{label} items must use deterministic category order")


def _safe_text(value: object, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or "\n" in value
        or "\r" in value
    ):
        raise ValueError(f"{label} must be non-empty single-line text")


def _integer(value: object, label: str, minimum: int | None = None) -> None:
    if type(value) is not int or (minimum is not None and value < minimum):
        raise ValueError(f"{label} must be an integer")


def _finite(value: object, label: str) -> None:
    if type(value) not in {int, float} or not math.isfinite(value):
        raise ValueError(f"{label} must be finite")


def _probability(value: object, label: str) -> None:
    _finite(value, label)
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"{label} must be a probability")


def _validate_optional_rate(
    value: object, met: int, applicable: int, label: str
) -> None:
    if applicable == 0:
        if met != 0 or value is not None:
            raise ValueError(f"{label} must be null when not estimable")
        return
    _probability(value, label)
    if not math.isclose(value, met / applicable, abs_tol=1e-12):
        raise ValueError(f"{label} is inconsistent")


def _interval(value: object, label: str) -> None:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"{label} must contain two limits")
    _finite(value[0], f"{label} lower")
    _finite(value[1], f"{label} upper")
    if value[0] > value[1]:
        raise ValueError(f"{label} must be ordered")


def _pct(value: float, digits: int) -> str:
    return f"{value * 100:.{digits}f}%"


def _criterion_rate(value: float | None, language: str) -> str:
    if value is not None:
        return _pct(value, 1)
    return "not estimable" if language == "en" else "無法估計"


def _points(value: float, digits: int) -> str:
    return f"{value * 100:.{digits}f} percentage points"


def _points_zh(value: float, digits: int) -> str:
    return f"{value * 100:.{digits}f} 個百分點"


def _one(value: float) -> str:
    return f"{value:.1f}"


def _signed(value: float) -> str:
    return f"{value:+.1f}" if value != 0 else "0.0"


def _kappa(value: float | None, language: str) -> str:
    if value is not None:
        return f"{value:.2f}"
    return (
        "null (zero expected disagreement)"
        if language == "en"
        else "null（預期不一致為零）"
    )


def _normalize_lf(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _stage_text(path: Path, text: str, suffix: str = ".tmp") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=suffix, dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def _stage_backup(path: Path) -> Path:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".bak", dir=path.parent
    )
    backup = Path(temporary_name)
    try:
        with path.open("rb") as source, os.fdopen(descriptor, "wb") as target:
            descriptor = -1
            while chunk := source.read(64 * 1024):
                target.write(chunk)
            target.flush()
            os.fsync(target.fileno())
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
        backup.unlink(missing_ok=True)
        raise
    return backup


def _write_reports_transactionally(
    english_path: Path,
    english_text: str,
    chinese_path: Path,
    chinese_text: str,
) -> None:
    staged = {
        english_path: _stage_text(english_path, english_text),
        chinese_path: _stage_text(chinese_path, chinese_text),
    }
    backups: dict[Path, Path | None] = {}
    replaced: list[Path] = []
    preserve_backups = False
    try:
        for path in (english_path, chinese_path):
            backups[path] = _stage_backup(path) if path.exists() else None
        for path in (english_path, chinese_path):
            os.replace(staged[path], path)
            replaced.append(path)
    except Exception as publication_error:
        rollback_failed = False
        for path in reversed(replaced):
            try:
                backup = backups.get(path)
                if backup is None:
                    path.unlink(missing_ok=True)
                else:
                    os.replace(backup, path)
                    backups[path] = None
            except Exception:
                rollback_failed = True
        if rollback_failed:
            preserve_backups = True
            raise RuntimeError(REPORT_RECOVERY_ERROR) from publication_error
        raise
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)
        if not preserve_backups:
            for backup in backups.values():
                if backup is not None:
                    backup.unlink(missing_ok=True)


def _same_existing_file(left: Path, right: Path) -> bool:
    return left.exists() and right.exists() and left.samefile(right)


def _validate_report_paths(summary: Path, english: Path, chinese: Path) -> None:
    resolved_summary = summary.resolve()
    resolved_english = english.resolve()
    resolved_chinese = chinese.resolve()
    if (
        resolved_summary in {resolved_english, resolved_chinese}
        or resolved_english == resolved_chinese
        or _same_existing_file(resolved_summary, resolved_english)
        or _same_existing_file(resolved_summary, resolved_chinese)
        or _same_existing_file(resolved_english, resolved_chinese)
    ):
        raise ValueError("report outputs must not alias an input or each other")


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--english", required=True, type=Path)
    parser.add_argument("--traditional-chinese", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    return parser


def main() -> None:
    parser = _argument_parser()
    try:
        args = parser.parse_args()
        _validate_report_paths(
            args.summary, args.english, args.traditional_chinese
        )
        summary = json.loads(args.summary.read_text(encoding="utf-8"))
        english = render_report(summary, "en")
        chinese = render_report(summary, "zh-TW")
        if args.check:
            current_english = _normalize_lf(args.english.read_text(encoding="utf-8"))
            current_chinese = _normalize_lf(
                args.traditional_chinese.read_text(encoding="utf-8")
            )
            if current_english != english or current_chinese != chinese:
                parser.exit(1)
        else:
            _write_reports_transactionally(
                args.english,
                english,
                args.traditional_chinese,
                chinese,
            )
    except SystemExit:
        raise
    except Exception:
        parser.exit(2, REPORT_ERROR)


if __name__ == "__main__":
    main()
