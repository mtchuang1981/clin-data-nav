"""Validate one repository-external governance readiness instance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if __package__ in {None, ""}:
    sys.path.insert(0, str(ROOT))

from scripts.effectiveness_contract import ensure_external_path
from scripts.governance_readiness import (
    summarize_governance_readiness,
    validate_governance_readiness,
)


CLI_ERROR = "governance readiness validation failed\n"


class _SafeArgumentParser(argparse.ArgumentParser):
    """Keep command-line errors independent of governance input content."""

    def error(self, message: str) -> None:
        self.exit(2, CLI_ERROR)


def _argument_parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--input", required=True, type=Path)
    return parser


def main() -> None:
    parser = _argument_parser()
    args = parser.parse_args()
    try:
        input_path = ensure_external_path(args.input)
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if validate_governance_readiness(payload):
            raise ValueError("invalid governance readiness input")
        summary = summarize_governance_readiness(payload)
    except Exception:
        parser.exit(2, CLI_ERROR)

    sys.stdout.write(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    if summary["status"] == "incomplete":
        parser.exit(3)


if __name__ == "__main__":
    main()
