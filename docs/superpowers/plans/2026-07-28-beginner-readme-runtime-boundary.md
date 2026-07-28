# Beginner README and Runtime Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add beginner CDISC, SDTM, and ADaM explanations while documenting
that Python is a contributor tool rather than a Skill runtime dependency.

**Architecture:** Keep all user-facing guidance in the two root READMEs. Use
official CDISC links as the definition sources and one contract test to keep
both language versions structurally aligned.

**Tech Stack:** Markdown, Python 3.11, pytest 8

## Global Constraints

- Do not imply that every clinical or real-world dataset must pass through
  SDTM and ADaM.
- Do not describe Python as required to invoke or use the installed Skill.
- Keep Python 3.11 for repository testing, packaging, and the strict installer.
- Keep English and Traditional Chinese content equivalent.
- Do not change package contents, version, tag, or existing GitHub Release.

---

### Task 1: Define and implement the README contract

**Files:**
- Modify: `tests/test_project_metadata.py`
- Modify: `README.md`
- Modify: `README.zh-TW.md`

**Interfaces:**
- Consumes: the existing bilingual README structure and official CDISC pages.
- Produces: beginner explanations and an explicit runtime boundary.

- [x] **Step 1: Add the failing README contract test**

Require both READMEs to contain CDISC, SDTM, ADaM, the simplified flow,
official CDISC links, and a statement that Skill use does not require Python.
Require contributor-only Python headings and reject `python -c` from the POSIX
Release-install block.

- [x] **Step 2: Verify RED**

```bash
python -m pytest -q tests/test_project_metadata.py
```

Expected: failure because the beginner and runtime-boundary sections do not
exist yet.

- [x] **Step 3: Add the English and Traditional Chinese sections**

Add the approved beginner mental model, applicability caveat, Python boundary,
and native POSIX checksum commands. Preserve all existing installation safety
checks and clinical-data execution gates.

- [x] **Step 4: Verify GREEN**

Run the focused test again and require zero failures.

### Task 2: Verify the repository

**Files:**
- Review: `README.md`
- Review: `README.zh-TW.md`
- Review: all changed files

**Interfaces:**
- Consumes: Task 1.
- Produces: a reviewable, uncommitted documentation change.

- [x] **Step 1: Check bilingual structure and links**

Confirm matching H2 counts, matching code-block counts, valid local links, and
no placeholders.

- [x] **Step 2: Run all four repository gates**

```bash
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

- [x] **Step 3: Review the final diff**

Run `git diff --check`, inspect all changed files, and leave the work
uncommitted until the user requests commit or publication.
