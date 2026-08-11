# ClinNav Skill Rename Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single public Skill identity with `clin-nav`, preserve its clinical behavior and historical evidence, and prepare reproducible `0.5.0` artifacts without publishing them.

**Architecture:** Perform one atomic identity cutover across the Skill directory, metadata, active documentation, Python tooling, workflows, and tests. Preserve released v0.1.0–v0.4.0 evidence with an explicit historical allowlist, then validate the renamed Skill with deterministic tests, application scenarios, package comparison, and an isolated installer smoke test.

**Tech Stack:** Python 3.11, pytest, PyYAML, PowerShell, Git, GitHub Actions YAML, `npx skills`, ZIP, JSON, SHA-256.

## Global Constraints

- The only installable Skill is `skills/clin-nav/`; do not retain a redirect or alias Skill.
- The Skill ID is `clin-nav`, invocation is `$clin-nav`, and UI display name is `ClinNav`.
- The repository remains `mtchuang1981/clin-data-nav`; the formal title remains Clinical Data Research Navigator.
- Synchronize active package metadata at version `0.5.0` with artifacts `clin-nav-0.5.0.zip` and `clin-nav-0.5.0.manifest.json`.
- Preserve all released v0.1.0–v0.4.0 notes, verification evidence, filenames, hashes, tags, and Release facts verbatim.
- Do not change the clinical routing, authority hierarchy, output-depth contract, or public/private boundary while renaming.
- Use synthetic examples only. Do not read or copy private adapters, human data, task packs, answers, assignments, consent records, condition keys, or institutional metadata.
- Add or update failing tests before production behavior changes.
- Run the full pytest suite and the four required repository gates before completion.
- Do not push, tag, dispatch a workflow, or create a Release in this plan.

## File Map

| Responsibility | Files |
|---|---|
| Canonical Skill | Move `skills/clinical-data-research-navigator/` to `skills/clin-nav/`; modify `SKILL.md` and `agents/openai.yaml` |
| Identity validation | Modify `scripts/validate_skill.py`; create `tests/test_skill_rename.py`; modify `tests/test_skill_structure.py`, `tests/test_skill_contract.py`, `tests/test_acceptance.py` |
| Packaging and install | Modify `pyproject.toml`, `scripts/package_skill.py`, `scripts/install_local.py`, `scripts/verify_release.py`, `tests/test_packaging.py`, `tests/test_install_local.py`, `tests/test_release_verification.py` |
| Public boundary | Modify `AGENTS.md`, `scripts/check_public_boundary.py`, `tests/test_public_boundary.py` |
| Active navigation | Modify `README.md`, `README.zh-TW.md`, `docs/architecture.md`, `docs/glossary.md`, `docs/glossary.zh-TW.md`, `docs/installation.md`, `docs/installation.zh-TW.md`, `docs/learning-paths.md`, `docs/learning-paths.zh-TW.md`, `docs/release.md` |
| Release-candidate metadata | Modify `CITATION.cff`, `CHANGELOG.md`, `CHANGELOG.zh-TW.md`, `.github/workflows/release.yml`, `tests/test_project_metadata.py`; create `docs/releases/0.5.0.md` |
| Historical evidence | Read-only: `docs/releases/0.1.0.md` through `0.4.0.md` where present, `docs/verification/**`, completed historical specs and plans |

---

### Task 1: Establish the Rename Contract and RED Evidence

**Files:**
- Create: `tests/test_skill_rename.py`
- No production changes

**Interfaces:**
- Consumes: repository root and current active/historical path classification.
- Produces: deterministic tests for the single canonical Skill, active identity synchronization, active old-ID rejection, and historical preservation.

- [ ] **Step 1: Record the pre-change application failure**

Use a fresh worker that has not loaded the old Skill. Ask it to resolve
`skills/clin-nav/SKILL.md` and answer this synthetic prompt through `$clin-nav`:

```text
$clin-nav Explain why ADaM does not prove source-data quality.
```

Record in ignored SDD evidence that the worker cannot load `clin-nav` because
the directory and frontmatter do not yet exist. Do not count a generic answer
as a pass; the test is Skill discovery plus application.

- [ ] **Step 2: Write the failing repository identity tests**

Create `tests/test_skill_rename.py` with literal, independent expectations:

```python
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
ACTIVE_SKILL = SKILLS / "clin-nav"
OLD_SKILL = SKILLS / "clinical-data-research-navigator"
HISTORICAL_ROOTS = (
    ROOT / "docs/releases",
    ROOT / "docs/verification",
    ROOT / "docs/superpowers/specs",
    ROOT / "docs/superpowers/plans",
)
ACTIVE_TEXT_FILES = (
    ROOT / "README.md",
    ROOT / "README.zh-TW.md",
    ROOT / "docs/architecture.md",
    ROOT / "docs/glossary.md",
    ROOT / "docs/glossary.zh-TW.md",
    ROOT / "docs/installation.md",
    ROOT / "docs/installation.zh-TW.md",
    ROOT / "docs/learning-paths.md",
    ROOT / "docs/learning-paths.zh-TW.md",
    ROOT / "docs/release.md",
)


def test_repository_has_exactly_one_clin_nav_skill():
    assert sorted(path.name for path in SKILLS.iterdir() if path.is_dir()) == [
        "clin-nav"
    ]
    assert ACTIVE_SKILL.is_dir()
    assert not OLD_SKILL.exists()


def test_clin_nav_metadata_and_invocation_are_synchronized():
    frontmatter = yaml.safe_load(
        (ACTIVE_SKILL / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1]
    )
    metadata = yaml.safe_load(
        (ACTIVE_SKILL / "agents/openai.yaml").read_text(encoding="utf-8")
    )["interface"]
    assert frontmatter["name"] == "clin-nav"
    assert metadata["display_name"] == "ClinNav"
    assert "$clin-nav" in metadata["default_prompt"]
    assert "$clinical-data-research-navigator" not in metadata["default_prompt"]


def test_active_user_documents_use_only_the_new_invocation_and_paths():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in ACTIVE_TEXT_FILES)
    assert "$clin-nav" in combined
    assert "skills/clin-nav/" in combined
    assert "$clinical-data-research-navigator" not in combined
    assert "skills/clinical-data-research-navigator/" not in combined


def test_released_history_still_contains_the_original_skill_identity():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for root in HISTORICAL_ROOTS
        for path in root.rglob("*.md")
    )
    assert "clinical-data-research-navigator" in combined
```

- [ ] **Step 3: Run the exact RED nodes**

Run:

```text
python -m pytest -q tests/test_skill_rename.py
```

Expected: the first three tests fail because `skills/clin-nav/`, `$clin-nav`,
and active `skills/clin-nav/` links do not exist; the historical-preservation
test passes.

- [ ] **Step 4: Confirm no production file changed**

Run `git status --short` and confirm only `tests/test_skill_rename.py` is new.
Do not commit RED alone; Task 2 provides the atomic identity cutover.

---

### Task 2: Perform the Atomic Skill Identity Cutover

**Files:**
- Move: `skills/clinical-data-research-navigator/` → `skills/clin-nav/`
- Modify: `skills/clin-nav/SKILL.md`
- Modify: `skills/clin-nav/agents/openai.yaml`
- Modify: `scripts/validate_skill.py`
- Modify: `scripts/check_public_boundary.py`
- Modify: `AGENTS.md`
- Modify: `tests/test_skill_structure.py`
- Modify: `tests/test_skill_contract.py`
- Modify: `tests/test_acceptance.py`
- Modify: `tests/test_public_boundary.py`
- Modify: active path links in the ten `ACTIVE_TEXT_FILES` from Task 1
- Test: `tests/test_skill_rename.py`

**Interfaces:**
- Consumes: the RED identity tests from Task 1.
- Produces: canonical directory `skills/clin-nav/`, metadata name `clin-nav`, invocation `$clin-nav`, display name `ClinNav`, and a validator that derives the invocation from the directory name.

- [ ] **Step 1: Move the canonical directory without copying it**

Run the exact scoped rename:

```text
git mv skills/clinical-data-research-navigator skills/clin-nav
```

Immediately verify `Get-ChildItem skills -Directory` returns only `clin-nav`.

- [ ] **Step 2: Change only the Skill identity metadata**

Apply these exact replacements:

```yaml
---
name: clin-nav
description: Use when a clinical-data, CDISC, ADaM, SDTM, PICO, RWD, RWE, causal, target-trial, SAS, SQL, R, EHR, claims, registry, OMOP, or TMUCRD question requires source navigation, terminology mapping, evidence ranking, a data contract, study-design routing, or an implementation specification.
---
```

Keep the SKILL body unchanged except its H1 may become `# ClinNav`. Set
`skills/clin-nav/agents/openai.yaml` to:

```yaml
interface:
  display_name: "ClinNav"
  short_description: "Navigate clinical-data standards, evidence, and implementation contracts"
  default_prompt: "Use $clin-nav for a clinical-data question and choose the appropriate output depth."
```

- [ ] **Step 3: Make validation use the supplied directory identity**

In `validate_skill(skill_dir)`, replace the hard-coded display and invocation
checks with:

```python
expected_name = skill_dir.name
expected_display_name = "ClinNav" if expected_name == "clin-nav" else "Clinical Data Research Navigator"
expected_invocation = f"${expected_name}"
```

Require `interface["display_name"] == expected_display_name` and
`expected_invocation in default_prompt`. Retain all YAML, reference, sentence,
length, and `clinical-data` checks. Change the script entry point to:

```python
failures = validate_skill(root / "skills/clin-nav")
```

Update validator tests so temporary `bad-skill` fixtures use display name
`Clinical Data Research Navigator` and invocation `$bad-skill`, while the
public fixture expects `ClinNav` and `$clin-nav`.

- [ ] **Step 4: Update active repository paths**

Replace active `skills/clinical-data-research-navigator/` links with
`skills/clin-nav/` in `AGENTS.md`, `scripts/check_public_boundary.py`, the four
path-based test modules, and all ten active documentation files listed in Task
1. Do not edit `docs/releases/**`, `docs/verification/**`, or completed specs
and plans.

Change these test constants exactly:

```python
SKILL_DIR = ROOT / "skills/clin-nav"
SKILL = ROOT / "skills/clin-nav"
PROFILE = ROOT / "skills/clin-nav/references/tmucrd-public-profile.md"
```

Update the large-text allowlist to
`skills/clin-nav/references/tmucrd-public-profile.md`.

- [ ] **Step 5: Update active invocations**

Replace `$clinical-data-research-navigator` with `$clin-nav` in active README,
installation, metadata, and current tests. Do not change quoted historical
commands in released evidence.

- [ ] **Step 6: Verify the focused identity contract is GREEN**

Run:

```text
python -m pytest -q tests/test_skill_rename.py tests/test_skill_structure.py tests/test_skill_contract.py tests/test_acceptance.py tests/test_public_boundary.py
python scripts/validate_skill.py
python scripts/check_public_boundary.py
git diff --check
```

Expected: every command exits 0.

- [ ] **Step 7: Commit the atomic identity cutover**

Review `git diff --summary` and require one rename, no duplicate Skill, and no
historical evidence edits. Then:

```text
git add -- AGENTS.md README.md README.zh-TW.md docs/architecture.md docs/glossary.md docs/glossary.zh-TW.md docs/installation.md docs/installation.zh-TW.md docs/learning-paths.md docs/learning-paths.zh-TW.md docs/release.md scripts/validate_skill.py scripts/check_public_boundary.py skills/clin-nav tests/test_skill_rename.py tests/test_skill_structure.py tests/test_skill_contract.py tests/test_acceptance.py tests/test_public_boundary.py
git commit -m "refactor: rename public skill to clin-nav"
```

---

### Task 3: Synchronize Versioned Packaging and Local Installation

**Files:**
- Modify: `pyproject.toml`
- Modify: `scripts/package_skill.py`
- Modify: `scripts/install_local.py`
- Modify: `scripts/verify_release.py`
- Modify: `tests/test_packaging.py`
- Modify: `tests/test_install_local.py`
- Modify: `tests/test_release_verification.py`
- Modify: `tests/test_project_metadata.py`

**Interfaces:**
- Consumes: canonical `skills/clin-nav/` from Task 2.
- Produces: `SKILL_NAME = "clin-nav"`, `PACKAGE_VERSION = "0.5.0"`, safe install target `clin-nav`, and deterministic 0.5.0 artifact names.

- [ ] **Step 1: Add failing package synchronization assertions**

Add or update literal assertions:

```python
assert project["project"]["version"] == "0.5.0"
assert PACKAGER_VERSION == "0.5.0"
assert INSTALLER_VERSION == "0.5.0"
assert result.archive.name == "clin-nav-0.5.0.zip"
assert result.manifest.name == "clin-nav-0.5.0.manifest.json"
```

Update installer expectations to `destination / "clin-nav"` and temporary
backup globs to `.clin-nav-*`. Keep generic temporary fixture Skills named
`bad-skill` or `test-skill` generic; change only fixtures intended to model the
public package.

- [ ] **Step 2: Run package tests and verify RED**

Run:

```text
python -m pytest -q tests/test_packaging.py tests/test_install_local.py tests/test_release_verification.py tests/test_project_metadata.py
```

Expected: failures identify old `0.4.0`, old archive names, old install target,
and old canonical Skill constants.

- [ ] **Step 3: Update canonical constants**

Set:

```python
SKILL_NAME = "clin-nav"
PACKAGE_VERSION = "0.5.0"
```

in `scripts/package_skill.py` and `scripts/install_local.py`, set
`SKILL_NAME = "clin-nav"` in `scripts/verify_release.py`, and set
`version = "0.5.0"` in `pyproject.toml`. Change installer temporary prefixes to
`.clin-nav-` and `.clin-nav-backup-`. Do not change size, path, hash, overwrite,
or rollback protections.

- [ ] **Step 4: Point public package tests at the renamed Skill**

Replace every public path `Path("skills/clinical-data-research-navigator")`
with `Path("skills/clin-nav")`. Update public fixture metadata to `name:
clin-nav`, `display_name: ClinNav`, and `$clin-nav`. Preserve generic validator
fixtures that intentionally use other names.

- [ ] **Step 5: Run packaging GREEN checks**

Run:

```text
python -m pytest -q tests/test_packaging.py tests/test_install_local.py tests/test_release_verification.py tests/test_project_metadata.py
python scripts/package_skill.py --check-reproducible
git diff --check
```

Expected: every command exits 0 and the reproducibility command has no error
output.

- [ ] **Step 6: Commit packaging synchronization**

```text
git add -- pyproject.toml scripts/package_skill.py scripts/install_local.py scripts/verify_release.py tests/test_packaging.py tests/test_install_local.py tests/test_release_verification.py tests/test_project_metadata.py
git commit -m "build: package clin-nav 0.5.0"
```

---

### Task 4: Add Migration Guidance and Prepare the 0.5.0 Release Contract

**Files:**
- Modify: `README.md`
- Modify: `README.zh-TW.md`
- Modify: `docs/installation.md`
- Modify: `docs/installation.zh-TW.md`
- Modify: `docs/release.md`
- Modify: `CITATION.cff`
- Modify: `CHANGELOG.md`
- Modify: `CHANGELOG.zh-TW.md`
- Create: `docs/releases/0.5.0.md`
- Modify: `.github/workflows/release.yml`
- Modify: `tests/test_project_metadata.py`
- Test: `tests/test_skill_rename.py`

**Interfaces:**
- Consumes: the 0.5.0 package identity from Task 3.
- Produces: aligned bilingual migration instructions, static 0.5.0 candidate notes, and a release workflow that builds only `clin-nav-0.5.0` when a future annotated v0.5.0 tag is authorized.

- [ ] **Step 1: Add failing migration and workflow contracts**

Require both installation guides to contain, in this order:

```text
clinical-data-research-navigator
clin-nav
npx skills add mtchuang1981/clin-data-nav
$clin-nav
```

Require the migration section to say the old directory is inspected before
removal, the new install is verified with `/skills`, and no broad or unresolved
path is deleted. Permit the old ID only inside that bounded migration section
and current v0.4.0 verified-ZIP instructions.

Require `.github/workflows/release.yml` to contain:

```bash
test "$VERSION" = "0.5.0"
archive="clin-nav-$VERSION.zip"
manifest="clin-nav-$VERSION.manifest.json"
notes="docs/releases/0.5.0.md"
```

Require `CITATION.cff` version `0.5.0` with no `date-released` field before
publication, both changelogs to begin with a 0.5.0 candidate entry, and the
static notes to state that the rename does not establish human effectiveness.

- [ ] **Step 2: Run the focused documentation tests and verify RED**

Run the new node IDs plus:

```text
python -m pytest -q tests/test_skill_rename.py tests/test_project_metadata.py
```

Expected: failures show missing migration semantics, old workflow bundle names,
and unsynchronized 0.5.0 metadata.

- [ ] **Step 3: Write the bilingual migration procedure**

Add a `Migrate from the previous Skill ID` section and aligned Traditional
Chinese section. It must instruct users to:

1. inspect the exact existing `.agents/skills/clinical-data-research-navigator` directory;
2. remove or archive only that verified directory using their platform's safe file operation;
3. rerun `npx skills add mtchuang1981/clin-data-nav`;
4. confirm `.agents/skills/clin-nav/SKILL.md` exists;
5. restart the Skill host if required, inspect `/skills`, and invoke `$clin-nav`.

Do not give a recursive deletion command. Keep v0.4.0 verified-ZIP examples
clearly labeled as historical/current published v0.4.0 evidence until a later
v0.5.0 publication is authorized.

- [ ] **Step 4: Prepare release-candidate metadata without publishing**

Add a 0.5.0 changelog entry covering only the ID migration, packaging change,
and preserved clinical behavior. Its limitation states that the separate
effectiveness-recovery implementation remains pending and no replacement human
pilot has reached green. Update `CITATION.cff` to version `0.5.0` and remove
`date-released`; that field is added only after a real publication. Create
`docs/releases/0.5.0.md` with English and Traditional Chinese install,
migration, limitations, and verification sections; do not claim a tag, Release,
or recovery capability exists.

Update the release workflow's exact version, archive, manifest, and notes
names. Leave permissions, immutable tag checks, checksums, artifact-ID binding,
and Release refusal behavior unchanged.

- [ ] **Step 5: Verify documentation and workflow GREEN**

Run:

```text
python -m pytest -q tests/test_skill_rename.py tests/test_project_metadata.py
python scripts/check_public_boundary.py
git diff --check
```

Inspect `git diff -- docs/verification docs/releases/0.4.0.md` and require no
output.

- [ ] **Step 6: Commit migration and candidate metadata**

```text
git add -- README.md README.zh-TW.md docs/installation.md docs/installation.zh-TW.md docs/release.md CITATION.cff CHANGELOG.md CHANGELOG.zh-TW.md docs/releases/0.5.0.md .github/workflows/release.yml tests/test_project_metadata.py tests/test_skill_rename.py
git commit -m "docs: add clin-nav migration guidance"
```

---

### Task 5: Verify Skill Behavior, Artifacts, and Isolated Installation

**Files:**
- No tracked production changes expected
- Ignored evidence: `.superpowers/sdd/2026-08-11-clin-nav-rename/`
- Generated and untracked: `dist/clin-nav-0.5.0.zip`, `dist/clin-nav-0.5.0.manifest.json`

**Interfaces:**
- Consumes: Tasks 1–4 candidate tree.
- Produces: final behavioral, package, cross-runtime, and isolated-install evidence; no publication.

- [ ] **Step 1: Run the renamed Skill application scenario**

Use a fresh worker, require it to read `skills/clin-nav/SKILL.md`, and give the
same synthetic ADaM prompt from Task 1. Require the output to select
`Output depth: quick explanation`, include the five common-header fields,
distinguish ADaM standardization from source-data quality, and avoid invented
institutional schema. Record the outcome in ignored SDD evidence.

- [ ] **Step 2: Run complete host verification**

```text
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
python scripts/render_eval_summary.py --check
python scripts/render_effectiveness_report.py --summary evals/effectiveness/examples/synthetic-summary.json --english evals/effectiveness/examples/synthetic-report.md --traditional-chinese evals/effectiveness/examples/synthetic-report.zh-TW.md --check
git diff --check HEAD~3 HEAD
```

Every command must exit 0 with no warning treated as success.

- [ ] **Step 3: Run the same verification with official Python 3.11.9**

Confirm the embedded runtime's `_pth` and `sys.path` resolve this checkout, then
run the full pytest suite, four required gates, and two renderer checks with
`C:\tmp\python-3.11.9-embed-amd64\python.exe`. Stop if the runtime resolves a
different checkout.

- [ ] **Step 4: Build and independently verify fresh artifacts**

Use a verified empty output directory, run:

```text
python scripts/package_skill.py --output-dir dist
python scripts/verify_release.py artifacts --archive dist/clin-nav-0.5.0.zip --manifest dist/clin-nav-0.5.0.manifest.json
```

Independently parse the manifest, require sorted unique member paths, compare
every ZIP member's size and SHA-256, require exact member order, and run the
public-boundary scanner against a fresh extraction. Record both artifact
SHA-256 values; do not commit `dist/`.

- [ ] **Step 5: Perform an isolated `npx skills` smoke test**

Create an empty temporary project outside the checkout. Run
`npx skills add mtchuang1981/clin-data-nav` there, require discovery of exactly
one Skill named `clin-nav`, verify its `SKILL.md` frontmatter and
`agents/openai.yaml`, then remove only the temporary project after resolving
and checking its absolute path. The repository checkout must remain clean.

- [ ] **Step 6: Final review and handoff**

Require:

```text
git status --porcelain
git diff --check
git log -4 --oneline
```

The status must be empty except ignored/generated evidence, the three task
commits must be present, and no push, tag, workflow dispatch, or Release may
have occurred. Report the candidate commit, test counts, gates, artifact names
and hashes, and the explicit fact that real human-effectiveness evidence is
still pending the recovery plan.
