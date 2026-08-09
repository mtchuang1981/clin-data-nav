from collections import Counter
from pathlib import Path

import pytest
import yaml

from scripts.effectiveness_contract import (
    load_effectiveness_contract,
    task_variants,
    validate_effectiveness_contract,
)


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "evals/effectiveness/offline-tasks.yaml"
RUBRIC = ROOT / "evals/effectiveness/rubric.yaml"


def test_offline_bank_has_eight_pairs_two_per_depth_and_two_variants():
    catalog, rubric = load_effectiveness_contract(TASKS, RUBRIC)

    pairs = catalog["task_pairs"]
    assert len(pairs) == 8
    assert Counter(pair["output_depth"] for pair in pairs) == {
        "quick explanation": 2,
        "evidence navigation": 2,
        "research design": 2,
        "implementation specification": 2,
    }
    assert all(set(pair["variants"]) == {"A", "B"} for pair in pairs)
    assert len(task_variants(catalog)) == 16
    assert rubric["minimum_quality_fraction"] == 0.8


def test_variants_share_pair_level_difficulty_and_criteria():
    catalog, _ = load_effectiveness_contract(TASKS, RUBRIC)

    for pair in catalog["task_pairs"]:
        assert set(pair) == {
            "id",
            "output_depth",
            "expected_minutes",
            "difficulty",
            "mandatory_criteria",
            "quality_criteria",
            "variants",
        }
        assert pair["variants"]["A"]["prompt"] != pair["variants"]["B"]["prompt"]
        assert "synthetic" in pair["variants"]["A"]["prompt"].casefold()
        assert "synthetic" in pair["variants"]["B"]["prompt"].casefold()


def test_contract_rejects_unknown_criterion_and_extra_key():
    catalog = {
        "schema_version": "1",
        "task_pairs": [
            {
                "id": "quick-invalid",
                "output_depth": "quick explanation",
                "expected_minutes": 10,
                "difficulty": 1,
                "mandatory_criteria": ["not-defined"],
                "quality_criteria": [],
                "variants": {
                    "A": {"prompt": "Synthetic prompt A."},
                    "B": {"prompt": "Synthetic prompt B."},
                },
                "unexpected": True,
            }
        ],
    }
    rubric = {
        "schema_version": "1",
        "minimum_quality_fraction": 0.8,
        "criteria": [],
        "critical_violations": [],
    }

    errors = validate_effectiveness_contract(catalog, rubric)

    assert "pair quick-invalid: unexpected keys: unexpected" in errors
    assert "pair quick-invalid: unknown mandatory criterion: not-defined" in errors
