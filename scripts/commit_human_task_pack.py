"""Create and verify commitments for externally held human task packs."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import secrets
import sys

import yaml


ROOT = Path(__file__).resolve().parents[1]
if __package__ in {None, ""}:
    sys.path.insert(0, str(ROOT))

from scripts.effectiveness_contract import ensure_external_path, load_effectiveness_contract


DOMAIN = b"clin-data-nav-human-task-pack-v1\0"
SCHEME = "sha256-nonce-task-pack-v1"
COMMITMENT_KEYS = {
    "schema_version",
    "scheme",
    "commitment_sha256",
    "canonical_task_bytes",
    "pair_count",
    "depth_counts",
    "pair_ids",
}


def canonical_task_pack_bytes(path: Path) -> bytes:
    """Return UTF-8, LF-normalized bytes for a task pack."""
    data = path.read_bytes()
    if b"\x00" in data:
        raise ValueError("human task pack must be UTF-8 text without NUL bytes")
    text = data.decode("utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _commitment_digest(canonical_bytes: bytes, nonce: bytes) -> str:
    if len(nonce) != 32:
        raise ValueError("commitment nonce must be exactly 32 bytes")
    return hashlib.sha256(DOMAIN + nonce + b"\0" + canonical_bytes).hexdigest()


def build_commitment(canonical_bytes: bytes, nonce: bytes, catalog: dict) -> dict:
    """Build public metadata and a domain-separated digest without task text."""
    pairs = _task_pairs(catalog)
    pair_ids = sorted(_pair_id(pair, index) for index, pair in enumerate(pairs))
    depth_counts = Counter(
        _output_depth(pair, index) for index, pair in enumerate(pairs)
    )
    return {
        "schema_version": "1",
        "scheme": SCHEME,
        "commitment_sha256": _commitment_digest(canonical_bytes, nonce),
        "canonical_task_bytes": len(canonical_bytes),
        "pair_count": len(pairs),
        "depth_counts": dict(sorted(depth_counts.items())),
        "pair_ids": pair_ids,
    }


def verify_commitment(task_pack: Path, nonce: bytes, commitment: dict) -> list[str]:
    """Return deterministic validation errors without revealing task content."""
    errors = _commitment_schema_errors(commitment)
    if errors:
        return errors
    canonical_bytes = canonical_task_pack_bytes(task_pack)
    expected_digest = _commitment_digest(canonical_bytes, nonce)
    if commitment["commitment_sha256"] != expected_digest:
        return ["commitment_sha256 mismatch"]

    catalog = yaml.safe_load(canonical_bytes.decode("utf-8"))
    try:
        expected = build_commitment(canonical_bytes, nonce, catalog)
    except ValueError:
        return ["task pack metadata is invalid"]
    return [
        f"{field} mismatch"
        for field in (
            "schema_version",
            "scheme",
            "canonical_task_bytes",
            "pair_count",
            "depth_counts",
            "pair_ids",
        )
        if commitment[field] != expected[field]
    ]


def _task_pairs(catalog: object) -> list[object]:
    if not isinstance(catalog, dict) or not isinstance(catalog.get("task_pairs"), list):
        raise ValueError("task pack catalog must contain a task_pairs list")
    return catalog["task_pairs"]


def _pair_id(pair: object, index: int) -> str:
    if not isinstance(pair, dict) or not isinstance(pair.get("id"), str):
        raise ValueError(f"task pair {index}: id must be a string")
    return pair["id"]


def _output_depth(pair: object, index: int) -> str:
    if not isinstance(pair, dict) or not isinstance(pair.get("output_depth"), str):
        raise ValueError(f"task pair {index}: output_depth must be a string")
    return pair["output_depth"]


def _commitment_schema_errors(commitment: object) -> list[str]:
    if not isinstance(commitment, dict):
        return ["commitment: must be a mapping"]
    errors: list[str] = []
    missing = sorted(COMMITMENT_KEYS - set(commitment))
    unexpected = sorted(set(commitment) - COMMITMENT_KEYS)
    if missing:
        errors.append("commitment: missing keys: " + ", ".join(missing))
    if unexpected:
        errors.append("commitment: unexpected keys: " + ", ".join(unexpected))
    if errors:
        return errors
    if commitment["schema_version"] != "1":
        errors.append('commitment: schema_version must be "1"')
    if commitment["scheme"] != SCHEME:
        errors.append(f"commitment: scheme must be {SCHEME}")
    if not isinstance(commitment["commitment_sha256"], str):
        errors.append("commitment: commitment_sha256 must be a string")
    if isinstance(commitment["canonical_task_bytes"], bool) or not isinstance(
        commitment["canonical_task_bytes"], int
    ):
        errors.append("commitment: canonical_task_bytes must be an integer")
    if isinstance(commitment["pair_count"], bool) or not isinstance(
        commitment["pair_count"], int
    ):
        errors.append("commitment: pair_count must be an integer")
    if not isinstance(commitment["depth_counts"], dict):
        errors.append("commitment: depth_counts must be a mapping")
    if not isinstance(commitment["pair_ids"], list):
        errors.append("commitment: pair_ids must be a list")
    return errors


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)

    create = subcommands.add_parser("create")
    create.add_argument("--task-pack", required=True, type=Path)
    create.add_argument(
        "--rubric", type=Path, default=ROOT / "evals/effectiveness/rubric.yaml"
    )
    create.add_argument("--nonce-output", required=True, type=Path)
    create.add_argument("--commitment-output", required=True, type=Path)

    verify = subcommands.add_parser("verify")
    verify.add_argument("--task-pack", required=True, type=Path)
    verify.add_argument("--nonce-file", required=True, type=Path)
    verify.add_argument("--commitment", required=True, type=Path)
    return parser


def _create(args: argparse.Namespace) -> None:
    nonce_output = ensure_external_path(args.nonce_output)
    task_pack = ensure_external_path(args.task_pack)
    catalog, _ = load_effectiveness_contract(task_pack, args.rubric)
    nonce = secrets.token_bytes(32)
    canonical_bytes = canonical_task_pack_bytes(task_pack)
    commitment = build_commitment(canonical_bytes, nonce, catalog)
    with nonce_output.open("xb") as nonce_file:
        nonce_file.write(nonce)
    args.commitment_output.write_bytes(_canonical_json_bytes(commitment))


def _verify(args: argparse.Namespace) -> None:
    nonce = args.nonce_file.read_bytes()
    commitment = json.loads(args.commitment.read_text(encoding="utf-8"))
    errors = verify_commitment(args.task_pack, nonce, commitment)
    if errors:
        raise ValueError("invalid commitment: " + "; ".join(errors))


def _canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def main() -> None:
    parser = _argument_parser()
    args = parser.parse_args()
    try:
        if args.command == "create":
            _create(args)
        else:
            _verify(args)
    except (OSError, UnicodeDecodeError, ValueError, yaml.YAMLError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
