# ClinNav Public Simulation Benchmark Design

- **Status:** approved design; pending review of this written specification
- **Design date:** 2026-08-16 (Asia/Taipei)
- **Target:** `v0.6.0` candidate capability
- **First benchmark target:** released `clin-nav` `v0.5.0`
- **Dependencies:** existing deterministic Eval catalog, effectiveness contracts,
  public-boundary scanner, deterministic packaging, and `v0.5.0` Release

## 1. Decision

Add a provider-neutral, repository-native public simulation benchmark. It
compares model responses produced without the Skill (`control`) against
responses produced with an exact `clin-nav` bundle (`intervention`) while
holding the model and all shared settings fixed.

The benchmark does not call a model from CI. Users run models in their own
approved environments and supply repository-external response files. The
repository validates a closed plan, response index, file hashes, complete
paired layout, and reproducible aggregate summary. It then renders aligned
English and Traditional Chinese reports.

The terminal software state is `benchmark-observed`. A predeclared directional
classification may be `positive-signal`, `mixed-or-null`, or
`negative-signal`. None of these states means `human-effective`,
`evaluation-green`, clinical validity, causal validity, patient benefit, or
fitness for deployment.

## 2. Current state

The repository already contains two complementary evaluation layers:

1. `evals/cases.yaml`, `evals/rubric.yaml`, and
   `scripts/evaluate_response.py` provide twelve deterministic behavior-contract
   cases and a tested evaluator.
2. `evals/effectiveness/` provides eight matched task pairs, blinded rating,
   agreement, lock, unlock, aggregation, governance readiness, and incident
   recovery for a separately authorized human pilot.

The deterministic and recovery software is tested and green-capable. It has
not yet produced an independently executed model comparison or observed human
effectiveness evidence. The new benchmark fills the model-comparison gap
without weakening or pretending to complete the human-evidence path.

## 3. Evaluated approaches

### 3.1 Public reproducible simulation benchmark plus safe community feedback

Selected. It produces quantitative, repeatable evidence appropriate to a
GitHub project while remaining provider-neutral and free of human-study data.
Community feedback is retained as a secondary, explicitly self-reported signal.

### 3.2 Documentation and unstructured GitHub feedback only

Rejected as the primary path. It is inexpensive but cannot bind model settings,
prevent case selection, reproduce outputs, or distinguish installation reports
from product-effect evidence.

### 3.3 Immediate human effectiveness study

Deferred. Representative-user evidence remains necessary before making human
usability claims, but it is not the next required stage for this open-source
project. Its governance, privacy, recruitment, and operational requirements
should not block a public synthetic benchmark.

## 4. Evidence tiers

### 4.1 Tier 1: deterministic public benchmark

Tier 1 uses every case in `evals/cases.yaml` and the existing deterministic
evaluator. The first normative layout is:

```text
12 cases x 2 conditions x 3 repeats = 72 response cells
```

The two conditions are:

- `control`: the exact shared model setup with `clin-nav` unavailable; and
- `intervention`: the same setup with the exact bound `clin-nav` bundle
  available and invoked as `$clin-nav`.

Every case and repeat has exactly one response in each condition. A run cannot
select cases, omit unfavorable responses, add private cases, or change the
repeat count after the plan is frozen.

Each response starts in a fresh session with no prior cell, answer, condition,
or conversation memory. The normative first campaign uses an offline tool
policy with network and external retrieval disabled. This isolates the Skill's
response contract and makes evidence-navigation failures observable as bounded
limitations rather than allowing changing search results to become an
unrecorded treatment difference.

The plan uses a fixed assignment seed to balance control-first and
intervention-first order across the 36 pairs. The runner follows that complete
cell sequence and must not copy a prior response into a later session. Order,
fresh-session policy, and offline policy are bound in the plan and reported as
externally asserted runner metadata.

### 4.2 Tier 2: optional independent depth review

Tier 2 may reuse the eight public matched pairs and rubric under
`evals/effectiveness/`. It requires two independent, condition-blind reviewers
and reuses the existing agreement, ratings-lock, unlock, and aggregate
contracts. A model must not judge its own responses for this tier.

Without two complete independent reviews, Tier 2 remains
`awaiting-independent-review`. It is optional for `v0.6.0` and cannot block or
silently modify the Tier 1 result. Even after completion, it remains a review
of public synthetic tasks rather than representative-user usability evidence.

## 5. Architecture

New public components live under `evals/benchmark/`, `scripts/`, and
`.github/ISSUE_TEMPLATE/`:

```text
evals/benchmark/
|-- README.md
|-- benchmark-plan-template.json
|-- response-index-template.json
|-- summary-schema.md
|-- report-template.md
|-- report-template.zh-TW.md
`-- examples/
    `-- synthetic-summary.json

scripts/
|-- prepare_simulation_benchmark.py
|-- evaluate_simulation_benchmark.py
`-- render_simulation_benchmark.py

.github/ISSUE_TEMPLATE/
|-- benchmark-result.yml
`-- usability-feedback.yml
```

The implementation reuses `load_catalog()` and `evaluate_response()` from
`scripts/evaluate_response.py`. It must not copy the catalog validator,
normalization, depth-section rules, regex evaluation, forbidden-rule logic, or
pass calculation.

Real run plans, response indexes, raw responses, provider logs, reports, and
credentials remain outside the checkout. Only closed templates, schemas,
guidance, report templates, and explicitly synthetic examples enter Git.

## 6. Frozen benchmark plan

`prepare_simulation_benchmark.py` creates one canonical JSON plan in an
external output location. The command accepts:

```text
python scripts/prepare_simulation_benchmark.py \
  --skill-ref v0.5.0 \
  --model-provider <provider> \
  --model-id <model> \
  --repeats 3 \
  --seed 20260816 \
  --output <external-dir>/benchmark-plan.json
```

The plan uses an exact-key schema and records only controlled metadata:

- schema version and a safe benchmark ID;
- catalog and rubric SHA-256 values;
- the full ordered case-ID set;
- repeat count, assignment seed, balanced condition order, and the complete
  expected 72-cell sequence;
- `clin-nav` name, semantic version, Git ref, peeled commit, package filename,
  package SHA-256, and public member-set digest;
- model provider, model ID, externally reported model snapshot/version, and
  runner name/version;
- shared temperature, top-p, maximum-output, model seed policy,
  fresh-session policy, base-system-prompt SHA-256, network policy, and
  tool-policy SHA-256;
- condition definitions whose only permitted difference is whether the bound
  Skill is available; and
- creation time and plan-format version.

Provider names and model metadata are external assertions bound for
reproduction; the tool does not claim they are independently verified.

The command never accepts or reads an API key, access token, credential file,
endpoint secret, participant identifier, private prompt, or private task. It
resolves the Skill ref locally, requires an annotated release tag for the first
normative campaign, verifies the peeled commit, and binds the deterministic
package digest. It performs no network call.

## 7. Response index and files

The model runner is outside the repository and outside the benchmark CLI. It
writes one UTF-8 Markdown response per planned cell and a closed response index.
Each index record contains exactly:

- case ID;
- condition (`control` or `intervention`);
- one-based repeat number;
- safe relative response filename;
- response byte length; and
- lowercase SHA-256.

The index binds the plan SHA-256 and contains the exact 72 records in canonical
plan order. It contains no status, score, favorable-result flag, path outside
the response root, response text, model credential, or free-form note.

Every input path resolves outside the repository. The evaluator rejects path
traversal, symlinks or reparse points that escape the response root, hardlink
aliases between cells, duplicate records, unexpected files, non-UTF-8 input,
and size or digest mismatch. Identical bytes in two distinct regular files are
valid and produce a tie; content equality alone is not treated as fraud.

## 8. Evaluation and summary

The evaluation command is:

```text
python scripts/evaluate_simulation_benchmark.py \
  --plan <external-dir>/benchmark-plan.json \
  --response-index <external-dir>/response-index.json \
  --responses-dir <external-dir>/responses \
  --output-summary <external-dir>/benchmark-summary.json
```

It validates all immutable bindings before reading response text. It reads
each response exactly once, verifies its byte length and SHA-256, decodes it as
UTF-8, and calls the existing evaluator. It writes a staged canonical summary
only after every response and aggregate check succeeds. Inputs are not
modified.

The summary contains only safe benchmark metadata and evaluator-derived data:

- schema version, benchmark ID, plan SHA-256, catalog/rubric/Skill bindings,
  model metadata, repeat count, and expected/observed cell counts;
- `benchmark-observed` status;
- the directional classification;
- control and intervention pass counts and rates;
- absolute intervention-minus-control pass-rate difference;
- paired counts for improved, worsened, both-pass, and both-fail cells;
- control and intervention forbidden-rule violation counts;
- the same aggregates by output depth;
- per-case pass counts and stability across the three repeats; and
- explicit simulation-only claim boundaries.

It does not include response text, filenames, local paths, dynamic exception
text, provider logs, prompts, credentials, or a human-effectiveness field.

## 9. Primary metric and direction classification

Raw evaluator scores are not averaged across cases because cases have different
numbers of positive rules and therefore different attainable totals. The
primary metric is the paired contract pass-rate difference:

```text
intervention pass rate - control pass rate
```

Supporting measures are:

- improved discordant pairs (`control fail`, `intervention pass`);
- worsened discordant pairs (`control pass`, `intervention fail`);
- both-pass and both-fail pairs;
- forbidden-rule violations by condition;
- output-depth strata; and
- repeat stability by case.

The predeclared `positive-signal` requirements are all of:

1. overall absolute pass-rate improvement is at least `0.20`;
2. improved pairs outnumber worsened pairs;
3. intervention has zero forbidden-rule violations; and
4. no output-depth stratum has a negative pass-rate difference.

`negative-signal` requires either an overall negative pass-rate difference, a
higher intervention forbidden-rule violation count, or a negative difference
in any output-depth stratum. All other complete outcomes are
`mixed-or-null`.

The 20-percentage-point practical threshold is fixed before observing a real
benchmark and aligns with the existing effectiveness framework. The benchmark
does not calculate a confirmatory sample size or reuse simulation results for
human-study power analysis.

## 10. Status and exit codes

The result status and directional classification are separate. A complete,
valid run returns `benchmark-observed` regardless of whether the direction is
positive, mixed, or negative.

Exit codes are:

- `0`: complete, valid, reproducible `benchmark-observed` summary;
- `3`: schema-valid plan/index but one or more planned cells are absent; and
- `2`: unsafe path, malformed input, invalid schema, extra or duplicate cell,
  configuration drift, identity/hash mismatch, evaluator failure, output
  alias, or attempted status/claim injection.

The CLI writes fixed content-free stderr for invalid inputs. It never echoes a
response, model name, provider value, external identifier, local path, hash,
or exception string. Incomplete output is a sanitized fixed-shape summary and
cannot be rendered as a result report.

## 11. Bilingual reporting

`render_simulation_benchmark.py` consumes only a valid canonical summary:

```text
python scripts/render_simulation_benchmark.py \
  --summary <external-dir>/benchmark-summary.json \
  --english <external-dir>/benchmark-report.md \
  --traditional-chinese <external-dir>/benchmark-report.zh-TW.md
```

The renderer validates exact schema and recomputes all direction rules. It
writes both outputs using staged replacement and rollback so mixed report
versions cannot remain after a partial failure. `--check` compares existing
outputs without modifying them.

Both reports contain the frozen identities, complete aggregate table, paired
counts, strata, stability, limitations, and these mandatory statements:

- results concern public synthetic prompts and deterministic contract checks;
- model metadata are externally reported;
- deterministic rules do not measure all semantic quality;
- no representative user performed a usability task;
- no clinical, causal, patient-outcome, or deployment claim follows; and
- `positive-signal` is not `human-effective` or `evaluation-green`.

## 12. Community feedback

The secondary GitHub path uses two structured Issue Forms.

`benchmark-result.yml` collects only:

- repository version/tag and benchmark summary schema version;
- plan and aggregate-summary SHA-256 values;
- model provider/ID/snapshot as self-reported metadata;
- operating system and runner version;
- aggregate status and direction;
- an optional public aggregate-report URL; and
- reproduction notes that contain no raw response.

`usability-feedback.yml` collects installation method, agent, operating system,
task category, completion outcome, and a bounded problem description. Both
forms require an acknowledgement that the report contains no patient data,
private schema, internal document, condition key, task pack, nonce, API key,
access token, credential, or other sensitive content.

Issue reports are labeled conceptually as `community-reported`. They are
unverified observations and never enter benchmark aggregates automatically.
Maintainers must close or redact unsafe reports according to GitHub's available
moderation controls; a form acknowledgement reduces but cannot eliminate the
risk of a user pasting sensitive material.

## 13. Public boundary

The scanner preserves explicit allowlists for the public benchmark templates,
schemas, README, report templates, Issue Forms, and synthetic summary. It
rejects likely real run material before reading file content, including:

- `evals/benchmark/runs/` or `evals/benchmark/results/`;
- raw-response or response-bundle paths;
- real benchmark plans, response indexes, or generated reports;
- credential, API-key, token, private-task, condition-key, assignment, nonce,
  participant, patient, institutional-schema, or human-study filenames; and
- result fixtures not explicitly located under the synthetic example allowlist.

Findings report only a safe repository-relative path and rule ID. They never
print file content. The existing global private-study and recovery rules retain
precedence.

## 14. Failure handling

- Case selection, an altered repeat count, or any unplanned cell is invalid.
- A missing planned cell is incomplete and returns exit `3`; it is never scored
  as a failure or silently removed from the denominator.
- Shared model or runner drift between conditions invalidates the bundle.
- The condition-specific Skill availability is the only allowed treatment
  difference.
- Catalog, rubric, Skill package, plan, response, or summary hash mismatch is
  invalid.
- A favorable partial result cannot override an invalid or incomplete bundle.
- A forbidden-rule regression prevents `positive-signal` even when the overall
  pass rate improves.
- A supplied status, directional label, human claim, or precomputed aggregate
  is rejected and recomputed.
- Renderer schema or recomputation failure leaves both report files unchanged.
- Community feedback never changes a formal benchmark result.

## 15. Test-driven implementation

Every behavior change starts with a failing test. Tests use only public
contracts, generated synthetic responses, and disposable external temporary
directories.

Required tests include:

- exact 72-cell plan generation, seed-balanced order, uniqueness, and canonical
  JSON serialization;
- annotated tag, peeled commit, package, catalog, rubric, system-prompt, and
  tool-policy bindings;
- rejection of credentials, unsafe free text, unknown fields, status injection,
  invalid numeric parameters, and unreported required metadata;
- exact response-index layout and mutation tests for every record field;
- missing, extra, duplicate, reordered, traversal, symlink/reparse, hardlink,
  non-UTF-8, size, and SHA-256 failures;
- proof that evaluation calls the existing `evaluate_response()` behavior and
  remains synchronized with its catalog/rubric contracts;
- exact paired and output-depth aggregates;
- synthetic positive, mixed, and negative classifications at boundary values;
- zero-intervention-forbidden and no-negative-stratum guardrails;
- input immutability, staged output, rollback, content-free errors, and fixed
  exit codes;
- bilingual report equality of facts and renderer `--check` behavior;
- Issue Form structure and mandatory sensitive-data acknowledgement;
- public-boundary allowlist and reject-before-read mutations; and
- a provider-free synthetic end-to-end run that creates and removes one unique
  external temporary workspace.

CI performs no model call and requires no model credential. Completion requires:

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

The complete set is repeated with the official Python 3.11.9 runtime used by
the release process.

## 16. Inversion and second-order controls

The benchmark fails most seriously if it becomes a machine for manufacturing a
favorable claim. Full-case planning, fixed repeats, immutable hashes, complete
cell accounting, paired results, safety guardrails, and rejection of
input-supplied labels prevent cherry-picking and result injection.

It also fails if the treatment changes more than Skill availability. The plan
separates shared model/runner configuration from the single condition-specific
Skill binding and invalidates all other drift.

A deterministic regex evaluator can be gamed and cannot establish complete
semantic quality. Reports state this limitation; the optional independent
review tier is separate and does not let a model grade itself.

Provider-specific runners would create credential handling, network
nondeterminism, maintenance burden, and vendor lock-in. The first version
therefore validates externally produced files and deliberately omits model API
adapters. A future adapter must receive its own design and threat review.

Public Issue Forms cannot prevent every accidental disclosure. Required
acknowledgements, structured aggregate fields, absence of raw-response upload
fields, moderation guidance, and exclusion from formal aggregates reduce the
risk without claiming it is eliminated.

The benchmark harness is a `v0.6.0` feature, while its first campaign evaluates
the already released `v0.5.0` Skill. This separation avoids using an
unreleased candidate to claim evidence about itself. Later campaigns bind their
own exact released Skill tag and package.

## 17. Acceptance criteria

- A public user can create a frozen provider-neutral plan without a network
  call or credential.
- The normative plan contains all twelve cases, both conditions, three repeats,
  and exactly 72 cells.
- Every cell starts in a fresh session; the normative first campaign is offline
  and its seed-balanced condition order is fixed before execution.
- The two conditions differ only by exact `clin-nav` availability.
- All catalogs, settings, Skill bytes, plans, responses, and summaries have
  deterministic identity bindings.
- Missing or unsafe evidence fails closed and cannot produce a report.
- Complete evidence is evaluated by the existing deterministic evaluator and
  yields exact paired, depth, safety, and stability aggregates.
- The 20-point positive threshold and safety/stratum guardrails are fixed before
  observing a real benchmark.
- English and Traditional Chinese reports contain identical facts and explicit
  simulation-only limitations.
- Community reports are structured, privacy-warned, self-reported, and excluded
  from formal aggregates.
- No model call, credential, raw real run, human-study input, private
  institutional material, or participant data enters CI or Git.
- The feature remains a `v0.6.0` candidate until full dual-runtime verification
  and a separate release decision.
