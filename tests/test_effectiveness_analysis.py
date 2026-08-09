import copy
from datetime import datetime, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys

import pytest

import scripts.analyze_effectiveness as analyze_module
from scripts.effectiveness_analysis import (
    aggregate_criterion_results,
    aggregate_paired_metric,
    blinded_agreement_status,
    bootstrap_mean_interval,
    clopper_pearson,
    cohens_kappa,
    compute_environment_fingerprint,
    linear_weighted_kappa,
    participant_paired_differences,
    score_nasa_tlx,
    score_sus,
    summarize_effectiveness,
    task_success,
    unlock_observations,
    validate_blinded_scores,
    validate_condition_key,
    validate_pilot_layout,
    validate_ratings_lock,
    validate_study_manifest,
)
from scripts.effectiveness_contract import load_effectiveness_contract
from scripts.generate_study_assignments import generate_assignments
from scripts.render_effectiveness_report import render_report


ROOT = Path(__file__).resolve().parents[1]
CLI_ERROR = "effectiveness analysis failed\n"
DEPTHS = {
    "quick explanation",
    "evidence navigation",
    "research design",
    "implementation specification",
}


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


def completed_observation(**changes):
    observation = copy.deepcopy(valid_scores()["observations"][0])
    observation.update(changes)
    return observation


def status_observation(status):
    observation = completed_observation(completion_status=status)
    if status in {"abandoned", "technical_failure"}:
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
            observation[field] = None
    return observation


def unlocked_complete_pilot(intervention_successes=None, control_successes=None):
    manifest, scores, lock, key, raw_scores = full_pilot_payloads()
    observations = unlock_observations(manifest, scores, lock, key, raw_scores)
    requested = {
        "intervention": intervention_successes or {},
        "control": control_successes or {},
    }
    for condition, successes_by_person in requested.items():
        for participant_code, successes in successes_by_person.items():
            rows = [
                row
                for row in observations
                if row["participant_code"] == participant_code
                and row["condition"] == condition
            ]
            assert len(rows) == 2
            for index, row in enumerate(rows):
                row["mandatory_complete"] = index < successes
                mandatory_ids = {
                    item["criterion_id"]
                    for item in row["criterion_scores"]
                    if item["criterion_id"] in {
                        criterion["id"]
                        for criterion in load_effectiveness_contract(
                            ROOT / "evals/effectiveness/offline-tasks.yaml",
                            ROOT / "evals/effectiveness/rubric.yaml",
                        )[1]["criteria"]
                        if criterion["kind"] == "mandatory"
                    }
                }
                for item in row["criterion_scores"]:
                    if item["criterion_id"] in mandatory_ids:
                        item["met"] = index < successes
                row["mandatory_complete"] = all(
                    item["met"]
                    for item in row["criterion_scores"]
                    if item["criterion_id"] in mandatory_ids
                )
                row["critical_violation"] = False
    return observations


def mark_unscored(observation, status):
    replacement = status_observation(status)
    for field in (
        "completion_status",
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
        observation[field] = replacement[field]


def scores_for_agreement(binary_pairs, ordinal_pairs=None, critical_pairs=None):
    ordinal_pairs = ordinal_pairs or [(4, 4)] * len(binary_pairs)
    critical_pairs = critical_pairs or [(False, False)] * len(binary_pairs)
    rater_scores = []
    for index, (binary_pair, ordinal_pair, critical_pair) in enumerate(
        zip(binary_pairs, ordinal_pairs, critical_pairs, strict=True), start=1
    ):
        answer_id = f"A{index:015X}"
        for rater_index, rater_code in enumerate(("R1", "R2")):
            rater_scores.append(
                {
                    "answer_id": answer_id,
                    "rater_code": rater_code,
                    "success": binary_pair[rater_index],
                    "critical_violation": critical_pair[rater_index],
                    "ordinal_quality": ordinal_pair[rater_index],
                }
            )
    return {"rater_scores": rater_scores, "adjudications": []}


def test_nasa_tlx_uses_six_weights_summing_to_fifteen():
    assert score_nasa_tlx(
        [40, 0, 35, 70, 45, 20],
        [3, 0, 3, 3, 3, 3],
    ) == pytest.approx(42.0)


@pytest.mark.parametrize(
    ("ratings", "weights"),
    [
        ([40] * 5, [3] * 5),
        ([40] * 6, [3, 3, 3, 3, 3, 1]),
        ([101, 0, 0, 0, 0, 0], [3, 3, 3, 3, 3, 0]),
        ([40] * 6, [6, 3, 3, 3, 0, 0]),
        ([True, 0, 0, 0, 0, 0], [3, 3, 3, 3, 3, 0]),
    ],
)
def test_nasa_tlx_rejects_invalid_scale_or_weights(ratings, weights):
    with pytest.raises(ValueError):
        score_nasa_tlx(ratings, weights)


def test_sus_uses_standard_odd_even_scoring():
    assert score_sus([4, 2, 4, 2, 4, 2, 4, 2, 4, 2]) == 75.0


@pytest.mark.parametrize(
    "items",
    ([4, 2] * 4, [4, 2, 4, 2, 4, 2, 4, 2, 4, 6], [True] * 10),
)
def test_sus_rejects_incomplete_or_out_of_range_items(items):
    with pytest.raises(ValueError):
        score_sus(items)


def test_kappa_is_one_for_perfect_agreement_and_none_without_variation():
    assert cohens_kappa([(True, True), (False, False)]) == 1.0
    assert cohens_kappa([(True, True), (True, True)]) is None


def test_linear_weighted_kappa_is_one_for_perfect_ordinal_agreement():
    assert linear_weighted_kappa([(0, 0), (2, 2), (4, 4)]) == 1.0


@pytest.mark.parametrize(
    ("function", "pairs"),
    [
        (cohens_kappa, [(True,)]),
        (cohens_kappa, [(True, 1)]),
        (linear_weighted_kappa, [(0,)]),
        (linear_weighted_kappa, [(0, 5)]),
    ],
)
def test_kappa_rejects_mismatched_pairs_and_unknown_categories(function, pairs):
    with pytest.raises(ValueError):
        function(pairs)


@pytest.mark.parametrize(
    "scores",
    [
        scores_for_agreement(
            [(True, True)] * 7 + [(False, True)] * 3,
            [(4, 4)] * 10,
        ),
        scores_for_agreement(
            [(True, True)] * 8 + [(True, False)] + [(False, True)],
            [(4, 4)] * 10,
        ),
        scores_for_agreement(
            [(True, True), (False, False)] * 5,
            [(0, 0)] * 3
            + [(4, 4)] * 4
            + [(0, 4), (4, 0), (0, 4)],
        ),
    ],
)
def test_agreement_status_stops_before_unlock_for_each_threshold(scores):
    result = blinded_agreement_status(scores)

    assert result["status"] == "recalibrate-and-rescore-before-unlock"


def test_null_kappa_does_not_fail_when_raw_agreement_passes():
    result = blinded_agreement_status(
        scores_for_agreement([(True, True)] * 8, [(4, 4)] * 8)
    )

    assert result["binary_kappa"] is None
    assert result["ordinal_weighted_kappa"] is None
    assert result["status"] == "eligible-for-locked-unlock"


def test_agreement_status_is_eligible_only_when_all_applicable_thresholds_pass():
    result = blinded_agreement_status(
        scores_for_agreement(
            [(True, True), (False, False)] * 4,
            [(0, 0), (4, 4)] * 4,
        )
    )

    assert result["raw_binary_agreement"] == 1.0
    assert result["binary_kappa"] == 1.0
    assert result["ordinal_weighted_kappa"] == 1.0
    assert result["status"] == "eligible-for-locked-unlock"


@pytest.mark.parametrize(
    ("mandatory", "met", "applicable", "critical", "expected"),
    [
        (True, 4, 5, False, True),
        (True, 3, 5, False, True),
        (True, 0, 0, False, True),
        (False, 5, 5, False, False),
        (True, 5, 5, True, False),
    ],
)
def test_task_success_uses_only_mandatory_completion_and_no_critical_violation(
    mandatory, met, applicable, critical, expected
):
    observation = completed_observation(
        mandatory_complete=mandatory,
        quality_met=met,
        quality_applicable=applicable,
        critical_violation=critical,
    )
    assert task_success(observation) is expected


def test_abandonment_is_failure_and_technical_failure_is_missing():
    assert task_success(status_observation("abandoned")) is False
    assert task_success(status_observation("technical_failure")) is None


def test_task_success_accepts_zero_applicable_quality_as_not_estimable():
    assert task_success(
        completed_observation(quality_met=0, quality_applicable=0)
    ) is True


def test_participant_effect_is_skill_minus_control():
    observations = unlocked_complete_pilot(
        intervention_successes={"B01": 2},
        control_successes={"B01": 1},
    )
    assert participant_paired_differences(observations)["B01"] == 0.5


def test_participant_effect_requires_exactly_two_tasks_per_condition():
    observations = unlocked_complete_pilot()
    observations.pop()

    with pytest.raises(ValueError, match="two observations per condition"):
        participant_paired_differences(observations)


def test_participant_effect_excludes_any_technical_failure_but_not_abandonment():
    observations = unlocked_complete_pilot()
    technical_row = next(
        row for row in observations if row["participant_code"] == "B01"
    )
    abandoned_row = next(
        row for row in observations if row["participant_code"] == "B02"
    )
    mark_unscored(technical_row, "technical_failure")
    mark_unscored(abandoned_row, "abandoned")

    differences = participant_paired_differences(observations)

    assert "B01" not in differences
    assert "B02" in differences


def test_bootstrap_mean_interval_is_constant_for_constant_values():
    assert bootstrap_mean_interval([0.5] * 8, seed=20260809, resamples=1000) == (
        0.5,
        0.5,
    )


def test_bootstrap_mean_interval_repeats_for_same_seed_and_resamples():
    values = [-1.0, -0.5, 0.0, 0.5, 1.0]

    first = bootstrap_mean_interval(values, seed=73, resamples=1000)
    second = bootstrap_mean_interval(values, seed=73, resamples=1000)

    assert first == second
    assert first[0] < 0 < first[1]


@pytest.mark.parametrize(
    ("values", "seed", "resamples", "confidence"),
    [
        ([], 1, 1000, 0.95),
        ([float("nan")], 1, 1000, 0.95),
        ([True], 1, 1000, 0.95),
        ([0.0], True, 1000, 0.95),
        ([0.0], 1, 999, 0.95),
        ([0.0], 1, 1000, float("inf")),
    ],
)
def test_bootstrap_rejects_empty_non_finite_bool_and_out_of_range_inputs(
    values, seed, resamples, confidence
):
    with pytest.raises(ValueError):
        bootstrap_mean_interval(values, seed, resamples, confidence)


@pytest.mark.parametrize(
    ("successes", "total", "expected"),
    [
        (0, 10, (0.0, 0.308497)),
        (5, 10, (0.187086, 0.812914)),
        (10, 10, (0.691503, 1.0)),
    ],
)
def test_clopper_pearson_reference_values(successes, total, expected):
    actual = clopper_pearson(successes, total)
    assert actual == pytest.approx(expected, abs=1e-5)


def test_clopper_pearson_large_central_interval_is_finite_and_symmetric():
    lower, upper = clopper_pearson(1000, 2000)

    assert all(map(math.isfinite, (lower, upper)))
    assert 0.0 < lower < 0.5 < upper < 1.0
    assert lower == pytest.approx(1.0 - upper, abs=1e-12)


def test_clopper_pearson_large_tail_intervals_have_complement_symmetry():
    low_successes = clopper_pearson(1, 2000)
    high_successes = clopper_pearson(1999, 2000)

    assert all(map(math.isfinite, (*low_successes, *high_successes)))
    assert 0.0 < low_successes[0] < low_successes[1] < 0.01
    assert 0.99 < high_successes[0] < high_successes[1] < 1.0
    assert low_successes[0] == pytest.approx(1.0 - high_successes[1], abs=1e-12)
    assert low_successes[1] == pytest.approx(1.0 - high_successes[0], abs=1e-12)


@pytest.mark.parametrize(
    ("successes", "total", "confidence"),
    [
        (-1, 10, 0.95),
        (11, 10, 0.95),
        (0, 0, 0.95),
        (True, 10, 0.95),
        (1, True, 0.95),
        (1, 10, float("nan")),
        (1, 10, 1.0),
    ],
)
def test_clopper_pearson_rejects_invalid_or_bool_inputs(
    successes, total, confidence
):
    with pytest.raises(ValueError):
        clopper_pearson(successes, total, confidence)


def test_paired_metric_uses_participant_means_intervention_minus_control():
    observations = unlocked_complete_pilot()
    for row in observations:
        row["completion_seconds"] = 300
        if row["participant_code"] == "B01" and row["condition"] == "intervention":
            row["completion_seconds"] = 180

    result = aggregate_paired_metric(observations, "completion_seconds")

    assert result["complete_pairs"] == 16
    assert result["mean_difference"] == pytest.approx(-7.5)
    assert result["median_difference"] == 0.0
    assert len(result["confidence_interval"]) == 2


def test_paired_metric_excludes_participant_with_missing_scale_values():
    observations = unlocked_complete_pilot()
    mark_unscored(observations[0], "technical_failure")

    assert aggregate_paired_metric(observations, "nasa_tlx_points")[
        "complete_pairs"
    ] == 15


def test_criterion_results_preserve_rubric_order_and_condition_denominators():
    manifest, scores, lock, key, raw_scores = full_pilot_payloads()
    observations = unlock_observations(manifest, scores, lock, key, raw_scores)
    first_control = next(row for row in observations if row["condition"] == "control")
    first_control["criterion_scores"][0]["met"] = False
    first_control["mandatory_complete"] = False

    results = aggregate_criterion_results(scores, observations)
    _, rubric = load_effectiveness_contract(
        ROOT / "evals/effectiveness/offline-tasks.yaml",
        ROOT / "evals/effectiveness/rubric.yaml",
    )

    assert [row["criterion_id"] for row in results] == [
        criterion["id"] for criterion in rubric["criteria"]
    ]
    first = results[0]
    assert set(first) == {
        "criterion_id",
        "control_met",
        "control_applicable",
        "control_rate",
        "intervention_met",
        "intervention_applicable",
        "intervention_rate",
    }
    assert first["control_applicable"] == 32
    assert first["control_met"] == 31
    assert first["intervention_applicable"] == 32
    assert first["intervention_met"] == 32


def test_summary_has_fixed_aggregate_contract_and_paired_denominators():
    manifest, scores, lock, key, raw_scores = full_pilot_payloads()
    observations = unlock_observations(manifest, scores, lock, key, raw_scores)

    summary = summarize_effectiveness(manifest, scores, observations)

    assert set(summary) == {
        "schema_version",
        "study_id",
        "synthetic_example",
        "protocol_commit",
        "environment",
        "minimum_practical_difference",
        "participant_flow",
        "primary",
        "safety",
        "secondary",
        "agreement",
        "power_scenarios",
        "protocol_deviations",
        "limitations",
    }
    assert set(summary["environment"]) == {
        "skill_version",
        "skill_commit",
        "codex_surface",
        "model",
        "reasoning_effort",
        "service_tier",
        "python_version",
        "platform",
        "study_started_at",
        "study_ended_at",
        "task_commitment_sha256",
        "task_commitment_verified",
        "assignment_version",
        "bootstrap_seed",
        "bootstrap_resamples",
    }
    assert summary["study_id"] == "synthetic-pilot-v1"
    assert summary["synthetic_example"] is False
    assert summary["minimum_practical_difference"] == 0.20
    assert summary["participant_flow"] == {
        "assigned": 16,
        "completed": 16,
        "beginners": 8,
        "professionals": 8,
        "abandonments": 0,
        "timeouts": 0,
        "technical_failures": 0,
        "primary_complete_pairs": 16,
        "interpretation_status": "eligible-for-exploratory-interpretation",
    }
    expected_primary_keys = {
        "control_successes",
        "control_total",
        "control_success_rate",
        "intervention_successes",
        "intervention_total",
        "intervention_success_rate",
        "paired_risk_difference",
        "confidence_interval",
        "complete_pairs",
        "paired_distribution",
    }
    assert set(summary["primary"]) == {
        "overall",
        "beginner",
        "professional",
        "conservative_missingness",
    }
    assert all(
        set(result) == expected_primary_keys for result in summary["primary"].values()
    )
    overall = summary["primary"]["overall"]
    assert overall == {
        "control_successes": 32,
        "control_total": 32,
        "control_success_rate": 1.0,
        "intervention_successes": 32,
        "intervention_total": 32,
        "intervention_success_rate": 1.0,
        "paired_risk_difference": 0.0,
        "confidence_interval": [0.0, 0.0],
        "complete_pairs": 16,
        "paired_distribution": {
            "minus_one": 0,
            "minus_half": 0,
            "zero": 16,
            "plus_half": 0,
            "plus_one": 0,
        },
    }
    assert summary["primary"]["beginner"]["control_total"] == 16
    assert summary["primary"]["professional"]["control_total"] == 16
    assert summary["safety"]["control"] == {
        "events": 0,
        "total": 32,
        "rate": 0.0,
        "exact_interval": pytest.approx([0.0, 0.108881], abs=1e-5),
    }
    assert set(summary["secondary"]) == {
        "paired_time_seconds",
        "paired_quality_points",
        "paired_nasa_tlx_points",
        "paired_confidence_change",
        "paired_understanding_change",
        "intervention_sus",
        "timeout_rate",
        "technical_failure_rate",
        "criterion_results",
    }
    for field in (
        "paired_time_seconds",
        "paired_quality_points",
        "paired_nasa_tlx_points",
        "paired_confidence_change",
        "paired_understanding_change",
    ):
        assert set(summary["secondary"][field]) == {
            "complete_pairs",
            "mean_difference",
            "median_difference",
            "confidence_interval",
        }
        assert summary["secondary"][field]["complete_pairs"] == 16
        assert summary["secondary"][field]["mean_difference"] == 0.0
    assert summary["secondary"]["intervention_sus"] == {
        "participants": 16,
        "mean": 75.0,
        "median": 75.0,
    }
    assert summary["secondary"]["timeout_rate"] == {
        "events": 0,
        "assigned_tasks": 64,
        "rate": 0.0,
    }
    assert summary["secondary"]["technical_failure_rate"] == {
        "events": 0,
        "assigned_tasks": 64,
        "rate": 0.0,
    }
    assert len(summary["secondary"]["criterion_results"]) == 12
    assert set(summary["agreement"]) == {
        "answers_rated",
        "raw_binary_agreement",
        "binary_kappa",
        "raw_ordinal_agreement",
        "ordinal_weighted_kappa",
        "critical_disagreements",
        "adjudications",
        "status",
    }
    assert summary["agreement"] == {
        "answers_rated": 64,
        "raw_binary_agreement": 1.0,
        "binary_kappa": None,
        "raw_ordinal_agreement": 1.0,
        "ordinal_weighted_kappa": None,
        "critical_disagreements": 0,
        "adjudications": 0,
        "status": "eligible-for-locked-unlock",
    }
    assert len(summary["power_scenarios"]) == 3
    for scenario, control_rate in zip(
        summary["power_scenarios"], (0.30, 0.50, 0.70), strict=True
    ):
        assert set(scenario) == {
            "scenario_id",
            "minimum_difference",
            "control_rate",
            "paired_discordance",
            "attrition_rate",
            "two_sided_alpha",
            "target_power",
            "analysis_method",
            "required_complete_pairs",
            "required_recruits",
            "status",
        }
        assert scenario["control_rate"] == control_rate
        assert scenario["minimum_difference"] == 0.20
        assert scenario["required_complete_pairs"] is None
        assert scenario["required_recruits"] is None
        assert scenario["status"] == "deferred-until-post-pilot"
    assert summary["protocol_deviations"] == []
    assert summary["limitations"]


def test_summary_excludes_technical_failure_and_adds_conservative_sensitivity():
    manifest, scores, lock, key, raw_scores = full_pilot_payloads()
    observations = unlock_observations(manifest, scores, lock, key, raw_scores)
    technical_row = next(
        row
        for row in observations
        if row["participant_code"] == "B01"
        and row["condition"] == "intervention"
    )
    mark_unscored(technical_row, "technical_failure")

    summary = summarize_effectiveness(manifest, scores, observations)

    assert summary["participant_flow"]["primary_complete_pairs"] == 15
    assert summary["primary"]["overall"]["complete_pairs"] == 15
    assert summary["primary"]["overall"]["control_total"] == 30
    assert summary["primary"]["overall"]["intervention_total"] == 30
    sensitivity = summary["primary"]["conservative_missingness"]
    assert sensitivity["complete_pairs"] == 16
    assert sensitivity["control_successes"] == 32
    assert sensitivity["control_total"] == 32
    assert sensitivity["intervention_successes"] == 31
    assert sensitivity["intervention_total"] == 32
    assert sensitivity["paired_risk_difference"] == -0.03125
    assert sensitivity["paired_distribution"] == {
        "minus_one": 0,
        "minus_half": 1,
        "zero": 15,
        "plus_half": 0,
        "plus_one": 0,
    }


@pytest.mark.parametrize(
    ("incomplete_participants", "expected_completed", "expected_status"),
    [
        (3, 13, "workflow-feasibility-only"),
        (2, 14, "eligible-for-exploratory-interpretation"),
    ],
)
def test_interpretation_stop_rule_uses_fourteen_of_sixteen_completed_participants(
    incomplete_participants, expected_completed, expected_status
):
    manifest, scores, lock, key, raw_scores = full_pilot_payloads()
    observations = unlock_observations(manifest, scores, lock, key, raw_scores)
    participant_codes = sorted({row["participant_code"] for row in observations})
    for row in observations:
        if row["participant_code"] in participant_codes[:incomplete_participants]:
            mark_unscored(row, "abandoned")

    summary = summarize_effectiveness(manifest, scores, observations)

    assert summary["participant_flow"]["completed"] == expected_completed
    assert summary["participant_flow"]["interpretation_status"] == expected_status
    assert summary["primary"]["overall"]["paired_risk_difference"] == 0.0


def test_summary_contains_no_row_identifiers_assignments_or_participant_differences():
    manifest, scores, lock, key, raw_scores = full_pilot_payloads()
    observations = unlock_observations(manifest, scores, lock, key, raw_scores)

    summary = summarize_effectiveness(manifest, scores, observations)
    serialized = json.dumps(summary, ensure_ascii=False, sort_keys=True)

    for forbidden_value in (
        observations[0]["participant_code"],
        observations[0]["answer_id"],
        observations[0]["task_pair_id"],
    ):
        assert forbidden_value not in serialized
    for forbidden_key in (
        "participant_code",
        "answer_id",
        "task_pair_id",
        "task_variant",
        "order",
        "participant_paired_differences",
    ):
        assert f'"{forbidden_key}"' not in serialized


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


@pytest.mark.parametrize(
    ("mutate", "marker"),
    [
        (
            lambda rows: rows.__setitem__(
                0, {**rows[0], "criterion_id": "not-in-rubric"}
            ),
            "criterion IDs must exactly match task contract order",
        ),
        (
            lambda rows: rows.__setitem__(1, copy.deepcopy(rows[0])),
            "criterion IDs must exactly match task contract order",
        ),
        (
            lambda rows: rows.reverse(),
            "criterion IDs must exactly match task contract order",
        ),
        (
            lambda rows: rows[0].update({"unexpected": True}),
            "keys must match the closed schema",
        ),
        (
            lambda rows: rows[0].update({"applicable": False}),
            "mandatory criterion must be applicable",
        ),
        (
            lambda rows: rows[-1].update({"applicable": False, "met": True}),
            "non-applicable quality criterion must have null met",
        ),
    ],
)
def test_criterion_scores_reject_unknown_duplicate_order_and_invalid_rows(
    mutate, marker
):
    scores = valid_scores()
    mutate(scores["observations"][0]["criterion_scores"])

    assert any(marker in error for error in validate_blinded_scores(scores))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("mandatory_complete", False),
        ("quality_applicable", 2),
        ("quality_met", 2),
    ],
)
def test_criterion_scores_must_match_aggregate_observation_fields(field, value):
    scores = valid_scores()
    scores["observations"][0][field] = value

    assert any(
        "criterion detail does not match aggregate fields" in error
        for error in validate_blinded_scores(scores)
    )


def test_quality_criterion_can_be_non_applicable_with_null_met():
    scores = valid_scores()
    observation = scores["observations"][0]
    observation["criterion_scores"][-1].update(
        {"applicable": False, "met": None}
    )
    observation["quality_applicable"] = 2
    observation["quality_met"] = 2

    assert validate_blinded_scores(scores) == []


def test_all_quality_criteria_na_are_valid_secondary_nulls_end_to_end():
    manifest, scores, _, key, _ = full_pilot_payloads()
    _, rubric = load_effectiveness_contract(
        ROOT / "evals/effectiveness/offline-tasks.yaml",
        ROOT / "evals/effectiveness/rubric.yaml",
    )
    quality_ids = {
        criterion["id"]
        for criterion in rubric["criteria"]
        if criterion["kind"] == "quality"
    }
    for observation in scores["observations"]:
        for criterion in observation["criterion_scores"]:
            if criterion["criterion_id"] in quality_ids:
                criterion["applicable"] = False
                criterion["met"] = None
        observation["quality_applicable"] = 0
        observation["quality_met"] = 0

    raw_scores = score_bytes(scores)
    lock = valid_lock(raw_scores)
    assert validate_blinded_scores(scores) == []
    observations = unlock_observations(manifest, scores, lock, key, raw_scores)
    summary = summarize_effectiveness(manifest, scores, observations)

    assert summary["primary"]["overall"]["control_successes"] == 32
    assert summary["primary"]["overall"]["intervention_successes"] == 32
    quality_results = [
        row
        for row in summary["secondary"]["criterion_results"]
        if row["criterion_id"] in quality_ids
    ]
    assert quality_results
    assert all(
        row["control_met"] == 0
        and row["control_applicable"] == 0
        and row["control_rate"] is None
        and row["intervention_met"] == 0
        and row["intervention_applicable"] == 0
        and row["intervention_rate"] is None
        for row in quality_results
    )

    english = render_report(summary, "en")
    chinese = render_report(summary, "zh-TW")
    assert "not estimable" in english
    assert "無法估計" in chinese
    assert "Quality criteria are secondary and never determine primary task success" in english
    assert "品質準則屬於次要結果，絕不決定主要任務成功" in chinese


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
        "criterion_scores",
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


def test_unlocked_nested_lists_are_isolated_from_blinded_scores_in_both_directions():
    manifest, scores, lock, key, raw_scores = full_pilot_payloads()

    unlocked = unlock_observations(manifest, scores, lock, key, raw_scores)
    original_score_ratings = scores["observations"][0]["nasa_tlx_ratings"].copy()
    original_unlocked_weights = unlocked[0]["nasa_tlx_weights"].copy()
    original_score_criteria = copy.deepcopy(
        scores["observations"][0]["criterion_scores"]
    )
    unlocked[0]["nasa_tlx_ratings"][0] = 99
    unlocked[0]["criterion_scores"][0]["met"] = False
    changed_unlocked_criteria = copy.deepcopy(unlocked[0]["criterion_scores"])
    assert scores["observations"][0]["nasa_tlx_ratings"] == original_score_ratings
    assert scores["observations"][0]["criterion_scores"] == original_score_criteria

    scores["observations"][0]["nasa_tlx_weights"][0] = 5
    scores["observations"][0]["criterion_scores"][0]["met"] = False

    assert unlocked[0]["nasa_tlx_weights"] == original_unlocked_weights
    assert unlocked[0]["criterion_scores"] == changed_unlocked_criteria


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


def _agreement_cli_args(paths):
    return [
        sys.executable,
        str(ROOT / "scripts/analyze_effectiveness.py"),
        "agreement-check",
        "--study-manifest",
        str(paths["manifest"]),
        "--scores",
        str(paths["scores"]),
        "--ratings-lock",
        str(paths["lock"]),
        "--output-summary",
        str(paths["summary"]),
    ]


def _make_cli_scores_recalibration_required(paths):
    scores = json.loads(paths["scores"].read_text(encoding="utf-8"))
    answer_ids = [row["answer_id"] for row in scores["observations"][:13]]
    r2_by_answer = {
        row["answer_id"]: row
        for row in scores["rater_scores"]
        if row["rater_code"] == "R2"
    }
    for answer_id in answer_ids:
        r2_by_answer[answer_id]["success"] = False
        scores["adjudications"].append(
            {
                "answer_id": answer_id,
                "adjudicator_code": "R3",
                "final_success": True,
                "final_critical_violation": False,
                "final_ordinal_quality": 4,
                "rationale_code": "mandatory-criterion",
            }
        )
    raw_scores = score_bytes(scores)
    paths["scores"].write_bytes(raw_scores)
    paths["lock"].write_text(
        json.dumps(valid_lock(raw_scores), sort_keys=True), encoding="utf-8"
    )


def test_agreement_check_writes_only_blinded_aggregate_and_accepts_no_condition_key(
    tmp_path,
):
    paths = _write_cli_inputs(tmp_path)

    result = subprocess.run(
        _agreement_cli_args(paths), capture_output=True, text=True, check=False
    )

    assert result.returncode == 0
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    assert set(summary) == {"schema_version", "study_id", "agreement"}
    assert summary["agreement"]["status"] == "eligible-for-locked-unlock"
    assert "condition" not in json.dumps(summary, sort_keys=True)

    paths["summary"].unlink()
    rejected = subprocess.run(
        [*_agreement_cli_args(paths), "--condition-key", str(paths["key"])],
        capture_output=True,
        text=True,
        check=False,
    )
    assert rejected.returncode == 2
    assert rejected.stderr == CLI_ERROR
    assert not paths["summary"].exists()


def test_agreement_check_exits_three_after_writing_recalibration_status(tmp_path):
    paths = _write_cli_inputs(tmp_path)
    _make_cli_scores_recalibration_required(paths)

    result = subprocess.run(
        _agreement_cli_args(paths), capture_output=True, text=True, check=False
    )

    assert result.returncode == 3
    assert result.stdout == ""
    assert result.stderr == ""
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    assert (
        summary["agreement"]["status"]
        == "recalibrate-and-rescore-before-unlock"
    )


def test_analyze_refuses_unlock_when_blinded_agreement_is_not_eligible(tmp_path):
    paths = _write_cli_inputs(tmp_path)
    _make_cli_scores_recalibration_required(paths)

    result = subprocess.run(
        [*_cli_args(paths), "--unlock-after-ratings-lock"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
    assert not paths["summary"].exists()


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


@pytest.mark.parametrize(
    "unlock_prefix",
    (
        "--unlock",
        "--unlock-after",
        "--unlock-after-ratings",
        "--unlock-after-ratings-loc",
    ),
)
def test_cli_rejects_abbreviated_unlock_flags_content_free(tmp_path, unlock_prefix):
    paths = _write_cli_inputs(tmp_path)

    result = subprocess.run(
        [*_cli_args(paths), unlock_prefix],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
    assert unlock_prefix not in result.stderr
    assert str(paths["summary"]) not in result.stderr
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


@pytest.mark.parametrize("aliased_input", ("manifest", "scores", "lock", "key"))
def test_cli_rejects_hardlink_output_alias_without_corrupting_input(
    tmp_path, aliased_input
):
    paths = _write_cli_inputs(tmp_path)
    original_bytes = paths[aliased_input].read_bytes()
    os.link(paths[aliased_input], paths["summary"])

    result = subprocess.run(
        [*_cli_args(paths), "--unlock-after-ratings-lock"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == CLI_ERROR
    assert str(paths[aliased_input]) not in result.stderr
    assert paths[aliased_input].read_bytes() == original_bytes
    assert paths["summary"].read_bytes() == original_bytes


def test_atomic_summary_failure_preserves_existing_output_and_cleans_temp_file(
    tmp_path, monkeypatch
):
    paths = _write_cli_inputs(tmp_path)
    original_summary = b"existing aggregate summary\n"
    paths["summary"].write_bytes(original_summary)
    args = analyze_module._argument_parser().parse_args(
        [*_cli_args(paths)[2:], "--unlock-after-ratings-lock"]
    )

    def fail_replace(source, destination):
        raise OSError("synthetic replace failure")

    monkeypatch.setattr(analyze_module.os, "replace", fail_replace)

    with pytest.raises(OSError, match="synthetic replace failure"):
        analyze_module._analyze(args)

    assert paths["summary"].read_bytes() == original_summary
    assert list(tmp_path.glob(".summary.json.*.tmp")) == []


def test_cli_replaces_existing_output_with_canonical_aggregate_summary(tmp_path):
    paths = _write_cli_inputs(tmp_path)
    paths["summary"].write_bytes(b"stale aggregate summary\n")

    result = subprocess.run(
        [*_cli_args(paths), "--unlock-after-ratings-lock"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
    summary_bytes = paths["summary"].read_bytes()
    summary = json.loads(summary_bytes)
    assert summary_bytes == (
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    assert summary["schema_version"] == "1"
    assert summary["study_id"] == "synthetic-pilot-v1"
    assert summary["participant_flow"]["assigned"] == 16
    assert summary["primary"]["overall"]["control_total"] == 32
    assert summary["primary"]["overall"]["intervention_total"] == 32
    serialized = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    for forbidden in (
        "A000000000000001",
        "B01",
        '"observations"',
        '"mappings"',
        '"sessions"',
        '"participant_code"',
        '"answer_id"',
        '"task_variant"',
        '"order"',
    ):
        assert forbidden not in serialized
