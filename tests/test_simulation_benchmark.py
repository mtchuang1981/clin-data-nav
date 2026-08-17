from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.evaluate_response import load_catalog
from scripts.prepare_simulation_benchmark import (
    _output_is_inside_root,
    balanced_cells,
    build_benchmark_plan,
    canonical_json_bytes,
    load_released_skill_bindings,
    resolve_released_skill_binding,
    validate_benchmark_plan,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "evals" / "benchmark" / "released-skill-bindings.json"
TEMPLATE = ROOT / "evals" / "benchmark" / "benchmark-plan-template.json"
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


def valid_plan(tmp_path: Path, *, repeats: int = 3, seed: int = 20260816) -> dict:
    return build_benchmark_plan(
        root=ROOT,
        skill_ref="v0.5.0",
        temporary_root=tmp_path,
        model_provider="synthetic-provider",
        model_id="synthetic-model",
        model_snapshot="synthetic-snapshot",
        runner_name="synthetic-runner",
        runner_version="1.0.0",
        temperature=0.2,
        top_p=0.9,
        max_output_tokens=600,
        model_seed_policy="externally-reported",
        base_system_prompt_sha256="a" * 64,
        tool_policy_sha256="b" * 64,
        repeats=repeats,
        seed=seed,
        created_at="2026-08-16T00:00:00+00:00",
    )


def test_v050_registry_matches_rebuilt_annotated_tag(tmp_path):
    observed = resolve_released_skill_binding(ROOT, "v0.5.0", tmp_path)
    assert observed == V050_BINDING


def test_registry_is_closed_canonical_public_binding():
    payload = load_released_skill_bindings(REGISTRY)
    assert set(payload) == {"schema_version", "releases"}
    assert payload == {"schema_version": "1", "releases": [V050_BINDING]}
    assert REGISTRY.read_bytes() == canonical_json_bytes(payload)


@pytest.mark.parametrize(
    "key,value",
    [
        ("archive", "clin-nav-0.5.1.zip"),
        ("archive_sha256", "0" * 64),
        ("commit", "0" * 40),
        ("manifest", "clin-nav-0.5.1.manifest.json"),
        ("manifest_sha256", "0" * 64),
        ("member_set_sha256", "0" * 64),
        ("tag", "v0.5.1"),
        ("tag_object", "0" * 40),
        ("version", "0.5.1"),
    ],
)
def test_registry_rejects_every_mutated_release_binding(key, value, tmp_path):
    """A changed public publication identity must not become a local release alias."""
    payload = load_released_skill_bindings(REGISTRY)
    payload["releases"][0][key] = value
    path = tmp_path / "released-skill-bindings.json"
    path.write_bytes(canonical_json_bytes(payload))

    with pytest.raises(ValueError, match="invalid released Skill registry"):
        load_released_skill_bindings(path)


def test_resolver_rejects_a_nonannotated_tag_type(monkeypatch, tmp_path):
    """Accepting a lightweight ref would disconnect the plan from publication evidence."""
    from scripts import prepare_simulation_benchmark as benchmark

    original_git = benchmark._git

    def git_with_lightweight_tag(root, *args, text=True):
        if args[:2] == ("cat-file", "-t"):
            return "commit\n" if text else b"commit\n"
        return original_git(root, *args, text=text)

    monkeypatch.setattr(benchmark, "_git", git_with_lightweight_tag)
    with pytest.raises(ValueError, match="annotated tag"):
        benchmark.resolve_released_skill_binding(ROOT, "v0.5.0", tmp_path)


def test_plan_has_complete_seed_balanced_layout(tmp_path):
    plan = valid_plan(tmp_path, repeats=3, seed=20260816)
    cells = plan["cells"]

    assert len(cells) == 72
    assert [cell["sequence"] for cell in cells] == list(range(1, 73))
    assert len({(c["case_id"], c["repeat"], c["condition"]) for c in cells}) == 72
    first_conditions = [cells[index]["condition"] for index in range(0, 72, 2)]
    assert first_conditions.count("control") == 18
    assert first_conditions.count("intervention") == 18


def test_plan_binds_catalog_rubric_and_the_complete_release(tmp_path):
    plan = valid_plan(tmp_path)
    catalog, _ = load_catalog(ROOT / "evals/cases.yaml", ROOT / "evals/rubric.yaml")

    assert plan["case_ids"] == [case["id"] for case in catalog["cases"]]
    assert plan["catalog_sha256"] == hashlib.sha256(
        (ROOT / "evals/cases.yaml").read_bytes()
    ).hexdigest()
    assert plan["rubric_sha256"] == hashlib.sha256(
        (ROOT / "evals/rubric.yaml").read_bytes()
    ).hexdigest()
    assert plan["skill"] == V050_BINDING
    assert plan["conditions"] == {
        "control": {"skill_invocation": None},
        "intervention": {"skill_invocation": "$clin-nav"},
    }
    assert plan["shared_configuration"]["fresh_session"] is True
    assert plan["shared_configuration"]["network_policy"] == "offline"
    assert validate_benchmark_plan(plan) == []
    assert canonical_json_bytes(plan).endswith(b"\n")
    assert json.loads(canonical_json_bytes(plan)) == plan


@pytest.mark.parametrize(
    "path,value",
    [
        (("schema_version",), "2"),
        (("plan_format_version",), "2"),
        (("benchmark_id",), "unsafe benchmark id"),
        (("benchmark_id",), "public-simulation-v0-5-1"),
        (("catalog_sha256",), "0" * 64),
        (("rubric_sha256",), "not-a-digest"),
        (("case_ids",), ["wrong-order"]),
        (("repeats",), 2),
        (("assignment_seed",), -1),
        (("created_at",), "2026-08-16T00:00:00"),
        (("skill", "tag"), "v0.5.1"),
        (("skill", "tag_object"), "0" * 40),
        (("skill", "commit"), "0" * 40),
        (("skill", "archive"), "different.zip"),
        (("skill", "archive_sha256"), "0" * 64),
        (("skill", "manifest"), "different.manifest.json"),
        (("skill", "manifest_sha256"), "0" * 64),
        (("skill", "member_set_sha256"), "0" * 64),
        (("skill", "version"), "0.5.1"),
        (("model", "provider"), "unsafe provider"),
        (("model", "id"), "unsafe model"),
        (("model", "snapshot"), "unsafe snapshot"),
        (("model", "seed_policy"), "unsafe policy"),
        (("model", "temperature"), float("inf")),
        (("model", "top_p"), -0.1),
        (("model", "max_output_tokens"), 0),
        (("runner", "name"), "unsafe runner"),
        (("runner", "version"), "unsafe version"),
        (("shared_configuration", "base_system_prompt_sha256"), "A" * 64),
        (("shared_configuration", "tool_policy_sha256"), "A" * 64),
        (("shared_configuration", "fresh_session"), False),
        (("shared_configuration", "network_policy"), "networked"),
        (("conditions", "control", "skill_invocation"), "$clin-nav"),
        (("conditions", "intervention", "skill_invocation"), None),
    ],
)
def test_plan_validator_rejects_mutated_binding_or_control(path, value, tmp_path):
    """A changed immutable field would permit drift or a cherry-picked plan."""
    plan = valid_plan(tmp_path)
    target = plan
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value

    assert validate_benchmark_plan(plan)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda plan: plan["cells"].pop(),
        lambda plan: plan["cells"].__setitem__(1, deepcopy(plan["cells"][0])),
        lambda plan: plan["cells"].reverse(),
        lambda plan: plan["cells"][0].__setitem__("case_id", "unplanned-case"),
        lambda plan: plan["cells"][0].__setitem__("condition", "unplanned-condition"),
        lambda plan: plan["cells"][0].__setitem__("repeat", 4),
        lambda plan: plan["cells"][0].__setitem__("sequence", 0),
        lambda plan: plan["conditions"]["control"].__setitem__("other_difference", True),
        lambda plan: plan.__setitem__("status", "benchmark-observed"),
        lambda plan: plan.__setitem__("direction", "positive-signal"),
        lambda plan: plan.__setitem__("human_effective", True),
        lambda plan: plan.__setitem__("evaluation_green", True),
        lambda plan: plan.__setitem__("api_key", "synthetic-only"),
        lambda plan: plan.__setitem__("token", "synthetic-only"),
        lambda plan: plan.__setitem__("credential", "synthetic-only"),
    ],
)
def test_plan_validator_rejects_cell_or_claim_injection(mutation, tmp_path):
    """Missing cells or supplied outcome/credential claims must fail closed."""
    plan = valid_plan(tmp_path)
    mutation(plan)

    assert validate_benchmark_plan(plan)


@pytest.mark.parametrize(
    "container,key",
    [
        ("model", "id"),
        ("runner", "name"),
        ("shared_configuration", "fresh_session"),
    ],
)
@pytest.mark.parametrize("kind", ["missing", "extra"])
def test_plan_validator_returns_errors_for_nested_key_schema_violations(
    container, key, kind, tmp_path
):
    """A malformed nested mapping must fail closed without leaking a KeyError."""
    plan = valid_plan(tmp_path)
    if kind == "missing":
        del plan[container][key]
    else:
        plan[container]["unexpected"] = True

    errors = validate_benchmark_plan(plan)

    assert errors
    assert f"{container.replace('_', ' ')}: exact keys required" in errors


def test_balanced_cells_requires_the_normative_repeat_count():
    """Allowing another repeat count would make the frozen denominator drift."""
    with pytest.raises(ValueError, match="repeats"):
        balanced_cells(("one",), 2, 1)


def test_template_is_documentation_only_not_a_runnable_plan():
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    assert validate_benchmark_plan(template)
    serialized = TEMPLATE.read_bytes()
    for prohibited in (b"api_key", b"credential", b"synthetic-provider", b"synthetic-model"):
        assert prohibited not in serialized


def test_output_must_be_outside_the_repository(tmp_path):
    """An in-checkout plan would violate the public no-real-run-material boundary."""
    assert _output_is_inside_root(ROOT, ROOT / "benchmark-plan.json")
    assert not _output_is_inside_root(ROOT, tmp_path / "benchmark-plan.json")


PREP_ERROR = b"simulation benchmark preparation failed\n"
PREP_SUCCESS = b'{"cell_count":72,"schema_version":"1","status":"benchmark-plan-ready"}\n'


def _prepare_command(output: Path, **overrides: str) -> list[str]:
    """Return a complete public command using synthetic runner metadata."""
    values = {
        "--skill-ref": "v0.5.0",
        "--model-provider": "synthetic-provider",
        "--model-id": "synthetic-model",
        "--model-snapshot": "synthetic-snapshot",
        "--runner-name": "synthetic-runner",
        "--runner-version": "1.0.0",
        "--temperature": "0.2",
        "--top-p": "0.9",
        "--max-output-tokens": "600",
        "--model-seed-policy": "externally-reported",
        "--base-system-prompt-sha256": "a" * 64,
        "--tool-policy-sha256": "b" * 64,
        "--repeats": "3",
        "--seed": "20260816",
        "--output": str(output),
    }
    values.update(overrides)
    command = [sys.executable, str(ROOT / "scripts" / "prepare_simulation_benchmark.py")]
    return command + [part for option, value in values.items() for part in (option, value)]


def _run_prepare(output: Path, **overrides: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        _prepare_command(output, **overrides),
        cwd=ROOT,
        capture_output=True,
        check=False,
    )


def test_prepare_cli_writes_a_valid_complete_external_plan(tmp_path):
    """Skipping a cell or writing inside checkout would make a real run untraceable."""
    output = tmp_path / "benchmark-plan.json"

    completed = _run_prepare(output)

    assert completed.returncode == 0
    assert completed.stdout == PREP_SUCCESS
    assert completed.stderr == b""
    payload = json.loads(output.read_bytes())
    assert len(payload["cells"]) == 72
    assert validate_benchmark_plan(payload) == []


def test_prepare_main_writes_identical_canonical_bytes_for_a_fixed_clock(tmp_path):
    """Using wall-clock time directly would make an otherwise fixed plan non-reproducible."""
    from scripts import prepare_simulation_benchmark as benchmark

    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    fixed_now = lambda: datetime(2026, 8, 16, tzinfo=timezone.utc)
    arguments = _prepare_command(first)[2:]

    assert benchmark.main(arguments, now=fixed_now) == 0
    arguments[arguments.index(str(first))] = str(second)
    assert benchmark.main(arguments, now=fixed_now) == 0

    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes() == canonical_json_bytes(json.loads(first.read_bytes()))


@pytest.mark.parametrize(
    "output,overrides,extra_arguments",
    [
        (ROOT / "benchmark-plan.json", {}, []),
        (Path("missing-parent") / "benchmark-plan.json", {}, []),
        (Path("existing-directory"), {}, []),
        (Path("safe-output.json"), {"--skill-ref": "not-a-closed-release"}, []),
        (Path("safe-output.json"), {"--temperature": "nan"}, []),
        (Path("safe-output.json"), {}, ["--credential-MARKER-DO-NOT-ECHO", "value"]),
        (Path("safe-output.json"), {}, ["--model-pro", "synthetic-provider"]),
    ],
)
def test_prepare_cli_rejects_unsafe_or_malformed_input_without_content(
    tmp_path, output, overrides, extra_arguments
):
    """Echoing rejected input or accepting an alias could disclose credentials or drift config."""
    if output == Path("existing-directory"):
        output = tmp_path / output
        output.mkdir()
    elif not output.is_absolute():
        output = tmp_path / output
    if output.parent.name == "missing-parent":
        output = tmp_path / "missing-parent" / output.name
    command = _prepare_command(output, **overrides) + extra_arguments

    completed = subprocess.run(command, cwd=ROOT, capture_output=True, check=False)

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr == PREP_ERROR
    assert b"MARKER-DO-NOT-ECHO" not in completed.stdout + completed.stderr


def test_prepare_cli_rejects_a_symlinked_or_reparse_output_parent(tmp_path):
    """Following a redirected parent would permit output to escape its reviewed location."""
    target = tmp_path / "target"
    target.mkdir()
    redirected = tmp_path / "redirected"
    try:
        os.symlink(target, redirected, target_is_directory=True)
    except (NotImplementedError, OSError):
        junction = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", "/J", str(redirected), str(target)],
            capture_output=True,
            check=False,
        )
        if junction.returncode:
            pytest.skip("the current filesystem cannot create a symlink or junction")

    completed = _run_prepare(redirected / "benchmark-plan.json")

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr == PREP_ERROR
    assert not (target / "benchmark-plan.json").exists()
    if redirected.exists():
        redirected.rmdir()


def test_prepare_cli_failure_does_not_replace_an_existing_output(tmp_path):
    """A failed validation must not destroy a prior completed external plan."""
    output = tmp_path / "benchmark-plan.json"
    original = b"previous-valid-plan-bytes\n"
    output.write_bytes(original)

    completed = _run_prepare(output, **{"--skill-ref": "MARKER-DO-NOT-ECHO"})

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr == PREP_ERROR
    assert output.read_bytes() == original
