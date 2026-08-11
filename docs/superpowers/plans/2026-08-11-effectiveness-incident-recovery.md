# Effectiveness Incident Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a fail-closed, external-input recovery workflow that permanently excludes the affected batch and computes `evaluation-green` only for a new clean, locked, agreement-eligible, reproducible replacement pilot.

**Architecture:** Add a closed recovery-record schema and stage calculator, then orchestrate the repository's existing study-manifest, environment, agreement, lock, unlock, aggregation, and report validators. Expose stage-specific, content-free CLI commands and bilingual guidance; keep every real record and human-study input outside Git.

**Tech Stack:** Python 3.11, pytest, JSON, SHA-256, existing effectiveness-analysis modules, Markdown, PowerShell.

## Global Constraints

- Complete the `clin-nav` rename and version `0.5.0` before freezing a replacement pilot environment.
- The affected batch disposition is always `excluded-from-effectiveness-analysis`; no override exists.
- No real incident record, governance decision, participant row, answer, score, condition key, task pack, nonce, assignment, consent record, or private path may enter Git.
- All real inputs resolve outside the repository checkout; errors and summaries never echo paths, identifiers, hashes, input values, or exception text.
- The recovery input contains no computed status, green flag, approval shortcut, or free text.
- Reuse existing effectiveness validators and calculations; do not copy agreement, unlock, success, bootstrap, or report logic.
- `evaluation-green` requires a replacement study, a new task commitment, no replacement integrity event, valid lock, agreement thresholds, explicit unlock, at least 14/16 complete participants, and exact aggregate recomputation.
- The affected batch contributes nothing to power analysis. Power scenarios remain deferred until the first valid replacement batch is green.
- Use only synthetic fixtures and temporary external paths in tests and CI.
- Add failing tests before production behavior changes and run the four repository gates before completion.
- Do not recruit, collect, rate, unlock, analyze real human data, push, tag, or publish a Release in this plan.

## File Map

| Responsibility | Files |
|---|---|
| Shared synthetic test builders | Create `tests/effectiveness_fixtures.py`; modify `tests/test_effectiveness_analysis.py` |
| Recovery schema and states | Create `scripts/effectiveness_recovery.py`; create `tests/test_effectiveness_recovery.py` |
| Public fixtures | Create `evals/effectiveness/recovery/recovery-template.json`; create `evals/effectiveness/recovery/examples/synthetic-recovery.json` |
| CLI | Create `scripts/validate_effectiveness_recovery.py`; test in `tests/test_effectiveness_recovery.py` |
| Guidance | Create `evals/effectiveness/recovery/README.md`, `checklist.md`, `checklist.zh-TW.md`; modify `evals/effectiveness/README.md`, `evals/effectiveness/protocol.md`, `evals/effectiveness/protocol.zh-TW.md` |
| Public boundary and navigation | Modify `scripts/check_public_boundary.py`, `tests/test_public_boundary.py`, `tests/test_project_metadata.py` |
| 0.5.0 candidate documentation | Modify `CHANGELOG.md`, `CHANGELOG.zh-TW.md`, `docs/releases/0.5.0.md` after the capability exists |

---

### Task 1: Extract Reusable Synthetic Effectiveness Fixtures

**Files:**
- Create: `tests/effectiveness_fixtures.py`
- Modify: `tests/test_effectiveness_analysis.py`

**Interfaces:**
- Consumes: existing synthetic helper functions in `tests/test_effectiveness_analysis.py`.
- Produces: `criterion_scores_for_pair`, `valid_manifest`, `valid_scores`, `score_bytes`, `valid_lock`, `valid_key`, and `full_pilot_payloads` imports for both analysis and recovery tests.

- [ ] **Step 1: Prove the existing analysis suite is green before refactoring**

Run:

```text
python -m pytest -q tests/test_effectiveness_analysis.py
```

Record the passing count. Any existing failure stops the extraction.

- [ ] **Step 2: Move shared builders without changing their returned values**

Create `tests/effectiveness_fixtures.py` with the exact imports currently used
by the seven named builders:

```python
from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

from scripts.effectiveness_analysis import compute_environment_fingerprint
from scripts.effectiveness_contract import load_effectiveness_contract
from scripts.generate_study_assignments import generate_assignments


ROOT = Path(__file__).resolve().parents[1]
```

Move the seven builders byte-for-byte apart from imports. Keep all literal
synthetic IDs, dates, model names, scores, and conditions unchanged. Import them
back into `tests/test_effectiveness_analysis.py`:

```python
from tests.effectiveness_fixtures import (
    criterion_scores_for_pair,
    full_pilot_payloads,
    score_bytes,
    valid_key,
    valid_lock,
    valid_manifest,
    valid_scores,
)
```

Remove only now-unused imports from the original test module.

- [ ] **Step 3: Verify behavior is unchanged**

Run the same test command from Step 1 and require the identical pass count.
Run `git diff --check`.

- [ ] **Step 4: Commit the fixture extraction**

```text
git add -- tests/effectiveness_fixtures.py tests/test_effectiveness_analysis.py
git commit -m "test: share synthetic effectiveness fixtures"
```

---

### Task 2: Define the Closed Recovery Record and Public Fixtures

**Files:**
- Create: `scripts/effectiveness_recovery.py`
- Create: `tests/test_effectiveness_recovery.py`
- Create: `evals/effectiveness/recovery/recovery-template.json`
- Create: `evals/effectiveness/recovery/examples/synthetic-recovery.json`

**Interfaces:**
- Consumes: no prior production API.
- Produces: `validate_recovery_record(payload: object) -> list[str]`, `compute_record_state(record: dict) -> dict`, `RECOVERY_KEYS`, and the two public fixtures.

- [ ] **Step 1: Write failing fixture and schema tests**

Create `tests/test_effectiveness_recovery.py` with:

```python
import copy
import json
from pathlib import Path

import pytest

from scripts.effectiveness_recovery import (
    compute_record_state,
    validate_recovery_record,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "evals/effectiveness/recovery/recovery-template.json"
SYNTHETIC = ROOT / "evals/effectiveness/recovery/examples/synthetic-recovery.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_template_is_valid_and_blocked_without_external_closure():
    payload = load_json(TEMPLATE)
    assert validate_recovery_record(payload) == []
    assert compute_record_state(payload)["status"] == "blocked-incident-open"


def test_synthetic_record_never_claims_terminal_human_evidence():
    payload = load_json(SYNTHETIC)
    assert payload["synthetic_example"] is True
    assert validate_recovery_record(payload) == []
    assert compute_record_state(payload)["status"] == "authorized-for-fresh-batch"
```

Add parameterized mutations for every top-level key, extra keys named
`status`, `green`, `approved`, and `authorization`, uppercase or short hashes,
unsafe identifiers, naive timestamps, inconsistent null groups, equal affected
and replacement study IDs, equal task commitments, wrong Skill name/version,
and non-boolean integrity flags.

- [ ] **Step 2: Run the schema tests and verify RED**

Run the two exact nodes. Expected: collection error because the module and
fixtures do not exist.

- [ ] **Step 3: Implement immutable schema constants**

Create `scripts/effectiveness_recovery.py` with:

```python
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
import re


RECOVERY_KEYS = frozenset({
    "schema_version", "synthetic_example",
    "affected_study_id", "affected_task_commitment_sha256",
    "affected_batch_disposition",
    "incident_status", "incident_closed_at", "incident_record_sha256",
    "restart_decision", "restart_decided_at", "restart_record_sha256",
    "replacement_study_id", "replacement_protocol_commit",
    "replacement_skill_name", "replacement_skill_version",
    "replacement_skill_commit", "replacement_task_commitment_sha256",
    "replacement_assignment_version", "replacement_environment_fingerprint",
    "collection_status", "collection_closed_at", "collection_record_sha256",
    "integrity_attested_at", "integrity_record_sha256",
    "environment_change_detected", "task_pack_leakage_detected",
    "reportable_incident_detected",
})
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
LOWER_HEX_40 = re.compile(r"^[0-9a-f]{40}$")
LOWER_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
AFFECTED_DISPOSITION = "excluded-from-effectiveness-analysis"
RESTART_DECISIONS = {None, "not-authorized", "authorized-for-replacement-batch"}
```

Implement exact-key validation with deterministic missing then unexpected
errors. Require all lifecycle groups to be either fully null or fully populated.
Require aware, chronological timestamps; when collection is closed, require its
timestamp after restart decision and before integrity attestation. Require
`replacement_skill_name == "clin-nav"` and
`replacement_skill_version == "0.5.0"` whenever replacement bindings exist.
Reject equal affected/replacement IDs and commitments.

- [ ] **Step 4: Create canonical public fixtures**

The template sets `synthetic_example: false`, the fixed affected disposition,
`incident_status: "open"`, and all record-specific identities, hashes,
timestamps, decisions, bindings, closure, and integrity fields to null.

The synthetic example uses only `synthetic-*` safe IDs and repeated lowercase
hexadecimal characters. It sets the affected disposition, closes the synthetic
incident, authorizes a replacement, binds `clin-nav` `0.5.0`, closes synthetic
collection, and attests all three adverse flags false. It remains
`synthetic_example: true`, so its computed state stops at
`authorized-for-fresh-batch` without external study inputs.

Serialize both files as UTF-8, sorted-key, two-space JSON with one final newline.

- [ ] **Step 5: Implement record-only state calculation**

Return only sanitized fields:

```python
{
    "schema_version": "1",
    "status": status,
    "passed_gate_ids": passed,
    "blocked_gate_ids": blocked,
    "synthetic_example": record["synthetic_example"],
}
```

Record-only states stop at `authorized-for-fresh-batch`. Later stage functions
in Tasks 3 and 4 require their corresponding external inputs before calculating
collection, rating, or terminal evidence states.

- [ ] **Step 6: Run mutation tests and verify GREEN**

Run:

```text
python -m pytest -q tests/test_effectiveness_recovery.py
python scripts/check_public_boundary.py
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 7: Commit the recovery schema**

```text
git add -- scripts/effectiveness_recovery.py tests/test_effectiveness_recovery.py evals/effectiveness/recovery/recovery-template.json evals/effectiveness/recovery/examples/synthetic-recovery.json
git commit -m "feat: define effectiveness recovery contract"
```

---

### Task 3: Compute Restart and Collection States from Existing Contracts

**Files:**
- Modify: `scripts/effectiveness_recovery.py`
- Modify: `tests/test_effectiveness_recovery.py`

**Interfaces:**
- Consumes: `validate_study_manifest`, `compute_environment_fingerprint`, and the Task 2 recovery record.
- Produces: `restart_status(record: dict) -> dict` and `collection_status(record: dict, manifest: dict) -> dict`.

- [ ] **Step 1: Write failing state-transition tests**

Use deep copies of the public fixtures and `valid_manifest()` from
`tests.effectiveness_fixtures`. Add exact tests for:

```python
assert restart_status(open_record)["status"] == "blocked-incident-open"
assert restart_status(closed_without_decision)["status"] == "ready-for-restart-review"
assert restart_status(authorized_record)["status"] == "authorized-for-fresh-batch"
assert collection_status(authorized_record, bound_manifest)["status"] == "ready-for-blinded-rating"
```

Add mutations proving collection fails closed for a study-ID mismatch,
protocol commit mismatch, Skill version/commit mismatch, task-commitment
mismatch, assignment-version mismatch, environment-fingerprint mismatch,
non-closed collection, integrity attestation before closure, and any true
adverse flag.

- [ ] **Step 2: Run exact nodes and verify RED**

Expected: import errors for the two missing functions.

- [ ] **Step 3: Implement restart and manifest binding**

Import existing functions:

```python
from scripts.effectiveness_analysis import (
    compute_environment_fingerprint,
    validate_study_manifest,
)
```

`restart_status` validates the record and calculates the highest permitted
pre-collection state. `collection_status` first requires
`authorized-for-fresh-batch`, validates the manifest, and compares:

```python
record["replacement_study_id"] == manifest["study_id"]
record["replacement_protocol_commit"] == manifest["protocol_commit"]
record["replacement_skill_version"] == manifest["skill_version"]
record["replacement_skill_commit"] == manifest["skill_commit"]
record["replacement_task_commitment_sha256"] == manifest["task_commitment_sha256"]
record["replacement_environment_fingerprint"] == compute_environment_fingerprint(manifest)
record["replacement_assignment_version"] == unique_session_assignment_version
```

Require collection closed and all integrity flags exactly false. Return
content-free gate IDs, never mismatched values.

- [ ] **Step 4: Verify GREEN and commit**

```text
python -m pytest -q tests/test_effectiveness_recovery.py tests/test_effectiveness_analysis.py
git diff --check
git add -- scripts/effectiveness_recovery.py tests/test_effectiveness_recovery.py
git commit -m "feat: gate replacement pilot collection"
```

---

### Task 4: Bind Rating, Unlock, and Aggregate Recalculation

**Files:**
- Modify: `scripts/effectiveness_recovery.py`
- Modify: `tests/test_effectiveness_recovery.py`

**Interfaces:**
- Consumes: `validate_blinded_agreement_inputs`, `blinded_agreement_status`, `unlock_observations`, `summarize_effectiveness`, `render_effectiveness_report.render_report`, and Task 3 collection state.
- Produces: `rating_status(record: dict, manifest: dict, scores: dict, lock: dict, scores_bytes: bytes) -> dict` and `green_status(record: dict, manifest: dict, scores: dict, lock: dict, key: dict, scores_bytes: bytes, aggregate_summary: dict, *, unlock_after_ratings_lock: bool) -> dict`.

- [ ] **Step 1: Write failing rating and terminal-green tests**

Use `full_pilot_payloads()` and bind its manifest values into a recovery record.
Add tests proving:

```python
assert rating_status(record, manifest, scores, lock, raw_scores)["status"] == "eligible-for-locked-unlock"
assert green_status(
    record, manifest, scores, lock, key, raw_scores, expected_summary,
    unlock_after_ratings_lock=True,
)["status"] == "evaluation-green"
```

Build `expected_summary` only by calling `unlock_observations` followed by
`summarize_effectiveness`; do not hand-author it.

Add mutation tests for changed score bytes, incomplete ratings, raw agreement
below 0.80, any estimable kappa below 0.60, missing explicit unlock, condition
key mismatch, stale aggregate summary, `synthetic_example: true`, fewer than 14
complete participants, affected study ID reuse, and affected task commitment
reuse.

Add controlled-review mutations for protocol deviations
`environment-consistency` and `task-pack-integrity`, and limitations
`environment-batch-change` and `task-pack-leakage`; each must block green even
when the effect estimate is favorable.

- [ ] **Step 2: Run focused tests and verify RED**

Expected: missing `rating_status` and `green_status` imports.

- [ ] **Step 3: Implement rating orchestration without copying formulas**

Use:

```python
errors = validate_blinded_agreement_inputs(manifest, scores, lock, scores_bytes)
agreement = blinded_agreement_status(scores)
```

Require Task 3 `ready-for-blinded-rating`, no validation errors, and agreement
status `eligible-for-locked-unlock`. Do not inspect a condition key in
`rating_status`.

- [ ] **Step 4: Implement terminal green recomputation**

Require `unlock_after_ratings_lock is True`, then call:

```python
observations = unlock_observations(manifest, scores, lock, key, scores_bytes)
recomputed = summarize_effectiveness(manifest, scores, observations)
```

Require the supplied aggregate summary to equal `recomputed` as a Python data
structure. Call `render_report(recomputed, "en")` and
`render_report(recomputed, "zh-TW")` to exercise the existing public report
schema validation without writing files. Require both the recovery record and
`recomputed` to have `synthetic_example is False`, participant interpretation
status `eligible-for-exploratory-interpretation`, and completed count at least
14.
Inspect only controlled category IDs and counts for the four prohibited
replacement integrity findings. Return `evaluation-green` only after all checks.

- [ ] **Step 5: Verify GREEN and commit**

```text
python -m pytest -q tests/test_effectiveness_recovery.py tests/test_effectiveness_analysis.py
python scripts/check_public_boundary.py
git diff --check
git add -- scripts/effectiveness_recovery.py tests/test_effectiveness_recovery.py
git commit -m "feat: compute effectiveness green gate"
```

---

### Task 5: Add the Content-Free Stage CLI

**Files:**
- Create: `scripts/validate_effectiveness_recovery.py`
- Modify: `tests/test_effectiveness_recovery.py`

**Interfaces:**
- Consumes: all four status functions and `ensure_external_path`.
- Produces: `restart-check`, `collection-check`, `rating-check`, and `green-check` commands with exit codes 0, 2, and 3.

- [ ] **Step 1: Write failing subprocess tests**

Define:

```python
CLI_ERROR = "effectiveness recovery validation failed\n"
```

Copy fixtures and generated synthetic inputs to `tmp_path`. Test exact argument
sets for each subcommand, canonical JSON output, exit 0 when the requested stage
passes, exit 3 for a valid incomplete/blocked stage, and exit 2 with empty
stdout and exact `CLI_ERROR` for invalid input.

Require rejection of repository-internal paths, malformed JSON, abbreviated
flags, output paths aliasing inputs, missing explicit unlock, and a marker value
that must not appear in stdout or stderr. Require the green command to leave
all input bytes unchanged.

- [ ] **Step 2: Run CLI tests and verify RED**

Expected: subprocess exit 2 because the script does not exist.

- [ ] **Step 3: Implement the parser and safe dispatcher**

Use a parser subclass identical in behavior to the existing governance and
analysis CLIs:

```python
CLI_ERROR = "effectiveness recovery validation failed\n"


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.exit(2, CLI_ERROR)
```

Set `allow_abbrev=False` on the root and all subparsers. Resolve every input
through `ensure_external_path` before reading. Read score bytes once and pass
the same bytes to lock validation. `green-check` accepts the literal required
`--unlock-after-ratings-lock` flag. Catch all input, parse, schema, path, and
cross-file exceptions and exit 2 without dynamic text.

Write only canonical sanitized JSON to stdout. Exit 3 when the requested stage
is not satisfied; exit 0 otherwise.

- [ ] **Step 4: Verify GREEN and commit**

```text
python -m pytest -q tests/test_effectiveness_recovery.py
python scripts/check_public_boundary.py
git diff --check
git add -- scripts/validate_effectiveness_recovery.py tests/test_effectiveness_recovery.py
git commit -m "feat: validate effectiveness recovery stages"
```

---

### Task 6: Add Bilingual Recovery Guidance and Public-Boundary Enforcement

**Files:**
- Create: `evals/effectiveness/recovery/README.md`
- Create: `evals/effectiveness/recovery/checklist.md`
- Create: `evals/effectiveness/recovery/checklist.zh-TW.md`
- Modify: `evals/effectiveness/README.md`
- Modify: `evals/effectiveness/protocol.md`
- Modify: `evals/effectiveness/protocol.zh-TW.md`
- Modify: `scripts/check_public_boundary.py`
- Modify: `tests/test_public_boundary.py`
- Modify: `tests/test_effectiveness_recovery.py`
- Modify: `tests/test_project_metadata.py`
- Modify: `CHANGELOG.md`
- Modify: `CHANGELOG.zh-TW.md`
- Modify: `docs/releases/0.5.0.md`

**Interfaces:**
- Consumes: Task 5 commands, state names, exit codes, and public/private boundaries.
- Produces: aligned human guidance and scanner rules that prevent real recovery artifacts from entering Git.

- [ ] **Step 1: Write failing documentation and boundary contracts**

Require both checklists to contain all six states in canonical order and the
literal statements:

```text
excluded-from-effectiveness-analysis
evaluation-green
not an ethics determination
not recruitment authorization
```

Use an aligned Traditional Chinese assertion for the two authority limitations
and parse the state IDs independently from both files. Require the parent README
to link `recovery/README.md` and show all four CLI commands.

Add public-boundary mutations for tracked paths under:

```text
evals/effectiveness/recovery/real/
evals/effectiveness/recovery/incident-record.json
evals/effectiveness/recovery/condition-key.json
evals/effectiveness/recovery/human-task-pack.yaml
```

Require findings to report only the safe path and rule name, never file content.
Require the 0.5.0 changelogs and static notes to describe the recovery CLI as
green-capable, state that no real replacement pilot was performed, and preserve
the affected batch exclusion and power-analysis deferral.

- [ ] **Step 2: Run focused tests and verify RED**

Run the new documentation and boundary node IDs. Expected: missing files,
missing navigation, and unrecognized prohibited paths.

- [ ] **Step 3: Write the recovery README and aligned checklists**

The README sections appear in this order:

1. purpose and authority boundary;
2. why the affected batch remains excluded;
3. external recovery record;
4. restart check;
5. collection check;
6. rating check;
7. terminal green check;
8. interpret states and exit codes;
9. replacement incident recursion;
10. reporting and power-analysis boundary.

Both checklists map each state to required external evidence, responsible role,
permitted next action, and prohibited action. They must state that the first
power analysis uses only the first valid replacement batch and the predeclared
20-point practical difference.

- [ ] **Step 4: Update the protocol and parent navigation**

Add a bounded incident-recovery section to both protocols. Preserve all
canonical existing facts and add a new aligned fact stating that an affected
batch is excluded, a replacement incident recursively stops the replacement,
and green requires a new clean batch. Add the four commands to the parent README.

Update the existing 0.5.0 changelog entries and static candidate notes only
after the recovery tests pass. Describe the implemented contract, states, and
CLI without claiming observed human evidence, an existing tag, or a published
Release.

- [ ] **Step 5: Harden the scanner**

Add recovery-specific private path parts and filenames to the scanner without
reading or printing file content. Permit only the template, synthetic example,
README, and two checklists under the public recovery directory.

- [ ] **Step 6: Verify GREEN and commit**

```text
python -m pytest -q tests/test_effectiveness_recovery.py tests/test_public_boundary.py tests/test_project_metadata.py
python scripts/check_public_boundary.py
git diff --check
git add -- evals/effectiveness/recovery/README.md evals/effectiveness/recovery/checklist.md evals/effectiveness/recovery/checklist.zh-TW.md evals/effectiveness/README.md evals/effectiveness/protocol.md evals/effectiveness/protocol.zh-TW.md scripts/check_public_boundary.py tests/test_public_boundary.py tests/test_effectiveness_recovery.py tests/test_project_metadata.py CHANGELOG.md CHANGELOG.zh-TW.md docs/releases/0.5.0.md
git commit -m "docs: add effectiveness recovery guidance"
```

---

### Task 7: Complete Dual-Runtime Verification and Report the Real Remaining Gate

**Files:**
- No tracked production changes expected
- Ignored evidence: `.superpowers/sdd/2026-08-11-effectiveness-incident-recovery/`

**Interfaces:**
- Consumes: Tasks 1–6 and the completed `clin-nav` plan.
- Produces: verified green-capable software and an explicit status that real `evaluation-green` remains blocked until valid external replacement-pilot evidence exists.

- [ ] **Step 1: Run the synthetic end-to-end recovery path**

Create all files in a fresh external temporary directory. Use the synthetic
fixture builders to exercise restart, collection, rating, and green commands.
The terminal test may deep-copy the recovery record and generated aggregate and
set both `synthetic_example` fields to false only inside the disposable test
scenario required to exercise the code; the checked-in synthetic recovery
record must never claim real evidence.

Verify adverse mutations return exit 3 or 2 as specified and never disclose the
input marker.

- [ ] **Step 2: Run complete host verification**

```text
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
python scripts/render_eval_summary.py --check
python scripts/render_effectiveness_report.py --summary evals/effectiveness/examples/synthetic-summary.json --english evals/effectiveness/examples/synthetic-report.md --traditional-chinese evals/effectiveness/examples/synthetic-report.zh-TW.md --check
git diff --check
```

- [ ] **Step 3: Run the same command set with official Python 3.11.9**

First confirm the embedded runtime resolves the candidate worktree. Require the
same pass count and exit codes as the host run.

- [ ] **Step 4: Review the complete recovery diff**

Confirm the diff contains only the approved public modules, synthetic fixtures,
tests, guidance, navigation, and scanner changes. Search for participant rows,
answers, condition mappings, task wording, nonce material, incident narratives,
institution names, direct identifiers, and repository-external paths; any real
match outside synthetic contracts stops completion.

- [ ] **Step 5: Record the truthful terminal state**

The implementation result is `green-capable`, not observed
`evaluation-green`. Report:

- affected batch: externally retained and excluded;
- software gates: verified;
- replacement incident closure: requires authoritative external record;
- replacement pilot: not created or executed by this plan;
- terminal human evidence: pending a separately authorized clean pilot;
- power analysis: deferred until that first valid replacement batch reaches
  `evaluation-green`.

Require `git status --porcelain` empty. Do not push, tag, dispatch, or publish.
