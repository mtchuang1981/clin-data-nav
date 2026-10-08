# Public Docs, Actionable Gaps and Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修正文檔／範例漂移，讓正式缺口可行動，提供不要求原始資料的雙語回饋。

**Architecture:** 只修改現有公開文件與正式輸出規則；quick shape 不變。五欄 gaps 集中定義於 evidence-output-template，其他 references 指向它；兩份 Issue Forms 共用語意欄位但各自有可讀語言。

**Tech Stack:** Markdown、GitHub Issue Forms YAML、既有 pytest／PyYAML；不新增 runtime dependency。

**Spec:** [已核准設計](../specs/2026-10-04-public-core-usability-design.md)，第二、三、五節；[共同執行約束](2026-10-04-public-core-usability.md)。

## Global Constraints

- 不變更版本號、CHANGELOG、已發布 tag 或 Release assets。
- Quick explanation 不增加必填表頭或表格；metadata-only connector 不升級 executable。
- TEAE／mapping 為 dictionary-specified，OMOP 為 conceptual；前兩者的虛構核准只放 Assumptions。
- Gate 一律 unmet，保留 `SPECIFICATION ONLY — NOT EXECUTABLE`；不新增實體 placeholder。
- 回饋是 unverified self-report，不進 formal aggregates；不要求 logs、prompts、responses、attachments 或私有資料。

## Review Focus

1. 歷史 v0.4.0 段落被全域 replace 誤改：A1 僅檢查 current v0.8.0 區段且保留歷史指令。
2. 合成字典核准被放入 Confirmed facts：A2 的 maturity／assumptions 測試明確拒絕。
3. Research 偏差缺口被錯導向 SQL metadata gates：A2 檢查 research 與 implementation 邊界說明。
4. 使用者無問題完成卻被迫填問題：A3 optional-textarea 測試不允許 default／value 或 conditional-required 假設定。
5. 中文 dropdown 與英文語意不一致：A3 以固定 translation map 核對 ID、順序、選項與必要確認。

---

### Task A1: 文件中的資產版本與 trusted-SHA 流程

**Files:**
- Modify: `docs/installation.md:134`、`docs/installation.zh-TW.md:116`、`docs/architecture.md:111`
- Create/Test: `tests/test_public_core_docs.py`

**Interfaces:**
- Consumes: 現有 `.github/workflows/release.yml` 的 main dispatch 與 immutable `github.sha` checkout，以及現行 v0.8.0 文檔。
- Produces: 修正後的文件，沒有 Python API 或 workflow 行為變更。

- [x] **Step 1: 新增 `test_current_release_asset_names_are_consistent` 與 `test_release_docs_describe_dispatch_sha_not_tag_checkout`**

第一個測試對兩版 current verification H2 區段 assert 包含 `clin-nav-0.8.0.zip`、`clin-nav-0.8.0.manifest.json`，不含 `clin-nav-0.7.0.`；另 assert 歷史 v0.4.0 指令仍存在。第二個讀現有 YAML 的 jobs，assert preflight／validate／build checkout ref 為 `${{ github.sha }}`，文件說明 dispatch main、tag only verification／identity，不再描述 tag 控制 checkout。不要按完整段落字串綁定。

```python
@pytest.mark.parametrize(("name", "heading"), [
    ("installation.md", "## Current verified v0.8.0 Release artifact verification"),
    ("installation.zh-TW.md", "## 目前已驗證的 v0.8.0 Release 產物核對"),
])
def test_current_release_asset_names_are_consistent(name, heading):
    text = (ROOT / "docs" / name).read_text(encoding="utf-8")
    section = text.split(heading, 1)[1].split("\n## ", 1)[0]
    assert "clin-nav-0.8.0.zip" in section
    assert "clin-nav-0.8.0.manifest.json" in section
    assert "clin-nav-0.7.0." not in section
    assert 'release_version="0.4.0"' in text
```

新 test module 的 ROOT 定義為 `Path(__file__).resolve().parents[1]`。

- [x] **Step 2: RED**

Run `python -m pytest -q tests/test_public_core_docs.py --basetemp <fresh-external-basetemp>`。期望文件一致性 assertion 失敗；不能是語法、匯入或 tmp ACL 錯誤。

- [x] **Step 3: 僅修正文檔的錯誤敘述**

不改發布 hash、歷史 migration 指令或 release.yml；Current 資產名從 0.7.0 改為 0.8.0，architecture 描述與 trusted SHA 流程一致。

- [x] **Step 4: GREEN 與既有 recovery／activation 文檔測試**

Run `python -m pytest -q tests/test_public_core_docs.py tests/test_project_metadata.py --basetemp <fresh-external-basetemp>`。期望所有相關測試 pass，無文檔 recovery route 回歸。

- [x] **Step 5: Commit**

僅 add 上述三份 docs 與新 test module，commit `docs: align current release installation and trusted-sha guidance`。

### Task A2: 正式五欄 gaps 與三個不可執行範例

**Files:**
- Modify: `skills/clin-nav/SKILL.md:70`、`skills/clin-nav/references/evidence-output-template.md:65`、`skills/clin-nav/references/output-depths-and-learning-paths.md:102`
- Modify: `examples/teae-to-sas-spec.md`、`examples/omop-phenotype-to-sql-spec.md`、`examples/synthetic-institutional-mapping.md`
- Modify/Test: `tests/test_skill_contract.py:292`、`tests/test_public_core_docs.py`
- Review only: `skills/clin-nav/agents/openai.yaml`、`evals/cases.yaml`、`scripts/evaluate_response.py`、`tests/fixtures/baseline/`、`tests/fixtures/forward/`

**Interfaces:**
- Consumes: 現有正式共同 header、DEPTH_SECTION_CONTRACTS，以及 A1 的新 docs tests。
- Produces: Gap、Blocks、Next safe action、Responsible role、Completion evidence 五欄規則與完整 examples；不修改 evaluator schema、case IDs、既有得分／門檻或歷史 fixtures。

- [x] **Step 1: 新增失敗契約測試**

`test_formal_gaps_are_actionable_without_changing_quick_shape` assert template 定義上述五欄、safe authorization／role unknown／completion evidence／仍可完成工作，其他兩處 references 明確指向它，quick 段落仍無固定表頭要求。`test_examples_match_implementation_contract` 對三例 assert depth、六個非空 header、五個 implementation H2、單一 maturity、unmet gate 與 specification-only；dictionary-specified 例子的 Assumptions 必須明示 synthetic approval，不將 SYNTH 核准寫成 reviewed/confirmed 真實證據。`test_research_gaps_do_not_require_physical_execution_gates` 核對研究設計沒有被加上 Code maturity／Execution gate 必填章節。

```python
@pytest.mark.parametrize(("name", "maturity"), [
    ("teae-to-sas-spec.md", "dictionary-specified"),
    ("omop-phenotype-to-sql-spec.md", "conceptual"),
    ("synthetic-institutional-mapping.md", "dictionary-specified"),
])
def test_examples_match_implementation_contract(name, maturity):
    text = (ROOT / "examples" / name).read_text(encoding="utf-8")
    assert "Output depth: implementation specification" in text
    for section in ("Governing evidence", "Data contract", "Code maturity",
                    "Validation gaps", "Execution gate"):
        assert f"## {section}" in text
    assert maturity in text
    assert "SPECIFICATION ONLY — NOT EXECUTABLE" in text
    assert "unmet" in text.casefold()
```

同一測試再以既有共同 header patterns 檢查非空欄位，並擷取 Assumptions／Confirmed facts 分別核對 synthetic approval 的位置。

- [x] **Step 2: RED**

Run `python -m pytest -q tests/test_skill_contract.py tests/test_public_core_docs.py --basetemp <fresh-external-basetemp>`。期望因缺五欄／範例正式 header 而失敗。

- [x] **Step 3: 以單一規則來源更新 Skill、references 與 examples**

Template 定義 Gap 狀態與五欄表格；其餘文件引用模板而非完整重複。每個例子補「目前仍可完成的工作」，責任角色未知就待確認，不猜人名、schema、概念 ID 或真實查閱狀態。成熟度升級才重新評估全部 execution gates；research gaps 使用其設計適用的審閱條件。Evidence navigation 保留原 shape。

- [x] **Step 4: GREEN 與 deterministic Eval 不變檢查**

Run `python -m pytest -q tests/test_skill_contract.py tests/test_public_core_docs.py tests/test_response_evaluator.py --basetemp <fresh-external-basetemp>` 及 `python scripts/render_eval_summary.py --check`。期望 pass／exit 0；agents YAML 不需要新增 policy.products。若 catalog／evaluator／fixtures 確有必要行為調整，先停下報告契約衝突，不默默改 frozen baseline 或 scoring 來通過。

- [x] **Step 5: Commit**

僅 add 本 task 實際修改的 Skill、references、examples 與 tests，commit `feat: make formal validation gaps actionable`；review-only 檔案不要無故重寫。

### Task A3: 雙語低負擔 Issue Forms 與 README 入口

**Files:**
- Modify: `.github/ISSUE_TEMPLATE/usability-feedback.yml`、`README.md`、`README.zh-TW.md`
- Create: `.github/ISSUE_TEMPLATE/usability-feedback.zh-TW.yml`、`tests/test_usability_feedback_forms.py`
- Modify/Test: `tests/test_project_metadata.py:4613`（僅調整現有 textarea 必填假設與共用確認斷言）

**Interfaces:**
- Consumes: 現有 field IDs／英文選項語義；GitHub 表單入口 `https://github.com/mtchuang1981/clin-data-nav/issues/new?template=<filename>`。
- Produces: 八個 input IDs 的雙語對應（repository_version、installation_method、agent、operating_system、task_category、completion_outcome、problem_reproduction、acknowledgement），不新增 upload／raw-material 欄位。

- [x] **Step 1: 新增表單失敗測試**

`test_no_problem_feedback_may_omit_description` assert problem_reproduction required false、render text、無 default/value/max_length，completion_outcome 無 default。`test_feedback_forms_preserve_semantic_parity` 核對 ID 順序與每個選項的明確翻譯 map。安裝選項依序為「npx 專案安裝／已核對 ZIP 安裝／本機開發 checkout」；OS 為 Linux/macOS/Windows/其他或混合；任務為「安裝或更新／快速解說／證據導覽／研究設計／實作規格／repository benchmark 工具」；結果為「無問題完成／遇到問題但完成／未完成」。`test_feedback_readmes_open_forms_not_yaml_source` 核對英文／繁中入口各選正確 template。`test_forms_do_not_solicit_raw_material` 檢查雙語警語、required checkbox option 與 closed ID set。

```python
@pytest.mark.parametrize("filename", ["usability-feedback.yml", "usability-feedback.zh-TW.yml"])
def test_no_problem_feedback_may_omit_description(filename):
    payload = yaml.safe_load((ROOT / ".github/ISSUE_TEMPLATE" / filename).read_text(encoding="utf-8"))
    fields = {row["id"]: row for row in payload["body"] if "id" in row}
    description = fields["problem_reproduction"]
    assert description["validations"]["required"] is False
    assert description["attributes"]["render"] == "text"
    assert not {"value", "default", "max_length"} & description["attributes"].keys()
    assert "default" not in fields["completion_outcome"]["attributes"]
    assert fields["acknowledgement"]["attributes"]["options"][0]["required"] is True
```

- [x] **Step 2: RED**

Run `python -m pytest -q tests/test_usability_feedback_forms.py --basetemp <fresh-external-basetemp>`。期望因缺繁中表單、textarea 必填與入口缺失而失敗。

- [x] **Step 3: 更新表單與入口，保留 truthful claim boundary**

兩版說明只填約 1,000 字元公開／合成摘要；禁止 prompts、responses、logs、screenshots、attachments 及既有敏感類別。無問題可留白。確認 option 設 required true；不假造 conditional-required 或 max_length 屬性。README 不把 self-report 當成已驗證使用成效；benchmark-result.yml 不改。

- [x] **Step 4: GREEN**

Run `python -m pytest -q tests/test_usability_feedback_forms.py tests/test_project_metadata.py tests/test_public_boundary.py --basetemp <fresh-external-basetemp>`，再跑 public-boundary CLI。期望 pass／exit 0；這輪不改 scanner 行為。若新公開表單意外被拒絕，先查根因並回報，不順手放寬 private-artifact 規則。

- [x] **Step 5: Commit**

僅 add 兩 forms、兩 README 與相關 tests，commit `feat: add safe bilingual community feedback forms`。
