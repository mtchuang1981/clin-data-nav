# Simulation benchmark aggregate-summary schema

This schema describes the safe, aggregate-only JSON consumed by
`scripts/render_simulation_benchmark.py`. The root is a closed object: unknown,
missing, human-effectiveness, green-readiness, response, path, prompt, log, or
credential fields are invalid. Real evaluation emits `synthetic_example: false`.
The checked-in contract example alone may be validated with an explicit
synthetic opt-in after the renderer CLI proves all three resolved example paths.

## Root fields

| Field | JSON type | Rule |
|---|---|---|
| `schema_version` | string | Controlled value `"1"`. |
| `benchmark_id` | string | Safe lowercase hyphenated identifier. |
| `synthetic_example` | boolean | Literal `false` for real summaries; literal `true` only for the checked-in example opt-in. |
| `status` | string | Controlled value `benchmark-observed`; completeness does not imply a favorable direction. |
| `direction` | string | Recomputed controlled value: `positive-signal`, `mixed-or-null`, or `negative-signal`. |
| `plan_sha256` | string | Lowercase 64-character SHA-256 of the canonical frozen plan. |
| `catalog_sha256` | string | Lowercase SHA-256; must equal the current public `evals/cases.yaml` bytes. |
| `rubric_sha256` | string | Lowercase SHA-256; must equal the current public `evals/rubric.yaml` bytes. |
| `skill` | object | Exact released-Skill binding defined below. |
| `model` | object | Exact shared model settings defined below. |
| `execution_attestation` | object | Exact externally asserted projection defined below. |
| `repeats` | integer | Exactly `3`; booleans are invalid. |
| `cell_counts` | object | Exact `expected,observed` nonnegative integer fields; both recompute to `72`. |
| `overall` | object | Exact paired aggregate defined below. |
| `paired_counts` | object | Exact nonnegative integer counts `both_fail,both_pass,improved,worsened`; sum is 36. |
| `forbidden_violations` | object | Exact nonnegative integer `control,intervention` counts recomputed from cases. |
| `output_depth_results` | array | One exact recomputed row per canonical public output depth, in sorted order. |
| `case_results` | array | Exactly twelve recomputable rows in public catalog order. |
| `claim_boundaries` | array | Exact ordered controlled values listed under Claim boundary. |

## Released Skill binding (`skill`)

The object has only `archive`, `archive_sha256`, `commit`, `manifest`,
`manifest_sha256`, `member_set_sha256`, `tag`, `tag_object`, and `version`.
Names must agree with the semantic `version`; all three SHA-256 fields are
lowercase 64-character digests; `commit` and `tag_object` are lowercase
40-character Git object IDs; `tag` identifies an annotated release tag. The
whole object must satisfy the public released-Skill binding validator.

## Model and execution provenance

`model` has only `provider`, `id`, `snapshot`, `seed_policy`,
`temperature`, `top_p`, and `max_output_tokens`. Identity values are bounded
single-line identifiers. `temperature` and `top_p` are finite JSON numbers;
the renderer formats them to six decimal places. `max_output_tokens` is a
nonnegative integer and not a boolean.

`execution_attestation` has only `assertion_basis`, `completed_at`,
`model_provider`, `model_id`, `model_snapshot`, `runner_name`,
`runner_version`, `plan_followed`, `fresh_sessions`, `offline`, and
`shared_configuration_unchanged`. `assertion_basis` is exactly
`externally-asserted`; `completed_at` is a timezone-aware timestamp; model
identities exactly repeat `model`; runner values are bounded identifiers; and
each controlled boolean is literal `true`. Although the summary validator
accepts any single-character ISO date/time separator, the Markdown renderer
fails closed when a displayed string contains CR, LF, or `|`; therefore a
renderable `completed_at` uses a table-safe ISO separator such as `T`. These
declarations are not provider verification.

## Aggregates and recomputation

`overall` has only `pairs`, `control_passes`, `control_pass_rate`,
`intervention_passes`, `intervention_pass_rate`, and `difference`. Counts are
nonnegative integers. Rates and the intervention-minus-control `difference`
are JSON decimals rounded once to six places from exact integer fractions.

Every `output_depth_results` row adds `output_depth`, `case_count`,
`paired_counts`, and `forbidden_violations` to the exact `overall` fields.
Rows are recomputed from `case_results` and ordered by `output_depth`.

Every `case_results` row has only `case_id`, `output_depth`,
`control_passes`, `intervention_passes`, `paired_counts`,
`forbidden_violations`, and `stability`. Case identity/depth and order must
match the public catalog. Each paired-count object has only `both_fail`,
`both_pass`, `improved`, and `worsened`, summing to `repeats`.
`control_passes = both_pass + worsened`; `intervention_passes = both_pass +
improved`. Each forbidden-count object has only `control,intervention`.
Each `stability` object has only `control,intervention`, with controlled value
`stable-pass`, `stable-fail`, or `variable`, recomputed from its pass count and
three repeats.

The root counts, rates, paired counts, forbidden counts, depth rows, stability,
cell counts, and `direction` are all recomputed. `negative-signal` takes
precedence when the overall difference is negative, intervention forbidden
violations exceed control, or any depth difference is negative.
`positive-signal` requires difference at least `0.200000`, improved greater
than worsened, zero intervention forbidden violations, and no negative depth.
All other complete results are `mixed-or-null`.

## Claim boundary

`claim_boundaries` is exactly, in order:

1. `public-synthetic-prompts-only`
2. `deterministic-contract-checks-only`
3. `no-representative-user-evidence`
4. `no-clinical-causal-patient-outcome-or-deployment-claim`

A `benchmark-observed` status or `positive-signal` direction is not
`human-effective`, `evaluation-green`, clinical validity, causal validity,
patient-outcome evidence, or deployment readiness.
