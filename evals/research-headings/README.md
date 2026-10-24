# Opt-in research heading evaluation

This is a separate contract check, not a new model benchmark or a replacement
for the frozen core/compiler catalogs. It reuses `scripts/evaluate_response.py`
and the existing case's content and safety requirements.

## Select the contract explicitly

The Python API defaults to `heading_contract="legacy-v1"`. The CLI also defaults
to `legacy-v1`. Historical simulation callers do not select the new contract and
remain unchanged. There is no auto-detection from the response language.

For the new contract, use:

```bash
python scripts/evaluate_response.py --case omop-phenotype --response tests/fixtures/research_headings/omop-phenotype.zh-TW.md --heading-contract research-bilingual-v1
```

For historical behavior, omit `--heading-contract` or select `legacy-v1`.
The translated fixture intentionally fails under legacy. Do not substitute the
new contract when replaying an archived benchmark or reinterpret its scores.

Successful opted-in CLI JSON contains `heading_contract: research-bilingual-v1`.
Default and explicit legacy JSON retain the original shape with no new field.
The Python `Evaluation` result shape remains unchanged. API callers must retain
their selected contract ID alongside any newly produced report.

## Closed heading vocabulary

The single production alias map is
[`research-heading-contract.json`](../../skills/clin-nav/references/research-heading-contract.json).
It contains five exact canonical-English/Traditional-Chinese pairs. Do not add
synonyms, translate all headings, or silently extend this versioned map. A new
accepted vocabulary requires a separately reviewed contract change.

Under `research-bilingual-v1`:

- English, Traditional Chinese and mixed headings identify the same five
  research sections. Catalog section selectors remain canonical English.
- Required sections must be visible Markdown H2 headings. Prose, examples in
  fenced/indented code, approximate titles, suffixes and wrong levels do not count.
- Existing rubric normalization still applies. Matching both aliases does not
  earn extra points for the same section.
- The same Chinese titles remain reserved as research sections when another
  output depth is selected. They cannot bypass cross-depth restrictions.
- Common headers, `Handoff status`, output-depth labels, other depth titles,
  content rules, forbidden patterns, scores and thresholds remain unchanged.
- Unknown contract IDs or missing/invalid new-contract data fail closed, without
  fallback or retry. Legacy does not depend on the new JSON reference.

## Evidence boundary

The new public fixture changes only the five headings of the existing synthetic
OMOP phenotype response. Its body remains English deliberately: it isolates
heading recognition, not translation quality or bilingual semantic coverage.

`tests/test_research_heading_contract.py` checks positive/negative structure,
content and safety retention, CLI contract identity, unusable-contract rejection,
and unchanged aggregate outputs for 36 pre-change core/compiler fixture cells.
These are deterministic format and regression checks, not expert content review,
source verification, model effectiveness, clinical validity or permission to
execute code. A responsible case owner must still review real deliverables.

No private consultations or answers, participant materials, model responses or
new 72-cell campaign are used. Existing fixture scores and archived evidence
are not rewritten.
