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

EXPECTED_CATALOG = {
    "schema_version": "1",
    "task_pairs": [
        {
            "id": "quick-adam-sdtm",
            "output_depth": "quick explanation",
            "expected_minutes": 10,
            "difficulty": 1,
            "mandatory_criteria": [
                "correct-output-depth",
                "answers-requested-decision",
                "states-confirmed-assumed-limited",
            ],
            "quality_criteria": [
                "beginner-readable",
                "actionable-next-step",
                "validation-gaps",
            ],
            "variants": {
                "A": {
                    "prompt": "Synthetic scenario: A new clinical-data researcher asks what ADaM is and how it differs from SDTM. At quick-explanation depth, answer in plain language, separate confirmed facts from limitations, and give one safe next step."
                },
                "B": {
                    "prompt": "Synthetic scenario: A new clinical-data researcher asks how SDTM differs from source data collection. At quick-explanation depth, answer in plain language, separate confirmed facts from limitations, and give one safe next step."
                },
            },
        },
        {
            "id": "quick-rwd-rwe",
            "output_depth": "quick explanation",
            "expected_minutes": 10,
            "difficulty": 1,
            "mandatory_criteria": [
                "correct-output-depth",
                "answers-requested-decision",
                "states-confirmed-assumed-limited",
            ],
            "quality_criteria": [
                "beginner-readable",
                "actionable-next-step",
                "validation-gaps",
            ],
            "variants": {
                "A": {
                    "prompt": "Synthetic scenario: A beginner has records from a patient registry and calls the records RWE. At quick-explanation depth, distinguish RWD from RWE, state what has and has not yet been established, and give one safe next step."
                },
                "B": {
                    "prompt": "Synthetic scenario: A beginner has administrative claims and calls them causal evidence. At quick-explanation depth, distinguish claims RWD from RWE and causal evidence, state the main limitation, and give one safe next step."
                },
            },
        },
        {
            "id": "evidence-cdisc-source-route",
            "output_depth": "evidence navigation",
            "expected_minutes": 18,
            "difficulty": 2,
            "mandatory_criteria": [
                "correct-output-depth",
                "answers-requested-decision",
                "states-confirmed-assumed-limited",
            ],
            "quality_criteria": [
                "authority-appropriate-sources",
                "citation-verifiable",
                "actionable-next-step",
                "validation-gaps",
            ],
            "variants": {
                "A": {
                    "prompt": "Synthetic scenario: A researcher needs to confirm the definition and derivation expectations for an ADaM analysis variable. At evidence-navigation depth, provide an ordered authority route, explain what each source can establish, identify unresolved version details, and do not invent a citation."
                },
                "B": {
                    "prompt": "Synthetic scenario: A researcher needs to confirm how an SDTM timing variable should be represented. At evidence-navigation depth, provide an ordered authority route, explain what each source can establish, identify unresolved version details, and do not invent a citation."
                },
            },
        },
        {
            "id": "evidence-lexjansen-sas",
            "output_depth": "evidence navigation",
            "expected_minutes": 20,
            "difficulty": 2,
            "mandatory_criteria": [
                "correct-output-depth",
                "answers-requested-decision",
                "states-confirmed-assumed-limited",
            ],
            "quality_criteria": [
                "authority-appropriate-sources",
                "citation-verifiable",
                "actionable-next-step",
                "validation-gaps",
            ],
            "variants": {
                "A": {
                    "prompt": "Synthetic scenario: A researcher wants to optimize SAS logic for treatment-emergent adverse events and asks whether LexJansen examples are enough. At evidence-navigation depth, route the question through authoritative requirements and relevant secondary implementation literature, explain how LexJansen material may be used and independently verified, and identify validation gaps."
                },
                "B": {
                    "prompt": "Synthetic scenario: A researcher wants to optimize SAS logic for treatment exposure and asks whether LexJansen examples are enough. At evidence-navigation depth, route the question through authoritative requirements and relevant secondary implementation literature, explain how LexJansen material may be used and independently verified, and identify validation gaps."
                },
            },
        },
        {
            "id": "research-descriptive-rwd",
            "output_depth": "research design",
            "expected_minutes": 20,
            "difficulty": 2,
            "mandatory_criteria": [
                "correct-output-depth",
                "answers-requested-decision",
                "states-confirmed-assumed-limited",
            ],
            "quality_criteria": [
                "pico-and-time-zero",
                "authority-appropriate-sources",
                "actionable-next-step",
                "validation-gaps",
            ],
            "variants": {
                "A": {
                    "prompt": "Synthetic scenario: Design a non-causal study describing use of a therapy class in routinely collected health data. At research-design depth, define the descriptive question, population, observation window, measures, source-authority checks, and limitations; do not imply a causal effect."
                },
                "B": {
                    "prompt": "Synthetic scenario: Design a non-causal study estimating the observed incidence of a diagnosis in routinely collected health data. At research-design depth, define the descriptive question, population, time origin, follow-up, measures, source-authority checks, and limitations; do not imply a causal effect."
                },
            },
        },
        {
            "id": "research-causal-tte",
            "output_depth": "research design",
            "expected_minutes": 25,
            "difficulty": 3,
            "mandatory_criteria": [
                "correct-output-depth",
                "answers-requested-decision",
                "states-confirmed-assumed-limited",
                "tte-readiness",
            ],
            "quality_criteria": [
                "pico-and-time-zero",
                "authority-appropriate-sources",
                "actionable-next-step",
                "validation-gaps",
            ],
            "variants": {
                "A": {
                    "prompt": "Synthetic scenario: Design an observational comparison of drug A versus drug B for a clinical outcome using routinely collected data. At research-design depth, specify PICO and time zero, assess target-trial-emulation readiness and key causal threats, define the analysis direction, and state that build-rwe-sap is optional and not bundled or executable unless its separate prerequisites are met."
                },
                "B": {
                    "prompt": "Synthetic scenario: Design an observational comparison of procedure A versus procedure B for a clinical outcome using routinely collected data. At research-design depth, specify PICO and time zero, assess target-trial-emulation readiness and key causal threats, define the analysis direction, and state that build-rwe-sap is optional and not bundled or executable unless its separate prerequisites are met."
                },
            },
        },
        {
            "id": "implementation-teae-sas",
            "output_depth": "implementation specification",
            "expected_minutes": 25,
            "difficulty": 3,
            "mandatory_criteria": [
                "correct-output-depth",
                "answers-requested-decision",
                "states-confirmed-assumed-limited",
                "logical-data-contract",
                "execution-status",
            ],
            "quality_criteria": [
                "authority-appropriate-sources",
                "actionable-next-step",
                "validation-gaps",
            ],
            "variants": {
                "A": {
                    "prompt": "Synthetic scenario: Specify SAS-ready logical requirements for a treatment-emergent adverse-event derivation without access to any physical schema. At implementation-specification depth, provide inputs, outputs, key variables, timing rules, pseudocode, validation checks, assumptions, and an explicit non-executable status."
                },
                "B": {
                    "prompt": "Synthetic scenario: Specify SAS-ready logical requirements for a treatment-emergent laboratory-abnormality derivation without access to any physical schema. At implementation-specification depth, provide inputs, outputs, key variables, timing rules, pseudocode, validation checks, assumptions, and an explicit non-executable status."
                },
            },
        },
        {
            "id": "implementation-omop-sql",
            "output_depth": "implementation specification",
            "expected_minutes": 25,
            "difficulty": 3,
            "mandatory_criteria": [
                "correct-output-depth",
                "answers-requested-decision",
                "states-confirmed-assumed-limited",
                "logical-data-contract",
                "execution-status",
            ],
            "quality_criteria": [
                "authority-appropriate-sources",
                "actionable-next-step",
                "validation-gaps",
            ],
            "variants": {
                "A": {
                    "prompt": "Synthetic scenario: Specify a logical OMOP SQL phenotype for diabetes without access to any local database or physical schema. At implementation-specification depth, provide cohort entry, inclusion and exclusion logic, time windows, logical table and field requirements, pseudocode, validation checks, assumptions, and an explicit non-executable status."
                },
                "B": {
                    "prompt": "Synthetic scenario: Specify a logical OMOP SQL phenotype for hypertension without access to any local database or physical schema. At implementation-specification depth, provide cohort entry, inclusion and exclusion logic, time windows, logical table and field requirements, pseudocode, validation checks, assumptions, and an explicit non-executable status."
                },
            },
        },
    ],
}

EXPECTED_RUBRIC = {
    "schema_version": "1",
    "minimum_quality_fraction": 0.8,
    "criteria": [
        {
            "id": "correct-output-depth",
            "kind": "mandatory",
            "description": "Uses the required output-depth contract.",
        },
        {
            "id": "answers-requested-decision",
            "kind": "mandatory",
            "description": "Directly completes the assigned decision.",
        },
        {
            "id": "states-confirmed-assumed-limited",
            "kind": "mandatory",
            "description": "Separates facts, assumptions, and limits.",
        },
        {
            "id": "authority-appropriate-sources",
            "kind": "quality",
            "description": "Routes claims to appropriate source authority.",
        },
        {
            "id": "actionable-next-step",
            "kind": "quality",
            "description": "Gives a safe and usable next action.",
        },
        {
            "id": "beginner-readable",
            "kind": "quality",
            "description": "Uses plain language where the task requires it.",
        },
        {
            "id": "pico-and-time-zero",
            "kind": "quality",
            "description": "Defines applicable PICO and time anchors.",
        },
        {
            "id": "tte-readiness",
            "kind": "mandatory",
            "description": "Evaluates TTE readiness for causal comparison.",
        },
        {
            "id": "logical-data-contract",
            "kind": "mandatory",
            "description": "Supplies the complete logical contract when requested.",
        },
        {
            "id": "execution-status",
            "kind": "mandatory",
            "description": "Uses the correct maturity/execution status.",
        },
        {
            "id": "citation-verifiable",
            "kind": "quality",
            "description": "Gives verifiable rather than fabricated citations.",
        },
        {
            "id": "validation-gaps",
            "kind": "quality",
            "description": "Makes unresolved checks explicit.",
        },
    ],
    "critical_violations": [
        {
            "id": "invented-schema",
            "description": "Invents a table, field, key, code, date meaning, or institutional fact.",
        },
        {
            "id": "false-executable-status",
            "description": "Claims executable or validated status without required current metadata and evidence.",
        },
        {
            "id": "rwd-rwe-confusion",
            "description": "Treats RWD as RWE or asserts an unsupported causal conclusion.",
        },
        {
            "id": "unsupported-causal-claim",
            "description": "Makes an unsupported causal claim.",
        },
        {
            "id": "fabricated-citation",
            "description": "Fabricates a citation.",
        },
        {
            "id": "unreviewed-search-as-authority",
            "description": "Promotes an unreviewed search result to governing evidence.",
        },
        {
            "id": "missing-tte-readiness",
            "description": "Omits the required TTE-readiness decision for a causal-comparative task.",
        },
        {
            "id": "private-data-request-or-exposure",
            "description": "Requests, exposes, or reproduces patient data, a private adapter, or an internal document.",
        },
    ],
}


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


def test_checked_in_offline_contract_matches_the_binding_public_fixture():
    """Any prompt, rubric, or pair-contract drift must fail repository CI."""
    catalog, rubric = load_effectiveness_contract(TASKS, RUBRIC)

    assert catalog == EXPECTED_CATALOG
    assert rubric == EXPECTED_RUBRIC


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
