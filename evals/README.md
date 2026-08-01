# Offline Eval Results

`cases.yaml` defines 12 catalog cases with 12 scored fixture pairs. Every case
has a checked-in baseline response and forward response.

<!-- BEGIN GENERATED EVAL SUMMARY -->
| Case | Output depth | Baseline | Forward |
| --- | --- | ---: | ---: |
| `adam-quick-explanation` | quick explanation | 0 FAIL | 100 PASS |
| `teae-sas-spec` | implementation specification | 0 FAIL | 100 PASS |
| `sas-optimization-lexjansen` | evidence navigation | 10 FAIL | 210 PASS |
| `institutional-sql-without-dictionary` | implementation specification | 10 FAIL | 100 PASS |
| `stale-codingbook` | implementation specification | 20 FAIL | 100 PASS |
| `cdisc-variable-definition` | quick explanation | 10 FAIL | 100 PASS |
| `omop-phenotype` | implementation specification | 0 FAIL | 100 PASS |
| `tmucrd-public-profile` | evidence navigation | 30 FAIL | 100 PASS |
| `descriptive-rwd-no-tte` | research design | 0 FAIL | 140 PASS |
| `causal-rwd-tte-handoff` | research design | 10 FAIL | 200 PASS |
| `causal-rwd-incomplete-readiness` | research design | 0 FAIL | 150 PASS |
| `build-rwe-sap-unavailable` | implementation specification | 20 FAIL | 170 PASS |

> These keyword fixtures test repository behavior contracts, not clinical validity or real-world effectiveness.
<!-- END GENERATED EVAL SUMMARY -->

Scores are deterministic outputs of `scripts/evaluate_response.py` using the
catalog and rubric in this directory. They are regression evidence for the
checked-in response pairs, not proof of semantic correctness or clinical validity.
They also do not prove source accuracy, causal validity, or complete real-world
coverage.
