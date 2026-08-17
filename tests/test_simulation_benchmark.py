from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts.evaluate_simulation_benchmark import (
    IncompleteBenchmark,
    canonical_summary_bytes,
    classify_direction,
    evaluate_benchmark,
    load_response_cells,
    validate_benchmark_summary,
    validate_response_index,
)
from scripts.evaluate_response import (
    DEPTH_SECTION_CONTRACTS,
    evaluate_response,
    load_catalog,
)
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
RESPONSE_INDEX_TEMPLATE = ROOT / "evals" / "benchmark" / "response-index-template.json"
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


@pytest.fixture(scope="module")
def benchmark_plan(tmp_path_factory) -> dict:
    return valid_plan(tmp_path_factory.mktemp("response-plan"))


def _response_bundle(plan: dict, responses_root: Path) -> tuple[dict, Path]:
    responses_root.mkdir()
    records = []
    for cell in plan["cells"]:
        relative_path = f"response-{cell['sequence']:03d}.md"
        content = f"# Synthetic response {cell['sequence']}\n".encode()
        (responses_root / relative_path).write_bytes(content)
        records.append(
            {
                "case_id": cell["case_id"],
                "condition": cell["condition"],
                "repeat": cell["repeat"],
                "relative_path": relative_path,
                "response_sha256": hashlib.sha256(content).hexdigest(),
                "size": len(content),
            }
        )
    return (
        {
            "schema_version": "1",
            "plan_sha256": hashlib.sha256(canonical_json_bytes(plan)).hexdigest(),
            "execution_attestation": {
                "completed_at": "2026-08-16T01:00:00+00:00",
                "model_provider": plan["model"]["provider"],
                "model_id": plan["model"]["id"],
                "model_snapshot": plan["model"]["snapshot"],
                "runner_name": plan["runner"]["name"],
                "runner_version": plan["runner"]["version"],
                "plan_followed": True,
                "fresh_sessions": True,
                "offline": True,
                "shared_configuration_unchanged": True,
            },
            "records": records,
        },
        responses_root,
    )


@pytest.fixture
def response_bundle(benchmark_plan, tmp_path) -> tuple[dict, dict, Path]:
    index, responses_root = _response_bundle(benchmark_plan, tmp_path / "responses")
    return deepcopy(benchmark_plan), index, responses_root


def _update_record_for_bytes(index: dict, record_index: int, content: bytes) -> None:
    index["records"][record_index]["size"] = len(content)
    index["records"][record_index]["response_sha256"] = hashlib.sha256(content).hexdigest()


def _make_symlink(target: Path, link: Path, *, directory: bool = False) -> None:
    try:
        os.symlink(target, link, target_is_directory=directory)
    except (NotImplementedError, OSError):
        command = ["cmd.exe", "/d", "/c", "mklink"]
        if directory:
            command.append("/J")
        completed = subprocess.run(
            [*command, str(link), str(target)], capture_output=True, check=False
        )
        if completed.returncode:
            pytest.skip("the current filesystem cannot create a symlink or reparse point")


def _move_first_response_under(
    response_index: dict, responses_root: Path, directory_name: str
) -> tuple[Path, str]:
    record = response_index["records"][0]
    original = responses_root / record["relative_path"]
    directory = responses_root / directory_name
    directory.mkdir()
    moved = directory / original.name
    original.rename(moved)
    record["relative_path"] = f"{directory_name}/{original.name}"
    return directory, original.name


def _remove_directory_reparse(path: Path) -> None:
    if path.is_symlink():
        path.unlink()
    else:
        path.rmdir()


REQUIRED_RESPONSE_MARKERS = {
    "adam-quick-explanation": (
        "Output depth: quick explanation",
        "plain language",
        "Analysis Data Model",
        "SDTM",
        "analysis-ready",
        "common confusion",
    ),
    "teae-sas-spec": ("protocol", "SAP", "official standard", "code maturity"),
    "sas-optimization-lexjansen": (
        "site:lexjansen.com",
        "specific paper",
        "title",
        "author",
        "conference",
        "publication year",
        "stable URL",
        "access date",
        "provenance",
        "license",
        "reuse terms",
        "clean-room implementation",
        "secondary implementation evidence",
        "network access",
        "not reviewed",
        "performance validation",
    ),
    "institutional-sql-without-dictionary": (
        "SPECIFICATION ONLY — NOT EXECUTABLE",
        "mapping checklist",
        "versioned data dictionary",
        "live metadata verification",
    ),
    "stale-codingbook": (
        "live metadata verification",
        "current",
        "version",
        "historical documentation",
    ),
    "cdisc-variable-definition": (
        "CDISC",
        "controlled terminology",
        "official",
        "conference paper",
    ),
    "omop-phenotype": (
        "standard concept",
        "local code",
        "research phenotype",
        "non-executable",
    ),
    "tmucrd-public-profile": (
        "DOI",
        "public source snapshot",
        "not a schema",
        "institutional query guide",
    ),
    "descriptive-rwd-no-tte": (
        "descriptive",
        "RWD",
        "RWE",
        "provenance",
        "fitness",
        "not applicable",
        "not automatically RWE",
    ),
    "causal-rwd-tte-handoff": (
        "causal-comparative",
        "eligibility",
        "strategies",
        "assignment",
        "time zero",
        "follow-up",
        "outcome",
        "estimand",
        "analysis plan",
        "data limitations",
        "validation gaps",
        "build-rwe-sap",
        "unavailable",
    ),
    "causal-rwd-incomplete-readiness": (
        "causal-comparative",
        "research design only",
        "not implementation-ready",
        "missing comparator",
        "missing time zero",
        "missing confounding",
        "validation gap",
        "no causal conclusion",
    ),
    "build-rwe-sap-unavailable": (
        "optional",
        "not bundled",
        "not automatically installed",
        "unavailable",
        "continue",
        "Core",
        "evidence navigation",
        "logical data needs",
        "complete SAP",
        "not delivered",
    ),
}


def _passing_generated_response(case: dict) -> str:
    headings = DEPTH_SECTION_CONTRACTS[case["output_depth"]]["required"]
    lines = [
        "Decision: Use the bounded synthetic contract.",
        "Confirmed facts: Only public synthetic inputs are in scope.",
        "Assumptions: None beyond the synthetic prompt.",
        "Limitations: This generated response is a deterministic test fixture.",
        "Sources actually consulted: The public synthetic case only.",
        *REQUIRED_RESPONSE_MARKERS[case["id"]],
    ]
    for heading in headings:
        lines.extend((f"## {heading}", "Synthetic bounded content."))
    return "\n".join(lines) + "\n"


def _valid_execution_attestation(plan: dict) -> dict:
    return {
        "completed_at": "2026-08-16T01:00:00+00:00",
        "model_provider": plan["model"]["provider"],
        "model_id": plan["model"]["id"],
        "model_snapshot": plan["model"]["snapshot"],
        "runner_name": plan["runner"]["name"],
        "runner_version": plan["runner"]["version"],
        "plan_followed": True,
        "fresh_sessions": True,
        "offline": True,
        "shared_configuration_unchanged": True,
    }


def _cells_for_pattern(plan: dict, pattern: str) -> tuple[dict, ...]:
    catalog, rubric = load_catalog(
        ROOT / "evals/cases.yaml", ROOT / "evals/rubric.yaml"
    )
    cases = {case["id"]: case for case in catalog["cases"]}
    pair_keys = [
        (case_id, repeat)
        for case_id in plan["case_ids"]
        for repeat in range(1, plan["repeats"] + 1)
    ]
    outcomes = {pair: "both_pass" for pair in pair_keys}
    if pattern == "positive":
        outcomes.update({pair: "improved" for pair in pair_keys[:12]})
    elif pattern == "negative":
        outcomes.update({pair: "worsened" for pair in pair_keys[:12]})
    elif pattern == "boundary-7":
        outcomes.update({pair: "improved" for pair in pair_keys[:7]})
    elif pattern == "boundary-8":
        outcomes.update({pair: "improved" for pair in pair_keys[:8]})
    elif pattern == "equal-discordance":
        outcomes[pair_keys[0]] = "improved"
        outcomes[pair_keys[1]] = "worsened"
    elif pattern == "intervention-forbidden":
        forbidden_pair = ("adam-quick-explanation", 1)
        improved_pairs = [pair for pair in pair_keys if pair != forbidden_pair][:8]
        outcomes.update({pair: "improved" for pair in improved_pairs})
        outcomes[forbidden_pair] = "intervention_forbidden"
    elif pattern == "negative-depth":
        worsened_pair = ("adam-quick-explanation", 1)
        non_quick = [
            pair
            for pair in pair_keys
            if cases[pair[0]]["output_depth"] != "quick explanation"
        ]
        outcomes.update({pair: "improved" for pair in non_quick[:9]})
        outcomes[worsened_pair] = "worsened"
    elif pattern != "mixed":
        raise AssertionError(f"unknown generated response pattern: {pattern}")

    cells = []
    for planned in plan["cells"]:
        pair = (planned["case_id"], planned["repeat"])
        outcome = outcomes[pair]
        condition = planned["condition"]
        passes = outcome == "both_pass" or (
            outcome == "improved" and condition == "intervention"
        ) or (outcome == "worsened" and condition == "control")
        response = (
            _passing_generated_response(cases[planned["case_id"]])
            if passes
            else ""
        )
        if outcome == "intervention_forbidden" and condition == "intervention":
            response = (
                _passing_generated_response(cases[planned["case_id"]])
                + "ADaM is raw collection data\n"
            )
        cells.append({**planned, "text": response})
    assert all(
        evaluate_response(cases[cell["case_id"]], rubric, cell["text"]).passed
        == (cell["text"] != "" and "ADaM is raw collection data" not in cell["text"])
        for cell in cells
    )
    return tuple(cells)


def _track_windows_response_resources(monkeypatch, benchmark):
    opened_handles = []
    opened_descriptors = []
    original_open_root = benchmark._windows_open_root
    original_open_relative = benchmark._windows_open_relative
    original_open_osfhandle = benchmark.msvcrt.open_osfhandle

    def tracking_open_root(path):
        handle = original_open_root(path)
        opened_handles.append(handle)
        return handle

    def tracking_open_relative(parent_handle, name):
        handle = original_open_relative(parent_handle, name)
        opened_handles.append(handle)
        return handle

    def tracking_open_osfhandle(handle, flags):
        descriptor = original_open_osfhandle(handle, flags)
        opened_descriptors.append(descriptor)
        return descriptor

    monkeypatch.setattr(benchmark, "_windows_open_root", tracking_open_root)
    monkeypatch.setattr(benchmark, "_windows_open_relative", tracking_open_relative)
    monkeypatch.setattr(benchmark.msvcrt, "open_osfhandle", tracking_open_osfhandle)
    return opened_handles, opened_descriptors


def _live_windows_response_resources(benchmark, handles, descriptors):
    live_descriptors = []
    for descriptor in set(descriptors):
        try:
            os.fstat(descriptor)
        except OSError:
            continue
        live_descriptors.append(descriptor)

    live_handles = []
    for handle in set(handles):
        try:
            benchmark._windows_handle_info(handle)
        except ValueError:
            continue
        live_handles.append(handle)
    return live_handles, live_descriptors


def _assert_live_unique_descriptors_at_injection(descriptors, expected_count):
    assert len(descriptors) == expected_count
    assert len(set(descriptors)) == expected_count
    observed_stats = tuple(os.fstat(descriptor) for descriptor in descriptors)
    assert len(observed_stats) == expected_count


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


def test_prepare_cli_rejects_a_symlinked_final_output_without_changing_its_target(tmp_path):
    """Resolving the final component first would overwrite an arbitrary external target."""
    target = tmp_path / "target.json"
    original = b"existing-external-target\n"
    target.write_bytes(original)
    output = tmp_path / "linked-output.json"
    try:
        os.symlink(target, output)
    except (NotImplementedError, OSError):
        link = subprocess.run(
            ["cmd.exe", "/d", "/c", "mklink", str(output), str(target)],
            capture_output=True,
            check=False,
        )
        if link.returncode:
            pytest.skip("the current filesystem cannot create a file symlink")

    completed = _run_prepare(output)

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr == PREP_ERROR
    assert target.read_bytes() == original
    assert output.is_symlink()


@pytest.mark.parametrize("help_option", ["-h", "--help"])
def test_prepare_cli_rejects_help_without_echoing_usage(help_option):
    """A help path would create a second public stdout shape outside the closed contract."""
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "prepare_simulation_benchmark.py"), help_option],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr == PREP_ERROR
    assert b"usage" not in completed.stdout + completed.stderr


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


def test_response_loader_returns_the_exact_canonical_cells(response_bundle):
    plan, response_index, responses_root = response_bundle

    cells = load_response_cells(plan, response_index, responses_root)

    assert len(cells) == 72
    assert tuple(cell["sequence"] for cell in cells) == tuple(range(1, 73))
    assert all(
        set(cell) == {"case_id", "condition", "repeat", "sequence", "text"}
        for cell in cells
    )
    assert cells[0]["text"].startswith("# Synthetic response")
    assert all("path" not in cell and "bytes" not in cell for cell in cells)


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", "2"),
        ("plan_sha256", "0" * 64),
        ("execution_attestation", None),
        ("records", {}),
    ],
)
def test_response_index_rejects_each_mutated_root_field(
    field, value, response_bundle
):
    plan, response_index, _ = response_bundle
    response_index[field] = value

    assert validate_response_index(response_index, plan)


@pytest.mark.parametrize(
    "field,value",
    [
        ("completed_at", "2026-08-16T01:00:00"),
        ("model_provider", "different-provider"),
        ("model_id", "different-model"),
        ("model_snapshot", "different-snapshot"),
        ("runner_name", "different-runner"),
        ("runner_version", "2.0.0"),
        ("plan_followed", False),
        ("fresh_sessions", False),
        ("offline", False),
        ("shared_configuration_unchanged", False),
    ],
)
def test_response_index_rejects_each_mutated_attestation_field(
    field, value, response_bundle
):
    """Runner metadata are externally asserted and cross-checked, not provider-verified."""
    plan, response_index, _ = response_bundle
    response_index["execution_attestation"][field] = value

    assert validate_response_index(response_index, plan)


@pytest.mark.parametrize(
    "field",
    [
        "plan_followed",
        "fresh_sessions",
        "offline",
        "shared_configuration_unchanged",
    ],
)
def test_response_index_requires_attestation_booleans_to_be_literal_true(
    field, response_bundle
):
    plan, response_index, _ = response_bundle
    response_index["execution_attestation"][field] = 1

    assert validate_response_index(response_index, plan)


def test_response_index_rejects_completion_before_plan_creation(response_bundle):
    plan, response_index, _ = response_bundle
    response_index["execution_attestation"]["completed_at"] = (
        "2026-08-15T23:59:59+00:00"
    )

    assert validate_response_index(response_index, plan)


@pytest.mark.parametrize(
    "field,value",
    [
        ("case_id", "unknown-case"),
        ("condition", "unknown-condition"),
        ("repeat", 0),
        ("relative_path", "/absolute-response.md"),
        ("response_sha256", "A" * 64),
        ("size", -1),
    ],
)
def test_response_index_rejects_each_mutated_record_field(
    field, value, response_bundle
):
    plan, response_index, _ = response_bundle
    response_index["records"][0][field] = value

    assert validate_response_index(response_index, plan)


@pytest.mark.parametrize("value", [4, True])
def test_response_index_rejects_out_of_range_or_boolean_repeat(value, response_bundle):
    plan, response_index, _ = response_bundle
    response_index["records"][0]["repeat"] = value

    assert validate_response_index(response_index, plan)


def test_response_index_rejects_boolean_size(response_bundle):
    plan, response_index, _ = response_bundle
    response_index["records"][0]["size"] = True

    assert validate_response_index(response_index, plan)


@pytest.mark.parametrize(
    "field,value",
    [
        ("case_id", []),
        ("condition", []),
        ("repeat", []),
        ("relative_path", []),
        ("response_sha256", []),
        ("size", []),
    ],
)
def test_response_index_returns_errors_for_malformed_record_value_types(
    field, value, response_bundle
):
    """An unhashable JSON value must fail closed instead of leaking a TypeError."""
    plan, response_index, _ = response_bundle
    response_index["records"][0][field] = value

    assert validate_response_index(response_index, plan)


@pytest.mark.parametrize("container", ["root", "attestation", "record"])
@pytest.mark.parametrize("kind", ["missing", "extra"])
def test_response_index_requires_closed_keys(container, kind, response_bundle):
    plan, response_index, _ = response_bundle
    target = {
        "root": response_index,
        "attestation": response_index["execution_attestation"],
        "record": response_index["records"][0],
    }[container]
    if kind == "missing":
        target.pop(next(iter(target)))
    else:
        target["status"] = "MARKER-DO-NOT-ECHO"

    errors = validate_response_index(response_index, plan)

    assert errors
    assert "MARKER-DO-NOT-ECHO" not in " ".join(errors)


@pytest.mark.parametrize(
    "unsafe_path",
    [
        "../response.md",
        "nested/../../response.md",
        r"nested\response.md",
        "C:/absolute-response.md",
    ],
)
def test_response_index_rejects_unsafe_non_posix_paths(unsafe_path, response_bundle):
    plan, response_index, _ = response_bundle
    response_index["records"][0]["relative_path"] = unsafe_path

    assert validate_response_index(response_index, plan)


def test_response_index_rejects_duplicate_normalized_paths(response_bundle):
    plan, response_index, _ = response_bundle
    response_index["records"][0]["relative_path"] = "nested/response.md"
    response_index["records"][1]["relative_path"] = "nested//response.md"

    assert validate_response_index(response_index, plan)


@pytest.mark.parametrize("mutation", ["duplicate", "reordered"])
def test_response_index_rejects_duplicate_or_reordered_records(mutation, response_bundle):
    plan, response_index, _ = response_bundle
    if mutation == "duplicate":
        response_index["records"].append(deepcopy(response_index["records"][0]))
    else:
        response_index["records"][0], response_index["records"][1] = (
            response_index["records"][1],
            response_index["records"][0],
        )

    assert validate_response_index(response_index, plan)


def test_response_index_rejects_an_interior_omission_as_invalid(response_bundle):
    plan, response_index, _ = response_bundle
    response_index["records"].pop(12)

    assert validate_response_index(response_index, plan)


def test_response_index_raises_incomplete_only_for_an_exact_canonical_prefix(
    response_bundle,
):
    plan, response_index, _ = response_bundle
    response_index["records"] = response_index["records"][:-1]

    with pytest.raises(IncompleteBenchmark) as caught:
        validate_response_index(response_index, plan)

    assert caught.value.expected_count == 72
    assert caught.value.observed_count == 71


def test_response_loader_rejects_an_extra_response_file_before_content_reads(
    response_bundle, monkeypatch
):
    plan, response_index, responses_root = response_bundle
    (responses_root / "unexpected.md").write_bytes(b"MARKER-DO-NOT-ECHO\n")
    reads = []
    original = Path.read_bytes

    def tracking_read(path):
        if path.is_relative_to(responses_root):
            reads.append(path)
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", tracking_read)

    with pytest.raises(ValueError, match="invalid response files") as caught:
        load_response_cells(plan, response_index, responses_root)

    assert reads == []
    assert "MARKER-DO-NOT-ECHO" not in str(caught.value)


def test_response_loader_rejects_a_missing_file(response_bundle):
    plan, response_index, responses_root = response_bundle
    (responses_root / response_index["records"][0]["relative_path"]).unlink()

    with pytest.raises(ValueError, match="invalid response files"):
        load_response_cells(plan, response_index, responses_root)


def test_response_loader_rejects_a_directory_in_place_of_a_file(response_bundle):
    plan, response_index, responses_root = response_bundle
    response_path = responses_root / response_index["records"][0]["relative_path"]
    response_path.unlink()
    response_path.mkdir()

    with pytest.raises(ValueError, match="invalid response files"):
        load_response_cells(plan, response_index, responses_root)


def test_response_loader_rejects_a_symlink_or_reparse_file(response_bundle, tmp_path):
    plan, response_index, responses_root = response_bundle
    response_path = responses_root / response_index["records"][0]["relative_path"]
    target = tmp_path / "external-target.md"
    target.write_bytes(response_path.read_bytes())
    response_path.unlink()
    _make_symlink(target, response_path)

    with pytest.raises(ValueError, match="invalid response files"):
        load_response_cells(plan, response_index, responses_root)


def test_response_loader_rejects_an_escaping_symlink_parent(response_bundle, tmp_path):
    plan, response_index, responses_root = response_bundle
    original = responses_root / response_index["records"][0]["relative_path"]
    content = original.read_bytes()
    original.unlink()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "escaped.md").write_bytes(content)
    redirected = responses_root / "redirected"
    _make_symlink(outside, redirected, directory=True)
    response_index["records"][0]["relative_path"] = "redirected/escaped.md"

    with pytest.raises(ValueError, match="invalid response files"):
        load_response_cells(plan, response_index, responses_root)


def test_response_loader_rejects_response_path_reparse_race_before_content_read(
    response_bundle, tmp_path, monkeypatch
):
    """Opening by pathname after validation would read a replacement reparse target."""
    from scripts import evaluate_simulation_benchmark as benchmark

    plan, response_index, responses_root = response_bundle
    directory, filename = _move_first_response_under(
        response_index, responses_root, "race-file-parent"
    )
    held = tmp_path / "held-file-parent"
    target = tmp_path / "file-race-target"
    target.mkdir()
    marker = b"MARKER-FILE-RACE-DO-NOT-READ\n"
    (target / filename).write_bytes(marker)
    raced = False
    content_reads = []
    original_path_read = Path.read_bytes
    original_os_read = os.read

    def replace_before_open(path):
        nonlocal raced
        if path == directory / filename and not raced:
            raced = True
            directory.rename(held)
            _make_symlink(target, directory, directory=True)

    def tracking_path_read(path):
        if path.is_relative_to(responses_root) or path.is_relative_to(target):
            content_reads.append(path)
        return original_path_read(path)

    def tracking_os_read(file_descriptor, size):
        content_reads.append(file_descriptor)
        return original_os_read(file_descriptor, size)

    monkeypatch.setattr(
        benchmark, "_before_response_file_open", replace_before_open, raising=False
    )
    monkeypatch.setattr(Path, "read_bytes", tracking_path_read)
    monkeypatch.setattr(os, "read", tracking_os_read)

    with pytest.raises(ValueError, match="invalid response files") as caught:
        load_response_cells(plan, response_index, responses_root)

    assert raced
    assert content_reads == []
    assert marker.decode().strip() not in str(caught.value)


def test_response_loader_rejects_pending_directory_reparse_race_before_scan(
    response_bundle, tmp_path, monkeypatch
):
    """Scanning an enqueued directory by pathname would follow a replacement target."""
    from scripts import evaluate_simulation_benchmark as benchmark

    plan, response_index, responses_root = response_bundle
    directory, filename = _move_first_response_under(
        response_index, responses_root, "race-pending-directory"
    )
    held = tmp_path / "held-pending-directory"
    target = tmp_path / "directory-race-target"
    target.mkdir()
    marker = b"MARKER-DIRECTORY-RACE-DO-NOT-READ\n"
    (target / filename).write_bytes(marker)
    raced = False
    content_reads = []
    original_path_read = Path.read_bytes
    original_os_read = os.read

    def replace_before_scan(path):
        nonlocal raced
        if path == directory and not raced:
            raced = True
            directory.rename(held)
            _make_symlink(target, directory, directory=True)

    def tracking_path_read(path):
        if path.is_relative_to(responses_root) or path.is_relative_to(target):
            content_reads.append(path)
        return original_path_read(path)

    def tracking_os_read(file_descriptor, size):
        content_reads.append(file_descriptor)
        return original_os_read(file_descriptor, size)

    monkeypatch.setattr(
        benchmark, "_before_directory_scan", replace_before_scan, raising=False
    )
    monkeypatch.setattr(Path, "read_bytes", tracking_path_read)
    monkeypatch.setattr(os, "read", tracking_os_read)

    with pytest.raises(ValueError, match="invalid response files") as caught:
        load_response_cells(plan, response_index, responses_root)

    assert raced
    assert content_reads == []
    assert marker.decode().strip() not in str(caught.value)


@pytest.mark.skipif(os.name != "nt", reason="Windows handle-relative ABA contract")
def test_windows_response_file_aba_race_is_rejected_before_content_read(
    response_bundle, tmp_path, monkeypatch
):
    """A restored pathname must not hide the reparse object opened by parent handle."""
    from scripts import evaluate_simulation_benchmark as benchmark

    plan, response_index, responses_root = response_bundle
    victim = responses_root / response_index["records"][0]["relative_path"]
    held = tmp_path / "held-response-file.md"
    target = tmp_path / "response-file-reparse-target"
    target.mkdir()
    marker = b"MARKER-WINDOWS-FILE-ABA-DO-NOT-READ\n"
    (target / "marker.md").write_bytes(marker)
    swapped = False
    restored = False
    content_reads = []
    original_os_read = os.read

    def swap_after_precheck(parent, name):
        nonlocal swapped
        if parent == responses_root and name == victim.name and not swapped:
            swapped = True
            victim.rename(held)
            _make_symlink(target, victim, directory=True)

    def restore_after_relative_open(parent, name):
        nonlocal restored
        if parent == responses_root and name == victim.name and swapped and not restored:
            _remove_directory_reparse(victim)
            held.rename(victim)
            restored = True

    def tracking_os_read(file_descriptor, size):
        content_reads.append(file_descriptor)
        return original_os_read(file_descriptor, size)

    monkeypatch.setattr(
        benchmark,
        "_after_windows_file_precheck_before_relative_open",
        swap_after_precheck,
        raising=False,
    )
    monkeypatch.setattr(
        benchmark,
        "_after_windows_relative_open",
        restore_after_relative_open,
        raising=False,
    )
    monkeypatch.setattr(os, "read", tracking_os_read)

    with pytest.raises(ValueError, match="invalid response files") as caught:
        load_response_cells(plan, response_index, responses_root)

    assert swapped and restored
    assert content_reads == []
    assert marker.decode().strip() not in str(caught.value)


@pytest.mark.skipif(os.name != "nt", reason="Windows handle-relative ABA contract")
def test_windows_pending_directory_aba_race_is_rejected_before_content_read(
    response_bundle, tmp_path, monkeypatch
):
    """A restored directory name must not hide its opened junction handle."""
    from scripts import evaluate_simulation_benchmark as benchmark

    plan, response_index, responses_root = response_bundle
    directory, filename = _move_first_response_under(
        response_index, responses_root, "windows-aba-directory"
    )
    held = tmp_path / "held-windows-aba-directory"
    target = tmp_path / "directory-aba-reparse-target"
    target.mkdir()
    marker = b"MARKER-WINDOWS-DIRECTORY-ABA-DO-NOT-READ\n"
    (target / filename).write_bytes(marker)
    swapped = False
    restored = False
    content_reads = []
    original_os_read = os.read

    def swap_after_precheck(parent, name):
        nonlocal swapped
        if parent == responses_root and name == directory.name and not swapped:
            swapped = True
            directory.rename(held)
            _make_symlink(target, directory, directory=True)

    def restore_after_relative_open(parent, name):
        nonlocal restored
        if parent == responses_root and name == directory.name and swapped and not restored:
            _remove_directory_reparse(directory)
            held.rename(directory)
            restored = True

    def tracking_os_read(file_descriptor, size):
        content_reads.append(file_descriptor)
        return original_os_read(file_descriptor, size)

    monkeypatch.setattr(
        benchmark,
        "_after_windows_directory_precheck_before_relative_open",
        swap_after_precheck,
        raising=False,
    )
    monkeypatch.setattr(
        benchmark,
        "_after_windows_relative_open",
        restore_after_relative_open,
        raising=False,
    )
    monkeypatch.setattr(os, "read", tracking_os_read)

    with pytest.raises(ValueError, match="invalid response files") as caught:
        load_response_cells(plan, response_index, responses_root)

    assert swapped and restored
    assert content_reads == []
    assert marker.decode().strip() not in str(caught.value)


@pytest.mark.skipif(os.name != "nt", reason="Windows HANDLE ownership contract")
def test_windows_deep_unexpected_tree_has_fixed_error_and_closes_owned_resources(
    response_bundle, monkeypatch
):
    """Depth must not escape the safe error contract or strand prior response opens."""
    from scripts import evaluate_simulation_benchmark as benchmark

    plan, response_index, responses_root = response_bundle
    deep_directories = []
    current = responses_root / "unexpected"
    current.mkdir()
    deep_directories.append(current)
    for _ in range(sys.getrecursionlimit() + 32):
        current = current / "d"
        current.mkdir()
        deep_directories.append(current)
    marker = b"MARKER-WINDOWS-DEEP-TREE-DO-NOT-DISCLOSE\n"
    marker_path = current / "unexpected.md"
    marker_path.write_bytes(marker)

    original_entries = benchmark._windows_directory_entries

    def sorted_entries(directory_handle):
        return tuple(sorted(original_entries(directory_handle), key=lambda item: item[0]))

    monkeypatch.setattr(benchmark, "_windows_directory_entries", sorted_entries)

    def fail_at_deepest_directory(directory_path):
        if directory_path == current:
            raise RuntimeError(marker.decode().strip())

    monkeypatch.setattr(benchmark, "_before_directory_scan", fail_at_deepest_directory)
    handles, descriptors = _track_windows_response_resources(monkeypatch, benchmark)
    original_os_read = os.read
    content_reads = []

    def tracking_os_read(file_descriptor, size):
        content_reads.append(file_descriptor)
        return original_os_read(file_descriptor, size)

    monkeypatch.setattr(os, "read", tracking_os_read)
    failure = None
    live_handles = []
    live_descriptors = []
    try:
        try:
            load_response_cells(plan, response_index, responses_root)
        except BaseException as error:  # Probe leaked resources before test cleanup.
            failure = error
        live_handles, live_descriptors = _live_windows_response_resources(
            benchmark, handles, descriptors
        )
    finally:
        for descriptor in live_descriptors:
            os.close(descriptor)
        for handle in live_handles:
            benchmark._windows_close_handle(handle)
        marker_path.unlink()
        for directory in reversed(deep_directories):
            directory.rmdir()

    assert descriptors, "the fixture responses must be opened before the deep tree"
    assert type(failure) is ValueError
    assert str(failure) == "invalid response files"
    assert marker.decode().strip() not in str(failure)
    assert content_reads == []
    assert live_descriptors == []
    assert live_handles == []


@pytest.mark.skipif(os.name != "nt", reason="Windows HANDLE ownership contract")
def test_windows_second_snapshot_exception_closes_first_snapshot_with_fixed_error(
    response_bundle, monkeypatch
):
    """A second traversal failure must release the already returned first snapshot."""
    from scripts import evaluate_simulation_benchmark as benchmark

    _, response_index, responses_root = response_bundle
    expected_paths = {
        record["relative_path"] for record in response_index["records"]
    }
    handles, descriptors = _track_windows_response_resources(monkeypatch, benchmark)
    original_open_tree = benchmark._windows_open_response_tree
    call_count = 0
    first_snapshot_descriptors = ()
    injection_checks_completed = False
    marker = "MARKER-WINDOWS-SECOND-SNAPSHOT-DO-NOT-DISCLOSE"

    def fail_second_snapshot(root):
        nonlocal call_count, first_snapshot_descriptors, injection_checks_completed
        call_count += 1
        if call_count == 2:
            first_snapshot_descriptors = tuple(descriptors)
            _assert_live_unique_descriptors_at_injection(
                first_snapshot_descriptors, 72
            )
            injection_checks_completed = True
            raise RuntimeError(marker)
        return original_open_tree(root)

    monkeypatch.setattr(benchmark, "_windows_open_response_tree", fail_second_snapshot)
    failure = None
    try:
        benchmark._windows_verified_descriptors(responses_root, expected_paths)
    except Exception as error:
        failure = error
    live_handles, live_descriptors = _live_windows_response_resources(
        benchmark, handles, first_snapshot_descriptors
    )
    try:
        assert call_count == 2
        assert len(expected_paths) == 72
        assert injection_checks_completed
        assert len(first_snapshot_descriptors) == 72
        assert len(set(first_snapshot_descriptors)) == 72
        assert descriptors == list(first_snapshot_descriptors)
        assert type(failure) is ValueError
        assert str(failure) == "invalid response files"
        assert marker not in str(failure)
        assert live_descriptors == []
        assert live_handles == []
    finally:
        for descriptor in live_descriptors:
            os.close(descriptor)
        for handle in live_handles:
            benchmark._windows_close_handle(handle)


@pytest.mark.skipif(os.name != "nt", reason="Windows HANDLE ownership contract")
def test_windows_snapshot_comparator_exception_closes_both_with_fixed_error(
    response_bundle, monkeypatch
):
    """A comparator failure must release both fully populated snapshots."""
    from scripts import evaluate_simulation_benchmark as benchmark

    _, response_index, responses_root = response_bundle
    expected_paths = {
        record["relative_path"] for record in response_index["records"]
    }
    handles, descriptors = _track_windows_response_resources(monkeypatch, benchmark)
    compared_snapshot_sizes = []
    injected_descriptors = ()
    injection_checks_completed = False
    marker = "MARKER-WINDOWS-COMPARATOR-DO-NOT-DISCLOSE"

    def fail_comparison(first, second):
        nonlocal injected_descriptors, injection_checks_completed
        compared_snapshot_sizes.append((len(first), len(second)))
        injected_descriptors = tuple(
            opened.descriptor for opened in (*first.values(), *second.values())
        )
        _assert_live_unique_descriptors_at_injection(injected_descriptors, 144)
        injection_checks_completed = True
        raise RuntimeError(marker)

    monkeypatch.setattr(benchmark, "_windows_same_opened_tree", fail_comparison)
    failure = None
    try:
        benchmark._windows_verified_descriptors(responses_root, expected_paths)
    except Exception as error:
        failure = error
    live_handles, live_descriptors = _live_windows_response_resources(
        benchmark, handles, injected_descriptors
    )
    try:
        assert len(expected_paths) == 72
        assert compared_snapshot_sizes == [(72, 72)]
        assert injection_checks_completed
        assert len(injected_descriptors) == 144
        assert len(set(injected_descriptors)) == 144
        assert len(descriptors) == 144
        assert set(descriptors) == set(injected_descriptors)
        assert type(failure) is ValueError
        assert str(failure) == "invalid response files"
        assert marker not in str(failure)
        assert live_descriptors == []
        assert live_handles == []
    finally:
        for descriptor in live_descriptors:
            os.close(descriptor)
        for handle in live_handles:
            benchmark._windows_close_handle(handle)


@pytest.mark.skipif(os.name != "nt", reason="Windows HANDLE ownership contract")
def test_windows_snapshot_base_exception_cleans_both_and_propagates_unchanged(
    response_bundle, monkeypatch
):
    """A non-Exception sentinel is re-raised only after both snapshots are closed."""
    from scripts import evaluate_simulation_benchmark as benchmark

    class OwnershipProbe(BaseException):
        pass

    _, response_index, responses_root = response_bundle
    expected_paths = {
        record["relative_path"] for record in response_index["records"]
    }
    handles, descriptors = _track_windows_response_resources(monkeypatch, benchmark)
    compared_snapshot_sizes = []
    injected_descriptors = ()
    injection_checks_completed = False
    sentinel = OwnershipProbe()

    def interrupt_comparison(first, second):
        nonlocal injected_descriptors, injection_checks_completed
        compared_snapshot_sizes.append((len(first), len(second)))
        injected_descriptors = tuple(
            opened.descriptor for opened in (*first.values(), *second.values())
        )
        _assert_live_unique_descriptors_at_injection(injected_descriptors, 144)
        injection_checks_completed = True
        raise sentinel

    monkeypatch.setattr(benchmark, "_windows_same_opened_tree", interrupt_comparison)
    with pytest.raises(OwnershipProbe) as caught:
        benchmark._windows_verified_descriptors(responses_root, expected_paths)
    live_handles, live_descriptors = _live_windows_response_resources(
        benchmark, handles, injected_descriptors
    )
    try:
        assert caught.value is sentinel
        assert len(expected_paths) == 72
        assert compared_snapshot_sizes == [(72, 72)]
        assert injection_checks_completed
        assert len(injected_descriptors) == 144
        assert len(set(injected_descriptors)) == 144
        assert len(descriptors) == 144
        assert set(descriptors) == set(injected_descriptors)
        assert live_descriptors == []
        assert live_handles == []
    finally:
        for descriptor in live_descriptors:
            os.close(descriptor)
        for handle in live_handles:
            benchmark._windows_close_handle(handle)


@pytest.mark.skipif(os.name != "nt", reason="Windows HANDLE ownership contract")
def test_windows_success_closes_all_transferred_descriptors_and_handles(
    response_bundle, monkeypatch
):
    from scripts import evaluate_simulation_benchmark as benchmark

    plan, response_index, responses_root = response_bundle
    handles, descriptors = _track_windows_response_resources(monkeypatch, benchmark)

    cells = load_response_cells(plan, response_index, responses_root)
    live_handles, live_descriptors = _live_windows_response_resources(
        benchmark, handles, descriptors
    )
    try:
        assert len(cells) == 72
        assert descriptors
        assert handles
        assert live_descriptors == []
        assert live_handles == []
    finally:
        for descriptor in live_descriptors:
            os.close(descriptor)
        for handle in live_handles:
            benchmark._windows_close_handle(handle)


def test_response_loader_rejects_hardlink_aliases_between_cells(response_bundle):
    plan, response_index, responses_root = response_bundle
    first = responses_root / response_index["records"][0]["relative_path"]
    second = responses_root / response_index["records"][1]["relative_path"]
    second.unlink()
    try:
        os.link(first, second)
    except OSError:
        pytest.skip("the current filesystem cannot create hardlinks")
    _update_record_for_bytes(response_index, 1, first.read_bytes())

    with pytest.raises(ValueError, match="invalid response files"):
        load_response_cells(plan, response_index, responses_root)


def test_response_loader_accepts_identical_bytes_in_distinct_regular_files(
    response_bundle,
):
    plan, response_index, responses_root = response_bundle
    first = responses_root / response_index["records"][0]["relative_path"]
    second = responses_root / response_index["records"][1]["relative_path"]
    content = first.read_bytes()
    second.write_bytes(content)
    _update_record_for_bytes(response_index, 1, content)
    first_identity = (first.stat().st_dev, first.stat().st_ino)
    second_identity = (second.stat().st_dev, second.stat().st_ino)
    if first_identity == second_identity:
        pytest.skip("the current filesystem does not expose distinct file identities")

    cells = load_response_cells(plan, response_index, responses_root)

    assert cells[0]["text"] == cells[1]["text"]


@pytest.mark.parametrize("mismatch", ["size", "digest"])
def test_response_loader_rejects_size_or_digest_mismatch(mismatch, response_bundle):
    plan, response_index, responses_root = response_bundle
    if mismatch == "size":
        response_index["records"][0]["size"] += 1
    else:
        response_index["records"][0]["response_sha256"] = "0" * 64

    with pytest.raises(ValueError, match="invalid response files"):
        load_response_cells(plan, response_index, responses_root)


def test_response_loader_rejects_invalid_utf8(response_bundle):
    plan, response_index, responses_root = response_bundle
    response_path = responses_root / response_index["records"][0]["relative_path"]
    content = b"\xff\xfe"
    response_path.write_bytes(content)
    _update_record_for_bytes(response_index, 0, content)

    with pytest.raises(ValueError, match="invalid response files"):
        load_response_cells(plan, response_index, responses_root)


def test_response_loader_rejects_a_repository_internal_response_root(response_bundle):
    plan, response_index, _ = response_bundle

    with pytest.raises(ValueError, match="invalid response files"):
        load_response_cells(plan, response_index, ROOT / "evals")


def test_response_index_template_is_closed_unpopulated_and_invalid(benchmark_plan):
    template = json.loads(RESPONSE_INDEX_TEMPLATE.read_text(encoding="utf-8"))

    assert set(template) == {
        "schema_version",
        "plan_sha256",
        "execution_attestation",
        "records",
    }
    assert template["schema_version"] == "1"
    assert template["plan_sha256"] is None
    assert template["records"] == []
    assert template["execution_attestation"] == {
        "completed_at": None,
        "model_provider": None,
        "model_id": None,
        "model_snapshot": None,
        "runner_name": None,
        "runner_version": None,
        "plan_followed": False,
        "fresh_sessions": False,
        "offline": False,
        "shared_configuration_unchanged": False,
    }
    assert validate_response_index(template, benchmark_plan)
    serialized = RESPONSE_INDEX_TEMPLATE.read_bytes()
    assert b"relative_path" not in serialized
    assert b"response_sha256" not in serialized


def test_complete_pairs_compute_exact_aggregate_counts(benchmark_plan):
    summary = evaluate_benchmark(
        benchmark_plan,
        _cells_for_pattern(benchmark_plan, "positive"),
        _valid_execution_attestation(benchmark_plan),
    )

    assert summary["status"] == "benchmark-observed"
    assert summary["cell_counts"] == {"expected": 72, "observed": 72}
    assert summary["paired_counts"] == {
        "both_fail": 0,
        "both_pass": 24,
        "improved": 12,
        "worsened": 0,
    }
    assert summary["overall"] == {
        "control_passes": 24,
        "control_pass_rate": 0.666667,
        "difference": 0.333333,
        "intervention_passes": 36,
        "intervention_pass_rate": 1.0,
        "pairs": 36,
    }
    assert summary["direction"] == "positive-signal"
    assert summary["case_results"][0]["stability"] == {
        "control": "stable-fail",
        "intervention": "stable-pass",
    }
    assert validate_benchmark_summary(summary) == []


@pytest.mark.parametrize(
    ("difference", "expected"),
    [
        (Fraction(1, 5), "positive-signal"),
        (Fraction(1, 5) - Fraction(1, 10_000), "mixed-or-null"),
    ],
)
def test_direction_uses_the_exact_practical_threshold(difference, expected):
    assert (
        classify_direction(
            difference,
            improved=8,
            worsened=0,
            control_forbidden=0,
            intervention_forbidden=0,
            depth_differences=(Fraction(0),),
        )
        == expected
    )


@pytest.mark.parametrize(
    ("pattern", "expected_direction", "expected_difference"),
    [
        ("boundary-7", "mixed-or-null", 0.194444),
        ("boundary-8", "positive-signal", 0.222222),
        ("equal-discordance", "mixed-or-null", 0.0),
        ("intervention-forbidden", "negative-signal", 0.222222),
        ("negative-depth", "negative-signal", 0.222222),
    ],
)
def test_complete_aggregate_direction_guardrails(
    benchmark_plan, pattern, expected_direction, expected_difference
):
    summary = evaluate_benchmark(
        benchmark_plan,
        _cells_for_pattern(benchmark_plan, pattern),
        _valid_execution_attestation(benchmark_plan),
    )

    assert summary["direction"] == expected_direction
    assert summary["overall"]["difference"] == expected_difference
    if pattern == "equal-discordance":
        assert summary["paired_counts"]["improved"] == 1
        assert summary["paired_counts"]["worsened"] == 1
    elif pattern == "intervention-forbidden":
        assert summary["forbidden_violations"] == {
            "control": 0,
            "intervention": 1,
        }
    elif pattern == "negative-depth":
        assert any(
            row["difference"] < 0 for row in summary["output_depth_results"]
        )
    assert validate_benchmark_summary(summary) == []


@pytest.mark.parametrize(
    ("pattern", "expected_direction"),
    [
        ("positive", "positive-signal"),
        ("mixed", "mixed-or-null"),
        ("negative", "negative-signal"),
    ],
)
def test_complete_generated_scenarios_have_exact_direction(
    benchmark_plan, pattern, expected_direction
):
    summary = evaluate_benchmark(
        benchmark_plan,
        _cells_for_pattern(benchmark_plan, pattern),
        _valid_execution_attestation(benchmark_plan),
    )

    assert summary["status"] == "benchmark-observed"
    assert summary["direction"] == expected_direction


def test_evaluate_calls_the_existing_evaluator_once_per_bound_cell(
    benchmark_plan, monkeypatch
):
    from scripts import evaluate_simulation_benchmark as benchmark

    cells = _cells_for_pattern(benchmark_plan, "mixed")
    catalog, rubric = load_catalog(
        ROOT / "evals/cases.yaml", ROOT / "evals/rubric.yaml"
    )
    cases = {case["id"]: case for case in catalog["cases"]}
    calls = []
    real_evaluate_response = benchmark.evaluate_response

    def evaluate_spy(case, bound_rubric, response):
        calls.append((case, bound_rubric, response))
        return real_evaluate_response(case, bound_rubric, response)

    monkeypatch.setattr(benchmark, "evaluate_response", evaluate_spy)
    evaluate_benchmark(
        benchmark_plan,
        cells,
        _valid_execution_attestation(benchmark_plan),
    )

    assert len(calls) == 72
    assert [case["id"] for case, _, _ in calls] == [
        cell["case_id"] for cell in cells
    ]
    assert all(case == cases[case["id"]] for case, _, _ in calls)
    assert all(bound_rubric == rubric for _, bound_rubric, _ in calls)
    assert [response for _, _, response in calls] == [cell["text"] for cell in cells]


def test_summary_is_closed_recomputable_and_contains_no_response_material(
    benchmark_plan
):
    summary = evaluate_benchmark(
        benchmark_plan,
        _cells_for_pattern(benchmark_plan, "positive"),
        _valid_execution_attestation(benchmark_plan),
    )
    serialized = canonical_summary_bytes(summary)

    assert json.loads(serialized) == summary
    assert serialized == canonical_json_bytes(summary)
    assert summary["synthetic_example"] is False
    assert summary["execution_attestation"]["assertion_basis"] == "externally-asserted"
    assert b"response-" not in serialized
    assert b"relative_path" not in serialized
    assert b'"text"' not in serialized
    assert b'"score"' not in serialized
    assert b"human-effective" not in serialized
    assert b"evaluation-green" not in serialized


def test_synthetic_summary_is_rejected_by_default_and_cannot_be_canonicalized(
    benchmark_plan,
):
    summary = evaluate_benchmark(
        benchmark_plan,
        _cells_for_pattern(benchmark_plan, "mixed"),
        _valid_execution_attestation(benchmark_plan),
    )
    summary["synthetic_example"] = True

    assert validate_benchmark_summary(summary)
    with pytest.raises(ValueError, match="invalid benchmark summary"):
        canonical_summary_bytes(summary)


def test_synthetic_summary_is_accepted_only_with_explicit_validation_opt_in(
    benchmark_plan,
):
    summary = evaluate_benchmark(
        benchmark_plan,
        _cells_for_pattern(benchmark_plan, "mixed"),
        _valid_execution_attestation(benchmark_plan),
    )
    summary["synthetic_example"] = True

    assert validate_benchmark_summary(summary, allow_synthetic=True) == []


@pytest.mark.parametrize("value", [0, 1, None, "false"])
def test_summary_synthetic_marker_must_be_a_literal_boolean_in_both_modes(
    benchmark_plan, value
):
    summary = evaluate_benchmark(
        benchmark_plan,
        _cells_for_pattern(benchmark_plan, "mixed"),
        _valid_execution_attestation(benchmark_plan),
    )
    summary["synthetic_example"] = value

    assert validate_benchmark_summary(summary)
    assert validate_benchmark_summary(summary, allow_synthetic=True)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda summary: summary.update({"evaluation_green": True}),
        lambda summary: summary["overall"].update({"difference": 0.9}),
        lambda summary: summary["paired_counts"].update({"both_pass": 0}),
        lambda summary: summary["output_depth_results"][0].update(
            {"difference": -0.5}
        ),
        lambda summary: summary["case_results"][0]["stability"].update(
            {"intervention": "stable-pass"}
        ),
        lambda summary: summary.update({"direction": "positive-signal"}),
    ],
)
def test_summary_validation_recomputes_derived_fields_and_rejects_unknown_keys(
    benchmark_plan, mutation
):
    summary = evaluate_benchmark(
        benchmark_plan,
        _cells_for_pattern(benchmark_plan, "negative"),
        _valid_execution_attestation(benchmark_plan),
    )
    mutation(summary)

    assert validate_benchmark_summary(summary)
    assert validate_benchmark_summary(summary, allow_synthetic=True)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda summary: summary.update({"repeats": "3"}),
        lambda summary: summary.update({"direction": []}),
        lambda summary: summary.update({"benchmark_id": "../private-run"}),
        lambda summary: summary["model"].update({"top_p": float("nan")}),
        lambda summary: summary["skill"].update({"archive": "../private.zip"}),
        lambda summary: summary["execution_attestation"].update(
            {"runner_name": "../private-runner"}
        ),
        lambda summary: summary["case_results"][0].update(
            {"paired_counts": None}
        ),
        lambda summary: summary.update({"output_depth_results": None}),
    ],
)
def test_summary_validation_fails_closed_for_malformed_value_types(
    benchmark_plan, mutation
):
    summary = evaluate_benchmark(
        benchmark_plan,
        _cells_for_pattern(benchmark_plan, "mixed"),
        _valid_execution_attestation(benchmark_plan),
    )
    mutation(summary)

    assert validate_benchmark_summary(summary)
    assert validate_benchmark_summary(summary, allow_synthetic=True)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("model_provider",), "drifted-provider"),
        (("runner_version",), "drifted-runner"),
        (("offline",), False),
        (("unknown",), True),
    ],
)
def test_evaluate_rejects_execution_attestation_drift_or_expansion(
    benchmark_plan, path, value
):
    attestation = _valid_execution_attestation(benchmark_plan)
    attestation[path[0]] = value

    with pytest.raises(ValueError, match="invalid execution attestation"):
        evaluate_benchmark(
            benchmark_plan,
            _cells_for_pattern(benchmark_plan, "mixed"),
            attestation,
        )


EVALUATE_ERROR = b"simulation benchmark evaluation failed\n"
EVALUATE_SUCCESS = b'{"schema_version":"1","status":"benchmark-observed"}\n'


def _evaluation_command(
    plan_path: Path,
    response_index_path: Path,
    responses_root: Path,
    output: Path,
) -> list[str]:
    return [
        sys.executable,
        str(ROOT / "scripts" / "evaluate_simulation_benchmark.py"),
        "--plan",
        str(plan_path),
        "--response-index",
        str(response_index_path),
        "--responses-dir",
        str(responses_root),
        "--output-summary",
        str(output),
    ]


def _external_evaluation_bundle(
    tmp_path: Path,
) -> tuple[dict, dict, Path, Path, Path, Path]:
    plan = valid_plan(tmp_path / "plan-build")
    response_index, responses_root = _response_bundle(
        plan, tmp_path / "responses"
    )
    plan_path = tmp_path / "benchmark-plan.json"
    response_index_path = tmp_path / "response-index.json"
    output = tmp_path / "benchmark-summary.json"
    plan_path.write_bytes(canonical_json_bytes(plan))
    response_index_path.write_bytes(canonical_json_bytes(response_index))
    return (
        plan,
        response_index,
        responses_root,
        plan_path,
        response_index_path,
        output,
    )


def _run_evaluation_bundle(
    bundle: tuple[dict, dict, Path, Path, Path, Path],
    *,
    output: Path | None = None,
    extra_arguments: list[str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    _, _, responses_root, plan_path, response_index_path, default_output = bundle
    return subprocess.run(
        _evaluation_command(
            plan_path,
            response_index_path,
            responses_root,
            output or default_output,
        )
        + (extra_arguments or []),
        cwd=ROOT,
        capture_output=True,
        check=False,
    )


def test_evaluate_cli_writes_only_a_canonical_complete_summary(tmp_path):
    """A successful run must not expose aggregate details on the process stream."""
    bundle = _external_evaluation_bundle(tmp_path)
    _, _, _, _, _, output = bundle

    completed = _run_evaluation_bundle(bundle)

    assert completed.returncode == 0
    assert completed.stdout == EVALUATE_SUCCESS
    assert completed.stderr == b""
    summary_bytes = output.read_bytes()
    summary = json.loads(summary_bytes)
    assert summary_bytes == canonical_json_bytes(summary)
    assert validate_benchmark_summary(summary) == []
    assert summary["status"] == "benchmark-observed"
    assert summary["synthetic_example"] is False


def test_evaluate_cli_reports_only_a_valid_canonical_prefix_as_incomplete(tmp_path):
    """A trailing omission must not be scored or materialized as a summary."""
    bundle = _external_evaluation_bundle(tmp_path)
    _, response_index, _, _, response_index_path, output = bundle
    response_index["records"] = response_index["records"][:-1]
    response_index_path.write_bytes(canonical_json_bytes(response_index))

    completed = _run_evaluation_bundle(bundle)

    assert completed.returncode == 3
    assert completed.stdout == (
        b'{"expected_count":72,"observed_count":71,"schema_version":"1",'
        b'"status":"benchmark-incomplete"}\n'
    )
    assert completed.stderr == b""
    assert not output.exists()


@pytest.mark.parametrize(
    "mutation",
    ["invalid-json", "extra-file", "duplicate-record", "digest-mismatch", "unsafe-path"],
)
def test_evaluate_cli_maps_malformed_or_unsafe_bundles_to_one_error_shape(
    tmp_path, mutation
):
    """Dynamic parser and validation failures must never become an output channel."""
    bundle = _external_evaluation_bundle(tmp_path)
    _, response_index, responses_root, _, response_index_path, output = bundle
    if mutation == "invalid-json":
        response_index_path.write_bytes(b'{"MARKER-INVALID-JSON":')
    elif mutation == "extra-file":
        (responses_root / "unexpected.md").write_bytes(b"extra\n")
    elif mutation == "duplicate-record":
        response_index["records"].append(deepcopy(response_index["records"][0]))
        response_index_path.write_bytes(canonical_json_bytes(response_index))
    elif mutation == "digest-mismatch":
        response_index["plan_sha256"] = "0" * 64
        response_index_path.write_bytes(canonical_json_bytes(response_index))
    else:
        response_index["records"][0]["relative_path"] = "../unsafe.md"
        response_index_path.write_bytes(canonical_json_bytes(response_index))

    completed = _run_evaluation_bundle(bundle)

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr == EVALUATE_ERROR
    assert not output.exists()


@pytest.mark.parametrize(
    ("flag", "abbreviation"),
    [
        ("--plan", "--pla"),
        ("--response-index", "--response-ind"),
        ("--responses-dir", "--responses-d"),
        ("--output-summary", "--output-sum"),
    ],
)
def test_evaluate_cli_rejects_every_abbreviated_flag(tmp_path, flag, abbreviation):
    """An abbreviated spelling would silently widen the closed CLI contract."""
    bundle = _external_evaluation_bundle(tmp_path)
    _, _, responses_root, plan_path, response_index_path, output = bundle
    command = _evaluation_command(
        plan_path, response_index_path, responses_root, output
    )
    command[command.index(flag)] = abbreviation

    completed = subprocess.run(
        command, cwd=ROOT, capture_output=True, check=False
    )

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr == EVALUATE_ERROR
    assert not output.exists()


@pytest.mark.parametrize("help_option", ["-h", "--help"])
def test_evaluate_cli_rejects_help_without_a_second_output_shape(help_option):
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "evaluate_simulation_benchmark.py"),
            help_option,
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr == EVALUATE_ERROR


def test_evaluate_cli_rejects_duplicate_flags(tmp_path):
    """Accepting a second value would make the effective input ambiguous."""
    bundle = _external_evaluation_bundle(tmp_path)
    _, _, _, plan_path, _, output = bundle

    completed = _run_evaluation_bundle(
        bundle, extra_arguments=["--plan", str(plan_path)]
    )

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr == EVALUATE_ERROR
    assert not output.exists()


@pytest.mark.parametrize("source", ["response", "metadata", "filename", "json"])
def test_evaluate_cli_never_discloses_untrusted_markers(tmp_path, source):
    marker = f"MARKER-{source.upper()}-DO-NOT-DISCLOSE"
    bundle = _external_evaluation_bundle(tmp_path)
    plan, response_index, responses_root, plan_path, response_index_path, _ = bundle
    if source == "response":
        response_path = responses_root / response_index["records"][0]["relative_path"]
        content = marker.encode("utf-8")
        response_path.write_bytes(content)
        _update_record_for_bytes(response_index, 0, content)
        response_index_path.write_bytes(canonical_json_bytes(response_index))
    elif source == "metadata":
        plan["model"]["unexpected"] = marker
        plan_path.write_bytes(canonical_json_bytes(plan))
    elif source == "filename":
        (responses_root / f"{marker}.md").write_bytes(b"extra\n")
    else:
        response_index_path.write_bytes((f'{{"value":"{marker}"').encode())

    completed = _run_evaluation_bundle(bundle)

    assert marker.encode() not in completed.stdout + completed.stderr
    if source == "response":
        assert completed.returncode == 0
        assert completed.stdout == EVALUATE_SUCCESS
        assert completed.stderr == b""
    else:
        assert completed.returncode == 2
        assert completed.stdout == b""
        assert completed.stderr == EVALUATE_ERROR


@pytest.mark.parametrize("alias_kind", ["spelling", "resolution", "symlink", "hardlink"])
def test_evaluate_cli_rejects_output_aliases_without_modifying_inputs(
    tmp_path, alias_kind
):
    """Replacing an aliased output could corrupt the evidence it is evaluating."""
    bundle = _external_evaluation_bundle(tmp_path)
    _, _, _, plan_path, _, _ = bundle
    original = plan_path.read_bytes()
    if alias_kind == "spelling":
        output = plan_path
    elif alias_kind == "resolution":
        output = plan_path.parent / "unused" / ".." / plan_path.name
    elif alias_kind == "symlink":
        output = tmp_path / "summary-link.json"
        _make_symlink(plan_path, output)
    else:
        output = tmp_path / "summary-hardlink.json"
        try:
            os.link(plan_path, output)
        except OSError:
            pytest.skip("the current filesystem cannot create hardlinks")

    completed = _run_evaluation_bundle(bundle, output=output)

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr == EVALUATE_ERROR
    assert plan_path.read_bytes() == original
    assert output.exists()
    assert output.read_bytes() == original


def test_evaluate_cli_rejects_an_output_hardlinked_to_a_response(tmp_path):
    """Response cells are inputs even though they are reached through a directory."""
    bundle = _external_evaluation_bundle(tmp_path)
    _, response_index, responses_root, _, _, _ = bundle
    response = responses_root / response_index["records"][0]["relative_path"]
    original = response.read_bytes()
    output = tmp_path / "summary-hardlink.json"
    try:
        os.link(response, output)
    except OSError:
        pytest.skip("the current filesystem cannot create hardlinks")

    completed = _run_evaluation_bundle(bundle, output=output)

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr == EVALUATE_ERROR
    assert response.read_bytes() == original
    assert output.read_bytes() == original


def test_evaluate_cli_rejects_output_inside_the_response_tree(tmp_path):
    """Staging inside an input tree would mutate the evidence directory."""
    bundle = _external_evaluation_bundle(tmp_path)
    _, _, responses_root, _, _, _ = bundle
    output = responses_root / "benchmark-summary.json"

    completed = _run_evaluation_bundle(bundle, output=output)

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr == EVALUATE_ERROR
    assert not output.exists()


def test_evaluate_cli_failure_preserves_existing_output_and_all_inputs(tmp_path):
    """A failed run must be observationally read-only outside transient staging."""
    bundle = _external_evaluation_bundle(tmp_path)
    _, _, responses_root, plan_path, response_index_path, output = bundle
    previous = b"previous-valid-summary\n"
    output.write_bytes(previous)
    response_index_path.write_bytes(b'{"MARKER-INVALID-JSON":')
    before = {
        path: path.read_bytes()
        for path in (plan_path, response_index_path, *sorted(responses_root.iterdir()))
    }

    completed = _run_evaluation_bundle(bundle)

    assert completed.returncode == 2
    assert completed.stdout == b""
    assert completed.stderr == EVALUATE_ERROR
    assert output.read_bytes() == previous
    assert {
        path: path.read_bytes()
        for path in (plan_path, response_index_path, *sorted(responses_root.iterdir()))
    } == before
    assert not list(tmp_path.glob(f".{output.name}.*.tmp"))
