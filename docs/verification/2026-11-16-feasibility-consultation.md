# Feasibility consultation refinement — local verification

## Change boundary

The user approved the proposed refinement on 2026-11-16. Changes are confined
to the public Skill, one new reference, routing/output references, a separate
synthetic semantic-review suite and its integrity/packaging tests. No private
Adapter, original consultation, institutional mapping, patient data, real-data
tool call, installed Skill copy or publication is part of this change.

Agent metadata was reviewed and retained: the existing generic prompt remains
compatible. No dependency, maturity label, compiler operation, OMOP connector
contract, frozen benchmark input or release version was changed.

## Red and green checks

- Before guidance edits, the new targeted tests failed: missing routed and
  packaged consultation reference and missing separate scenario catalog.
- After edits, consultation, skill-contract and structure tests passed:
  **54 passed**. These are integration/fixture checks, not model-effectiveness
  evidence. The separate catalog deliberately has no regex/heading scoring.
- Full `python -m pytest -q`: **1957 passed, 13 skipped**, exit 0. Skips concern
  symlink/reparse privileges, filesystem case/trailing-space behavior and a
  POSIX-only cleanup test. No skipped check is reported as passing.
- `python scripts/validate_skill.py`: exit 0.
- `python scripts/check_public_boundary.py`: exit 0.
- `python scripts/package_skill.py --check-reproducible`: exit 0.
- Core and compiler-pipeline `render_eval_summary.py --check`: exit 0.
- `git diff --check`: exit 0.

Commands ran through RTK on the local Windows/Python 3.13 environment. Targeted
tests were repeated after the final routing-table and prose edits. Final file
review and final package/boundary checks are completed before delivery.

## Independent behavioral review

Fresh-context agents read the public Skill and applicable references only.
Baseline repeats used the HEAD versions; forward repeats used the working-tree
versions. Agents received actual synthetic user prompts without expected
actions, prior answers or the grading rubric. Outputs were manually read.

The initial combined case tested unflagged semantic conflict, mixed modalities,
an empty exact search, unread pages and unresolved study choices. The baseline
already handled these safety issues correctly; it returned a full formal
implementation specification for a coordinator orientation request. The forward
answer retained those judgments while using a coordinator review sheet.

There were five baseline and five forward orientation samples: one combined
candidate-review prompt per version, plus four fresh-context repetitions of
the same ALPHA/modality-Q definition-review prompt per version. All five
baseline outputs used a formal document (one implementation specification,
four research designs). All five forward outputs used coordinator-oriented
decision/review sheets. Manual review found no invented fixed timing rule,
claim of real counts or unauthorized institutional operation in these samples.
This is a shape/routing observation across two prompts, not five identical
paired trials or a measured improvement in clinical accuracy. Semantic safety
was already present in the baseline and was retained in the combined forward
case. Forward responses still vary in length and recommendation detail.

One additional supplied-record question in the final forward context covered
invalid site enums and a too-short term. The response correctly identified
both argument errors, did not guess cross-tool site mappings or pad the term,
and distinguished a correction proposal from an actual tool invocation. This
was record interpretation only, not a runtime integration test.

A separate explicit formal-specification request retained all implementation
sections, logical inputs/keys/grain, time and mapping unknowns, conceptual
maturity, actionable gaps and the non-executable gate. Its agent also reviewed
the public reference changes and found no concrete contradiction or permission
expansion.

## Claim limits

This is a small local behavioral check with manual review, not a randomized
benchmark, formal clinical validation or proof of general effectiveness.
No private tool calls, real dictionary lookups, runtime argument corrections,
compiler invocation or institutional compatibility acceptance were tested.
The seven-case catalog provides reusable scenarios; catalog validation does
not imply seven independently executed semantic tests. Proposed defaults remain
unapproved study parameters until the responsible investigator confirms them.
