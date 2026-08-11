"""Validate repository-external effectiveness recovery stages."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if __package__ in {None, ""}:
    sys.path.insert(0, str(ROOT))

from scripts.effectiveness_analysis import (
    validate_blinded_agreement_inputs,
    validate_study_manifest,
)
from scripts.effectiveness_contract import ensure_external_path
from scripts.effectiveness_recovery import (
    collection_status,
    green_status,
    rating_status,
    restart_status,
)


CLI_ERROR = "effectiveness recovery validation failed\n"

_EXPECTED_STATUS = {
    "restart-check": "authorized-for-fresh-batch",
    "collection-check": "ready-for-blinded-rating",
    "rating-check": "eligible-for-locked-unlock",
    "green-check": "evaluation-green",
}
_CROSS_FILE_GATES = frozenset(
    {
        "replacement-study-manifest",
        "replacement-study-id",
        "replacement-protocol-commit",
        "replacement-skill-version",
        "replacement-skill-commit",
        "replacement-task-commitment",
        "replacement-environment-fingerprint",
        "replacement-assignment-version",
        "explicit-locked-unlock",
        "aggregate-recomputation",
        "aggregate-report-schema",
    }
)


class _SafeArgumentParser(argparse.ArgumentParser):
    """Keep every command-line error independent of external input content."""

    def error(self, message: str) -> None:
        self.exit(2, CLI_ERROR)


def _argument_parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(description=__doc__, allow_abbrev=False)
    subcommands = parser.add_subparsers(
        dest="command", required=True, parser_class=_SafeArgumentParser
    )

    restart = subcommands.add_parser("restart-check", allow_abbrev=False)
    _add_recovery_record(restart)

    collection = subcommands.add_parser("collection-check", allow_abbrev=False)
    _add_recovery_record(collection)
    collection.add_argument("--study-manifest", required=True, type=Path)

    rating = subcommands.add_parser("rating-check", allow_abbrev=False)
    _add_rating_inputs(rating)

    green = subcommands.add_parser("green-check", allow_abbrev=False)
    _add_rating_inputs(green)
    green.add_argument("--condition-key", required=True, type=Path)
    green.add_argument("--aggregate-summary", required=True, type=Path)
    green.add_argument(
        "--unlock-after-ratings-lock", action="store_true", required=True
    )
    return parser


def _add_recovery_record(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--recovery-record", required=True, type=Path)


def _add_rating_inputs(parser: argparse.ArgumentParser) -> None:
    _add_recovery_record(parser)
    parser.add_argument("--study-manifest", required=True, type=Path)
    parser.add_argument("--scores", required=True, type=Path)
    parser.add_argument("--ratings-lock", required=True, type=Path)


def _path_arguments(args: argparse.Namespace) -> dict[str, Path]:
    names = ["recovery_record"]
    if args.command != "restart-check":
        names.append("study_manifest")
    if args.command in {"rating-check", "green-check"}:
        names.extend(("scores", "ratings_lock"))
    if args.command == "green-check":
        names.extend(("condition_key", "aggregate_summary"))
    return {
        name: ensure_external_path(getattr(args, name))
        for name in names
    }


def _reject_aliases(paths: dict[str, Path]) -> None:
    values = list(paths.values())
    for index, left in enumerate(values):
        for right in values[index + 1 :]:
            if left == right or (
                left.exists() and right.exists() and left.samefile(right)
            ):
                raise ValueError("recovery inputs must be distinct files")


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_mapping(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("recovery input must be a JSON mapping")
    return payload


def _dispatch(args: argparse.Namespace) -> dict:
    paths = _path_arguments(args)
    _reject_aliases(paths)

    record = _require_mapping(_read_json(paths["recovery_record"]))
    restart_status(record)
    if args.command == "restart-check":
        return restart_status(record)

    manifest = _require_mapping(_read_json(paths["study_manifest"]))
    if validate_study_manifest(manifest):
        raise ValueError("invalid replacement study manifest")
    if args.command == "collection-check":
        return collection_status(record, manifest)

    scores_bytes = paths["scores"].read_bytes()
    scores = _require_mapping(json.loads(scores_bytes.decode("utf-8")))
    lock = _require_mapping(_read_json(paths["ratings_lock"]))
    agreement_errors = validate_blinded_agreement_inputs(
        manifest, scores, lock, scores_bytes
    )
    invalid_errors = [
        error
        for error in agreement_errors
        if error != "ratings lock: ratings_complete must be true"
    ]
    if invalid_errors:
        raise ValueError("invalid blinded agreement inputs")
    if args.command == "rating-check":
        return rating_status(record, manifest, scores, lock, scores_bytes)

    key = _require_mapping(_read_json(paths["condition_key"]))
    aggregate = _require_mapping(_read_json(paths["aggregate_summary"]))
    return green_status(
        record,
        manifest,
        scores,
        lock,
        key,
        scores_bytes,
        aggregate,
        unlock_after_ratings_lock=args.unlock_after_ratings_lock,
    )


def _has_cross_file_failure(summary: dict) -> bool:
    blocked = summary.get("blocked_gate_ids")
    return isinstance(blocked, list) and bool(_CROSS_FILE_GATES.intersection(blocked))


def main() -> None:
    parser = _argument_parser()
    try:
        args = parser.parse_args()
        summary = _dispatch(args)
        if _has_cross_file_failure(summary):
            raise ValueError("invalid cross-file recovery bindings")
    except Exception:
        parser.exit(2, CLI_ERROR)

    sys.stdout.write(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    if summary["status"] != _EXPECTED_STATUS[args.command]:
        parser.exit(3)


if __name__ == "__main__":
    main()
