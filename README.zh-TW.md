[English](README.md) | 繁體中文

# Clinical Data Research Navigator

這是一套可安裝的 Agent Skill，協助你把臨床資料問題整理成依權威性排序的指引，但不會提供私有 schema，也不會宣稱已產出具臨床效度的結論。

[![Validation](https://github.com/mtchuang1981/clin-data-nav/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/mtchuang1981/clin-data-nav/actions/workflows/validate.yml?query=branch%3Amain)

## 安裝到專案

```bash
npx skills add mtchuang1981/clin-data-nav
```

Node.js 必要條件、更新、驗證 ZIP 安裝與疑難排解，請見[安裝指南](docs/installation.zh-TW.md)。

## 第一次成功使用

請在 Codex 輸入：

```text
$clinical-data-research-navigator ADaM 是什麼、為什麼重要，又不能證明哪些來源資料品質？
```

預期第一行：`Output depth: quick explanation`

- 直接用白話定義 ADaM，並說明它在此情境的重要性。
- 列出一至兩項常見混淆或限制，再附上精簡的主導來源清單。

## 選擇輸出深度

| 深度 | 適合用途 | 不會自行加入 |
|---|---|---|
| `quick explanation` | 名詞解釋、比較與初學者問題 | 完整證據矩陣或實作契約 |
| `evidence navigation` | 尋找、排序與比較主導來源 | 把未審閱的搜尋摘要當成證據 |
| `research design` | 規劃描述、預測或因果比較研究 | 已完成的 SAP、estimand 或因果結果 |
| `implementation specification` | 資料契約、對應、衍生規則與驗證規則 | 在執行閘門未完備時產生可執行的機構程式碼 |

只要不牴觸安全閘門，Skill 會遵循你明確指定的深度；否則會選擇足以回答
問題的最精簡深度，並把更深入的模式列為下一步，不會一次混合所有深度。

## 選擇學習路徑

- [臨床試驗與 CDISC](docs/learning-paths.zh-TW.md#learn-the-terms)：CDISC → SDTM → ADaM → 試驗計畫書／SAP → 實作證據。
- [RWD 與 RWE](docs/learning-paths.zh-TW.md#assess-the-evidence)：目的 → PICO 延伸欄位 → RWD 適用性 → RWE 主張 → 因果比較問題的 TTE 就緒度。
- [機構實作](docs/learning-paths.zh-TW.md#prepare-an-implementation)：公開證據 → 邏輯資料契約 → 核准的 Adapter → 現行詮釋資料 → fixture → 可執行／已驗證狀態。

## Agent Skill 與 Plugin 的界線

OpenAI 官方文件說明，Skill 會封裝操作指引、資源與選用指令碼，讓 ChatGPT
或 Codex 能依工作流程執行任務；Plugin 則是另一種發布套件，用來發布可重複
使用的 Skills 與 connectors。本儲存庫透過 GitHub 發布可安裝的 Agent Skill，
不宣稱已刊登於公開 Plugin 目錄；安裝本儲存庫不會建立或發布 Plugin。

## 文件導覽

| 需求 | 請前往 |
|---|---|
| 安裝、更新、驗證 ZIP 或疑難排解 | [安裝指南](docs/installation.zh-TW.md) |
| 查詢名詞 | [初學者詞彙表](docs/glossary.zh-TW.md) |
| 依序學習 | [學習路徑](docs/learning-paths.zh-TW.md) |
| 合成資料實作範例 | [TEAE 到 SAS](examples/teae-to-sas-spec.md)、[OMOP phenotype 到 SQL 規格](examples/omop-phenotype-to-sql-spec.md)及[機構對應](examples/synthetic-institutional-mapping.md) |
| 證據輸出與限制 | [證據輸出範本](skills/clinical-data-research-navigator/references/evidence-output-template.md)與[架構說明](docs/architecture.md) |
| 產品效果評估框架 | [效果評估](evals/effectiveness/README.md) |
| 參與貢獻與驗證 | [貢獻指南](CONTRIBUTING.md) |
| 回報安全性問題 | [安全性說明](SECURITY.md) |
| 準備經核准的發布 | [發布流程](docs/release.md) |
| 查看 v0.3.0 變更 | [靜態 Release notes](docs/releases/0.3.0.md)與[版本紀錄](CHANGELOG.zh-TW.md) |
| 查核目前產品指引 | [OpenAI 的 ChatGPT Skills 說明](https://help.openai.com/en/articles/20001066)與[Codex Skill 文件](https://learn.chatgpt.com/docs/build-skills) |

## 證據、公開邊界與限制

Skill 會優先採用主導來源，再參考實作文獻，並清楚區分已確認事實、假設、
限制與來源。儲存庫的確定性 Evals 只檢查回覆契約，不能證明來源正確、臨床
效度、因果效度或真實世界情境已完整涵蓋。

儲存庫另有獨立的[效果評估框架](evals/effectiveness/README.md)，供公開離線
演練及另行核准的探索性人類先導研究使用。框架存在不代表已執行先導研究，
也不構成任何已觀察到的效果證據。

這套公開核心只包含可重複使用的指引、合成範例、測試與封裝工具；不包含私有
TMUCRD Adapter、codingbook、資料字典、實體 schema、串接規則、PII 分類、
憑證或需登入才能存取的文件，也不是 TMUCRD 資料字典。機構實作必須在本
儲存庫外使用經核准且具版本控管的私有 Adapter，並在受治理環境查核現行
詮釋資料。

[詞彙表](docs/glossary.zh-TW.md)說明 CDISC、SDTM、ADaM、RWD 與 RWE。
RWD 不會自動成為 RWE。只有具備必要設計欄位的因果比較問題，才會評估目標
試驗模擬。`build-rwe-sap` 是選配項目，未內附；clin-data-nav 不會自動安裝。

缺少核准的 Adapter、現行詮釋資料、參數或 fixture 時，實作要求會維持
`SPECIFICATION ONLY — NOT EXECUTABLE`，不得臆造本地資料表、欄位、join、
代碼或可直接上線的邏輯。資訊不足時，回覆會先做問題釐清並提供缺少資訊清單，
不會捏造確定答案。使用安裝後僅含指令與參考文件的 Skill 不需要 Python；
Python 3.11 只供[貢獻指南](CONTRIBUTING.md)所述的儲存庫開發與發布工具使用。
