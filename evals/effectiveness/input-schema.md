# Effectiveness analysis input schema

The analyzer fails closed on four external JSON inputs: a study manifest,
condition-blinded scores, a ratings lock, and a condition key. Every input path
must resolve outside the repository checkout. All schemas use
`schema_version: "1"`; unknown or missing keys are rejected. The public
repository may receive only a validated aggregate summary, never these inputs.

## Normative assignment contract

This visible contract is the sole exact assignment schema and validator API.
Lists are closed: keys may not be omitted, duplicated, or added.

```yaml
assignment_top_level_keys:
  - schema_version
  - study_id
  - seed
  - assignments
assignment_row_keys:
  - answer_id
  - participant_code
  - stratum
  - pair_id
  - variant
  - output_depth
  - condition
  - order
validator_api: validate_assignments(rows, catalog, study_id, seed)
```

## 1. Study manifest

The manifest has exactly these keys:

- `schema_version`, `study_id`, and `protocol_commit`;
- `skill_version`, `skill_commit`, `codex_surface`, `model`,
  `reasoning_effort`, `service_tier`, `python_version`, and `platform`;
- `study_started_at`, `study_ended_at`, `task_commitment_sha256`, and
  `task_commitment_verified`;
- `bootstrap_seed`, `bootstrap_resamples`; and
- `sessions`.

Commit fields are lowercase 40-character hexadecimal strings; the task
commitment is lowercase 64-character hexadecimal; study timestamps are
timezone-aware ISO 8601 values in chronological order; and task commitment
verification must be true. Bootstrap resamples are an integer from 1,000
through 100,000. Environment strings are non-empty, single-line, and no longer
than 200 characters.

`sessions` contains exactly 16 rows. Every row has exactly:

- `participant_code`;
- `stratum`;
- `assignment_version`;
- `session_date`; and
- `environment_fingerprint`.

Participant codes are exactly `B01` through `B08` with `beginner`, and `P01`
through `P08` with `professional`. The assignment version is shared, session
dates fall inside the study period, and the environment fingerprint is the
SHA-256 of canonical sorted JSON containing exactly the eight environment
fields listed above. A fingerprint mismatch is a stop-rule failure.

## 2. Condition-blinded scores

The top-level object has exactly `schema_version`, `study_id`, `observations`,
`rater_scores`, `adjudications`, and `sus_responses`. It contains no condition
mapping.

### Observation rows

Every observation has exactly:

- identity and task fields: `answer_id`, `participant_code`, `stratum`,
  `task_pair_id`, `task_variant`, `output_depth`, and `order`;
- timing fields: `started_at`, `ended_at`, `completion_status`, and
  `completion_seconds`;
- rubric aggregates: `mandatory_complete`, `quality_met`,
  `quality_applicable`, `quality_score`, `critical_violation`, and
  `criterion_scores`;
- workload fields: `nasa_tlx_ratings` and `nasa_tlx_weights`; and
- self-ratings: `confidence_before`, `confidence_after`,
  `understanding_before`, and `understanding_after`.

`answer_id` is 16 uppercase hexadecimal characters. `task_variant` is `A` or
`B`; `order` is 1 through 4; task/depth pairs must exist in the public catalog.
Timestamps are timezone-aware, within the study period, and their whole-second
difference equals the non-negative integer `completion_seconds`.

`completion_status` is one of `completed`, `timeout`, `abandoned`, or
`technical_failure`:

- `completed` and `timeout` are scored. All rubric, TLX, confidence, and
  understanding fields are populated.
- `abandoned` and `technical_failure` are unscored. The following fields are
  JSON null: `mandatory_complete`, `quality_met`, `quality_applicable`,
  `quality_score`, `critical_violation`, `criterion_scores`,
  `nasa_tlx_ratings`, `nasa_tlx_weights`, `confidence_before`,
  `confidence_after`, `understanding_before`, and `understanding_after`.
  Their timestamps, status, and `completion_seconds` remain populated.

For a scored row, `criterion_scores` is in the task contract's exact order and
contains one row per assigned criterion. Every criterion row has exactly
`criterion_id`, `applicable`, and `met`:

- mandatory criteria always have `applicable: true` and boolean `met`;
- quality criteria have boolean `applicable`; when applicable, `met` is
  boolean; when not applicable, `met` is JSON null; and
- the detailed rows must reproduce `mandatory_complete`, `quality_applicable`,
  and `quality_met` exactly.

All quality criteria may be N/A. In that case `quality_applicable=0`,
`quality_met=0`, and the aggregate quality rate is null and not estimable.
Abandonment is primary failure, while technical failure is missing for
complete-case primary analysis.

### Normative primary-outcome truth table

This visible truth table is the sole exact primary-success rule. The last field
states whether varying quality inputs may change any row's result.

```yaml
primary_success_truth_table:
  - mandatory_complete: false
    critical_violation: false
    success: false
  - mandatory_complete: false
    critical_violation: true
    success: false
  - mandatory_complete: true
    critical_violation: false
    success: true
  - mandatory_complete: true
    critical_violation: true
    success: false
quality_criteria_affect_primary: false
```

`quality_score` is an integer from 0 through 100. NASA-TLX has six integer
ratings from 0 through 100 and six integer weights from 0 through 5 that sum to
15. Confidence and understanding fields are integers from 1 through 5.

### Original rater rows

Each scored answer has exactly two distinct original rater rows; unscored
answers have none. A row has exactly `answer_id`, `rater_code`, `success`,
`critical_violation`, and `ordinal_quality`. Rater codes are safe uppercase
codes; success and critical violation are booleans; ordinal quality is an
integer from 0 through 4. Success cannot coexist with a critical violation.

### Adjudication rows

Any disagreement in the original success, critical-violation, or ordinal
quality decisions requires exactly one third-person adjudication. Complete
agreement forbids adjudication. A row has exactly `answer_id`,
`adjudicator_code`, `final_success`, `final_critical_violation`,
`final_ordinal_quality`, and `rationale_code`. The adjudicator cannot be either
original rater. The rationale is one of `critical-safety`,
`mandatory-criterion`, `quality-threshold`, `ordinal-quality`, or
`other-prespecified`; narrative rationale and answer excerpts are rejected.

Primary-success semantics are defined only by the normative truth table above.
The 0-through-100 quality score and 0-through-4 ordinal rating remain separate
secondary measures.

### SUS rows

Each `sus_responses` row has exactly `participant_code` and `items`. Participant
codes are unique and must occur in the observations. `items` contains ten
integers from 1 through 5.

## 3. Ratings lock

The lock has exactly `schema_version`, `study_id`, `scores_sha256`,
`ratings_complete`, `rater_codes`, and `locked_at`. `scores_sha256` is computed
over the raw score-file bytes exactly as read, not parsed or normalized JSON.
It must match SHA-256 of those raw score-file bytes. `ratings_complete` is true,
the two distinct rater codes exactly match the score file, and `locked_at` is a
timezone-aware timestamp no earlier than study end.

## 4. Condition key

The key has exactly `schema_version`, `study_id`, and `mappings`. Each mapping
has exactly `answer_id` and `condition`, where condition is `control` or
`intervention`. Answer IDs are unique and exactly match the blinded observation
set: no missing or additional mapping is accepted.

## Condition-blind agreement gate and exact unlock sequence

1. Validate the manifest, blinded scores, and ratings lock as closed schemas;
   verify study ID, participant/session membership, timing, two-rater set, and
   the raw-byte SHA-256 lock.
2. Run `agreement-check` without a condition key. Raw binary agreement must be
   at least 0.80; each estimable binary or linear-weighted ordinal kappa must be
   at least 0.60. A null kappa caused by zero marginal variation does not fail
   by itself because raw binary agreement remains the guardrail.
3. If status is `recalibrate-and-rescore-before-unlock`, stop before reading the
   key. Calibrate on designated synthetic examples, independently rescore every
   affected answer, create a new complete lock, and rerun the gate. Never merge
   scoring rounds.
4. Only status `eligible-for-locked-unlock` may proceed. Validate the separate
   condition key and confirm the same `study_id` across all four external
   inputs.
5. Require the explicit CLI flag `--unlock-after-ratings-lock`, then merge
   condition by `answer_id` and validate the fixed 64-observation layout: 16
   participants, four orders and four depths per participant, with two tasks
   per condition.
6. Write aggregate-only summary JSON. Never write participant-level unlocked
   rows to the repository.

## Rejected data

Closed schemas reject every unknown key. In particular, names, email
addresses, credentials, patient identifiers, `answer_text`, free-text answers,
identifying quotations, narrative rationale, and a direct `condition` field in
blinded observations are forbidden. The inputs also reject direct identifiers,
unknown tasks or depths, duplicate answer or participant mappings, incomplete
rater rows, and any condition key that does not map the exact blinded answer
set. Validation errors must not echo rejected field values or human text.
