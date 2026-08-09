import copy
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.render_effectiveness_report import render_report


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "evals/effectiveness/examples/synthetic-summary.json"
REPORT_EN = ROOT / "evals/effectiveness/examples/synthetic-report.md"
REPORT_ZH = ROOT / "evals/effectiveness/examples/synthetic-report.zh-TW.md"
TEMPLATE_EN = ROOT / "evals/effectiveness/report-template.md"
TEMPLATE_ZH = ROOT / "evals/effectiveness/report-template.zh-TW.md"
RENDERER = ROOT / "scripts/render_effectiveness_report.py"


ENGLISH_HEADINGS = (
    "Executive summary",
    "Methods",
    "Participant flow",
    "Primary outcome",
    "Stratified results",
    "Safety",
    "Secondary outcomes",
    "Rater agreement",
    "Missing data and sensitivity",
    "Power-analysis scenarios",
    "Protocol deviations",
    "Limitations",
)
CHINESE_HEADINGS = (
    "摘要",
    "方法",
    "參與者流程",
    "主要結果",
    "分層結果",
    "安全性",
    "次要結果",
    "評分者一致性",
    "缺失資料與敏感度分析",
    "樣本數情境",
    "規格偏離",
    "限制",
)


def test_reports_share_all_numeric_facts_and_limit_claims():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    english = render_report(summary, "en")
    chinese = render_report(summary, "zh-TW")

    for marker in ("16", "8", "20", "25.0%", "95%"):
        assert marker in english
        assert marker in chinese
    assert "exploratory" in english
    assert "探索性" in chinese
    assert "does not prove clinical validity" in english
    assert "不能證明臨床效度" in chinese
    assert "synthetic example" in english
    assert "合成範例" in chinese


def test_reports_have_identical_required_environment_and_denominator_facts():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    english = render_report(summary, "en")
    chinese = render_report(summary, "zh-TW")

    for marker in (
        summary["protocol_commit"],
        summary["environment"]["skill_commit"],
        summary["environment"]["model"],
        summary["environment"]["assignment_version"],
        summary["environment"]["task_commitment_sha256"],
        "16/32",
        "24/32",
        "5.0%",
        "45.0%",
        "deferred-until-post-pilot",
    ):
        assert marker in english
        assert marker in chinese
    assert "Task commitment: verified" in english
    assert "任務承諾：已驗證" in chinese
    assert "unknown" not in english.casefold()
    assert "unknown" not in chinese.casefold()


def test_reports_use_all_exact_headings_once_and_end_with_lf():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    for report, headings in (
        (render_report(summary, "en"), ENGLISH_HEADINGS),
        (render_report(summary, "zh-TW"), CHINESE_HEADINGS),
    ):
        for heading in headings:
            assert report.count(f"## {heading}\n") == 1
        assert report.endswith("\n")
        assert "\r" not in report


def test_renderer_fails_closed_for_missing_nonfinite_or_unsupported_inputs():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    missing = copy.deepcopy(summary)
    missing.pop("protocol_commit")
    nonfinite = copy.deepcopy(summary)
    nonfinite["primary"]["overall"]["paired_risk_difference"] = math.inf

    with pytest.raises(ValueError):
        render_report(missing, "en")
    with pytest.raises(ValueError):
        render_report(nonfinite, "en")
    with pytest.raises(ValueError):
        render_report(summary, "zh")


def test_renderer_rejects_paired_difference_contradicting_condition_rates():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    summary["primary"]["overall"]["paired_risk_difference"] = 0.20

    with pytest.raises(ValueError, match="paired risk difference is inconsistent"):
        render_report(summary, "en")


def test_renderer_rejects_paired_distribution_contradicting_condition_rates():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    distribution = summary["primary"]["overall"]["paired_distribution"]
    distribution["plus_half"] -= 1
    distribution["zero"] += 1

    with pytest.raises(ValueError, match="paired risk difference is inconsistent"):
        render_report(summary, "en")


def test_renderer_rejects_false_agreement_eligibility():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    summary["agreement"]["raw_binary_agreement"] = 0.75

    with pytest.raises(ValueError, match="agreement status is inconsistent"):
        render_report(summary, "en")


@pytest.mark.parametrize("invalid_kappa", (-1.01, 1.01))
def test_renderer_rejects_kappa_outside_unit_interval(invalid_kappa):
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    summary["agreement"]["binary_kappa"] = invalid_kappa

    with pytest.raises(ValueError, match="agreement binary_kappa must be between -1 and 1"):
        render_report(summary, "en")


def test_checked_in_example_reports_are_current():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    assert REPORT_EN.read_text(encoding="utf-8") == render_report(summary, "en")
    assert REPORT_ZH.read_text(encoding="utf-8") == render_report(summary, "zh-TW")


def test_checked_in_example_is_aggregate_only_and_explicitly_synthetic():
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    serialized = json.dumps(summary, ensure_ascii=False, sort_keys=True)

    assert summary["synthetic_example"] is True
    assert "not observed pilot evidence" in summary["limitations"][-1]
    for forbidden in (
        '"participant_code"',
        '"answer_id"',
        '"observations"',
        '"rater_scores"',
        '"sus_responses"',
        "B01",
        "A000000000000001",
    ):
        assert forbidden not in serialized


def test_templates_share_headings_define_fields_and_claim_no_result():
    english = TEMPLATE_EN.read_text(encoding="utf-8")
    chinese = TEMPLATE_ZH.read_text(encoding="utf-8")
    for heading in ENGLISH_HEADINGS:
        assert f"## {heading}\n" in english
    for heading in CHINESE_HEADINGS:
        assert f"## {heading}\n" in chinese
    assert "Field dictionary" in english
    assert "欄位字典" in chinese
    assert "negative or neutral" in english
    assert "負向或中性" in chinese
    assert "This template contains no result" in english
    assert "本模板不包含任何結果" in chinese
    assert "Quality criteria are secondary" in english
    assert "zero applicable denominator is not estimable" in english
    assert "品質準則屬於次要結果" in chinese
    assert "適用分母為零時無法估計" in chinese


def test_check_mode_is_deterministic_and_never_modifies_files(tmp_path):
    english = tmp_path / "report.md"
    chinese = tmp_path / "report.zh-TW.md"
    english.write_bytes(REPORT_EN.read_bytes())
    chinese.write_bytes(REPORT_ZH.read_bytes())
    command = [
        sys.executable,
        str(RENDERER),
        "--summary",
        str(SUMMARY),
        "--english",
        str(english),
        "--traditional-chinese",
        str(chinese),
        "--check",
    ]

    current = subprocess.run(command, capture_output=True, text=True, check=False)
    assert current.returncode == 0
    original_chinese = chinese.read_bytes()
    english.write_text("stale report\n", encoding="utf-8")
    stale_english = english.read_bytes()

    stale = subprocess.run(command, capture_output=True, text=True, check=False)

    assert stale.returncode == 1
    assert english.read_bytes() == stale_english
    assert chinese.read_bytes() == original_chinese


def test_renderer_rejects_hardlink_output_alias_without_corrupting_summary(tmp_path):
    summary = tmp_path / "summary.json"
    english = tmp_path / "report.md"
    chinese = tmp_path / "report.zh-TW.md"
    summary.write_bytes(SUMMARY.read_bytes())
    original = summary.read_bytes()
    os.link(summary, english)

    result = subprocess.run(
        [
            sys.executable,
            str(RENDERER),
            "--summary",
            str(summary),
            "--english",
            str(english),
            "--traditional-chinese",
            str(chinese),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stderr == "effectiveness report rendering failed\n"
    assert summary.read_bytes() == original
    assert english.read_bytes() == original
    assert not chinese.exists()
