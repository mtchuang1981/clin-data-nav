# Lex Jansen SAS Retrieval Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make SAS optimization requests use a traceable `lexjansen.com`
paper-search workflow while preserving authority, licensing, execution, and
validation boundaries.

**Architecture:** Keep the feature declarative: the eval catalog defines the
observable response contract, while `SKILL.md` and `retrieval-playbook.md`
teach the agent how to satisfy it. Do not add a crawler or network dependency;
the host agent uses available search tools and reports a validation gap when
they are unavailable.

**Tech Stack:** Markdown Skill, YAML eval catalog, Python 3.11, pytest 8,
PyYAML 6

## Global Constraints

- Official standards, protocol, and SAP govern definitions and study rules.
- Lex Jansen is secondary implementation evidence only.
- Review the specific paper; an index entry or snippet is insufficient.
- Do not copy code when provenance or reuse terms are absent or unclear.
- Do not claim an optimization without target-specific validation evidence.
- Do not add HTTP, crawler, or browser dependencies to the package.
- Commit only after the full suite and all four repository gates pass.

---

### Task 1: Add the SAS Optimization Eval Contract

**Files:**
- Modify: `evals/cases.yaml`
- Modify: `tests/test_repository_policy.py`
- Modify: `tests/test_eval_contract.py`
- Modify: `tests/test_acceptance.py`

**Interfaces:**
- Consumes: the existing eval schema and fixed scoring rubric.
- Produces: case ID `sas-optimization-lexjansen` with at least ten positive
  rules and high-signal forbidden patterns.

- [ ] **Step 1: Write the failing catalog tests**

Add `sas-optimization-lexjansen` to `CASE_IDS`, change catalog cardinality
assertions from six to seven, and add evaluator fixtures proving that an
incomplete generic Lex Jansen answer fails while a response containing the
domain query, paper review, metadata, provenance, reuse terms, validation, and
limitations passes.

- [ ] **Step 2: Run the focused tests to verify RED**

Run:

```bash
python -m pytest -q tests/test_repository_policy.py tests/test_eval_contract.py tests/test_acceptance.py
```

Expected: failures because the seventh catalog case does not yet exist.

- [ ] **Step 3: Add the minimal catalog case**

The prompt asks for evidence-backed optimization of synthetic SAS TEAE logic.
Required patterns cover `site:lexjansen.com`, the specific paper, title,
authors, conference, publication year, stable URL, access date, provenance,
reuse terms, performance validation, secondary implementation evidence, and a
network-access validation gap. Forbidden patterns reject official-authority
claims and unattributed copying.

- [ ] **Step 4: Run the focused tests to verify GREEN**

Run the same focused pytest command and require zero failures.

### Task 2: Teach the Retrieval Workflow

**Files:**
- Modify: `skills/clinical-data-research-navigator/SKILL.md`
- Modify: `skills/clinical-data-research-navigator/references/retrieval-playbook.md`
- Review: `skills/clinical-data-research-navigator/agents/openai.yaml`

**Interfaces:**
- Consumes: the new eval case.
- Produces: an explicit trigger, domain-restricted query shape, paper-level
  evidence fields, reuse boundary, and no-network behavior.

- [ ] **Step 1: Confirm the eval case remains RED against an incomplete response**

Run the focused evaluator test for the incomplete response and confirm it does
not meet the fixed threshold.

- [ ] **Step 2: Add the minimal Skill guidance**

Add a concise SAS optimization paragraph to `SKILL.md`. Expand the Lex Jansen
step in `retrieval-playbook.md` with the exact search query shape and evidence
handling requirements from the design.

- [ ] **Step 3: Review adjacent Skill surfaces**

Confirm `agents/openai.yaml` still accurately describes the Skill and requires
no change. Confirm the new guidance does not weaken the execution gate or
institutional Adapter boundary.

- [ ] **Step 4: Run Skill and eval validation**

```bash
python scripts/validate_skill.py
python -m pytest -q tests/test_skill_contract.py tests/test_eval_contract.py
```

Require both commands to exit zero.

### Task 3: Document the Public Behavior

**Files:**
- Modify: `README.md`
- Modify: `README.zh-TW.md`

**Interfaces:**
- Consumes: the retrieval and safety contract.
- Produces: matching English and Traditional Chinese descriptions.

- [ ] **Step 1: Add matching behavior notes**

State that SAS optimization requests use targeted Lex Jansen paper searches
when tools are available, that the reviewed paper must be cited, and that code
reuse and performance claims require provenance, permission, and validation.

- [ ] **Step 2: Verify bilingual structure and links**

Compare section counts and executable code blocks, check every local link, and
scan for placeholders.

### Task 4: Verify and Commit

**Files:**
- Review: all changed files

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: one intentional Git commit.

- [ ] **Step 1: Run the complete Python 3.11 verification**

```bash
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

Run in the project's supported Python 3.11 environment and require every
command to exit zero.

- [ ] **Step 2: Review the final diff**

Run `git diff --check`, inspect all tracked and untracked files, and confirm
there are no unrelated or private artifacts.

- [ ] **Step 3: Commit once**

Stage only the intended README, Skill, reference, eval, test, translation
preference, design, and plan files. Commit with:

```bash
git commit -m "feat: add Lex Jansen SAS retrieval contract"
```
