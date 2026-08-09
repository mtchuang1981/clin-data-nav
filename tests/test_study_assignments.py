import copy
from collections import Counter, defaultdict
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.effectiveness_contract import load_effectiveness_contract
from scripts.generate_study_assignments import generate_assignments, validate_assignments


ROOT = Path(__file__).resolve().parents[1]


def _rows():
    catalog, _ = load_effectiveness_contract(
        ROOT / "evals/effectiveness/offline-tasks.yaml",
        ROOT / "evals/effectiveness/rubric.yaml",
    )
    return catalog, generate_assignments(catalog, "pilot-v1", 20260809)


def test_assignment_has_sixteen_people_four_tasks_and_balanced_conditions():
    _, rows = _rows()
    by_person = defaultdict(list)
    for row in rows:
        by_person[row["participant_code"]].append(row)

    assert len(rows) == 64
    assert set(by_person) == {
        *(f"B{index:02d}" for index in range(1, 9)),
        *(f"P{index:02d}" for index in range(1, 9)),
    }
    for person_rows in by_person.values():
        assert len(person_rows) == 4
        assert Counter(row["condition"] for row in person_rows) == {
            "control": 2,
            "intervention": 2,
        }
        assert {row["output_depth"] for row in person_rows} == {
            "quick explanation",
            "evidence navigation",
            "research design",
            "implementation specification",
        }
        assert len({row["pair_id"] for row in person_rows}) == 4


def test_every_variant_is_balanced_by_condition_and_stratum():
    _, rows = _rows()
    counts = Counter(
        (row["stratum"], row["pair_id"], row["variant"], row["condition"])
        for row in rows
    )
    assert set(counts.values()) == {1}


def test_first_condition_and_depth_order_are_counterbalanced():
    _, rows = _rows()
    first = [row for row in rows if row["order"] == 1]
    for stratum in ("beginner", "professional"):
        stratum_first = [row for row in first if row["stratum"] == stratum]
        assert Counter(row["condition"] for row in stratum_first) == {
            "control": 4,
            "intervention": 4,
        }
        assert Counter(row["output_depth"] for row in stratum_first) == {
            "quick explanation": 2,
            "evidence navigation": 2,
            "research design": 2,
            "implementation specification": 2,
        }


def test_same_seed_is_stable_and_answer_ids_are_opaque_and_unique():
    catalog, rows = _rows()
    assert rows == generate_assignments(catalog, "pilot-v1", 20260809)
    assert len({row["answer_id"] for row in rows}) == 64
    assert all(len(row["answer_id"]) == 16 for row in rows)
    assert all(row["condition"] not in row["answer_id"].casefold() for row in rows)


def test_cli_rejects_output_path_inside_repository():
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/generate_study_assignments.py"),
            "--study-id",
            "pilot-v1",
            "--seed",
            "20260809",
            "--output",
            str(ROOT / "study-assignments.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "human-study output must be outside the repository" in result.stderr


def duplicate_answer_id(rows):
    rows[1]["answer_id"] = rows[0]["answer_id"]


def unbalance_one_condition(rows):
    person = [row for row in rows if row["participant_code"] == "B01"]
    control = next(row for row in person if row["condition"] == "control")
    control["condition"] = "intervention"


def give_person_both_variants_of_pair(rows):
    person = [row for row in rows if row["participant_code"] == "B01"]
    first, second = person[:2]
    second["pair_id"] = first["pair_id"]
    second["output_depth"] = first["output_depth"]
    second["variant"] = "B" if first["variant"] == "A" else "A"


def remove_one_assignment(rows):
    rows.pop()


@pytest.mark.parametrize(
    ("mutate", "expected_error"),
    [
        (duplicate_answer_id, "duplicate answer_id"),
        (unbalance_one_condition, "expected two assignments per condition"),
        (give_person_both_variants_of_pair, "received both variants"),
        (remove_one_assignment, "expected 64 assignments"),
    ],
)
def test_assignment_validator_rejects_adversarial_mutations(mutate, expected_error):
    catalog, generated = _rows()
    rows = copy.deepcopy(generated)
    mutate(rows)
    assert any(expected_error in error for error in validate_assignments(rows, catalog))
