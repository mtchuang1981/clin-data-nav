from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path

from scripts.effectiveness_analysis import compute_environment_fingerprint
from scripts.effectiveness_contract import load_effectiveness_contract
from scripts.generate_study_assignments import generate_assignments


ROOT = Path(__file__).resolve().parents[1]


def criterion_scores_for_pair(pair_id, *, met=True):
    catalog, _ = load_effectiveness_contract(
        ROOT / "evals/effectiveness/offline-tasks.yaml",
        ROOT / "evals/effectiveness/rubric.yaml",
    )
    pair = next(item for item in catalog["task_pairs"] if item["id"] == pair_id)
    return [
        {"criterion_id": criterion_id, "applicable": True, "met": met}
        for criterion_id in (*pair["mandatory_criteria"], *pair["quality_criteria"])
    ]


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
        "protocol_deviations": {
            "review_status": "reviewed-none",
            "items": [],
        },
        "study_limitations": {
            "review_status": "reviewed-with-findings",
            "items": [
                {"category_id": "small-exploratory-sample", "count": 1},
                {"category_id": "synthetic-task-generalizability", "count": 1},
                {
                    "category_id": "controlled-environment-generalizability",
                    "count": 1,
                },
                {"category_id": "no-clinical-validity-inference", "count": 1},
            ],
        },
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
                "quality_met": 3,
                "quality_applicable": 3,
                "quality_score": 82,
                "critical_violation": False,
                "criterion_scores": criterion_scores_for_pair("quick-adam-sdtm"),
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
    pairs_by_id = {pair["id"]: pair for pair in catalog["task_pairs"]}
    for assignment in assignments:
        session_start = datetime.fromisoformat(
            "2026-09-01T09:00:00+08:00"
            if assignment["stratum"] == "beginner"
            else "2026-09-02T09:00:00+08:00"
        )
        started_at = session_start + timedelta(minutes=10 * (assignment["order"] - 1))
        ended_at = started_at + timedelta(minutes=7)
        pair = pairs_by_id[assignment["pair_id"]]
        criterion_scores = [
            {"criterion_id": criterion_id, "applicable": True, "met": True}
            for criterion_id in (
                *pair["mandatory_criteria"],
                *pair["quality_criteria"],
            )
        ]
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
                "quality_met": len(pair["quality_criteria"]),
                "quality_applicable": len(pair["quality_criteria"]),
                "quality_score": 82,
                "critical_violation": False,
                "criterion_scores": criterion_scores,
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
        "protocol_deviations": {
            "review_status": "reviewed-none",
            "items": [],
        },
        "study_limitations": {
            "review_status": "reviewed-with-findings",
            "items": [
                {"category_id": "small-exploratory-sample", "count": 1},
                {"category_id": "synthetic-task-generalizability", "count": 1},
                {
                    "category_id": "controlled-environment-generalizability",
                    "count": 1,
                },
                {"category_id": "no-clinical-validity-inference", "count": 1},
            ],
        },
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
