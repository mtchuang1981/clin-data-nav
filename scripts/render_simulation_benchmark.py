"""Render aligned English and Traditional Chinese simulation benchmark reports."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import stat
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
if __package__ in {None, ""}:
    sys.path.insert(0, str(ROOT))

try:
    from scripts.effectiveness_contract import ensure_external_path
    from scripts.evaluate_simulation_benchmark import validate_benchmark_summary
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from effectiveness_contract import ensure_external_path
    from evaluate_simulation_benchmark import validate_benchmark_summary


LANGUAGES = ("en", "zh-TW")
CLI_ERROR = b"simulation benchmark report rendering failed\n"
RECOVERY_ERROR = (
    "simulation benchmark report recovery required; bilingual backups preserved"
)
EXAMPLE_SUMMARY = (
    ROOT / "evals/benchmark/examples/synthetic-summary.json"
).resolve()
EXAMPLE_ENGLISH = (
    ROOT / "evals/benchmark/examples/synthetic-report.md"
).resolve()
EXAMPLE_CHINESE = (
    ROOT / "evals/benchmark/examples/synthetic-report.zh-TW.md"
).resolve()
def _display(value: object) -> str:
    if type(value) is float:
        return f"{value:.6f}"
    if type(value) is bool:
        return str(value).lower()
    return str(value)


def _fact_table(rows: list[tuple[str, object]], language: str) -> list[str]:
    header = "Field" if language == "en" else "欄位"
    value_header = "Value" if language == "en" else "值"
    return [
        f"| {header} | {value_header} |",
        "|---|---|",
        *[f"| `{key}` | {_display(value)} |" for key, value in rows],
    ]


def _identity_rows(summary: dict) -> list[tuple[str, object]]:
    rows: list[tuple[str, object]] = [
        ("benchmark_id", summary["benchmark_id"]),
        ("schema_version", summary["schema_version"]),
        ("status", summary["status"]),
        ("direction", summary["direction"]),
        ("synthetic_example", summary["synthetic_example"]),
        ("plan_sha256", summary["plan_sha256"]),
        ("catalog_sha256", summary["catalog_sha256"]),
        ("rubric_sha256", summary["rubric_sha256"]),
        ("repeats", summary["repeats"]),
        ("cell_counts.expected", summary["cell_counts"]["expected"]),
        ("cell_counts.observed", summary["cell_counts"]["observed"]),
    ]
    rows.extend(
        (f"skill.{key}", summary["skill"][key]) for key in sorted(summary["skill"])
    )
    rows.extend(
        (f"model.{key}", summary["model"][key]) for key in sorted(summary["model"])
    )
    rows.extend(
        (f"execution_attestation.{key}", summary["execution_attestation"][key])
        for key in sorted(summary["execution_attestation"])
    )
    rows.extend(
        (f"claim_boundaries.{index}", value)
        for index, value in enumerate(summary["claim_boundaries"])
    )
    return rows


def _overall_rows(summary: dict) -> list[tuple[str, object]]:
    return [
        (f"overall.{key}", summary["overall"][key])
        for key in sorted(summary["overall"])
    ]


def _paired_rows(summary: dict) -> list[tuple[str, object]]:
    return [
        (f"paired_counts.{key}", summary["paired_counts"][key])
        for key in sorted(summary["paired_counts"])
    ]


def _depth_rows(summary: dict) -> list[tuple[str, object]]:
    rows: list[tuple[str, object]] = []
    scalar_keys = (
        "case_count",
        "pairs",
        "control_passes",
        "control_pass_rate",
        "intervention_passes",
        "intervention_pass_rate",
        "difference",
    )
    for depth in summary["output_depth_results"]:
        prefix = f"depth.{depth['output_depth']}"
        rows.extend((f"{prefix}.{key}", depth[key]) for key in scalar_keys)
        for group in ("paired_counts", "forbidden_violations"):
            rows.extend(
                (f"{prefix}.{group}.{key}", depth[group][key])
                for key in sorted(depth[group])
            )
    return rows


def _case_rows(summary: dict) -> list[tuple[str, object]]:
    rows: list[tuple[str, object]] = []
    for case in summary["case_results"]:
        prefix = f"case.{case['case_id']}"
        rows.extend(
            [
                (f"{prefix}.output_depth", case["output_depth"]),
                (f"{prefix}.control_passes", case["control_passes"]),
                (f"{prefix}.intervention_passes", case["intervention_passes"]),
            ]
        )
        for group in ("paired_counts", "forbidden_violations", "stability"):
            rows.extend(
                (f"{prefix}.{group}.{key}", case[group][key])
                for key in sorted(case[group])
            )
    return rows


def _forbidden_rows(summary: dict) -> list[tuple[str, object]]:
    return [
        (f"forbidden_violations.{key}", summary["forbidden_violations"][key])
        for key in sorted(summary["forbidden_violations"])
    ]


def render_report(
    summary: dict, language: str, *, allow_synthetic: bool = False
) -> str:
    """Render one deterministic aggregate report after closed validation."""
    if language not in LANGUAGES:
        raise ValueError("report language must be en or zh-TW")
    if validate_benchmark_summary(summary, allow_synthetic=allow_synthetic):
        raise ValueError("invalid benchmark summary")
    return _render(summary, language)


def _render(summary: dict, language: str) -> str:
    synthetic = summary["synthetic_example"]
    if language == "en":
        title = "# Public simulation benchmark report"
        if synthetic:
            title += " — synthetic contract example"
        sections = (
            (
                "Identity and scope",
                [
                    (
                        "This report contains aggregate benchmark facts only. The "
                        "execution identity is recorded for reproduction, not independently verified."
                    ),
                    *(_fact_table(_identity_rows(summary), language)),
                ],
            ),
            (
                "Aggregate result",
                [
                    "The status and direction are separate predeclared classifications.",
                    *(_fact_table(_overall_rows(summary), language)),
                ],
            ),
            (
                "Paired changes",
                [
                    "Each count compares the control and intervention result for one case/repeat pair.",
                    *(_fact_table(_paired_rows(summary), language)),
                ],
            ),
            (
                "Output-depth strata",
                [
                    "Strata use the canonical output-depth order from the validated summary.",
                    *(_fact_table(_depth_rows(summary), language)),
                ],
            ),
            (
                "Per-case stability",
                [
                    "Pass counts and stability labels cover all three repeats in canonical case order.",
                    *(_fact_table(_case_rows(summary), language)),
                ],
            ),
            (
                "Forbidden-rule guardrail",
                [
                    "Forbidden-rule violations are reported separately and participate in direction classification.",
                    *(_fact_table(_forbidden_rows(summary), language)),
                ],
            ),
            (
                "Limitations and next evidence step",
                [
                    "These results concern only public synthetic prompts and deterministic contract checks.",
                    "Model metadata and the execution attestation are externally reported and are not provider-verified.",
                    "Deterministic rules do not measure all semantic quality.",
                    "No representative user performed a usability task.",
                    "No clinical-validity, causal-validity, patient-outcome, or deployment-ready claim follows from this report.",
                    "`positive-signal` is not `human-effective` or `evaluation-green`.",
                    "The next evidence step is optional independent depth review and, under separate authorization, representative-user evaluation.",
                ],
            ),
        )
    else:
        title = "# 公開模擬基準測試報告"
        if synthetic:
            title += "—合成契約範例"
        sections = (
            (
                "識別資訊與範圍",
                [
                    "本報告僅包含基準測試彙總事實；執行識別資訊用於重現，不代表已獨立驗證。",
                    *(_fact_table(_identity_rows(summary), language)),
                ],
            ),
            (
                "整體結果",
                [
                    "狀態與方向是兩個分開的預先指定分類。",
                    *(_fact_table(_overall_rows(summary), language)),
                ],
            ),
            (
                "配對變化",
                [
                    "每個計數均比較同一個案與重複次數下的對照及介入結果。",
                    *(_fact_table(_paired_rows(summary), language)),
                ],
            ),
            (
                "輸出深度分層",
                [
                    "分層依已驗證摘要中的標準輸出深度順序呈現。",
                    *(_fact_table(_depth_rows(summary), language)),
                ],
            ),
            (
                "個案穩定性",
                [
                    "通過次數與穩定性標籤涵蓋三次重複，並依標準個案順序呈現。",
                    *(_fact_table(_case_rows(summary), language)),
                ],
            ),
            (
                "禁止規則護欄",
                [
                    "禁止規則違反數獨立呈現，並參與方向分類。",
                    *(_fact_table(_forbidden_rows(summary), language)),
                ],
            ),
            (
                "限制與下一步證據",
                [
                    "這些結果僅涉及公開合成提示與確定性契約檢查。",
                    "模型中繼資料與執行證明均由外部回報，未經提供者驗證。",
                    "確定性規則無法衡量所有語意品質。",
                    "沒有具代表性的使用者執行可用性任務。",
                    "本報告不能推導出臨床效度、因果效度、病人結果或可部署性的主張。",
                    "`positive-signal` 不代表 `human-effective` 或 `evaluation-green`。",
                    "下一步證據是選用的獨立深度審查，以及另行取得授權後的代表性使用者評估。",
                ],
            ),
        )
    lines = [title, ""]
    for heading, body in sections:
        lines.extend((f"## {heading}", "", *body, ""))
    return "\n".join(lines)


def _is_link(path: Path) -> bool:
    if not path.exists() and not path.is_symlink():
        return False
    metadata = path.lstat()
    reparse = getattr(metadata, "st_file_attributes", 0) & getattr(
        stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400
    )
    return stat.S_ISLNK(metadata.st_mode) or bool(reparse)


def _same_existing_file(left: Path, right: Path) -> bool:
    try:
        return left.exists() and right.exists() and left.samefile(right)
    except OSError:
        return False


def _validate_report_paths(summary: Path, english: Path, chinese: Path) -> None:
    paths = (summary, english, chinese)
    resolved = tuple(path.resolve() for path in paths)
    if len(set(resolved)) != 3 or any(
        _same_existing_file(left, right)
        for index, left in enumerate(paths)
        for right in paths[index + 1 :]
    ):
        raise ValueError("report paths must not alias an input or each other")
    if english.name.casefold().endswith(".zh-tw.md") or not chinese.name.casefold().endswith(
        ".zh-tw.md"
    ):
        raise ValueError("report output language suffixes are invalid")
    if _is_link(english) or _is_link(chinese):
        raise ValueError("report output links are unsafe")


def _is_exact_example_paths(summary: Path, english: Path, chinese: Path) -> bool:
    return (
        summary.resolve(),
        english.resolve(),
        chinese.resolve(),
    ) == (EXAMPLE_SUMMARY, EXAMPLE_ENGLISH, EXAMPLE_CHINESE)


def _stage_text(path: Path, text: str, suffix: str = ".tmp") -> Path:
    if not path.parent.is_dir():
        raise ValueError("report output parent must exist")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=suffix, dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            descriptor = -1
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
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


def _validate_output_pair(english: Path, chinese: Path) -> None:
    if english.resolve() == chinese.resolve() or _same_existing_file(english, chinese):
        raise ValueError("report outputs must not alias each other")
    if _is_link(english) or _is_link(chinese):
        raise ValueError("report output links are unsafe")


def _write_reports_transactionally(
    english_path: Path,
    english_text: str,
    chinese_path: Path,
    chinese_text: str,
) -> None:
    _validate_output_pair(english_path, chinese_path)
    staged: dict[Path, Path] = {}
    backups: dict[Path, Path | None] = {}
    replaced: list[Path] = []
    preserve_backups = False
    try:
        for path, text in (
            (english_path, english_text),
            (chinese_path, chinese_text),
        ):
            staged[path] = _stage_text(path, text)
        _validate_output_pair(english_path, chinese_path)
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
            raise RuntimeError(RECOVERY_ERROR) from publication_error
        raise
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)
        if not preserve_backups:
            for backup in backups.values():
                if backup is not None:
                    backup.unlink(missing_ok=True)


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.exit(2)

    def exit(self, status: int = 0, message: str | None = None) -> None:
        if status == 2:
            raise ValueError("invalid report arguments")
        raise SystemExit(status)


def _argument_parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(
        description=__doc__, allow_abbrev=False, add_help=False
    )
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--english", required=True, type=Path)
    parser.add_argument("--traditional-chinese", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    return parser


def _write_error() -> None:
    stream = getattr(sys.stderr, "buffer", sys.stderr)
    try:
        stream.write(CLI_ERROR)
        stream.flush()
    except Exception:
        pass


def main(argv: list[str] | None = None) -> int:
    try:
        args = _argument_parser().parse_args(argv)
        _validate_report_paths(args.summary, args.english, args.traditional_chinese)
        allow_synthetic = _is_exact_example_paths(
            args.summary, args.english, args.traditional_chinese
        )
        if not allow_synthetic:
            ensure_external_path(args.summary, ROOT)
            ensure_external_path(args.english, ROOT)
            ensure_external_path(args.traditional_chinese, ROOT)
        summary = json.loads(args.summary.read_text(encoding="utf-8"))
        english = render_report(summary, "en", allow_synthetic=allow_synthetic)
        chinese = render_report(summary, "zh-TW", allow_synthetic=allow_synthetic)
        if args.check:
            if (
                args.english.read_bytes() != english.encode("utf-8")
                or args.traditional_chinese.read_bytes() != chinese.encode("utf-8")
            ):
                return 1
            return 0
        _validate_report_paths(args.summary, args.english, args.traditional_chinese)
        _write_reports_transactionally(
            args.english,
            english,
            args.traditional_chinese,
            chinese,
        )
        return 0
    except Exception:
        _write_error()
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
