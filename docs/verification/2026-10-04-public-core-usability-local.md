# 公開核心本機驗證紀錄

日期：2026-10-04。狀態：本機實作及 deterministic 驗證完成，未合併或發布。

## 範圍與基線

- 分支：`codex/public-core-usability`；Native 執行，最後一次獨立全分支審查。
- 基線／未變的 main：`a8b9976dbbf62fec250fb7c571f3e714ce0b360f`。
- 最終產品驗證 commit：`fd69a609dd1881d55eae428564233f580db8951e`。
- 本紀錄只保存 aggregate-only 計數、命令、版本、commit、雜湊與限制。
  不包含實際 audit、來源副本、raw responses、私有結構或真人研究資料。
- 不變更版本號、CHANGELOG、workflow、已發布資產、舊 ledger parser／example、
  agents policy、Eval catalog／scoring／fixtures／歷史結果；不接觸私有 adapter。

## 已完成交付

| Task | 本機 commit | 交付 |
| --- | --- | --- |
| A1 | d50cf5e | 雙語目前 release 資產名稱與 main dispatch／不可變 SHA 文件 |
| A2 | dbc698c | 正式缺口五欄契約與三個不可執行的合成範例 |
| A3 | afecf02 | 雙語選填公開流程回饋；未驗證 community self-report 界線 |
| B1 | bb4622e | 限額、深度與重複鍵／非有限數值拒收的 strict JSON reader |
| B2 | 79f7d5e | 選用 companion audit，綁定 ledger 並聯集全部既有缺口 |
| C1 | 5cf7ff4 | 狹窄套件 helper 抽取，保留 installer wrappers／constants／行為 |
| C2 | 6207534 | 可信 manifest 唯讀診斷、雙語文件與解壓 ZIP parity |
| Review fix | fd69a60 | IDNA 後 IP／localhost 與非標準數字 IPv4 拒收 |

每項行為變更先觀察 RED，再實作及 GREEN。C1 完整回歸定位到既有環境的
舊 scripts package 遮蔽新 helper；以專用失敗測試修正明確 submodule import，
保留本機 fallback，未修改全域設定或弱化測試。全部測試只用公開合成 fixtures。

## Runtime 與驗證

既有可執行環境：Python **3.11.9**（uv-managed build）、pytest **9.1.1**、
PyYAML **6.0.3**，符合專案 `>=3.11,<3.12`。確認版本與執行，未獨立查核
runtime 發行檔 provenance／hash；不稱為已驗證的官方 Python.org 安裝。
未下載、安裝或改動全域 runtime。每次 pytest 使用新的 repository 外 basetemp；
使用 `PYTHONDONTWRITEBYTECODE=1`、`PYTHONUTF8=1`，以 RTK proxy 保留判定輸出。

| 檢查 | 結果 | Exit |
| --- | --- | --- |
| `python -m pytest -q --basetemp <fresh-external-basetemp>` | 修補後 1,681 passed、11 skipped；167.69s | 0 |
| `python scripts/validate_skill.py` | 無 findings | 0 |
| `python scripts/check_public_boundary.py` | 無 findings | 0 |
| `python scripts/package_skill.py --check-reproducible` | 可重現 | 0 |
| `python scripts/render_eval_summary.py --check` | 快照一致 | 0 |
| `python scripts/render_effectiveness_report.py --summary evals/effectiveness/examples/synthetic-summary.json --english evals/effectiveness/examples/synthetic-report.md --traditional-chinese evals/effectiveness/examples/synthetic-report.zh-TW.md --check` | 合成報告一致 | 0 |
| `python scripts/render_simulation_benchmark.py --summary evals/benchmark/examples/synthetic-summary.json --english evals/benchmark/examples/synthetic-report.md --traditional-chinese evals/benchmark/examples/synthetic-report.zh-TW.md --check` | 合成報告一致 | 0 |
| `git diff --check` | 無 whitespace errors | 0 |

11 skips：audit 真實 file-symlink 1 項、既有 benchmark file-symlink 1 項及
symlink/reparse 3 項、POSIX dir-fd cleanup 1 項、安裝診斷 root/member/cache/
manifest/ancestor symlink 5 項。略過原因為 Windows 權限或平台不提供該能力。
實體 Windows junction 拒收有執行；合成 reparse attributes、opened-fstat identity、
post-stat mtime 與讀取中成長檢查也有執行，不將模擬結果說成真實 symlink 覆蓋。

最後文件／計畫狀態更新後，文件 focused 回歸 171 passed；再次完整回歸
1,681 passed、11 skipped，171.32s、exit 0。公開邊界與 diff 檢查再次通過。

真 ZIP 解壓到 repository 外目錄後，與 source audit CLI 的 complete／review／
invalid 三態 stdout、stderr、exit `0/3/2` 完全一致（3 項 integration tests）。
不讀取任何真實安裝或歷史外部 pilot artifact。

## 可重現開發候選產物

URL 修補後兩次獨立 development build 的 ZIP／manifest **逐位元相同**。
以下保留原 package version／檔名，只表示未發布的候選；**不是已發布 v0.8.0
產物的 hash，不可用來取代既有 release 的信任根**。

| 候選產物 | Bytes | SHA-256 |
| --- | --- | --- |
| clin-nav-0.8.0.zip | 54162 | 884debb04144c7a1541ce78bfd4a722175f6ef01dc4aff498712b4eb929c3457 |
| clin-nav-0.8.0.manifest.json | 3200 | b1b598db643205e2e95253e72b7d7a773f30540bede503c35b59fab41beb6c7d |

沒有覆寫或上傳任何已發布產物。

## 獨立審查與單次修補

一次 fresh-context `gpt-6-astra` 唯讀審查範圍 `a8b9976..6207534`。
Critical 0、Important 1、Minor 0。審查者自行以記憶體內合成輸入重現：IDNA
之前做 IP 拒收會放過全形 IPv4，以及短寫、八進位、十六進位數字 IPv4 別名。
沒有網路連線，因此不是已發生的 SSRF／外洩，但違反公開 URL 契約。

作者完成唯一 fix pass：三種 URL 欄位合計 18 項負向測試先失敗，再改為先
IDNA／大小寫／結尾點正規化，之後拒收 IP／localhost 與非標準數字形式。
另有 3 項一般網域接受測試。修補後 audit／CLI／ZIP parity 156 passed、1 skipped，
完整 suite 與上述 gates 通過。沒有派第二位 reviewer，也不宣稱重新獨立審查
過修補後的程式；修補證據是 RED→GREEN 與完整回歸。

## 執行裁定與剩餘限制

1. A/B/C task IDs 不符 skill task-brief 的 numeric-only helper：採原生 PowerShell
   精確 heading extraction 及 BASE／結果 ledger。代價是人工 bookkeeping；以
   task brief、commit range 及完成證據核對。
2. 不執行模型 campaign 或改歷史 Eval scoring：採 deterministic 結構契約及
   舊消費端相容測試。代價是沒有新的模型措辭／真人成效證據，不宣稱已證明。
3. 新增窄 `read_bounded_stream` 共用介面：C2 必須 fstat 同一 opened descriptor，
   避免重開檔或重複 guard。代價是多維護一個已測試的 helper；舊 reader 不改。
4. 來源真實性、notes 語意、scope 合理性仍由人工判斷。代價是記錄完整也可能
   判斷錯誤；audit exit 0 不等於來源正確、臨床有效或部署就緒。
5. 已知 public-boundary nested `.git` root-discovery 變體另案處理。代價是該
   變體仍可能接受祖先 repo；本輪未修復，也未弱化其測試。
6. Host loaded version 與惡意本機競態的原子性不在工具保證內。代價是內容
   一致不代表已載入，best-effort 也不能保證防住具有本機修改權限的攻擊者。
   Manifest 範圍的成功不包含 archive、ignored bytecode 或 runtime 完整性。
7. 遠端 Windows／Ubuntu CI 與真實安裝相容性未驗證。代價是其他環境差異仍
   可能存在；本機合成結果不能替代日後經授權的 CI／host smoke checks。

延期 Minor：無。保持本機隔離分支；merge、push、遠端 CI、tag／Release 需另行授權。
