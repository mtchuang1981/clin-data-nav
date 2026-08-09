# Effectiveness evaluation framework

This directory contains a repository-native framework for an `offline dry run`
and a `separately authorized human pilot`. It is independent from the existing
deterministic response-contract Evals. The framework, its public synthetic
examples, and its reports do not prove real-use effectiveness, clinical
validity, causal validity, or patient-outcome validity. The Skill emits no telemetry,
and CI makes no external model call.

No human study has been authorized or conducted by adding this framework. The
checked-in reports are synthetic examples, not observed results.

## Stages and authority

| Stage | Safe repository activity | Separate authorization required |
|---|---|---|
| Public contract | Validate the public synthetic tasks, rubric, scripts, and checked-in aggregate example | No |
| Offline dry run | Generate an external synthetic assignment file and exercise the pipeline without people | Any external model invocation still requires its own approval and is never a CI step |
| Human-task commitment | Inspect the CLI and example commitment | Preparing the confidential pack, creating the actual nonce and commitment, and choosing governed storage |
| Human pilot | Inspect the fixed protocol and validators | Governance decision, consent, storage, recruitment, orientation, collection, rating, locking, and unlocking |
| Reporting | Render or check the checked-in synthetic aggregate report | Publishing real aggregate results and the post-lock task pack and nonce |

Never place an assignment file, participant row, human answer, blinded score
file, ratings lock, condition key, nonce, or confidential task pack in this
repository. Human-study inputs must remain in an approved external location.

## Public contract validation

This safe dry run validates the eight public matched pairs and the rubric:

```bash
python -m pytest tests/test_effectiveness_contract.py -q
```

The public files are [offline-tasks.yaml](offline-tasks.yaml) and
[rubric.yaml](rubric.yaml). They support pipeline testing and rater training;
they are not the confidential human task pack.

## Generate an external balanced assignment

Replace `<external-dir>` with a path outside this repository checkout:

```bash
python scripts/generate_study_assignments.py --study-id pilot-v1 --seed 20260809 --output <external-dir>/assignments.json
```

`--tasks` and `--rubric` are optional overrides; their defaults are the public
contracts in this directory. The CLI generates 64 rows for 16 synthetic
participant codes. The callable validator contract is exactly
`validate_assignments(rows, catalog, study_id, seed)`. An actual human-study
assignment is separately authorized and stays external.

## Commit and later verify a human task pack

Both the confidential task pack and the 32-byte nonce file must be external.
The commitment output should also remain in the approved external workflow
until its publication has been authorized.

```bash
python scripts/commit_human_task_pack.py create --task-pack <external-dir>/human-tasks.yaml --nonce-output <external-dir>/human-tasks.nonce --commitment-output <external-dir>/human-task-commitment.json
```

After collection and data lock, verify the published synthetic task pack and
nonce against the prior commitment:

```bash
python scripts/commit_human_task_pack.py verify --task-pack <external-dir>/human-tasks.yaml --nonce-file <external-dir>/human-tasks.nonce --commitment <external-dir>/human-task-commitment.json
```

Creating the real pack, nonce, or commitment is not an offline dry run and
requires separate governance and human-study authorization. Early task leakage
stops the affected batch and requires a completely new pack and commitment.

## Check agreement before condition unlock

The condition-blind agreement gate uses three external inputs and deliberately
does not accept a condition key:

```bash
python scripts/analyze_effectiveness.py agreement-check --study-manifest <external-dir>/study-manifest.json --scores <external-dir>/blinded-scores.json --ratings-lock <external-dir>/ratings-lock.json --output-summary <external-dir>/agreement-summary.json
```

The output status must be `eligible-for-locked-unlock`. A status of
`recalibrate-and-rescore-before-unlock` produces `exit code 3`: stop, calibrate
on designated synthetic training examples, complete a new independent scoring
round, create a new lock, and rerun the check. Keep the superseded round in
approved external audit storage; do not combine rounds and do not inspect or
use the condition key.

## Explicitly unlock and analyze

Analysis has four external inputs: the study manifest, blinded scores, ratings
lock, and condition key. It rechecks the agreement gate before reading the key
and requires the literal unlock flag:

```bash
python scripts/analyze_effectiveness.py analyze --study-manifest <external-dir>/study-manifest.json --scores <external-dir>/blinded-scores.json --ratings-lock <external-dir>/ratings-lock.json --condition-key <external-dir>/condition-key.json --unlock-after-ratings-lock --output-summary <external-dir>/aggregate-summary.json
```

Only the aggregate summary may be considered for later publication. This
command is not authorization to recruit, collect, unlock, analyze, or publish
human-study data. The four strict input contracts and unlock sequence are in
[input-schema.md](input-schema.md).

## Render or check bilingual aggregate reports

Omit `--check` to write both reports. Add it to compare existing files without
modifying them:

```bash
python scripts/render_effectiveness_report.py --summary evals/effectiveness/examples/synthetic-summary.json --english evals/effectiveness/examples/synthetic-report.md --traditional-chinese evals/effectiveness/examples/synthetic-report.zh-TW.md --check
```

The [English protocol](protocol.md), [Taiwan Traditional Chinese protocol](protocol.zh-TW.md),
[English template](report-template.md), and [Traditional Chinese template](report-template.zh-TW.md)
fix the claim and reporting boundaries. Positive, neutral, and negative
findings use the same aggregate structure.
