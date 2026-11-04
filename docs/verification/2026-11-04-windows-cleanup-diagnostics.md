# Windows 清理異常：有限範圍診斷紀錄

日期：2026-11-04（Asia/Taipei）。
狀態：未重現，根因未明；不宣稱已修復。

## 調查範圍與依據

依照[既有計畫的診斷邊界](../superpowers/plans/2026-10-19-governed-compiler-pipeline.md)，
本次只查閱公開實作、執行合成測試及保留本機診斷。沒有修改 benchmark 執行邏輯、
現有清理測試、發布版本或安全門檻，也未存取私有系統。

歷史異常記於[2026-10-19 驗證紀錄](2026-10-19-governed-compiler-pipeline.md)：
`test_windows_summary_close_after_effect_is_never_retried[parent]` 曾出現殘留檔案，
名稱含大寫 backup 文字及 `.TMP.tmp` 尾碼。原始現場已不存在，無法補查當時的
檔案身分、建立者、開啟 HANDLE 或事件時間軸。

本機 HEAD：`e8b74d6`。沿用既有 Python 3.11.9 環境與 pytest 9.1.1，
並確認 `scripts` 載入目前 checkout。前輪文件與安裝測試變更仍留在工作目錄。

## 程式碼追查

`_SummaryTransaction.prepare` 先持有原輸出的 backup HANDLE，將原輸出改名，
再建立 stage 與寫入內容。`commit` 驗證檔案身分後，以 stage HANDLE 改名。

`finish` 驗證輸出仍是持有的 stage，先以 backup HANDLE 要求刪除備份，
再關閉 backup、stage、parent。`_finalize_reference` 對每個傳入 reference
只呼叫一次關閉函式；關閉函式拋錯時，不重試可能已被系統重用的數值。
這是程式碼與本次測試觀察，不代表所有環境下都不會洩漏資源。

名稱由 `_unique_name` 組成：小寫 `backup`／`stage` label、32 字元小寫十六進位亂數，
以及 `.tmp` 尾碼。歷史異常名稱與此形式不符；這不足以證明外部干擾，也不能排除
未重現的程式或系統問題。不應以萬用字元刪檔或重試關閉 HANDLE 來消除表面症狀。

## 有限範圍重現

預定上限為五輪有效診斷，每輪以獨立 Python 程序執行 backup、stage、parent
三個既有案例。診斷包裝器記錄交易邊界、關閉順序、HANDLE 查詢、合成檔名、
檔案身分與時間；不讀取回答或檔案內容。每個案例最多 500 筆事件。

第一次設定無效：將 pytest 合成輸入放在 repo 的 `dist/` 下，三個案例都在交易
開始前遭 `ensure_external_path` 拒絕，交易事件為零。此為診斷設定錯誤，
不列入清理異常重現或有效測試成功數。該紀錄保留，不以重跑成功覆蓋。

修正為每輪建立 repo 外的新暫存目錄後，完成五輪、共 15 個有效案例，全部通過：

- 共 240 筆事件，每個案例 16 筆，沒有事件截斷。
- 觀察到刪除 backup 後，依序關閉 backup、stage、parent。
- 交易結束時三個 owner/reference 欄位均為零，目錄內沒有交易暫存檔。
- 既有測試同時確認每個被觀察的關閉操作只嘗試一次，sentinel 身分不變，
  無關 HANDLE 未被再次關閉，輸入未改動，摘要與成功輸出符合原有斷言。

診斷會增加查詢與時間成本，可能影響競爭條件；五輪通過只能表示這五輪未重現，
不能建立失敗率上界、根因結論或修復證據。

未加診斷包裝器的完整 benchmark 測試模組：273 passed、5 skipped，102.14 秒，
退出 0。跳過項目為檔案系統 symlink 權限與 POSIX dir-fd 清理行為，未列為通過。

## 最終驗證

同一 Python 3.11.9 環境的完整 `python -m pytest -q`：1,949 passed、13 skipped，
206.74 秒，退出 0。此執行包含完整套件的既有測試順序，仍未重現原異常。
跳過項目涉及 symlink 權限、大小寫／尾端空白檔名及 POSIX dir-fd 行為。

`python scripts/validate_skill.py`、`python scripts/check_public_boundary.py`、
`python scripts/package_skill.py --check-reproducible` 均退出 0。
已檢閱文件差異、核對本機彙總／逐筆紀錄及原始碼雜湊，並通過 diff 空白檢查與
本次兩份進度／診斷文件的 11 個檔案連結檢查。未提交、推送或發布。

## 本機證據識別

診斷工具、逐筆事件、無效設定紀錄及每輪結果留在 Git 忽略的
`dist/cleanup-diagnostics-20261104/`。合成測試現場留在各輪新建的 repo 外暫存目錄，
位置記於該輪 `synthetic-root.txt`。這些是本機調查資料，不是公開套件的必要依賴。

| 項目 | SHA-256 |
| --- | --- |
| 本機彙總 `summary.json`（含五輪逐筆紀錄的雜湊） | `e6dc8e4ea71ea255cd9d5ae2d17da1c0ea0737b89862caab477e38d36de8bee0` |
| 本機診斷工具 `probe.py` | `34a936c053d132dc0b27417c7d0bc76ba3a89bcb6943770f1cea4aedcb16e7b9` |
| `scripts/evaluate_simulation_benchmark.py` | `8d39edd0419fd7f63ac074af875d2d869e518becf001fda0cde95dc673f8a910` |
| `tests/test_simulation_benchmark.py` | `7593c0f1372a3198681997be5bf89781391e01929bc4456d5480ed5b8fccfc86` |

## 下次失敗時的證據保留

先在受支援的 Python 3.11 環境執行原測試：

```text
python -m pytest tests/test_simulation_benchmark.py -q -k windows_summary_close_after_effect_is_never_retried --showlocals
```

保留首次失敗的完整輸出、測試 node ID、Python／pytest 版本、原始碼雜湊及 pytest
回報的暫存目錄。後續執行可能輪替 pytest 暫存目錄，須先將合成現場保存在 repo 外。
如需指定 `--basetemp`，必須使用新建且尚不存在的 repo 外路徑；pytest 會清除既有
basetemp，不能指向現有資料目錄。

在失敗現場記錄殘留檔案的精確名稱、檔案身分、時間與交易持有的 HANDLE 身分；
先比較是否為本交易建立的物件，再判斷刪除、關閉或其他行為。未建立身分關聯前，
不得擴大刪除範圍、改鬆斷言或把失敗視為可忽略的環境雜訊。
