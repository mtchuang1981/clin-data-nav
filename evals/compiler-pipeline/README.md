# Governed compiler pipeline contract cases

This optional suite uses the existing evaluator and rubric, separately from
the frozen core catalog and historical simulation benchmark. Its hand-authored
synthetic fixtures are regression examples, not model observations, private
adapter conformance, clinical validity, or human effectiveness evidence.

Run `python scripts/render_eval_summary.py --suite compiler-pipeline --check`.
Raw model-probe answers and logs remain outside this repository. Keyword
matches cannot prove semantic correctness; review real responses separately.

<!-- BEGIN GENERATED EVAL SUMMARY -->
| Case | Output depth | Baseline | Forward |
| --- | --- | ---: | ---: |
| `pipeline-complete` | implementation specification | -190 FAIL | 210 PASS |
| `pipeline-fixture-unavailable` | implementation specification | -80 FAIL | 150 PASS |
| `pipeline-digest-mismatch` | implementation specification | -200 FAIL | 160 PASS |
| `pipeline-gates-missing` | implementation specification | -180 FAIL | 160 PASS |
| `pipeline-feasibility-scope` | implementation specification | -190 FAIL | 170 PASS |
| `pipeline-absent` | implementation specification | -100 FAIL | 150 PASS |

> These keyword fixtures test repository behavior contracts, not clinical validity or real-world effectiveness.
<!-- END GENERATED EVAL SUMMARY -->
