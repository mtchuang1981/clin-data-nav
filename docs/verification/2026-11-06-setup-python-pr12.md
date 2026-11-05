# setup-python PR #12 根因與驗證

日期：2026-11-06（Asia/Taipei）。範圍：公開 CI 維護與進度文件同步。

## 失敗證據與根因

原 PR head 為 `8b82c116f55281253f9713c25cd65fec3e3a2658`。
[原 validate run](https://github.com/mtchuang1981/clin-data-nav/actions/runs/40109747818)
的 Windows 與 Ubuntu 日誌均顯示 setup-python 與 Python 安裝成功，之後只有
`test_validation_workflow_uses_verified_node24_action_pins` 與
`test_release_workflow_uses_verified_node24_action_pins` 失敗。

Dependabot 已將兩個工作流程的五處 setup-python 引用更新至 v7.1.0，
但兩個測試仍要求 v7.0.0 的完整 SHA，因而拒絕新引用。套件比對因測試失敗而略過，
不能當成比對通過；原 head 的 CodeQL 為 neutral，也不能當成掃描通過。

先將已通過的 `main`（`e4f5edf`）整合至工作分支，再執行上述兩項測試，
得到相同的兩個斷言失敗，確認問題不只是過時基底。同步測試預期後，同一命令
得到 2 passed、159 deselected，退出 0。

## 上游依據與修正邊界

- [官方 v7.1.0 Release](https://github.com/actions/setup-python/releases/tag/v7.1.0)
  與 GitHub tag API 均指向完整 commit
  `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0`；API 回報 commit signature verified。
- [該 commit 的 action.yml](https://github.com/actions/setup-python/blob/6d4fd22b20465ccc0f7354476588e8df7c9ca0e0/action.yml)
  宣告 `runs.using: node24`，與原有執行環境要求一致。
- 僅同步兩個測試中的 SHA 與版本註解預期，保留不可變完整 SHA、版本註解、
  工作流程權限與兩平台／套件比對檢查，不改為接受任意 tag 或放寬 allowlist。
- 更新待辦文件的遠端整合狀態，將已完成公開補強移出目前待辦；歷史證據保持原樣。
- Skill 內容、契約、CLI、套件版本及發布附件均未修改。未執行 release 工作流程，
  因此不能以 validate 通過宣稱已實測發布流程。

後續 Dependabot 若更新其他受固定 SHA 檢查的 action，仍須先查核官方來源再同步預期；
這是保留的審查步驟，不以停用測試或自動信任新版本消除維護成本。

## 驗證與遠端驗收

Skill 驗證、公開邊界、可重現封裝檢查均退出 0。
公開 CI 的驗收以 [PR #12](https://github.com/mtchuang1981/clin-data-nav/pull/12)
確切最新 head 為準；本紀錄不預先宣告遠端 CI 成功或 PR 已合併。

### 本機完整測試首次失敗與有限追蹤

Python 3.11.9 完整測試首次結果：1,948 passed、1 failed、13 skipped，175.49 秒。
失敗項目為 `test_backup_cleanup_failure_rolls_back_before_success_notification`：
退出碼、固定錯誤輸出、原摘要還原及輸入不變的斷言均通過，最後「沒有交易暫存檔」
斷言失敗。列出的檔名為大寫 backup 文字加上 `.TMP.tmp` 尾碼，與過去異常形式相同，
但不足以證明兩次失敗的根因相同。

在再次執行 pytest 前，已將該案例的完全合成目錄複製至獨立 repo 外暫存位置，
並記錄可見檔案的 inode、裝置、時間、大小及 SHA-256。原始失敗輸出保留於本輪對話。
回查時異常名稱已不在原目錄中，因此沒有取得該檔案的身分、建立者或失敗當下 HANDLE；
不能判定為本程式缺陷、外部介入或特定系統行為，也未擴大刪除或放寬斷言。

沿用既有本機 probe，只改為追蹤本次失敗 node：1 passed、277 deselected，
共 16 筆事件，無截斷。觀察到注入的 backup 刪除錯誤後，rollback 刪除 stage、
關閉 stage／backup／parent；最後 owner/reference 均為零，原摘要存在且未見暫存檔。
追蹤工具與逐筆事件留在 Git 忽略的 `dist/cleanup-diagnostics-20261106/`；
probe 增加的時間與查詢可能改變競爭條件，單次通過不代表已修復。

未改動清理實作或相關測試，第二次完整測試為 1,949 passed、13 skipped，159.25 秒，
退出 0。跳過項目涉及本機 symlink 權限、Windows 檔名限制與 POSIX dir-fd 契約，
不列為已通過。此結果不覆寫首次失敗，也不提供 Windows 異常的修復證據。

Windows 間歇性清理異常仍未定位根因；本次 action pin 修正不代表該問題已修復。
私有機構驗收與真人評估仍須另行授權，未在本輪執行。
