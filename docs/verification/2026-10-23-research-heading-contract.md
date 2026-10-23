# Opt-in research heading contract verification

Verified locally on 2026-10-23 (Asia/Taipei).
Base: `e7572b0c5b00f21054cbef52edf5c9b0731cef52`.
Branch: `codex/research-heading-contract`.

## Delivered contract

`research-bilingual-v1` is an explicit opt-in to the existing evaluator. It
recognizes exactly the five approved English/Traditional-Chinese research
heading pairs in the shared installable JSON reference. English and mixed
headings are supported. Existing catalog section selectors remain English.

`legacy-v1` remains the default for the API, CLI and historical benchmark
callers. It does not load the new reference. Existing `Evaluation` fields and
default CLI JSON are unchanged. Only selected new-contract CLI JSON adds
`heading_contract`; API callers must record their selected contract separately.

The new contract does not translate common headers, other depth titles,
`Handoff status` or output-depth labels. It does not add an output-depth-label
validator or change content patterns, forbidden claims, scoring or thresholds.
No new evaluator, network dependency or automatic fallback was introduced.

## Test evidence

- RED: the first newly written opt-in test failed before implementation because
  `evaluate_response` had no `heading_contract` keyword.
- GREEN: 57 new contract tests passed, including Chinese/mixed/English scores,
  missing sections, prose/code headings, approximate names, incorrect heading
  levels, duplicate scoring, cross-depth aliases, missing content, unsafe claims,
  case-sensitive rubric behavior, invalid contract data and CLI error behavior.
- Focused evaluator/Eval/documentation tests: 139 passed in 2.27 seconds.
- Full official Python 3.11.9 suite: 1944 passed, 13 environment skips in
  170.93 seconds. Skips concern unavailable symlink privileges, filesystem case
  and trailing-space semantics, and POSIX dir-fd cleanup, not verified passes.
- Required Skill validation, public-boundary validation and reproducible
  packaging passed. Core and compiler generated Eval summaries passed their
  check mode. Supplemental skill-creator validation passed with `-X utf8`.
- Git diff checks passed. No catalog, rubric, previous baseline/forward fixture,
  archived benchmark input/result, UI metadata or version was changed.

Before implementation, all 36 core/compiler baseline and forward evaluations
were serialized as `[suite, arm, asdict(result)]`, ordered by suite, catalog
and then baseline/forward. SHA-256 of UTF-8 JSON with `ensure_ascii=False`,
`sort_keys=True` and compact separators was:

```text
6c7db3794be2f5b74107a27ae9dae5e385aa82cfabb98be691bf4b67b72b8757
```

Both default and explicit legacy evaluation retain that exact result digest.
The independent reviewer also executed the base evaluator in memory and
confirmed the same 36-cell digest. This preserves actual rule results and
scores, not merely pass/fail totals.

The new public fixture changes only five headings of the existing synthetic
OMOP phenotype response; its English body deliberately remains unchanged.
It scores 90/FAIL under legacy and 140/PASS only with the new contract.
That difference is heading recognition, not evidence of better research content.

## Independent review and boundaries

A fresh read-only reviewer found no Critical, Important or Minor issue. It
additionally checked five aliases across three other depths and H1–H6 (90
combinations), observing the expected forbidden-section failures. It did not
claim to witness the main test process, TDD history, medical validity or model
effectiveness. The observed main-process commands above provide gate evidence.

Skill routing, both output references, unchanged UI metadata and related Evals
were reviewed. The production alias vocabulary is maintained in one JSON
reference rather than duplicated in the output guides.

This is deterministic format/compatibility/safety-rule testing, not a model
campaign, full bilingual content assessment, case-owner review, clinical
validation or private Adapter acceptance. No private consultation, schema,
patient material or human participant data was accessed. No historical answer
was rescored and no existing failure was retrospectively changed to a pass.

Delivery is local only. Main and its unrelated untracked backlog remain
untouched. No push, PR, tag, version bump or Release is included in this task.
