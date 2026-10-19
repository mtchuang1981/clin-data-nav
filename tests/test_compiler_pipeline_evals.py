"""A separate suite must not alter frozen core benchmark inputs."""
from pathlib import Path
import shutil

import pytest

from scripts.evaluate_response import evaluate_response, load_catalog
from scripts import render_eval_summary

ROOT = Path(__file__).resolve().parents[1]
CASE_IDS = (
    "pipeline-complete", "pipeline-fixture-unavailable", "pipeline-digest-mismatch",
    "pipeline-gates-missing", "pipeline-feasibility-scope", "pipeline-absent",
)


@pytest.mark.parametrize("case_id", CASE_IDS)
def test_pipeline_case_has_passing_forward_and_rejected_negative(case_id):
    path = ROOT / "evals/compiler-pipeline/cases.yaml"
    assert path.is_file(), "separate compiler-pipeline catalog is absent"
    catalog, rubric = load_catalog(path, ROOT / "evals/rubric.yaml")
    assert {case["id"] for case in catalog["cases"]} == set(CASE_IDS)
    case = next(case for case in catalog["cases"] if case["id"] == case_id)
    fixtures = ROOT / "tests/fixtures/compiler_pipeline"
    forward = (fixtures / "forward" / f"{case_id}.md").read_text(encoding="utf-8")
    negative = (fixtures / "baseline" / f"{case_id}.md").read_text(encoding="utf-8")
    assert evaluate_response(case, rubric, forward).passed
    assert not evaluate_response(case, rubric, negative).passed
    # Even a fully shaped answer fails when an unsafe executable claim/code is added.
    unsafe = "\nMaturity: executable\nSELECT 1;\n"
    assert not evaluate_response(case, rubric, forward + unsafe).passed


def test_pipeline_renderer_only_changes_selected_suite(tmp_path):
    shutil.copytree(ROOT / "evals", tmp_path / "evals")
    shutil.copytree(ROOT / "tests/fixtures", tmp_path / "tests/fixtures")
    core_path = tmp_path / "evals/README.md"
    before = core_path.read_bytes()
    readme = tmp_path / "evals/compiler-pipeline/README.md"
    assert readme.is_file(), "pipeline suite README is absent"
    readme.write_text("preserved prefix\n<!-- BEGIN GENERATED EVAL SUMMARY -->\nstale\n"
                      "<!-- END GENERATED EVAL SUMMARY -->\npreserved suffix\n", encoding="utf-8")
    assert render_eval_summary.main(["--suite", "compiler-pipeline"], root=tmp_path) == 0
    assert render_eval_summary.main(["--suite", "compiler-pipeline", "--check"], root=tmp_path) == 0
    assert core_path.read_bytes() == before
    rendered = readme.read_text(encoding="utf-8")
    assert rendered.startswith("preserved prefix\n")
    assert rendered.endswith("preserved suffix\n")
    for case_id in CASE_IDS:
        assert f"`{case_id}`" in rendered


def test_default_renderer_still_checks_core_and_rejects_unknown_suite():
    before = (ROOT / "evals/README.md").read_bytes()
    assert render_eval_summary.main(["--check"]) == 0
    with pytest.raises(SystemExit) as failure:
        render_eval_summary.main(["--suite", "../untrusted"])
    assert failure.value.code == 2
    assert (ROOT / "evals/README.md").read_bytes() == before
