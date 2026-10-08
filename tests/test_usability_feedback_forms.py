"""Community forms collect low-burden self-report, never raw material."""
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
FILES = ("usability-feedback.yml", "usability-feedback.zh-TW.yml")
IDS = ("repository_version", "installation_method", "agent", "operating_system",
       "task_category", "completion_outcome", "problem_reproduction", "acknowledgement")
OPTIONS = {
    "installation_method": (("npx project installation", "Verified ZIP installation", "Local contributor checkout"),
                            ("npx 專案安裝", "已核對 ZIP 安裝", "本機開發 checkout")),
    "operating_system": (("Linux", "macOS", "Windows", "Other or mixed"),
                         ("Linux", "macOS", "Windows", "其他或混合")),
    "task_category": (("Installation or update", "Quick explanation", "Evidence navigation", "Research design", "Implementation specification", "Repository benchmark tooling"),
                      ("安裝或更新", "快速解說", "證據導覽", "研究設計", "實作規格", "repository benchmark 工具")),
    "completion_outcome": (("Completed without a problem", "Completed with a problem", "Not completed"),
                           ("無問題完成", "遇到問題但完成", "未完成")),
}


def load_form(filename):
    return yaml.safe_load((ROOT / ".github/ISSUE_TEMPLATE" / filename).read_text(encoding="utf-8"))


@pytest.mark.parametrize("filename", FILES)
def test_no_problem_feedback_may_omit_description(filename):
    fields = {row["id"]: row for row in load_form(filename)["body"] if "id" in row}
    desc = fields["problem_reproduction"]
    assert desc["validations"]["required"] is False
    assert desc["attributes"]["render"] == "text"
    assert not {"value", "default", "max_length"} & desc["attributes"].keys()
    assert "default" not in fields["completion_outcome"]["attributes"]
    assert fields["acknowledgement"]["attributes"]["options"][0]["required"] is True


def test_feedback_forms_preserve_semantic_parity():
    for index, filename in enumerate(FILES):
        payload = load_form(filename)
        assert payload["labels"] == ["community-reported"]
        fields = {row["id"]: row for row in payload["body"] if "id" in row}
        assert tuple(fields) == IDS
        for name, variants in OPTIONS.items():
            assert fields[name]["attributes"]["options"] == list(variants[index])
            assert fields[name]["validations"]["required"] is True


@pytest.mark.parametrize(("filename", "readme"), tuple(zip(FILES, ("README.md", "README.zh-TW.md"))))
def test_feedback_readmes_open_forms_not_yaml_source(filename, readme):
    text = (ROOT / readme).read_text(encoding="utf-8")
    assert f"https://github.com/mtchuang1981/clin-data-nav/issues/new?template={filename}" in text
    assert f"blob/main/.github/ISSUE_TEMPLATE/{filename}" not in text


@pytest.mark.parametrize(("filename", "warnings"), [
    (FILES[0], ("patient data", "private schema", "API key", "credential", "raw prompts", "model responses", "logs", "attachments", "unverified self-report", "never enter formal aggregates")),
    (FILES[1], ("病人資料", "機構 schema", "API key", "憑證", "原始提示", "模型回答", "日誌", "附件", "未驗證的自陳", "不會納入正式成效彙總")),
])
def test_forms_do_not_solicit_raw_material(filename, warnings):
    payload = load_form(filename)
    assert set(payload) == {"name", "description", "title", "labels", "body"}
    fields = [row for row in payload["body"] if "id" in row]
    assert tuple(row["id"] for row in fields) == IDS
    assert [row["id"] for row in fields if row["type"] == "textarea"] == ["problem_reproduction"]
    assert {row["type"] for row in fields} <= {"input", "dropdown", "textarea", "checkboxes"}
    prose = " ".join(row["attributes"].get("value", "") for row in payload["body"] if row["type"] == "markdown")
    assert all(warning in prose for warning in warnings)
    acknowledgement = fields[-1]
    assert acknowledgement["validations"] == {"required": True}
    assert acknowledgement["attributes"]["options"][0]["required"] is True
    confirmation = acknowledgement["attributes"]["options"][0]["label"]
    forbidden_material = ("raw prompts", "model responses", "logs", "attachments") if filename == FILES[0] else ("原始提示", "模型回答", "日誌", "附件")
    assert all(item in confirmation for item in forbidden_material)
