# Offline Eval Results

`cases.yaml` defines 11 catalog cases. The table below covers only the 3 scored fixture pairs
that currently have both a checked-in baseline response and a
checked-in forward response.

| Case | Baseline score | Forward score |
| --- | ---: | ---: |
| `institutional-sql-without-dictionary` | 10 | 80 |
| `stale-codingbook` | 20 | 90 |
| `tmucrd-public-profile` | 30 | 30 |

Scores are deterministic outputs of `scripts/evaluate_response.py` using the
catalog and rubric in this directory. They are regression evidence for the
three checked-in response pairs,
not proof of semantic correctness or clinical validity and not complete
coverage of all 11 catalog cases.
