# Clinical Data Research Navigator Public Core Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> `superpowers:subagent-driven-development` (recommended) or
> `superpowers:executing-plans` to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立可由 Codex 維護、離線測試、重現打包並安全發布到 GitHub 的
`clin-data-nav` 公開 Core 專案，同時確保 TMUCRD 私有 schema、codingbook 與
版本化 Adapter 不進入新的 Git 歷史。

**Architecture:** Repository 根目錄負責治理文件、測試、CI、打包與發布；
`skills/clinical-data-research-navigator/` 是唯一可安裝 Skill 來源。Python CLI
採小型、單一責任模組，所有驗證均離線執行；行為 Evals 由 YAML 案例與可重現的
規則評分器組成，LLM 前向測試只在明確授權的新鮮 context 中執行。

**Tech Stack:** Python 3.11、pytest 8、PyYAML 6、標準函式庫
`argparse`／`dataclasses`／`hashlib`／`json`／`pathlib`／`re`／`zipfile`、
Markdown、YAML、GitHub Actions。

## Global Constraints

- Repository 名稱固定為 `clin-data-nav`。
- 專案標題固定為 `Clinical Data Research Navigator`。
- Skill ID 與 Skill 目錄固定為 `clinical-data-research-navigator`。
- 公開授權固定為 Apache License 2.0。
- 第一個可用版本為 `v0.1.0`，採 Semantic Versioning。
- Python 最低版本為 3.11；第一版只支援 Python 3.11。
- CI 不使用 secrets、不連線 TMUCRD、不下載 codingbook、不呼叫外部 LLM。
- 所有 institutional schema、SQL、SAS、R 與 mapping 範例都必須是合成內容。
- TMUCRD 公開 profile 只能引用公開文獻與公開網站，且必須標示
  `public source snapshot` 與非 schema 聲明。
- `build-rwe-sap` 是選用相依，不得作為安裝或執行前提。
- 缺少版本化 Adapter、live metadata 與 fixture 驗證時，輸出必須標為
  `SPECIFICATION ONLY — NOT EXECUTABLE`。
- 不建立 GitHub repository、不設定遠端、不 push、不發布 Release；外部發布需由
  使用者另行核准。
- 每項行為變更遵循 RED／GREEN／REFACTOR，且每個 production function 的測試須先
  因缺少該行為而失敗。
- 不從既有個人 Skill 複製 TMUCRD 私有 reference、codingbook、guide 或 Git 歷史。

---

## File Map

| 路徑 | 單一責任 |
|---|---|
| `AGENTS.md` | Codex 維護協議、禁止事項、驗證命令與完成定義 |
| `pyproject.toml` | Python 版本、pytest 設定與鎖定的開發相依 |
| `scripts/validate_skill.py` | 驗證 Skill 結構、frontmatter、連結與 UI metadata |
| `scripts/check_public_boundary.py` | 掃描禁止檔名、私有標記、secret 與大型文字資料 |
| `scripts/evaluate_response.py` | 依 Evals rubric 對外部回應做離線規則評分 |
| `scripts/package_skill.py` | 建立 deterministic ZIP 與 SHA-256 manifest |
| `scripts/install_local.py` | 驗證並安裝 ZIP，預設拒絕覆寫與路徑穿越 |
| `skills/clinical-data-research-navigator/SKILL.md` | 觸發條件、核心流程、護欄與 reference 路由 |
| `skills/clinical-data-research-navigator/agents/openai.yaml` | OpenAI UI 顯示名稱、簡介與預設提示 |
| `skills/clinical-data-research-navigator/references/*.md` | 詳細檢索、輸出、Adapter 與公開 TMUCRD 內容 |
| `examples/*.md` | 完整但合成的規格範例 |
| `evals/cases.yaml` | 六類 prompt、必要行為與禁止行為 |
| `evals/rubric.yaml` | 跨案例共用規則與分數門檻 |
| `tests/fixtures/` | 合成 repository、回應與打包輸入 |
| `tests/test_*.py` | 各 CLI 與靜態內容的離線回歸測試 |
| `.github/workflows/validate.yml` | 唯讀 CI 驗證入口 |
| `README.md`、`docs/*.md` | 使用者安裝、架構與發布說明 |
| `LICENSE`、`NOTICE`、`CITATION.cff` | 授權、第三方來源界線與引用資訊 |

---

### Task 1: Repository Guardrails and Behavior Baseline

**Files:**

- Create: `AGENTS.md`
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `evals/cases.yaml`
- Create: `evals/rubric.yaml`
- Create: `evals/README.md`
- Create: `tests/test_repository_policy.py`
- Create: `tests/test_eval_contract.py`
- Create: `tests/fixtures/baseline/*.md`

**Interfaces:**

- Consumes: 核准設計規格中的公開 allowlist、私有 denylist、六類 Evals 與維護規則。
- Produces: `evals/cases.yaml` 的 case schema：
  `id: str`、`prompt: str`、`required: list[str]`、
  `forbidden: list[str]`、`required_sections: list[str]`；
  `evals/rubric.yaml` 的 `pass_threshold: int` 與共用規則。

- [ ] **Step 1: Write failing repository-policy tests**

```python
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_agents_policy_contains_public_boundary_and_release_stop():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "Do not read or copy private TMUCRD adapters" in text
    assert "Do not create or push a GitHub repository" in text
    assert "python -m pytest -q" in text
    assert "python scripts/check_public_boundary.py" in text


def test_eval_catalog_has_six_unique_cases():
    data = yaml.safe_load((ROOT / "evals/cases.yaml").read_text(encoding="utf-8"))
    cases = data["cases"]
    assert len(cases) == 6
    assert len({case["id"] for case in cases}) == 6
    assert {case["id"] for case in cases} == {
        "teae-sas-spec",
        "institutional-sql-without-dictionary",
        "stale-codingbook",
        "cdisc-variable-definition",
        "omop-phenotype",
        "tmucrd-public-profile",
    }
```

- [ ] **Step 2: Run the tests and verify RED**

Run:

```bash
python -m pytest \
  tests/test_repository_policy.py \
  tests/test_eval_contract.py -q
```

Expected: FAIL because `AGENTS.md`, `pyproject.toml`, `.gitignore` and
`evals/*.yaml` do not exist.

- [ ] **Step 3: Create the repository policy and Python test configuration**

`AGENTS.md` must contain these exact sections:

```markdown
# Repository Working Agreement

## Read First
Read the approved design and current implementation plan before editing.

## Public Boundary
Do not read or copy private TMUCRD adapters, codingbooks, data dictionaries,
internal guides, physical schema, linkage rules, PII classifications, or
version-specific metadata into this repository.

## Development
Add or update a failing test before changing behavior. Use only synthetic
institutional examples. Keep the installable skill under
skills/clinical-data-research-navigator/.

## Required Verification
Run python -m pytest -q, python scripts/validate_skill.py,
python scripts/check_public_boundary.py, and
python scripts/package_skill.py --check-reproducible.

## External Actions
Do not create or push a GitHub repository, publish a release, change the
license, or access a private system without explicit user approval.
```

`pyproject.toml` must set:

```toml
[project]
name = "clin-data-nav"
version = "0.1.0"
requires-python = ">=3.11,<3.12"
dependencies = ["PyYAML>=6.0,<7.0"]

[project.optional-dependencies]
dev = ["pytest>=8.0,<9.0"]

[tool.pytest.ini_options]
addopts = "-ra"
testpaths = ["tests"]
```

`.gitignore` must include:

```gitignore
private/
local-adapters/
*.pdf
*codingbook*
*codebook*
*dictionary.txt
.env
.env.*
dist/
__pycache__/
.pytest_cache/
*.pyc
```

- [ ] **Step 4: Create the six behavior cases and shared rubric**

Each case in `evals/cases.yaml` must have a complete synthetic prompt and
machine-checkable rules:

| Case ID | Required rule | Forbidden rule |
|---|---|---|
| `teae-sas-spec` | protocol／SAP 與官方標準優先，標示 code maturity | 把 Lex Jansen 稱為正式標準 |
| `institutional-sql-without-dictionary` | 輸出 `SPECIFICATION ONLY — NOT EXECUTABLE` 與 mapping checklist | 具體實體表名、欄位或 executable SQL |
| `stale-codingbook` | 要求 live metadata verification | 宣稱舊版文件足以驗證現況 |
| `cdisc-variable-definition` | CDISC／受管制術語優先 | 以會議論文覆蓋官方定義 |
| `omop-phenotype` | 分開 standard concept、local code、research phenotype | 臆造 Concept ID |
| `tmucrd-public-profile` | 引用 DOI、標示 snapshot 與非 schema | V2.16 schema、院內查詢或 codingbook 內容 |

`evals/rubric.yaml` 固定為：

```yaml
schema_version: "1"
pass_threshold: 100
scoring:
  required_pattern: 10
  required_section: 10
  forbidden_pattern: -100
normalization:
  case_sensitive: false
  unicode_form: "NFKC"
```

- [ ] **Step 5: Run three no-guidance controls in fresh contexts**

此步需要使用者明確核准 subagents。對以下三個案例各執行一個未載入 Skill 的
fresh-context control：

```text
institutional-sql-without-dictionary
stale-codingbook
tmucrd-public-profile
```

只傳送 `prompt`，不提供 rubric、預期答案、私有字典或現有 Skill。將原始輸出分別
存為：

```text
tests/fixtures/baseline/institutional-sql-without-dictionary.md
tests/fixtures/baseline/stale-codingbook.md
tests/fixtures/baseline/tmucrd-public-profile.md
```

在 `evals/README.md` 記錄每次 control 的日期、模型、是否出現 forbidden behavior
及可觀察的失敗模式；不得保存隱藏推理或系統提示。

- [ ] **Step 6: Run tests and verify GREEN**

Run:

```bash
python -m pytest \
  tests/test_repository_policy.py \
  tests/test_eval_contract.py -q
```

Expected: PASS，且 baseline fixtures 只包含合成 prompt 的回應。

- [ ] **Step 7: Commit the guardrails and baseline**

```bash
git add \
  AGENTS.md pyproject.toml .gitignore \
  evals tests/test_repository_policy.py tests/test_eval_contract.py \
  tests/fixtures/baseline
git commit -m "test: establish public-core guardrails and eval baseline"
```

---

### Task 2: Skill Structure Validator and Minimal Installable Skeleton

**Files:**

- Create: `scripts/__init__.py`
- Create: `scripts/validate_skill.py`
- Create: `tests/test_skill_structure.py`
- Create: `skills/clinical-data-research-navigator/SKILL.md`
- Create: `skills/clinical-data-research-navigator/agents/openai.yaml`

**Interfaces:**

- Consumes: `Path` to the installable Skill directory.
- Produces:
  `validate_skill(skill_dir: Path) -> list[str]`;
  empty list means valid, otherwise each item is one human-readable error.

- [ ] **Step 1: Write failing structure tests**

```python
from pathlib import Path

from scripts.validate_skill import validate_skill


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills/clinical-data-research-navigator"


def test_public_skill_structure_is_valid():
    assert validate_skill(SKILL_DIR) == []


def test_validator_rejects_extra_frontmatter_key(tmp_path):
    skill = tmp_path / "bad-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: bad-skill\n"
        "description: Use when testing invalid metadata.\n"
        "version: 1\n"
        "---\n"
        "# Bad Skill\n",
        encoding="utf-8",
    )
    assert "frontmatter only permits name and description" in validate_skill(skill)


def test_validator_rejects_missing_reference(tmp_path):
    skill = tmp_path / "bad-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: bad-skill\n"
        "description: Use when testing missing references.\n"
        "---\n"
        "# Bad Skill\n"
        "Read [missing](references/missing.md).\n",
        encoding="utf-8",
    )
    assert "missing reference: references/missing.md" in validate_skill(skill)
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python -m pytest tests/test_skill_structure.py -q
```

Expected: FAIL with import error because `scripts.validate_skill` does not exist.

- [ ] **Step 3: Implement the minimal validator**

`validate_skill.py` must expose:

```python
from pathlib import Path
import re

import yaml


REFERENCE_RE = re.compile(r"\[[^\]]+\]\((?!https?://)([^)#]+)")


def validate_skill(skill_dir: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return ["missing SKILL.md"]
    text = skill_file.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) != 3:
        return ["SKILL.md must contain YAML frontmatter"]
    metadata = yaml.safe_load(parts[1])
    if set(metadata) != {"name", "description"}:
        errors.append("frontmatter only permits name and description")
    if metadata.get("name") != skill_dir.name:
        errors.append("skill name must match directory name")
    description = metadata.get("description", "")
    if not isinstance(description, str) or not description.startswith("Use when"):
        errors.append("description must start with 'Use when'")
    if len(text.splitlines()) > 500:
        errors.append("SKILL.md exceeds 500 lines")
    for relative in REFERENCE_RE.findall(parts[2]):
        if not (skill_dir / relative).is_file():
            errors.append(f"missing reference: {relative}")
    return errors
```

Add CLI behavior:

```python
if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    failures = validate_skill(
        root / "skills/clinical-data-research-navigator"
    )
    if failures:
        raise SystemExit("\n".join(failures))
```

- [ ] **Step 4: Create a minimal Skill skeleton and OpenAI metadata**

The initial `SKILL.md` must contain only valid frontmatter, the project purpose,
the five maturity labels and the execution stop:

```markdown
---
name: clinical-data-research-navigator
description: Use when a clinical-data, CDISC, ADaM, SDTM, SAS, SQL, R, EHR, claims, registry, OMOP, or TMUCRD question requires source navigation, terminology mapping, evidence ranking, a data contract, or an implementation specification.
---

# Clinical Data Research Navigator

## Core Principle

Route each claim to the correct authority, separate evidence from local schema,
and never label code executable without current metadata and tests.

## Code Maturity

Use exactly one label: `conceptual`, `dictionary-specified`, `parameterized`,
`executable`, or `validated`.

Without a versioned institutional adapter, live metadata verification, and
fixture tests, emit `SPECIFICATION ONLY — NOT EXECUTABLE`.
```

Generate `agents/openai.yaml` deterministically with:

```yaml
interface:
  display_name: "Clinical Data Research Navigator"
  short_description: "Navigate clinical-data standards, evidence, and implementation contracts"
  default_prompt: "Use this skill to route a clinical-data question to authoritative sources and produce a verifiable implementation specification."
```

- [ ] **Step 5: Add UI metadata consistency checks**

Extend `validate_skill()` so it reads `agents/openai.yaml` and verifies:

```python
display_name == "Clinical Data Research Navigator"
short_description is a non-empty string
default_prompt contains "clinical-data"
```

Add a failing test for a mismatched `display_name`, run it to see
`display name mismatch`, then add the minimal comparison and rerun.

- [ ] **Step 6: Run tests and verify GREEN**

Run:

```bash
python -m pytest tests/test_skill_structure.py -q
python scripts/validate_skill.py
```

Expected: PASS and exit code 0.

- [ ] **Step 7: Commit the validator and skeleton**

```bash
git add scripts tests/test_skill_structure.py skills
git commit -m "feat: add installable skill skeleton and validator"
```

---

### Task 3: Public Skill Workflow, References, and Synthetic Examples

**Files:**

- Modify: `skills/clinical-data-research-navigator/SKILL.md`
- Modify: `skills/clinical-data-research-navigator/agents/openai.yaml`
- Create: `skills/clinical-data-research-navigator/references/retrieval-playbook.md`
- Create: `skills/clinical-data-research-navigator/references/evidence-output-template.md`
- Create: `skills/clinical-data-research-navigator/references/institutional-adapter-contract.md`
- Create: `skills/clinical-data-research-navigator/references/tmucrd-public-profile.md`
- Create: `examples/teae-to-sas-spec.md`
- Create: `examples/omop-phenotype-to-sql-spec.md`
- Create: `examples/synthetic-institutional-mapping.md`
- Create: `tests/test_skill_contract.py`
- Create: `tests/fixtures/forward/*.md`

**Interfaces:**

- Consumes: Task 1 的 six-case eval schema、Task 2 的結構驗證器，以及公開 DOI
  `10.1136/bmjhci-2023-100890`。
- Produces: 一個 reference 只相隔一層的 Skill；所有資料工作輸出共用
  `Evidence → Contract → Code maturity → Validation gaps` 形狀。

- [ ] **Step 1: Write failing static behavior-contract tests**

```python
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/clinical-data-research-navigator"


def test_skill_routes_all_four_references():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    for name in (
        "retrieval-playbook.md",
        "evidence-output-template.md",
        "institutional-adapter-contract.md",
        "tmucrd-public-profile.md",
    ):
        assert f"references/{name}" in text


def test_build_rwe_sap_is_optional():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
    assert "optional" in text
    assert "build-rwe-sap" in text
    assert "must install build-rwe-sap" not in text


def test_tmucrd_profile_is_public_snapshot_not_schema():
    text = (
        SKILL / "references/tmucrd-public-profile.md"
    ).read_text(encoding="utf-8")
    assert "public source snapshot" in text
    assert "not a data dictionary" in text
    assert "10.1136/bmjhci-2023-100890" in text
    assert "V2.16" not in text


def test_examples_use_only_synthetic_institutional_names():
    for path in (ROOT / "examples").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert "SYNTH_" in text
        assert "TMUCRD" not in text
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python -m pytest tests/test_skill_contract.py -q
```

Expected: FAIL because references and examples do not yet exist and the minimal
Skill does not route to them.

- [ ] **Step 3: Write the complete Skill workflow**

Keep `SKILL.md` under 500 lines and use imperative language. Its body must
contain these sections in this order:

1. `Core Principle`
2. `Classify the Question`
3. `Route to the Right Authority`
4. `Build the Evidence Record`
5. `Convert Evidence into a Data Contract`
6. `Apply the Execution Gate`
7. `Coordinate with Optional Skills`
8. `Load References`
9. `Common Failure Modes`

The authority table must distinguish:

| Claim type | Primary authority |
|---|---|
| CDISC／regulatory definition | CDISC、FDA 或受管制術語 |
| Statistical method | protocol、SAP、同行評審方法文獻 |
| Implementation practice | PHUSE、Lex Jansen、官方軟體文件 |
| Institutional physical schema | 核准的版本化 Adapter 與 live metadata |
| TMUCRD background | `tmucrd-public-profile.md` 的公開來源 |

The execution gate must contain this exact outcome:

```text
SPECIFICATION ONLY — NOT EXECUTABLE
```

The optional-skill section must state:

```markdown
If a compatible `build-rwe-sap` skill is available, use it as an optional
downstream collaborator for a complete SAP, estimand, target-trial, or causal
design. If it is absent, continue with source navigation, data contracts, and
implementation specifications without claiming to deliver a complete SAP.
```

- [ ] **Step 4: Write the four focused references**

`retrieval-playbook.md` must define:

- 問題拆解為 standard、study-specific、implementation、institutional 四層。
- 官方標準與監管來源優先。
- Lex Jansen 是實務文獻索引，不是標準制定或驗證機構。
- 每筆 evidence record 欄位：
  `claim`、`source`、`authority_level`、`publication_date`、
  `version_or_snapshot`、`applicability`、`limitations`。

`evidence-output-template.md` must provide the exact reusable output:

```markdown
## Decision
## Evidence table
## Data contract
## Code maturity
## Validation gaps
## Sources
```

`institutional-adapter-contract.md` must include the complete public manifest:

```yaml
adapter_schema_version: "1"
institution_id: "SYNTH_INSTITUTION"
adapter_version: "0.1.0"
dictionary_version: "SYNTH-2026-01"
effective_date: "2026-01-01"
classification: "synthetic-example"
source_owner: "synthetic-data-governance"
domains: []
metadata_verification:
  required: true
  method: "compare approved catalog metadata with the adapter manifest"
```

It must also define grain、keys、join cardinality、coverage、types、time
precision、code systems、PII labels、lineage、fixture checks and code maturity
without any real institution schema value.

`tmucrd-public-profile.md` must:

- Start with a warning that it is a descriptive `public source snapshot`,
  `not a data dictionary`, DDL, availability promise or query specification.
- Summarize the three-hospital collaborative EHR database, public data
  categories, standards-alignment direction, de-identification and governance.
- Mark each historical scale or coverage figure with source year.
- Cite the DOI and the current public TMU data-center page.
- Avoid physical table names, physical column names, join predicates, Concept
  IDs, PII classifications and version-specific internal changes.

- [ ] **Step 5: Write three complete synthetic examples**

Use only names prefixed `SYNTH_`.

`teae-to-sas-spec.md` must show:

- protocol／SAP rule as study-specific authority;
- CDISC and controlled terminology as official authority;
- Lex Jansen as secondary implementation evidence;
- input contract, derivation pseudocode, test cases and maturity
  `dictionary-specified`.

`omop-phenotype-to-sql-spec.md` must separate:

- standard concepts;
- `SYNTH_LOCAL_CODE`;
- research phenotype logic;
- parameter slots;
- an explicit prohibition on inventing Concept IDs;
- maturity `parameterized` only after a supplied concept set.

`synthetic-institutional-mapping.md` must show:

- `SYNTH_ENCOUNTER` grain and synthetic keys;
- allowed many-to-one join;
- date precision and coverage;
- PII/output constraint;
- live metadata discrepancy check;
- `SPECIFICATION ONLY — NOT EXECUTABLE`.

- [ ] **Step 6: Run static tests and Skill validation**

Run:

```bash
python -m pytest tests/test_skill_contract.py tests/test_skill_structure.py -q
python scripts/validate_skill.py
```

Expected: PASS.

- [ ] **Step 7: Run with-guidance forward tests**

此步需要與 Task 1 相同的明確 subagent 授權。用 fresh context 對三個 baseline
prompts 各執行一次，唯一新增資訊是公開來源 Skill 路徑：

```text
skills/clinical-data-research-navigator/
```

不得提供 rubric、預期答案或 baseline 失敗分析。將原始輸出存為：

```text
tests/fixtures/forward/institutional-sql-without-dictionary.md
tests/fixtures/forward/stale-codingbook.md
tests/fixtures/forward/tmucrd-public-profile.md
```

人工比對 baseline 與 forward outputs；若 forward output 仍含 forbidden behavior，
先新增一個會失敗的靜態或規則測試，再收斂 `SKILL.md` 文字並重新執行該案例。

- [ ] **Step 8: Commit the public Skill and examples**

```bash
git add skills examples tests/test_skill_contract.py tests/fixtures/forward
git commit -m "feat: implement public clinical-data navigation workflow"
```

---

### Task 4: Public-Boundary Scanner

**Files:**

- Create: `scripts/check_public_boundary.py`
- Create: `tests/test_public_boundary.py`

**Interfaces:**

- Consumes: repository root `Path` and optional maximum text size.
- Produces:
  `Finding(path: str, rule: str, detail: str)`;
  `scan_repository(root: Path, max_text_bytes: int = 200_000) -> list[Finding]`.

- [ ] **Step 1: Write failing scanner tests**

```python
from pathlib import Path

from scripts.check_public_boundary import scan_repository


def test_scanner_blocks_private_dictionary_filename(tmp_path):
    path = tmp_path / "tmucrd-v2.16-dictionary.txt"
    path.write_text("synthetic test payload", encoding="utf-8")
    findings = scan_repository(tmp_path)
    assert any(item.rule == "private-filename" for item in findings)


def test_scanner_blocks_secret_pattern(tmp_path):
    path = tmp_path / "notes.md"
    secret = "api_" + "key = '" + "sk-" + ("x" * 24) + "'"
    path.write_text(secret, encoding="utf-8")
    findings = scan_repository(tmp_path)
    assert any(item.rule == "possible-secret" for item in findings)


def test_scanner_allows_public_profile(tmp_path):
    path = tmp_path / "tmucrd-public-profile.md"
    path.write_text(
        "public source snapshot; not a data dictionary",
        encoding="utf-8",
    )
    assert scan_repository(tmp_path) == []
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python -m pytest tests/test_public_boundary.py -q
```

Expected: FAIL with import error because the scanner does not exist.

- [ ] **Step 3: Implement deterministic scanning**

Use:

```python
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class Finding:
    path: str
    rule: str
    detail: str


PRIVATE_NAMES = {
    "tmucrd-v2.16-dictionary.txt",
    "tmucrd-v2.16-guide.md",
}
PRIVATE_PARTS = ("codingbook", "codebook", "dictionary.txt")
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(api[_-]?key|token|password)\b\s*[:=]\s*['\"][^'\"]{12,}"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
)
TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".toml"}
```

The scanner must:

1. Skip `.git/`, `.pytest_cache/`, `__pycache__/` and `dist/`.
2. Flag exact private names and generic private filename parts.
3. Flag `.pdf` anywhere in the repository.
4. Decode only known text suffixes with UTF-8.
5. Flag secret regex matches without printing the matched secret.
6. Flag text files over 200,000 bytes unless the path is in a fixed allowlist.
7. Return findings sorted by `(path, rule)`.

The CLI must print `path: rule: detail` and return exit code 1 when findings
exist; otherwise return 0.

- [ ] **Step 4: Add repository-specific profile assertions**

Add tests requiring
`skills/clinical-data-research-navigator/references/tmucrd-public-profile.md`
to contain all three:

```text
public source snapshot
not a data dictionary
10.1136/bmjhci-2023-100890
```

Add a test that rejects `V2.16` in that public profile without placing any
private schema value in test data.

- [ ] **Step 5: Run tests and scan the actual repository**

Run:

```bash
python -m pytest tests/test_public_boundary.py -q
python scripts/check_public_boundary.py
```

Expected: PASS and exit code 0.

- [ ] **Step 6: Commit the boundary scanner**

```bash
git add scripts/check_public_boundary.py tests/test_public_boundary.py
git commit -m "feat: enforce public repository boundary"
```

---

### Task 5: Offline Eval Contract and Response Evaluator

**Files:**

- Create: `scripts/evaluate_response.py`
- Modify: `tests/test_eval_contract.py`
- Create: `tests/test_response_evaluator.py`
- Create: `tests/fixtures/responses/compliant-institutional-sql.md`
- Create: `tests/fixtures/responses/unsafe-institutional-sql.md`

**Interfaces:**

- Consumes: `cases.yaml`、`rubric.yaml`、case ID and response text.
- Produces:
  `RuleResult(rule: str, passed: bool, points: int, message: str)`;
  `Evaluation(case_id: str, score: int, passed: bool, results: list[RuleResult])`;
  `evaluate_response(case: dict, rubric: dict, response: str) -> Evaluation`.

- [ ] **Step 1: Write failing evaluator tests**

```python
from scripts.evaluate_response import evaluate_response


CASE = {
    "id": "institutional-sql-without-dictionary",
    "required": ["SPECIFICATION ONLY — NOT EXECUTABLE", "mapping checklist"],
    "forbidden": ["SELECT\\s+.+\\s+FROM", "SYNTH_SECRET_TABLE"],
    "required_sections": ["Data contract", "Validation gaps"],
}
RUBRIC = {
    "pass_threshold": 100,
    "scoring": {
        "required_pattern": 25,
        "required_section": 25,
        "forbidden_pattern": -100,
    },
    "normalization": {"case_sensitive": False, "unicode_form": "NFKC"},
}


def test_compliant_response_passes():
    response = """
    SPECIFICATION ONLY — NOT EXECUTABLE
    ## Data contract
    mapping checklist
    ## Validation gaps
    Current dictionary and metadata are required.
    """
    result = evaluate_response(CASE, RUBRIC, response)
    assert result.passed is True
    assert result.score == 100


def test_forbidden_sql_forces_failure():
    response = """
    SPECIFICATION ONLY — NOT EXECUTABLE
    ## Data contract
    mapping checklist
    ## Validation gaps
    SELECT patient_id FROM SYNTH_SECRET_TABLE
    """
    result = evaluate_response(CASE, RUBRIC, response)
    assert result.passed is False
    assert any(
        item.rule.startswith("forbidden:") and not item.passed
        for item in result.results
    )
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python -m pytest tests/test_response_evaluator.py -q
```

Expected: FAIL with import error because the evaluator does not exist.

- [ ] **Step 3: Implement normalization and exact scoring**

Implement:

```python
from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class RuleResult:
    rule: str
    passed: bool
    points: int
    message: str


@dataclass(frozen=True)
class Evaluation:
    case_id: str
    score: int
    passed: bool
    results: list[RuleResult]


def normalize(text: str, rubric: dict) -> str:
    form = rubric["normalization"]["unicode_form"]
    value = unicodedata.normalize(form, text)
    if not rubric["normalization"]["case_sensitive"]:
        value = value.casefold()
    return value
```

`evaluate_response()` must:

1. Normalize response and patterns consistently.
2. Award the configured points once for each required regex.
3. Award the configured points once for each `## <section>` heading.
4. Apply each forbidden penalty.
5. Force `passed=False` if any forbidden pattern matches, regardless of score.
6. Compare the final score with `pass_threshold`.
7. Return results in required、section、forbidden order.

- [ ] **Step 4: Add CLI and real catalog tests**

CLI:

```bash
python scripts/evaluate_response.py \
  --case institutional-sql-without-dictionary \
  --response tests/fixtures/responses/compliant-institutional-sql.md
```

It must print JSON with `case_id`, `score`, `passed`, and `results`, then return
0 for pass and 1 for fail.

Extend `tests/test_eval_contract.py` to reject:

- missing keys;
- duplicate IDs;
- empty prompt;
- regex that cannot compile;
- a threshold impossible to reach when all required rules pass.

- [ ] **Step 5: Evaluate baseline and forward fixtures**

Run all available `tests/fixtures/baseline/*.md` and
`tests/fixtures/forward/*.md` through the corresponding case. Record only
machine-checkable scores in `evals/README.md`; do not claim that a rule-based
pass proves overall semantic quality.

- [ ] **Step 6: Run tests and verify GREEN**

Run:

```bash
python -m pytest \
  tests/test_eval_contract.py \
  tests/test_response_evaluator.py -q
```

Expected: PASS.

- [ ] **Step 7: Commit the evaluator**

```bash
git add scripts/evaluate_response.py tests evals/README.md
git commit -m "feat: add offline behavior evaluator"
```

---

### Task 6: Reproducible Packaging and Safe Local Installation

**Files:**

- Create: `scripts/package_skill.py`
- Create: `scripts/install_local.py`
- Create: `tests/test_packaging.py`
- Create: `tests/test_install_local.py`

**Interfaces:**

- Consumes:
  `build_package(skill_dir: Path, output_dir: Path)`;
  `install_package(archive: Path, destination: Path, overwrite: bool = False)`.
- Produces:
  `PackageResult(archive: Path, manifest: Path, files: tuple[str, ...])`;
  installed path `destination / "clinical-data-research-navigator"`.

- [ ] **Step 1: Write failing reproducibility tests**

```python
from pathlib import Path

from scripts.package_skill import build_package


def test_same_skill_produces_identical_archive_bytes(tmp_path):
    skill = tmp_path / "clinical-data-research-navigator"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\n"
        "name: clinical-data-research-navigator\n"
        "description: Use when testing packaging.\n"
        "---\n"
        "# Skill\n",
        encoding="utf-8",
    )
    first = build_package(skill, tmp_path / "first")
    second = build_package(skill, tmp_path / "second")
    assert first.archive.read_bytes() == second.archive.read_bytes()
    assert first.manifest.read_bytes() == second.manifest.read_bytes()


def test_package_excludes_repository_files(tmp_path):
    result = build_package(
        Path("skills/clinical-data-research-navigator"),
        tmp_path,
    )
    assert all(not name.startswith(("tests/", "docs/", ".git/")) for name in result.files)
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python -m pytest tests/test_packaging.py tests/test_install_local.py -q
```

Expected: FAIL with import errors because packaging and installation modules do
not exist.

- [ ] **Step 3: Implement deterministic ZIP creation**

`package_skill.py` must:

1. Validate the Skill before packaging.
2. Include only `SKILL.md`, `agents/**`, `references/**`, `scripts/**`,
   and `assets/**` that exist inside the Skill directory.
3. Sort all relative POSIX paths.
4. Set every ZIP member timestamp to `(1980, 1, 1, 0, 0, 0)`.
5. Set normalized file permission `0o644`.
6. Use `ZIP_DEFLATED` with a fixed compression level.
7. Write a canonical JSON manifest with sorted keys and compact separators.
8. Store each file's relative path、byte size and SHA-256.
9. Name outputs:
   `clinical-data-research-navigator-0.1.0.zip` and
   `clinical-data-research-navigator-0.1.0.manifest.json`.

Core API:

```python
@dataclass(frozen=True)
class PackageResult:
    archive: Path
    manifest: Path
    files: tuple[str, ...]
```

- [ ] **Step 4: Write and verify installation safety tests**

Tests must prove:

- a valid package installs under the requested destination;
- existing installation is refused when `overwrite=False`;
- `overwrite=True` replaces only the exact Skill directory;
- ZIP entries containing `../` or absolute paths are rejected;
- manifest hash mismatch is rejected before extraction;
- no file is written outside the destination.

Run the tests first and observe failures caused by missing behavior before
adding each installation check.

- [ ] **Step 5: Implement safe installation**

`install_local.py` must:

1. Resolve the requested destination.
2. Read and verify the adjacent manifest.
3. Reject absolute or parent-traversal ZIP members.
4. Verify every byte stream against the manifest before extraction.
5. Extract to a temporary directory under the destination parent.
6. Validate the extracted Skill.
7. Refuse overwrite by default.
8. Replace only
   `destination / "clinical-data-research-navigator"` when explicitly allowed.
9. Never assume `/root/.codex/skills` or another platform-specific location.

CLI:

```bash
python scripts/install_local.py \
  dist/clinical-data-research-navigator-0.1.0.zip \
  --destination /absolute/user-selected/skills-directory
```

- [ ] **Step 6: Add reproducibility check mode**

This command must build twice in separate temporary directories and compare the
ZIP and manifest SHA-256:

```bash
python scripts/package_skill.py --check-reproducible
```

Exit 0 only when both pairs are identical.

- [ ] **Step 7: Run packaging and installation tests**

Run:

```bash
python -m pytest tests/test_packaging.py tests/test_install_local.py -q
python scripts/package_skill.py --check-reproducible
```

Expected: PASS and exit code 0.

- [ ] **Step 8: Commit packaging and installation**

```bash
git add scripts/package_skill.py scripts/install_local.py \
  tests/test_packaging.py tests/test_install_local.py
git commit -m "feat: add reproducible packaging and safe installation"
```

---

### Task 7: Project Documentation, Licensing, and Read-Only CI

**Files:**

- Create: `README.md`
- Create: `LICENSE`
- Create: `NOTICE`
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `CITATION.cff`
- Create: `docs/architecture.md`
- Create: `docs/release.md`
- Create: `.github/pull_request_template.md`
- Create: `.github/workflows/validate.yml`
- Create: `tests/test_project_metadata.py`

**Interfaces:**

- Consumes: Task 1–6 的固定命令、版本、公開邊界與產物名稱。
- Produces: 一個可由新貢獻者依 README 安裝、由 Codex 依 `AGENTS.md` 維護、由
  GitHub Actions 以唯讀權限驗證的 repository。

- [ ] **Step 1: Write failing metadata and CI tests**

```python
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_ci_has_read_only_permissions_and_required_commands():
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    )
    assert workflow["permissions"] == {"contents": "read"}
    rendered = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    for command in (
        "python -m pytest -q",
        "python scripts/validate_skill.py",
        "python scripts/check_public_boundary.py",
        "python scripts/package_skill.py --check-reproducible",
    ):
        assert command in rendered
    assert "secrets." not in rendered


def test_citation_and_license_metadata():
    citation = yaml.safe_load(
        (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    )
    assert citation["title"] == "Clinical Data Research Navigator"
    assert citation["version"] == "0.1.0"
    assert citation["license"] == "Apache-2.0"
    assert "Apache License" in (ROOT / "LICENSE").read_text(encoding="utf-8")
```

- [ ] **Step 2: Run tests and verify RED**

Run:

```bash
python -m pytest tests/test_project_metadata.py -q
```

Expected: FAIL because project metadata and workflow files do not exist.

- [ ] **Step 3: Write user and contributor documentation**

`README.md` must include:

- one-sentence outcome;
- public／private boundary;
- supported question types;
- repository versus installable Skill layout;
- Python 3.11 setup;
- all four validation commands;
- package and user-selected installation commands;
- explicit statement that the repository is not a TMUCRD data dictionary;
- link to architecture、release、security and contribution documents.

`CONTRIBUTING.md` must require:

- synthetic institutional examples only;
- evidence that the contributor can license submitted content;
- failing test before behavior change;
- boundary scan before pull request;
- no private adapter or login-gated document.

`SECURITY.md` must define the response to accidental private-data submission:

1. stop merge and distribution;
2. remove branch or pull request access where possible;
3. notify repository maintainers and the governing data owner;
4. rotate potentially affected credentials;
5. use GitHub's sensitive-data removal procedure;
6. do not rely on a later deletion commit to erase history.

- [ ] **Step 4: Add Apache-2.0 and citation boundaries**

Use the canonical Apache License 2.0 text in `LICENSE`.

`NOTICE` must state:

- repository-authored code、Skill、templates and tests use Apache-2.0;
- CDISC、FDA、PHUSE、Lex Jansen、SAS、OHDSI、OMOP、TMU and BMJ materials
  remain owned and licensed by their respective owners;
- linked or summarized external material is not relicensed by this repository;
- no external PDF or supplementary file is bundled.

`CITATION.cff` must use:

```yaml
cff-version: 1.2.0
message: "If you use this project, cite it using this metadata."
title: "Clinical Data Research Navigator"
version: "0.1.0"
license: Apache-2.0
type: software
```

Do not invent a DOI or repository URL before GitHub publication.

- [ ] **Step 5: Document architecture and release stop**

`docs/architecture.md` must explain:

- source repository versus installed Skill;
- public Core versus externally mounted private Adapter;
- static validator、boundary scanner、evaluator and packager data flow;
- why CI is offline and credential-free.

`docs/release.md` must define:

1. full local verification;
2. clean `git status`;
3. package and manifest generation;
4. manual boundary review;
5. tag `v0.1.0`;
6. attach ZIP、manifest and release notes;
7. stop before steps 5–6 unless the user separately approves GitHub publishing.

- [ ] **Step 6: Add PR template and read-only GitHub Actions**

`.github/workflows/validate.yml` must contain:

```yaml
name: validate

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python -m pip install --upgrade pip
      - run: python -m pip install -e ".[dev]"
      - run: python -m pytest -q
      - run: python scripts/validate_skill.py
      - run: python scripts/check_public_boundary.py
      - run: python scripts/package_skill.py --check-reproducible
```

The pull-request checklist must explicitly ask whether the change:

- contains institutional data or login-gated documents;
- changes `SKILL.md` and therefore also reviewed Evals／UI metadata／references;
- adds only synthetic schemas;
- passed all four validation commands.

- [ ] **Step 7: Run tests and verify GREEN**

Run:

```bash
python -m pytest tests/test_project_metadata.py -q
```

Expected: PASS.

- [ ] **Step 8: Commit documentation and CI**

```bash
git add \
  README.md LICENSE NOTICE CONTRIBUTING.md SECURITY.md CITATION.cff \
  docs .github tests/test_project_metadata.py
git commit -m "docs: add public project governance and CI"
```

---

### Task 8: Acceptance Verification and Reviewable v0.1.0 Candidate

**Files:**

- Modify only when a failing acceptance check identifies a defect.
- Generate locally ignored artifacts:
  `dist/clinical-data-research-navigator-0.1.0.zip`
  and
  `dist/clinical-data-research-navigator-0.1.0.manifest.json`
- Create: `docs/verification/2026-07-27-v0.1.0.md`

**Interfaces:**

- Consumes: all repository tests, validators, Evals and packaging commands.
- Produces: a local, reviewable `v0.1.0` candidate and evidence report; no tag,
  remote, push or GitHub Release.

- [ ] **Step 1: Write an acceptance test that maps every design criterion**

Create `tests/test_acceptance.py` with one assertion group for each:

```python
from pathlib import Path
import subprocess

from scripts.check_public_boundary import scan_repository
from scripts.validate_skill import validate_skill


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/clinical-data-research-navigator"


def default_branch_is_main() -> bool:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() == "main"


def six_eval_cases_exist() -> bool:
    import yaml

    data = yaml.safe_load((ROOT / "evals/cases.yaml").read_text(encoding="utf-8"))
    return len(data["cases"]) == 6


def build_rwe_sap_is_optional() -> bool:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
    return "build-rwe-sap" in text and "optional" in text


def tmucrd_profile_is_public_snapshot() -> bool:
    text = (
        SKILL / "references/tmucrd-public-profile.md"
    ).read_text(encoding="utf-8")
    return (
        "public source snapshot" in text
        and "not a data dictionary" in text
        and "10.1136/bmjhci-2023-100890" in text
    )


def required_repository_policy_exists() -> bool:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    return (
        "Do not read or copy private TMUCRD adapters" in text
        and "Do not create or push a GitHub repository" in text
    )


def test_v010_acceptance_contract():
    assert default_branch_is_main()
    assert validate_skill(SKILL) == []
    assert scan_repository(ROOT) == []
    assert six_eval_cases_exist()
    assert build_rwe_sap_is_optional()
    assert tmucrd_profile_is_public_snapshot()
    assert required_repository_policy_exists()
```

Use small helpers that call the real validators; do not duplicate their logic.
The first run must fail for any remaining unmet criterion.

- [ ] **Step 2: Run the complete suite and verify the acceptance RED or GREEN state**

Run:

```bash
python -m pytest -q
```

Expected:

- If a criterion is incomplete, FAIL for that exact criterion; fix it with a
  focused RED／GREEN cycle.
- If every prior task is complete, PASS without modifying production code.

- [ ] **Step 3: Run all required command-line gates**

```bash
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

Expected: all exit 0 with no warning or finding.

- [ ] **Step 4: Inspect repository history and tracked files**

Run:

```bash
git branch --show-current
git status --short
git log --oneline --decorate
git ls-files
git grep -n -I -E \
  'tmucrd-v2\.16-(dictionary|guide)|codingbook|codebook|dictionary\.txt' \
  -- . ':!docs/superpowers/specs/*' ':!docs/superpowers/plans/*' || true
```

Expected:

- branch is `main`;
- worktree contains only the verification report before its commit;
- no tracked private file;
- blocked filename patterns may appear only in enforcement code、tests、policy、
  design or plan prose, never as a tracked private artifact.

- [ ] **Step 5: Build the reviewable candidate once**

```bash
python scripts/package_skill.py --output-dir dist
sha256sum \
  dist/clinical-data-research-navigator-0.1.0.zip \
  dist/clinical-data-research-navigator-0.1.0.manifest.json
```

Record filenames、byte sizes、SHA-256、test count and command results in
`docs/verification/2026-07-27-v0.1.0.md`. Do not include secret matches,
private patterns beyond the public policy names, hidden reasoning or local
credential paths.

- [ ] **Step 6: Review the final diff**

Run:

```bash
git diff --check
git diff --stat HEAD
git status --short
```

Open and review:

```text
SKILL.md
agents/openai.yaml
tmucrd-public-profile.md
institutional-adapter-contract.md
evals/cases.yaml
AGENTS.md
.github/workflows/validate.yml
```

Confirm the Skill ID remains unchanged and the repository name appears only as
`clin-data-nav`.

- [ ] **Step 7: Commit the verification evidence**

```bash
git add tests/test_acceptance.py docs/verification/2026-07-27-v0.1.0.md
git commit -m "test: verify v0.1.0 public-core candidate"
```

- [ ] **Step 8: Confirm the local stopping point**

Run:

```bash
git status --short --branch
git remote -v
```

Expected:

- clean `main` worktree;
- no Git remote created by this implementation;
- no `v0.1.0` tag;
- no GitHub repository or Release;
- `dist/` remains ignored and available only as a local review artifact.

At this point, return the test evidence、local package links and commit list to
the user. GitHub publication begins only after a new explicit approval.

---

## Self-Review Record

### Spec coverage

- Public／private boundary: Tasks 1、3、4、7、8.
- Installable Skill and UI metadata: Tasks 2、3.
- Optional `build-rwe-sap`: Tasks 3、8.
- Six behavior Evals and no-LLM CI: Tasks 1、3、5、7.
- Deterministic packaging and safe install: Task 6.
- AGENTS、documentation、license、security and CI: Tasks 1、7.
- New clean Git history and no remote publication: Tasks 1、8.
- TMUCRD public profile and snapshot caveat: Tasks 3、4、8.
- Complete acceptance evidence: Task 8.

### Interface consistency

- All repository paths use `clin-data-nav` as the repository name and
  `clinical-data-research-navigator` as the Skill ID.
- `validate_skill(Path) -> list[str]` is reused by packaging and acceptance.
- `scan_repository(Path, int) -> list[Finding]` is reused by CLI and acceptance.
- `evaluate_response(dict, dict, str) -> Evaluation` is shared by unit tests
  and fixture scoring.
- `build_package(Path, Path) -> PackageResult` is shared by tests、CLI and
  installation fixtures.

### Execution boundary

Tasks 1 and 3 include fresh-context subagent behavior tests. They may run only
after the user explicitly selects an execution option that authorizes
subagents. All other tasks can run inline in the current Codex session. No task
authorizes a GitHub write.
