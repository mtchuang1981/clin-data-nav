# 待辦同步與 Windows 清理異常再現

歷史驗證日期：2026-11-16（Asia/Taipei）。當次查核基準為 `56146e9bb9f14fdb348e6afcebc3147eee38e591`。
本輪獲准更新進度文件，將 v0.11.1、PR #17／#18 與發布紀錄列為完成，
保留未解決缺口；沒有修改安裝器、benchmark、測試或技能執行行為。

## 本次驗證結果

Python 3.11.9／pytest 9.1.1，使用 repo 外的新合成暫存目錄：
完整測試 **1,972 passed、1 failed、13 skipped**，178.88 秒，退出 1。
失敗 node ID：
`tests/test_simulation_benchmark.py::test_windows_summary_close_after_effect_is_never_retried[stage]`。

斷言的 glob 列出含大寫 BACKUP 與 `.TMP.tmp` 尾碼的名稱，
因此「沒有交易暫存檔」斷言失敗。此命名與斷言型態曾見於
[11/06 原生診斷](2026-11-06-windows-native-cleanup.md)，不代表兩次根因已確認相同。
略過項目涉及平台檔名、symlink／reparse 權限與 POSIX dir-fd 契約，不能算通過。

Skill 驗證、公開邊界、可重現封裝與 diff 空白檢查均退出 0。
文件本機連結另行核對；未以子集或重跑成功取代本次完整測試的失敗。

## 事後現場與證據限制

失敗後只讀取該合成目錄的名稱、大小、inode、時間及屬性，不讀取檔案內容。
檢視時斷言列出的異常名稱已不在目錄，因此沒有取得該物件的直接身分、
大小、建立者或消失時間，也不能將前輪的零位元組或檔案 ID 當作本輪觀察。
其餘目錄項目的事後中繼資料已保留；沒有刪除、改名或重跑該測試。

本機中繼資料留在 Git 忽略的 `dist/backlog-sync-20261116/failure-metadata.json`，
SHA-256 為 `0b390aa75f9037ce1ead1d78ff1a4a5a5888ff2b6962d9437891c92740c3be39`。
首次失敗輸出保留於本次工具紀錄；本機檔案不宣稱包含完整 stdout 或原生事件軌跡。

| 公開來源 | SHA-256 |
| --- | --- |
| scripts/evaluate_simulation_benchmark.py | 8d39edd0419fd7f63ac074af875d2d869e518becf001fda0cde95dc673f8a910 |
| tests/test_simulation_benchmark.py | 7593c0f1372a3198681997be5bf89781391e01929bc4456d5480ed5b8fccfc86 |

這兩個來源雜湊與 11/06 診斷紀錄一致。此事實不足以定位根因；
未據此新增延遲、放寬斷言、刪除萬用字元命中的物件，或重試可能已關閉的 HANDLE。
Windows 間歇性清理缺口仍開放，與已修復的安裝 DACL 繼承問題分開追蹤。
在上述 11/16 驗證當時，診斷驅動或程序歸因追蹤仍待另行核准，尚未執行；後續進度見末節。

v0.11.1 的先前發布通過結果維持歷史紀錄，另見[發布驗證](2026-11-16-v0.11.1-publication.md)；
本次失敗同樣保留，不將兩次結果合併成全數通過。未重產、推送或改動發布產物。

## 當時的下一步診斷準備（2026-11-16 尚未執行追蹤）

重新檢視既有 `dist/cleanup-native-probe-20261106/probe.py`：它包裝交易方法、
本模組的 NtSetInformationFile／CloseHandle 與斷言 glob；不記錄系統其他程序的
檔案建立操作。直接開啟異常路徑取得身分的能力，也不能回溯建立者 PID。
因此目前缺的是跨程序事件證據，不能把沒有觀察到建立操作解讀為沒有建立操作。
本輪僅查詢 PATH 中的 Procmon.exe／Procmon64.exe／Procmon64a.exe，未找到命令；
這不等於電腦未安裝，也未遍搜磁碟。沒有啟動、下載或載入診斷工具。

建議在另行明確核准後，依下列範圍執行一次診斷工作階段：

1. 從 Microsoft 官方來源取得或確認既有 Process Monitor，記錄版本、SHA-256
   與有效的 Microsoft Authenticode 簽章。確認沒有其他使用中的追蹤工作階段；
   不停止使用者既有工作階段，不開啟開機追蹤，不變更防毒或安全設定。
2. 只使用新建、repo 外的合成暫存根目錄。開始擷取前確認篩選只納入該根目錄
   本身及其子項目的檔案系統事件，停用 Registry、Network、Process/Thread
   與 Profiling 事件。不要以 Python PID 篩選，以免漏掉其他程序對該目錄的操作。
   確認 Drop Filtered Events 設定與實際儲存結果，不能只憑畫面篩選宣稱未保留其他事件；
   若無法事先確認此範圍，便不開始測試或擷取。
3. 使用已確認的 Python 3.11.9，執行既有 backup-cleanup 案例及 backup／stage／parent
   三個 close-after-effect 案例，pytest 加 `-x`。最多五批、20 個案例；
   從開始擷取起最多 60 秒，或首次測試失敗即停止擷取及後續批次。
   開始前備妥獨立計時停止機制；到時仍在執行的案例可結束，但不得延長擷取，
   並標示該案例事件不完整。不強制關閉測試 HANDLE 或刪除現場。
4. 保留操作時間、程序 PID／映像身分、路徑、操作種類、結果與詳細參數，
   對照原生交易事件、斷言及直接取得的檔案身分。CreateFile 操作名稱本身
   不足以證明新建檔案，須檢視建立方式、結果及前後事件；PID 也不單獨視為穩定身分。
5. PML、完整輸出及程序中繼資料只存於本機 Git 忽略的診斷目錄，不上傳或提交；
   即使路徑已篩選，程序中繼資料仍可能包含映像路徑或命令列。
   公開文件只保留經邊界檢查的合成彙總、來源雜湊及證據限制。
6. 無重現、事件遺失、篩選不符或期限截斷，都只能記錄為證據不足。
   不自動延長追蹤、不重試到通過；取得可歸因證據後才決定是否新增失敗回歸測試與最小修正。

此方案延續 [11/06 診斷邊界](2026-11-06-windows-native-cleanup.md)所要求的
「須先另行核准載入診斷驅動」及最多 60 秒限制；本段不是執行授權。
[Microsoft 官方說明](https://learn.microsoft.com/en-us/sysinternals/downloads/procmon)
確認此工具可擷取檔案系統與程序資訊，並指出其一般篩選為非破壞式；
[Microsoft 官方教學](https://learn.microsoft.com/en-us/shows/defrag-tools/3-process-monitor)
另列出 Drop Filtered Events 選項。實際版本的設定與保留範圍仍須執行前確認，
不將文件描述當成已驗證的本機擷取結果。

## 後續公開狀態（2026-11-17）

本機診斷已依另行核准的範圍完成，原始紀錄依要求僅保留本機，未納入 Git。
本頁保留 11/16 失敗與當時規劃，不將後續結果回寫為該次測試通過，也不視為再次追蹤的授權。

後續公開合成回歸證明目標測試的廣泛 glob 會把不同身分的外部物件判成交易殘留，
並漏掉改成一般檔名的真正 backup。[PR #19](https://github.com/mtchuang1981/clin-data-nav/pull/19)
已以身分判定修正該測試，合併提交為 `69a206eb2e316d3738895b6213fe32c1ff2ffcae`。
產品清理程式未改動；原始碼雜湊表僅記錄 11/16 當時版本，不能當作目前測試檔的雜湊。

本機修正後完整測試為 1,996 passed、13 skipped；合併提交的
[CI](https://github.com/mtchuang1981/clin-data-nav/actions/runs/43985353281)
為 Windows 2,006 passed、3 skipped，Ubuntu 1,974 passed、35 skipped，套件比對成功；
[CodeQL](https://github.com/mtchuang1981/clin-data-nav/actions/runs/43985352292) 亦成功。
略過仍受平台與權限限制，不能視為通過。完整範圍見[修正驗證](2026-11-17-summary-cleanup-identity.md)。
先前自然失敗的完整因果仍未證實；其他清理斷言與超出立即父目錄的物件生命週期不在本次修正範圍。
