# Opt-in research heading contract

The user approved this compatibility design on 2026-10-23 after the existing
English fixture passed and its five translated headings failed.

## Selected approach

Add `research-bilingual-v1` as an explicit evaluator choice. Keep `legacy-v1`
as the default, including old Python calls, CLI JSON and benchmark callers.
Global alias acceptance was rejected because it changes historical replay.
Do not create a second evaluator or change scoring weights or thresholds.

The shared, installable reference
`skills/clin-nav/references/research-heading-contract.json` contains exactly
these five canonical-to-Traditional-Chinese pairs:

| Canonical | Accepted Traditional Chinese |
| --- | --- |
| Primary intent and design route | 研究意圖與設計路徑 |
| Design fields and time anchors | 設計欄位與時間軸 |
| Data suitability and claim boundary | 資料適用性與主張邊界 |
| Bias and validation gaps | 偏差與驗證缺口 |
| Analysis or diagnostics | 分析或診斷 |

## Semantics and boundaries

- Add keyword-only `heading_contract="legacy-v1"` to `evaluate_response`.
- Add CLI `--heading-contract` with the two closed choices. Only opted-in CLI
  JSON adds `heading_contract`; legacy output shape remains unchanged.
- For research design, match either member of each pair as the same strict
  visible Markdown H2. Apply the same aliases to canonical case-required sections.
- Count a canonical section once. Preserve English, Chinese and mixed headings.
- Keep prose, code, approximate synonyms, wrong heading levels, missing sections,
  common headers, required content and forbidden-pattern handling unchanged.
- Under the new contract, translated research headings are also reserved when
  detecting another depth's sections, at the existing H1–H6 levels. Do not allow
  translation to bypass a cross-depth restriction.
- Output-depth selection, other depth headings, `Handoff status` and common
  labels are not translated. This does not add a new depth-label validator.
- Unknown contract IDs and unusable new-contract data fail closed. Legacy does
  not read the new reference and remains usable if it is absent or malformed.
- Keep catalog selectors canonical English. Do not edit frozen catalogs,
  rubrics, benchmark inputs, historical answers or reports.

## Delivery and evidence

Test evaluator behavior first using public synthetic fixtures. Preserve a
pre-change aggregate digest of all 36 core/compiler baseline/forward results.
Compare the default and explicit legacy results to that exact digest; this is
an API compatibility check, not a model-effectiveness result.

Review Skill routing, output references, UI metadata and Evals. Add a separate
usage/validation record for the opted-in contract. Run full pytest and required
gates, generated summary checks, and independent review. No private Adapter,
consultations, patient data, model campaign, version bump, merge, push, tag or
Release in this local implementation.
