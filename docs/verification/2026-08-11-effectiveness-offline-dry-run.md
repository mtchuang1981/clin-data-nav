# Effectiveness Offline Dry-Run Verification

## English

### Scope and evidence boundary

- Verification date: `2026-08-11` (`Asia/Taipei`, UTC+08:00).
- Observation captured: `2026-08-11T11:30:58.4197801+08:00`.
- Branch: `codex/effectiveness-offline-dry-run`.
- Baseline HEAD: `55cfa26b185456ec4c1bd054467c74be51f69877`.
- Interpreter: `Python 3.13.13`.
- External synthetic workspace:
  `C:\tmp\clin-data-nav-effectiveness-offline-2026-08-11-55cfa26`.

This was a repository-native pipeline rehearsal using only public synthetic
contracts and test fixtures. It made no external model call, recruited no
person, collected no human response, created no real human-task commitment,
and accessed no private or institutional system. The external workspace was
used only because the assignment generator rejects repository-internal study
outputs by design.

### Baseline and public contract

| Command | Exit | Observed result |
|---|---:|---|
| `python -m pytest -q` | 0 | `581 passed in 29.38s` |
| `python -m pytest -p no:cacheprovider tests/test_effectiveness_contract.py -q` | 0 | `4 passed in 0.04s` |
| `python -m pytest -p no:cacheprovider tests/test_study_assignments.py -q` | 0 | `19 passed in 0.26s` |

The first contract run from the host-authorized external-directory context
also passed all four tests but emitted a pytest cache warning because that
Windows identity could not write the worktree cache owned by the sandbox
identity. Re-running with pytest's cache provider disabled produced the clean
result above. This was an environment ownership warning, not a test or product
failure.

### External synthetic assignment

The following command exited `0`:

```text
python scripts/generate_study_assignments.py --study-id synthetic-offline-v1 --seed 20260811 --output C:\tmp\clin-data-nav-effectiveness-offline-2026-08-11-55cfa26\assignments.json
```

Independent PowerShell assertions, separate from the generator's validator,
observed:

| Property | Observed value |
|---|---:|
| Schema version | `1` |
| Rows | `64` |
| Synthetic participant codes | `16` |
| Unique opaque answer IDs | `64` |
| Rows per participant | `4` |
| Control/intervention rows per participant | `2` / `2` |
| Output depths per participant | `4` |
| Stratum × pair × variant × condition cells | `64`, each with count `1` |
| Strata failing first-order balance | `0` |
| Assignment file size | `18,356` bytes |
| Assignment file SHA-256 | `9587666a20dd5ed29c77ace77f921941902b47867aec914c7e50dbbdb412a8a2` |

The assignment file is a temporary synthetic artifact. It is not tracked and
must not be treated as a real study assignment.

### Blinded-rating, calibration, unlock, and report rehearsal

| Command | Exit | Observed result |
|---|---:|---|
| `python -m pytest -p no:cacheprovider tests/test_effectiveness_analysis.py tests/test_effectiveness_reports.py tests/test_human_task_commitment.py -q` | 0 | `179 passed in 11.57s` |
| Focused agreement, recalibration, unlock, fixed-layout, and aggregate-summary nodes | 0 | `9 passed in 1.05s` |
| `python scripts/render_effectiveness_report.py --summary evals/effectiveness/examples/synthetic-summary.json --english evals/effectiveness/examples/synthetic-report.md --traditional-chinese evals/effectiveness/examples/synthetic-report.zh-TW.md --check` | 0 | Both checked-in synthetic reports reproduced without a diff |

The exact focused command was:

```text
python -m pytest -p no:cacheprovider -q tests/test_effectiveness_analysis.py::test_agreement_status_stops_before_unlock_for_each_threshold tests/test_effectiveness_analysis.py::test_agreement_status_is_eligible_only_when_all_applicable_thresholds_pass tests/test_effectiveness_analysis.py::test_agreement_check_writes_only_blinded_aggregate_and_accepts_no_condition_key tests/test_effectiveness_analysis.py::test_agreement_check_exits_three_after_writing_recalibration_status tests/test_effectiveness_analysis.py::test_analyze_refuses_unlock_when_blinded_agreement_is_not_eligible tests/test_effectiveness_analysis.py::test_full_pilot_unlock_has_fixed_64_row_ratings_locked_layout tests/test_effectiveness_analysis.py::test_summary_has_fixed_aggregate_contract_and_paired_denominators
```

The focused nodes verified that:

- every applicable agreement threshold must pass before the status becomes
  `eligible-for-locked-unlock`;
- a failed agreement threshold produces
  `recalibrate-and-rescore-before-unlock` and CLI exit code `3`;
- the agreement-only command accepts no condition key and writes only blinded
  aggregate agreement;
- analysis refuses condition unlock while agreement is ineligible;
- the fixed synthetic layout contains 64 locked ratings; and
- aggregate output excludes row identifiers and human-answer content.

The checked-in synthetic example contains illustrative agreement and outcome
values solely to exercise report rendering. Its 25-percentage-point paired
difference, interval, kappa values, and eligibility status are not observed
pilot results and are not evidence that the Skill is effective. Confirmatory
sample-size fields remain `null` with status
`deferred-until-post-pilot`; no power analysis was performed.

### Readiness decision and next gate

The public evaluation pipeline is mechanically ready for a governance review
of a separately authorized human pilot. This dry run does not establish task
quality, rater readiness with real raters, clinical validity, causal validity,
or real-use effectiveness. Before any human activity, the project still needs
an explicit governance and ethics-path decision, approved external storage,
consent and recruitment procedures, a frozen model/Skill environment, rater
orientation, and an externally held confidential task-pack commitment.

## 繁體中文

### 範圍與證據邊界

本次僅以公開合成契約與測試資料演練評估管線；沒有呼叫外部模型、
招募人員、收集真人回答、建立真正的人類任務承諾，亦未存取私人或機構
內部系統。分派檔放在 repository 外，是因為產生器本來就會拒絕把研究
輸出寫入 repository。

### 演練結果

- 完整 baseline：`581 passed`。
- 公開效果契約：`4 passed`。
- 分派契約與竄改防護：`19 passed`。
- 盲化分析、報告與任務承諾 focused suite：`179 passed`。
- 一致性、重新校準、解盲阻擋與固定配置精準檢查：`9 passed`。
- 雙語合成報告可決定性重現，沒有差異。
- 外部合成分派為 16 個代碼、64 筆任務，每人四題且 control／
  intervention 各兩題；所有分層、題組、版本與條件組合均平衡。

合成報告中的 25 個百分點差異、信賴區間及評分者一致性數字只是管線
測試值，不是實際先導研究效應量，也不能證明 Skill 有效。樣本數欄位仍
維持 `deferred-until-post-pilot`；本次沒有執行 power analysis。

### 下一道門檻

目前僅能判定公開評估管線已具備送交真人先導研究治理審查的機械性條件。
任何真人活動開始前，仍須另行完成治理／倫理路徑、外部資料儲存、同意與
招募程序、模型與 Skill 環境凍結、評分者訓練，以及外部機密任務包承諾。
