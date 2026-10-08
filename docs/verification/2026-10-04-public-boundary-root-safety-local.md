# Public-boundary 根目錄辨識：本機驗證紀錄

日期：2026-10-04。範圍：已核准的小範圍修補；本機隔離分支，不 merge、push 或發布。

## 基線與修補

- 分支：`codex/public-boundary-root-safety`。
- 基線／未變的 main：`945492fbb2c53b97e594c5f1452d908148e8255a`。
- 根因：`.git.exists()` 加上 `--is-inside-work-tree=true` 只證明屬於某個
  repository；無效 nested `.git` 仍可能讓 Git discovery 接受祖先根目錄。
- 修補：取得 `--show-toplevel`，只移除輸出結尾的一個換行，驗證絕對路徑，
  再 resolve／samefile 核對實體根目錄；不同或查詢失敗沿用
  `tracked-path-query-failed`。CLI exit `1`，不回顯 Git stderr 或實體路徑。
- 保留合法 linked-worktree `.git` file、無 `.git` 的 filesystem fallback、
  分類規則與其他 API／CLI 契約。沒有讀取私有 adapter 或真人研究資料。

## TDD 與驗證

使用既有 Python **3.11.9**（uv-managed build）；不下載、安裝或修改全域設定。
僅確認版本與執行，未獨立查核 runtime provenance／發行檔 hash。
所有 fixtures 都是公開合成案例，每次 pytest 使用全新的 repository 外 basetemp。

| 階段／檢查 | 結果 | Exit |
| --- | --- | --- |
| 完整基線 | 1681 passed、11 skipped；205.35s | 0 |
| 新 ancestor／redirect regressions，修改前 | 3 failed、7 passed、1 skipped；API／CLI 誤接受及 root redirect | 1 |
| 首次修補 focused boundary／policy | 101 passed、1 skipped | 0 |
| 首次修補完整回歸 | 1691 passed、12 skipped；210.77s | 0 |
| Review identity regressions，samefile 修改前 | 2 failed、1 skipped、11 deselected | 1 |
| samefile 後 focused boundary／policy | 103 passed、2 skipped；5.36s | 0 |
| 最終產品完整回歸 | 1693 passed、13 skipped；212.32s | 0 |
| `python scripts/validate_skill.py` | 無 findings | 0 |
| `python scripts/check_public_boundary.py` | 無 findings | 0 |
| `python scripts/package_skill.py --check-reproducible` | 可重現 | 0 |
| `python scripts/render_eval_summary.py --check` | 快照一致 | 0 |
| 既有 effectiveness 合成英文／繁體中文 renderer `--check` | 快照一致 | 0 |
| 既有 simulation benchmark 合成英文／繁體中文 renderer `--check` | 快照一致 | 0 |
| `git diff --cached --check` | 無 whitespace errors | 0 |

最終兩個 renderer 分別使用 `evals/effectiveness/examples/synthetic-summary.json`
及 `evals/benchmark/examples/synthetic-summary.json`，核對各自既有
`synthetic-report.md`／`synthetic-report.zh-TW.md`；未重新生成或改寫歷史結果。

13 skips：既有 symlink 權限／平台及 POSIX dir-fd 能力 11 項；新增 Win32
不可靠的結尾空白 path 1 項、此 filesystem 不支援 case-distinct sibling
directories 1 項。後兩項不是已實測通過。真實 linked worktree、Unicode／內部
空白、Windows separator／大小寫別名有執行；OS identity 不同與 lookup failure
使用明確標示的合成 boundary 模擬，不冒稱真實 Windows case-sensitive 實測。

## 套件不變與審查

修改前與最終 development candidate 的 ZIP／manifest **逐位元相同**：

| 產物 | Bytes | SHA-256 |
| --- | --- | --- |
| clin-nav-0.8.0.zip | 54162 | 884debb04144c7a1541ce78bfd4a722175f6ef01dc4aff498712b4eb929c3457 |
| clin-nav-0.8.0.manifest.json | 3200 | b1b598db643205e2e95253e72b7d7a773f30540bede503c35b59fab41beb6c7d |

這些是未發布 development candidate hashes，不是已發布 v0.8.0 的信任根。
Skill、版本號、CHANGELOG、workflows、歷史 Eval 與發布產物均未改動。

一次唯讀完成品 review：Critical 0、Important 1、Minor 0。Important 是 Windows
路徑 equality 的 case-fold，可能誤接受 case-sensitive directories 中不同實體
根目錄；reviewer 只確認純記憶體 equality，未重現實體情境。作者以 2 筆 RED
測試補強 samefile，再跑 focused、完整 suite 與全部 gates。
同一 reviewer 已核對單次 fix diff，確認該項 addressed；不是第二輪全分支審查，
reviewer 未獨立重跑 suite。延期 Minor：無。

公開紀錄加入後再跑 focused boundary／policy：103 passed、2 skipped，exit 0；
公開邊界及 staged diff-check 也再次 exit 0。

## 執行裁定與剩餘限制

1. 查詢與列舉之間的惡意本機競態不在本輪處理；代價是 root identity gate
   不等於原子檔案系統／index 快照，不能宣稱防住有本機修改權限的攻擊者。
2. `GIT_DIR`／`GIT_INDEX_FILE` 指向其他 metadata、但實際回報的 worktree root
   正確時，index provenance 是另一個信任邊界，本輪未修。代價是本次成功只
   證明特定 root-discovery 問題已修補，不證明所有 Git 環境重導都安全。
3. 沿用現有隔離 worktree，只建立新分支，保留 E 槽 OMOP checkout；未修 ACL。
   遠端 Windows／Ubuntu CI、POSIX 新案例及實體 case-sensitive Windows 情境
   尚未驗證。未建立 tag 或 Release，不宣稱新的模型或真人使用成效。
