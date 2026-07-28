# RWE Question Routing and Optional build-rwe-sap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add PICO-informed RWD/RWE and TTE routing to the Core while defining a safe, documented, optional handoff to an unbundled `build-rwe-sap` Skill.

**Architecture:** Keep classification, data-fitness review, handoff preparation, and degraded operation in `clinical-data-research-navigator`. Put the complete causal-design method outside this repository, expose it only through a documented compatibility contract, and preserve all existing Adapter and execution-maturity gates.

**Tech Stack:** Markdown, YAML, Python 3.11, pytest 8

## Global Constraints

- Do not create or package a second Skill.
- Do not automatically install or download `build-rwe-sap`.
- Do not call a database, extract, cohort, or OMOP instance RWE.
- Do not imply that PICO establishes causal validity.
- Route TTE only for causal comparative questions.
- Missing or incompatible `build-rwe-sap` must not block Core work.
- Do not promote collaborator output to `executable` or `validated` without the existing Adapter, current metadata, fixture, and result-review gates.
- Keep use of the installed Core independent of Python.
- Do not change version, tag, package name, or existing GitHub Release.

---

### Task 1: Define failing Core and packaging contracts

**Files:**
- Modify: `tests/test_skill_contract.py`
- Modify: `tests/test_skill_structure.py`
- Modify: `tests/test_project_metadata.py`
- Modify: `tests/test_packaging.py`

**Interfaces:**
- Consumes: the approved design in `docs/superpowers/specs/2026-07-28-rwe-question-routing-build-rwe-sap-design.md`.
- Produces: executable contracts for the Core routing reference, bilingual public explanation, and one-Skill packaging boundary.

- [x] **Step 1: Add Core routing assertions**

Extend `tests/test_skill_contract.py` to require:

```python
def test_rwe_question_routing_contract_is_explicit():
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    routing = (
        SKILL / "references/rwe-question-routing.md"
    ).read_text(encoding="utf-8")

    assert "references/rwe-question-routing.md" in skill_text
    assert "RWD is not automatically RWE" in routing
    assert "PICO does not establish causal validity" in routing
    assert "causal-comparative" in routing
    assert "TTE is not the default" in routing
    assert "unavailable" in routing
    assert "incompatible" in routing
```

Add a second contract that requires all handoff fields from the approved design
and requires the evidence template heading `Research question and study-design
routing`.

- [x] **Step 2: Extend reference validation and packaging assertions**

Add `references/rwe-question-routing.md` to the real-reference parameter list
in `tests/test_skill_structure.py`. Add a packaging assertion:

```python
def test_package_contains_rwe_routing_reference_but_no_second_skill(tmp_path):
    result = build_package(
        Path("skills/clinical-data-research-navigator"),
        tmp_path,
    )

    assert "references/rwe-question-routing.md" in result.files
    assert all("build-rwe-sap/" not in name for name in result.files)
```

- [x] **Step 3: Add bilingual README contract**

Extend `tests/test_project_metadata.py` to require both READMEs to state that
`build-rwe-sap` is optional, not bundled, never automatically installed, and
not required for normal Core use. Require both languages to distinguish RWD
from RWE and to limit TTE routing to causal comparative questions.

- [x] **Step 4: Run RED**

Run:

```bash
python -m pytest -q \
  tests/test_skill_contract.py \
  tests/test_skill_structure.py \
  tests/test_project_metadata.py \
  tests/test_packaging.py
```

Expected: failures for the missing routing reference, README section, evidence
template section, and package member.

### Task 2: Implement the minimum Core routing and public documentation

**Files:**
- Create: `skills/clinical-data-research-navigator/references/rwe-question-routing.md`
- Modify: `skills/clinical-data-research-navigator/SKILL.md`
- Modify: `skills/clinical-data-research-navigator/references/evidence-output-template.md`
- Modify: `README.md`
- Modify: `README.zh-TW.md`

**Interfaces:**
- Consumes: Task 1 contracts.
- Produces: the Core classification, RWD/RWE distinction, TTE readiness gate, handoff record, and degraded behaviour.

- [x] **Step 1: Add the focused routing reference**

Create `rwe-question-routing.md` with these sections:

```markdown
# RWE Question Routing

## Classify the intent
## Frame intervention or exposure questions
## Keep RWD and RWE distinct
## Apply the TTE readiness gate
## Hand off to optional build-rwe-sap
## Continue when the optional Skill is unavailable
## Reapply the execution gate
```

Include the five intent labels, PICO-informed fields, seven TTE components,
twelve handoff fields, compatibility rule, degraded operation, and failure
boundaries exactly as approved.

- [x] **Step 2: Route from SKILL.md**

Update the Skill description to include PICO, RWD, RWE, TTE, and causal-study
routing triggers. Add a compact instruction after `Classify the Question` that
loads the focused reference for relevant requests. Expand `Coordinate with
Optional Skills` so the name alone is not compatibility evidence and missing
collaboration does not block Core work.

- [x] **Step 3: Extend the output template**

After `## Decision`, add:

```markdown
## Research question and study-design routing

State the primary intent. For intervention or exposure questions, record the
population, intervention or exposure, comparator, outcomes, time zero,
follow-up, setting, data source, intended use, and target estimand when causal.
Distinguish RWD from RWE, report TTE readiness only for causal comparative
questions, and state optional `build-rwe-sap` status as available, unavailable,
or incompatible.
```

- [x] **Step 4: Add equivalent public README sections**

Add `## Real-world evidence and causal-study routing` and
`## 真實世界證據與因果研究路由` sections. Explain PICO-informed framing,
the RWD/RWE boundary, when TTE applies, what the optional collaborator does,
that it is not bundled or auto-installed, and exactly what the Core still
delivers without it.

- [x] **Step 5: Run GREEN**

Run the Task 1 test command and require zero failures.

### Task 3: Add behavioural eval coverage

**Files:**
- Modify: `evals/cases.yaml`
- Modify: `tests/test_eval_contract.py`
- Modify: `tests/test_acceptance.py`
- Modify: `tests/test_repository_policy.py`

**Interfaces:**
- Consumes: Task 2 routing behaviour.
- Produces: four offline regression cases and an eleven-case acceptance contract.

- [x] **Step 1: Add failing eval-catalog expectations**

Add these IDs to `CASE_IDS`:

```python
"descriptive-rwd-no-tte",
"causal-rwd-tte-handoff",
"causal-rwd-incomplete-readiness",
"build-rwe-sap-unavailable",
```

Change the acceptance helper and repository-policy catalog contract from seven
cases to eleven cases. Add direct tests that descriptive work forbids default
TTE, incomplete causal work requires `conceptual`, and unavailable
collaboration requires continued Core work plus a complete-SAP disclaimer.

- [x] **Step 2: Run eval RED**

Run:

```bash
python -m pytest -q tests/test_eval_contract.py tests/test_acceptance.py
```

Expected: failure because the four case IDs are absent and the catalog still
contains seven cases.

- [x] **Step 3: Add four eval cases**

Each case must use the existing public schema and have at least ten positive
rules. Required content:

- `descriptive-rwd-no-tte`: RWD, descriptive intent, provenance, fitness,
  `not applicable`, and no default TTE or causal-effect claim.
- `causal-rwd-tte-handoff`: causal-comparative intent, PICO-informed fields,
  seven TTE components, data limitations, validation gaps, and optional
  collaborator status.
- `causal-rwd-incomplete-readiness`: missing time zero, comparator, and
  confounding information; `conceptual`; no executable or causal conclusion.
- `build-rwe-sap-unavailable`: optional, not bundled, not automatically
  installed, Core continuation, and no complete SAP claim.

- [x] **Step 4: Run eval GREEN**

Run the Task 3 test command and require zero failures.

### Task 4: Verify, commit, and publish main

**Files:**
- Review: all files changed by Tasks 1–3
- Modify: this plan only to mark completed checkboxes

**Interfaces:**
- Consumes: all implementation tasks.
- Produces: verified commits on GitHub `main`.

- [x] **Step 1: Review structure and whitespace**

Run `git diff --check`, inspect all changed and untracked files, confirm the
English and Traditional Chinese sections remain structurally equivalent, and
confirm no second Skill directory exists.

- [x] **Step 2: Run all repository tests and four gates**

In a clean Python 3.11 Linux environment, run:

```bash
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

All commands must exit zero.

- [x] **Step 3: Commit the implementation**

Stage only the approved implementation and plan files. Commit with:

```bash
git commit -m "feat: add RWE study-design routing"
```

- [x] **Step 4: Push and verify**

Push `main` to `origin`, then verify that `HEAD`, `origin/main`, and
`git ls-remote origin refs/heads/main` resolve to the same commit and that the
working tree is clean.
