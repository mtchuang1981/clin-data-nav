# Windows 清理異常：原生 API 與檔案身分證據

日期：2026-11-06（Asia/Taipei）。本機基底：`d9f2e90`。
狀態：已重現；建立異常物件的程序與根因仍未明，尚未修復。

本次只使用公開合成測試與 repo 外的新建暫存目錄，延續
[既有診斷邊界](../superpowers/plans/2026-10-19-governed-compiler-pipeline.md)
及[現場保留流程](2026-11-04-windows-cleanup-diagnostics.md)。
沒有修改清理實作、測試斷言或 HANDLE 所有權規則，沒有存取私有系統或真人材料。

## 本輪結果

在 Python 3.11.9 下，追蹤既有 backup-cleanup 失敗還原案例，以及
`test_windows_summary_close_after_effect_is_never_retried` 的 backup、stage、parent
三個案例。每個案例事件上限 400 筆，最多五輪。

| 輪次 | 環境與追蹤 | 結果 |
| --- | --- | --- |
| 1 | 一般工具沙箱，原生 API 結果與斷言時的 lstat | 4 passed |
| 2 | 同上；首次失敗即停止該組重跑 | 3 passed、1 failed（parent 關閉案例） |
| 3 | 一般 Windows 執行環境對照 | 4 passed；pytest cache 有存取拒絕警告 |
| 4 | 工具沙箱；另準備在異常名稱出現時取得原生 ID | 4 passed，沒有觸發異常名稱的原生 ID 查詢 |
| 5 | 第四輪追蹤設定的一般 Windows 環境對照 | 4 passed；pytest cache 有存取拒絕警告 |

合計 19 passed、1 failed，共 505 筆事件，沒有截斷。
保留第二輪失敗輸出、事件、合成現場及各輪結果；後續對照不覆寫首次失敗。
追蹤包裝器會增加查詢與時間成本，這些結果不構成失敗率估計。

另以不載入專案、pytest 或自訂原生函式的 Python 標準函式庫控制組，
在 20 個新建合成目錄執行 rename/delete，延遲 10 ms 後列舉，未見異常。
這個操作序列不等於完整交易，不能據此判定哪個 API 或環境是根因。

## 失敗當下已確認的事實

- 兩次 rename 與一次 delete disposition 的 NTSTATUS 均為 0。
- backup、stage、parent 的 CloseHandle 各一次，均回傳 1；未見重新關閉同一數值。
- 原 backup 的原生 128-bit ID 為 `4a9c4100000003000000000000000000`，
  低 64 位整數為 `844424934431818`。
- 斷言列出大寫 backup 文字及 `.TMP.tmp` 尾碼的名稱；立即 lstat 觀察到的
  inode 為 `1125899911142474`、大小為 0，與原 backup 的 ID 及 17-byte 內容長度不同。
- backup CloseHandle 至該 glob 記錄約 9.82 ms。這不是檔案建立時間或存在期間。
- 最終摘要、固定成功輸出、輸入不變與 sentinel 身分的既有斷言通過；
  失敗點仍是「沒有交易暫存檔」的名稱列舉斷言。

在此環境的既有檔案 ID 比對規則下，觀察到的物件不是原 backup 的同一檔案身分。
這不足以證明建立者是外部程序，也不能排除尚未追蹤的程式或系統路徑。
第二輪沒有取得異常名稱的直接原生 HANDLE ID；第四輪才加入該查詢，且未重現，
因此不可將第四輪能力回寫成第二輪已取得的證據。

## 推論與修正界線

目前證據不支持直接將本次異常稱為「原 backup HANDLE 關閉失敗造成殘留」。
兩輪一般環境對照共八個案例通過，但帳號／權限、cache 警告、時序及樣本數均限制可比性，
不能據此歸因於沙箱。

[Microsoft FILE_DISPOSITION_INFORMATION 文件](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntddk/ns-ntddk-_file_disposition_information)
說明刪除標記與實際移除有區別；
[NtSetInformationFile 文件](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntsetinformationfile)
限制刪除標記成功後只應關閉該 HANDLE。本輪未在 disposition 成功後查詢該 HANDLE，
也未重試可能已關閉的數值或刪除身分未確認的新物件。

既有 probe 只包裝本模組的原生入口，不是系統完整事件紀錄，無法查明新物件的建立者 PID。
下一步若使用 Process Monitor，須先另行核准載入診斷驅動，確認只保留新建合成目錄事件，
最多追蹤 60 秒或首次失敗即停止。該追蹤目前尚未執行。
不以重跑通過、增加延遲、萬用字元刪除或放寬斷言當作修復。

## 本機證據與來源識別

逐筆事件、輸出、合成現場副本與工具留在 Git 忽略的
`dist/cleanup-native-probe-20261106/`，各輪另記 repo 外合成根目錄。
公開文件只保留合成觀察摘要與雜湊，不包含主機路徑或全域程序事件。

| 項目 | SHA-256 |
| --- | --- |
| 彙總 summary.json，含各輪事件檔雜湊 | `9c522bbfb17ba0cd4801b9b07517fe9aa31e1f0feb715f590163adde9343bc2b` |
| 第一、二輪使用的 probe-v1.py | `795f6fd799cf0149d45009becb7497399777fab69575180139d3db5f6ee50b22` |
| scripts/evaluate_simulation_benchmark.py | `8d39edd0419fd7f63ac074af875d2d869e518becf001fda0cde95dc673f8a910` |
| tests/test_simulation_benchmark.py | `7593c0f1372a3198681997be5bf89781391e01929bc4456d5480ed5b8fccfc86` |

PR #12 已另行合併至 `d9f2e90`，該 main 提交的 Windows、Ubuntu、套件比對及
CodeQL 均成功；這些成功不推翻本輪重現結果，也不代表本項已修復。

## 進度文件同步驗證

本次變更只有本紀錄與待辦清單。Python 3.11.9 完整 `python -m pytest -q`：
1,949 passed、13 skipped，169.46 秒，退出 0。跳過項目涉及本機 symlink 權限、
Windows 檔名限制及 POSIX dir-fd 契約，不列為通過。
Skill 驗證、公開邊界與可重現封裝檢查均退出 0；兩份文件的本機連結、
所引用的本機證據／來源雜湊及 diff 空白檢查均通過。
本輪完整測試輸出留在上述本機診斷目錄的 `docs-full-pytest.txt`。
此次通過只驗證文件變更所在 checkout 的該次執行，不覆寫前述 19／1 診斷結果。
