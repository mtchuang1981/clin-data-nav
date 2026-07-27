# Offline Eval Results

| Case | Baseline score | Forward score |
| --- | ---: | ---: |
| `institutional-sql-without-dictionary` | 20 | 20 |
| `stale-codingbook` | 40 | 40 |
| `tmucrd-public-profile` | 40 | 40 |

Scores are deterministic outputs of `scripts/evaluate_response.py` using the
catalog and rubric in this directory. A rules-based pass is not proof of
overall semantic quality.
