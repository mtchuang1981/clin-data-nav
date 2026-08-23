# 公開模擬基準測試報告模板

本模板不包含任何基準測試結果。renderer 會從一份通過驗證的彙總摘要取代所有
`<value>`；請勿手動填寫。

## 識別資訊與範圍

| 欄位 | 值 |
|---|---|
| `benchmark_id` | <value> |
| `status` | <value> |
| `direction` | <value> |
| `plan_sha256` | <value> |
| `skill.commit` | <value> |
| `skill.tag` | <value> |
| `skill.archive_sha256` | <value> |
| `model.*` | <value> |
| `execution_attestation.*` | <value> |

## 整體結果

| 欄位 | 值 |
|---|---|
| `overall.*` | <value> |

## 配對變化

| 欄位 | 值 |
|---|---|
| `paired_counts.*` | <value> |

## 輸出深度分層

| 欄位 | 值 |
|---|---|
| `depth.<output_depth>.*` | <value> |

## 個案穩定性

| 欄位 | 值 |
|---|---|
| `case.<case_id>.*` | <value> |

## 禁止規則護欄

| 欄位 | 值 |
|---|---|
| `forbidden_violations.*` | <value> |

## 限制與下一步證據

這些結果僅涉及公開合成提示與確定性契約檢查。
模型中繼資料與執行證明均由外部回報，未經提供者驗證。
確定性規則無法衡量所有語意品質。
沒有具代表性的使用者執行可用性任務。
本報告不能推導出臨床效度、因果效度、病人結果或可部署性的主張。
`positive-signal` 不代表 `human-effective` 或 `evaluation-green`。
