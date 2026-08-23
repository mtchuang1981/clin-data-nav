from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

import scripts.render_simulation_benchmark as report_module
from scripts.render_simulation_benchmark import render_report
from scripts.evaluate_simulation_benchmark import validate_benchmark_summary
from scripts.prepare_simulation_benchmark import canonical_json_bytes


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "evals/benchmark/examples/synthetic-summary.json"
REPORT_EN = ROOT / "evals/benchmark/examples/synthetic-report.md"
REPORT_ZH = ROOT / "evals/benchmark/examples/synthetic-report.zh-TW.md"
TEMPLATE_EN = ROOT / "evals/benchmark/report-template.md"
TEMPLATE_ZH = ROOT / "evals/benchmark/report-template.zh-TW.md"
SCHEMA = ROOT / "evals/benchmark/summary-schema.md"
RENDERER = ROOT / "scripts/render_simulation_benchmark.py"

ENGLISH_HEADINGS = (
    "Identity and scope",
    "Aggregate result",
    "Paired changes",
    "Output-depth strata",
    "Per-case stability",
    "Forbidden-rule guardrail",
    "Limitations and next evidence step",
)
CHINESE_HEADINGS = (
    "識別資訊與範圍",
    "整體結果",
    "配對變化",
    "輸出深度分層",
    "個案穩定性",
    "禁止規則護欄",
    "限制與下一步證據",
)


def _load_summary() -> dict:
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


def _facts(report: str) -> dict[str, str]:
    facts: dict[str, str] = {}
    for line in report.splitlines():
        match = re.fullmatch(r"\| `([^`]+)` \| (.*) \|", line)
        if match:
            key, value = match.groups()
            assert key not in facts
            facts[key] = value
    return facts


def _expected_facts(summary: dict) -> dict[str, str]:
    facts = {
        "benchmark_id": summary["benchmark_id"],
        "schema_version": summary["schema_version"],
        "status": summary["status"],
        "direction": summary["direction"],
        "synthetic_example": str(summary["synthetic_example"]).lower(),
        "plan_sha256": summary["plan_sha256"],
        "catalog_sha256": summary["catalog_sha256"],
        "rubric_sha256": summary["rubric_sha256"],
        "repeats": str(summary["repeats"]),
        "cell_counts.expected": str(summary["cell_counts"]["expected"]),
        "cell_counts.observed": str(summary["cell_counts"]["observed"]),
    }
    for key, value in summary["skill"].items():
        facts[f"skill.{key}"] = str(value)
    for key, value in summary["model"].items():
        facts[f"model.{key}"] = (
            f"{value:.6f}" if type(value) is float else str(value)
        )
    for key, value in summary["execution_attestation"].items():
        facts[f"execution_attestation.{key}"] = (
            str(value).lower() if type(value) is bool else str(value)
        )
    for key, value in summary["overall"].items():
        facts[f"overall.{key}"] = (
            f"{value:.6f}" if type(value) is float else str(value)
        )
    for key, value in summary["paired_counts"].items():
        facts[f"paired_counts.{key}"] = str(value)
    for row in summary["output_depth_results"]:
        prefix = f"depth.{row['output_depth']}"
        for key in (
            "case_count",
            "pairs",
            "control_passes",
            "control_pass_rate",
            "intervention_passes",
            "intervention_pass_rate",
            "difference",
        ):
            value = row[key]
            facts[f"{prefix}.{key}"] = (
                f"{value:.6f}" if type(value) is float else str(value)
            )
        for group in ("paired_counts", "forbidden_violations"):
            for key, value in row[group].items():
                facts[f"{prefix}.{group}.{key}"] = str(value)
    for row in summary["case_results"]:
        prefix = f"case.{row['case_id']}"
        facts[f"{prefix}.output_depth"] = row["output_depth"]
        for key in ("control_passes", "intervention_passes"):
            facts[f"{prefix}.{key}"] = str(row[key])
        for group in ("paired_counts", "forbidden_violations", "stability"):
            for key, value in row[group].items():
                facts[f"{prefix}.{group}.{key}"] = str(value)
    for key, value in summary["forbidden_violations"].items():
        facts[f"forbidden_violations.{key}"] = str(value)
    for index, value in enumerate(summary["claim_boundaries"]):
        facts[f"claim_boundaries.{index}"] = value
    return facts


def test_render_report_rejects_synthetic_by_default_and_invalid_language():
    summary = _load_summary()

    with pytest.raises(ValueError, match="invalid benchmark summary"):
        render_report(summary, "en")
    with pytest.raises(ValueError, match="language"):
        render_report(summary, "zh", allow_synthetic=True)

    assert "synthetic contract example" in render_report(
        summary, "en", allow_synthetic=True
    )


def test_reports_have_exact_section_order_and_identical_parseable_facts():
    summary = _load_summary()
    english = render_report(summary, "en", allow_synthetic=True)
    chinese = render_report(summary, "zh-TW", allow_synthetic=True)

    for report, headings in (
        (english, ENGLISH_HEADINGS),
        (chinese, CHINESE_HEADINGS),
    ):
        observed = tuple(
            line.removeprefix("## ")
            for line in report.splitlines()
            if line.startswith("## ")
        )
        assert observed == headings
        assert report.endswith("\n")
        assert "\r" not in report

    expected = _expected_facts(summary)
    assert _facts(english) == expected
    assert _facts(chinese) == expected
    assert "| Field | Value |" in english
    assert "| 欄位 | 值 |" in chinese


def test_rendering_is_independent_of_json_object_insertion_order():
    summary = _load_summary()
    reordered = deepcopy(summary)
    for key in ("skill", "model", "execution_attestation", "overall", "paired_counts"):
        reordered[key] = dict(reversed(tuple(reordered[key].items())))
    reordered["forbidden_violations"] = dict(
        reversed(tuple(reordered["forbidden_violations"].items()))
    )
    for depth in reordered["output_depth_results"]:
        for key in ("paired_counts", "forbidden_violations"):
            depth[key] = dict(reversed(tuple(depth[key].items())))
    for case in reordered["case_results"]:
        for key in ("paired_counts", "forbidden_violations", "stability"):
            case[key] = dict(reversed(tuple(case[key].items())))

    assert render_report(
        reordered, "en", allow_synthetic=True
    ) == render_report(summary, "en", allow_synthetic=True)


def test_reports_include_fixed_limitations_without_overclaiming():
    summary = _load_summary()
    english = render_report(summary, "en", allow_synthetic=True)
    chinese = render_report(summary, "zh-TW", allow_synthetic=True)

    english_limitations = (
        "These results concern only public synthetic prompts and deterministic contract checks.",
        "Model metadata and the execution attestation are externally reported and are not provider-verified.",
        "Deterministic rules do not measure all semantic quality.",
        "No representative user performed a usability task.",
        "No clinical-validity, causal-validity, patient-outcome, or deployment-ready claim follows from this report.",
        "`positive-signal` is not `human-effective` or `evaluation-green`.",
    )
    chinese_limitations = (
        "這些結果僅涉及公開合成提示與確定性契約檢查。",
        "模型中繼資料與執行證明均由外部回報，未經提供者驗證。",
        "確定性規則無法衡量所有語意品質。",
        "沒有具代表性的使用者執行可用性任務。",
        "本報告不能推導出臨床效度、因果效度、病人結果或可部署性的主張。",
        "`positive-signal` 不代表 `human-effective` 或 `evaluation-green`。",
    )
    assert all(sentence in english for sentence in english_limitations)
    assert all(sentence in chinese for sentence in chinese_limitations)
    for claim in (
        "is human-effective",
        "is evaluation-green",
        "establishes clinical validity",
        "establishes causal validity",
        "improves patient outcomes",
        "is deployment-ready",
    ):
        assert claim not in english.casefold()


@pytest.mark.parametrize(
    "mutation",
    [
        lambda summary: summary.update({"direction": "mixed-or-null"}),
        lambda summary: summary.update({"plan_sha256": "0" * 63}),
        lambda summary: summary["overall"].update({"difference": 0.999999}),
        lambda summary: summary["case_results"][0]["stability"].update(
            {"control": "stable-pass"}
        ),
    ],
)
def test_renderer_rejects_stale_or_nonrecomputable_summary_facts(mutation):
    summary = _load_summary()
    mutation(summary)

    assert validate_benchmark_summary(summary, allow_synthetic=True)
    with pytest.raises(ValueError, match="invalid benchmark summary"):
        render_report(summary, "en", allow_synthetic=True)


def test_checked_in_examples_are_current_and_canonical():
    summary = _load_summary()

    assert summary["synthetic_example"] is True
    assert summary["cell_counts"] == {"expected": 72, "observed": 72}
    assert summary["direction"] == "positive-signal"
    assert validate_benchmark_summary(summary, allow_synthetic=True) == []
    assert SUMMARY.read_bytes() == canonical_json_bytes(summary)
    assert REPORT_EN.read_text(encoding="utf-8") == render_report(
        summary, "en", allow_synthetic=True
    )
    assert REPORT_ZH.read_text(encoding="utf-8") == render_report(
        summary, "zh-TW", allow_synthetic=True
    )


def test_schema_and_templates_define_the_closed_contract_without_a_result():
    summary = _load_summary()
    schema = SCHEMA.read_text(encoding="utf-8")
    english = TEMPLATE_EN.read_text(encoding="utf-8")
    chinese = TEMPLATE_ZH.read_text(encoding="utf-8")

    for key in summary:
        assert f"`{key}`" in schema
    for key in (
        "assertion_basis",
        "completed_at",
        "control_pass_rate",
        "paired_counts",
        "stability",
        "synthetic_example",
    ):
        assert f"`{key}`" in schema
    for heading in ENGLISH_HEADINGS:
        assert f"## {heading}\n" in english
    for heading in CHINESE_HEADINGS:
        assert f"## {heading}\n" in chinese
    assert "This template contains no benchmark result" in english
    assert "本模板不包含任何基準測試結果" in chinese
    assert "<value>" in english
    assert "<value>" in chinese


def test_exact_checked_in_cli_paths_are_the_only_synthetic_opt_in():
    command = [
        sys.executable,
        str(RENDERER),
        "--summary",
        str(SUMMARY),
        "--english",
        str(REPORT_EN),
        "--traditional-chinese",
        str(REPORT_ZH),
        "--check",
    ]
    accepted = subprocess.run(command, capture_output=True, text=True, check=False)
    redirected = subprocess.run(
        [*command[:-2], str(REPORT_EN.with_name("redirected.zh-TW.md")), "--check"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert accepted.returncode == 0
    assert accepted.stdout == accepted.stderr == ""
    assert redirected.returncode == 2
    assert redirected.stdout == ""
    assert redirected.stderr == "simulation benchmark report rendering failed\n"
    assert not REPORT_EN.with_name("redirected.zh-TW.md").exists()


def test_check_mode_detects_drift_and_performs_zero_writes(tmp_path, monkeypatch):
    summary_path = tmp_path / "synthetic-summary.json"
    english_path = tmp_path / "synthetic-report.md"
    chinese_path = tmp_path / "synthetic-report.zh-TW.md"
    summary_path.write_bytes(SUMMARY.read_bytes())
    english_path.write_bytes(REPORT_EN.read_bytes())
    chinese_path.write_bytes(REPORT_ZH.read_bytes())
    monkeypatch.setattr(report_module, "EXAMPLE_SUMMARY", summary_path.resolve())
    monkeypatch.setattr(report_module, "EXAMPLE_ENGLISH", english_path.resolve())
    monkeypatch.setattr(report_module, "EXAMPLE_CHINESE", chinese_path.resolve())
    monkeypatch.setattr(
        report_module,
        "_write_reports_transactionally",
        lambda *args: pytest.fail("--check attempted a write"),
    )
    before = {path: path.read_bytes() for path in (summary_path, english_path, chinese_path)}

    assert report_module.main(
        [
            "--summary",
            str(summary_path),
            "--english",
            str(english_path),
            "--traditional-chinese",
            str(chinese_path),
            "--check",
        ]
    ) == 0
    english_path.write_bytes(b"stale\n")
    stale = english_path.read_bytes()
    assert report_module.main(
        [
            "--summary",
            str(summary_path),
            "--english",
            str(english_path),
            "--traditional-chinese",
            str(chinese_path),
            "--check",
        ]
    ) == 1
    assert summary_path.read_bytes() == before[summary_path]
    assert english_path.read_bytes() == stale
    assert chinese_path.read_bytes() == before[chinese_path]


@pytest.mark.parametrize(
    "mutation",
    [
        lambda text: text.replace("## Aggregate result\n", "", 1),
        lambda text: text.replace("## Aggregate result", "## TEMP", 1)
        .replace("## Paired changes", "## Aggregate result", 1)
        .replace("## TEMP", "## Paired changes", 1),
        lambda text: text.replace("0.666667", "0.666668", 1),
        lambda text: text.replace("positive-signal", "mixed-or-null", 1),
        lambda text: text.replace("c" * 64, "d" * 64, 1),
        lambda text: text.replace(
            "Deterministic rules do not measure all semantic quality.\n", "", 1
        ),
    ],
    ids=(
        "missing-section",
        "reordered-sections",
        "stale-number",
        "stale-direction",
        "wrong-digest",
        "missing-limitation",
    ),
)
def test_check_rejects_named_report_mutations_without_writing(
    tmp_path, monkeypatch, mutation
):
    summary_path = tmp_path / "synthetic-summary.json"
    english_path = tmp_path / "synthetic-report.md"
    chinese_path = tmp_path / "synthetic-report.zh-TW.md"
    summary_path.write_bytes(SUMMARY.read_bytes())
    english_path.write_text(
        mutation(REPORT_EN.read_text(encoding="utf-8")), encoding="utf-8"
    )
    chinese_path.write_bytes(REPORT_ZH.read_bytes())
    monkeypatch.setattr(report_module, "EXAMPLE_SUMMARY", summary_path.resolve())
    monkeypatch.setattr(report_module, "EXAMPLE_ENGLISH", english_path.resolve())
    monkeypatch.setattr(report_module, "EXAMPLE_CHINESE", chinese_path.resolve())
    before = {path: path.read_bytes() for path in (summary_path, english_path, chinese_path)}

    assert report_module.main(
        [
            "--summary",
            str(summary_path),
            "--english",
            str(english_path),
            "--traditional-chinese",
            str(chinese_path),
            "--check",
        ]
    ) == 1
    assert {path: path.read_bytes() for path in before} == before


def test_exact_example_triple_permits_generation(tmp_path, monkeypatch):
    summary_path = tmp_path / "synthetic-summary.json"
    english_path = tmp_path / "synthetic-report.md"
    chinese_path = tmp_path / "synthetic-report.zh-TW.md"
    summary_path.write_bytes(SUMMARY.read_bytes())
    english_path.write_bytes(b"old english\n")
    chinese_path.write_bytes("舊版中文\n".encode())
    monkeypatch.setattr(report_module, "EXAMPLE_SUMMARY", summary_path.resolve())
    monkeypatch.setattr(report_module, "EXAMPLE_ENGLISH", english_path.resolve())
    monkeypatch.setattr(report_module, "EXAMPLE_CHINESE", chinese_path.resolve())

    assert report_module.main(
        [
            "--summary",
            str(summary_path),
            "--english",
            str(english_path),
            "--traditional-chinese",
            str(chinese_path),
        ]
    ) == 0
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert english_path.read_text(encoding="utf-8") == render_report(
        summary, "en", allow_synthetic=True
    )
    assert chinese_path.read_text(encoding="utf-8") == render_report(
        summary, "zh-TW", allow_synthetic=True
    )


def test_bilingual_publication_rolls_back_first_replace_on_second_failure(
    tmp_path, monkeypatch
):
    english = tmp_path / "report.md"
    chinese = tmp_path / "report.zh-TW.md"
    english.write_bytes(b"old english\n")
    chinese.write_bytes("舊版中文\n".encode())
    real_replace = report_module.os.replace
    replace_calls = 0

    def fail_second(source, destination):
        nonlocal replace_calls
        replace_calls += 1
        if replace_calls == 2:
            raise OSError("second replacement failed")
        return real_replace(source, destination)

    monkeypatch.setattr(report_module.os, "replace", fail_second)

    with pytest.raises(OSError, match="second replacement failed"):
        report_module._write_reports_transactionally(
            english, "new english\n", chinese, "新版中文\n"
        )

    assert english.read_bytes() == b"old english\n"
    assert chinese.read_bytes() == "舊版中文\n".encode()
    assert not list(tmp_path.glob(".*.tmp"))
    assert not list(tmp_path.glob(".*.bak"))


def test_bilingual_publication_cleans_first_stage_when_second_staging_fails(
    tmp_path, monkeypatch
):
    english = tmp_path / "report.md"
    chinese = tmp_path / "report.zh-TW.md"
    english.write_bytes(b"old english\n")
    chinese.write_bytes("舊版中文\n".encode())
    real_stage = report_module._stage_text
    stage_calls = 0

    def fail_second_stage(path, text, suffix=".tmp"):
        nonlocal stage_calls
        stage_calls += 1
        if stage_calls == 2:
            raise OSError("second staging failed")
        return real_stage(path, text, suffix)

    monkeypatch.setattr(report_module, "_stage_text", fail_second_stage)

    with pytest.raises(OSError, match="second staging failed"):
        report_module._write_reports_transactionally(
            english, "new english\n", chinese, "新版中文\n"
        )

    assert english.read_bytes() == b"old english\n"
    assert chinese.read_bytes() == "舊版中文\n".encode()
    assert not list(tmp_path.glob(".*.tmp"))
    assert not list(tmp_path.glob(".*.bak"))


def test_report_paths_reject_hardlink_output_alias_input_alias_and_language_mix(
    tmp_path,
):
    summary = tmp_path / "summary.json"
    english = tmp_path / "report.md"
    chinese = tmp_path / "report.zh-TW.md"
    summary.write_bytes(b"{}\n")
    english.write_bytes(b"old\n")
    os.link(english, chinese)

    with pytest.raises(ValueError, match="alias"):
        report_module._validate_report_paths(summary, english, chinese)

    chinese.unlink()
    os.link(summary, chinese)
    with pytest.raises(ValueError, match="alias"):
        report_module._validate_report_paths(summary, english, chinese)

    chinese.unlink()
    with pytest.raises(ValueError, match="language"):
        report_module._validate_report_paths(
            summary, tmp_path / "english.zh-TW.md", tmp_path / "chinese.md"
        )


def test_redirected_synthetic_generation_and_input_alias_leave_files_unchanged(
    tmp_path,
):
    summary = tmp_path / "synthetic-summary.json"
    english = tmp_path / "report.md"
    chinese = tmp_path / "report.zh-TW.md"
    summary.write_bytes(SUMMARY.read_bytes())
    original = summary.read_bytes()

    redirected = subprocess.run(
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
    assert redirected.returncode == 2
    assert redirected.stderr == "simulation benchmark report rendering failed\n"
    assert not english.exists()
    assert not chinese.exists()

    os.link(summary, english)
    aliased = subprocess.run(
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
    assert aliased.returncode == 2
    assert summary.read_bytes() == original
    assert english.read_bytes() == original
    assert not chinese.exists()


def test_external_non_synthetic_summary_renders_without_example_label(tmp_path):
    summary_path = tmp_path / "benchmark-summary.json"
    english = tmp_path / "benchmark-report.md"
    chinese = tmp_path / "benchmark-report.zh-TW.md"
    summary = _load_summary()
    summary["synthetic_example"] = False
    summary_path.write_bytes(canonical_json_bytes(summary))

    result = subprocess.run(
        [
            sys.executable,
            str(RENDERER),
            "--summary",
            str(summary_path),
            "--english",
            str(english),
            "--traditional-chinese",
            str(chinese),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == result.stderr == ""
    assert "synthetic contract example" not in english.read_text(encoding="utf-8")
    assert "合成契約範例" not in chinese.read_text(encoding="utf-8")
