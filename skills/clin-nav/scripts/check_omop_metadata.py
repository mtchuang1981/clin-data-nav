"""Check repository-external OMOP metadata responses without network access."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from omop_metadata_connector import assess_connector


CLI_ERROR = "OMOP metadata validation failed\n"
CATALOG_PATH = SCRIPT_DIR.parent / "references/omop-v5.4-core-catalog.json"
_UNSUMMARIZABLE_CODES = {
    "capabilities-invalid-bytes",
    "capabilities-invalid-json",
    "capabilities-response-too-large",
    "inspection-invalid-bytes",
    "inspection-invalid-json",
    "inspection-response-too-large",
}
_SUCCESS_STATUSES = {"compatible", "compatible-with-deviations"}
_POLICY_FAILURE_STATUSES = {
    "incompatible",
    "stale",
    "version-mismatch",
    "reference-mismatch",
    "unavailable",
}


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
        raise ValueError("input must be outside the repository or installed skill")
    return resolved


def _parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--capabilities", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--as-of", required=True)
    return parser


def main() -> None:
    parser = _parser()
    args = parser.parse_args()
    try:
        capabilities_path = _external_path(args.capabilities)
        inspection_path = _external_path(args.input)
        catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        summary = assess_connector(
            capabilities_path.read_bytes,
            lambda request: inspection_path.read_bytes(),
            catalog=catalog,
            as_of=args.as_of,
        )
    except Exception:
        parser.exit(2, CLI_ERROR)

    codes = summary.get("validation_codes", [])
    if isinstance(codes, list) and any(code in _UNSUMMARIZABLE_CODES for code in codes):
        parser.exit(2, CLI_ERROR)

    sys.stdout.write(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    status = summary.get("status")
    if status in _SUCCESS_STATUSES:
        return
    if status in _POLICY_FAILURE_STATUSES:
        parser.exit(3)
    parser.exit(2)


if __name__ == "__main__":
    main()
