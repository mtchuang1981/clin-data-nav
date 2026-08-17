"""Create a credential-free frozen plan for the public simulation benchmark."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import random
import re
import subprocess
import tempfile

try:
    from scripts.evaluate_response import load_catalog
    from scripts.package_skill import build_package
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from evaluate_response import load_catalog
    from package_skill import build_package


ROOT = Path(__file__).resolve().parents[1]
BINDING_KEYS = frozenset(
    {
        "archive",
        "archive_sha256",
        "commit",
        "manifest",
        "manifest_sha256",
        "member_set_sha256",
        "tag",
        "tag_object",
        "version",
    }
)
PLAN_KEYS = frozenset(
    {
        "assignment_seed",
        "benchmark_id",
        "case_ids",
        "catalog_sha256",
        "cells",
        "conditions",
        "created_at",
        "model",
        "plan_format_version",
        "repeats",
        "rubric_sha256",
        "runner",
        "schema_version",
        "shared_configuration",
        "skill",
    }
)
MODEL_KEYS = frozenset(
    {"id", "max_output_tokens", "provider", "seed_policy", "snapshot", "temperature", "top_p"}
)
RUNNER_KEYS = frozenset({"name", "version"})
SHARED_CONFIGURATION_KEYS = frozenset(
    {"base_system_prompt_sha256", "fresh_session", "network_policy", "tool_policy_sha256"}
)
CONDITION_KEYS = frozenset({"control", "intervention"})
CELL_KEYS = frozenset({"case_id", "condition", "repeat", "sequence"})
SHA256 = re.compile(r"^[0-9a-f]{64}$")
GIT_OBJECT = re.compile(r"^[0-9a-f]{40}$")
SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
SAFE_BENCHMARK_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SAFE_TAG = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
BENCHMARK_ID = "public-simulation-v0-5-0"
V050_BINDING = {
    "archive": "clin-nav-0.5.0.zip",
    "archive_sha256": "195967e3e3b1a6ee32de18a442a7c84badc6642ce6b4ddc0456c441b5f25686d",
    "commit": "3af75bec2c6c79e5617fb94f031eec60a7604143",
    "manifest": "clin-nav-0.5.0.manifest.json",
    "manifest_sha256": "03b736ec703ce3c8b78acc56a8e467d109612fbdd01b08240202d355228332c6",
    "member_set_sha256": "7bb1705efb150f44f65a3b41003cad7cbcfc9b257d29a5f9e7c33bd12e2059ad",
    "tag": "v0.5.0",
    "tag_object": "77c1e1ea140fab8343b178bae63d9c6fc740ccd7",
    "version": "0.5.0",
}


def canonical_json_bytes(value: object) -> bytes:
    """Return the one canonical UTF-8 representation used by benchmark files."""
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        .encode("utf-8")
        + b"\n"
    )


def _package_canonical_json_bytes(value: object) -> bytes:
    """Match the package manifest's compact canonical JSON representation."""
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _git(root: Path, *args: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=text,
    )
    return completed.stdout


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and SHA256.fullmatch(value) is not None


def _exact_keys(value: object, expected: frozenset[str], label: str, errors: list[str]) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        errors.append(f"{label}: exact keys required")


def _valid_binding(binding: object) -> bool:
    if not isinstance(binding, dict) or set(binding) != BINDING_KEYS:
        return False
    if not all(isinstance(binding[key], str) for key in BINDING_KEYS):
        return False
    return (
        binding["tag"].startswith("v")
        and SAFE_TAG.fullmatch(binding["tag"]) is not None
        and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", binding["version"]) is not None
        and binding["archive"] == f"clin-nav-{binding['version']}.zip"
        and binding["manifest"] == f"clin-nav-{binding['version']}.manifest.json"
        and all(_is_sha256(binding[key]) for key in ("archive_sha256", "manifest_sha256", "member_set_sha256"))
        and all(GIT_OBJECT.fullmatch(binding[key]) is not None for key in ("commit", "tag_object"))
    )


def load_released_skill_bindings(path: Path) -> dict:
    """Load the closed, canonical public registry without accepting aliases."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("invalid released Skill registry") from error
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "releases"}:
        raise ValueError("invalid released Skill registry")
    if payload["schema_version"] != "1" or not isinstance(payload["releases"], list):
        raise ValueError("invalid released Skill registry")
    if (
        len(payload["releases"]) != 1
        or not _valid_binding(payload["releases"][0])
        or payload["releases"][0] != V050_BINDING
    ):
        raise ValueError("invalid released Skill registry")
    if path.read_bytes() != canonical_json_bytes(payload):
        raise ValueError("released Skill registry must be canonical")
    return payload


def _safe_tree_paths(root: Path, tag: str) -> tuple[str, ...]:
    listed = _git(root, "ls-tree", "-r", "-z", "--name-only", tag, "--", "skills/clin-nav", text=False)
    assert isinstance(listed, bytes)
    paths = tuple(item.decode("utf-8") for item in listed.split(b"\0") if item)
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("release Skill tree is invalid")
    for path in paths:
        relative = PurePosixPath(path)
        if (
            not path.startswith("skills/clin-nav/")
            or "\\" in path
            or relative.is_absolute()
            or ".." in relative.parts
            or path == "skills/clin-nav/"
        ):
            raise ValueError("release Skill tree is invalid")
    return paths


def resolve_released_skill_binding(root: Path, tag: str, temporary_root: Path) -> dict:
    """Rebuild a local annotated release tag and require its published binding."""
    root = root.resolve()
    if not isinstance(tag, str) or SAFE_TAG.fullmatch(tag) is None or ".." in tag:
        raise ValueError("release tag is invalid")
    registry = load_released_skill_bindings(root / "evals/benchmark/released-skill-bindings.json")
    expected = next((item for item in registry["releases"] if item["tag"] == tag), None)
    if expected is None:
        raise ValueError("release tag is not in the public registry")
    tag_type = _git(root, "cat-file", "-t", tag).strip()
    if tag_type != "tag":
        raise ValueError("release ref must be an annotated tag")
    tag_object = _git(root, "rev-parse", f"{tag}^{{tag}}").strip()
    commit = _git(root, "rev-parse", f"{tag}^{{}}").strip()
    if tag_object != expected["tag_object"] or commit != expected["commit"]:
        raise ValueError("release Git identity does not match the public registry")

    temporary_root = temporary_root.resolve()
    temporary_root.mkdir(parents=True, exist_ok=True)
    paths = _safe_tree_paths(root, tag)
    with tempfile.TemporaryDirectory(prefix="clin-nav-v050-", dir=temporary_root) as materialized:
        materialized_root = Path(materialized)
        skill_dir = materialized_root / "skills" / "clin-nav"
        for path in paths:
            destination = materialized_root / Path(*PurePosixPath(path).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            contents = _git(root, "show", f"{tag}:{path}", text=False)
            assert isinstance(contents, bytes)
            destination.write_bytes(contents)
        result = build_package(skill_dir, materialized_root / "package", package_version=expected["version"])
        manifest = json.loads(result.manifest.read_text(encoding="utf-8"))
        observed = {
            "archive": result.archive.name,
            "archive_sha256": hashlib.sha256(result.archive.read_bytes()).hexdigest(),
            "commit": commit,
            "manifest": result.manifest.name,
            "manifest_sha256": hashlib.sha256(result.manifest.read_bytes()).hexdigest(),
            "member_set_sha256": hashlib.sha256(
                _package_canonical_json_bytes(manifest["files"])
            ).hexdigest(),
            "tag": tag,
            "tag_object": tag_object,
            "version": expected["version"],
        }
    if observed != expected:
        raise ValueError("rebuilt release does not match the public registry")
    return observed


def balanced_cells(case_ids: tuple[str, ...], repeats: int, seed: int) -> tuple[dict, ...]:
    """Return the complete predeclared paired cell order for the normative run."""
    if repeats != 3:
        raise ValueError("repeats must be exactly 3")
    if not isinstance(seed, int) or isinstance(seed, bool) or seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if not case_ids or any(not isinstance(case_id, str) or not case_id for case_id in case_ids):
        raise ValueError("case IDs must be non-empty strings")
    if len(case_ids) != len(set(case_ids)):
        raise ValueError("case IDs must be unique")
    pairs = [(case_id, repeat) for case_id in case_ids for repeat in range(1, repeats + 1)]
    random.Random(seed).shuffle(pairs)
    cells: list[dict] = []
    for pair_index, (case_id, repeat) in enumerate(pairs):
        conditions = ("control", "intervention")
        if pair_index % 2:
            conditions = tuple(reversed(conditions))
        for condition in conditions:
            cells.append(
                {
                    "case_id": case_id,
                    "condition": condition,
                    "repeat": repeat,
                    "sequence": len(cells) + 1,
                }
            )
    return tuple(cells)


def _catalog_contract(root: Path) -> tuple[list[str], str, str]:
    catalog_path = root / "evals/cases.yaml"
    rubric_path = root / "evals/rubric.yaml"
    catalog, _ = load_catalog(catalog_path, rubric_path)
    return (
        [case["id"] for case in catalog["cases"]],
        hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
        hashlib.sha256(rubric_path.read_bytes()).hexdigest(),
    )


def build_benchmark_plan(
    *,
    root: Path,
    skill_ref: str,
    temporary_root: Path,
    model_provider: str,
    model_id: str,
    model_snapshot: str,
    runner_name: str,
    runner_version: str,
    temperature: float,
    top_p: float,
    max_output_tokens: int,
    model_seed_policy: str,
    base_system_prompt_sha256: str,
    tool_policy_sha256: str,
    repeats: int,
    seed: int,
    created_at: str | None = None,
) -> dict:
    """Build a complete plan while resolving every local immutable binding."""
    root = root.resolve()
    case_ids, catalog_sha256, rubric_sha256 = _catalog_contract(root)
    created_at = created_at or datetime.now(timezone.utc).isoformat()
    plan = {
        "assignment_seed": seed,
        "benchmark_id": BENCHMARK_ID,
        "case_ids": case_ids,
        "catalog_sha256": catalog_sha256,
        "cells": list(balanced_cells(tuple(case_ids), repeats, seed)),
        "conditions": {
            "control": {"skill_invocation": None},
            "intervention": {"skill_invocation": "$clin-nav"},
        },
        "created_at": created_at,
        "model": {
            "id": model_id,
            "max_output_tokens": max_output_tokens,
            "provider": model_provider,
            "seed_policy": model_seed_policy,
            "snapshot": model_snapshot,
            "temperature": temperature,
            "top_p": top_p,
        },
        "plan_format_version": "1",
        "repeats": repeats,
        "rubric_sha256": rubric_sha256,
        "runner": {"name": runner_name, "version": runner_version},
        "schema_version": "1",
        "shared_configuration": {
            "base_system_prompt_sha256": base_system_prompt_sha256,
            "fresh_session": True,
            "network_policy": "offline",
            "tool_policy_sha256": tool_policy_sha256,
        },
        "skill": resolve_released_skill_binding(root, skill_ref, temporary_root),
    }
    errors = validate_benchmark_plan(plan)
    if errors:
        raise ValueError("invalid benchmark plan: " + "; ".join(errors))
    return plan


def _valid_identifier(value: object) -> bool:
    return isinstance(value, str) and SAFE_IDENTIFIER.fullmatch(value) is not None


def _aware_utc(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(parsed)


def validate_benchmark_plan(payload: object) -> list[str]:
    """Return deterministic failures for any plan that drifts from the campaign."""
    errors: list[str] = []
    _exact_keys(payload, PLAN_KEYS, "plan", errors)
    if errors:
        return errors
    assert isinstance(payload, dict)
    if payload["schema_version"] != "1" or payload["plan_format_version"] != "1":
        errors.append("plan: unsupported schema version")
    if payload["benchmark_id"] != BENCHMARK_ID:
        errors.append("plan: invalid benchmark ID")
    if not isinstance(payload["repeats"], int) or isinstance(payload["repeats"], bool) or payload["repeats"] != 3:
        errors.append("plan: repeats must be exactly 3")
    if not isinstance(payload["assignment_seed"], int) or isinstance(payload["assignment_seed"], bool) or payload["assignment_seed"] < 0:
        errors.append("plan: invalid assignment seed")
    if not _aware_utc(payload["created_at"]):
        errors.append("plan: created_at must be aware UTC")
    if not _is_sha256(payload["catalog_sha256"]) or not _is_sha256(payload["rubric_sha256"]):
        errors.append("plan: catalog and rubric digests must be lowercase SHA-256")

    case_ids = payload["case_ids"]
    if not isinstance(case_ids, list) or any(not isinstance(item, str) or not item for item in case_ids):
        errors.append("plan: case IDs must be non-empty strings")
        expected_case_ids: list[str] = []
    else:
        expected_case_ids, expected_catalog, expected_rubric = _catalog_contract(ROOT)
        if case_ids != expected_case_ids:
            errors.append("plan: case IDs do not match the catalog order")
        if payload["catalog_sha256"] != expected_catalog or payload["rubric_sha256"] != expected_rubric:
            errors.append("plan: catalog or rubric binding does not match")

    skill = payload["skill"]
    _exact_keys(skill, BINDING_KEYS, "skill", errors)
    if isinstance(skill, dict):
        try:
            registry = load_released_skill_bindings(ROOT / "evals/benchmark/released-skill-bindings.json")
        except ValueError:
            errors.append("skill: release registry is invalid")
        else:
            if skill not in registry["releases"]:
                errors.append("skill: binding is not a closed public release")

    model = payload["model"]
    _exact_keys(model, MODEL_KEYS, "model", errors)
    if isinstance(model, dict) and set(model) == MODEL_KEYS:
        for key in ("provider", "id", "snapshot", "seed_policy"):
            if not _valid_identifier(model[key]):
                errors.append(f"model: invalid {key}")
        for key in ("temperature", "top_p"):
            value = model[key]
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1:
                errors.append(f"model: invalid {key}")
        if not isinstance(model["max_output_tokens"], int) or isinstance(model["max_output_tokens"], bool) or model["max_output_tokens"] <= 0:
            errors.append("model: invalid max_output_tokens")

    runner = payload["runner"]
    _exact_keys(runner, RUNNER_KEYS, "runner", errors)
    if isinstance(runner, dict) and set(runner) == RUNNER_KEYS and not all(
        _valid_identifier(runner[key]) for key in RUNNER_KEYS
    ):
        errors.append("runner: invalid identity")

    shared = payload["shared_configuration"]
    _exact_keys(shared, SHARED_CONFIGURATION_KEYS, "shared configuration", errors)
    if isinstance(shared, dict) and set(shared) == SHARED_CONFIGURATION_KEYS:
        if shared["fresh_session"] is not True:
            errors.append("shared configuration: fresh_session must be true")
        if shared["network_policy"] != "offline":
            errors.append("shared configuration: network_policy must be offline")
        for key in ("base_system_prompt_sha256", "tool_policy_sha256"):
            if not _is_sha256(shared[key]):
                errors.append(f"shared configuration: invalid {key}")

    conditions = payload["conditions"]
    _exact_keys(conditions, CONDITION_KEYS, "conditions", errors)
    if conditions != {
        "control": {"skill_invocation": None},
        "intervention": {"skill_invocation": "$clin-nav"},
    }:
        errors.append("conditions: only bound Skill availability may differ")

    cells = payload["cells"]
    if not isinstance(cells, list):
        errors.append("plan: cells must be a list")
    elif isinstance(case_ids, list) and isinstance(payload["repeats"], int) and isinstance(payload["assignment_seed"], int):
        try:
            expected_cells = list(balanced_cells(tuple(case_ids), payload["repeats"], payload["assignment_seed"]))
        except ValueError:
            errors.append("plan: cells cannot be derived from plan inputs")
        else:
            if any(not isinstance(cell, dict) or set(cell) != CELL_KEYS for cell in cells):
                errors.append("plan: cells have invalid keys")
            if cells != expected_cells:
                errors.append("plan: cells do not match the frozen balanced layout")
    return errors


def _output_is_inside_root(root: Path, output: Path) -> bool:
    return output.resolve().is_relative_to(root.resolve())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-ref", required=True)
    parser.add_argument("--model-provider", required=True)
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--model-snapshot", required=True)
    parser.add_argument("--runner-name", required=True)
    parser.add_argument("--runner-version", required=True)
    parser.add_argument("--temperature", type=float, required=True)
    parser.add_argument("--top-p", type=float, required=True)
    parser.add_argument("--max-output-tokens", type=int, required=True)
    parser.add_argument("--model-seed-policy", required=True)
    parser.add_argument("--base-system-prompt-sha256", required=True)
    parser.add_argument("--tool-policy-sha256", required=True)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20260816)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if _output_is_inside_root(ROOT, args.output):
        parser.error("output must be outside the repository")
    try:
        with tempfile.TemporaryDirectory(prefix="clin-nav-plan-") as temporary_root:
            plan = build_benchmark_plan(
                root=ROOT,
                skill_ref=args.skill_ref,
                temporary_root=Path(temporary_root),
                model_provider=args.model_provider,
                model_id=args.model_id,
                model_snapshot=args.model_snapshot,
                runner_name=args.runner_name,
                runner_version=args.runner_version,
                temperature=args.temperature,
                top_p=args.top_p,
                max_output_tokens=args.max_output_tokens,
                model_seed_policy=args.model_seed_policy,
                base_system_prompt_sha256=args.base_system_prompt_sha256,
                tool_policy_sha256=args.tool_policy_sha256,
                repeats=args.repeats,
                seed=args.seed,
            )
    except (OSError, ValueError, subprocess.CalledProcessError):
        parser.error("unable to create a valid benchmark plan")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    staging = args.output.with_name(args.output.name + ".tmp")
    staging.write_bytes(canonical_json_bytes(plan))
    staging.replace(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
