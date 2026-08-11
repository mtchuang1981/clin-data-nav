import copy
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.effectiveness_recovery import (
    RECOVERY_KEYS,
    collection_status,
    compute_record_state,
    green_status,
    rating_status,
    restart_status,
    validate_recovery_record,
)
from scripts.effectiveness_analysis import (
    compute_environment_fingerprint,
    summarize_effectiveness,
    unlock_observations,
)
from tests.effectiveness_fixtures import (
    full_pilot_payloads,
    score_bytes,
    valid_lock,
    valid_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "evals/effectiveness/recovery/recovery-template.json"
SYNTHETIC = ROOT / "evals/effectiveness/recovery/examples/synthetic-recovery.json"
CLI = ROOT / "scripts/validate_effectiveness_recovery.py"
CLI_ERROR = "effectiveness recovery validation failed\n"
RECOVERY_README = ROOT / "evals/effectiveness/recovery/README.md"
RECOVERY_CHECKLIST = ROOT / "evals/effectiveness/recovery/checklist.md"
RECOVERY_CHECKLIST_ZH_TW = (
    ROOT / "evals/effectiveness/recovery/checklist.zh-TW.md"
)
RECOVERY_STATES = (
    "blocked-incident-open",
    "ready-for-restart-review",
    "authorized-for-fresh-batch",
    "ready-for-blinded-rating",
    "eligible-for-locked-unlock",
    "evaluation-green",
)
RECOVERY_COMMANDS = (
    "python scripts/validate_effectiveness_recovery.py restart-check --recovery-record <external-path>",
    "python scripts/validate_effectiveness_recovery.py collection-check --recovery-record <external-path> --study-manifest <external-path>",
    "python scripts/validate_effectiveness_recovery.py rating-check --recovery-record <external-path> --study-manifest <external-path> --scores <external-path> --ratings-lock <external-path>",
    "python scripts/validate_effectiveness_recovery.py green-check --recovery-record <external-path> --study-manifest <external-path> --scores <external-path> --ratings-lock <external-path> --condition-key <external-path> --aggregate-summary <external-path> --unlock-after-ratings-lock",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def run_recovery_cli(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *(str(arg) for arg in args)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def canonical_stdout(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def documented_recovery_states(text: str) -> tuple[str, ...]:
    return tuple(
        line.split("`", 2)[1]
        for line in text.splitlines()
        if line.startswith("| `")
    )


def test_bilingual_recovery_checklists_align_states_and_authority_boundaries():
    english = RECOVERY_CHECKLIST.read_text(encoding="utf-8")
    traditional_chinese = RECOVERY_CHECKLIST_ZH_TW.read_text(encoding="utf-8")

    assert documented_recovery_states(english) == RECOVERY_STATES
    assert documented_recovery_states(traditional_chinese) == RECOVERY_STATES
    for text in (english, traditional_chinese):
        assert "excluded-from-effectiveness-analysis" in text
        assert "evaluation-green" in text
        assert "not an ethics determination" in text
        assert "not recruitment authorization" in text
    assert "不是倫理判定" in traditional_chinese
    assert "不是招募授權" in traditional_chinese
    assert "20-point practical difference" in english
    assert "20 個百分點的預先指定實務差異" in traditional_chinese


def test_recovery_readme_has_fixed_section_order_commands_and_exit_codes():
    text = RECOVERY_README.read_text(encoding="utf-8")
    assert tuple(
        line for line in text.splitlines() if line.startswith("## ")
    ) == (
        "## 1. Purpose and authority boundary",
        "## 2. Why the affected batch remains excluded",
        "## 3. External recovery record",
        "## 4. Restart check",
        "## 5. Collection check",
        "## 6. Rating check",
        "## 7. Terminal green check",
        "## 8. Interpret states and exit codes",
        "## 9. Replacement incident recursion",
        "## 10. Reporting and power-analysis boundary",
    )
    for command in RECOVERY_COMMANDS:
        assert command in text
    for exit_code in ("`0`", "`2`", "`3`"):
        assert exit_code in text
    assert "not an ethics determination" in text
    assert "not recruitment authorization" in text


def test_effectiveness_readme_routes_every_recovery_stage():
    text = (ROOT / "evals/effectiveness/README.md").read_text(encoding="utf-8")

    assert "recovery/README.md" in text
    for command in RECOVERY_COMMANDS:
        assert command in text


def write_green_cli_inputs(tmp_path: Path) -> tuple[dict[str, Path], tuple]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    record, manifest, scores, lock, key, raw_scores, summary = green_gate_inputs()
    payloads = {
        "recovery_record": record,
        "study_manifest": manifest,
        "ratings_lock": lock,
        "condition_key": key,
        "aggregate_summary": summary,
    }
    paths = {
        name: tmp_path / f"{name.replace('_', '-')}.json" for name in payloads
    }
    paths["scores"] = tmp_path / "scores.json"
    for name, payload in payloads.items():
        write_json(paths[name], payload)
    paths["scores"].write_bytes(raw_scores)
    return paths, (record, manifest, scores, lock, key, raw_scores, summary)


def invalid_errors(payload: object) -> list[str]:
    errors = validate_recovery_record(payload)
    assert errors
    return errors


def test_template_is_valid_and_blocked_without_external_closure():
    payload = load_json(TEMPLATE)

    assert validate_recovery_record(payload) == []
    assert compute_record_state(payload)["status"] == "blocked-incident-open"


def test_synthetic_record_never_claims_terminal_human_evidence():
    payload = load_json(SYNTHETIC)

    assert payload["synthetic_example"] is True
    assert validate_recovery_record(payload) == []
    assert compute_record_state(payload)["status"] == "authorized-for-fresh-batch"


def test_public_fixtures_are_canonical_json_with_one_final_newline():
    for path in (TEMPLATE, SYNTHETIC):
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))

        assert raw == (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")


@pytest.mark.parametrize("key", sorted(RECOVERY_KEYS))
def test_schema_rejects_every_missing_top_level_key(key):
    payload = load_json(SYNTHETIC)
    del payload[key]

    assert invalid_errors(payload) == [f"missing key: {key}"]


@pytest.mark.parametrize("key", ("status", "green", "approved", "authorization"))
def test_schema_rejects_status_and_approval_shortcuts(key):
    payload = load_json(SYNTHETIC)
    payload[key] = True

    assert invalid_errors(payload) == ["unexpected key"]


def test_schema_reports_missing_keys_before_unexpected_keys():
    payload = load_json(SYNTHETIC)
    del payload["schema_version"]
    payload["status"] = "evaluation-green"

    assert invalid_errors(payload) == ["missing key: schema_version"]


@pytest.mark.parametrize(
    "field,value",
    (
        ("affected_task_commitment_sha256", "A" * 64),
        ("replacement_skill_commit", "a" * 39),
        ("incident_record_sha256", "b" * 63),
        ("affected_study_id", "bad id"),
        ("replacement_assignment_version", "a"),
        ("incident_closed_at", "2026-08-11T09:00:00"),
    ),
)
def test_schema_rejects_invalid_hash_identifier_and_timestamp_values(field, value):
    payload = load_json(SYNTHETIC)
    payload[field] = value

    assert invalid_errors(payload) == [f"invalid {field}"]


@pytest.mark.parametrize(
    "field",
    (
        "incident_closed_at",
        "restart_decided_at",
        "replacement_skill_name",
        "collection_closed_at",
        "integrity_attested_at",
    ),
)
def test_schema_rejects_inconsistent_lifecycle_groups(field):
    payload = load_json(SYNTHETIC)
    payload[field] = None

    assert invalid_errors(payload) == [f"incomplete lifecycle group: {field}"]


@pytest.mark.parametrize(
    "field",
    (
        "environment_change_detected",
        "task_pack_leakage_detected",
        "reportable_incident_detected",
    ),
)
def test_schema_requires_boolean_integrity_flags(field):
    payload = load_json(SYNTHETIC)
    payload[field] = "false"

    assert invalid_errors(payload) == [f"invalid {field}"]


def test_schema_rejects_reused_affected_bindings():
    payload = load_json(SYNTHETIC)
    payload["replacement_study_id"] = payload["affected_study_id"]

    assert invalid_errors(payload) == ["affected and replacement study IDs must differ"]

    payload = load_json(SYNTHETIC)
    payload["replacement_task_commitment_sha256"] = payload[
        "affected_task_commitment_sha256"
    ]

    assert invalid_errors(payload) == ["affected and replacement task commitments must differ"]


def test_schema_requires_affected_identity_before_restart_authorization():
    payload = load_json(SYNTHETIC)
    payload["affected_study_id"] = None
    payload["affected_task_commitment_sha256"] = None

    assert invalid_errors(payload) == [
        "affected identity is required for authorized restart"
    ]
    with pytest.raises(ValueError, match="^invalid recovery record$"):
        compute_record_state(payload)


def test_schema_rejects_mixed_type_unknown_keys_without_sorting_error():
    payload = load_json(SYNTHETIC)
    payload[1] = True
    payload["unexpected"] = True

    assert invalid_errors(payload) == ["unexpected key"]


@pytest.mark.parametrize(
    "field,value",
    (
        ("replacement_skill_name", "clinical-data-research-navigator"),
        ("replacement_skill_version", "0.4.0"),
    ),
)
def test_schema_requires_the_frozen_replacement_skill(field, value):
    payload = load_json(SYNTHETIC)
    payload[field] = value

    assert invalid_errors(payload) == [f"invalid {field}"]


def test_schema_rejects_non_chronological_lifecycle_timestamps():
    payload = load_json(SYNTHETIC)
    payload["restart_decided_at"] = payload["incident_closed_at"]

    assert invalid_errors(payload) == ["timestamps must be chronological"]


def test_state_is_sanitized_and_record_only():
    state = compute_record_state(load_json(SYNTHETIC))

    assert state == {
        "schema_version": "1",
        "status": "authorized-for-fresh-batch",
        "passed_gate_ids": [
            "affected-batch-excluded",
            "incident-closure",
            "restart-authorization",
            "replacement-bindings",
        ],
        "blocked_gate_ids": [],
        "synthetic_example": True,
    }


def test_state_requires_external_incident_closure_before_restart_review():
    payload = load_json(TEMPLATE)
    payload["affected_study_id"] = "synthetic-affected-study"
    payload["affected_task_commitment_sha256"] = "a" * 64

    assert compute_record_state(payload) == {
        "schema_version": "1",
        "status": "blocked-incident-open",
        "passed_gate_ids": ["affected-batch-excluded"],
        "blocked_gate_ids": ["incident-closure"],
        "synthetic_example": False,
    }


def test_state_blocks_restart_when_authorization_or_bindings_are_incomplete():
    payload = load_json(SYNTHETIC)
    payload["restart_decision"] = None
    payload["restart_decided_at"] = None
    payload["restart_record_sha256"] = None
    for field in (
        "replacement_study_id",
        "replacement_protocol_commit",
        "replacement_skill_name",
        "replacement_skill_version",
        "replacement_skill_commit",
        "replacement_task_commitment_sha256",
        "replacement_assignment_version",
        "replacement_environment_fingerprint",
        "collection_status",
        "collection_closed_at",
        "collection_record_sha256",
        "integrity_attested_at",
        "integrity_record_sha256",
        "environment_change_detected",
        "task_pack_leakage_detected",
        "reportable_incident_detected",
    ):
        payload[field] = None

    assert compute_record_state(payload) == {
        "schema_version": "1",
        "status": "ready-for-restart-review",
        "passed_gate_ids": ["affected-batch-excluded", "incident-closure"],
        "blocked_gate_ids": ["restart-authorization", "replacement-bindings"],
        "synthetic_example": True,
    }


def test_state_rejects_invalid_record_without_echoing_input_values():
    payload = copy.deepcopy(load_json(SYNTHETIC))
    marker = "unsafe marker"
    payload["affected_study_id"] = marker

    with pytest.raises(ValueError, match="^invalid recovery record$"):
        compute_record_state(payload)


def bound_manifest_and_record():
    manifest = valid_manifest()
    manifest["skill_version"] = "0.5.0"
    fingerprint = compute_environment_fingerprint(manifest)
    for session in manifest["sessions"]:
        session["environment_fingerprint"] = fingerprint

    record = copy.deepcopy(load_json(SYNTHETIC))
    record.update(
        {
            "replacement_study_id": manifest["study_id"],
            "replacement_protocol_commit": manifest["protocol_commit"],
            "replacement_skill_version": manifest["skill_version"],
            "replacement_skill_commit": manifest["skill_commit"],
            "replacement_task_commitment_sha256": manifest[
                "task_commitment_sha256"
            ],
            "replacement_assignment_version": "pilot-v1-assignments",
            "replacement_environment_fingerprint": fingerprint,
        }
    )
    return manifest, record


def refresh_manifest_fingerprint(manifest):
    fingerprint = compute_environment_fingerprint(manifest)
    for session in manifest["sessions"]:
        session["environment_fingerprint"] = fingerprint


def test_restart_status_transitions_are_limited_to_record_prerequisites():
    _, open_record = bound_manifest_and_record()
    open_record["incident_status"] = "open"
    open_record["incident_closed_at"] = None
    open_record["incident_record_sha256"] = None
    for field in (
        "restart_decision",
        "restart_decided_at",
        "restart_record_sha256",
        "replacement_study_id",
        "replacement_protocol_commit",
        "replacement_skill_name",
        "replacement_skill_version",
        "replacement_skill_commit",
        "replacement_task_commitment_sha256",
        "replacement_assignment_version",
        "replacement_environment_fingerprint",
        "collection_status",
        "collection_closed_at",
        "collection_record_sha256",
        "integrity_attested_at",
        "integrity_record_sha256",
        "environment_change_detected",
        "task_pack_leakage_detected",
        "reportable_incident_detected",
    ):
        open_record[field] = None

    closed_without_decision = copy.deepcopy(open_record)
    closed_without_decision.update(
        {
            "incident_status": "closed",
            "incident_closed_at": "2026-08-11T09:00:00+08:00",
            "incident_record_sha256": "b" * 64,
        }
    )
    _, authorized_record = bound_manifest_and_record()

    assert restart_status(open_record)["status"] == "blocked-incident-open"
    assert restart_status(closed_without_decision)["status"] == "ready-for-restart-review"
    assert restart_status(authorized_record)["status"] == "authorized-for-fresh-batch"


def test_collection_status_accepts_only_a_closed_clean_manifest_bound_batch():
    manifest, record = bound_manifest_and_record()

    assert collection_status(record, manifest)["status"] == "ready-for-blinded-rating"


@pytest.mark.parametrize(
    "mutation",
    (
        lambda record, manifest: record.update({"replacement_study_id": "other-study"}),
        lambda record, manifest: record.update({"replacement_protocol_commit": "d" * 40}),
        lambda record, manifest: (
            manifest.update({"skill_version": "0.4.0"}),
            refresh_manifest_fingerprint(manifest),
        ),
        lambda record, manifest: record.update({"replacement_skill_commit": "e" * 40}),
        lambda record, manifest: record.update(
            {"replacement_task_commitment_sha256": "f" * 64}
        ),
        lambda record, manifest: record.update(
            {"replacement_assignment_version": "different-assignment"}
        ),
        lambda record, manifest: record.update(
            {"replacement_environment_fingerprint": "0" * 64}
        ),
        lambda record, manifest: record.update(
            {
                "collection_status": None,
                "collection_closed_at": None,
                "collection_record_sha256": None,
                "integrity_attested_at": None,
                "integrity_record_sha256": None,
                "environment_change_detected": None,
                "task_pack_leakage_detected": None,
                "reportable_incident_detected": None,
            }
        ),
        lambda record, manifest: record.update({"environment_change_detected": True}),
        lambda record, manifest: record.update({"task_pack_leakage_detected": True}),
        lambda record, manifest: record.update({"reportable_incident_detected": True}),
    ),
)
def test_collection_status_fails_closed_when_any_binding_or_integrity_gate_breaks(
    mutation,
):
    manifest, record = bound_manifest_and_record()
    mutation(record, manifest)

    assert collection_status(record, manifest)["status"] != "ready-for-blinded-rating"


def test_collection_status_rejects_integrity_attestation_before_collection_closure():
    manifest, record = bound_manifest_and_record()
    record["collection_status"] = None
    record["collection_closed_at"] = None
    record["collection_record_sha256"] = None

    with pytest.raises(ValueError, match="^invalid recovery record$"):
        collection_status(record, manifest)


def test_collection_status_rejects_integrity_attestation_at_collection_closure():
    manifest, record = bound_manifest_and_record()
    record["integrity_attested_at"] = record["collection_closed_at"]

    with pytest.raises(ValueError, match="^invalid recovery record$"):
        collection_status(record, manifest)


def green_gate_inputs():
    manifest, scores, lock, key, raw_scores = full_pilot_payloads()
    manifest["skill_version"] = "0.5.0"
    refresh_manifest_fingerprint(manifest)
    record = copy.deepcopy(load_json(SYNTHETIC))
    record.update(
        {
            "synthetic_example": False,
            "replacement_study_id": manifest["study_id"],
            "replacement_protocol_commit": manifest["protocol_commit"],
            "replacement_skill_version": manifest["skill_version"],
            "replacement_skill_commit": manifest["skill_commit"],
            "replacement_task_commitment_sha256": manifest[
                "task_commitment_sha256"
            ],
            "replacement_assignment_version": "pilot-v1-assignments",
            "replacement_environment_fingerprint": compute_environment_fingerprint(
                manifest
            ),
        }
    )
    observations = unlock_observations(manifest, scores, lock, key, raw_scores)
    expected_summary = summarize_effectiveness(manifest, scores, observations)
    return record, manifest, scores, lock, key, raw_scores, expected_summary


def refresh_lock(scores):
    raw_scores = score_bytes(scores)
    return valid_lock(raw_scores), raw_scores


def add_disagreements(scores, changes):
    ratings = {
        (row["answer_id"], row["rater_code"]): row
        for row in scores["rater_scores"]
    }
    answer_ids = [row["answer_id"] for row in scores["observations"]]
    for index, (rater_code, fields) in enumerate(changes):
        answer_id = answer_ids[index]
        ratings[(answer_id, rater_code)].update(fields)
        scores["adjudications"].append(
            {
                "answer_id": answer_id,
                "adjudicator_code": "R3",
                "final_success": True,
                "final_critical_violation": False,
                "final_ordinal_quality": 4,
                "rationale_code": "other-prespecified",
            }
        )


def mark_participants_abandoned(scores, participant_codes):
    answer_ids = {
        row["answer_id"]
        for row in scores["observations"]
        if row["participant_code"] in participant_codes
    }
    for row in scores["observations"]:
        if row["answer_id"] not in answer_ids:
            continue
        row["completion_status"] = "abandoned"
        for field in (
            "mandatory_complete",
            "quality_met",
            "quality_applicable",
            "quality_score",
            "critical_violation",
            "criterion_scores",
            "nasa_tlx_ratings",
            "nasa_tlx_weights",
            "confidence_before",
            "confidence_after",
            "understanding_before",
            "understanding_after",
        ):
            row[field] = None
    scores["rater_scores"] = [
        row for row in scores["rater_scores"] if row["answer_id"] not in answer_ids
    ]


def make_effect_favorable(scores, key):
    condition_by_answer = {
        row["answer_id"]: row["condition"] for row in key["mappings"]
    }
    changed_participants = set()
    changed_answer_ids = set()
    for observation in scores["observations"]:
        if (
            condition_by_answer[observation["answer_id"]] == "control"
            and observation["participant_code"] not in changed_participants
        ):
            observation["criterion_scores"][0]["met"] = False
            observation["mandatory_complete"] = False
            changed_participants.add(observation["participant_code"])
            changed_answer_ids.add(observation["answer_id"])
    for rating in scores["rater_scores"]:
        if rating["answer_id"] in changed_answer_ids:
            rating["success"] = False


def assert_not_green(result):
    assert result["status"] != "evaluation-green"
    assert set(result) == {
        "schema_version",
        "status",
        "passed_gate_ids",
        "blocked_gate_ids",
        "synthetic_example",
    }


def test_rating_status_requires_exact_locked_bytes_and_eligible_agreement():
    record, manifest, scores, lock, _, raw_scores, _ = green_gate_inputs()

    assert rating_status(record, manifest, scores, lock, raw_scores)[
        "status"
    ] == "eligible-for-locked-unlock"

    changed_bytes = rating_status(record, manifest, scores, lock, raw_scores + b" ")
    assert changed_bytes["status"] == "ready-for-blinded-rating"
    assert "ratings-lock-and-blinded-inputs" in changed_bytes["blocked_gate_ids"]

    incomplete_lock = copy.deepcopy(lock)
    incomplete_lock["ratings_complete"] = False
    incomplete = rating_status(record, manifest, scores, incomplete_lock, raw_scores)
    assert incomplete["status"] == "ready-for-blinded-rating"
    assert "ratings-lock-and-blinded-inputs" in incomplete["blocked_gate_ids"]


def test_rating_status_blocks_raw_agreement_below_eighty_percent():
    record, manifest, scores, _, _, _, _ = green_gate_inputs()
    add_disagreements(scores, [("R2", {"success": False})] * 13)
    lock, raw_scores = refresh_lock(scores)

    result = rating_status(record, manifest, scores, lock, raw_scores)

    assert result["status"] == "ready-for-blinded-rating"
    assert "blinded-agreement" in result["blocked_gate_ids"]


@pytest.mark.parametrize(
    "changes",
    (
        [("R1", {"success": False})] * 6
        + [("R2", {"success": False})] * 6,
        [("R1", {"ordinal_quality": 0})] * 6
        + [("R2", {"ordinal_quality": 0})] * 6,
    ),
)
def test_rating_status_blocks_each_estimable_kappa_below_sixty_percent(changes):
    record, manifest, scores, _, _, _, _ = green_gate_inputs()
    add_disagreements(scores, changes)
    lock, raw_scores = refresh_lock(scores)

    result = rating_status(record, manifest, scores, lock, raw_scores)

    assert result["status"] == "ready-for-blinded-rating"
    assert "blinded-agreement" in result["blocked_gate_ids"]


def test_green_status_recomputes_the_exact_aggregate_after_explicit_unlock():
    record, manifest, scores, lock, key, raw_scores, expected_summary = (
        green_gate_inputs()
    )

    result = green_status(
        record,
        manifest,
        scores,
        lock,
        key,
        raw_scores,
        expected_summary,
        unlock_after_ratings_lock=True,
    )

    assert result["status"] == "evaluation-green"
    assert result["blocked_gate_ids"] == []
    assert result["synthetic_example"] is False


@pytest.mark.parametrize(
    ("mutation_name", "mutation"),
    (
        (
            "integer-zero-replaced-by-false",
            lambda summary: summary["participant_flow"].update(
                {"abandonments": False}
            ),
        ),
        (
            "integer-one-replaced-by-true",
            lambda summary: summary["limitations"]["items"][0].update(
                {"count": True}
            ),
        ),
        (
            "integer-zero-replaced-by-decimal",
            lambda summary: summary["participant_flow"].update(
                {"abandonments": Decimal(0)}
            ),
        ),
        (
            "finite-number-replaced-by-nan",
            lambda summary: summary["primary"]["overall"].update(
                {"paired_risk_difference": float("nan")}
            ),
        ),
        (
            "finite-number-replaced-by-infinity",
            lambda summary: summary["primary"]["overall"].update(
                {"paired_risk_difference": float("inf")}
            ),
        ),
    ),
)
def test_green_status_requires_type_strict_json_safe_aggregate(
    mutation_name, mutation
):
    record, manifest, scores, lock, key, raw_scores, expected_summary = (
        green_gate_inputs()
    )
    mutation(expected_summary)

    result = green_status(
        record,
        manifest,
        scores,
        lock,
        key,
        raw_scores,
        expected_summary,
        unlock_after_ratings_lock=True,
    )

    assert_not_green(result), mutation_name
    assert "aggregate-recomputation" in result["blocked_gate_ids"]


def test_green_status_requires_literal_explicit_unlock():
    record, manifest, scores, lock, key, raw_scores, expected_summary = (
        green_gate_inputs()
    )

    result = green_status(
        record,
        manifest,
        scores,
        lock,
        key,
        raw_scores,
        expected_summary,
        unlock_after_ratings_lock=1,
    )

    assert_not_green(result)
    assert "explicit-locked-unlock" in result["blocked_gate_ids"]


def test_green_status_hides_condition_key_validation_values():
    record, manifest, scores, lock, key, raw_scores, expected_summary = (
        green_gate_inputs()
    )
    marker = "SENSITIVE-SYNTHETIC-STUDY-MARKER"
    key["study_id"] = marker

    result = green_status(
        record,
        manifest,
        scores,
        lock,
        key,
        raw_scores,
        expected_summary,
        unlock_after_ratings_lock=True,
    )

    assert_not_green(result)
    assert marker not in json.dumps(result, sort_keys=True)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda record, summary: summary.update({"minimum_practical_difference": 0.3}),
        lambda record, summary: record.update({"synthetic_example": True}),
        lambda record, summary: record.update(
            {"replacement_study_id": record["affected_study_id"]}
        ),
        lambda record, summary: record.update(
            {
                "replacement_task_commitment_sha256": record[
                    "affected_task_commitment_sha256"
                ]
            }
        ),
    ),
)
def test_green_status_blocks_stale_synthetic_or_reused_evidence(mutation):
    record, manifest, scores, lock, key, raw_scores, expected_summary = (
        green_gate_inputs()
    )
    mutation(record, expected_summary)

    result = green_status(
        record,
        manifest,
        scores,
        lock,
        key,
        raw_scores,
        expected_summary,
        unlock_after_ratings_lock=True,
    )

    assert_not_green(result)


def test_green_status_requires_at_least_fourteen_complete_participants():
    record, manifest, scores, _, key, _, _ = green_gate_inputs()
    mark_participants_abandoned(scores, {"B01", "B02", "B03"})
    lock, raw_scores = refresh_lock(scores)
    observations = unlock_observations(manifest, scores, lock, key, raw_scores)
    expected_summary = summarize_effectiveness(manifest, scores, observations)
    assert expected_summary["participant_flow"]["completed"] == 13

    result = green_status(
        record,
        manifest,
        scores,
        lock,
        key,
        raw_scores,
        expected_summary,
        unlock_after_ratings_lock=True,
    )

    assert_not_green(result)
    assert "completion-and-interpretation" in result["blocked_gate_ids"]


@pytest.mark.parametrize(
    ("review_field", "summary_field", "category_id"),
    (
        ("protocol_deviations", "protocol_deviations", "environment-consistency"),
        ("protocol_deviations", "protocol_deviations", "task-pack-integrity"),
        ("study_limitations", "limitations", "environment-batch-change"),
        ("study_limitations", "limitations", "task-pack-leakage"),
    ),
)
def test_green_status_blocks_each_prohibited_finding_despite_favorable_effect(
    review_field, summary_field, category_id
):
    record, manifest, scores, _, key, _, _ = green_gate_inputs()
    make_effect_favorable(scores, key)
    scores[review_field] = {
        "review_status": "reviewed-with-findings",
        "items": [{"category_id": category_id, "count": 1}],
    }
    lock, raw_scores = refresh_lock(scores)
    observations = unlock_observations(manifest, scores, lock, key, raw_scores)
    expected_summary = summarize_effectiveness(manifest, scores, observations)
    assert expected_summary["primary"]["overall"]["paired_risk_difference"] > 0
    assert expected_summary[summary_field]["items"] == [
        {"category_id": category_id, "count": 1}
    ]

    result = green_status(
        record,
        manifest,
        scores,
        lock,
        key,
        raw_scores,
        expected_summary,
        unlock_after_ratings_lock=True,
    )

    assert_not_green(result)
    assert "replacement-integrity-findings" in result["blocked_gate_ids"]


def assert_cli_status(
    result: subprocess.CompletedProcess[str], exit_code: int, status: str
) -> dict:
    assert result.returncode == exit_code
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert result.stdout == canonical_stdout(payload)
    assert set(payload) == {
        "schema_version",
        "status",
        "passed_gate_ids",
        "blocked_gate_ids",
    }
    assert payload["status"] == status
    return payload


def test_cli_restart_check_accepts_only_the_recovery_record(tmp_path):
    paths, _ = write_green_cli_inputs(tmp_path)

    result = run_recovery_cli(
        "restart-check", "--recovery-record", paths["recovery_record"]
    )

    payload = assert_cli_status(result, 0, "authorized-for-fresh-batch")
    assert payload["blocked_gate_ids"] == []


def test_cli_collection_check_binds_the_external_manifest(tmp_path):
    paths, _ = write_green_cli_inputs(tmp_path)

    result = run_recovery_cli(
        "collection-check",
        "--recovery-record",
        paths["recovery_record"],
        "--study-manifest",
        paths["study_manifest"],
    )

    payload = assert_cli_status(result, 0, "ready-for-blinded-rating")
    assert payload["blocked_gate_ids"] == []


def test_cli_rating_check_uses_the_exact_locked_score_bytes(tmp_path):
    paths, _ = write_green_cli_inputs(tmp_path)

    result = run_recovery_cli(
        "rating-check",
        "--recovery-record",
        paths["recovery_record"],
        "--study-manifest",
        paths["study_manifest"],
        "--scores",
        paths["scores"],
        "--ratings-lock",
        paths["ratings_lock"],
    )

    payload = assert_cli_status(result, 0, "eligible-for-locked-unlock")
    assert payload["blocked_gate_ids"] == []


def test_cli_green_check_is_canonical_and_does_not_mutate_any_input(tmp_path):
    paths, _ = write_green_cli_inputs(tmp_path)
    before = {name: path.read_bytes() for name, path in paths.items()}

    result = run_recovery_cli(
        "green-check",
        "--recovery-record",
        paths["recovery_record"],
        "--study-manifest",
        paths["study_manifest"],
        "--scores",
        paths["scores"],
        "--ratings-lock",
        paths["ratings_lock"],
        "--condition-key",
        paths["condition_key"],
        "--aggregate-summary",
        paths["aggregate_summary"],
        "--unlock-after-ratings-lock",
    )

    payload = assert_cli_status(result, 0, "evaluation-green")
    assert payload["blocked_gate_ids"] == []
    assert {name: path.read_bytes() for name, path in paths.items()} == before


def test_cli_returns_exit_3_for_each_valid_incomplete_or_blocked_stage(tmp_path):
    paths, inputs = write_green_cli_inputs(tmp_path)
    record, _, scores, _, _, _, _ = inputs

    open_record = load_json(TEMPLATE)
    write_json(paths["recovery_record"], open_record)
    restart = run_recovery_cli(
        "restart-check", "--recovery-record", paths["recovery_record"]
    )
    assert_cli_status(restart, 3, "blocked-incident-open")

    record["environment_change_detected"] = True
    write_json(paths["recovery_record"], record)
    collection = run_recovery_cli(
        "collection-check",
        "--recovery-record",
        paths["recovery_record"],
        "--study-manifest",
        paths["study_manifest"],
    )
    assert_cli_status(collection, 3, "authorized-for-fresh-batch")

    record["environment_change_detected"] = False
    add_disagreements(scores, [("R2", {"success": False})] * 13)
    lock, raw_scores = refresh_lock(scores)
    write_json(paths["recovery_record"], record)
    paths["scores"].write_bytes(raw_scores)
    write_json(paths["ratings_lock"], lock)
    rating = run_recovery_cli(
        "rating-check",
        "--recovery-record",
        paths["recovery_record"],
        "--study-manifest",
        paths["study_manifest"],
        "--scores",
        paths["scores"],
        "--ratings-lock",
        paths["ratings_lock"],
    )
    assert_cli_status(rating, 3, "ready-for-blinded-rating")

    paths, inputs = write_green_cli_inputs(tmp_path / "synthetic-green")
    record = inputs[0]
    record["synthetic_example"] = True
    write_json(paths["recovery_record"], record)
    green = run_recovery_cli(
        "green-check",
        "--recovery-record",
        paths["recovery_record"],
        "--study-manifest",
        paths["study_manifest"],
        "--scores",
        paths["scores"],
        "--ratings-lock",
        paths["ratings_lock"],
        "--condition-key",
        paths["condition_key"],
        "--aggregate-summary",
        paths["aggregate_summary"],
        "--unlock-after-ratings-lock",
    )
    assert_cli_status(green, 3, "eligible-for-locked-unlock")


def test_cli_rejects_repository_internal_paths_without_reading_them():
    result = run_recovery_cli(
        "restart-check", "--recovery-record", SYNTHETIC
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR


def test_cli_rejects_malformed_json_without_disclosing_content(tmp_path):
    marker = "SENSITIVE-MALFORMED-RECOVERY-MARKER"
    record_path = tmp_path / "recovery.json"
    record_path.write_text(f'{{"marker":"{marker}"', encoding="utf-8")

    result = run_recovery_cli(
        "restart-check", "--recovery-record", record_path
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
    assert marker not in result.stdout + result.stderr


def test_cli_rejects_abbreviated_flags_with_the_fixed_error(tmp_path):
    paths, _ = write_green_cli_inputs(tmp_path)

    result = run_recovery_cli(
        "restart-check", "--recovery-rec", paths["recovery_record"]
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR


def test_cli_green_check_requires_the_literal_unlock_flag(tmp_path):
    paths, _ = write_green_cli_inputs(tmp_path)

    result = run_recovery_cli(
        "green-check",
        "--recovery-record",
        paths["recovery_record"],
        "--study-manifest",
        paths["study_manifest"],
        "--scores",
        paths["scores"],
        "--ratings-lock",
        paths["ratings_lock"],
        "--condition-key",
        paths["condition_key"],
        "--aggregate-summary",
        paths["aggregate_summary"],
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR


def test_cli_rejects_hardlink_aliases_between_two_inputs(tmp_path):
    paths, _ = write_green_cli_inputs(tmp_path)
    aggregate_alias = tmp_path / "aggregate-alias.json"
    aggregate_alias.hardlink_to(paths["scores"])

    result = run_recovery_cli(
        "green-check",
        "--recovery-record",
        paths["recovery_record"],
        "--study-manifest",
        paths["study_manifest"],
        "--scores",
        paths["scores"],
        "--ratings-lock",
        paths["ratings_lock"],
        "--condition-key",
        paths["condition_key"],
        "--aggregate-summary",
        aggregate_alias,
        "--unlock-after-ratings-lock",
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR


@pytest.mark.parametrize(
    ("late_input_name", "late_input_state"),
    (
        ("condition_key", "malformed"),
        ("condition_key", "missing"),
        ("aggregate_summary", "malformed"),
        ("aggregate_summary", "missing"),
    ),
)
def test_cli_green_check_does_not_open_late_inputs_before_rating_is_eligible(
    tmp_path, late_input_name, late_input_state
):
    paths, inputs = write_green_cli_inputs(tmp_path)
    scores = inputs[2]
    add_disagreements(scores, [("R2", {"success": False})] * 13)
    lock, raw_scores = refresh_lock(scores)
    paths["scores"].write_bytes(raw_scores)
    write_json(paths["ratings_lock"], lock)

    marker = "SENSITIVE-LATE-STAGE-MARKER"
    if late_input_state == "malformed":
        paths[late_input_name].write_text(
            f'{{"marker":"{marker}"', encoding="utf-8"
        )
    else:
        paths[late_input_name] = tmp_path / f"missing-{late_input_name}.json"

    result = run_recovery_cli(
        "green-check",
        "--recovery-record",
        paths["recovery_record"],
        "--study-manifest",
        paths["study_manifest"],
        "--scores",
        paths["scores"],
        "--ratings-lock",
        paths["ratings_lock"],
        "--condition-key",
        paths["condition_key"],
        "--aggregate-summary",
        paths["aggregate_summary"],
        "--unlock-after-ratings-lock",
    )

    payload = assert_cli_status(result, 3, "ready-for-blinded-rating")
    assert payload["blocked_gate_ids"][-1] == "blinded-agreement"
    assert marker not in result.stdout + result.stderr


def test_cli_never_projects_source_synthetic_example_to_stdout(tmp_path):
    paths, inputs = write_green_cli_inputs(tmp_path)
    record = inputs[0]
    record["synthetic_example"] = True
    write_json(paths["recovery_record"], record)

    result = run_recovery_cli(
        "restart-check", "--recovery-record", paths["recovery_record"]
    )

    payload = assert_cli_status(result, 0, "authorized-for-fresh-batch")
    assert "synthetic_example" not in payload


def test_cli_rating_check_treats_an_incomplete_lock_as_valid_but_blocked(tmp_path):
    paths, inputs = write_green_cli_inputs(tmp_path)
    lock = inputs[3]
    lock["ratings_complete"] = False
    write_json(paths["ratings_lock"], lock)

    result = run_recovery_cli(
        "rating-check",
        "--recovery-record",
        paths["recovery_record"],
        "--study-manifest",
        paths["study_manifest"],
        "--scores",
        paths["scores"],
        "--ratings-lock",
        paths["ratings_lock"],
    )

    payload = assert_cli_status(result, 3, "ready-for-blinded-rating")
    assert payload["blocked_gate_ids"][-1] == "ratings-lock-and-blinded-inputs"


def test_cli_rejects_score_lock_mismatch_without_dynamic_text(tmp_path):
    paths, _ = write_green_cli_inputs(tmp_path)
    paths["scores"].write_bytes(paths["scores"].read_bytes() + b" ")

    result = run_recovery_cli(
        "rating-check",
        "--recovery-record",
        paths["recovery_record"],
        "--study-manifest",
        paths["study_manifest"],
        "--scores",
        paths["scores"],
        "--ratings-lock",
        paths["ratings_lock"],
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR


def test_cli_rejects_recovery_manifest_cross_file_mismatch(tmp_path):
    paths, inputs = write_green_cli_inputs(tmp_path)
    marker = "SENSITIVE-MISMATCHED-STUDY"
    record = inputs[0]
    record["replacement_study_id"] = marker
    write_json(paths["recovery_record"], record)

    result = run_recovery_cli(
        "collection-check",
        "--recovery-record",
        paths["recovery_record"],
        "--study-manifest",
        paths["study_manifest"],
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
    assert marker not in result.stdout + result.stderr


@pytest.mark.parametrize(
    ("target", "payload"),
    (
        ("recovery_record", {"marker": "SENSITIVE-INVALID-RECORD"}),
        ("study_manifest", {"marker": "SENSITIVE-INVALID-MANIFEST"}),
        ("scores", {"marker": "SENSITIVE-INVALID-SCORES"}),
        ("condition_key", {"marker": "SENSITIVE-INVALID-KEY"}),
        ("ratings_lock", {"marker": "SENSITIVE-INVALID-LOCK"}),
        ("aggregate_summary", {"marker": "SENSITIVE-STALE-SUMMARY"}),
    ),
)
def test_cli_rejects_schema_and_cross_file_failures_without_dynamic_text(
    tmp_path, target, payload
):
    paths, _ = write_green_cli_inputs(tmp_path)
    write_json(paths[target], payload)

    result = run_recovery_cli(
        "green-check",
        "--recovery-record",
        paths["recovery_record"],
        "--study-manifest",
        paths["study_manifest"],
        "--scores",
        paths["scores"],
        "--ratings-lock",
        paths["ratings_lock"],
        "--condition-key",
        paths["condition_key"],
        "--aggregate-summary",
        paths["aggregate_summary"],
        "--unlock-after-ratings-lock",
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
    assert payload["marker"] not in result.stdout + result.stderr
