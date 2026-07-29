# npx Quick Start Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `npx skills add mtchuang1981/clin-data-nav` the primary bilingual quick-start path while retaining the checksum-verified GitHub Release installation workflow.

**Architecture:** This is a documentation-only feature guarded by the existing README contract test. The two READMEs remain structurally aligned: each gains an early quick-start section and each relabels the existing Release instructions as the verified manual path.

**Tech Stack:** Markdown, Python 3.11, pytest

## Global Constraints

- The exact quick-start command is `npx skills add mtchuang1981/clin-data-nav`.
- The command must be described as project-local under `.agents/skills`, not global.
- `/skills` verifies discovery and `$clinical-data-research-navigator` explicitly invokes the Skill.
- The GitHub Release instructions remain complete for pinned, manifest-verified, SHA-256-verified, offline, or personal-directory installation.
- Do not change Skill runtime behavior, packaging contents, version numbers, or Release assets.
- Keep English and Traditional Chinese structure and meaning aligned.

---

### Task 1: Add the bilingual npx quick start

**Files:**
- Modify: `tests/test_project_metadata.py:53-65`
- Modify: `README.md:3-8,143`
- Modify: `README.zh-TW.md:3-7,111`

**Interfaces:**
- Consumes: the repository layout with one installable Skill under `skills/clinical-data-research-navigator`
- Produces: a bilingual README contract for the exact npx command, project-local scope, discovery check, explicit invocation, and retained verified manual path

- [ ] **Step 1: Write the failing README contract test**

Replace `test_readmes_document_installation_activation_and_examples` with:

```python
def test_readmes_document_quick_start_verified_installation_and_activation():
    english = (ROOT / "README.md").read_text(encoding="utf-8")
    traditional_chinese = (ROOT / "README.zh-TW.md").read_text(encoding="utf-8")

    for text in (english, traditional_chinese):
        assert "npx skills add mtchuang1981/clin-data-nav" in text
        assert ".agents/skills" in text
        assert "/skills" in text
        assert "$clinical-data-research-navigator" in text
        assert "$HOME/.agents/skills" in text
        assert "v0.2.0" in text
        assert "SHA-256" in text

    assert "## Quick start" in english
    assert "from the root of the project" in english
    assert "## Verified manual installation from GitHub Release" in english
    assert "## Use the Skill" in english

    assert "## 快速開始" in traditional_chinese
    assert "要使用此 Skill 的專案根目錄" in traditional_chinese
    assert "## 經驗證的 GitHub Release 手動安裝" in traditional_chinese
    assert "## 使用 Skill" in traditional_chinese
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```bash
python -m pytest tests/test_project_metadata.py::test_readmes_document_quick_start_verified_installation_and_activation -q
```

Expected: FAIL because neither README contains the new quick-start heading and both still use the old GitHub Release heading.

- [ ] **Step 3: Add the English quick-start section**

Insert this section after the introductory paragraph in `README.md`:

````markdown
## Quick start

Run this command from the root of the project where you want to use the Skill:

```bash
npx skills add mtchuang1981/clin-data-nav
```

By default, `skills` installs it for that project under `.agents/skills`. Run
`/skills` to confirm discovery, then use `$clinical-data-research-navigator` to
invoke it explicitly. Review third-party Skills before use because they run
with your agent's permissions.
````

Rename `## Install from GitHub Release` to:

```markdown
## Verified manual installation from GitHub Release
```

Do not change the existing PowerShell, POSIX, manifest, SHA-256, or destination
instructions beneath that heading.

- [ ] **Step 4: Add the Traditional Chinese quick-start section**

Insert this section after the introductory paragraph in `README.zh-TW.md`:

````markdown
## 快速開始

請在要使用此 Skill 的專案根目錄執行：

```bash
npx skills add mtchuang1981/clin-data-nav
```

`skills` 預設會將它安裝到該專案的 `.agents/skills`。請用 `/skills`
確認系統已偵測到 Skill，再以 `$clinical-data-research-navigator`
明確呼叫。第三方 Skill 會使用代理程式的權限執行，使用前請先審閱內容。
````

Rename `## 從 GitHub Release 安裝` to:

```markdown
## 經驗證的 GitHub Release 手動安裝
```

Do not change the existing PowerShell, POSIX, manifest, SHA-256, or destination
instructions beneath that heading.

- [ ] **Step 5: Run the focused test and verify GREEN**

Run:

```bash
python -m pytest tests/test_project_metadata.py::test_readmes_document_quick_start_verified_installation_and_activation -q
```

Expected: PASS.

- [ ] **Step 6: Run the complete release checks**

Run:

```bash
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

Expected: every command exits `0`; the full pytest count is at least 168.

- [ ] **Step 7: Review the diff and commit**

Run:

```bash
git diff --check
git diff -- README.md README.zh-TW.md tests/test_project_metadata.py
git status --short
git add README.md README.zh-TW.md tests/test_project_metadata.py
git commit -m "docs: add npx quick start"
```

Expected: the commit contains only the two READMEs and the focused contract
test; versioned Release instructions and package contents are unchanged.
