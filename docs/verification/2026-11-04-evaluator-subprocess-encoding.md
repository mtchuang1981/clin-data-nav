# Evaluator subprocess 編碼一致性驗證

日期：2026-11-04（Asia/Taipei）。範圍：測試行程的編碼設定。

## 根因與重現

[v0.11.0 候選驗證紀錄](2026-10-24-ste-project-candidate.md)保留了父、子行程
編碼不同的已知限制。本次在 Windows、Python 3.11.9 重現於
`test_cli_returns_json_and_exit_codes_for_response_fixtures`。

原測試以 `sys.executable` 啟動子行程，沒有傳入父行程的 `-X utf8` 選項，
也沒有明訂 `subprocess.run(..., text=True)` 的解碼方式。父行程啟用 UTF-8 時，
子 CLI 仍依 Windows 預設 cp950 輸出；父行程的讀取執行緒以 UTF-8 解碼，
因 `0xa1` 位元組發生 `UnicodeDecodeError`。未取得的 stdout 成為 `None`，
後續 `json.loads` 因而拋出 `TypeError`。問題發生在測試的行程邊界，
不是評分、章節識別或輸入檔案的 UTF-8 讀取。

環境實測：一般行程 `locale=cp950`、`stdout=cp950`、`utf8_mode=0`；
啟用 `-X utf8` 後仍為 `locale=cp950`，但 `stdout=utf-8`、`utf8_mode=1`。

初次重現：兩個既有 Eval 測試模組共 1 failed、61 passed、2 個執行緒警告。
另將原測試兩次讀取明訂為 UTF-8、尚未調整子行程時，一般模式也重現同一失敗，
確認並非只在特定父行程啟動方式才會被測試偵測。

## 最小修正與相容性

沿用 `test_research_heading_contract.py` 已有模式：子行程命令加入 `-X utf8`，
並於兩次 `subprocess.run` 指定 `encoding="utf-8"`。沒有修改 CLI 本身、
預設輸出編碼、JSON 欄位、評分門檻、fixtures 或安裝套件。

不更動全域環境變數，也不依賴父行程選項會自動傳入子行程。
明訂解碼方式可讓未來移除子行程編碼設定的回歸在 Windows 既有環境中被偵測。
此修正只建立該測試的兩端編碼一致性，不宣稱所有 CLI 已有通用的編碼協定。

## 驗證

受影響的 evaluator、Eval contract 與 research heading 三個測試模組，
都使用 `-W error`，避免執行緒解碼警告被當成可忽略輸出：

| 父行程模式 | 結果 |
| --- | --- |
| 一般 `python -m pytest` | 119 passed，4.09 秒 |
| 僅父行程 `python -X utf8 -m pytest` | 119 passed，4.29 秒 |

上述測試包含既有 36 組 legacy 評估雜湊檢查，仍符合
`6c7db3794be2f5b74107a27ae9dae5e385aa82cfabb98be691bf4b67b72b8757`。
這是決定性的測試相容性結果，不是模型或臨床成效證據。

最終一般模式完整 `python -m pytest -q`：1,949 passed、13 skipped，205.39 秒，
退出 0。跳過項目為 Windows symlink 權限、大小寫／尾端空白檔名及 POSIX dir-fd
平台差異；未列為已驗證。本次未執行完整套件的父行程 UTF-8 模式，該模式的結果
僅限上表三個相關模組。

`validate_skill.py`、`check_public_boundary.py`、`package_skill.py --check-reproducible`
均退出 0；差異審閱、diff 空白與本次三份進度／診斷文件的 13 個檔案連結檢查通過。
前輪 Windows 清理異常仍維持未重現、根因未明；本次未提交、推送或發布。
