# Public simulation benchmark report template

This template contains no benchmark result. The renderer replaces every
`<value>` from one validated aggregate summary; do not fill it manually.

## Identity and scope

| Field | Value |
|---|---|
| `benchmark_id` | <value> |
| `status` | <value> |
| `direction` | <value> |
| `plan_sha256` | <value> |
| `skill.commit` | <value> |
| `skill.tag` | <value> |
| `skill.archive_sha256` | <value> |
| `model.*` | <value> |
| `execution_attestation.*` | <value> |

## Aggregate result

| Field | Value |
|---|---|
| `overall.*` | <value> |

## Paired changes

| Field | Value |
|---|---|
| `paired_counts.*` | <value> |

## Output-depth strata

| Field | Value |
|---|---|
| `depth.<output_depth>.*` | <value> |

## Per-case stability

| Field | Value |
|---|---|
| `case.<case_id>.*` | <value> |

## Forbidden-rule guardrail

| Field | Value |
|---|---|
| `forbidden_violations.*` | <value> |

## Limitations and next evidence step

These results concern only public synthetic prompts and deterministic contract checks.
Model metadata and the execution attestation are externally reported and are not provider-verified.
Deterministic rules do not measure all semantic quality.
No representative user performed a usability task.
No clinical-validity, causal-validity, patient-outcome, or deployment-ready claim follows from this report.
`positive-signal` is not `human-effective` or `evaluation-green`.
