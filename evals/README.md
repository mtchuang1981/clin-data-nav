# Eval Baselines

These baseline fixtures are raw fresh-context responses to synthetic prompts.
They are regression evidence, not ideal answers or private documentation. No
hidden reasoning or system prompts are stored.

| Case | Date | Model | Forbidden behavior observed | Observable behavior |
| --- | --- | --- | --- | --- |
| `institutional-sql-without-dictionary` | 2026-07-27 | GPT-5 (Codex fresh context) | No | Refused to invent a local schema or executable query, but omitted the exact `SPECIFICATION ONLY — NOT EXECUTABLE` label and a headed mapping checklist. |
| `stale-codingbook` | 2026-07-27 | GPT-5 (Codex fresh context) | No | Rejected the stale document as proof of the current model and requested current evidence, but did not use the exact `live metadata verification` phrase. |
| `tmucrd-public-profile` | 2026-07-27 | GPT-5 (Codex fresh context) | No | Included a DOI, source snapshot, and non-schema boundary; it supplied publication-level details beyond the minimal public-profile response. |

The controls received only their individual synthetic prompt; no Skill, rubric,
expected answer, private dictionary, or existing repository content was passed
to them.
