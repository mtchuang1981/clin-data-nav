# Offline Eval Results

| Case | Baseline score | Forward score |
| --- | ---: | ---: |
| `institutional-sql-without-dictionary` | 10 | 80 |
| `stale-codingbook` | 20 | 90 |
| `tmucrd-public-profile` | 30 | 30 |

Scores are deterministic outputs of `scripts/evaluate_response.py` using the
catalog and rubric in this directory. A rules-based pass is not proof of
overall semantic quality.
