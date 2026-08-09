"""Validate ratings-locked, condition-blinded effectiveness study inputs."""

from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import date, datetime
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics

from scripts.effectiveness_contract import load_effectiveness_contract


ROOT = Path(__file__).resolve().parents[1]
STRATA = frozenset({"beginner", "professional"})
CONDITIONS = frozenset({"control", "intervention"})
COMPLETION_STATUSES = frozenset(
    {"completed", "timeout", "abandoned", "technical_failure"}
)
SCORED_STATUSES = frozenset({"completed", "timeout"})
UNSCORED_STATUSES = frozenset({"abandoned", "technical_failure"})
DEPTHS = frozenset(
    {
        "quick explanation",
        "evidence navigation",
        "research design",
        "implementation specification",
    }
)
RATIONALE_CODES = frozenset(
    {
        "critical-safety",
        "mandatory-criterion",
        "quality-threshold",
        "ordinal-quality",
        "other-prespecified",
    }
)

ENVIRONMENT_FIELDS = (
    "skill_version",
    "skill_commit",
    "codex_surface",
    "model",
    "reasoning_effort",
    "service_tier",
    "python_version",
    "platform",
)
MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "study_id",
        "protocol_commit",
        *ENVIRONMENT_FIELDS,
        "study_started_at",
        "study_ended_at",
        "task_commitment_sha256",
        "task_commitment_verified",
        "bootstrap_seed",
        "bootstrap_resamples",
        "sessions",
    }
)
SESSION_KEYS = frozenset(
    {
        "participant_code",
        "stratum",
        "assignment_version",
        "session_date",
        "environment_fingerprint",
    }
)
SCORES_KEYS = frozenset(
    {
        "schema_version",
        "study_id",
        "observations",
        "rater_scores",
        "adjudications",
        "sus_responses",
    }
)
OBSERVATION_KEYS = frozenset(
    {
        "answer_id",
        "participant_code",
        "stratum",
        "task_pair_id",
        "task_variant",
        "output_depth",
        "order",
        "started_at",
        "ended_at",
        "completion_status",
        "completion_seconds",
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
    }
)
RATER_SCORE_KEYS = frozenset(
    {
        "answer_id",
        "rater_code",
        "success",
        "critical_violation",
        "ordinal_quality",
    }
)
ADJUDICATION_KEYS = frozenset(
    {
        "answer_id",
        "adjudicator_code",
        "final_success",
        "final_critical_violation",
        "final_ordinal_quality",
        "rationale_code",
    }
)
SUS_RESPONSE_KEYS = frozenset({"participant_code", "items"})
CRITERION_SCORE_KEYS = frozenset({"criterion_id", "applicable", "met"})
RATINGS_LOCK_KEYS = frozenset(
    {
        "schema_version",
        "study_id",
        "scores_sha256",
        "ratings_complete",
        "rater_codes",
        "locked_at",
    }
)
CONDITION_KEY_KEYS = frozenset({"schema_version", "study_id", "mappings"})
CONDITION_MAPPING_KEYS = frozenset({"answer_id", "condition"})

LOWER_HEX_40 = re.compile(r"^[0-9a-f]{40}$")
LOWER_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
ANSWER_ID_PATTERN = re.compile(r"^[A-F0-9]{16}$")
RATER_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_-]{0,31}$")

_CATALOG, _RUBRIC = load_effectiveness_contract(
    ROOT / "evals/effectiveness/offline-tasks.yaml",
    ROOT / "evals/effectiveness/rubric.yaml",
)
TASK_DEPTHS = {
    pair["id"]: pair["output_depth"] for pair in _CATALOG["task_pairs"]
}
TASK_CRITERIA = {
    pair["id"]: (
        tuple(pair["mandatory_criteria"]),
        tuple(pair["quality_criteria"]),
    )
    for pair in _CATALOG["task_pairs"]
}
RUBRIC_ORDER = tuple(criterion["id"] for criterion in _RUBRIC["criteria"])


def score_nasa_tlx(ratings: list[int], weights: list[int]) -> float:
    """Score the standard six-dimension weighted NASA-TLX."""
    if (
        not isinstance(ratings, list)
        or len(ratings) != 6
        or any(type(value) is not int or not 0 <= value <= 100 for value in ratings)
    ):
        raise ValueError("NASA-TLX ratings must contain six integers from 0 through 100")
    if (
        not isinstance(weights, list)
        or len(weights) != 6
        or any(type(value) is not int or not 0 <= value <= 5 for value in weights)
        or sum(weights) != 15
    ):
        raise ValueError("NASA-TLX weights must contain six integers summing to 15")
    return sum(
        rating * weight for rating, weight in zip(ratings, weights, strict=True)
    ) / 15


def score_sus(items: list[int]) -> float:
    """Score ten SUS responses with the standard odd/even transformation."""
    if (
        not isinstance(items, list)
        or len(items) != 10
        or any(type(value) is not int or not 1 <= value <= 5 for value in items)
    ):
        raise ValueError("SUS items must contain ten integers from 1 through 5")
    contributions = [
        response - 1 if index % 2 else 5 - response
        for index, response in enumerate(items, start=1)
    ]
    return sum(contributions) * 2.5


def cohens_kappa(pairs: list[tuple[bool, bool]]) -> float | None:
    """Compute binary Cohen kappa, or null for zero expected disagreement."""
    validated = _validate_pairs(pairs, lambda value: type(value) is bool, "binary")
    total = len(validated)
    observed_agreement = sum(left == right for left, right in validated) / total
    left_positive = sum(left for left, _ in validated) / total
    right_positive = sum(right for _, right in validated) / total
    expected_agreement = (
        left_positive * right_positive
        + (1.0 - left_positive) * (1.0 - right_positive)
    )
    expected_disagreement = 1.0 - expected_agreement
    if math.isclose(expected_disagreement, 0.0, abs_tol=1e-15):
        return None
    return _bounded_kappa((observed_agreement - expected_agreement) / expected_disagreement)


def linear_weighted_kappa(
    pairs: list[tuple[int, int]],
    categories: tuple[int, ...] = (0, 1, 2, 3, 4),
) -> float | None:
    """Compute linearly weighted ordinal kappa from original paired ratings."""
    if (
        not isinstance(categories, tuple)
        or len(categories) < 2
        or any(type(value) is not int for value in categories)
        or len(set(categories)) != len(categories)
        or tuple(sorted(categories)) != categories
    ):
        raise ValueError("ordinal categories must be a unique increasing integer tuple")
    allowed = set(categories)
    validated = _validate_pairs(
        pairs, lambda value: type(value) is int and value in allowed, "ordinal"
    )
    total = len(validated)
    denominator = len(categories) - 1
    observed_disagreement = math.fsum(
        abs(left - right) / denominator for left, right in validated
    ) / total
    left_counts = Counter(left for left, _ in validated)
    right_counts = Counter(right for _, right in validated)
    expected_disagreement = math.fsum(
        (left_counts[left] / total)
        * (right_counts[right] / total)
        * (abs(left - right) / denominator)
        for left in categories
        for right in categories
    )
    if math.isclose(expected_disagreement, 0.0, abs_tol=1e-15):
        return None
    return _bounded_kappa(1.0 - observed_disagreement / expected_disagreement)


def blinded_agreement_status(scores: dict) -> dict:
    """Summarize original pre-adjudication ratings and apply the unlock gate."""
    if not isinstance(scores, dict):
        raise ValueError("blinded scores must be a mapping")
    rater_scores = scores.get("rater_scores")
    adjudications = scores.get("adjudications")
    if not isinstance(rater_scores, list) or not isinstance(adjudications, list):
        raise ValueError("blinded rating collections must be lists")

    by_answer: dict[str, list[dict]] = defaultdict(list)
    for rating in rater_scores:
        if not isinstance(rating, dict) or not isinstance(rating.get("answer_id"), str):
            raise ValueError("original rating row is invalid")
        by_answer[rating["answer_id"]].append(rating)
    if not by_answer:
        raise ValueError("agreement requires rated answers")

    binary_pairs: list[tuple[bool, bool]] = []
    ordinal_pairs: list[tuple[int, int]] = []
    critical_pairs: list[tuple[bool, bool]] = []
    for answer_id in sorted(by_answer):
        ratings = sorted(by_answer[answer_id], key=lambda row: str(row.get("rater_code")))
        if len(ratings) != 2:
            raise ValueError("agreement requires two original ratings per answer")
        binary_pairs.append((ratings[0].get("success"), ratings[1].get("success")))
        ordinal_pairs.append(
            (ratings[0].get("ordinal_quality"), ratings[1].get("ordinal_quality"))
        )
        critical_pairs.append(
            (
                ratings[0].get("critical_violation"),
                ratings[1].get("critical_violation"),
            )
        )

    binary_kappa = cohens_kappa(binary_pairs)
    ordinal_kappa = linear_weighted_kappa(ordinal_pairs)
    raw_binary = sum(left == right for left, right in binary_pairs) / len(binary_pairs)
    raw_ordinal = sum(left == right for left, right in ordinal_pairs) / len(ordinal_pairs)
    eligible = (
        raw_binary >= 0.80
        and (binary_kappa is None or binary_kappa >= 0.60)
        and (ordinal_kappa is None or ordinal_kappa >= 0.60)
    )
    return {
        "answers_rated": len(binary_pairs),
        "raw_binary_agreement": raw_binary,
        "binary_kappa": binary_kappa,
        "raw_ordinal_agreement": raw_ordinal,
        "ordinal_weighted_kappa": ordinal_kappa,
        "critical_disagreements": sum(left != right for left, right in critical_pairs),
        "adjudications": len(adjudications),
        "status": (
            "eligible-for-locked-unlock"
            if eligible
            else "recalibrate-and-rescore-before-unlock"
        ),
    }


def compute_environment_fingerprint(manifest: dict) -> str:
    """Hash only the fixed execution environment using canonical sorted JSON."""
    payload = {field: manifest.get(field) for field in ENVIRONMENT_FIELDS}
    canonical = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def task_success(observation: dict) -> bool | None:
    """Return safety-gated task success, preserving technical missingness."""
    if not isinstance(observation, dict):
        raise ValueError("observation must be a mapping")
    status = observation.get("completion_status")
    if status == "abandoned":
        return False
    if status == "technical_failure":
        return None
    if status not in SCORED_STATUSES:
        raise ValueError("completion_status is invalid")

    mandatory = observation.get("mandatory_complete")
    quality_met = observation.get("quality_met")
    quality_applicable = observation.get("quality_applicable")
    critical = observation.get("critical_violation")
    if type(mandatory) is not bool:
        raise ValueError("mandatory_complete must be boolean")
    if type(quality_met) is not int or quality_met < 0:
        raise ValueError("quality_met must be a non-negative integer")
    if type(quality_applicable) is not int or quality_applicable <= 0:
        raise ValueError("quality_applicable must be a positive integer")
    if quality_met > quality_applicable:
        raise ValueError("quality_met cannot exceed quality_applicable")
    if type(critical) is not bool:
        raise ValueError("critical_violation must be boolean")

    quality_fraction = quality_met / quality_applicable
    return mandatory and quality_fraction >= 0.8 and not critical


def participant_paired_differences(
    observations: list[dict],
) -> dict[str, float]:
    """Compute complete-case participant effects, intervention minus control."""
    grouped = _group_participant_observations(observations)
    differences: dict[str, float] = {}
    for participant_code, rows_by_condition in grouped.items():
        outcomes = [
            task_success(row)
            for rows in rows_by_condition.values()
            for row in rows
        ]
        if any(outcome is None for outcome in outcomes):
            continue
        control_rate = sum(
            task_success(row) is True for row in rows_by_condition["control"]
        ) / 2
        intervention_rate = sum(
            task_success(row) is True for row in rows_by_condition["intervention"]
        ) / 2
        differences[participant_code] = intervention_rate - control_rate
    return differences


def bootstrap_mean_interval(
    values: list[float],
    seed: int,
    resamples: int,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """Return a deterministic participant-resampling percentile interval."""
    if not isinstance(values, list) or not values:
        raise ValueError("bootstrap values must be a non-empty list")
    if any(not _is_finite_number(value) for value in values):
        raise ValueError("bootstrap values must be finite numbers")
    if type(seed) is not int:
        raise ValueError("bootstrap seed must be an integer")
    if type(resamples) is not int or not 1_000 <= resamples <= 100_000:
        raise ValueError("bootstrap resamples must be from 1000 through 100000")
    if not _valid_confidence(confidence):
        raise ValueError("confidence must be a finite number between zero and one")

    numeric_values = [float(value) for value in values]
    count = len(numeric_values)
    generator = random.Random(seed)
    means = [
        math.fsum(numeric_values[generator.randrange(count)] for _ in range(count))
        / count
        for _ in range(resamples)
    ]
    means.sort()
    alpha = 1.0 - float(confidence)
    return (
        _linear_percentile(means, alpha / 2.0),
        _linear_percentile(means, 1.0 - alpha / 2.0),
    )


def clopper_pearson(
    successes: int, total: int, confidence: float = 0.95
) -> tuple[float, float]:
    """Return a two-sided exact Clopper-Pearson binomial interval."""
    if type(successes) is not int or type(total) is not int:
        raise ValueError("successes and total must be integers")
    if total <= 0 or not 0 <= successes <= total:
        raise ValueError("successes and total are outside the allowed range")
    if not _valid_confidence(confidence):
        raise ValueError("confidence must be a finite number between zero and one")

    alpha_tail = (1.0 - float(confidence)) / 2.0
    lower = (
        0.0
        if successes == 0
        else _binomial_cdf_quantile(total, successes - 1, 1.0 - alpha_tail)
    )
    upper = (
        1.0
        if successes == total
        else _binomial_cdf_quantile(total, successes, alpha_tail)
    )
    return lower, upper


def aggregate_paired_metric(observations: list[dict], field: str) -> dict:
    """Aggregate participant-level intervention-minus-control differences."""
    return _aggregate_paired_metric(
        observations, field, seed=20260809, resamples=1_000
    )


def aggregate_criterion_results(scores: dict, observations: list[dict]) -> list[dict]:
    """Aggregate applicable criterion decisions in fixed rubric order."""
    if not isinstance(scores, dict):
        raise ValueError("scores must be a mapping")
    if not isinstance(observations, list) or not observations:
        raise ValueError("observations must be a non-empty list")
    counts = {
        criterion_id: {
            condition: {"met": 0, "applicable": 0}
            for condition in ("control", "intervention")
        }
        for criterion_id in RUBRIC_ORDER
    }
    for observation in observations:
        if not isinstance(observation, dict):
            raise ValueError("each observation must be a mapping")
        if observation.get("completion_status") not in SCORED_STATUSES:
            continue
        condition = observation.get("condition")
        if condition not in CONDITIONS:
            raise ValueError("condition is invalid")
        criterion_scores = observation.get("criterion_scores")
        if not isinstance(criterion_scores, list):
            raise ValueError("scored observation criterion_scores must be a list")
        for criterion_score in criterion_scores:
            if not isinstance(criterion_score, dict):
                raise ValueError("criterion score must be a mapping")
            criterion_id = criterion_score.get("criterion_id")
            if criterion_id not in counts:
                raise ValueError("criterion score ID is unknown")
            if criterion_score.get("applicable") is True:
                counts[criterion_id][condition]["applicable"] += 1
                if criterion_score.get("met") is True:
                    counts[criterion_id][condition]["met"] += 1

    results: list[dict] = []
    for criterion_id in RUBRIC_ORDER:
        control = counts[criterion_id]["control"]
        intervention = counts[criterion_id]["intervention"]
        if control["applicable"] == 0 or intervention["applicable"] == 0:
            raise ValueError("criterion aggregation requires both condition denominators")
        results.append(
            {
                "criterion_id": criterion_id,
                "control_met": control["met"],
                "control_applicable": control["applicable"],
                "control_rate": control["met"] / control["applicable"],
                "intervention_met": intervention["met"],
                "intervention_applicable": intervention["applicable"],
                "intervention_rate": (
                    intervention["met"] / intervention["applicable"]
                ),
            }
        )
    return results


def _aggregate_paired_metric(
    observations: list[dict],
    field: str,
    *,
    seed: int,
    resamples: int,
) -> dict:
    if field not in {
        "completion_seconds",
        "quality_score",
        "nasa_tlx_points",
        "confidence_change",
        "understanding_change",
    }:
        raise ValueError("paired metric field is unsupported")
    grouped = _group_participant_observations(observations)
    differences: list[float] = []
    for rows_by_condition in grouped.values():
        values_by_condition: dict[str, list[float]] = {}
        complete = True
        for condition, rows in rows_by_condition.items():
            values = [_paired_metric_value(row, field) for row in rows]
            if any(value is None for value in values):
                complete = False
                break
            values_by_condition[condition] = [
                float(value) for value in values if value is not None
            ]
        if not complete:
            continue
        differences.append(
            math.fsum(values_by_condition["intervention"]) / 2
            - math.fsum(values_by_condition["control"]) / 2
        )
    if not differences:
        raise ValueError("paired metric has no complete participant pairs")
    interval = bootstrap_mean_interval(differences, seed, resamples)
    return {
        "complete_pairs": len(differences),
        "mean_difference": math.fsum(differences) / len(differences),
        "median_difference": float(statistics.median(differences)),
        "confidence_interval": [interval[0], interval[1]],
    }


def _paired_metric_value(observation: dict, field: str) -> float | None:
    if observation.get("completion_status") not in SCORED_STATUSES:
        return None
    if field == "completion_seconds":
        value = observation.get("completion_seconds")
    elif field == "quality_score":
        value = observation.get("quality_score")
    elif field == "nasa_tlx_points":
        return score_nasa_tlx(
            observation.get("nasa_tlx_ratings"),
            observation.get("nasa_tlx_weights"),
        )
    elif field == "confidence_change":
        before = observation.get("confidence_before")
        after = observation.get("confidence_after")
        if type(before) is not int or type(after) is not int:
            return None
        value = after - before
    else:
        before = observation.get("understanding_before")
        after = observation.get("understanding_after")
        if type(before) is not int or type(after) is not int:
            return None
        value = after - before
    if not _is_finite_number(value):
        return None
    return float(value)


def summarize_effectiveness(
    manifest: dict, scores: dict, observations: list[dict]
) -> dict:
    """Build the fixed aggregate-only Task 6 effectiveness summary."""
    if not isinstance(manifest, dict) or not isinstance(scores, dict):
        raise ValueError("manifest and scores must be mappings")
    layout_errors = validate_pilot_layout(observations)
    if layout_errors:
        raise ValueError("invalid effectiveness summary layout")
    if manifest.get("study_id") != scores.get("study_id"):
        raise ValueError("effectiveness summary study_id mismatch")

    sessions = manifest.get("sessions")
    if not isinstance(sessions, list):
        raise ValueError("study sessions must be a list")
    assignment_versions = {
        session.get("assignment_version")
        for session in sessions
        if isinstance(session, dict)
        and isinstance(session.get("assignment_version"), str)
    }
    if len(assignment_versions) != 1:
        raise ValueError("study sessions must share one assignment version")

    grouped = _group_participant_observations(observations)
    complete_participants = sum(
        all(
            row.get("completion_status") in SCORED_STATUSES
            for rows in rows_by_condition.values()
            for row in rows
        )
        for rows_by_condition in grouped.values()
    )
    overall = _primary_summary(
        observations,
        manifest["bootstrap_seed"],
        manifest["bootstrap_resamples"],
    )
    beginner_rows = [
        row for row in observations if row.get("stratum") == "beginner"
    ]
    professional_rows = [
        row for row in observations if row.get("stratum") == "professional"
    ]
    conservative = _primary_summary(
        observations,
        manifest["bootstrap_seed"],
        manifest["bootstrap_resamples"],
        conservative_missingness=True,
    )

    environment = {
        field: manifest[field]
        for field in (
            *ENVIRONMENT_FIELDS,
            "study_started_at",
            "study_ended_at",
            "task_commitment_sha256",
            "task_commitment_verified",
        )
    }
    environment.update(
        {
            "assignment_version": next(iter(assignment_versions)),
            "bootstrap_seed": manifest["bootstrap_seed"],
            "bootstrap_resamples": manifest["bootstrap_resamples"],
        }
    )
    paired_metrics = {
        output_name: _aggregate_paired_metric(
            observations,
            field,
            seed=manifest["bootstrap_seed"],
            resamples=manifest["bootstrap_resamples"],
        )
        for output_name, field in (
            ("paired_time_seconds", "completion_seconds"),
            ("paired_quality_points", "quality_score"),
            ("paired_nasa_tlx_points", "nasa_tlx_points"),
            ("paired_confidence_change", "confidence_change"),
            ("paired_understanding_change", "understanding_change"),
        )
    }
    sus_responses = scores.get("sus_responses")
    if not isinstance(sus_responses, list) or not sus_responses:
        raise ValueError("effectiveness summary requires intervention SUS responses")
    sus_scores = [score_sus(response.get("items")) for response in sus_responses]
    assigned_tasks = len(observations)
    secondary = {
        **paired_metrics,
        "intervention_sus": {
            "participants": len(sus_scores),
            "mean": math.fsum(sus_scores) / len(sus_scores),
            "median": float(statistics.median(sus_scores)),
        },
        "timeout_rate": _event_rate(observations, "timeout"),
        "technical_failure_rate": _event_rate(observations, "technical_failure"),
        "criterion_results": aggregate_criterion_results(scores, observations),
    }
    if any(
        result["assigned_tasks"] != assigned_tasks
        for result in (
            secondary["timeout_rate"],
            secondary["technical_failure_rate"],
        )
    ):
        raise AssertionError("secondary task denominator mismatch")
    return {
        "schema_version": "1",
        "study_id": manifest["study_id"],
        "synthetic_example": False,
        "protocol_commit": manifest["protocol_commit"],
        "environment": environment,
        "minimum_practical_difference": 0.20,
        "participant_flow": {
            "assigned": len(sessions),
            "completed": complete_participants,
            "beginners": sum(
                session.get("stratum") == "beginner" for session in sessions
            ),
            "professionals": sum(
                session.get("stratum") == "professional" for session in sessions
            ),
            "abandonments": sum(
                row.get("completion_status") == "abandoned" for row in observations
            ),
            "timeouts": sum(
                row.get("completion_status") == "timeout" for row in observations
            ),
            "technical_failures": sum(
                row.get("completion_status") == "technical_failure"
                for row in observations
            ),
            "primary_complete_pairs": overall["complete_pairs"],
            "interpretation_status": (
                "eligible-for-exploratory-interpretation"
                if complete_participants >= 14
                else "workflow-feasibility-only"
            ),
        },
        "primary": {
            "overall": overall,
            "beginner": _primary_summary(
                beginner_rows,
                manifest["bootstrap_seed"],
                manifest["bootstrap_resamples"],
            ),
            "professional": _primary_summary(
                professional_rows,
                manifest["bootstrap_seed"],
                manifest["bootstrap_resamples"],
            ),
            "conservative_missingness": conservative,
        },
        "safety": {
            condition: _safety_summary(observations, condition)
            for condition in ("control", "intervention")
        },
        "secondary": secondary,
        "agreement": blinded_agreement_status(scores),
        "power_scenarios": _deferred_power_scenarios(),
        "protocol_deviations": [],
        "limitations": [
            "This 16-person pilot is exploratory and not confirmatory.",
            "Synthetic tasks and a controlled environment limit real-world generalizability.",
            "Product task performance does not prove clinical validity, causal validity, or patient-outcome validity.",
        ],
    }


def _event_rate(observations: list[dict], status: str) -> dict:
    events = sum(
        observation.get("completion_status") == status
        for observation in observations
        if isinstance(observation, dict)
    )
    assigned_tasks = len(observations)
    if assigned_tasks == 0:
        raise ValueError("event rate requires assigned tasks")
    return {
        "events": events,
        "assigned_tasks": assigned_tasks,
        "rate": events / assigned_tasks,
    }


def _deferred_power_scenarios() -> list[dict]:
    scenarios = (
        ("lower-control-rate", 0.30, 0.35, 0.15),
        ("mid-control-rate", 0.50, 0.50, 0.15),
        ("higher-control-rate", 0.70, 0.35, 0.15),
    )
    return [
        {
            "scenario_id": scenario_id,
            "minimum_difference": 0.20,
            "control_rate": control_rate,
            "paired_discordance": paired_discordance,
            "attrition_rate": attrition_rate,
            "two_sided_alpha": 0.05,
            "target_power": 0.80,
            "analysis_method": "paired-binary-or-participant-task-clustered-design",
            "required_complete_pairs": None,
            "required_recruits": None,
            "status": "deferred-until-post-pilot",
        }
        for scenario_id, control_rate, paired_discordance, attrition_rate in scenarios
    ]


def _group_participant_observations(
    observations: list[dict],
) -> dict[str, dict[str, list[dict]]]:
    if not isinstance(observations, list) or not observations:
        raise ValueError("observations must be a non-empty list")
    grouped: dict[str, dict[str, list[dict]]] = defaultdict(
        lambda: {"control": [], "intervention": []}
    )
    for observation in observations:
        if not isinstance(observation, dict):
            raise ValueError("each observation must be a mapping")
        participant_code = observation.get("participant_code")
        condition = observation.get("condition")
        if not isinstance(participant_code, str) or not participant_code:
            raise ValueError("participant_code is invalid")
        if condition not in CONDITIONS:
            raise ValueError("condition is invalid")
        grouped[participant_code][condition].append(observation)
    if any(
        len(rows) != 2
        for rows_by_condition in grouped.values()
        for rows in rows_by_condition.values()
    ):
        raise ValueError("each participant must have two observations per condition")
    return dict(grouped)


def _primary_summary(
    observations: list[dict],
    seed: int,
    resamples: int,
    conservative_missingness: bool = False,
) -> dict:
    grouped = _group_participant_observations(observations)
    differences: list[float] = []
    successes = {"control": 0, "intervention": 0}
    totals = {"control": 0, "intervention": 0}
    for rows_by_condition in grouped.values():
        outcomes_by_condition = {
            condition: [task_success(row) for row in rows]
            for condition, rows in rows_by_condition.items()
        }
        if not conservative_missingness and any(
            outcome is None
            for outcomes in outcomes_by_condition.values()
            for outcome in outcomes
        ):
            continue
        if conservative_missingness:
            outcomes_by_condition = {
                condition: [
                    outcome
                    if outcome is not None
                    else condition == "control"
                    for outcome in outcomes
                ]
                for condition, outcomes in outcomes_by_condition.items()
            }
        condition_rates: dict[str, float] = {}
        for condition in ("control", "intervention"):
            outcomes = outcomes_by_condition[condition]
            if any(type(outcome) is not bool for outcome in outcomes):
                raise ValueError("primary outcome remained missing")
            condition_successes = sum(outcome is True for outcome in outcomes)
            successes[condition] += condition_successes
            totals[condition] += len(outcomes)
            condition_rates[condition] = condition_successes / len(outcomes)
        differences.append(
            condition_rates["intervention"] - condition_rates["control"]
        )

    if not differences:
        raise ValueError("primary analysis has no complete participant pairs")
    interval = bootstrap_mean_interval(differences, seed, resamples)
    distribution_names = {
        -1.0: "minus_one",
        -0.5: "minus_half",
        0.0: "zero",
        0.5: "plus_half",
        1.0: "plus_one",
    }
    distribution = {name: 0 for name in distribution_names.values()}
    for difference in differences:
        if difference not in distribution_names:
            raise ValueError("paired difference is outside the fixed distribution")
        distribution[distribution_names[difference]] += 1
    return {
        "control_successes": successes["control"],
        "control_total": totals["control"],
        "control_success_rate": successes["control"] / totals["control"],
        "intervention_successes": successes["intervention"],
        "intervention_total": totals["intervention"],
        "intervention_success_rate": (
            successes["intervention"] / totals["intervention"]
        ),
        "paired_risk_difference": math.fsum(differences) / len(differences),
        "confidence_interval": [interval[0], interval[1]],
        "complete_pairs": len(differences),
        "paired_distribution": distribution,
    }


def _safety_summary(observations: list[dict], condition: str) -> dict:
    critical_flags = [
        observation.get("critical_violation")
        for observation in observations
        if observation.get("condition") == condition
        and type(observation.get("critical_violation")) is bool
    ]
    if not critical_flags:
        raise ValueError("safety analysis has no scored observations")
    events = sum(flag is True for flag in critical_flags)
    total = len(critical_flags)
    interval = clopper_pearson(events, total)
    return {
        "events": events,
        "total": total,
        "rate": events / total,
        "exact_interval": [interval[0], interval[1]],
    }


def _linear_percentile(sorted_values: list[float], probability: float) -> float:
    position = (len(sorted_values) - 1) * probability
    lower_index = math.floor(position)
    upper_index = math.ceil(position)
    if lower_index == upper_index:
        return sorted_values[lower_index]
    fraction = position - lower_index
    return (
        sorted_values[lower_index] * (1.0 - fraction)
        + sorted_values[upper_index] * fraction
    )


def _binomial_cdf_quantile(total: int, maximum_successes: int, target: float) -> float:
    lower = 0.0
    upper = 1.0
    for _ in range(100):
        midpoint = (lower + upper) / 2.0
        probability = _binomial_cdf(total, maximum_successes, midpoint)
        if probability > target:
            lower = midpoint
        else:
            upper = midpoint
    return (lower + upper) / 2.0


def _binomial_cdf(total: int, maximum_successes: int, probability: float) -> float:
    if probability <= 0.0:
        return 1.0
    if probability >= 1.0:
        return 1.0 if maximum_successes >= total else 0.0

    # Scale the modal PMF to one. Ratios moving away from a binomial mode are
    # at most one, so neither combinatorial coefficients nor huge terms arise.
    mode = min(total, math.floor((total + 1) * probability))
    relative_probabilities = [0.0] * (total + 1)
    relative_probabilities[mode] = 1.0

    relative_probability = 1.0
    inverse_odds = (1.0 - probability) / probability
    for successes in range(mode, 0, -1):
        relative_probability *= (
            successes / (total - successes + 1) * inverse_odds
        )
        relative_probabilities[successes - 1] = relative_probability

    relative_probability = 1.0
    odds = probability / (1.0 - probability)
    for successes in range(mode, total):
        relative_probability *= (
            (total - successes) / (successes + 1) * odds
        )
        relative_probabilities[successes + 1] = relative_probability

    denominator = math.fsum(relative_probabilities)
    numerator = math.fsum(relative_probabilities[: maximum_successes + 1])
    result = numerator / denominator
    if not math.isfinite(result):
        raise ArithmeticError("binomial CDF calculation is non-finite")
    rounding_tolerance = 16 * math.ulp(1.0)
    if result < -rounding_tolerance or result > 1.0 + rounding_tolerance:
        raise ArithmeticError("binomial CDF calculation is outside probability bounds")
    return min(1.0, max(0.0, result))


def _is_finite_number(value: object) -> bool:
    return type(value) in {int, float} and math.isfinite(value)


def _validate_pairs(pairs: object, predicate, label: str) -> list[tuple]:
    if not isinstance(pairs, list) or not pairs:
        raise ValueError(f"{label} agreement pairs must be a non-empty list")
    validated: list[tuple] = []
    for pair in pairs:
        if (
            not isinstance(pair, tuple)
            or len(pair) != 2
            or not predicate(pair[0])
            or not predicate(pair[1])
        ):
            raise ValueError(f"{label} agreement pair is invalid")
        validated.append(pair)
    return validated


def _bounded_kappa(value: float) -> float:
    if not math.isfinite(value):
        raise ArithmeticError("kappa calculation is non-finite")
    tolerance = 16 * math.ulp(1.0)
    if not -1.0 - tolerance <= value <= 1.0 + tolerance:
        raise ArithmeticError("kappa calculation is outside its bounds")
    return min(1.0, max(-1.0, value))


def _valid_confidence(value: object) -> bool:
    return _is_finite_number(value) and 0.0 < float(value) < 1.0


def validate_study_manifest(payload: object) -> list[str]:
    """Validate the closed study manifest and fixed 16-session contract."""
    if not isinstance(payload, dict):
        return ["study manifest: must be a mapping"]
    errors: list[str] = []
    _validate_exact_keys("study manifest", payload, MANIFEST_KEYS, errors)
    if payload.get("schema_version") != "1":
        errors.append('study manifest: schema_version must be "1"')
    if not _is_safe_string(payload.get("study_id")):
        errors.append("study manifest: study_id must be a non-empty safe string")

    if not _matches(payload.get("protocol_commit"), LOWER_HEX_40):
        errors.append("study manifest: protocol_commit must be lowercase hexadecimal")
    if not _matches(payload.get("skill_commit"), LOWER_HEX_40):
        errors.append("study manifest: skill_commit must be lowercase hexadecimal")
    if not _matches(payload.get("task_commitment_sha256"), LOWER_HEX_64):
        errors.append(
            "study manifest: task_commitment_sha256 must be lowercase hexadecimal"
        )
    if payload.get("task_commitment_verified") is not True:
        errors.append("study manifest: task commitment must be verified")

    for field in ENVIRONMENT_FIELDS:
        if not _is_safe_string(payload.get(field)):
            errors.append(f"study manifest: {field} must be a non-empty safe string")

    started_at = _aware_datetime(payload.get("study_started_at"))
    ended_at = _aware_datetime(payload.get("study_ended_at"))
    if started_at is None:
        errors.append("study manifest: study_started_at must be timezone-aware ISO 8601")
    if ended_at is None:
        errors.append("study manifest: study_ended_at must be timezone-aware ISO 8601")
    if started_at is not None and ended_at is not None and started_at >= ended_at:
        errors.append("study manifest: study timestamps must be chronological")

    if type(payload.get("bootstrap_seed")) is not int:
        errors.append("study manifest: bootstrap_seed must be an integer")
    resamples = payload.get("bootstrap_resamples")
    if type(resamples) is not int or not 1_000 <= resamples <= 100_000:
        errors.append(
            "study manifest: bootstrap_resamples must be from 1000 through 100000"
        )

    sessions = payload.get("sessions")
    if not isinstance(sessions, list):
        errors.append("study manifest: sessions must be a list")
        return errors
    if len(sessions) != 16:
        errors.append("study manifest: expected exactly 16 sessions")

    expected_fingerprint = compute_environment_fingerprint(payload)
    observed_codes: list[str] = []
    assignment_versions: set[str] = set()
    for index, session in enumerate(sessions):
        label = f"study session {index}"
        if not isinstance(session, dict):
            errors.append(f"{label}: must be a mapping")
            continue
        _validate_exact_keys(label, session, SESSION_KEYS, errors)
        participant_code = session.get("participant_code")
        expected_stratum = _stratum_for_code(participant_code)
        if expected_stratum is None:
            errors.append(f"{label}: participant_code is invalid")
        elif session.get("stratum") != expected_stratum:
            errors.append(f"{label}: stratum does not match participant_code")
        else:
            observed_codes.append(participant_code)

        assignment_version = session.get("assignment_version")
        if not _is_safe_string(assignment_version):
            errors.append(f"{label}: assignment_version must be a non-empty safe string")
        else:
            assignment_versions.add(assignment_version)

        session_date = _iso_date(session.get("session_date"))
        if session_date is None:
            errors.append(f"{label}: session_date must be an ISO 8601 date")
        elif (
            started_at is not None
            and ended_at is not None
            and not started_at.date() <= session_date <= ended_at.date()
        ):
            errors.append(f"{label}: session_date must be inside the study period")

        fingerprint = session.get("environment_fingerprint")
        if not _matches(fingerprint, LOWER_HEX_64):
            errors.append(f"{label}: environment_fingerprint is invalid")
        elif fingerprint != expected_fingerprint:
            errors.append(f"{label}: environment stop-rule mismatch")

    if len(observed_codes) != len(set(observed_codes)):
        errors.append("study manifest: duplicate session participant_code")
    if set(observed_codes) != _expected_participants():
        errors.append("study manifest: session participant set is incomplete or invalid")
    if len(assignment_versions) != 1:
        errors.append("study manifest: sessions must share one assignment_version")
    return errors


def validate_blinded_scores(payload: object) -> list[str]:
    """Validate score rows without requiring the fixed 64-row pilot layout."""
    if not isinstance(payload, dict):
        return ["blinded scores: must be a mapping"]
    errors: list[str] = []
    _validate_exact_keys("blinded scores", payload, SCORES_KEYS, errors)
    if payload.get("schema_version") != "1":
        errors.append('blinded scores: schema_version must be "1"')
    if not _is_safe_string(payload.get("study_id")):
        errors.append("blinded scores: study_id must be a non-empty safe string")

    observations = payload.get("observations")
    rater_scores = payload.get("rater_scores")
    adjudications = payload.get("adjudications")
    sus_responses = payload.get("sus_responses")
    for field, value in (
        ("observations", observations),
        ("rater_scores", rater_scores),
        ("adjudications", adjudications),
        ("sus_responses", sus_responses),
    ):
        if not isinstance(value, list):
            errors.append(f"blinded scores: {field} must be a list")

    if not isinstance(observations, list):
        observations = []
    if not isinstance(rater_scores, list):
        rater_scores = []
    if not isinstance(adjudications, list):
        adjudications = []
    if not isinstance(sus_responses, list):
        sus_responses = []

    observations_by_answer: dict[str, dict] = {}
    for index, observation in enumerate(observations):
        label = f"observation {index}"
        if not isinstance(observation, dict):
            errors.append(f"{label}: must be a mapping")
            continue
        _validate_observation(observation, label, errors)
        answer_id = observation.get("answer_id")
        if isinstance(answer_id, str):
            if answer_id in observations_by_answer:
                errors.append("blinded scores: duplicate answer_id")
            else:
                observations_by_answer[answer_id] = observation

    ratings_by_answer: dict[str, list[dict]] = defaultdict(list)
    seen_ratings: set[tuple[str, str]] = set()
    for index, rating in enumerate(rater_scores):
        label = f"rater score {index}"
        if not isinstance(rating, dict):
            errors.append(f"{label}: must be a mapping")
            continue
        _validate_rating(rating, label, errors)
        answer_id = rating.get("answer_id")
        rater_code = rating.get("rater_code")
        if isinstance(answer_id, str) and isinstance(rater_code, str):
            rating_identity = (answer_id, rater_code)
            if rating_identity in seen_ratings:
                errors.append("blinded scores: duplicate original rater row")
            seen_ratings.add(rating_identity)
            ratings_by_answer[answer_id].append(rating)
        if not isinstance(answer_id, str) or answer_id not in observations_by_answer:
            errors.append(f"{label}: answer_id has no observation")

    scored_observations = [
        observation
        for observation in observations_by_answer.values()
        if _is_enum_value(observation.get("completion_status"), SCORED_STATUSES)
    ]
    original_rater_codes = {
        rating.get("rater_code")
        for rating in rater_scores
        if isinstance(rating, dict) and isinstance(rating.get("rater_code"), str)
    }
    if scored_observations and len(original_rater_codes) != 2:
        errors.append("blinded scores: expected exactly two original raters")

    adjudication_by_answer: dict[str, dict] = {}
    for index, adjudication in enumerate(adjudications):
        label = f"adjudication {index}"
        if not isinstance(adjudication, dict):
            errors.append(f"{label}: must be a mapping")
            continue
        _validate_adjudication(adjudication, label, errors)
        answer_id = adjudication.get("answer_id")
        if isinstance(answer_id, str):
            if answer_id in adjudication_by_answer:
                errors.append("blinded scores: duplicate adjudication")
            else:
                adjudication_by_answer[answer_id] = adjudication
        if not isinstance(answer_id, str) or answer_id not in observations_by_answer:
            errors.append(f"{label}: answer_id has no observation")

    for answer_id, observation in observations_by_answer.items():
        ratings = ratings_by_answer.get(answer_id, [])
        adjudication = adjudication_by_answer.get(answer_id)
        status = observation.get("completion_status")
        if _is_enum_value(status, SCORED_STATUSES):
            _validate_original_ratings_and_adjudication(
                observation, ratings, adjudication, errors
            )
        elif _is_enum_value(status, UNSCORED_STATUSES):
            if ratings:
                errors.append("unscored observation: original rater rows are forbidden")
            if adjudication is not None:
                errors.append("unscored observation: adjudication is forbidden")

    participant_codes = {
        observation.get("participant_code")
        for observation in observations
        if isinstance(observation, dict)
        and isinstance(observation.get("participant_code"), str)
    }
    seen_sus_codes: set[str] = set()
    for index, response in enumerate(sus_responses):
        label = f"SUS response {index}"
        if not isinstance(response, dict):
            errors.append(f"{label}: must be a mapping")
            continue
        _validate_exact_keys(label, response, SUS_RESPONSE_KEYS, errors)
        participant_code = response.get("participant_code")
        if _stratum_for_code(participant_code) is None:
            errors.append(f"{label}: participant_code is invalid")
        elif participant_code in seen_sus_codes:
            errors.append("blinded scores: duplicate SUS participant_code")
        else:
            seen_sus_codes.add(participant_code)
        if (
            not isinstance(participant_code, str)
            or participant_code not in participant_codes
        ):
            errors.append(f"{label}: participant_code has no observation")
        _validate_integer_list(response.get("items"), 10, 1, 5, label, errors)
    return errors


def validate_pilot_layout(observations: list[dict]) -> list[str]:
    """Validate the fixed 16-person, 64-observation unlocked pilot layout."""
    if not isinstance(observations, list):
        return ["pilot layout: observations must be a list"]
    errors: list[str] = []
    if len(observations) != 64:
        errors.append("pilot layout: expected exactly 64 observations")
    by_person: dict[str, list[dict]] = defaultdict(list)
    answer_ids: list[str] = []
    for index, observation in enumerate(observations):
        if not isinstance(observation, dict):
            errors.append(f"pilot observation {index}: must be a mapping")
            continue
        participant_code = observation.get("participant_code")
        if isinstance(participant_code, str):
            by_person[participant_code].append(observation)
        answer_id = observation.get("answer_id")
        if isinstance(answer_id, str):
            answer_ids.append(answer_id)
    if len(answer_ids) != len(set(answer_ids)):
        errors.append("pilot layout: answer IDs must be unique")
    if set(by_person) != _expected_participants():
        errors.append("pilot layout: expected exactly 16 fixed participant codes")
    for participant_code in sorted(_expected_participants()):
        rows = by_person.get(participant_code, [])
        if len(rows) != 4:
            errors.append("pilot layout: each participant must have four observations")
            continue
        orders = [row.get("order") for row in rows]
        if any(type(order) is not int for order in orders) or Counter(orders) != Counter(
            {1: 1, 2: 1, 3: 1, 4: 1}
        ):
            errors.append("pilot layout: each participant must have orders 1 through 4")
        depths = [row.get("output_depth") for row in rows]
        if any(not isinstance(depth, str) for depth in depths) or Counter(
            depths
        ) != Counter({depth: 1 for depth in DEPTHS}):
            errors.append("pilot layout: each participant must have one task per depth")
        conditions = [row.get("condition") for row in rows]
        if any(not isinstance(condition, str) for condition in conditions) or Counter(
            conditions
        ) != Counter({"control": 2, "intervention": 2}):
            errors.append("pilot layout: each participant must have two tasks per condition")
    return errors


def validate_ratings_lock(lock: object, scores_bytes: bytes) -> list[str]:
    """Validate a completed ratings lock against the raw score-file bytes."""
    if not isinstance(lock, dict):
        return ["ratings lock: must be a mapping"]
    errors: list[str] = []
    _validate_exact_keys("ratings lock", lock, RATINGS_LOCK_KEYS, errors)
    if lock.get("schema_version") != "1":
        errors.append('ratings lock: schema_version must be "1"')
    if not _is_safe_string(lock.get("study_id")):
        errors.append("ratings lock: study_id must be a non-empty safe string")
    digest = lock.get("scores_sha256")
    if not _matches(digest, LOWER_HEX_64):
        errors.append("ratings lock: scores_sha256 must be lowercase hexadecimal")
    if not isinstance(scores_bytes, bytes):
        errors.append("ratings lock: score file must be raw bytes")
    elif isinstance(digest, str) and digest != hashlib.sha256(scores_bytes).hexdigest():
        errors.append("ratings lock: raw score-file SHA-256 mismatch")
    if lock.get("ratings_complete") is not True:
        errors.append("ratings lock: ratings_complete must be true")
    rater_codes = lock.get("rater_codes")
    if not isinstance(rater_codes, list) or len(rater_codes) != 2:
        errors.append("ratings lock: rater_codes must contain two original raters")
    elif (
        any(not _matches(code, RATER_CODE_PATTERN) for code in rater_codes)
        or len(set(rater_codes)) != 2
    ):
        errors.append("ratings lock: rater_codes must be distinct safe codes")
    if _aware_datetime(lock.get("locked_at")) is None:
        errors.append("ratings lock: locked_at must be timezone-aware ISO 8601")
    return errors


def validate_blinded_agreement_inputs(
    manifest: object,
    scores: object,
    lock: object,
    scores_bytes: bytes,
) -> list[str]:
    """Validate all condition-free inputs needed for the pre-unlock gate."""
    errors = validate_study_manifest(manifest)
    errors.extend(validate_blinded_scores(scores))
    errors.extend(validate_ratings_lock(lock, scores_bytes))
    study_ids = [
        value.get("study_id") if isinstance(value, dict) else None
        for value in (manifest, scores, lock)
    ]
    if any(not isinstance(study_id, str) for study_id in study_ids) or (
        len(set(study_ids)) != 1
        if all(isinstance(study_id, str) for study_id in study_ids)
        else True
    ):
        errors.append("effectiveness agreement: study_id mismatch")
    if _manifest_session_members(manifest) != _observation_members(scores):
        errors.append("effectiveness agreement: observation/session membership mismatch")
    locked_rater_codes = (
        {
            code
            for code in lock.get("rater_codes", [])
            if isinstance(code, str)
        }
        if isinstance(lock, dict) and isinstance(lock.get("rater_codes"), list)
        else set()
    )
    if locked_rater_codes != _score_rater_codes(scores):
        errors.append("effectiveness agreement: lock rater set mismatch")
    _validate_study_timing(manifest, scores, lock, errors)
    observations = scores.get("observations") if isinstance(scores, dict) else None
    errors.extend(_validate_blinded_pilot_layout(observations))
    return errors


def _validate_blinded_pilot_layout(observations: object) -> list[str]:
    if not isinstance(observations, list):
        return ["blinded pilot layout: observations must be a list"]
    errors: list[str] = []
    if len(observations) != 64:
        errors.append("blinded pilot layout: expected exactly 64 observations")
    by_person: dict[str, list[dict]] = defaultdict(list)
    for observation in observations:
        if isinstance(observation, dict) and isinstance(
            observation.get("participant_code"), str
        ):
            by_person[observation["participant_code"]].append(observation)
    if set(by_person) != _expected_participants():
        errors.append("blinded pilot layout: participant set is incomplete")
    for participant_code in sorted(_expected_participants()):
        rows = by_person.get(participant_code, [])
        if len(rows) != 4:
            errors.append("blinded pilot layout: each participant needs four observations")
            continue
        if Counter(row.get("order") for row in rows) != Counter({1: 1, 2: 1, 3: 1, 4: 1}):
            errors.append("blinded pilot layout: participant orders are invalid")
        if Counter(row.get("output_depth") for row in rows) != Counter(
            {depth: 1 for depth in DEPTHS}
        ):
            errors.append("blinded pilot layout: participant depths are invalid")
    return errors


def validate_condition_key(key: object, answer_ids: set[str]) -> list[str]:
    """Validate a closed condition key with an exact one-to-one answer mapping."""
    if not isinstance(key, dict):
        return ["condition key: must be a mapping"]
    errors: list[str] = []
    _validate_exact_keys("condition key", key, CONDITION_KEY_KEYS, errors)
    if key.get("schema_version") != "1":
        errors.append('condition key: schema_version must be "1"')
    if not _is_safe_string(key.get("study_id")):
        errors.append("condition key: study_id must be a non-empty safe string")
    mappings = key.get("mappings")
    if not isinstance(mappings, list):
        errors.append("condition key: mappings must be a list")
        return errors
    mapped_answer_ids: list[str] = []
    for index, mapping in enumerate(mappings):
        label = f"condition mapping {index}"
        if not isinstance(mapping, dict):
            errors.append(f"{label}: must be a mapping")
            continue
        _validate_exact_keys(label, mapping, CONDITION_MAPPING_KEYS, errors)
        answer_id = mapping.get("answer_id")
        if not _matches(answer_id, ANSWER_ID_PATTERN):
            errors.append(f"{label}: answer_id is invalid")
        else:
            mapped_answer_ids.append(answer_id)
        if not _is_enum_value(mapping.get("condition"), CONDITIONS):
            errors.append(f"{label}: condition is invalid")
    if len(mapped_answer_ids) != len(set(mapped_answer_ids)):
        errors.append("condition key: duplicate answer mapping")
    if set(mapped_answer_ids) != answer_ids:
        errors.append("condition key: answer mapping set must exactly match scores")
    return errors


def unlock_observations(
    manifest: dict,
    scores: dict,
    lock: dict,
    key: dict,
    scores_bytes: bytes,
) -> list[dict]:
    """Validate all four external inputs before merging the condition key."""
    errors = validate_study_manifest(manifest)
    errors.extend(validate_blinded_scores(scores))
    errors.extend(validate_ratings_lock(lock, scores_bytes))
    answer_ids = _score_answer_ids(scores)
    errors.extend(validate_condition_key(key, answer_ids))

    study_ids = [
        value.get("study_id") if isinstance(value, dict) else None
        for value in (manifest, scores, lock, key)
    ]
    if any(not isinstance(study_id, str) for study_id in study_ids) or (
        len(set(study_ids)) != 1
        if all(isinstance(study_id, str) for study_id in study_ids)
        else True
    ):
        errors.append("effectiveness study: study_id mismatch")

    session_members = _manifest_session_members(manifest)
    observation_members = _observation_members(scores)
    if session_members != observation_members:
        errors.append("effectiveness study: observation/session membership mismatch")

    locked_rater_codes = {
        code
        for code in lock.get("rater_codes", [])
        if isinstance(code, str)
    } if isinstance(lock, dict) and isinstance(lock.get("rater_codes"), list) else set()
    score_rater_codes = _score_rater_codes(scores)
    if locked_rater_codes != score_rater_codes:
        errors.append("effectiveness study: lock rater set mismatch")

    _validate_study_timing(manifest, scores, lock, errors)
    if errors:
        raise ValueError("invalid effectiveness study: " + "; ".join(errors))

    assert isinstance(scores, dict)
    assert isinstance(key, dict)
    condition_by_answer = {
        mapping["answer_id"]: mapping["condition"] for mapping in key["mappings"]
    }
    unlocked = [
        {
            **deepcopy(observation),
            "condition": condition_by_answer[observation["answer_id"]],
        }
        for observation in scores["observations"]
    ]
    layout_errors = validate_pilot_layout(unlocked)
    if layout_errors:
        raise ValueError(
            "invalid effectiveness study: " + "; ".join(layout_errors)
        )
    return unlocked


def _validate_observation(
    observation: dict, label: str, errors: list[str]
) -> None:
    _validate_exact_keys(label, observation, OBSERVATION_KEYS, errors)
    if not _matches(observation.get("answer_id"), ANSWER_ID_PATTERN):
        errors.append(f"{label}: answer_id is invalid")
    participant_code = observation.get("participant_code")
    expected_stratum = _stratum_for_code(participant_code)
    if expected_stratum is None:
        errors.append(f"{label}: participant_code is invalid")
    elif observation.get("stratum") != expected_stratum:
        errors.append(f"{label}: stratum does not match participant_code")

    task_pair_id = observation.get("task_pair_id")
    if not isinstance(task_pair_id, str) or task_pair_id not in TASK_DEPTHS:
        errors.append(f"{label}: task_pair_id is unknown")
    elif observation.get("output_depth") != TASK_DEPTHS[task_pair_id]:
        errors.append(f"{label}: output_depth does not match task_pair_id")
    if not _is_enum_value(observation.get("output_depth"), DEPTHS):
        errors.append(f"{label}: output_depth is invalid")
    if not _is_enum_value(observation.get("task_variant"), {"A", "B"}):
        errors.append(f"{label}: task_variant must be A or B")
    if type(observation.get("order")) is not int or observation.get("order") not in {
        1,
        2,
        3,
        4,
    }:
        errors.append(f"{label}: order must be an integer from 1 through 4")

    started_at = _aware_datetime(observation.get("started_at"))
    ended_at = _aware_datetime(observation.get("ended_at"))
    if started_at is None:
        errors.append(f"{label}: started_at must be timezone-aware ISO 8601")
    if ended_at is None:
        errors.append(f"{label}: ended_at must be timezone-aware ISO 8601")
    if started_at is not None and ended_at is not None and started_at > ended_at:
        errors.append(f"{label}: timestamps must be chronological")
    completion_seconds = observation.get("completion_seconds")
    if type(completion_seconds) is not int or completion_seconds < 0:
        errors.append(f"{label}: completion_seconds must be a non-negative integer")
    elif started_at is not None and ended_at is not None:
        elapsed = (ended_at - started_at).total_seconds()
        if elapsed != completion_seconds:
            errors.append(f"{label}: completion_seconds must equal timestamp duration")

    status = observation.get("completion_status")
    if not _is_enum_value(status, COMPLETION_STATUSES):
        errors.append(f"{label}: completion_status is invalid")
    elif status in SCORED_STATUSES:
        _validate_populated_observation_scores(observation, label, errors)
    else:
        for field in _nullable_observation_fields():
            if observation.get(field) is not None:
                errors.append(f"{label}: {field} must be null for an unscored status")


def _validate_populated_observation_scores(
    observation: dict, label: str, errors: list[str]
) -> None:
    if type(observation.get("mandatory_complete")) is not bool:
        errors.append(f"{label}: mandatory_complete must be boolean")
    quality_met = observation.get("quality_met")
    quality_applicable = observation.get("quality_applicable")
    if type(quality_met) is not int or quality_met < 0:
        errors.append(f"{label}: quality_met must be a non-negative integer")
    if type(quality_applicable) is not int or not 1 <= quality_applicable <= 100:
        errors.append(f"{label}: quality_applicable must be an integer from 1 through 100")
    if (
        type(quality_met) is int
        and type(quality_applicable) is int
        and quality_applicable >= 0
        and quality_met > quality_applicable
    ):
        errors.append(f"{label}: quality_met cannot exceed quality_applicable")
    quality_score = observation.get("quality_score")
    if type(quality_score) is not int or not 0 <= quality_score <= 100:
        errors.append(f"{label}: quality_score must be an integer from 0 through 100")
    if type(observation.get("critical_violation")) is not bool:
        errors.append(f"{label}: critical_violation must be boolean")
    _validate_criterion_scores(observation, label, errors)
    _validate_integer_list(
        observation.get("nasa_tlx_ratings"), 6, 0, 100, f"{label} TLX ratings", errors
    )
    weights = observation.get("nasa_tlx_weights")
    _validate_integer_list(weights, 6, 0, 5, f"{label} TLX weights", errors)
    if isinstance(weights, list) and all(type(value) is int for value in weights):
        if sum(weights) != 15:
            errors.append(f"{label}: NASA-TLX weights must sum to 15")
    for field in (
        "confidence_before",
        "confidence_after",
        "understanding_before",
        "understanding_after",
    ):
        value = observation.get(field)
        if type(value) is not int or not 1 <= value <= 5:
            errors.append(f"{label}: {field} must be an integer from 1 through 5")


def _validate_criterion_scores(
    observation: dict, label: str, errors: list[str]
) -> None:
    task_pair_id = observation.get("task_pair_id")
    contract = TASK_CRITERIA.get(task_pair_id) if isinstance(task_pair_id, str) else None
    criterion_scores = observation.get("criterion_scores")
    if not isinstance(criterion_scores, list):
        errors.append(f"{label}: criterion_scores must be a list")
        return
    if contract is None:
        return
    mandatory_ids, quality_ids = contract
    expected_ids = (*mandatory_ids, *quality_ids)
    observed_ids: list[object] = []
    by_id: dict[str, dict] = {}
    for index, criterion_score in enumerate(criterion_scores):
        row_label = f"{label} criterion score {index}"
        if not isinstance(criterion_score, dict):
            errors.append(f"{row_label}: must be a mapping")
            continue
        _validate_exact_keys(row_label, criterion_score, CRITERION_SCORE_KEYS, errors)
        criterion_id = criterion_score.get("criterion_id")
        observed_ids.append(criterion_id)
        if isinstance(criterion_id, str) and criterion_id not in by_id:
            by_id[criterion_id] = criterion_score
        applicable = criterion_score.get("applicable")
        met = criterion_score.get("met")
        if criterion_id in mandatory_ids:
            if applicable is not True:
                errors.append(f"{row_label}: mandatory criterion must be applicable")
            if type(met) is not bool:
                errors.append(f"{row_label}: mandatory criterion met must be boolean")
        elif criterion_id in quality_ids:
            if type(applicable) is not bool:
                errors.append(f"{row_label}: quality applicable must be boolean")
            elif applicable and type(met) is not bool:
                errors.append(
                    f"{row_label}: applicable quality criterion met must be boolean"
                )
            elif not applicable and met is not None:
                errors.append(
                    f"{row_label}: non-applicable quality criterion must have null met"
                )

    if tuple(observed_ids) != expected_ids:
        errors.append(
            f"{label}: criterion IDs must exactly match task contract order"
        )
        return
    mandatory_complete = all(by_id[item].get("met") is True for item in mandatory_ids)
    quality_applicable = sum(
        by_id[item].get("applicable") is True for item in quality_ids
    )
    quality_met = sum(
        by_id[item].get("applicable") is True and by_id[item].get("met") is True
        for item in quality_ids
    )
    if quality_applicable <= 0 or (
        observation.get("mandatory_complete") is not mandatory_complete
        or observation.get("quality_applicable") != quality_applicable
        or observation.get("quality_met") != quality_met
    ):
        errors.append(f"{label}: criterion detail does not match aggregate fields")


def _validate_rating(rating: dict, label: str, errors: list[str]) -> None:
    _validate_exact_keys(label, rating, RATER_SCORE_KEYS, errors)
    if not _matches(rating.get("answer_id"), ANSWER_ID_PATTERN):
        errors.append(f"{label}: answer_id is invalid")
    if not _matches(rating.get("rater_code"), RATER_CODE_PATTERN):
        errors.append(f"{label}: rater_code is invalid")
    if type(rating.get("success")) is not bool:
        errors.append(f"{label}: success must be boolean")
    if type(rating.get("critical_violation")) is not bool:
        errors.append(f"{label}: critical_violation must be boolean")
    ordinal_quality = rating.get("ordinal_quality")
    if type(ordinal_quality) is not int or not 0 <= ordinal_quality <= 4:
        errors.append(f"{label}: ordinal_quality must be an integer from 0 through 4")
    if rating.get("success") is True and rating.get("critical_violation") is True:
        errors.append(f"{label}: success is forbidden with a critical violation")


def _validate_adjudication(
    adjudication: dict, label: str, errors: list[str]
) -> None:
    _validate_exact_keys(label, adjudication, ADJUDICATION_KEYS, errors)
    if not _matches(adjudication.get("answer_id"), ANSWER_ID_PATTERN):
        errors.append(f"{label}: answer_id is invalid")
    if not _matches(adjudication.get("adjudicator_code"), RATER_CODE_PATTERN):
        errors.append(f"{label}: adjudicator_code is invalid")
    if type(adjudication.get("final_success")) is not bool:
        errors.append(f"{label}: final_success must be boolean")
    if type(adjudication.get("final_critical_violation")) is not bool:
        errors.append(f"{label}: final_critical_violation must be boolean")
    ordinal_quality = adjudication.get("final_ordinal_quality")
    if type(ordinal_quality) is not int or not 0 <= ordinal_quality <= 4:
        errors.append(
            f"{label}: final_ordinal_quality must be an integer from 0 through 4"
        )
    if not _is_enum_value(adjudication.get("rationale_code"), RATIONALE_CODES):
        errors.append(f"{label}: rationale_code is invalid")
    if (
        adjudication.get("final_success") is True
        and adjudication.get("final_critical_violation") is True
    ):
        errors.append(f"{label}: final success is forbidden with a critical violation")


def _validate_original_ratings_and_adjudication(
    observation: dict,
    ratings: list[dict],
    adjudication: dict | None,
    errors: list[str],
) -> None:
    if len(ratings) != 2 or len(
        {
            rating.get("rater_code")
            for rating in ratings
            if isinstance(rating, dict)
            and isinstance(rating.get("rater_code"), str)
        }
    ) != 2:
        errors.append("scored observation: expected two distinct original rater rows")
        return
    rating_decisions = [
        (
            rating.get("success"),
            rating.get("critical_violation"),
            rating.get("ordinal_quality"),
        )
        for rating in ratings
    ]
    disagreement = rating_decisions[0] != rating_decisions[1]
    if disagreement and adjudication is None:
        errors.append("scored observation: rater disagreement requires adjudication")
        return
    if not disagreement and adjudication is not None:
        errors.append("scored observation: agreement forbids adjudication")
        return

    if adjudication is not None:
        if adjudication.get("adjudicator_code") in {
            rating.get("rater_code") for rating in ratings
        }:
            errors.append("scored observation: adjudicator must be a third rater")
        final_success = adjudication.get("final_success")
        final_critical = adjudication.get("final_critical_violation")
    else:
        final_success = ratings[0].get("success")
        final_critical = ratings[0].get("critical_violation")

    derived_success = _derived_success(observation)
    if derived_success is not None and final_success != derived_success:
        errors.append("scored observation: final success does not match derived success")
    if (
        type(observation.get("critical_violation")) is bool
        and final_critical != observation.get("critical_violation")
    ):
        errors.append(
            "scored observation: final critical flag does not match observation"
        )


def _derived_success(observation: dict) -> bool | None:
    mandatory = observation.get("mandatory_complete")
    quality_met = observation.get("quality_met")
    quality_applicable = observation.get("quality_applicable")
    critical = observation.get("critical_violation")
    if (
        type(mandatory) is not bool
        or type(quality_met) is not int
        or type(quality_applicable) is not int
        or quality_applicable <= 0
        or type(critical) is not bool
    ):
        return None
    return mandatory and quality_met * 5 >= quality_applicable * 4 and not critical


def _validate_study_timing(
    manifest: object, scores: object, lock: object, errors: list[str]
) -> None:
    if not isinstance(manifest, dict):
        return
    study_start = _aware_datetime(manifest.get("study_started_at"))
    study_end = _aware_datetime(manifest.get("study_ended_at"))
    if study_start is not None and study_end is not None and isinstance(scores, dict):
        observations = scores.get("observations")
        if isinstance(observations, list):
            for index, observation in enumerate(observations):
                if not isinstance(observation, dict):
                    continue
                started_at = _aware_datetime(observation.get("started_at"))
                ended_at = _aware_datetime(observation.get("ended_at"))
                if started_at is not None and not study_start <= started_at <= study_end:
                    errors.append(
                        f"observation {index}: started_at must be inside the study period"
                    )
                if ended_at is not None and not study_start <= ended_at <= study_end:
                    errors.append(
                        f"observation {index}: ended_at must be inside the study period"
                    )
    if study_end is not None and isinstance(lock, dict):
        locked_at = _aware_datetime(lock.get("locked_at"))
        if locked_at is not None and locked_at < study_end:
            errors.append("ratings lock: locked_at must not precede study end")


def _score_answer_ids(scores: object) -> set[str]:
    if not isinstance(scores, dict) or not isinstance(scores.get("observations"), list):
        return set()
    return {
        observation["answer_id"]
        for observation in scores["observations"]
        if isinstance(observation, dict)
        and _matches(observation.get("answer_id"), ANSWER_ID_PATTERN)
    }


def _manifest_session_members(manifest: object) -> set[tuple[str, str]]:
    if not isinstance(manifest, dict) or not isinstance(manifest.get("sessions"), list):
        return set()
    return {
        (session["participant_code"], session["stratum"])
        for session in manifest["sessions"]
        if isinstance(session, dict)
        and isinstance(session.get("participant_code"), str)
        and isinstance(session.get("stratum"), str)
    }


def _observation_members(scores: object) -> set[tuple[str, str]]:
    if not isinstance(scores, dict) or not isinstance(scores.get("observations"), list):
        return set()
    return {
        (observation["participant_code"], observation["stratum"])
        for observation in scores["observations"]
        if isinstance(observation, dict)
        and isinstance(observation.get("participant_code"), str)
        and isinstance(observation.get("stratum"), str)
    }


def _score_rater_codes(scores: object) -> set[str]:
    if not isinstance(scores, dict) or not isinstance(scores.get("rater_scores"), list):
        return set()
    return {
        rating["rater_code"]
        for rating in scores["rater_scores"]
        if isinstance(rating, dict) and isinstance(rating.get("rater_code"), str)
    }


def _nullable_observation_fields() -> tuple[str, ...]:
    return (
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
    )


def _expected_participants() -> set[str]:
    return {
        *(f"B{index:02d}" for index in range(1, 9)),
        *(f"P{index:02d}" for index in range(1, 9)),
    }


def _stratum_for_code(participant_code: object) -> str | None:
    if not isinstance(participant_code, str):
        return None
    if re.fullmatch(r"B0[1-8]", participant_code):
        return "beginner"
    if re.fullmatch(r"P0[1-8]", participant_code):
        return "professional"
    return None


def _validate_exact_keys(
    label: str, value: dict, expected: frozenset[str], errors: list[str]
) -> None:
    if set(value) != expected:
        errors.append(f"{label}: keys must match the closed schema")


def _validate_integer_list(
    value: object,
    length: int,
    minimum: int,
    maximum: int,
    label: str,
    errors: list[str],
) -> None:
    if not isinstance(value, list) or len(value) != length:
        errors.append(f"{label}: must contain exactly {length} items")
        return
    if any(type(item) is not int or not minimum <= item <= maximum for item in value):
        errors.append(f"{label}: items must be integers in the allowed range")


def _is_safe_string(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and len(value) <= 200
        and "\n" not in value
        and "\r" not in value
    )


def _matches(value: object, pattern: re.Pattern[str]) -> bool:
    return isinstance(value, str) and pattern.fullmatch(value) is not None


def _is_enum_value(value: object, allowed: set[str] | frozenset[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _aware_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or "\n" in value or "\r" in value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _iso_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.isoformat() == value else None
