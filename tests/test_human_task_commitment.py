import json
from pathlib import Path
import subprocess
import sys

from scripts.commit_human_task_pack import (
    build_commitment,
    canonical_task_pack_bytes,
    verify_commitment,
)
from scripts.effectiveness_contract import load_effectiveness_contract


ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "evals/effectiveness/offline-tasks.yaml"
RUBRIC = ROOT / "evals/effectiveness/rubric.yaml"
EXAMPLE = ROOT / "evals/effectiveness/examples/human-task-commitment.example.json"


def test_lf_and_crlf_task_packs_have_the_same_commitment(tmp_path):
    lf = tmp_path / "lf.yaml"
    crlf = tmp_path / "crlf.yaml"
    payload = "schema_version: '1'\ntask_pairs: []\n"
    lf.write_bytes(payload.encode("utf-8"))
    crlf.write_bytes(payload.replace("\n", "\r\n").encode("utf-8"))
    nonce = bytes.fromhex("00" * 32)

    assert build_commitment(
        canonical_task_pack_bytes(lf), nonce, {"task_pairs": []}
    )["commitment_sha256"] == build_commitment(
        canonical_task_pack_bytes(crlf), nonce, {"task_pairs": []}
    )["commitment_sha256"]


def test_commitment_contains_metadata_but_not_nonce_or_prompt_text():
    canonical = b"schema_version: '1'\ntask_pairs: []\n"
    nonce = bytes.fromhex("ab" * 32)
    commitment = build_commitment(canonical, nonce, {"task_pairs": []})
    serialized = json.dumps(commitment, sort_keys=True)

    assert nonce.hex() not in serialized
    assert "prompt" not in serialized
    assert commitment["scheme"] == "sha256-nonce-task-pack-v1"
    assert commitment["canonical_task_bytes"] == len(canonical)
    assert set(commitment) == {
        "schema_version",
        "scheme",
        "commitment_sha256",
        "canonical_task_bytes",
        "pair_count",
        "depth_counts",
        "pair_ids",
    }


def test_verify_rejects_changed_task_pack_and_changed_nonce(tmp_path):
    task_pack = tmp_path / "human-tasks.yaml"
    original = b"schema_version: '1'\ntask_pairs: []\n"
    nonce = bytes.fromhex("12" * 32)
    task_pack.write_bytes(original)
    commitment = build_commitment(
        canonical_task_pack_bytes(task_pack), nonce, {"task_pairs": []}
    )

    task_pack.write_bytes(original + b"# changed\n")
    assert verify_commitment(task_pack, nonce, commitment) == [
        "commitment_sha256 mismatch"
    ]

    task_pack.write_bytes(original)
    changed_nonce = bytes([nonce[0] ^ 1]) + nonce[1:]
    assert verify_commitment(task_pack, changed_nonce, commitment) == [
        "commitment_sha256 mismatch"
    ]


def test_create_cli_rejects_nonce_output_inside_repository(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/commit_human_task_pack.py"),
            "create",
            "--task-pack",
            str(tmp_path / "external-human-tasks.yaml"),
            "--nonce-output",
            str(ROOT / "human-task-pack.nonce"),
            "--commitment-output",
            str(tmp_path / "commitment.json"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 2
    assert "human-study output must be outside the repository" in result.stderr


def test_public_example_is_exactly_recomputed_with_zero_nonce():
    catalog, _ = load_effectiveness_contract(TASKS, RUBRIC)
    expected = {
        "example_only": True,
        "commitment": build_commitment(
            canonical_task_pack_bytes(TASKS), bytes.fromhex("00" * 32), catalog
        ),
    }
    actual = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    serialized = json.dumps(actual, sort_keys=True)

    assert set(actual) == {"example_only", "commitment"}
    assert actual["example_only"] is True
    assert set(actual["commitment"]) == set(expected["commitment"])
    assert '"nonce"' not in serialized
    assert '"prompt"' not in serialized
    assert "00" * 32 not in serialized
    assert EXAMPLE.read_bytes() == (
        json.dumps(expected, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def test_verify_cli_allows_a_post_lock_task_pack_inside_repository(tmp_path):
    catalog, _ = load_effectiveness_contract(TASKS, RUBRIC)
    nonce = bytes.fromhex("00" * 32)
    nonce_path = tmp_path / "nonce.bin"
    commitment_path = tmp_path / "commitment.json"
    nonce_path.write_bytes(nonce)
    commitment_path.write_text(
        json.dumps(
            build_commitment(canonical_task_pack_bytes(TASKS), nonce, catalog),
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/commit_human_task_pack.py"),
            "verify",
            "--task-pack",
            str(TASKS),
            "--nonce-file",
            str(nonce_path),
            "--commitment",
            str(commitment_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
