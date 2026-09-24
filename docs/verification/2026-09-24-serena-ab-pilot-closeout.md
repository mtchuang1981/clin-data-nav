# Serena A/B Pilot: Aggregate Closeout

Date: 2026-09-24

## Decision

The Serena A/B pilot completed, but Serena did **not** meet the prespecified
threshold for default use in `clin-data-nav`. Keep it optional and close this
evaluation line. The decision is about this repository and the tested setup;
it is not a general claim about Serena.

## Verified aggregate results

The formal read-only navigation comparison used three public-repository
maintenance tasks, three repetitions per condition, and 18 valid runs in
total. It was run in WSL with Codex CLI 0.156.1, `gpt-6-sol` at medium
reasoning, repository commit `00c4519b9b409f2dd8bed7066cfbdc27ca640ae5`,
and a pinned Serena commit. Both conditions passed correctness in all nine
runs. All nine Serena runs made a successful Serena MCP call: 43 successful
calls in total, with no Serena MCP errors.

| Median | Baseline | Serena | Change |
| --- | ---: | ---: | ---: |
| Total tokens | 717,994 | 930,853 | +29.65% |
| Tool calls | 30 | 35 | +16.67% |
| Elapsed seconds | 293.312 | 313.937 | +7.03% |

The prespecified adoption gate required roughly 15% fewer total tokens,
nondecreasing correctness, no greater than 25% deterioration in tool calls
or time, consistent benefit on at least two tasks, and benefit for both
`symbol-rename` and `failing-test`. Correctness and the tool/time limits
passed. The token and task-direction requirements failed: the Serena median
token count increased on all three tasks. Excluding the marked first Serena
run and its paired baseline still yielded +29.53% total tokens.

An earlier availability-only comparison showed 7.61% fewer tokens, but its
nine Serena-condition runs made zero Serena MCP calls. It therefore cannot
establish a Serena effect. A 2026-09-23 Windows smoke test was invalidated by
the Codex command helper failure; the completed WSL comparison supersedes it.

## Evidence and limits

The repository-external evidence remains under
`CodexPilot/clin-data-nav-serena-ab-pilot/results/20260924-091602-wsl`.
The external `audit-results.py` completed successfully and checked the run
count, correctness, paired keys, cold-start marker, and Serena MCP activity.
This public record includes only aggregate results and evidence hashes:

| External file | SHA-256 |
| --- | --- |
| `PILOT-REPORT.md` | `c288d288d12e70efee90e7457d4cc353acb2192a48cd95b6934f9b4aac98029e` |
| `results/20260924-091602-wsl/summary.csv` | `0303e808c45b8990518864cef9c5940410c05e4d583b51667c98962c83e5a3e0` |

This was a small synthetic coding-task pilot. It does not measure human
usability, clinical outcomes, current `main`, other repositories, or actual
billing cost. Most recorded tokens were cached input tokens. No raw model
responses, run logs, or private-system material are included here.
