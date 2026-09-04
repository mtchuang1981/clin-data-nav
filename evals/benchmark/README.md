# Public simulation benchmark

## Purpose

This provider-neutral Tier 1 benchmark compares the existing deterministic
response contracts without the Skill (`control`) and with an exact released
`clin-nav` bundle (`intervention`). The normative layout is:

```text
12 cases x 2 conditions x 3 repeats = 72 response cells
```

It measures a paired deterministic contract signal. It does not call a model
from this repository or from CI.

## Evidence boundary

Keep every populated plan, response index, response file, provider log,
generated summary, and generated report outside the repository checkout. Use
only an approved external location. Each response cell starts in a fresh
session, the first normative campaign is offline with network and external
retrieval disabled, and the frozen plan's balanced condition order must be
followed exactly.

The external plan, response, and output directories require a single writer
for the duration of each CLI transaction. The validators reject unsafe state
and detectable namespace drift; they do not claim protection from a malicious
process continuously replacing POSIX directory entries.

## Released Skill binding

The first normative campaign evaluated the released `clin-nav` `v0.5.0`
bundle. The post-release campaign bound to `v0.7.0` completed on 2026-09-04
with all 72 externally run cells. Its canonical result is
`benchmark-observed` with direction `mixed-or-null`; the summary SHA-256 is
`ad369fd1d4048d066d30597e0d7a7a8b61a34d9c76c16cfbdb739f2bd46310d9`.
See the aggregate-only
[verification record](../../docs/verification/2026-09-04-v0.7.0-simulation-benchmark.md).
The frozen result remains authoritative and is not retroactively relabeled by
later evaluator refinements.
Preparation resolves the selected local annotated tag, rebuilds the
deterministic package, and compares it with
[`released-skill-bindings.json`](released-skill-bindings.json). A local tag by
itself is insufficient, and preparation performs no network call.

## Prepare plan

Create the frozen plan at an existing external directory. Supply controlled,
self-reported model and runner metadata; never supply a secret or credential.

```bash
python scripts/prepare_simulation_benchmark.py \
  --skill-ref v0.7.0 \
  --model-provider <provider> \
  --model-id <model> \
  --model-snapshot <snapshot> \
  --runner-name <runner> \
  --runner-version <runner-version> \
  --temperature <temperature> \
  --top-p <top-p> \
  --max-output-tokens <count> \
  --model-seed-policy <policy> \
  --base-system-prompt-sha256 <sha256> \
  --tool-policy-sha256 <sha256> \
  --repeats 3 \
  --seed 20260816 \
  --output <external-dir>/benchmark-plan.json
```

The generated plan fixes all 72 cells before any response is observed.

## Run externally

Use your own approved, repository-external runner. This project does not
provide a model runner, recommend a provider, or describe credential setup.
For every planned cell, start a fresh session and keep the shared model,
runner, base system prompt, tool policy, seed policy, and output settings
unchanged. `control` has no `clin-nav`; `intervention` makes the bound bundle
available and invokes `$clin-nav`. Do not copy a response between sessions or
change the frozen balanced condition order.

## Build response index

Start from [`response-index-template.json`](response-index-template.json) in
the external workspace. Populate exactly one record per planned cell in
canonical order, with its safe relative filename, byte length, and lowercase
SHA-256. The execution attestation repeats the plan-bound model and runner
identities and asserts that the plan, fresh-session, offline, and unchanged
shared-configuration requirements were followed. These are externally
asserted, not provider-verified.

## Evaluate

```bash
python scripts/evaluate_simulation_benchmark.py \
  --plan <external-dir>/benchmark-plan.json \
  --response-index <external-dir>/response-index.json \
  --responses-dir <external-dir>/responses \
  --output-summary <external-dir>/benchmark-summary.json
```

Exit `0` means a complete valid `benchmark-observed` summary was committed.
Exit `3` means the valid canonical record prefix is incomplete; no result
summary is written. Exit `2` means invalid or unsafe input, drift, mismatch,
aliasing, evaluation failure, or output/notification failure.

The canonical summary file is the authoritative result. Success stdout is only
a bounded notification after commit. If stdout fails before any byte, the CLI
emits its fixed stderr and exits `2`; after a partial notification it emits no
additional stderr and exits `2`. In either case, an already committed valid
summary remains authoritative and is not rolled back.

## Render

Render both reports from the canonical external summary:

```bash
python scripts/render_simulation_benchmark.py \
  --summary <external-dir>/benchmark-summary.json \
  --english <external-dir>/benchmark-report.md \
  --traditional-chinese <external-dir>/benchmark-report.zh-TW.md
```

Add `--check` only to compare existing outputs without modifying them. A real
summary and both generated reports remain outside this checkout.

## Interpret direction

Status and direction are separate. Every complete valid result is
`benchmark-observed`. A `positive-signal` requires all four predeclared gates:
an overall absolute pass-rate improvement of at least `0.20`, more improved
than worsened pairs, zero intervention forbidden-rule violations, and no
negative output-depth stratum. Any overall negative difference, increased
intervention forbidden violations, or negative depth stratum is a
`negative-signal`; all other complete results are `mixed-or-null`.

These directions concern synthetic prompts and deterministic contract checks.
A positive signal is not human-effective and is not evaluation-green. No representative user
performed a usability task, and no clinical, causal,
patient-outcome, usability, or deployment claim follows.

## Optional independent review

Tier 2 may reuse the public matched pairs and rubric described in
[`evals/effectiveness/README.md`](../effectiveness/README.md), but it requires
two independent condition-blind reviewers. A model must not judge its own
responses. Without both reviews it remains `awaiting-independent-review`; it
never changes Tier 1 and is not representative-user evidence.

## Community feedback

Use the aggregate-only
[`benchmark-result` Issue Form](../../.github/ISSUE_TEMPLATE/benchmark-result.yml)
or the structured
[`usability-feedback` Issue Form](../../.github/ISSUE_TEMPLATE/usability-feedback.yml).
Reports are labeled `community-reported`, remain unverified self-reports, and
Issues never enter formal aggregates. Do not use Issues as evidence storage.

## Prohibited content

Never commit or paste patient data, private schema, an internal document,
condition key, task pack, nonce, API key, access token, credential, raw answer,
prompt, provider log, populated plan or index, response bundle, real generated
report, or any other sensitive or human-study material. A form acknowledgement
reduces but cannot eliminate accidental disclosure risk; maintainers should
close or redact unsafe reports using the available moderation controls.
