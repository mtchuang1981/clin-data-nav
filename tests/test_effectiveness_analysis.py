import copy
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.effectiveness_analysis import (
    compute_environment_fingerprint,
    unlock_observations,
    validate_blinded_scores,
    validate_condition_key,
    validate_pilot_layout,
    validate_ratings_lock,
    validate_study_manifest,
)
from scripts.effectiveness_contract import load_effectiveness_contract
from scripts.generate_study_assignments import generate_assignments


ROOT = Path(__file__).resolve().parents[1]
CLI_ERROR = "effectiveness analysis failed\n"
DEPTHS = {
    "quick explanation",
    "evidence navigation",
    "research design",
    "implementation specification",
}


def valid_manifest():
    manifest = {
        "schema_version": "1",
        "study_id": "synthetic-pilot-v1",
        "protocol_commit": "a" * 40,
        "skill_version": "0.3.0",
        "skill_commit": "b" * 40,
        "codex_surface": "Codex desktop",
        "model": "fixed-model-snapshot",
        "reasoning_effort": "medium",
        "service_tier": "priority",
        "python_version": "3.11.9",
        "platform": "Windows",
        "study_started_at": "2026-09-01T09:00:00+08:00",
        "study_ended_at": "2026-09-02T17:00:00+08:00",
        "task_commitment_sha256": "c" * 64,
        "task_commitment_verified": True,
        "bootstrap_seed": 20260809,
        "bootstrap_resamples": 20000,
        "sessions": [],
    }
    fingerprint = compute_environment_fingerprint(manifest)
    manifest["sessions"] = [
        {
            "participant_code": f"B{index:02d}",
            "stratum": "beginner",
            "assignment_version": "pilot-v1-assignments",
            "session_date": "2026-09-01",
            "environment_fingerprint": fingerprint,
        }
        for index in range(1, 9)
    ] + [
        {
            "participant_code": f"P{index:02d}",
            "stratum": "professional",
            "assignment_version": "pilot-v1-assignments",
            "session_date": "2026-09-02",
            "environment_fingerprint": fingerprint,
        }
        for index in range(1, 9)
    ]
    return manifest


def valid_scores():
    return {
        "schema_version": "1",
        "study_id": "synthetic-pilot-v1",
        "observations": [
            {
                "answer_id": "A000000000000001",
                "participant_code": "B01",
                "stratum": "beginner",
                "task_pair_id": "quick-adam-sdtm",
                "task_variant": "A",
                "output_depth": "quick explanation",
                "order": 1,
                "started_at": "2026-09-01T09:00:00+08:00",
                "ended_at": "2026-09-01T09:07:00+08:00",
                "completion_status": "completed",
                "completion_seconds": 420,
                "mandatory_complete": True,
                "quality_met": 4,
                "quality_applicable": 5,
                "quality_score": 82,
                "critical_violation": False,
                "nasa_tlx_ratings": [40, 0, 35, 70, 45, 20],
                "nasa_tlx_weights": [3, 0, 3, 3, 3, 3],
                "confidence_before": 2,
                "confidence_after": 4,
                "understanding_before": 2,
                "understanding_after": 4,
            }
        ],
        "rater_scores": [
            {
                "answer_id": "A000000000000001",
                "rater_code": "R1",
                "success": True,
                "critical_violation": False,
                "ordinal_quality": 4,
            },
            {
                "answer_id": "A000000000000001",
                "rater_code": "R2",
                "success": True,
                "critical_violation": False,
                "ordinal_quality": 4,
            },
        ],
        "adjudications": [],
        "sus_responses": [
            {
                "participant_code": "B01",
                "items": [4, 2, 4, 2, 4, 2, 4, 2, 4, 2],
            }
        ],
    }


def score_bytes(scores):
    return (json.dumps(scores, ensure_ascii=False, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def valid_lock(scores_bytes):
    return {
        "schema_version": "1",
        "study_id": "synthetic-pilot-v1",
        "scores_sha256": hashlib.sha256(scores_bytes).hexdigest(),
        "ratings_complete": True,
        "rater_codes": ["R1", "R2"],
        "locked_at": "2026-09-02T18:00:00+08:00",
    }


def valid_key(answer_ids=("A000000000000001",)):
    return {
        "schema_version": "1",
        "study_id": "synthetic-pilot-v1",
        "mappings": [
            {"answer_id": answer_id, "condition": "intervention"}
            for answer_id in answer_ids
        ],
    }


def full_pilot_payloads():
    catalog, _ = load_effectiveness_contract(
        ROOT / "evals/effectiveness/offline-tasks.yaml",
        ROOT / "evals/effectiveness/rubric.yaml",
    )
    assignments = generate_assignments(catalog, "synthetic-pilot-v1", 20260809)
    observations = []
    rater_scores = []
    for assignment in assignments:
        session_start = datetime.fromisoformat(
            "2026-09-01T09:00:00+08:00"
            if assignment["stratum"] == "beginner"
            else "2026-09-02T09:00:00+08:00"
        )
        started_at = session_start + timedelta(minutes=10 * (assignment["order"] - 1))
        ended_at = started_at + timedelta(minutes=7)
        observations.append(
            {
                "answer_id": assignment["answer_id"],
                "participant_code": assignment["participant_code"],
                "stratum": assignment["stratum"],
                "task_pair_id": assignment["pair_id"],
                "task_variant": assignment["variant"],
                "output_depth": assignment["output_depth"],
                "order": assignment["order"],
                "started_at": started_at.isoformat(),
                "ended_at": ended_at.isoformat(),
                "completion_status": "completed",
                "completion_seconds": 420,
                "mandatory_complete": True,
                "quality_met": 4,
                "quality_applicable": 5,
                "quality_score": 82,
                "critical_violation": False,
                "nasa_tlx_ratings": [40, 0, 35, 70, 45, 20],
                "nasa_tlx_weights": [3, 0, 3, 3, 3, 3],
                "confidence_before": 2,
                "confidence_after": 4,
                "understanding_before": 2,
                "understanding_after": 4,
            }
        )
        for rater_code in ("R1", "R2"):
            rater_scores.append(
                {
                    "answer_id": assignment["answer_id"],
                    "rater_code": rater_code,
                    "success": True,
                    "critical_violation": False,
                    "ordinal_quality": 4,
                }
            )
    scores = {
        "schema_version": "1",
        "study_id": "synthetic-pilot-v1",
        "observations": observations,
        "rater_scores": rater_scores,
        "adjudications": [],
        "sus_responses": [
            {
                "participant_code": participant_code,
                "items": [4, 2, 4, 2, 4, 2, 4, 2, 4, 2],
            }
            for participant_code in (
                *(f"B{index:02d}" for index in range(1, 9)),
                *(f"P{index:02d}" for index in range(1, 9)),
            )
        ],
    }
    raw_scores = score_bytes(scores)
    condition_key = {
        "schema_version": "1",
        "study_id": "synthetic-pilot-v1",
        "mappings": [
            {
                "answer_id": assignment["answer_id"],
                "condition": assignment["condition"],
            }
            for assignment in assignments
        ],
    }
    return valid_manifest(), scores, valid_lock(raw_scores), condition_key, raw_scores


def test_valid_closed_schema_payloads_are_accepted():
    manifest = valid_manifest()
    scores = valid_scores()
    raw_scores = score_bytes(scores)

    assert validate_study_manifest(manifest) == []
    assert validate_blinded_scores(scores) == []
    assert validate_ratings_lock(valid_lock(raw_scores), raw_scores) == []
    assert validate_condition_key(
        valid_key(), {"A000000000000001"}
    ) == []


def test_environment_fingerprint_is_canonical_and_uses_only_environment_fields():
    manifest = valid_manifest()
    fingerprint = compute_environment_fingerprint(manifest)
    changed_non_environment = copy.deepcopy(manifest)
    changed_non_environment["study_id"] = "another-synthetic-study"
    changed_non_environment["bootstrap_seed"] = 7

    assert len(fingerprint) == 64
    assert fingerprint == compute_environment_fingerprint(changed_non_environment)
    changed_non_environment["model"] = "another-fixed-snapshot"
    assert fingerprint != compute_environment_fingerprint(changed_non_environment)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda payload: payload.update({"name": "Synthetic Person"}),
        lambda payload: payload.update({"email": "synthetic@example.invalid"}),
        lambda payload: payload["observations"][0].update(
            {"answer_text": "SYNTHETIC-ANSWER-MARKER"}
        ),
        lambda payload: payload["observations"][0].update(
            {"condition": "intervention"}
        ),
        lambda payload: payload.update({"unknown_top_level": True}),
        lambda payload: payload["rater_scores"][0].update({"unknown_row": True}),
    ],
)
def test_blinded_scores_reject_identifiers_answers_conditions_and_unknown_keys(mutate):
    scores = valid_scores()
    mutate(scores)

    assert validate_blinded_scores(scores)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("participant_code", "X01"),
        ("stratum", "expert"),
        ("task_pair_id", "unknown-task"),
        ("output_depth", "full answer"),
        ("completion_status", "skipped"),
        ("task_variant", "C"),
        ("order", True),
        ("quality_score", 101),
        ("confidence_before", 0),
    ],
)
def test_blinded_scores_reject_unrecognized_or_out_of_range_observation_values(
    field, value
):
    scores = valid_scores()
    scores["observations"][0][field] = value

    assert validate_blinded_scores(scores)


def test_blinded_scores_reject_duplicate_answer_ids_and_invalid_duration():
    scores = valid_scores()
    duplicate = copy.deepcopy(scores["observations"][0])
    scores["observations"].append(duplicate)
    scores["rater_scores"].extend(copy.deepcopy(scores["rater_scores"]))

    assert validate_blinded_scores(scores)


@pytest.mark.parametrize(
    "field",
    (
        "participant_code",
        "stratum",
        "task_pair_id",
        "task_variant",
        "output_depth",
        "completion_status",
    ),
)
def test_blinded_validator_rejects_non_hashable_values_without_traceback(field):
    scores = valid_scores()
    scores["observations"][0][field] = []

    assert validate_blinded_scores(scores)


def test_key_layout_and_unlock_reject_non_hashable_values_without_traceback():
    key = valid_key()
    key["mappings"][0]["condition"] = []
    assert validate_condition_key(key, {"A000000000000001"})

    manifest, scores, lock, key, raw_scores = full_pilot_payloads()
    unlocked = [
        {**row, "condition": "control"} for row in scores["observations"]
    ]
    unlocked[0]["order"] = []
    assert validate_pilot_layout(unlocked)

    manifest["study_id"] = []
    with pytest.raises(ValueError, match="^invalid effectiveness study:"):
        unlock_observations(manifest, scores, lock, key, raw_scores)

    scores = valid_scores()
    scores["observations"][0]["completion_seconds"] = 419
    assert validate_blinded_scores(scores)


@pytest.mark.parametrize("status", ["abandoned", "technical_failure"])
def test_unscored_statuses_require_all_rating_and_survey_fields_to_be_null(status):
    scores = valid_scores()
    observation = scores["observations"][0]
    observation["completion_status"] = status
    scores["rater_scores"] = []
    assert validate_blinded_scores(scores)

    for field in (
        "mandatory_complete",
        "quality_met",
        "quality_applicable",
        "quality_score",
        "critical_violation",
        "nasa_tlx_ratings",
        "nasa_tlx_weights",
        "confidence_before",
        "confidence_after",
        "understanding_before",
        "understanding_after",
    ):
        observation[field] = None

    assert validate_blinded_scores(scores) == []


def test_scored_statuses_require_two_distinct_original_ratings():
    for rater_scores in (
        [],
        [copy.deepcopy(valid_scores()["rater_scores"][0])],
        valid_scores()["rater_scores"]
        + [copy.deepcopy(valid_scores()["rater_scores"][0])],
    ):
        scores = valid_scores()
        scores["rater_scores"] = rater_scores
        assert validate_blinded_scores(scores)


def test_rater_disagreement_requires_one_adjudication_and_final_flags_must_match():
    scores = valid_scores()
    scores["rater_scores"][1]["success"] = False
    assert validate_blinded_scores(scores)

    scores["adjudications"] = [
        {
            "answer_id": "A000000000000001",
            "adjudicator_code": "R3",
            "final_success": True,
            "final_critical_violation": False,
            "final_ordinal_quality": 3,
            "rationale_code": "mandatory-criterion",
        }
    ]
    assert validate_blinded_scores(scores) == []

    scores["adjudications"][0]["final_critical_violation"] = True
    assert validate_blinded_scores(scores)


def test_rater_agreement_forbids_adjudication_and_narrative_rationale():
    scores = valid_scores()
    scores["adjudications"] = [
        {
            "answer_id": "A000000000000001",
            "adjudicator_code": "R3",
            "final_success": True,
            "final_critical_violation": False,
            "final_ordinal_quality": 4,
            "rationale_code": "other-prespecified",
        }
    ]
    assert validate_blinded_scores(scores)

    scores["rater_scores"][1]["ordinal_quality"] = 3
    scores["adjudications"][0]["rationale_code"] = "because the answer said ..."
    assert validate_blinded_scores(scores)


def test_lock_requires_completed_ratings_raw_byte_hash_and_closed_schema():
    raw_scores = score_bytes(valid_scores())
    lock = valid_lock(raw_scores)
    lock["ratings_complete"] = False
    assert validate_ratings_lock(lock, raw_scores)

    lock = valid_lock(raw_scores)
    assert validate_ratings_lock(lock, raw_scores + b" ")

    lock = valid_lock(raw_scores)
    lock["unknown"] = True
    assert validate_ratings_lock(lock, raw_scores)


def test_condition_key_requires_exact_unique_answer_set_and_valid_conditions():
    answer_ids = {"A000000000000001"}
    key = valid_key()
    key["mappings"].append(copy.deepcopy(key["mappings"][0]))
    assert validate_condition_key(key, answer_ids)

    key = valid_key(())
    assert validate_condition_key(key, answer_ids)

    key = valid_key(("A000000000000001", "A000000000000002"))
    assert validate_condition_key(key, answer_ids)

    key = valid_key()
    key["mappings"][0]["condition"] = "skill"
    assert validate_condition_key(key, answer_ids)


@pytest.mark.parametrize("target", ["scores", "lock", "key"])
def test_unlock_requires_same_study_id_as_manifest_and_among_rating_files(target):
    manifest, scores, lock, key, raw_scores = full_pilot_payloads()
    values = {"scores": scores, "lock": lock, "key": key}
    values[target]["study_id"] = "another-synthetic-study"

    with pytest.raises(ValueError, match="^invalid effectiveness study:"):
        unlock_observations(manifest, scores, lock, key, raw_scores)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda manifest: manifest["sessions"].pop(),
        lambda manifest: manifest["sessions"].append(
            copy.deepcopy(manifest["sessions"][0])
        ),
        lambda manifest: manifest["sessions"][0].update(
            {"assignment_version": "changed-version"}
        ),
        lambda manifest: manifest["sessions"][0].update(
            {"environment_fingerprint": "0" * 64}
        ),
    ],
)
def test_manifest_rejects_missing_duplicate_or_changed_session_contract(mutate):
    manifest = valid_manifest()
    mutate(manifest)

    assert validate_study_manifest(manifest)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda manifest: manifest.update({"protocol_commit": "A" * 40}),
        lambda manifest: manifest.update({"task_commitment_sha256": "C" * 64}),
        lambda manifest: manifest.update({"task_commitment_verified": False}),
        lambda manifest: manifest.update({"bootstrap_seed": True}),
        lambda manifest: manifest.update({"bootstrap_resamples": 999}),
        lambda manifest: manifest.update(
            {"study_started_at": "2026-09-01T09:00:00"}
        ),
        lambda manifest: manifest.update(
            {
                "study_started_at": "2026-09-03T09:00:00+08:00",
                "study_ended_at": "2026-09-02T17:00:00+08:00",
            }
        ),
        lambda manifest: manifest.update({"model": "line one\nline two"}),
    ],
)
def test_manifest_rejects_invalid_commits_dates_bootstrap_or_environment(mutate):
    manifest = valid_manifest()
    mutate(manifest)

    assert validate_study_manifest(manifest)


def test_unlock_requires_manifest_session_membership_timestamps_and_post_study_lock():
    manifest, scores, lock, key, raw_scores = full_pilot_payloads()
    scores["observations"][0]["participant_code"] = "B02"
    changed_bytes = score_bytes(scores)
    lock = valid_lock(changed_bytes)
    with pytest.raises(ValueError):
        unlock_observations(manifest, scores, lock, key, changed_bytes)

    manifest, scores, lock, key, raw_scores = full_pilot_payloads()
    scores["observations"][0]["started_at"] = "2026-08-31T09:00:00+08:00"
    scores["observations"][0]["ended_at"] = "2026-08-31T09:07:00+08:00"
    changed_bytes = score_bytes(scores)
    lock = valid_lock(changed_bytes)
    with pytest.raises(ValueError):
        unlock_observations(manifest, scores, lock, key, changed_bytes)

    manifest, scores, lock, key, raw_scores = full_pilot_payloads()
    lock["locked_at"] = "2026-09-02T16:59:59+08:00"
    with pytest.raises(ValueError):
        unlock_observations(manifest, scores, lock, key, raw_scores)


def test_full_pilot_unlock_has_fixed_64_row_ratings_locked_layout():
    manifest, scores, lock, key, raw_scores = full_pilot_payloads()

    unlocked = unlock_observations(manifest, scores, lock, key, raw_scores)

    assert len(unlocked) == 64
    assert validate_pilot_layout(unlocked) == []
    assert {row["condition"] for row in unlocked} == {
        "control",
        "intervention",
    }


@pytest.mark.parametrize(
    "mutate",
    [
        lambda rows: rows.pop(),
        lambda rows: rows.append(copy.deepcopy(rows[0])),
        lambda rows: rows[0].update({"participant_code": "B02"}),
        lambda rows: rows[0].update({"order": 2}),
        lambda rows: rows[0].update(
            {
                "output_depth": next(
                    depth for depth in DEPTHS if depth != rows[0]["output_depth"]
                )
            }
        ),
        lambda rows: rows[0].update({"condition": "control"})
        if rows[0]["condition"] == "intervention"
        else rows[0].update({"condition": "intervention"}),
    ],
)
def test_pilot_layout_rejects_non_fixed_participant_order_depth_or_condition(mutate):
    manifest, scores, lock, key, raw_scores = full_pilot_payloads()
    condition_by_answer = {
        mapping["answer_id"]: mapping["condition"] for mapping in key["mappings"]
    }
    rows = [
        {**row, "condition": condition_by_answer[row["answer_id"]]}
        for row in scores["observations"]
    ]
    mutate(rows)

    assert validate_pilot_layout(rows)


def _write_cli_inputs(tmp_path):
    manifest, scores, lock, key, raw_scores = full_pilot_payloads()
    paths = {
        "manifest": tmp_path / "study-manifest.json",
        "scores": tmp_path / "blinded-scores.json",
        "lock": tmp_path / "ratings-lock.json",
        "key": tmp_path / "condition-key.json",
        "summary": tmp_path / "summary.json",
    }
    paths["manifest"].write_text(
        json.dumps(manifest, sort_keys=True), encoding="utf-8"
    )
    paths["scores"].write_bytes(raw_scores)
    paths["lock"].write_text(json.dumps(lock, sort_keys=True), encoding="utf-8")
    paths["key"].write_text(json.dumps(key, sort_keys=True), encoding="utf-8")
    return paths


def _cli_args(paths):
    return [
        sys.executable,
        str(ROOT / "scripts/analyze_effectiveness.py"),
        "analyze",
        "--study-manifest",
        str(paths["manifest"]),
        "--scores",
        str(paths["scores"]),
        "--ratings-lock",
        str(paths["lock"]),
        "--condition-key",
        str(paths["key"]),
        "--output-summary",
        str(paths["summary"]),
    ]


def test_cli_requires_explicit_post_lock_unlock_without_echoing_paths(tmp_path):
    paths = _write_cli_inputs(tmp_path)

    result = subprocess.run(
        _cli_args(paths), capture_output=True, text=True, check=False
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
    assert str(paths["key"]) not in result.stderr
    assert not paths["summary"].exists()


def test_cli_hides_rejected_values_paths_and_tracebacks(tmp_path):
    paths = _write_cli_inputs(tmp_path)
    marker = "SENSITIVE-SYNTHETIC-MARKER-31d5"
    paths["scores"].write_text(
        json.dumps({"answer_text": marker}), encoding="utf-8"
    )

    result = subprocess.run(
        [*_cli_args(paths), "--unlock-after-ratings-lock"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
    assert marker not in result.stderr
    assert str(paths["scores"]) not in result.stderr
    assert "Traceback" not in result.stderr
    assert not paths["summary"].exists()


def test_cli_writes_only_the_minimal_canonical_aggregate_summary(tmp_path):
    paths = _write_cli_inputs(tmp_path)

    result = subprocess.run(
        [*_cli_args(paths), "--unlock-after-ratings-lock"],
        capture_output=True,
        text=True,
        check=False,
    )

    expected = {
        "schema_version": "1",
        "study_id": "synthetic-pilot-v1",
        "validated_observation_count": 64,
    }
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    assert paths["summary"].read_bytes() == (
        json.dumps(expected, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    assert not any(key in expected for key in ("observations", "mappings", "sessions"))
