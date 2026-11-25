# SAS 文獻來源由 lexjansen.com 改為 saslexicon.org：更動報告

日期：2026-11-25
狀態：保留原始盤點與初步驗證，實作結果見第 7 節。
基準：`main` @ `122c9bd`（v0.11.2 收尾後）

## 1. 緣由

維護者決定將 ClinNav 的 SAS 實作文獻檢索來源由舊站
`https://www.lexjansen.com/` 改為新站 `https://saslexicon.org/`。本報告記錄
引用盤點、建議修改、驗證結果與待決事項，供後續版本實作時依循。

## 2. 新站查核（已確認事實）

查核日期：2026-11-25；來源：`https://saslexicon.org/` 首頁。

- 站名 SAS LEX.ICON，自述為 Lex Jansen 的 SAS 知識分享社群站點，並設有紀念
  Lex Jansen 的頁面；由華沙理工大學數學與資訊科學學院架設。
- 收錄 16 個會議、37,882 篇論文，含 PharmaSUG、PharmaSUG CN、PHUSE US、
  PHUSE APAC、PHUSE EU、SUGI/SGF、WUSS、MWSUG、SCSUG、NESUG、PNWSUG、SEASUG、
  SAS Innovate、SAS Explore、VIEWS、SEUGI。
- 會議索引網址格式為 `saslexicon.org/<CONF>/<CONF>.html`；站內提供 Quick
  Search、作者與關鍵字瀏覽。
- 自述為託管位置、非出版者，另設勘誤回報頁。

### 尚未確認

- 首頁未提及 lexjansen.com，亦未聲明為其後繼或遷移站。
- 單篇論文的網址格式，以及 PDF 是由本站託管或連回原會議網站，尚未確認。
- 搜尋引擎對本站的收錄程度未知，`site:saslexicon.org` 查詢的召回率需實測。

### 補充檢索來源

- **SAS Papers Index（TUNECT）** 受 Lex Jansen 的工作啟發，提供公開的跨會議檢索，
  涵蓋 PHUSE、PharmaSUG、SAS Global Forum 和區域 SAS 使用者社群等。索引收錄書目資訊與
  連結，取得論文時可循連結查閱原始來源。[索引說明](https://sas-papers.tune-ct.com/about/)
- **PPI（The Pharmaceutical Proceedings Index）** 是供醫藥與臨床程式設計人員查找會議
  資料的社群索引。已核對建站者公告。直接連線時憑證驗證未通過，本次未確認 PharmaSUG 等
  會議的實際收錄範圍。[建站者公告](https://communities.sas.com/t5/All-Things-Community/PPI-The-Pharmaceutical-Proceedings-Index/td-p/992004)

兩者均可用來發現候選文獻，取得全文後再查核出處和重用條件。

## 3. 引用盤點

全 repo 共 25 個檔案含 `lexjansen`（不分大小寫）。依性質分為四類：

| 類別 | 檔案 | 處置 |
|---|---|---|
| A. 技能行為（會被安裝、影響輸出） | `skills/clin-nav/SKILL.md` L125、L132；`skills/clin-nav/references/retrieval-playbook.md` L44–45 | 改 |
| B. 評測規則與夾具 | `evals/cases.yaml` L43；`tests/test_simulation_benchmark.py` L217；`tests/fixtures/forward/sas-optimization-lexjansen.md` L10 | 改（與 A 同步，否則新行為會被判為不通過） |
| C. 識別碼 | 案例 ID `sas-optimization-lexjansen`、effectiveness 任務 `evidence-lexjansen-sas` 及其在測試、benchmark examples 的引用 | 不改；為穩定識別碼，改名會連動多個檔案與雜湊值 |
| D. 歷史文件 | `docs/superpowers/plans/2026-07-28-*`、`2026-08-02-*`；`docs/superpowers/specs/2026-07-28-*`、`2026-07-29-*`、`2026-09-18-*` | 不改；保留當時決策紀錄 |

另：`2026-09-18-v0.8.0-public-evidence-ledger-pilot-design.md` 引用單篇論文
`https://www.lexjansen.com/phuse/2017/as/AS02.pdf`。因新站單篇網址格式未確認，
暫不對應。

## 4. 建議修改（A、B 類，共 5 檔 7 行）

```diff
--- a/skills/clin-nav/SKILL.md
-Treat Lex Jansen as an index of implementation literature, not a standards
+Treat SAS LEX.ICON (saslexicon.org, the Lex Jansen community index) as an index of implementation literature, not a standards
-`site:lexjansen.com` query. Review the specific paper, not only an index entry or snippet.
+`site:saslexicon.org` query. Review the specific paper, not only an index entry or snippet.

--- a/skills/clin-nav/references/retrieval-playbook.md
-   `site:lexjansen.com <deliverable-or-domain> <technique> SAS`.
-2. Open the specific paper from `https://www.lexjansen.com/` or its linked
+   `site:saslexicon.org <deliverable-or-domain> <technique> SAS`.
+2. Open the specific paper from `https://saslexicon.org/` or its linked

--- a/evals/cases.yaml
-      - 'site:lexjansen\.com'
+      - 'site:saslexicon\.org'

--- a/tests/test_simulation_benchmark.py
-        "site:lexjansen.com",
+        "site:saslexicon.org",

--- a/tests/fixtures/forward/sas-optimization-lexjansen.md
-Use `site:lexjansen.com` for the specific technique, then review the specific paper
+Use `site:saslexicon.org` for the specific technique, then review the specific paper
```

`SKILL.md` 第一處改寫後超過原本行寬，實作時應重新斷行。

## 5. 驗證結果

於本地以 `python -m pytest -q` 比對修改前後的失敗清單：

- 修改前（基準）：228 筆 FAILED／ERROR。多數看似與執行環境有關，未逐一追查，
  不屬本次變更範圍。
- 套用第 4 節修改後：247 筆，新增 19 筆，全部來自凍結的雜湊值：
  - `tests/test_research_heading_contract.py::test_36_legacy_evaluations_keep_prechange_digest`
    （寫死 36 筆舊評測結果的 SHA-256，評測規則字串變動即改變）
  - `tests/test_simulation_benchmark_reports.py` 18 筆（`evals/benchmark/examples/`
    的 synthetic summary／report 記錄 `catalog_sha256`，`cases.yaml` 變動後不符）

新增失敗不代表新連結有誤，而是 repo 刻意凍結的紀錄需要更新。

## 6. 待決事項

1. 是否更新凍結雜湊值：建議以小版本（如 v0.11.3）處理，用
   `scripts/prepare_simulation_benchmark.py` 重新產生 benchmark examples，
   更新 `test_36_legacy_evaluations_keep_prechange_digest` 的 digest，並於
   `CHANGELOG.md`／`CHANGELOG.zh-TW.md` 說明原因。
2. 實測 `site:saslexicon.org` 的搜尋結果；若召回不足，於 playbook 補上站內
   Quick Search 或會議索引頁作為替代路徑。
3. 確認新站單篇論文網址與 PDF 託管方式後，再決定是否處理 v0.8.0 spec 中的
   單篇論文連結。
4. 確認 README、CHANGELOG 等使用者文件是否需加註來源變更。

## 7. 實作結果

- Skill 與檢索手冊已改用 SAS LEX.ICON。網域限定搜尋沒有相關結果時，可直接查索引或原會議論文集。
- 已同步更新評測規則、合成夾具與固定雜湊。36 筆結果中，只有換址案例的兩筆評測結果內容有差異，通過與未通過判定一致。
- 保留既有案例 ID 與歷史論文連結。這次提交範圍為來源遷移及其驗證文件。
