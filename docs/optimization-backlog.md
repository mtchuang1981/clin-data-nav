# ClinNav 優化待辦

本清單追蹤已核准的優化事項與後續缺口，不代表歷史工作已全部完成。列入待辦不等於已實作，也不包含 Git 提交、推送或發布授權。

最後盤點：2026-11-06。已即時查核 GitHub：公開核心補強、私有端驗收交接清單及雙語 README 導覽分別由 [PR #13](https://github.com/mtchuang1981/clin-data-nav/pull/13)、[PR #14](https://github.com/mtchuang1981/clin-data-nav/pull/14)、[PR #15](https://github.com/mtchuang1981/clin-data-nav/pull/15) 合併。盤點時本機與遠端 `main` 同為 `e4f5edf`，該提交的 validate 與 CodeQL 工作流程均成功；最新公開版本仍為 v0.11.0。

歷史整合紀錄：七個文件與測試檔曾提交為 `2ecc21c` 並合併回本機 `main`，其後已透過 PR #13 推送及合併遠端。當時的獨立只讀審查未發現實質問題，並另驗證六個重點案例與一個父行程 UTF-8 案例。下列驗證紀錄保留各次執行當時狀態；「未提交／未推送」不代表今日狀態。

提交前驗證（Python 3.11.9）：完整套件 1,949 passed、13 skipped，198.86 秒；Skill 驗證、公開邊界與可重現封裝檢查均退出 0，索引範圍與 diff 空白檢查也通過。跳過項目仍為前述平台與權限限制，不能視為通過。

本機合併後驗證（Python 3.11.9）：完整套件 1,949 passed、13 skipped，192.25 秒；Skill 驗證、公開邊界與可重現封裝檢查均退出 0。本次只將上述合併狀態與結果另行記錄，不改動實作或測試。

## 目前待辦

| 優先度 | 項目 | 狀態與驗收條件 |
| --- | --- | --- |
| 1 | setup-python 更新 PR #12 | 已定位兩平台 CI 失敗至測試仍要求舊版完整雜湊；修正同步至官方 v7.1.0。須在確切 PR head 通過 Windows、Ubuntu、套件比對與 CodeQL 後才可合併；實際狀態見 [PR #12](https://github.com/mtchuang1981/clin-data-nav/pull/12)。詳見[根因與驗證紀錄](verification/2026-11-06-setup-python-pr12.md)。 |
| 2 | Windows 間歇性清理異常根因分析 | 2026-11-04 五輪診斷未重現；2026-11-06 完整測試在 backup cleanup 案例再出現同類異常檔名。已保留合成現場，回查時異常檔案已不存在；一次追蹤執行通過，根因仍未明。不得只因重跑通過就標記已修復。見[原診斷流程](verification/2026-11-04-windows-cleanup-diagnostics.md)及[本次觀察](verification/2026-11-06-setup-python-pr12.md)。 |
| 另行授權 | 私有機構端驗收 | 2026-11-05 已整理[公開驗收交接清單](private-adapter-acceptance-checklist.zh-TW.md)。OMOP 1.2 私有實作／快照綁定及編譯器／工具映射仍待機構端授權與驗收；文件完成不代表私有端已通過。 |
| 另行決定 | 真人易用性與成效評估 | 公開評估框架已備妥，尚無本專案真人或臨床成效證據；啟動前須完成另行授權的治理流程。 |

## 已完成的公開補強

| 項目 | 完成依據 |
| --- | --- |
| 解壓安裝後的 OMOP 1.2 CLI 比對 | PR #13 已合併。五個合成案例比對 repo wrapper 與解壓套件的退出碼及完整 stdout/stderr；Python 3.11.9 相關測試 75 項通過。 |
| 可攜 JSON Schema 的整數型別限制說明 | PR #13 已合併中英文指南。Schema 可接受數學整數 `1.0`，不取代 Python 嚴格型別與完整契約驗證。 |
| Eval 測試的父、子行程編碼不一致 | PR #13 已合併測試兩端 UTF-8 設定。一般與父行程 UTF-8 模式的相關測試各 119 項通過；未改 CLI 或評分行為。見[編碼驗證紀錄](verification/2026-11-04-evaluator-subprocess-encoding.md)。 |
| 私有端驗收交接文件與 README 導覽 | PR #14、#15 已合併；只完成公開交接文件，不代表私有驗收已通過。 |

技術缺口依據：[OMOP 1.2 驗證與延後事項](verification/2026-10-12-omop-v12-dqd-expiration.md)、[Windows 異常原始紀錄](verification/2026-10-19-governed-compiler-pipeline.md)、[v0.11.0 已知限制](verification/2026-10-24-ste-project-candidate.md)。真人評估邊界見[成效評估框架](../evals/effectiveness/README.md)。

2026-11-04 調查與補強：既有 `test_offline_entry_points_agree` 只執行 repo wrapper 與 Skill 原始碼入口；新增 `test_unpacked_cli_matches_repository_bytes`，使用現有封裝器建立 ZIP，解壓至暫存安裝目錄，從 checkout 外的工作目錄執行並逐位元組比較輸出。首次執行發現新測試錯將 Windows 的 CRLF 當作 LF，已修正平台換行預期，兩入口的位元組比較仍完整保留，未改執行邏輯。Python 3.13.13 的該 CLI 模組 39 項通過；另從既有計畫找到 Python 3.11.9 環境，確認載入本 checkout 後，CLI、1.2 契約與文件相關測試共 75 項通過。

Windows 清理相關測試 `test_windows_summary_close_after_effect_is_never_retried` 在 Python 3.13.13 下三個案例通過，但舊失敗未重現、原始現場已不存在，根因仍未確定。原始碼的名稱產生器使用小寫 label／十六進位及 `.tmp`；歷史紀錄的異常名稱不符此形式。這不足以判定是外部干擾或清理缺陷；下次失敗須保留現場與身分／時間證據，不能推測後直接擴大刪除範圍或重試關閉 HANDLE。

前輪文件與安裝補強驗證（Python 3.11.9，2026-11-04）：完整 `python -m pytest -q` 為 1,949 passed、13 skipped，239.93 秒，包含上述 Windows 清理與新安裝案例。跳過項目涉及 Windows symlink 權限、大小寫／尾端空白檔名及 POSIX dir-fd 行為，不列為已驗證。`validate_skill.py`、`check_public_boundary.py`、`package_skill.py --check-reproducible` 均退出 0；diff 空白檢查與當時清單八個檔案連結檢查也通過。變更只涉及本機文件與合成測試，未提交、推送、發布或存取私有系統。

後續 Windows 診斷驗證（同日、Python 3.11.9）：五輪有效觀察 15 案例通過；未加診斷包裝器的 benchmark 模組 273 passed、5 skipped；完整套件 1,949 passed、13 skipped，206.74 秒。另三項必要檢查均退出 0。已保留診斷第一次無效設定與有效紀錄，公開文件只記錄彙總與雜湊；結論仍是未重現、未修復。

後續 Eval 編碼修正驗證（同日、Python 3.11.9）：先重現並確認測試的父、子行程編碼不一致，再明訂兩端 UTF-8。相關模組在一般及父行程 UTF-8 模式各 119 項通過；最終一般模式完整套件 1,949 passed、13 skipped，205.39 秒，另三項必要檢查均退出 0。此修正只涉及測試設定，未更動正式 CLI 或 Windows 清理邏輯。

歷史設計與驗證紀錄保留當時狀態，不回寫成今日進度。2026-10-24 發布計畫末尾仍有未勾選項目；發布證據文件與文件 PR 合併已可由提交確認。本次另確認上述 main CI 與最新 Release 標籤，未重新下載歷史發布附件，不新增附件完整性主張。

## 研究設計章節的中英對應契約

狀態：已完成。2026-10-07 核准列入待辦，2026-10-23 完成實作與本機驗證，2026-10-24 納入 v0.11.0 發布。

驗證依據：[標題契約驗證紀錄](verification/2026-10-23-research-heading-contract.md)、[v0.11.0 發布驗證](verification/2026-10-24-v0.11.0-publication.md)。須明確選用 `research-bilingual-v1`；預設仍為 `legacy-v1`。標題對應以[唯一 JSON 契約](../skills/clin-nav/references/research-heading-contract.json)為準。

目標：允許 `research design` 使用明確對應的英文或繁體中文章節標題，避免將標題語言差異誤當成章節缺漏。章節存在不代表內容充分，需求涵蓋、方法合理性與安全性仍須分別驗收。

### 範圍

以下五組對應名稱已納入明確選用的契約；下表供查閱，不另行定義對應規則：

| 英文標題 | 受支援繁體中文標題 |
| --- | --- |
| Primary intent and design route | 研究意圖與設計路徑 |
| Design fields and time anchors | 設計欄位與時間軸 |
| Data suitability and claim boundary | 資料適用性與主張邊界 |
| Bias and validation gaps | 偏差與驗證缺口 |
| Analysis or diagnostics | 分析或診斷 |

實作延續現有 [evaluator](../scripts/evaluate_response.py) 與輸出 references，未另建評分器。契約限定受支援標題集合，避免任意同義詞或內文關鍵字使缺少章節的回答誤通過。

本項只涵蓋上述五個研究設計章節；不自動翻譯共同表頭、不修改其他輸出深度，也不將格式通過視為臨床有效性、資料適用性或可執行性驗證。

### 實作與驗收紀錄

- [x] 先以公開合成 fixtures 新增失敗測試，再修改標題契約；保留英文輸出相容性。
- [x] 確認英文與受支援繁體中文標題可辨識為同一必要章節；缺少章節、只有內文提及或錯誤輸出深度仍不得通過。
- [x] 同步檢閱 SKILL、輸出 references、evaluator、Eval catalog 與 fixtures；對應規格集中維護，避免雙語版本漂移。
- [x] 保留原有必要內容、來源誠實性、未知 schema、不可執行狀態與安全限制，不降低門檻。
- [x] 分開記錄格式／安全規則測試與獨立語意審查的範圍；未宣稱完成案件負責人的內容審查或臨床驗證。
- [x] 以新契約另建驗證紀錄；不追溯改分既有 pilot／benchmark，不重寫封存規則，也不將既有失敗自動轉為通過。
- [x] 實作後執行完整 pytest、validate-skill、public-boundary、reproducible-package 與 diff 檢查；公開 repo 僅保存合成材料或 aggregate-only 紀錄。

### 不包含的工作

本次進度整理不重跑既有私有案例、不讀取或搬入原始諮詢單及回答、不存取 adapter 或患者資料、不修改歷史發布產物，也不指定新版本或發布。
