"""Generate the fixed balanced crossover study assignment."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import re
import sys


ROOT = Path(__file__).resolve().parents[1]
if __package__ in {None, ""}:
    sys.path.insert(0, str(ROOT))

from scripts.effectiveness_contract import (
    ensure_external_path,
    load_effectiveness_contract,
    task_variants,
)

DEPTH_ORDER = (
    "quick explanation",
    "evidence navigation",
    "research design",
    "implementation specification",
)
STRATA = (("beginner", "B"), ("professional", "P"))
ANSWER_ID_PATTERN = re.compile(r"^[A-F0-9]{16}$")
ROW_STRING_FIELDS = (
    "answer_id",
    "participant_code",
    "stratum",
    "pair_id",
    "variant",
    "output_depth",
    "condition",
)


def _structured_slot(catalog: dict, slot: int, depth_index: int) -> tuple[dict, str, str]:
    depth = DEPTH_ORDER[depth_index]
    pairs = [pair for pair in catalog["task_pairs"] if pair["output_depth"] == depth]
    pair = pairs[((slot // 4) + depth_index) % 2]
    variant = ("A", "B")[(slot // 2 + depth_index) % 2]
    condition = ("intervention", "control")[(slot + depth_index) % 2]
    return pair, variant, condition


def generate_assignments(catalog: dict, study_id: str, seed: int) -> list[dict]:
    """Return a deterministic 16-person, four-task balanced crossover schedule."""
    variants = {
        (item["pair_id"], item["variant"]): item
        for item in task_variants(catalog)
    }
    rows: list[dict] = []
    for stratum_index, (stratum, prefix) in enumerate(STRATA):
        slots = list(range(8))
        random.Random(seed + stratum_index).shuffle(slots)
        for participant_index, slot in enumerate(slots, start=1):
            participant_code = f"{prefix}{participant_index:02d}"
            rotation = (slot // 2) % 4
            for depth_index in range(4):
                pair, variant, condition = _structured_slot(catalog, slot, depth_index)
                metadata = variants[(pair["id"], variant)]
                order = ((depth_index - rotation) % 4) + 1
                answer_id = _answer_id(
                    study_id,
                    seed,
                    stratum,
                    slot,
                    order,
                    pair["id"],
                    variant,
                )
                rows.append(
                    {
                        "answer_id": answer_id,
                        "participant_code": participant_code,
                        "stratum": stratum,
                        "pair_id": metadata["pair_id"],
                        "variant": metadata["variant"],
                        "output_depth": metadata["output_depth"],
                        "condition": condition,
                        "order": order,
                    }
                )
    return sorted(rows, key=lambda row: (row["stratum"], row["participant_code"], row["order"]))


def validate_assignments(
    rows: list[dict], catalog: dict, study_id: str, seed: int
) -> list[str]:
    """Return deterministic errors for violations of the fixed pilot schedule."""
    errors: list[str] = []
    if not isinstance(rows, list):
        return ["assignments: must be a list"]
    if len(rows) != 64:
        errors.append(f"expected 64 assignments, received {len(rows)}")
    _validate_fixed_schedule(rows, catalog, study_id, seed, errors)

    expected_people = {
        f"{prefix}{index:02d}"
        for _, prefix in STRATA
        for index in range(1, 9)
    }
    by_person: dict[str, list[dict]] = defaultdict(list)
    pairs = {pair["id"]: pair for pair in catalog.get("task_pairs", [])}
    valid_rows: list[dict] = []

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"assignment {index}: must be a mapping")
            continue
        if not _has_valid_row_types(row, index, errors):
            continue
        valid_rows.append(row)
        participant_code = row["participant_code"]
        by_person[participant_code].append(row)
        _validate_row_catalog_values(row, index, pairs, errors)

    answer_ids = Counter(row["answer_id"] for row in valid_rows)
    for answer_id, count in sorted(answer_ids.items()):
        if count > 1:
            errors.append(f"duplicate answer_id: {answer_id}")

    observed_people = set(by_person)
    if observed_people != expected_people:
        missing = sorted(expected_people - observed_people)
        unexpected = sorted(observed_people - expected_people)
        if missing:
            errors.append("missing participant codes: " + ", ".join(missing))
        if unexpected:
            errors.append("unexpected participant codes: " + ", ".join(unexpected))

    for person in sorted(expected_people):
        _validate_person_rows(person, by_person.get(person, []), errors)

    _validate_variant_condition_stratum_balance(valid_rows, pairs, errors)
    _validate_first_order_balance(valid_rows, errors)
    return errors


def _validate_fixed_schedule(
    rows: list[dict], catalog: dict, study_id: str, seed: int, errors: list[str]
) -> None:
    expected_rows = generate_assignments(catalog, study_id, seed)
    for index, (row, expected) in enumerate(zip(rows, expected_rows)):
        if row != expected:
            errors.append(f"assignment {index}: does not match the fixed schedule")
            return
    if len(rows) != len(expected_rows):
        errors.append("assignments: do not match the fixed schedule")


def _has_valid_row_types(row: dict, index: int, errors: list[str]) -> bool:
    valid = True
    for field in ROW_STRING_FIELDS:
        if not isinstance(row.get(field), str):
            errors.append(f"assignment {index}: {field} must be a string")
            valid = False
    order = row.get("order")
    if isinstance(order, bool) or not isinstance(order, int):
        errors.append(f"assignment {index}: order must be an integer")
        valid = False
    return valid


def _answer_id(
    study_id: str,
    seed: int,
    stratum: str,
    slot: int,
    order: int,
    pair_id: str,
    variant: str,
) -> str:
    payload = "|".join(
        (study_id, str(seed), stratum, str(slot), str(order), pair_id, variant)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest().upper()[:16]


def _validate_row_catalog_values(
    row: dict, index: int, pairs: dict[str, dict], errors: list[str]
) -> None:
    participant_code = row.get("participant_code")
    answer_id = row["answer_id"]
    if not ANSWER_ID_PATTERN.fullmatch(answer_id):
        errors.append(f"invalid answer_id: {answer_id}")
    expected_stratum = _stratum_for_code(participant_code)
    if expected_stratum is None:
        errors.append(f"assignment {index}: invalid participant_code: {participant_code}")
    elif row.get("stratum") != expected_stratum:
        errors.append(f"assignment {index}: stratum does not match participant_code")
    pair_id = row.get("pair_id")
    pair = pairs.get(pair_id)
    if pair is None:
        errors.append(f"assignment {index}: unknown pair_id: {pair_id}")
    else:
        if row.get("output_depth") != pair["output_depth"]:
            errors.append(f"assignment {index}: output_depth does not match pair_id")
    if row.get("variant") not in {"A", "B"}:
        errors.append(f"assignment {index}: variant must be A or B")
    if row.get("condition") not in {"control", "intervention"}:
        errors.append(f"assignment {index}: condition must be control or intervention")
    if row["order"] not in {1, 2, 3, 4}:
        errors.append(f"assignment {index}: order must be an integer from 1 through 4")


def _stratum_for_code(participant_code: object) -> str | None:
    if not isinstance(participant_code, str):
        return None
    if re.fullmatch(r"B0[1-8]", participant_code):
        return "beginner"
    if re.fullmatch(r"P0[1-8]", participant_code):
        return "professional"
    return None


def _validate_person_rows(person: str, person_rows: list[dict], errors: list[str]) -> None:
    if len(person_rows) != 4:
        errors.append(f"{person}: expected four assignments, received {len(person_rows)}")
        return
    conditions = Counter(row.get("condition") for row in person_rows)
    if conditions != {"control": 2, "intervention": 2}:
        errors.append(f"{person}: expected two assignments per condition")
    depths = {row.get("output_depth") for row in person_rows}
    if depths != set(DEPTH_ORDER):
        errors.append(f"{person}: expected one assignment per output depth")
    orders = Counter(row.get("order") for row in person_rows)
    if orders != {1: 1, 2: 1, 3: 1, 4: 1}:
        errors.append(f"{person}: expected one assignment at each order")
    by_pair: dict[str, set[object]] = defaultdict(set)
    for row in person_rows:
        by_pair[row.get("pair_id")].add(row.get("variant"))
    for pair_id in sorted(by_pair, key=str):
        variants = by_pair[pair_id]
        if len(variants) > 1:
            errors.append(f"{person}: received both variants of pair {pair_id}")


def _validate_variant_condition_stratum_balance(
    rows: list[dict], pairs: dict[str, dict], errors: list[str]
) -> None:
    counts = Counter(
        (
            row.get("stratum"),
            row.get("pair_id"),
            row.get("variant"),
            row.get("condition"),
        )
        for row in rows
        if isinstance(row, dict)
    )
    expected = {
        (stratum, pair["id"], variant, condition)
        for stratum, _ in STRATA
        for pair in pairs.values()
        for variant in ("A", "B")
        for condition in ("control", "intervention")
    }
    observed = set(counts)
    if observed != expected or any(count != 1 for count in counts.values()):
        errors.append("expected every pair variant once per condition and stratum")


def _validate_first_order_balance(rows: list[dict], errors: list[str]) -> None:
    for stratum, _ in STRATA:
        first = [
            row
            for row in rows
            if isinstance(row, dict)
            and row.get("stratum") == stratum
            and row.get("order") == 1
        ]
        if Counter(row.get("condition") for row in first) != {
            "control": 4,
            "intervention": 4,
        }:
            errors.append(f"{stratum}: expected four first assignments per condition")
        if Counter(row.get("output_depth") for row in first) != {
            depth: 2 for depth in DEPTH_ORDER
        }:
            errors.append(f"{stratum}: expected each output depth first twice")


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks", type=Path, default=ROOT / "evals/effectiveness/offline-tasks.yaml")
    parser.add_argument("--rubric", type=Path, default=ROOT / "evals/effectiveness/rubric.yaml")
    parser.add_argument("--study-id", required=True)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    return parser


def main() -> None:
    parser = _argument_parser()
    args = parser.parse_args()
    try:
        output = ensure_external_path(args.output)
    except ValueError as error:
        parser.error(str(error))
    catalog, _ = load_effectiveness_contract(args.tasks, args.rubric)
    rows = generate_assignments(catalog, args.study_id, args.seed)
    errors = validate_assignments(rows, catalog, args.study_id, args.seed)
    if errors:
        raise SystemExit("invalid assignment schedule: " + "; ".join(errors))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "study_id": args.study_id,
                "seed": args.seed,
                "assignments": rows,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
