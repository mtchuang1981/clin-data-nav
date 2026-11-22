# ClinNav 優化待辦

本清單追蹤已核准的優化事項與後續缺口，不代表歷史工作已全部完成。列入待辦不等於已實作，也不包含 Git 提交、推送或發布授權。

2026-11-22 查核的最新公開版本為 [v0.11.2](https://github.com/mtchuang1981/clin-data-nav/releases/tag/v0.11.2)。發布標籤指向 `4a0c89f`。發布驗證報告與雙語文件由 [PR #26](https://github.com/mtchuang1981/clin-data-nav/pull/26) 合併至 `main` 的 `658e3b6`。該合併提交的 Windows、Ubuntu、套件比對及 CodeQL 均通過。[跨平台驗證](https://github.com/mtchuang1981/clin-data-nav/actions/runs/45010551880) · [CodeQL](https://github.com/mtchuang1981/clin-data-nav/actions/runs/45010551929)

2026-11-22 核准 v0.11.2 公開版優化結案。正式發布、產物雜湊驗證、雙語文件更新與本次 Codex 對話讀取核對均已完成。[PR #29](https://github.com/mtchuang1981/clin-data-nav/pull/29) 將對話讀取紀錄合併至 `main` 的 `87935d3`。該合併提交的 Windows、Ubuntu、跨平台套件比對及 CodeQL 均通過。[結案摘要](verification/2026-11-22-v0.11.2-publication.md#public-optimization-closeout) · [跨平台驗證](https://github.com/mtchuang1981/clin-data-nav/actions/runs/45035242390) · [CodeQL](https://github.com/mtchuang1981/clin-data-nav/actions/runs/45035242153)

歷史合併查核（2026-11-17）：當時的公開版本為 v0.11.1，`main` 提交 `69a206e` 的 Windows、Ubuntu、套件比對及 CodeQL 均通過。[PR #17](https://github.com/mtchuang1981/clin-data-nav/pull/17) 完成諮詢流程與安裝權限修正，[PR #18](https://github.com/mtchuang1981/clin-data-nav/pull/18) 完成發布紀錄與雙語安裝文件更新，[PR #19](https://github.com/mtchuang1981/clin-data-nav/pull/19) 完成目標 Windows 清理測試的身分判定修正。三者均已合併。

v0.11.1 發布驗證（Python 3.11.9）：完整測試 1,973 passed、13 skipped；Skill 驗證、公開邊界、可重現封裝與公開下載產物核對均通過。已安裝副本的 26 個檔案與正式 manifest 完全一致；這不代表 host 已重新載入。略過項目仍受平台或權限限制，不能列為通過。詳見[發布與下載驗證紀錄](verification/2026-11-16-v0.11.1-publication.md)。

歷史待辦同步驗證（2026-11-16）：完整測試為 1,972 passed、1 failed、13 skipped，於 `test_windows_summary_close_after_effect_is_never_retried[stage]` 再次出現交易暫存名稱的清理斷言失敗。事後檢視時，該異常名稱已不在目錄；未取得其直接檔案身分或大小。此失敗不能由後續測試通過覆蓋，也不能推定建立者或根因。詳見[當次重現與證據界線](verification/2026-11-16-backlog-sync.md)。

PR #19 修正驗證（2026-11-17，Python 3.11.9）：本機完整測試 1,996 passed、13 skipped；新增合成回歸確認外部同型物件不會誤判，真正 backup 殘留、改名洩漏及 stage 硬連結別名仍會失敗。見[設計與驗證界線](verification/2026-11-17-summary-cleanup-identity.md)。合併提交的 [CI](https://github.com/mtchuang1981/clin-data-nav/actions/runs/43985353281) 為 Windows 2,006 passed、3 skipped，Ubuntu 1,974 passed、35 skipped，套件比對通過；[CodeQL](https://github.com/mtchuang1981/clin-data-nav/actions/runs/43985352292) 亦成功。不同環境的略過項目不能當作通過，也不將跨平台數量相加為獨立案例數。

2026-11-19 同行程回滾補強：新增明確的原輸出有／無狀態判定，將三個標準回滾案例的最後 glob 轉為檔案身分檢查。本機完整測試為 2,039 passed、14 skipped，必要腳本檢查通過；這是[本機實作驗證](verification/2026-11-19-rollback-cleanup-identity.md)，不冒充尚未執行的遠端 CI 或已合併狀態。子行程身分蒐集與 POSIX 特殊契約保留後續處理。

歷史進度（2026-11-06）：公開核心補強、私有端驗收交接清單及雙語 README 導覽分別由 [PR #13](https://github.com/mtchuang1981/clin-data-nav/pull/13)、[PR #14](https://github.com/mtchuang1981/clin-data-nav/pull/14)、[PR #15](https://github.com/mtchuang1981/clin-data-nav/pull/15) 合併；setup-python 更新與測試雜湊同步由 [PR #12](https://github.com/mtchuang1981/clin-data-nav/pull/12) 合併。當時查核的 `main` 為 `d9f2e90`，最新公開版本為 v0.11.0；這些歷史狀態不代表目前版本。

歷史整合紀錄：七個文件與測試檔曾提交為 `2ecc21c` 並合併回本機 `main`，其後已透過 PR #13 推送及合併遠端。當時的獨立只讀審查未發現實質問題，並另驗證六個重點案例與一個父行程 UTF-8 案例。下列驗證紀錄保留各次執行當時狀態；「未提交／未推送」不代表今日狀態。

歷史提交前驗證（Python 3.11.9）：完整套件 1,949 passed、13 skipped，198.86 秒；Skill 驗證、公開邊界與可重現封裝檢查均退出 0，索引範圍與 diff 空白檢查也通過。跳過項目仍為前述平台與權限限制，不能視為通過。

歷史本機合併後驗證（Python 3.11.9）：完整套件 1,949 passed、13 skipped，192.25 秒；Skill 驗證、公開邊界與可重現封裝檢查均退出 0。該次僅記錄上述合併狀態與結果，未改動實作或測試。

## 目前待辦

| 優先度 | 項目 | 狀態與驗收條件 |
| --- | --- | --- |
| 另行授權 | 私有機構端驗收 | 2026-11-05 已整理[公開驗收交接清單](private-adapter-acceptance-checklist.zh-TW.md)。OMOP 1.2 私有實作／快照綁定及編譯器／工具映射仍待機構端授權與驗收；文件完成不代表私有端已通過。 |
| 另行決定 | 真人易用性與成效評估 | 公開評估框架已備妥，尚無本專案真人或臨床成效證據；啟動前須完成另行授權的治理流程。 |

## 已完成的公開補強

清理測試的證據限於所列的合成案例。歷史自然失敗的完整因果、跨目錄洩漏、長期 inode 重用及掃描後變動仍待證實。[歷史失敗紀錄](verification/2026-11-16-backlog-sync.md)與本機原始診斷均保留。

| 項目 | 完成依據 |
| --- | --- |
| v0.11.2 正式發布 | [PR #25](https://github.com/mtchuang1981/clin-data-nav/pull/25) 已合併，附註標籤 `v0.11.2` 指向 `4a0c89f`。[Release workflow](https://github.com/mtchuang1981/clin-data-nav/actions/runs/45007469684) 全數通過，已建立[公開 Release](https://github.com/mtchuang1981/clin-data-nav/releases/tag/v0.11.2)。 |
| v0.11.2 公開產物驗證 | 已從 GitHub 下載 ZIP 與 manifest，重新計算的 SHA-256 均與 GitHub 及本機候選檔一致。ZIP 雜湊與 manifest 的 `archive_sha256` 一致，發布產物驗證器通過。[發布與下載驗證報告](verification/2026-11-22-v0.11.2-publication.md) |
| v0.11.2 雙語 README 與安裝指南 | [PR #26](https://github.com/mtchuang1981/clin-data-nav/pull/26) 已合併。雙語 README 和指南中的 PowerShell、POSIX 指令均已更新至已驗證的 v0.11.2，並列出已核對的 ZIP 與 manifest SHA-256。[英文指南](installation.md) · [繁體中文指南](installation.zh-TW.md) |
| v0.11.2 隔離試裝 | 在 Windows 暫存目錄用正式 ZIP 試裝，26 個檔案逐位元組符合 manifest。缺少、多出及相異檔案各為零。[隔離試裝紀錄](verification/2026-11-22-v0.11.2-publication.md#isolated-installation-check) |
| 本次 Codex 對話讀取核對 | 本次對話從工作階段列出的 ClinNav 安裝路徑實際讀取 `SKILL.md`。該目錄的 26 個檔案均逐位元組符合 v0.11.2 正式 manifest。v0.11.1 與 v0.11.2 的 ZIP SHA-256 相同，原始安裝版號仍無法由檔案判定。此次查核全程唯讀。[Codex 對話讀取紀錄](verification/2026-11-22-v0.11.2-publication.md#codex-session-read-verification) |
| 子行程與 POSIX 清理測試的身分判定 | [PR #22](https://github.com/mtchuang1981/clin-data-nav/pull/22) 已合併三個子行程案例，[PR #23](https://github.com/mtchuang1981/clin-data-nav/pull/23) 已合併最後兩個 POSIX 案例。合併提交 `be635e4` 的 Windows 測試 2,060 項通過、3 項略過，Ubuntu 2,028 項通過、35 項略過，套件比對與 CodeQL 通過。[測試紀錄](superpowers/plans/2026-11-22-posix-cleanup-identity.md) |
| 三個標準同行程回滾測試的身分判定 | [PR #21](https://github.com/mtchuang1981/clin-data-nav/pull/21) 已合併。測試驗證回復原 backup 身分或原先無輸出的狀態，並捕捉原名或改名的 stage 殘留、硬連結別名，以及內容相同但身分不同的輸出。[本機驗證紀錄](verification/2026-11-19-rollback-cleanup-identity.md) |
| 目標 Windows 清理測試的身分判定 | PR #19 已合併至 `69a206e`。以交易 stage／backup 的檔案身分取代最後的廣泛名稱斷言，保留既有 HANDLE、sentinel、輸入與輸出檢查；加入外部物件、原名／改名 backup 殘留與 stage 別名等合成回歸。產品程式、版本與發布產物未變；本機、雙平台 CI、套件比對及 CodeQL 通過，詳見本頁上方查核與[本機驗證](verification/2026-11-17-summary-cleanup-identity.md)。完成的是明確示範的測試判定缺陷，不代表先前每次自然失敗均已取得完整歸因。 |
| 承辦諮詢流程與概念審查補強 | PR #17 已合併並納入 v0.11.1。初步諮詢採精簡決策單，正式規格保留完整契約；補上語意審查、搜尋完整性、工具參數與責任分工。七項合成情境與小樣本前後測不代表一般化成效，見[範圍與驗證紀錄](verification/2026-11-16-feasibility-consultation.md)。 |
| Windows 安裝權限繼承修正 | PR #17 已合併。解壓前準備目標目錄的 DACL；權限失敗時不替換舊安裝。原生安裝器測試 72 項通過，詳見[根因與發布前驗證](verification/2026-11-16-v0.11.1-preflight.md)。本項不包含間歇性清理異常。 |
| v0.11.1 發布、文件與安裝核對 | PR #17、#18 均已合併；annotated tag、正式發布、雙平台驗證與公開下載雜湊核對已完成。已安裝副本 26 個檔案一致，host 載入狀態未驗證；詳見[發布證據](verification/2026-11-16-v0.11.1-publication.md)。 |
| setup-python 更新與雜湊測試同步 | PR #12 已合併至 `d9f2e90`；PR 與 main 的 Windows、Ubuntu、套件比對及 CodeQL 均成功。保留完整 SHA 與版本註解檢查；不代表 Windows 間歇性清理問題已修復。見[根因與驗證紀錄](verification/2026-11-06-setup-python-pr12.md)。 |
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

歷史設計與驗證紀錄保留當時狀態。2026-10-24 發布計畫末尾仍有未勾選項目，當次發布與文件 PR 合併已可由提交確認。2026-11-06 盤點確認了當時的 main CI 與 Release 標籤，未重新下載歷史發布附件。v0.11.1 的下載核對見上方 2026-11-16 發布紀錄。

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
