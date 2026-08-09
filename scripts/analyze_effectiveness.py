"""Validate external effectiveness inputs and emit an aggregate-only summary."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if __package__ in {None, ""}:
    sys.path.insert(0, str(ROOT))

from scripts.effectiveness_analysis import unlock_observations
from scripts.effectiveness_contract import ensure_external_path


CLI_ERROR = "effectiveness analysis failed\n"


class _SafeArgumentParser(argparse.ArgumentParser):
    """Keep command-line errors independent of external study content."""

    def error(self, message: str) -> None:
        self.exit(2, CLI_ERROR)


def _argument_parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(
        dest="command", required=True, parser_class=_SafeArgumentParser
    )
    analyze = subcommands.add_parser("analyze")
    analyze.add_argument("--study-manifest", required=True, type=Path)
    analyze.add_argument("--scores", required=True, type=Path)
    analyze.add_argument("--ratings-lock", required=True, type=Path)
    analyze.add_argument("--condition-key", required=True, type=Path)
    analyze.add_argument(
        "--unlock-after-ratings-lock", action="store_true", required=True
    )
    analyze.add_argument("--output-summary", required=True, type=Path)
    return parser


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _analyze(args: argparse.Namespace) -> None:
    input_paths = {
        "manifest": ensure_external_path(args.study_manifest),
        "scores": ensure_external_path(args.scores),
        "lock": ensure_external_path(args.ratings_lock),
        "key": ensure_external_path(args.condition_key),
    }
    output_summary = args.output_summary.resolve()
    if output_summary in set(input_paths.values()):
        raise ValueError("aggregate output must not replace an external input")

    manifest = _read_json(input_paths["manifest"])
    scores_bytes = input_paths["scores"].read_bytes()
    scores = json.loads(scores_bytes.decode("utf-8"))
    lock = _read_json(input_paths["lock"])
    key = _read_json(input_paths["key"])
    if not all(isinstance(value, dict) for value in (manifest, scores, lock, key)):
        raise ValueError("all effectiveness inputs must be JSON mappings")

    observations = unlock_observations(
        manifest, scores, lock, key, scores_bytes
    )
    summary = {
        "schema_version": "1",
        "study_id": scores["study_id"],
        "validated_observation_count": len(observations),
    }
    output_summary.parent.mkdir(parents=True, exist_ok=True)
    output_summary.write_bytes(
        (
            json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n"
        ).encode("utf-8")
    )


def main() -> None:
    parser = _argument_parser()
    try:
        args = parser.parse_args()
        _analyze(args)
    except Exception:
        parser.exit(2, CLI_ERROR)


if __name__ == "__main__":
    main()
