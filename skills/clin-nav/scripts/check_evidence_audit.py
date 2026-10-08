"""Check two explicitly selected external JSON files; never open source URLs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from bounded_json import read_strict_json
from evidence_audit import MAX_BYTES, summarize_evidence_audit

CLI_ERROR = "evidence audit validation failed\n"


class _SafeArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.exit(2, CLI_ERROR)


def _repository_or_skill_root() -> Path:
    for candidate in SCRIPT_DIR.parents:
        if (candidate / ".git").exists():
            return candidate.resolve()
    return SCRIPT_DIR.parent.resolve()


def _external_path(path: Path) -> Path:
    resolved = path.resolve(strict=True)
    root = _repository_or_skill_root()
    if resolved == root or resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError("invalid external input")
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = _SafeArgumentParser(prog="check_evidence_audit", description=__doc__, allow_abbrev=False)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--as-of", required=True)
    args = parser.parse_args(argv)
    try:
        ledger_path, audit_path = _external_path(args.ledger), _external_path(args.audit)
        ledger = read_strict_json(ledger_path, max_bytes=MAX_BYTES)
        audit = read_strict_json(audit_path, max_bytes=MAX_BYTES)
        summary = summarize_evidence_audit(ledger, audit, as_of=args.as_of)
    except Exception:
        sys.stderr.write(CLI_ERROR)
        return 2
    sys.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    return 3 if summary["status"] == "needs-review" else 0


if __name__ == "__main__":
    raise SystemExit(main())
