# CodeQL Default Setup Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a durable operator guide and dated evidence record for the
approved CodeQL default setup, then verify both CodeQL languages on a real
repository-owned pull request without changing required checks.

**Architecture:** `docs/repository-settings.md` describes the reusable
operator procedure, while a new dated file under `docs/verification/` records
the immutable observation from the first scan. A metadata test protects the
cross-file audit contract; GitHub remains the authority for current state.

**Tech Stack:** Markdown, Python 3.11, pytest, GitHub CodeQL default setup,
GitHub REST API, GitHub Actions.

## Global Constraints

- Work only in the isolated `codex/codeql-verification` worktree and branch.
- Preserve CodeQL configuration as `actions` plus `python`, `default` query
  suite, `remote` threat model, `standard` runner, and `weekly` schedule.
- Do not add an advanced CodeQL workflow or change any external setting.
- Do not add CodeQL to `main` required checks.
- Preserve the annotated `v0.3.0` tag, Release, assets, package version,
  changelogs, and citation metadata unchanged.
- Record only public repository scan metadata; do not include private
  institutional material.
- Follow RED→GREEN TDD for the metadata contract.

---

### Task 1: Add a failing audit-contract test

**Files:**
- Modify: `tests/test_project_metadata.py`
- Test: `tests/test_project_metadata.py`

**Interfaces:**
- Consumes: repository root constant `ROOT` and UTF-8 Markdown files.
- Produces: `test_codeql_default_setup_guidance_and_evidence_are_auditable`,
  which protects the reusable guidance and dated evidence boundary.

- [ ] **Step 1: Add the test after the existing GitHub settings evidence test**

```python
def test_codeql_default_setup_guidance_and_evidence_are_auditable():
    guide = (ROOT / "docs/repository-settings.md").read_text(
        encoding="utf-8"
    )
    evidence = (
        ROOT / "docs/verification/2026-08-09-codeql-default-setup.md"
    ).read_text(encoding="utf-8")
    normalized_guide = " ".join(guide.split())
    normalized_evidence = " ".join(evidence.split())

    for guide_contract in (
        "## CodeQL default setup",
        "`actions`",
        "`python`",
        "`default`",
        "`remote`",
        "`standard`",
        "`weekly`",
        "not currently a required check",
        "zero results do not prove",
    ):
        assert guide_contract.casefold() in normalized_guide.casefold()

    for evidence_contract in (
        "0aff8038bb52457e9868fab9ea9a43dda9b4235c",
        "https://github.com/mtchuang1981/clin-data-nav/actions/runs/31269886134",
        "93133943497",
        "93133943498",
        "1590243272",
        "1590243578",
        "17 rules",
        "43 rules",
        "zero results",
        "zero open code-scanning alerts",
        "zero job annotations, warnings, or failures",
        "test (ubuntu-latest)",
        "test (windows-latest)",
        "compare-packages",
        "No branch-protection setting was changed",
        "No tag or GitHub Release was changed",
        "zero findings do not prove",
    ):
        assert evidence_contract.casefold() in normalized_evidence.casefold()
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```text
python -m pytest -q tests/test_project_metadata.py::test_codeql_default_setup_guidance_and_evidence_are_auditable
```

Expected: FAIL with `FileNotFoundError` for
`docs/verification/2026-08-09-codeql-default-setup.md`. A syntax error or
failure in an unrelated test does not satisfy RED.

### Task 2: Add minimal guidance and dated evidence

**Files:**
- Modify: `docs/repository-settings.md`
- Create: `docs/verification/2026-08-09-codeql-default-setup.md`
- Test: `tests/test_project_metadata.py`

**Interfaces:**
- Consumes: the exact external configuration and first-scan evidence in the
  approved design.
- Produces: reusable operator guidance plus an immutable historical record.

- [ ] **Step 1: Add this CodeQL section before Optional Zenodo evaluation**

```markdown
## CodeQL default setup

GitHub UI path: **Settings → Security → Advanced Security → CodeQL analysis**.
The approved default setup analyzes `actions` and `python` with the `default`
query suite, `remote` threat model, `standard` runner, and `weekly` schedule.
CodeQL is not currently a required check; do not add it to branch protection
until its exact PR check names and availability have been observed and a
separate change is approved.

Read-only post-change re-read:

```bash
gh api --method GET \
  repos/mtchuang1981/clin-data-nav/code-scanning/default-setup
gh api --method GET \
  'repos/mtchuang1981/clin-data-nav/code-scanning/alerts?state=open'
```

Confirm the stored configuration, inspect both language analyses, and review
every alert. A successful scan and zero results do not prove that the
repository is secure. Do not dismiss an alert merely to make a check green.
```

- [ ] **Step 2: Create the dated evidence with the exact initial observation**

Create `docs/verification/2026-08-09-codeql-default-setup.md` with these
sections and facts:

```markdown
# CodeQL Default Setup Evidence

- **Evidence recorded:** 2026-08-09 (`Asia/Taipei`)
- **Repository:** `mtchuang1981/clin-data-nav`
- **Scanned main commit:**
  `0aff8038bb52457e9868fab9ea9a43dda9b4235c`
- **Authorization:** explicit user approval to enable CodeQL default setup

This report records a historical API observation after the approved external
setting change. GitHub remains the authority for current state. Zero findings
do not prove that the repository is secure.

## Configuration

- state: `configured`;
- languages: `actions`, `python`;
- query suite: `default`;
- threat model: `remote`;
- runner type: `standard`; and
- schedule: `weekly`.

## Initial scan

The initial dynamic run was `31269886134`:

`https://github.com/mtchuang1981/clin-data-nav/actions/runs/31269886134`

- `Analyze (actions)` job `93133943497`: success;
- `Analyze (python)` job `93133943498`: success;
- Actions analysis `1590243272`: 17 rules and zero results; and
- Python analysis `1590243578`: 43 rules and zero results.

The final API re-read observed zero open code-scanning alerts and zero job
annotations, warnings, or failures. These observations apply only to the
identified commit, configuration, query versions, and scan time.

## Branch protection

No branch-protection setting was changed. CodeQL is not currently required.
The existing strict required contexts remain:

- `test (ubuntu-latest)`;
- `test (windows-latest)`; and
- `compare-packages`.

## Publication boundary

No tag or GitHub Release was changed. The annotated `v0.3.0` tag, Release,
ZIP, manifest, asset identities, and SHA-256 values remain governed by
`2026-08-09-v0.3.0-publication.md`.
```

- [ ] **Step 3: Run the focused test and verify GREEN**

Run:

```text
python -m pytest -q tests/test_project_metadata.py::test_codeql_default_setup_guidance_and_evidence_are_auditable
```

Expected: `1 passed`.

- [ ] **Step 4: Run the complete metadata test module**

Run:

```text
python -m pytest -q tests/test_project_metadata.py
```

Expected: all metadata tests pass.

### Task 3: Verify and commit the repository-local evidence

**Files:**
- Modify: `docs/repository-settings.md`
- Create: `docs/verification/2026-08-09-codeql-default-setup.md`
- Modify: `tests/test_project_metadata.py`

**Interfaces:**
- Consumes: the complete public repository verification contract.
- Produces: one implementation commit containing no unrelated change.

- [ ] **Step 1: Run the full suite and four required gates**

```text
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

Expected: every command exits `0`; pytest reports no failures.

- [ ] **Step 2: Audit scope and immutable publication identity**

```text
git diff --check
git status --short
git diff -- docs/repository-settings.md \
  docs/verification/2026-08-09-codeql-default-setup.md \
  tests/test_project_metadata.py
git rev-parse v0.3.0^{tag}
git rev-parse v0.3.0^{commit}
```

Expected: only the three implementation files are uncommitted. The tag object
remains `87ca8f379f6751fc465dbcd6ae8f430dabc73523`; the peeled commit remains
`6cf9593dd8a520f56e1e6e5b0bf2cb7d40b97791`.

- [ ] **Step 3: Commit only the intended files**

```text
git add -- docs/repository-settings.md \
  docs/verification/2026-08-09-codeql-default-setup.md \
  tests/test_project_metadata.py
git commit -m "docs: record CodeQL default setup evidence"
```

### Task 4: Push and observe CodeQL on a draft PR

**Files:**
- No additional repository files.

**Interfaces:**
- Consumes: committed `codex/codeql-verification` branch.
- Produces: a draft PR against `main` and hosted validation evidence.

- [ ] **Step 1: Confirm authentication and exact branch scope**

```text
gh auth status
git status --short
git log --oneline main..HEAD
git diff --name-status main...HEAD
```

Expected: clean worktree and exactly the design, plan, guide, dated evidence,
and metadata-test changes.

- [ ] **Step 2: Push the branch and open a draft PR**

```text
git push -u origin codex/codeql-verification
```

The PR body must identify the historical evidence, RED→GREEN result, full
local verification, unchanged required checks, and immutable v0.3.0 boundary.

- [ ] **Step 3: Wait for all hosted checks**

Expected successful checks with no failure annotations:

- `test (ubuntu-latest)`;
- `test (windows-latest)`;
- `compare-packages`;
- `Analyze (actions)`; and
- `Analyze (python)`.

- [ ] **Step 4: Re-read the PR, CodeQL alerts, branch protection, and Release**

Expected: draft PR scope is exact; open code-scanning alerts remain zero;
required contexts remain only the original three; v0.3.0 tag, Release, assets,
and SHA-256 identities remain unchanged.

Do not mark ready, merge, add required checks, delete the branch, or remove the
worktree without a subsequent explicit user decision.
