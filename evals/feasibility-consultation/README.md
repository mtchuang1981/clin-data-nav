# Synthetic feasibility consultation scenarios

This separate suite tests decision quality, search interpretation, tool-input
handling and delivery fit. It does not modify the frozen core benchmark or the
compiler-pipeline regex catalog. All prompts and identifiers are fictional.

## How to review

Give an independent fresh-context agent a case prompt and the applicable
Skill version, not expected actions, rejection actions or this rubric. Restrict
it to supplied synthetic summaries and public Skill references. Do not call a
private tool, open a private artifact or execute a real-data query.

Read the actual response and, when permitted and supplied, tool-call trace.
For each applicable criterion, record pass, fail or not observed with the
specific action/omission and supporting excerpt. Check expected and rejected
actions semantically; a keyword, heading, or statement of intent alone is not
evidence that a tool was called or a decision was made. Proposals and actual
operations must remain distinct. A critical unsafe action fails the case.
Missing evidence is not a pass. Do not give the agent the desired answer.

The pytest checks validate packaging, reference reachability and scenario
integrity only. They do not score model judgment or prove effectiveness.
Repeat independent runs before claiming stable improvement; report sample
size, mixed results and untested paths. Do not reuse unrelated historic passes.

## Initial local observation — 2026-11-16

One independent baseline and one fresh-context forward run use the same
combined synthetic coordinator prompt. The baseline correctly handled
unflagged semantic conflict, zero-hit ambiguity, mixed modalities and unread
pages, but returned a full formal contract instead of the desired coordinator
brief. These semantic behaviors are regression targets, not claimed new fixes.
The forward outcome and verification limits are recorded after actual review
in the dated repository verification note. This is a bounded observation,
not a benchmark effectiveness or institutional compatibility claim.
