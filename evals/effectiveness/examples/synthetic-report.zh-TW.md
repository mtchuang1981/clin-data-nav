# 效果評估先導研究彙總報告—合成範例

## 摘要

本探索性產品評估彙整通過安全門檻的任務表現；不能證明臨床效度、因果效度或病人結果效度。
目標是在相同模型與操作介面下，比較有無使用固定版本 Skill 的差異。
這是示例性合成範例，不是實際觀察到的先導研究證據。

## 方法

- 研究規格 commit：`4776d35c4138c0966c57888528936e7aae6388a4`。
- 研究期間：2026-09-01T09:00:00+08:00 至 2026-09-02T17:00:00+08:00。
- 模型／Skill 環境：Codex desktop；模型 fixed-model-snapshot；推理強度 medium；服務層級 priority；Skill 0.3.0（commit `1b4eeb2ca2272cfd05ecdd50708c4fea714db0d3`）；Windows 上的 Python 3.11.9。
- 分派版本：synthetic-pilot-v1-assignments。
- 任務承諾：已驗證 （`cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc`）。
- 參與者叢集 bootstrap：seed 20260809、20000 次重抽；連續型配對次要結果的 95% 區間採相同方法。
- 品質準則屬於次要結果，絕不決定主要任務成功；適用分母為零時標示為無法估計。

## 參與者流程

分派 16 人；完成 16 人；初學者 8 人、專業者 8 人。中途退出：0；逾時：0；技術失敗：0。主要分析完整配對：16。解讀狀態：`eligible-for-exploratory-interpretation`。

## 主要結果

對照組：16/32 （50.0%）；介入組：24/32 （75.0%）。配對風險差為 25.0%（介入減對照），示例性 95% 區間為 [5.0%, 45.0%]，完整配對 16 人。
預先指定的最小實務差異為絕對 20.0 個百分點；不是相對改善，也不會只用先導研究點估計進行檢定力規劃。

## 分層結果

- 初學者：8 人；對照 7/16（43.8%），介入 12/16（75.0%），配對差異 31.25 個百分點。
- 專業者：8 人；對照 9/16（56.2%），介入 12/16（75.0%），配對差異 18.75 個百分點。
兩個分層皆屬探索性，不能視為具確認性檢定力的比較。

## 安全性

- 對照組：0/32（0.0%）；精確 95% 區間 [0.0%, 10.9%]。
- 介入組：0/32（0.0%）；精確 95% 區間 [0.0%, 10.9%]。
重大安全事件獨立呈現，不得由品質或速度抵銷。

## 次要結果

- 時間（秒）：16 個完整配對；平均差異 -110.0；中位數差異 -120.0；95% 區間 [-180.0, -40.0]。
- 品質（分）：16 個完整配對；平均差異 +10.0；中位數差異 +10.0；95% 區間 [+4.0, +16.0]。
- NASA-TLX（分）：16 個完整配對；平均差異 -8.0；中位數差異 -8.0；95% 區間 [-12.0, -4.0]。
- 信心變化：16 個完整配對；平均差異 +1.0；中位數差異 +1.0；95% 區間 [+0.5, +1.5]。
- 理解程度變化：16 個完整配對；平均差異 +1.0；中位數差異 +1.0；95% 區間 [+0.5, +1.5]。
- 介入條件 SUS：16 人；平均 78.0；中位數 78.0。
- 逾時率：0/64（0.0%）。
- 技術失敗率：0/64（0.0%）。

### 評分準則結果

| 準則 | 對照達成／適用 | 對照率 | 介入達成／適用 | 介入率 |
|---|---:|---:|---:|---:|
| correct-output-depth | 28/32 | 87.5% | 30/32 | 93.8% |
| answers-requested-decision | 24/32 | 75.0% | 28/32 | 87.5% |
| states-confirmed-assumed-limited | 25/32 | 78.1% | 29/32 | 90.6% |
| authority-appropriate-sources | 18/24 | 75.0% | 22/24 | 91.7% |
| actionable-next-step | 24/32 | 75.0% | 28/32 | 87.5% |
| beginner-readable | 6/8 | 75.0% | 7/8 | 87.5% |
| pico-and-time-zero | 5/8 | 62.5% | 7/8 | 87.5% |
| tte-readiness | 3/4 | 75.0% | 4/4 | 100.0% |
| logical-data-contract | 6/8 | 75.0% | 8/8 | 100.0% |
| execution-status | 6/8 | 75.0% | 8/8 | 100.0% |
| citation-verifiable | 5/8 | 62.5% | 7/8 | 87.5% |
| validation-gaps | 20/32 | 62.5% | 27/32 | 84.4% |

## 評分者一致性

原始裁定前評分涵蓋 64 份答案。二元原始一致率為 87.5%（Cohen kappa：0.75）；序位原始一致率為 87.5%（線性加權 kappa：0.80）。重大事件歧見：0；裁定：8；解盲前狀態：`eligible-for-locked-unlock`。

## 缺失資料與敏感度分析

完整案例主要分析使用 16 個參與者配對。保守缺失值分析使用 16 個配對，估計值為 25.0%，95% 區間 [5.0%, 45.0%]。

## 樣本數情境

| 情境 | 對照率 | 配對不一致率 | 流失率 | alpha | 目標檢定力 | 方法 | 所需完整配對 | 所需招募 | 狀態 |
|---|---:|---:|---:|---:|---:|---|---:|---:|---|
| lower-control-rate | 30.0% | 35.0% | 15.0% | 0.05 | 80.0% | paired-binary-or-participant-task-clustered-design | deferred-until-post-pilot | deferred-until-post-pilot | deferred-until-post-pilot |
| mid-control-rate | 50.0% | 50.0% | 15.0% | 0.05 | 80.0% | paired-binary-or-participant-task-clustered-design | deferred-until-post-pilot | deferred-until-post-pilot | deferred-until-post-pilot |
| higher-control-rate | 70.0% | 35.0% | 15.0% | 0.05 | 80.0% | paired-binary-or-participant-task-clustered-design | deferred-until-post-pilot | deferred-until-post-pilot | deferred-until-post-pilot |

所有情境均使用預先指定的 20.0 個百分點，並納入保守的配對不一致、異質性、失敗與流失假設；在先導研究後的設計決策前，不虛構確認性樣本數。

## 規格偏離

審查狀態：`reviewed-none`；未記錄規格偏離。

## 限制

審查狀態：`reviewed-with-findings`。
- 小型探索性樣本：1。
- 合成任務推廣性：1。
- 受控環境推廣性：1。
- 不得推論臨床效度：1。
- 負向或中性結果必須使用相同結構發布，不得隱匿。
