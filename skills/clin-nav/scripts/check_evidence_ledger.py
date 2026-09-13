"""Check one repository-external evidence ledger without network access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from evidence_ledger import summarize_evidence_ledger, validate_evidence_ledger


CLI_ERROR = "evidence ledger validation failed\n"


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.exit(2, CLI_ERROR)


def _repository_or_skill_root() -> Path:
    for candidate in SCRIPT_DIR.parents:
        if (candidate / ".git").exists():
            return candidate.resolve()
    return SCRIPT_DIR.parent.resolve()


def _external_path(path: Path) -> Path:
    resolved = path.resolve()
    protected_root = _repository_or_skill_root()
    if resolved == protected_root or resolved.is_relative_to(protected_root):
        raise ValueError("ledger must be outside the repository or installed skill")
    return resolved


def _parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--as-of", required=True)
    return parser


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    try:
        path = _external_path(args.input)
        payload = json.loads(path.read_text(encoding="utf-8"))
        errors = validate_evidence_ledger(payload, as_of=args.as_of)
        if errors:
            raise ValueError("invalid evidence ledger")
        summary = summarize_evidence_ledger(payload, as_of=args.as_of)
    except Exception:
        parser.exit(2, CLI_ERROR)

    sys.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    if summary["status"] == "review-required":
        parser.exit(3)


if __name__ == "__main__":
    main()
