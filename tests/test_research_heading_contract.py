"""Opt-in aliases must not change legacy replay or weaken structural gates."""

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import evaluate_response as evaluator


ROOT = Path(__file__).resolve().parents[1]
PROFILE = "research-bilingual-v1"
PAIRS = (
    ("Primary intent and design route", "研究意圖與設計路徑"),
    ("Design fields and time anchors", "設計欄位與時間軸"),
    ("Data suitability and claim boundary", "資料適用性與主張邊界"),
    ("Bias and validation gaps", "偏差與驗證缺口"),
    ("Analysis or diagnostics", "分析或診斷"),
)


@pytest.fixture
def research():
    catalog, rubric = evaluator.load_catalog(ROOT / "evals/cases.yaml", ROOT / "evals/rubric.yaml")
    case = next(case for case in catalog["cases"] if case["id"] == "omop-phenotype")
    english = (ROOT / "tests/fixtures/forward/omop-phenotype.md").read_text(encoding="utf-8")
    return case, rubric, english


def translated(text, count=5):
    for english, chinese in PAIRS[:count]:
        text = text.replace("## " + english, "## " + chinese)
    return text


def selected(research, text, **changes):
    case, rubric, _ = research
    return evaluator.evaluate_response({**case, **changes}, rubric, text, heading_contract=PROFILE)


@pytest.mark.parametrize("count", (0, 2, 5))
def test_opted_in_english_mixed_and_chinese_have_identical_scores(research, count):
    case, rubric, english = research
    old = evaluator.evaluate_response(case, rubric, english)
    new = selected(research, translated(english, count))
    assert old.passed
    assert asdict(new) == asdict(old)


@pytest.mark.parametrize("index", range(5))
def test_an_alias_in_body_does_not_replace_a_missing_h2(research, index):
    text = translated(research[2])
    chinese = PAIRS[index][1]
    text = text.replace("## " + chinese, "Body mentions " + chinese)
    result = selected(research, text)
    assert not result.passed
    assert any(item.rule == "depth-section:" + PAIRS[index][0] and not item.passed for item in result.results)


@pytest.mark.parametrize("prefix,suffix", (
    ("# ", ""), ("### ", ""), ("#### ", ""), ("##### ", ""), ("###### ", ""),
    ("## ", " extra"), ("## ", " ##"), ("> ## ", ""),
))
def test_wrong_heading_shape_is_not_an_alias_match(research, prefix, suffix):
    text = translated(research[2]).replace("## " + PAIRS[0][1], prefix + PAIRS[0][1] + suffix)
    assert not selected(research, text).passed


@pytest.mark.parametrize("kind", ("backtick", "tilde", "indented"))
def test_code_examples_cannot_supply_missing_chinese_sections(research, kind):
    text = translated(research[2])
    block = "## " + PAIRS[0][1]
    replacement = {
        "backtick": "```markdown\n" + block + "\n```",
        "tilde": "~~~markdown\n" + block + "\n~~~",
        "indented": "    " + block,
    }[kind]
    assert not selected(research, text.replace(block, replacement)).passed


@pytest.mark.parametrize("index", range(5))
def test_unapproved_synonyms_do_not_count_as_sections(research, index):
    text = translated(research[2]).replace("## " + PAIRS[index][1], "## 其他" + PAIRS[index][1])
    assert not selected(research, text).passed


def test_canonical_case_required_sections_accept_aliases_without_double_credit(research):
    case, rubric, english = research
    case = {**case, "required_sections": [PAIRS[0][0]]}
    expected = evaluator.evaluate_response(case, rubric, english)
    text = translated(english) + "\n## " + PAIRS[0][0] + "\nRepeated section.\n"
    actual = evaluator.evaluate_response(case, rubric, text, heading_contract=PROFILE)
    assert actual.passed
    assert asdict(actual) == asdict(expected)


@pytest.mark.parametrize("level", range(1, 7))
def test_translated_research_titles_remain_forbidden_at_other_depths(research, level):
    catalog, rubric = evaluator.load_catalog(ROOT / "evals/cases.yaml", ROOT / "evals/rubric.yaml")
    case = next(case for case in catalog["cases"] if case["id"] == "institutional-sql-without-dictionary")
    text = (ROOT / "tests/fixtures/forward/institutional-sql-without-dictionary.md").read_text(encoding="utf-8")
    assert evaluator.evaluate_response(case, rubric, text).passed
    text += "\n" + "#" * level + " " + PAIRS[0][1] + "\nCross-depth section.\n"
    result = evaluator.evaluate_response(case, rubric, text, heading_contract=PROFILE)
    assert not result.passed
    assert any(item.rule == "forbidden-section:primary intent and design route" and not item.passed for item in result.results)


def test_wrong_selected_depth_still_fails(research):
    assert not selected(research, translated(research[2]), output_depth="implementation specification").passed


def test_aliases_do_not_translate_common_headers_or_required_content(research):
    text = translated(research[2])
    assert not selected(research, text.replace("Decision:", "決策：")).passed
    result = selected(research, text.replace("standard concept", "a different layer"))
    assert not result.passed
    assert any(item.rule.startswith("required:") and not item.passed for item in result.results)


def test_forbidden_claims_in_code_still_fail_with_valid_chinese_headings(research):
    text = translated(research[2]) + "\n```text\nOMOP Concept ID 12345\n```\n"
    result = selected(research, text)
    assert not result.passed
    assert any(item.rule.startswith("forbidden:") and not item.passed for item in result.results)


@pytest.mark.parametrize("contract", ("unknown", "research-bilingual-v2", "", None))
def test_unknown_contract_does_not_downgrade_to_legacy(research, contract):
    with pytest.raises(ValueError, match="unknown heading contract"):
        evaluator.evaluate_response(*research, heading_contract=contract)


def test_legacy_is_independent_of_new_reference_and_rejects_translations(research, tmp_path, monkeypatch):
    monkeypatch.setattr(evaluator, "RESEARCH_HEADING_CONTRACT_PATH", tmp_path / "absent.json")
    case, rubric, english = research
    assert evaluator.evaluate_response(case, rubric, english).passed
    assert not evaluator.evaluate_response(case, rubric, translated(english)).passed
    with pytest.raises(ValueError, match="invalid heading contract"):
        selected(research, translated(english))


@pytest.mark.parametrize("content", (
    "not-json", "null", "[]", "{}",
    '{"contract_id":"research-bilingual-v1","aliases":{},"extra":true}',
    '{"contract_id":"legacy-v1","aliases":{}}',
    '{"contract_id":"research-bilingual-v1","contract_id":"research-bilingual-v1","aliases":{}}',
))
def test_unusable_contract_data_fails_closed(research, tmp_path, monkeypatch, content):
    path = tmp_path / "bad-contract.json"
    path.write_text(content, encoding="utf-8")
    monkeypatch.setattr(evaluator, "RESEARCH_HEADING_CONTRACT_PATH", path)
    with pytest.raises(ValueError, match="invalid heading contract"):
        selected(research, translated(research[2]))
    assert evaluator.evaluate_response(*research).passed


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "non-string", "multiline", "extra"))
def test_alias_mapping_must_be_complete_unambiguous_and_closed(research, tmp_path, monkeypatch, mutation):
    aliases = dict(PAIRS)
    if mutation == "missing":
        aliases.pop(PAIRS[0][0])
    elif mutation == "duplicate":
        aliases[PAIRS[0][0]] = PAIRS[1][1]
    elif mutation == "non-string":
        aliases[PAIRS[0][0]] = []
    elif mutation == "multiline":
        aliases[PAIRS[0][0]] += "\nextra"
    else:
        aliases["Data contract"] = "資料契約"
    path = tmp_path / "bad-contract.json"
    path.write_text(json.dumps({"contract_id": PROFILE, "aliases": aliases}, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(evaluator, "RESEARCH_HEADING_CONTRACT_PATH", path)
    with pytest.raises(ValueError, match="invalid heading contract"):
        selected(research, translated(research[2]))


def test_36_legacy_evaluations_keep_prechange_digest():
    results = []
    explicit = []
    for suite, cases, fixtures in (
        ("core", "evals/cases.yaml", "tests/fixtures"),
        ("compiler-pipeline", "evals/compiler-pipeline/cases.yaml", "tests/fixtures/compiler_pipeline"),
    ):
        catalog, rubric = evaluator.load_catalog(ROOT / cases, ROOT / "evals/rubric.yaml")
        for case in catalog["cases"]:
            for arm in ("baseline", "forward"):
                text = (ROOT / fixtures / arm / (case["id"] + ".md")).read_text(encoding="utf-8")
                results.append([suite, arm, asdict(evaluator.evaluate_response(case, rubric, text))])
                explicit.append([suite, arm, asdict(evaluator.evaluate_response(case, rubric, text, heading_contract="legacy-v1"))])
    assert len(results) == 36
    assert explicit == results
    encoded = json.dumps(results, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(encoded).hexdigest() == "6c7db3794be2f5b74107a27ae9dae5e385aa82cfabb98be691bf4b67b72b8757"


def cli(response, *extra):
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(ROOT / "scripts/evaluate_response.py"),
         "--case", "omop-phenotype", "--response", str(response), *extra],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False,
    )


def test_cli_opt_in_is_recorded_and_default_output_stays_legacy(research, tmp_path):
    path = tmp_path / "response.md"
    path.write_text(translated(research[2]), encoding="utf-8")
    legacy = cli(path)
    explicit = cli(path, "--heading-contract", "legacy-v1")
    candidate = cli(path, "--heading-contract", PROFILE)
    assert legacy.returncode == 1
    assert explicit.stdout == legacy.stdout
    assert "heading_contract" not in json.loads(legacy.stdout)
    assert candidate.returncode == 0, candidate.stderr
    assert json.loads(candidate.stdout)["heading_contract"] == PROFILE
    assert json.loads(candidate.stdout)["passed"] is True


def test_cli_unknown_contract_returns_usage_error_not_traceback(research, tmp_path):
    path = tmp_path / "response.md"
    path.write_text(research[2], encoding="utf-8")
    result = cli(path, "--heading-contract", "unknown")
    assert result.returncode == 2
    assert "invalid choice" in result.stderr
    assert "Traceback" not in result.stderr


def test_cli_rejects_unavailable_selected_contract_without_retry(research, tmp_path, monkeypatch, capsys):
    path = tmp_path / "response.md"
    path.write_text(research[2], encoding="utf-8")
    monkeypatch.setattr(evaluator, "RESEARCH_HEADING_CONTRACT_PATH", tmp_path / "missing.json")
    with pytest.raises(SystemExit) as failure:
        evaluator.main(["--case", "omop-phenotype", "--response", str(path), "--heading-contract", PROFILE])
    assert failure.value.code == 2
    output = capsys.readouterr()
    assert not output.out
    assert "invalid heading contract" in output.err
    assert "Traceback" not in output.err


def test_shipped_public_fixture_only_changes_five_headings(research):
    fixture = ROOT / "tests/fixtures/research_headings/omop-phenotype.zh-TW.md"
    text = fixture.read_text(encoding="utf-8")
    assert text == translated(research[2])
    assert selected(research, text).passed
    assert not evaluator.evaluate_response(research[0], research[1], text).passed
    assert cli(fixture, "--heading-contract", PROFILE).returncode == 0


def test_new_contract_preserves_case_sensitive_rubric(research):
    case, rubric, english = research
    rubric = {**rubric, "normalization": {"case_sensitive": True, "unicode_form": "NFKC"}}
    assert evaluator.evaluate_response(case, rubric, translated(english), heading_contract=PROFILE).passed
    lower_heading = english.replace("## Primary intent and design route", "## primary intent and design route")
    assert not evaluator.evaluate_response(case, rubric, lower_heading, heading_contract=PROFILE).passed
