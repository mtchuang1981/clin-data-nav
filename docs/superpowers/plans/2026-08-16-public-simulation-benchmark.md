# ClinNav Public Simulation Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a provider-neutral, fail-closed public simulation benchmark that compares all twelve deterministic Eval cases without and with an exact released `clin-nav` bundle, validates a complete 72-response external run, and renders aggregate bilingual evidence without claiming human effectiveness.

**Architecture:** Extend deterministic Skill packaging so an annotated historical release tag can be reproduced and matched to a committed public binding. Add a closed plan generator, response-index validator, existing-evaluator orchestration, aggregate classifier, and bilingual renderer; keep actual run files outside Git and add only safe public templates, synthetic examples, Issue Forms, and scanner rules.

**Tech Stack:** Python 3.11, pytest, PyYAML, JSON, SHA-256, Git plumbing commands, Markdown, GitHub Issue Forms, PowerShell verification.

## Global Constraints

- Target capability is a `v0.6.0` candidate; the first normative campaign evaluates the released `clin-nav` `v0.5.0` bundle.
- The normative layout is exactly twelve cases, two conditions, three repeats, and 72 response cells.
- Each cell uses a fresh session; the first normative campaign is offline, has no network or external retrieval, and follows seed-balanced condition order.
- The only treatment difference is exact `clin-nav` availability and `$clin-nav` invocation in `intervention`.
- CI, tests, and repository scripts never call a model and never accept or read credentials.
- Actual benchmark plans, indexes, responses, provider logs, generated reports, and community source material remain outside Git.
- Reuse `scripts.evaluate_response.load_catalog` and `evaluate_response`; do not copy evaluator rules or pass logic.
- Primary analysis is paired contract pass-rate difference. Do not average case raw scores across cases.
- `positive-signal` requires at least `0.20` absolute improvement, more improved than worsened pairs, zero intervention forbidden violations, and no negative output-depth stratum.
- A complete result is `benchmark-observed`; no input may claim or force a status, direction, `human-effective`, or `evaluation-green`.
- The benchmark performs no human-study power analysis and makes no clinical, causal, patient-outcome, usability, or deployment claim.
- All external paths fail closed on repository containment, traversal, symlink/reparse escape, hardlink alias, and input/output aliasing.
- Errors are content-free and never echo model metadata, response text, external paths, hashes, or exception strings.
- Add a failing test before every production behavior change. Use only generated synthetic responses and unique external temporary directories.
- Before completion run the four repository gates, all three renderer checks, a complete diff review, and the same suite on official Python 3.11.9.
- Do not push, create or move a tag, dispatch a workflow, or publish a Release under this plan.

## File Map

| Responsibility | Files |
|---|---|
| Historical deterministic packaging | Modify `scripts/package_skill.py`; modify `tests/test_packaging.py` |
| Public release byte binding and plan contract | Create `evals/benchmark/released-skill-bindings.json`, `evals/benchmark/benchmark-plan-template.json`, `scripts/prepare_simulation_benchmark.py`, `tests/test_simulation_benchmark.py` |
| Response index and evaluator orchestration | Create `evals/benchmark/response-index-template.json`, `scripts/evaluate_simulation_benchmark.py`; modify `tests/test_simulation_benchmark.py` |
| Bilingual report | Create `scripts/render_simulation_benchmark.py`, `evals/benchmark/summary-schema.md`, `evals/benchmark/report-template.md`, `evals/benchmark/report-template.zh-TW.md`, and three files under `evals/benchmark/examples/`; create `tests/test_simulation_benchmark_reports.py` |
| Guidance and community feedback | Create `evals/benchmark/README.md`, `.github/ISSUE_TEMPLATE/benchmark-result.yml`, `.github/ISSUE_TEMPLATE/usability-feedback.yml`; modify `evals/README.md`, `README.md`, `README.zh-TW.md` |
| Public-boundary enforcement | Modify `scripts/check_public_boundary.py`, `tests/test_public_boundary.py`, `tests/test_project_metadata.py` |
| `v0.6.0` candidate metadata | Modify `pyproject.toml`, `scripts/package_skill.py`, `.github/workflows/release.yml`, `CHANGELOG.md`, `CHANGELOG.zh-TW.md`, `CITATION.cff`, `docs/releases/0.6.0.md`, and metadata/packaging tests |

---

### Task 1: Parameterize Deterministic Skill Packaging

**Files:**
- Modify: `scripts/package_skill.py:20-113`
- Modify: `tests/test_packaging.py`

**Interfaces:**
- Consumes: existing `build_package(skill_dir: Path, output_dir: Path) -> PackageResult` callers.
- Produces: backward-compatible `build_package(skill_dir: Path, output_dir: Path, *, package_version: str = PACKAGE_VERSION) -> PackageResult` whose archive and manifest names derive from `package_version`.

- [ ] **Step 1: Write the failing version-override tests**

Add tests that preserve default bytes and prove a historical version can be built without mutating module constants:

```python
def test_build_package_accepts_an_explicit_historical_version(tmp_path):
    result = build_package(SKILL, tmp_path, package_version="0.5.0")
    manifest = json.loads(result.manifest.read_text(encoding="utf-8"))

    assert result.archive.name == "clin-nav-0.5.0.zip"
    assert result.manifest.name == "clin-nav-0.5.0.manifest.json"
    assert manifest["archive"] == result.archive.name
    assert manifest["version"] == "0.5.0"


def test_default_package_call_retains_module_version_and_bytes(tmp_path):
    default_dir = tmp_path / "default"
    explicit_dir = tmp_path / "explicit"
    default = build_package(SKILL, default_dir)
    explicit = build_package(
        SKILL,
        explicit_dir,
        package_version=PACKAGE_VERSION,
    )

    assert default.archive.read_bytes() == explicit.archive.read_bytes()
    assert default.manifest.read_bytes() == explicit.manifest.read_bytes()
```

Add parameterized invalid versions for `"v0.5.0"`, `"0.5"`, `"0.5.0/zip"`, an empty string, and a boolean. Require `ValueError` before output creation.

- [ ] **Step 2: Run the exact tests and verify RED**

Run:

```text
python -m pytest -q tests/test_packaging.py::test_build_package_accepts_an_explicit_historical_version tests/test_packaging.py::test_default_package_call_retains_module_version_and_bytes
```

Expected: both fail because `build_package()` does not accept `package_version`.

- [ ] **Step 3: Implement the minimal backward-compatible parameter**

Add a strict semantic-version regex and derive names inside `build_package()`:

```python
SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


def _package_names(package_version: str) -> tuple[str, str]:
    if not isinstance(package_version, str) or SEMVER.fullmatch(package_version) is None:
        raise ValueError("package version must be X.Y.Z")
    return (
        f"{SKILL_NAME}-{package_version}.zip",
        f"{SKILL_NAME}-{package_version}.manifest.json",
    )
```

Use the returned local names for the archive path, manifest path,
`manifest_data["archive"]`, and `manifest_data["version"]`. Keep
`ARCHIVE_NAME` and `MANIFEST_NAME` as the default-version public constants.

- [ ] **Step 4: Verify GREEN and package compatibility**

Run:

```text
python -m pytest -q tests/test_packaging.py
python scripts/package_skill.py --check-reproducible
git diff --check
```

Require all exit codes `0` and no default artifact digest change.

- [ ] **Step 5: Commit Task 1**

```text
git add -- scripts/package_skill.py tests/test_packaging.py
git commit -m "refactor: parameterize deterministic Skill packaging"
```

---

### Task 2: Bind a Frozen Plan to the Published v0.5.0 Skill

**Files:**
- Create: `evals/benchmark/released-skill-bindings.json`
- Create: `evals/benchmark/benchmark-plan-template.json`
- Create: `scripts/prepare_simulation_benchmark.py`
- Create: `tests/test_simulation_benchmark.py`

**Interfaces:**
- Consumes: `package_skill.build_package`, `evaluate_response.load_catalog`, local Git objects, and the committed v0.5.0 publication identity.
- Produces: `canonical_json_bytes(value: object) -> bytes`, `load_released_skill_bindings(path: Path) -> dict`, `resolve_released_skill_binding(root: Path, tag: str, temporary_root: Path) -> dict`, `balanced_cells(case_ids: tuple[str, ...], repeats: int, seed: int) -> tuple[dict, ...]`, `build_benchmark_plan(...) -> dict`, and `validate_benchmark_plan(payload: object) -> list[str]`.

- [ ] **Step 1: Write failing registry and plan tests**

Create tests with these exact public v0.5.0 values:

```python
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
```

Require the registry to have exact root keys `schema_version,releases`, exactly
one release, and the release keys above in sorted canonical JSON. Add:

```python
def test_v050_registry_matches_rebuilt_annotated_tag(tmp_path):
    observed = resolve_released_skill_binding(ROOT, "v0.5.0", tmp_path)
    assert observed == V050_BINDING


def test_plan_has_complete_seed_balanced_layout(tmp_path):
    plan = valid_plan(tmp_path, repeats=3, seed=20260816)
    cells = plan["cells"]

    assert len(cells) == 72
    assert [cell["sequence"] for cell in cells] == list(range(1, 73))
    assert len({(c["case_id"], c["repeat"], c["condition"]) for c in cells}) == 72
    first_conditions = [cells[index]["condition"] for index in range(0, 72, 2)]
    assert first_conditions.count("control") == 18
    assert first_conditions.count("intervention") == 18
```

Add mutations for every registry and plan key, tag type, tag object, peeled
commit, archive/manifest/member digest, catalog/rubric hash, case order,
condition definition, repeat count, cell count/order/uniqueness, seed,
fresh-session boolean, network policy, timestamps, numeric model parameters,
and attempted keys `status`, `direction`, `human_effective`, `evaluation_green`,
`api_key`, `token`, and `credential`.

- [ ] **Step 2: Run focused tests and verify RED**

Expected: collection errors because the new module and public files do not
exist.

- [ ] **Step 3: Create the closed release registry**

Write canonical JSON containing `schema_version: "1"` and the exact
`V050_BINDING`. No URL, path, free text, or mutable latest-release alias is
allowed.

- [ ] **Step 4: Implement historical tag materialization and package binding**

Use only argument-array Git subprocesses with `check=True` and captured output:

```python
def _git(root: Path, *args: str, text: bool = True) -> str | bytes:
    completed = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=text,
    )
    return completed.stdout
```

Require `git cat-file -t tag` to be exactly `tag`, resolve the tag object and
`tag^{}` commit, enumerate only `skills/clin-nav/**` with `git ls-tree`, reject
unsafe or duplicate paths, and write `git show tag:path` bytes under the
unique temporary root. Build the materialized tree with
`build_package(..., package_version="0.5.0")`, hash archive and manifest bytes,
and hash canonical `manifest["files"]` as `member_set_sha256`. Compare the whole
observed mapping to the registry before returning it. No network call occurs.

- [ ] **Step 5: Implement canonical plan generation and validation**

Define exact nested key sets and controlled values. Generate balanced cells by
shuffling the 36 `(case_id, repeat)` pairs using `random.Random(seed)` and
alternating condition order:

```python
pairs = [(case_id, repeat) for case_id in case_ids for repeat in range(1, repeats + 1)]
random.Random(seed).shuffle(pairs)
cells = []
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
```

Require `repeats == 3`, network policy `offline`, fresh session `True`, Skill
invocation `None` for control and `$clin-nav` for intervention, exact catalog
case order, aware UTC creation time, finite numeric parameters, and lowercase
64-character digests. `canonical_json_bytes()` uses UTF-8, sorted keys,
`separators=(",", ":")`, and one final newline.

- [ ] **Step 6: Create the incomplete public plan template**

The template has every exact schema key, fixed policies and conditions, and
`null` only for values that a user must supply. Tests require it to be
documentation-only and rejected by `validate_benchmark_plan()` until populated.
It must not contain a real provider, model, system prompt, credential, or run
identity.

- [ ] **Step 7: Verify GREEN and commit Task 2**

Run:

```text
python -m pytest -q tests/test_simulation_benchmark.py
python scripts/check_public_boundary.py
git diff --check
```

Then commit only Task 2 files:

```text
git add -- evals/benchmark/released-skill-bindings.json evals/benchmark/benchmark-plan-template.json scripts/prepare_simulation_benchmark.py tests/test_simulation_benchmark.py
git commit -m "feat: freeze public simulation benchmark plans"
```

---

### Task 3: Add the Content-Free Plan Preparation CLI

**Files:**
- Modify: `scripts/prepare_simulation_benchmark.py`
- Modify: `tests/test_simulation_benchmark.py`

**Interfaces:**
- Consumes: Task 2 `build_benchmark_plan()` and `validate_benchmark_plan()`.
- Produces: CLI exit `0` with an external canonical plan or exit `2` with fixed `SIMULATION_PREP_ERROR` and no output mutation.

- [ ] **Step 1: Write failing subprocess and output-safety tests**

Use a `_SafeArgumentParser(allow_abbrev=False)` contract and require these
arguments: `--skill-ref`, `--model-provider`, `--model-id`, `--model-snapshot`,
`--runner-name`, `--runner-version`, `--temperature`, `--top-p`,
`--max-output-tokens`, `--model-seed-policy`,
`--base-system-prompt-sha256`, `--tool-policy-sha256`, `--repeats`, `--seed`, and
`--output`.

Tests must prove:

- the exact v0.5.0 command writes a valid 72-cell external plan;
- output JSON is canonical and a second identical invocation with a fixed test
  clock produces identical bytes;
- repository-internal output, missing parent, existing-directory output,
  symlink/reparse parent, abbreviated option, invalid enum, non-finite float,
  and credential-like unknown option return exit `2`;
- stdout is empty on failure and stderr is exactly
  `simulation benchmark preparation failed\n`;
- a marker in any rejected argument never appears in output; and
- failure leaves an existing output file byte-for-byte unchanged.

- [ ] **Step 2: Run subprocess tests and verify RED**

Expected: failures because `main()` and the parser do not yet implement the
public CLI.

- [ ] **Step 3: Implement staged external output**

Resolve output using `ensure_external_path()` before writing. Require its
parent to exist outside the repository. Build the plan in memory, validate it,
write canonical bytes to a same-directory unique temporary file opened with
exclusive creation, flush and close it, then use `os.replace()` for the final
path. On every exception, remove only that exact staged file.

Inject the current UTC time through a private `now: Callable[[], datetime]`
parameter to `main()` or the plan-building helper so tests use a fixed aware
timestamp without adding a public `--created-at` bypass.

Success stdout is canonical fixed-shape JSON only:

```json
{"cell_count":72,"schema_version":"1","status":"benchmark-plan-ready"}
```

- [ ] **Step 4: Verify GREEN and commit Task 3**

```text
python -m pytest -q tests/test_simulation_benchmark.py -k "prepare or plan"
python scripts/check_public_boundary.py
git diff --check
git add -- scripts/prepare_simulation_benchmark.py tests/test_simulation_benchmark.py
git commit -m "feat: prepare external simulation benchmark plans"
```

---

### Task 4: Validate the External Response Index and Files

**Files:**
- Create: `evals/benchmark/response-index-template.json`
- Create: `scripts/evaluate_simulation_benchmark.py`
- Modify: `tests/test_simulation_benchmark.py`

**Interfaces:**
- Consumes: Task 2 canonical plan and `effectiveness_contract.ensure_external_path`.
- Produces: `validate_response_index(payload: object, plan: dict) -> list[str]`, `IncompleteBenchmark`, and `load_response_cells(plan: dict, index: dict, responses_root: Path) -> tuple[dict, ...]`.

- [ ] **Step 1: Write failing exact-schema and filesystem mutation tests**

Define root keys
`schema_version,plan_sha256,execution_attestation,records`; attestation keys
`completed_at,model_provider,model_id,model_snapshot,runner_name,runner_version,plan_followed,fresh_sessions,offline,shared_configuration_unchanged`;
and record keys
`case_id,condition,repeat,relative_path,response_sha256,size`. Generate 72
synthetic UTF-8 Markdown files under `tmp_path` and require:

```python
cells = load_response_cells(plan, response_index, responses_root)
assert len(cells) == 72
assert tuple(cell["sequence"] for cell in cells) == tuple(range(1, 73))
assert all(set(cell) == {"case_id", "condition", "repeat", "sequence", "text"} for cell in cells)
```

Add one mutation per root/attestation/record field plus missing, extra, duplicate, reordered,
unknown case, wrong condition, zero/out-of-range repeat, absolute path,
`..` traversal, backslash path, duplicate normalized path, extra response file,
missing file, directory in place of a file, symlink/reparse file, escaping
symlink parent, hardlink alias, size mismatch, digest mismatch, invalid UTF-8,
repository-internal responses root, and an interior omitted record. Require every attestation identity to
equal the plan, every attestation boolean to be literal `True`, and
`completed_at` to be timezone-aware and no earlier than plan creation. State in
tests and output contracts that the attestation is externally asserted, not
provider-verified.

Prove two independent regular files with identical bytes remain valid.

- [ ] **Step 2: Run exact nodes and verify RED**

Expected: import failure because `evaluate_simulation_benchmark.py` does not
exist.

- [ ] **Step 3: Implement the closed index validator**

Require exact keys, plan SHA-256 equality, exact attestation-to-plan identity
matching, literal attestation booleans, valid timestamp ordering, and records forming a canonical
prefix of plan cell order, safe POSIX relative paths, lowercase digests, non-negative
integer sizes excluding booleans, and complete cell identity. Unknown fields
named `status`, `direction`, `score`, `human_effective`, or `credential` are
ordinary unexpected-key errors.

If schema and all existing records are valid but planned cells are absent,
raise `IncompleteBenchmark(expected_count=72, observed_count=len(records))`. Extra,
duplicate, reordered, or interior-omission records are invalid, not incomplete.

- [ ] **Step 4: Implement reject-before-read file loading**

Resolve the response root outside the repository. Resolve every relative path
lexically inside that root, `lstat()` before reading, reject symlink and Windows
reparse attributes, require a regular file, and require unique `(st_dev,
st_ino)` identities. Compare the root's complete recursive regular-file set to
the index path set before opening content. Read bytes once, verify size and
SHA-256, decode strict UTF-8, and return cells in plan sequence. Never retain a
path or raw bytes in the returned mapping.

- [ ] **Step 5: Create and test the public response-index template**

The template contains exact root keys, a null plan digest, a fully keyed
attestation with null identities/timestamp and false booleans, and an empty records
list. It is documentation-only, contains no response path or model output, and
is rejected as an invalid unpopulated template against a real plan. Incomplete
exit `3` is reserved for an otherwise valid index containing a proper prefix of
the 72 canonical records.

- [ ] **Step 6: Verify GREEN and commit Task 4**

```text
python -m pytest -q tests/test_simulation_benchmark.py -k "response or index or file"
python scripts/check_public_boundary.py
git diff --check
git add -- evals/benchmark/response-index-template.json scripts/evaluate_simulation_benchmark.py tests/test_simulation_benchmark.py
git commit -m "feat: validate external benchmark responses"
```

---

### Task 5: Evaluate Pairs and Compute the Benchmark Direction

**Files:**
- Modify: `scripts/evaluate_simulation_benchmark.py`
- Modify: `tests/test_simulation_benchmark.py`

**Interfaces:**
- Consumes: Task 4 response cells and existing `load_catalog()` / `evaluate_response()`.
- Produces: `classify_direction(overall_difference: Fraction, improved: int, worsened: int, control_forbidden: int, intervention_forbidden: int, depth_differences: tuple[Fraction, ...]) -> str`, `evaluate_benchmark(plan: dict, cells: tuple[dict, ...], execution_attestation: dict) -> dict`, `validate_benchmark_summary(payload: object) -> list[str]`, and `canonical_summary_bytes(summary: dict) -> bytes`.

- [ ] **Step 1: Write failing aggregation tests**

Create generated responses that drive the existing evaluator into exact pass or
fail states without mocking it. Cover:

```python
def test_complete_pairs_compute_exact_aggregate_counts():
    summary = evaluate_benchmark(
        plan,
        cells_for_pattern("positive"),
        valid_execution_attestation(plan),
    )
    assert summary["status"] == "benchmark-observed"
    assert summary["cell_counts"] == {"expected": 72, "observed": 72}
    assert summary["paired_counts"] == {
        "both_fail": 0,
        "both_pass": 24,
        "improved": 12,
        "worsened": 0,
    }
```

Unit-test `classify_direction()` at exact `Fraction(1, 5)` and immediately
below it. In complete 36-pair integration tests, require a net 7/36 improvement
to remain `mixed-or-null` and a net 8/36 improvement to satisfy the practical
threshold when every guardrail also passes. Separately cover improved equal to
worsened, one intervention forbidden violation, and one negative output-depth
stratum. Add complete positive, mixed/null, and negative scenarios and require
exact direction values.

Add a spy only around the imported existing function boundary to prove each of
the 72 cells calls `evaluate_response()` exactly once with the bound catalog
case and rubric. Do not duplicate evaluator expected scores in benchmark tests.

- [ ] **Step 2: Run aggregation tests and verify RED**

Expected: `evaluate_benchmark` and summary validation imports fail.

- [ ] **Step 3: Implement per-cell facts and paired aggregation**

For each evaluator result retain only case ID, condition, repeat, pass boolean,
and the count of failed `forbidden:` or `forbidden-section:` rules. Pair by
`(case_id, repeat)`. Use integer counts and `fractions.Fraction` for all
classification comparisons. Serialize rates and differences as six-decimal
JSON numbers only after the exact direction is determined.

Build exact overall, output-depth, and per-case aggregates. Set
`synthetic_example` to `False` in every summary produced by the evaluator CLI.
Copy only the closed safe execution-attestation fields into the summary,
require their identities to remain equal to the plan, and label them as
externally asserted rather than provider-verified. Do not copy response-index
records, paths, or response metadata. The attestation is an explicit third
argument; do not hide it in globals or expand response-cell mappings.
Per-case stability
is `stable-pass`, `stable-fail`, or `variable` separately for each condition.
Never aggregate raw scores across cases.

- [ ] **Step 4: Implement predeclared direction precedence**

Compute negative first:

```python
negative = (
    overall_difference < 0
    or intervention_forbidden > control_forbidden
    or any(stratum["difference"] < 0 for stratum in depth_results)
)
positive = (
    overall_difference >= Fraction(1, 5)
    and improved > worsened
    and intervention_forbidden == 0
    and all(stratum["difference"] >= 0 for stratum in depth_results)
)
direction = "negative-signal" if negative else "positive-signal" if positive else "mixed-or-null"
```

Require output `status == "benchmark-observed"` for every complete valid
direction. Summary validation rejects unknown keys, recomputes all rates,
counts, strata, stability, and direction, and rejects any human-effectiveness or
green field.

- [ ] **Step 5: Verify GREEN and commit Task 5**

```text
python -m pytest -q tests/test_simulation_benchmark.py -k "aggregate or direction or evaluate or summary"
python -m pytest -q tests/test_response_evaluator.py
git diff --check
git add -- scripts/evaluate_simulation_benchmark.py tests/test_simulation_benchmark.py
git commit -m "feat: summarize paired simulation benchmark results"
```

---

### Task 6: Add the Safe Evaluation CLI and Atomic Summary Output

**Files:**
- Modify: `scripts/evaluate_simulation_benchmark.py`
- Modify: `tests/test_simulation_benchmark.py`

**Interfaces:**
- Consumes: Tasks 4–5 validators, loader, and evaluator.
- Produces: public CLI with exact inputs `--plan`, `--response-index`, `--responses-dir`, and `--output-summary`; exit codes `0`, `2`, `3`.

- [ ] **Step 1: Write failing CLI tests**

Subprocess tests require:

- a complete external bundle exits `0`, writes canonical summary bytes, and
  prints only `{"schema_version":"1","status":"benchmark-observed"}`;
- a valid incomplete index exits `3`, writes no summary file, emits empty
  stderr, and prints only schema version, `benchmark-incomplete`, expected count,
  and observed count;
- malformed, unsafe, extra, duplicate, aliased, or mismatched input exits `2`,
  writes empty stdout, and stderr exactly
  `simulation benchmark evaluation failed\n`;
- all parsers reject abbreviated flags;
- output cannot alias any input by spelling, resolution, symlink/reparse point,
  or hardlink;
- failures leave an existing output unchanged; and
- a marker in response text, metadata, filename, and invalid JSON never appears
  in stdout or stderr.

- [ ] **Step 2: Run CLI tests and verify RED**

Expected: parser or `main()` behavior is absent.

- [ ] **Step 3: Implement safe dispatch and staged output**

Use a safe parser with `allow_abbrev=False`. Resolve and de-alias every path
before reading. Catch all parse, filesystem, JSON, YAML, Git, schema, evaluator,
and output exceptions at the CLI boundary and emit only the fixed error.

For complete evidence, validate the summary twice: once after computation and
once after canonical serialize/parse. Write a same-directory exclusive staged
file, flush, close, and atomically replace the output. On incomplete evidence,
write no file. Never modify inputs.

Pass the already validated `response_index["execution_attestation"]` explicitly
to `evaluate_benchmark(plan, cells, execution_attestation)`. Do not place the
attestation in response cells or module-global state.

- [ ] **Step 4: Verify GREEN and commit Task 6**

```text
python -m pytest -q tests/test_simulation_benchmark.py
python scripts/check_public_boundary.py
git diff --check
git add -- scripts/evaluate_simulation_benchmark.py tests/test_simulation_benchmark.py
git commit -m "feat: evaluate external simulation benchmarks"
```

---

### Task 7: Render Aligned English and Traditional Chinese Reports

**Files:**
- Create: `scripts/render_simulation_benchmark.py`
- Create: `evals/benchmark/summary-schema.md`
- Create: `evals/benchmark/report-template.md`
- Create: `evals/benchmark/report-template.zh-TW.md`
- Create: `evals/benchmark/examples/synthetic-summary.json`
- Create: `evals/benchmark/examples/synthetic-report.md`
- Create: `evals/benchmark/examples/synthetic-report.zh-TW.md`
- Create: `tests/test_simulation_benchmark_reports.py`

**Interfaces:**
- Consumes: Task 5 `validate_benchmark_summary()` and canonical synthetic summary.
- Produces: `render_report(summary: dict, language: str) -> str`, paired atomic writer, and CLI `--summary --english --traditional-chinese [--check]`.

- [ ] **Step 1: Write failing renderer and alignment tests**

Require exact section order in both languages:

1. identity and scope;
2. aggregate result;
3. paired changes;
4. output-depth strata;
5. per-case stability;
6. forbidden-rule guardrail; and
7. limitations and next evidence step.

Parse both reports and require identical commit, tag, package digest, plan
digest, model and runner metadata, execution-attestation completion time and
controlled booleans, counts, rates, differences, strata, stability, status,
and direction. Require the English and Traditional Chinese mandatory limitation
sentences and reject `human-effective`, `evaluation-green`, clinical validity,
causal validity, patient outcome, or deployment-ready claims.

Mutation tests cover missing/reordered sections, stale number, stale direction,
wrong digest, missing limitation, mixed-language output path, second-file write
failure rollback, hardlink output alias, input alias, and `--check` byte drift.

- [ ] **Step 2: Run renderer tests and verify RED**

Expected: module and public template files are missing.

- [ ] **Step 3: Implement summary schema documentation and synthetic example**

Document every exact summary field, type, controlled value, recomputation rule,
and claim boundary. Generate a complete summary with
`synthetic_example: true`, 72 cells, and internally consistent
`positive-signal` counts. The
example is contract demonstration only; real summary validation requires
`synthetic_example: false`, while renderer validation permits either and labels
it visibly.

- [ ] **Step 4: Implement deterministic bilingual rendering**

`render_report()` validates the summary and language (`en` or `zh-TW`) before
constructing Markdown. Numbers use fixed six-decimal formatting, and all tables
use canonical case/depth order. The CLI reads only an external summary for real
runs. The checked-in synthetic summary is permitted only when generating or
checking the exact checked-in English and Traditional Chinese example-report
paths; it cannot be redirected to arbitrary outputs.

Write both outputs via staged files and rollback the first replacement if the
second replacement fails, following the existing effectiveness renderer
pattern. `--check` performs no writes.

- [ ] **Step 5: Generate the checked-in reports and verify GREEN**

```text
python scripts/render_simulation_benchmark.py --summary evals/benchmark/examples/synthetic-summary.json --english evals/benchmark/examples/synthetic-report.md --traditional-chinese evals/benchmark/examples/synthetic-report.zh-TW.md
python scripts/render_simulation_benchmark.py --summary evals/benchmark/examples/synthetic-summary.json --english evals/benchmark/examples/synthetic-report.md --traditional-chinese evals/benchmark/examples/synthetic-report.zh-TW.md --check
python -m pytest -q tests/test_simulation_benchmark_reports.py
git diff --check
```

- [ ] **Step 6: Commit Task 7**

```text
git add -- scripts/render_simulation_benchmark.py evals/benchmark/summary-schema.md evals/benchmark/report-template.md evals/benchmark/report-template.zh-TW.md evals/benchmark/examples/synthetic-summary.json evals/benchmark/examples/synthetic-report.md evals/benchmark/examples/synthetic-report.zh-TW.md tests/test_simulation_benchmark_reports.py
git commit -m "feat: render simulation benchmark reports"
```

---

### Task 8: Add Guidance, Community Issue Forms, and Public-Boundary Rules

**Files:**
- Create: `evals/benchmark/README.md`
- Create: `.github/ISSUE_TEMPLATE/benchmark-result.yml`
- Create: `.github/ISSUE_TEMPLATE/usability-feedback.yml`
- Modify: `evals/README.md`
- Modify: `README.md`
- Modify: `README.zh-TW.md`
- Modify: `scripts/check_public_boundary.py`
- Modify: `tests/test_public_boundary.py`
- Modify: `tests/test_project_metadata.py`

**Interfaces:**
- Consumes: Tasks 2–7 CLI commands, states, directions, templates, and safety boundaries.
- Produces: aligned public instructions, structured self-reported feedback, and reject-before-read benchmark-private path rules.

- [ ] **Step 1: Write failing documentation, Issue Form, and scanner tests**

Require the benchmark README to contain the three exact commands, 72-cell
layout, fresh-session/offline/balanced-order rules, external-output boundary,
exit codes, direction criteria, Tier 2 link, and no-human-claim language.

Parse both Issue Forms as YAML and require GitHub Issue Form root keys
`name,description,title,labels,body`; unique safe body IDs; only aggregate
benchmark fields; and a required checkbox containing all prohibited categories:
patient data, private schema, internal document, condition key, task pack,
nonce, API key, access token, and credential. The benchmark form must not have a
raw-response textarea or upload instruction. Require `community-reported` and
the statement that Issues never enter formal aggregates.

Add scanner mutation paths for:

```text
evals/benchmark/runs/run.json
evals/benchmark/results/report.md
evals/benchmark/raw-responses/case.md
evals/benchmark/response-bundle.json
evals/benchmark/benchmark-plan.json
evals/benchmark/condition-key.json
evals/benchmark/api-key.txt
```

For each, monkeypatch `Path.stat`, `Path.lstat`, and `Path.read_text` probes and
prove the private benchmark classifier returns a safe path/rule finding before
content access. Preserve existing private-study and recovery rule precedence.

- [ ] **Step 2: Run focused tests and verify RED**

Expected: missing guidance/forms and unrecognized private benchmark paths.

- [ ] **Step 3: Write the public benchmark README and navigation**

Use these exact sections: purpose, evidence boundary, released Skill binding,
prepare plan, run externally, build response index, evaluate, render, interpret
direction, optional independent review, community feedback, and prohibited
content. Add concise aligned links to root and Eval READMEs. Do not add a model
runner, provider recommendation, credential setup, or real output example.

- [ ] **Step 4: Create both Issue Forms**

Use structured dropdown/input fields for versions, operating system, agent,
status, direction, SHA-256, and task category. The only free-text field is a
bounded problem/reproduction description preceded by the sensitive-data
warning. Include the required acknowledgement checkbox and no field that asks
for raw answers, prompts, logs, task packs, or attachments.

- [ ] **Step 5: Harden the public-boundary scanner**

Add an explicit benchmark public allowlist and a global basename/part
classifier for real plans, indexes, outputs, runs, results, raw responses,
credentials, and human-study artifacts. Apply it after the existing broader
private-study/recovery classifiers but before stat, size, or content reads.
Findings include only normalized repository-relative path and rule ID.

- [ ] **Step 6: Verify GREEN and commit Task 8**

```text
python -m pytest -q tests/test_public_boundary.py tests/test_project_metadata.py tests/test_simulation_benchmark.py tests/test_simulation_benchmark_reports.py
python scripts/check_public_boundary.py
git diff --check
git add -- evals/benchmark/README.md .github/ISSUE_TEMPLATE/benchmark-result.yml .github/ISSUE_TEMPLATE/usability-feedback.yml evals/README.md README.md README.zh-TW.md scripts/check_public_boundary.py tests/test_public_boundary.py tests/test_project_metadata.py
git commit -m "docs: add public simulation benchmark guidance"
```

---

### Task 9: Synchronize v0.6.0 Candidate Metadata and Packaging

**Files:**
- Modify: `pyproject.toml`
- Modify: `scripts/package_skill.py`
- Modify: `.github/workflows/release.yml`
- Modify: `CHANGELOG.md`
- Modify: `CHANGELOG.zh-TW.md`
- Modify: `CITATION.cff`
- Create: `docs/releases/0.6.0.md`
- Modify: `tests/test_packaging.py`
- Modify: `tests/test_project_metadata.py`
- Modify: `tests/test_release_verification.py`

**Interfaces:**
- Consumes: completed Tasks 1–8 and current published v0.5.0 security/install history.
- Produces: synchronized `0.6.0` candidate package and guarded future release workflow without creating a tag or Release.

- [ ] **Step 1: Write failing candidate-version tests**

Require:

- `pyproject.toml`, `package_skill.PACKAGE_VERSION`, generated archive/manifest,
  `CITATION.cff`, changelog headings, candidate notes, and release workflow to
  use `0.6.0`;
- generated names `clin-nav-0.6.0.zip` and
  `clin-nav-0.6.0.manifest.json`;
- release workflow build assertion `test "$VERSION" = "0.6.0"` and notes
  `docs/releases/0.6.0.md`;
- candidate notes to say no v0.6.0 tag or Release exists and no real benchmark
  campaign or human pilot has been performed;
- `CITATION.cff` to omit `date-released` until publication;
- `SECURITY.md` to keep the actually published `0.5.x` line supported during
  candidate development; and
- installation history to keep v0.5.0 as the latest published immutable bundle.

Run the exact nodes and require RED on the current `0.5.0` values and missing
0.6.0 notes.

- [ ] **Step 2: Update the candidate version surfaces**

Set project/package/CITATION version to `0.6.0`, remove `date-released`, add
English and Traditional Chinese `0.6.0 - Candidate` changelog sections, and
write bilingual static notes describing the provider-neutral benchmark,
released-Skill binding, external run boundary, deterministic evaluator reuse,
Issue Forms, and limitations.

Update only future release workflow constants and notes path. Do not modify
published v0.5.0 notes, verification evidence, tag, Release assets, or
`SECURITY.md` support truth.

- [ ] **Step 3: Verify metadata and deterministic candidate artifacts**

```text
python -m pytest -q tests/test_packaging.py tests/test_project_metadata.py tests/test_release_verification.py
python scripts/package_skill.py --check-reproducible
python scripts/package_skill.py --output-dir dist
python scripts/verify_release.py artifacts --archive dist/clin-nav-0.6.0.zip --manifest dist/clin-nav-0.6.0.manifest.json
git diff --check
```

Independently inspect manifest root keys, version, archive name, sorted unique
members, ZIP member order, and every member size/SHA-256.

- [ ] **Step 4: Commit Task 9**

```text
git add -- pyproject.toml scripts/package_skill.py .github/workflows/release.yml CHANGELOG.md CHANGELOG.zh-TW.md CITATION.cff docs/releases/0.6.0.md tests/test_packaging.py tests/test_project_metadata.py tests/test_release_verification.py
git commit -m "build: prepare clin-nav 0.6.0 benchmark candidate"
```

---

### Task 10: Complete Synthetic E2E, Dual-Runtime Verification, and Final Review

**Files:**
- Modify only if a verified bug requires a new RED test and scoped fix.
- Ignored evidence may be written under `.superpowers/sdd/2026-08-16-public-simulation-benchmark/`.

**Interfaces:**
- Consumes: Tasks 1–9 committed candidate.
- Produces: a clean, fully verified local `v0.6.0` candidate; no push, tag, workflow dispatch, model call, or Release.

- [ ] **Step 1: Run a fresh external synthetic end-to-end campaign**

Create one GUID directory under the system temporary root after proving it does
not exist. Use the prepare CLI with fixed synthetic provider/model/runner
metadata and v0.5.0 binding. Generate all 72 synthetic Markdown responses and a
canonical response index using test utilities that call no model. Run the
evaluation CLI and renderer, require `benchmark-observed`, exact intended
direction, two aligned reports, input byte immutability, and no repository
write. Delete only the resolved GUID directory and prove it no longer exists.

Run adverse copies for missing cell (exit `3`), hash mutation (exit `2`), model
configuration drift (exit `2`), forbidden-rule regression (complete negative or
mixed direction), and a marker-bearing invalid response (fixed error with no
marker disclosure).

- [ ] **Step 2: Run complete host verification**

```text
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
python scripts/render_eval_summary.py --check
python scripts/render_effectiveness_report.py --summary evals/effectiveness/examples/synthetic-summary.json --english evals/effectiveness/examples/synthetic-report.md --traditional-chinese evals/effectiveness/examples/synthetic-report.zh-TW.md --check
python scripts/render_simulation_benchmark.py --summary evals/benchmark/examples/synthetic-summary.json --english evals/benchmark/examples/synthetic-report.md --traditional-chinese evals/benchmark/examples/synthetic-report.zh-TW.md --check
git diff --check
```

Every command must exit `0` with no warning or changed generated file.

- [ ] **Step 3: Run the same set with official Python 3.11.9**

First prove `sys.executable`, `sys.version`, `sys.path`, and imports resolve the
candidate checkout. If the embedded `_pth` requires an external-path change,
obtain explicit approval, hash and save the original bytes, use the candidate
path only for the verification window, and restore byte-for-byte in `finally`.
Use one unique external pytest base temp and cache directory. Require the same
test count and exit codes as host, then prove `_pth` SHA restoration and zero
temporary leftovers.

- [ ] **Step 4: Independently verify candidate artifacts**

Rebuild into a clean `dist`, run `verify_release.py artifacts`, compare two
independent builds byte-for-byte, and inspect manifest/ZIP schema, version,
names, order, uniqueness, sizes, and SHA-256 values. Expand into a fresh unique
temporary directory, run the public-boundary scanner, and safely remove it.

- [ ] **Step 5: Review the complete implementation range**

Review every commit from the plan base through candidate HEAD. Require only
approved public code, templates, synthetic examples, documentation, Issue Forms,
tests, scanner rules, and metadata. Search tracked files for API keys, tokens,
credentials, raw response bundles, real plans, participant/patient content,
private schema, task packs, nonces, assignments, condition keys, institution
paths, model outputs, and unsupported human/clinical claims. Investigate every
match in context; any real private or credential content stops completion.

- [ ] **Step 6: Record final truthful state**

Require:

- all software and synthetic E2E gates green;
- first real 72-cell model campaign not yet executed;
- `benchmark-observed` demonstrated only by synthetic pipeline data;
- community feedback not yet collected or aggregated;
- human effectiveness and power analysis still pending their separate path;
- no v0.6.0 tag or GitHub Release;
- `git status --porcelain` empty; and
- no push performed under this plan.

Write the ignored final verification report with commit range, exact test
counts, commands, exits, artifact digests, runtime identities, temporary cleanup
evidence, and remaining external steps.
