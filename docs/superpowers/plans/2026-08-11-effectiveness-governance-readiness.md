# Effectiveness Governance Readiness Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a public, bilingual, machine-checkable governance documentation-readiness pack that fails closed and can never represent institutional approval or recruitment authorization.

**Architecture:** Keep governance documentation readiness inside the independent effectiveness-evaluation surface while forcing every completed study-specific instance outside the repository. A pure validation library enforces a closed JSON schema and builds a sanitized summary; a thin external-input CLI maps valid complete, valid incomplete, and invalid inputs to exit codes 0, 3, and 2. Public templates and synthetic examples exercise the contract without containing real institutional or human-study material.

**Tech Stack:** Python `>=3.11,<3.12` project contract, Python standard library, pytest, JSON, Markdown, existing public-boundary scanner, existing credential-free GitHub Actions gates.

## Global Constraints

- Work only in `E:\6GAI\AGY\clin-data-nav\.worktrees\effectiveness-governance-readiness` on `codex/effectiveness-governance-readiness-design` until the user-authorized merge step.
- The approved design is `docs/superpowers/specs/2026-08-11-effectiveness-governance-readiness-design.md` at commit `eabe27f75d3222660f9171ba06ad2a4173b55ee2`.
- Preserve package version `0.4.0`, annotated tag `v0.4.0`, its Release, workflow permissions, and repository settings.
- Add no runtime or development dependency and make no network or external model call in tests.
- Use only public templates and synthetic examples. Never read or commit a real institution, person, approval, storage reference, consent material, recruitment material, task pack, nonce, assignment, participant row, answer, rating, lock, or condition key.
- The only statuses are `incomplete` and `ready-for-institutional-review`; authorization is always `not-authorized-to-recruit`.
- The schema contains no institutional outcome or approval field. A validator result never substitutes for IRB, REC, legal, privacy, data-owner, or institutional authority.
- Real readiness instances are repository-external. The CLI must call `ensure_external_path` before reading input.
- CLI output and errors never print evidence references, rejected values, input paths, tracebacks, or private payloads.
- Follow RED -> GREEN -> REFACTOR. Every behavior change gets a focused failing test before production code.
- Preserve and run every existing test and the four required gates before completion.
- Commit each task separately after reviewing its complete scoped diff.
- The user has authorized implementation, local fast-forward merge to `main`, and `git push origin main`; tag and Release mutations remain out of scope.

## File Structure

### New production files

- `scripts/governance_readiness.py`: immutable schema constants, deterministic validation, and sanitized readiness summary.
- `scripts/validate_governance_readiness.py`: content-free external-input CLI with exit codes 0, 2, and 3.

### New public content

- `evals/effectiveness/governance/README.md`: English authority boundary, safe workflow, and CLI instructions.
- `evals/effectiveness/governance/checklist.md`: English 12-control checklist.
- `evals/effectiveness/governance/checklist.zh-TW.md`: aligned Taiwan Traditional Chinese checklist.
- `evals/effectiveness/governance/readiness-template.json`: valid incomplete template.
- `evals/effectiveness/governance/examples/synthetic-readiness.json`: valid synthetic review-ready example that remains unauthorized.

### New tests

- `tests/test_governance_readiness.py`: core contract, mutations, fixtures, CLI, and documentation alignment.

### Existing files modified

- `.gitignore`: ignore `study-governance/`.
- `scripts/check_public_boundary.py`: classify `study-governance/` as `private-study-data` without reading it.
- `tests/test_public_boundary.py`: prove the new root is rejected and its payload stays hidden.
- `evals/effectiveness/README.md`: add the governance-readiness stage and command link.
- `tests/test_project_metadata.py`: bind the new navigation and bilingual stage boundary.

---

### Task 1: Protect External Governance Material at the Public Boundary

**Files:**
- Modify: `.gitignore`
- Modify: `scripts/check_public_boundary.py`
- Modify: `tests/test_public_boundary.py`

**Interfaces:**
- Consumes: existing `_is_private_study_path(relative_path: Path) -> bool` and `scan_repository(root: Path, max_text_bytes: int = 200_000) -> list[Finding]`.
- Produces: `study-governance/` as an ignored and payload-safe `private-study-data` root.

- [ ] **Step 1: Extend the existing path test with the new root**

Add `"study-governance/readiness.json"` to the literal `relative_path` parameter list in `test_scanner_rejects_human_study_private_paths`. Add a separate payload test so the new path, rather than the older `study-data/` path, proves non-disclosure:

```python
def test_scanner_does_not_read_or_print_governance_payload(tmp_path):
    marker = "PRIVATE-GOVERNANCE-MARKER-7F31"
    path = tmp_path / "study-governance/readiness.json"
    path.parent.mkdir()
    path.write_text(marker, encoding="utf-8")

    finding = scan_repository(tmp_path)[0]

    assert (finding.path, finding.rule) == (
        "study-governance/readiness.json",
        "private-study-data",
    )
    assert marker not in finding.detail
```

Add a repository policy assertion using the literal line:

```python
def test_gitignore_keeps_study_governance_out_of_the_checkout():
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "study-governance/" in lines
```

- [ ] **Step 2: Run the focused tests and verify RED**

Run:

```text
python -m pytest -q tests/test_public_boundary.py::test_scanner_rejects_human_study_private_paths tests/test_public_boundary.py::test_scanner_does_not_read_or_print_governance_payload tests/test_public_boundary.py::test_gitignore_keeps_study_governance_out_of_the_checkout
```

Expected: the new cases fail because `study-governance/` is neither ignored nor included in `PRIVATE_STUDY_ROOTS`.

- [ ] **Step 3: Implement the exact boundary change**

Append this exact `.gitignore` line:

```text
study-governance/
```

Change the production constant to:

```python
PRIVATE_STUDY_ROOTS = {
    Path("study-data"),
    Path("study-governance"),
}
```

Do not alter finding text or scan order. The existing early `continue` must still prevent reading the rejected payload.

- [ ] **Step 4: Run boundary verification**

Run:

```text
python -m pytest -q tests/test_public_boundary.py
python scripts/check_public_boundary.py
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 5: Review and commit Task 1**

Review only the three Task 1 files, then:

```text
git add .gitignore scripts/check_public_boundary.py tests/test_public_boundary.py
git commit -m "security: protect study governance material"
```

---

### Task 2: Define the Closed Governance Schema and Public Fixtures

**Files:**
- Create: `scripts/governance_readiness.py`
- Create: `evals/effectiveness/governance/readiness-template.json`
- Create: `evals/effectiveness/governance/examples/synthetic-readiness.json`
- Create: `tests/test_governance_readiness.py`

**Interfaces:**
- Produces:
  - `CONTROL_IDS: tuple[str, ...]`
  - `validate_governance_readiness(payload: object) -> list[str]`
  - `summarize_governance_readiness(payload: dict) -> dict`
- Consumed later by: Task 3 CLI and Task 4 documentation contracts.

- [ ] **Step 1: Write failing literal contract and fixture tests**

Create `tests/test_governance_readiness.py` with a hand-written expected tuple, never imported from production:

```python
EXPECTED_CONTROL_IDS = (
    "study-owner-role",
    "institutional-path-request",
    "scope-risk-benefit",
    "external-storage",
    "access-minimization",
    "retention-deletion",
    "consent-material",
    "recruitment-plan",
    "incident-response",
    "environment-freeze",
    "rater-readiness",
    "task-pack-commitment-plan",
)


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_template_is_valid_incomplete_and_never_authorized():
    payload = load_json(TEMPLATE)
    assert validate_governance_readiness(payload) == []
    assert [row["control_id"] for row in payload["controls"]] == list(
        EXPECTED_CONTROL_IDS
    )
    assert summarize_governance_readiness(payload) == {
        "schema_version": "1",
        "status": "incomplete",
        "authorization": "not-authorized-to-recruit",
        "documented_controls": 0,
        "required_controls": 12,
        "missing_control_ids": list(EXPECTED_CONTROL_IDS),
    }


def test_synthetic_example_is_review_ready_but_never_authorized():
    payload = load_json(SYNTHETIC)
    assert payload["synthetic_example"] is True
    assert validate_governance_readiness(payload) == []
    assert summarize_governance_readiness(payload) == {
        "schema_version": "1",
        "status": "ready-for-institutional-review",
        "authorization": "not-authorized-to-recruit",
        "documented_controls": 12,
        "required_controls": 12,
        "missing_control_ids": [],
    }
```

Use repository-root paths for `TEMPLATE` and `SYNTHETIC`.

- [ ] **Step 2: Run the fixture tests and verify RED**

Run:

```text
python -m pytest -q tests/test_governance_readiness.py::test_template_is_valid_incomplete_and_never_authorized tests/test_governance_readiness.py::test_synthetic_example_is_review_ready_but_never_authorized
```

Expected: collection fails because `scripts.governance_readiness` and the fixtures do not exist.

- [ ] **Step 3: Add strict mutation tests before implementation**

Add helpers that deep-copy the synthetic fixture and mutate one behavior at a time. Test these literal failures:

```python
@pytest.mark.parametrize(
    "mutate",
    (
        lambda value: value.update(extra=True),
        lambda value: value.pop("prepared_at"),
        lambda value: value.__setitem__("schema_version", 1),
        lambda value: value.__setitem__("synthetic_example", "true"),
        lambda value: value.__setitem__("pack_id", "Contains Spaces"),
        lambda value: value.__setitem__("protocol_commit", "A" * 40),
        lambda value: value.__setitem__("prepared_at", "2026-08-11T12:00:00"),
    ),
)
def test_top_level_schema_mutations_fail_closed(mutate):
    payload = copy.deepcopy(load_json(SYNTHETIC))
    mutate(payload)
    assert validate_governance_readiness(payload)
```

Add separate mutations for a missing row, duplicate row, swapped rows, unknown ID, row extra key, invalid status, `not-documented` with a reference, `documented` with null, whitespace, `@`, slash, and backslash in reference tokens. Add a parameterized test proving top-level `approved`, `authorized`, `review_not_required`, `ethics_outcome`, and `ready_to_recruit` keys are rejected.

Add this status mutation test:

```python
@pytest.mark.parametrize("index", range(12))
def test_each_missing_documentation_control_makes_summary_incomplete(index):
    payload = copy.deepcopy(load_json(SYNTHETIC))
    payload["controls"][index]["documentation_status"] = "not-documented"
    payload["controls"][index]["evidence_reference"] = None

    summary = summarize_governance_readiness(payload)

    assert summary["status"] == "incomplete"
    assert summary["authorization"] == "not-authorized-to-recruit"
    assert summary["missing_control_ids"] == [EXPECTED_CONTROL_IDS[index]]
```

Run all Task 2 tests. Expected: RED because production behavior is absent.

- [ ] **Step 4: Create exact public fixtures**

Both fixtures use:

```json
{
  "schema_version": "1",
  "synthetic_example": false,
  "pack_id": "pilot-v1-governance-template",
  "protocol_commit": "d1738927305e36605be2833adbd999afb68b33aa",
  "prepared_at": "2026-08-11T13:14:11+08:00",
  "controls": []
}
```

The template has all 12 literal controls in design order with
`"documentation_status": "not-documented"` and `"evidence_reference": null`.

The synthetic example changes `synthetic_example` to true, uses pack ID
`synthetic-pilot-v1-governance`, marks all rows `documented`, and uses exact
tokens formed by uppercasing each literal control ID without changing its
hyphens: `SYNTH.STUDY-OWNER-ROLE.V1` through
`SYNTH.TASK-PACK-COMMITMENT-PLAN.V1`. The tokens contain no slash, backslash,
whitespace, or `@`. Every fixture is UTF-8, sorted-key, two-space JSON with a
final newline.

- [ ] **Step 5: Implement the core validator and summary**

Create `scripts/governance_readiness.py` with these immutable constants:

```python
TOP_LEVEL_KEYS = frozenset(
    {"schema_version", "synthetic_example", "pack_id", "protocol_commit", "prepared_at", "controls"}
)
CONTROL_KEYS = frozenset(
    {"control_id", "documentation_status", "evidence_reference"}
)
CONTROL_IDS = (
    "study-owner-role",
    "institutional-path-request",
    "scope-risk-benefit",
    "external-storage",
    "access-minimization",
    "retention-deletion",
    "consent-material",
    "recruitment-plan",
    "incident-response",
    "environment-freeze",
    "rater-readiness",
    "task-pack-commitment-plan",
)
PACK_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
REFERENCE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
```

Implement an internal `_validate_exact_keys(label, value, expected, errors)`
that appends sorted missing then unexpected-key errors. Validate scalar types
explicitly, parse `prepared_at` with `datetime.fromisoformat`, and require a
non-null `utcoffset()`.

Require `controls` to be a list of exactly 12 mappings. Iterate with
`zip(controls, CONTROL_IDS, strict=True)` only after confirming length 12.
Require each `control_id` to equal the expected literal at that index; this
single invariant rejects missing, duplicate, unknown, and reordered rows.
Require exact row keys, an allowed documentation status, and the null/reference
relationship from the design. Return deterministic errors without embedding a
reference token in any error.

Implement the summary as:

```python
def summarize_governance_readiness(payload: dict) -> dict:
    if validate_governance_readiness(payload):
        raise ValueError("invalid governance readiness input")
    missing = [
        row["control_id"]
        for row in payload["controls"]
        if row["documentation_status"] == "not-documented"
    ]
    return {
        "schema_version": "1",
        "status": "incomplete" if missing else "ready-for-institutional-review",
        "authorization": "not-authorized-to-recruit",
        "documented_controls": 12 - len(missing),
        "required_controls": 12,
        "missing_control_ids": missing,
    }
```

- [ ] **Step 6: Run Task 2 tests and mutation verification**

Run:

```text
python -m pytest -q tests/test_governance_readiness.py
python scripts/check_public_boundary.py
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 7: Review and commit Task 2**

Confirm fixtures contain only synthetic tokens and the module has no file or
network I/O, then:

```text
git add scripts/governance_readiness.py evals/effectiveness/governance/readiness-template.json evals/effectiveness/governance/examples/synthetic-readiness.json tests/test_governance_readiness.py
git commit -m "feat: define governance readiness contract"
```

---

### Task 3: Add the External-Input, Content-Free CLI

**Files:**
- Create: `scripts/validate_governance_readiness.py`
- Modify: `tests/test_governance_readiness.py`

**Interfaces:**
- Consumes: `ensure_external_path`, `validate_governance_readiness`, and `summarize_governance_readiness`.
- Produces: CLI `python scripts/validate_governance_readiness.py --input <external-json>` with canonical JSON stdout and exit codes 0, 2, and 3.

- [ ] **Step 1: Write failing CLI behavior tests**

Add a `run_cli(path)` subprocess helper using `sys.executable` and the absolute
script path. Copy the checked-in fixtures to `tmp_path`, which is outside the
repository checkout.

```python
def test_cli_returns_zero_for_review_ready_external_input(tmp_path):
    path = tmp_path / "governance-readiness.json"
    path.write_bytes(SYNTHETIC.read_bytes())
    result = run_cli(path)
    assert result.returncode == 0
    assert json.loads(result.stdout) == {
        "schema_version": "1",
        "status": "ready-for-institutional-review",
        "authorization": "not-authorized-to-recruit",
        "documented_controls": 12,
        "required_controls": 12,
        "missing_control_ids": [],
    }
    assert result.stderr == ""


def test_cli_returns_three_for_valid_incomplete_external_input(tmp_path):
    path = tmp_path / "governance-readiness.json"
    path.write_bytes(TEMPLATE.read_bytes())
    result = run_cli(path)
    assert result.returncode == 3
    assert json.loads(result.stdout)["status"] == "incomplete"
    assert json.loads(result.stdout)["authorization"] == "not-authorized-to-recruit"
    assert result.stderr == ""
```

Add tests proving:

- a repository-internal input exits 2 with empty stdout and exact stderr
  `governance readiness validation failed\n`;
- malformed JSON and schema-invalid JSON exit 2 with that same stderr;
- an input path, a synthetic sensitive marker in an evidence token, and
  `Traceback` never appear in either stream; and
- abbreviated `--inp` is rejected content-free because `allow_abbrev=False`.

- [ ] **Step 2: Run CLI tests and verify RED**

Run the new CLI node IDs. Expected: FAIL because the CLI script does not exist.

- [ ] **Step 3: Implement the thin CLI**

Create `scripts/validate_governance_readiness.py` with:

```python
CLI_ERROR = "governance readiness validation failed\n"


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.exit(2, CLI_ERROR)
```

The parser has only required `--input`, uses `allow_abbrev=False`, and resolves
the path through `ensure_external_path` before reading. Decode UTF-8 JSON,
require zero validation errors, compute the summary, and write exactly
`json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"`.
Return 3 after writing an incomplete summary, otherwise 0. Catch every parsing,
path, file, and schema exception and call `parser.exit(2, CLI_ERROR)` without a
traceback or dynamic message.

- [ ] **Step 4: Run CLI and complete governance tests**

Run:

```text
python -m pytest -q tests/test_governance_readiness.py
python scripts/check_public_boundary.py
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 5: Review and commit Task 3**

Review stdout/stderr assertions and confirm no CLI path can print source data,
then:

```text
git add scripts/validate_governance_readiness.py tests/test_governance_readiness.py
git commit -m "feat: validate external governance readiness"
```

---

### Task 4: Add Bilingual Governance Guidance and Navigation

**Files:**
- Create: `evals/effectiveness/governance/README.md`
- Create: `evals/effectiveness/governance/checklist.md`
- Create: `evals/effectiveness/governance/checklist.zh-TW.md`
- Modify: `evals/effectiveness/README.md`
- Modify: `tests/test_governance_readiness.py`
- Modify: `tests/test_project_metadata.py`

**Interfaces:**
- Consumes: all Task 1-3 commands, statuses, controls, and public/private boundaries.
- Produces: aligned human guidance that routes completed instances to external institutional review without claiming authorization.

- [ ] **Step 1: Write failing navigation and bilingual contract tests**

In `tests/test_governance_readiness.py`, parse backtick-delimited control IDs
from the two checklist tables and compare each list to the hand-written
`EXPECTED_CONTROL_IDS`. Require both files to contain literal
`ready-for-institutional-review` and `not-authorized-to-recruit`.

In `tests/test_project_metadata.py`, add:

```python
def test_effectiveness_readme_routes_governance_readiness_without_authorizing_people():
    text = (ROOT / "evals/effectiveness/README.md").read_text(encoding="utf-8")
    for marker in (
        "governance/README.md",
        "validate_governance_readiness.py",
        "ready-for-institutional-review",
        "not-authorized-to-recruit",
    ):
        assert marker in text
```

Add a behavioral mutation helper that removes each marker from a copy of the
README text and proves the helper returns a deterministic missing-marker list;
do not assert on incidental prose outside those public interface markers.

- [ ] **Step 2: Run documentation tests and verify RED**

Run the new node IDs. Expected: FAIL because the README and checklists do not
exist and effectiveness navigation lacks the governance command.

- [ ] **Step 3: Write the governance README**

The README must contain these sections in order:

1. `Purpose and authority boundary`;
2. `Public files and external instance`;
3. `Prepare without authorizing`;
4. `Validate an external instance`;
5. `Interpret exit codes`;
6. `Stop rules`;
7. `Next institutional step`.

Show the exact CLI from the design. State that the public template is valid but
incomplete, the synthetic example is not evidence, exit 0 means documentation
readiness only, and no validator result authorizes recruitment. Link the fixed
protocol, input schema, 2026-08-11 offline dry-run evidence, `SECURITY.md`, and
the parent effectiveness README. Do not include consent wording or legal
advice.

- [ ] **Step 4: Write aligned English and Traditional Chinese checklists**

Each checklist has one 12-row table in canonical order with columns:

- control ID;
- external evidence that must exist;
- responsible role;
- prohibited action while undocumented.

Use roles only: study owner, institutional reviewer, data custodian, privacy or
security owner, study coordinator, technical environment owner, rating lead,
and task-pack custodian. Include no person or institution. Both files end with
the same literal status and authorization markers and state that the list does
not determine an ethics pathway.

- [ ] **Step 5: Add minimal parent navigation**

Insert a `Governance readiness before a human pilot` section in
`evals/effectiveness/README.md` immediately after `Stages and authority`. Link
the governance README and show the exact external-input command. State that
`ready-for-institutional-review` remains `not-authorized-to-recruit` and that
actual completed instances never enter Git.

- [ ] **Step 6: Run documentation, contract, and boundary verification**

Run:

```text
python -m pytest -q tests/test_governance_readiness.py tests/test_project_metadata.py tests/test_public_boundary.py
python scripts/check_public_boundary.py
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 7: Review and commit Task 4**

Review English/Traditional Chinese fact alignment and every authority claim,
then:

```text
git add evals/effectiveness/governance/README.md evals/effectiveness/governance/checklist.md evals/effectiveness/governance/checklist.zh-TW.md evals/effectiveness/README.md tests/test_governance_readiness.py tests/test_project_metadata.py
git commit -m "docs: add governance readiness guidance"
```

---

### Task 5: Complete Verification, Merge, Push, and Remote Checks

**Files:**
- No new production file.
- Verify the complete branch and merged main.

**Interfaces:**
- Consumes: Tasks 1-4 and the approved external-action authorization.
- Produces: a clean `main`, an unchanged `v0.4.0` tag/Release, and exact-SHA successful Validation and CodeQL runs.

- [ ] **Step 1: Run complete pre-merge verification**

Run from the isolated worktree:

```text
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
python scripts/render_eval_summary.py --check
python scripts/render_effectiveness_report.py --summary evals/effectiveness/examples/synthetic-summary.json --english evals/effectiveness/examples/synthetic-report.md --traditional-chinese evals/effectiveness/examples/synthetic-report.zh-TW.md --check
git diff --check main...HEAD
git status --short --branch
```

Expected: every command exits 0 and the worktree is clean.

- [ ] **Step 2: Review the complete branch diff**

Run `git diff --stat main...HEAD` and `git diff main...HEAD`. Confirm:

- only the approved spec, plan, public templates, synthetic fixtures,
  validator, CLI, tests, navigation, ignore rule, and scanner changes exist;
- no real institution, person, approval, private reference, consent text,
  recruitment record, task pack, nonce, assignment, participant row, answer,
  score, lock, key, package version, tag, Release, workflow, or settings change
  exists; and
- `v0.4.0^{commit}` still resolves to
  `a5b5ad01e8fe6c72e4ea7f317b0bc5eed8644d52`.

- [ ] **Step 3: Fast-forward merge to local main**

From the main checkout:

```text
git pull --ff-only origin main
git merge --ff-only codex/effectiveness-governance-readiness-design
```

Stop on any remote divergence or non-fast-forward result.

- [ ] **Step 4: Re-run required verification on merged main**

Run the full command set from Step 1 again from `main`. Expected: all commands
exit 0 and `git status --porcelain` is empty.

- [ ] **Step 5: Clean the owned worktree and branch**

Remove only ignored caches from the owned worktree, verify the feature commit
is an ancestor of `main`, then run:

```text
git worktree remove E:\6GAI\AGY\clin-data-nav\.worktrees\effectiveness-governance-readiness
git worktree prune
git branch -d codex/effectiveness-governance-readiness-design
```

- [ ] **Step 6: Push the exact main commit**

Freshly confirm local `main` is clean, not behind `origin/main`, and differs
only by the reviewed task commits. Then run:

```text
git push origin main
```

- [ ] **Step 7: Verify remote terminal state**

Require local `HEAD`, `origin/main`, and `git ls-remote origin refs/heads/main`
to match exactly. Wait for the exact-SHA GitHub Validation workflow jobs
`test (ubuntu-latest)`, `test (windows-latest)`, and `compare-packages`, plus
CodeQL jobs `Analyze (actions)` and `Analyze (python)`, to reach
`completed/success`. Recheck the annotated `v0.4.0` tag object, peeled commit,
Release draft/prerelease state, and two asset names/sizes/digests without
modifying them.

---

## Requirements Traceability

| Approved design requirement | Implemented by |
|---|---|
| Fixed 12-control closed schema | Task 2 |
| Public incomplete template | Task 2 |
| Synthetic review-ready but unauthorized example | Task 2 |
| Statuses only incomplete/review-ready | Tasks 2-3 |
| Constant not-authorized-to-recruit | Tasks 2-4 |
| No institutional outcome field | Task 2 mutations |
| External real instances | Tasks 3-4 |
| Content-free output/errors | Task 3 |
| Exit codes 0/2/3 | Task 3 |
| study-governance path blocked without reading | Task 1 |
| Bilingual aligned checklist | Task 4 |
| No legal advice or human-study action | Tasks 2-4 |
| No dependency, network, model, or private input | Global constraints and Task 5 |
| Existing tests/four gates preserved | Every task; final proof in Task 5 |
| Merge/push only after full verification | Task 5 |

## Explicitly Deferred

This plan does not assign a study owner, create a real readiness instance,
choose an institutional pathway, submit for review, record an institutional
decision, approve storage or consent, prepare a confidential task pack, create
a nonce or commitment, recruit, orient, compensate, collect, rate, unlock,
analyze, publish pilot results, calculate power, move a tag, or edit a Release.
Every deferred action requires the separate authority and evidence appropriate
to that later stage.
