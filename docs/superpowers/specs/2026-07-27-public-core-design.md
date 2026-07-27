# Clinical Data Research Navigator 公開 Core 專案設計

**狀態：** 已核准，可進入 implementation plan 與 TDD 實作

**日期：** 2026-07-27

**預定儲存庫：** `clin-data-nav`

**預定授權：** Apache License 2.0

## 1. 決策摘要

建立一個全新的公開 Git 儲存庫，作為
`clin-data-nav` 的唯一來源專案（source of truth）。
現有個人 Skill 僅作為行為需求與測試基準，不沿用其 Git 歷史，也不直接複製
TMUCRD 私有參考檔。

公開儲存庫包含：

- 跨機構可用的臨床資料研究導航 Skill。
- 來源權威分級、檢索式、證據整理與實作規格工作流。
- 通用 institutional adapter contract。
- 以公開文獻重寫的 TMUCRD 描述性 profile。
- 離線可執行的結構、公開邊界與行為契約測試。
- Codex 維護規則、GitHub Actions、授權與社群文件。

公開儲存庫不包含：

- TMUCRD 內部 codingbook、文字擷取檔或其衍生資料字典。
- 內部手冊所載的實體表、欄位、型別、代碼、鍵、cardinality、筆數、
  availability matrix、PII 分類或版本異動。
- 任何可直接查詢 TMUCRD 的 SAS、SQL、R 程式。
- 目前個人 Skills 儲存庫的既有 commit history。

TMUCRD 私有 Adapter 暫留既有受管制環境，不在本階段建立第二個 repository。

## 2. 目標與非目標

### 2.1 目標

1. 讓 Codex、ChatGPT 與相容 Agent Skills 的系統能安裝、閱讀及執行通用工作流。
2. 讓 Codex 能依 repository 內的 `AGENTS.md` 自主維護、測試及審查變更。
3. 讓每次修改都能透過 GitHub Actions 驗證結構、公開邊界與回歸規則。
4. 讓機構專用資料字典以外掛 Adapter 方式掛載，不污染公開核心。
5. 讓 TMUCRD 作為有正式文獻支持的真實案例，但只回答「資料庫是什麼與具備哪些
   資料能力」，不回答「現行實體 schema 如何查」。
6. 提供可重現的安裝包，使 Git tag、GitHub Release 與本機安裝副本能追溯至同一
   commit。

### 2.2 非目標

- 不在公開版保存或同步院內文件。
- 不建立能存取 TMUCRD、Notion、IRB、EHR 或其他私有系統的 connector。
- 不在 CI 呼叫付費 LLM 或要求 API key。
- 不把本 Skill 擴張成完整 RWE SAP、target trial emulation 或因果推論引擎。
- 不在第一版包裝成 OpenAI Plugin；Plugin 是 Core 穩定後的後續發布層。
- 不在本階段建立或推送 GitHub repository；外部發布須另經使用者指示。

## 3. 公開／私有邊界

### 3.1 公開 allowlist

只有下列內容可以進入全新的 Git 歷史：

| 類別 | 可公開內容 |
|---|---|
| 核心工作流 | 問題拆解、來源分級、檢索式、證據表、實作契約、execution gate、驗證原則 |
| 公開標準入口 | CDISC、FDA、PHUSE、Lex Jansen、SAS、OMOP／OHDSI 等公開入口與引用 |
| 通用 Adapter | dictionary version、grain、keys、joins、coverage、PII、lineage、code status 的抽象契約 |
| TMUCRD 公開 profile | 自 Nguyen 等人（2024）與北醫公開頁面重寫的資料庫背景、資料類別、治理概述與來源快照 |
| 合成範例 | 不使用真實機構 schema、欄位、代碼或資料量的 SAS／SQL／R 規格範例 |
| 測試資料 | 人工撰寫的 prompt、rubric、預期護欄與合成回應 |

### 3.2 私有 denylist

以下內容不得提交，即使沒有病人層級列資料：

- TMUCRD 內部資料字典文字匯出、原始 PDF、codingbook、codebook 或完整擷取內容。
- 由院內手冊得知、但未見於公開來源的版本專用 guide 內容。
- 真實實體表名、欄位、型別、代碼、值域、主外鍵、跨院 linkage、
  cardinality、涵蓋期間、筆數、availability matrix、ETL 或 PII 分級。
- 由上述資料改寫而仍可反推出院內 schema 的 SQL、mapping table 或測試 fixture。
- 密碼、Token、API key、cookie、私有 URL、個人資料或病人資料。

### 3.3 公開文獻的使用限制

`tmucrd-public-profile.md` 只以自行撰寫的摘要呈現已公開事實，並連結原始論文及
公開網站。不得把論文 PDF、補充資料、整張表格、架構圖或長段文字納入 repository。

每一筆歷史規模或涵蓋期間都必須標示來源年份與「public source snapshot」：
它只能做資料庫概覽，不能代表現行核准版本、可取得欄位或研究可執行 schema。

## 4. 專案架構

```text
clin-data-nav/
├── AGENTS.md
├── README.md
├── LICENSE
├── NOTICE
├── CONTRIBUTING.md
├── SECURITY.md
├── CITATION.cff
├── pyproject.toml
├── .gitignore
├── .github/
│   ├── pull_request_template.md
│   └── workflows/
│       └── validate.yml
├── docs/
│   ├── architecture.md
│   ├── release.md
│   └── superpowers/
│       ├── specs/
│       └── plans/
├── skills/
│   └── clinical-data-research-navigator/
│       ├── SKILL.md
│       ├── agents/
│       │   └── openai.yaml
│       └── references/
│           ├── retrieval-playbook.md
│           ├── evidence-output-template.md
│           ├── institutional-adapter-contract.md
│           └── tmucrd-public-profile.md
├── examples/
│   ├── teae-to-sas-spec.md
│   ├── omop-phenotype-to-sql-spec.md
│   └── synthetic-institutional-mapping.md
├── evals/
│   ├── cases.yaml
│   ├── rubric.yaml
│   └── README.md
├── scripts/
│   ├── validate_skill.py
│   ├── check_public_boundary.py
│   ├── evaluate_response.py
│   ├── package_skill.py
│   └── install_local.py
└── tests/
    ├── test_skill_structure.py
    ├── test_public_boundary.py
    ├── test_eval_contract.py
    ├── test_packaging.py
    └── fixtures/
```

### 4.1 檔案責任

- `AGENTS.md`：repository 專屬的 Codex 工作協議、允許的命令、公開邊界及完成定義。
- `SKILL.md`：只保留觸發條件、核心工作流、必要護欄與何時讀取各 reference。
- `retrieval-playbook.md`：來源路由、Lex Jansen 檢索語法、證據擷取與 execution gate。
- `institutional-adapter-contract.md`：私有 Adapter 必須提供的版本、schema 與驗證介面；
  不含任何 TMUCRD 實值。
- `tmucrd-public-profile.md`：公開文獻支持的機構案例，明確聲明不是 data dictionary。
- `scripts/`：可重現、離線且不需憑證的驗證、評分、打包與安裝工具。
- `tests/`：測試 scripts 與靜態內容；不依賴 LLM 回應或網路。
- `evals/`：行為案例與 rubric；可對人工提供或 Agent 產生的回應進行離線評分。

## 5. Skill 行為設計

### 5.1 觸發範圍

公開版在下列情境觸發：

- 臨床資料、CDISC、ADaM、SDTM、SAS、SQL、R、EHR、claims、registry、
  OMOP 問題需要來源導航、術語 mapping、證據分級或實作規格。
- 使用者要求搜尋 Lex Jansen、會議論文或監管／標準文件。
- 使用者要求把方法學證據轉成可驗證的資料契約或程式規格。

只有 TMUCRD 字樣本身也可以觸發，但公開版只能使用公開 profile；若需要物理
schema，必須要求核准環境中的版本化 Adapter。

### 5.2 與其他 Skill 的關係

`build-rwe-sap` 改為選用相依：

- 若環境中存在相容的 RWE SAP Skill，完整 SAP、estimand、target trial 或因果分析
  設計可交由它處理，再把已確認的資料需求送回本 Skill。
- 若不存在，本 Skill 仍可獨立完成來源導航、資料契約與實作規格，但不宣稱提供完整
  SAP。

不得把特定平台工具（例如 `rg`）設為唯一方法。Skill 應優先使用環境內建全文搜尋，
`rg` 只是本機建議實作。

### 5.3 程式成熟度

所有程式或規格須標記為下列一級：

1. `conceptual`
2. `dictionary-specified`
3. `parameterized`
4. `executable`
5. `validated`

沒有目前實體 schema、鍵、值域、時間語意與測試結果時，不得標記為
`executable` 或 `validated`。

## 6. Institutional Adapter contract

私有 Adapter 是使用端提供的受管制相依，不進入公開 repository。其最小 manifest
須提供：

```yaml
adapter_schema_version: "1"
institution_id: "<local identifier>"
adapter_version: "<semantic or dated version>"
dictionary_version: "<owner-issued version>"
effective_date: "<YYYY-MM-DD>"
classification: "<local governance label>"
source_owner: "<governing role>"
domains: []
metadata_verification:
  required: true
  method: "<approved live metadata check>"
```

Adapter 還須定義：

- 每個資料域的 grain、鍵、join cardinality 與 coverage。
- 實體欄位、型別、時間精度、code system、value set 與版本。
- PII／敏感資料標示、允許用途與輸出限制。
- dictionary evidence 與 live schema 驗證的差異。
- 應用程式可執行前必須通過的 metadata 及 fixture 檢查。

核心 Skill 只認得 contract，不知道或猜測 Adapter 裡的實值。缺少 Adapter 時，
輸出必須標為 `SPECIFICATION ONLY — NOT EXECUTABLE`。

## 7. 測試與 Evals

### 7.1 CI 必跑測試

`python -m pytest -q` 必須涵蓋：

1. **結構測試**
   - `SKILL.md` frontmatter 含有效 `name` 與 `description`。
   - Skill 名稱、目錄名稱與 UI metadata 一致。
   - 所有 `SKILL.md` reference 連結存在。
   - `SKILL.md` 不超過 500 行。

2. **公開邊界測試**
   - 禁止指定的私有檔名、路徑、院內專用字串及檔案型態。
   - 偵測常見 secret 格式。
   - 阻擋超過門檻的文字型資料檔，除非明列於 allowlist。
   - `tmucrd-public-profile.md` 必須包含來源、snapshot 與非 schema 聲明。

3. **行為契約測試**
   - Lex Jansen 不是正式標準或驗證機構。
   - 沒有資料字典時不得臆造表、欄位、Concept ID 或 executable SQL。
   - 舊 codingbook 不能證明目前 live schema。
   - CDISC／監管、研究特定規則、會議實務與機構 schema 能路由至不同權威。
   - `build-rwe-sap` 不再是強制安裝相依。

4. **打包測試**
   - 安裝包只含 Skill 所需檔案。
   - 相同 commit 產生相同檔案清單與內容雜湊。
   - 安裝包不含 tests、docs、Git metadata 或 private patterns。

### 7.2 行為 Evals

第一版至少包含六類 prompt：

| Case | 必須觀察的行為 |
|---|---|
| TEAE 轉 SAS 規格 | 先找 protocol／SAP 與正式標準；Lex Jansen 僅作實務證據 |
| 無字典的機構 SQL | 阻擋 executable SQL，改交付 placeholder 與 mapping checklist |
| 舊版 codingbook | 標示版本證據，但仍要求 live metadata 驗證 |
| CDISC 變數定義 | 官方標準／受管制術語優先於會議論文 |
| OMOP phenotype | 區分標準 concept、local code 與研究 phenotype |
| TMUCRD 背景介紹 | 使用公開 profile；不輸出 V2.16 schema 或院內查詢 |

CI 不直接呼叫 LLM。`evaluate_response.py` 接收一份外部產生的回應檔，依 rubric 做
可重現的必要字串、禁止字串與章節檢查；語意品質另由人工或 Agent review 判定。

## 8. GitHub Actions 與安全設定

`validate.yml` 只使用唯讀 repository 權限：

```yaml
permissions:
  contents: read
```

在 Ubuntu 的受支援 Python 版本執行：

1. 安裝鎖定的開發相依。
2. 執行 `python -m pytest -q`。
3. 執行 `python scripts/validate_skill.py`。
4. 執行 `python scripts/check_public_boundary.py`。
5. 執行 `python scripts/package_skill.py --check-reproducible`。

CI 不取得 GitHub secrets、不連線 TMUCRD、不下載 codingbook，也不呼叫外部 LLM。

`.gitignore` 至少排除：

```gitignore
private/
local-adapters/
*.pdf
*codingbook*
*codebook*
*dictionary.txt
.env
.env.*
dist/
```

`.gitignore` 只是第二道防線；真正的阻擋由
`check_public_boundary.py` 與 pull request checklist 執行。

## 9. Codex 維護規則

根目錄 `AGENTS.md` 必須明訂：

- 先讀本設計與當前 implementation plan。
- 不得讀取、複製或要求提交本 repository 以外的 TMUCRD 私有 Adapter。
- 修改行為前先新增或更新失敗測試。
- 只用合成 institutional schema 做範例。
- 變更 `SKILL.md` 時同步檢查 `agents/openai.yaml`、Evals 與引用。
- 完成前必跑完整驗證命令並審查 `git diff`。
- 不得自行建立 GitHub repository、push、發布 Release 或變更授權。

此分工讓 `AGENTS.md` 管理「如何維護這個 repository」，讓 `SKILL.md` 管理
「使用者提出臨床資料問題時如何工作」。

## 10. 版本、發布與安裝

- 採 Semantic Versioning；第一個可用標籤為 `v0.1.0`。
- `main` 為受保護的穩定分支；變更經 pull request 與 CI。
- `package_skill.py` 從
  `skills/clinical-data-research-navigator/` 產生乾淨安裝包與 SHA-256 manifest。
- GitHub Release 只附安裝包、manifest 與 release notes。
- `install_local.py` 預設安裝至使用者指定目錄；不得假設某一平台的個人 Skill
  路徑，也不得覆寫既有版本而不提示。
- Codex repository-scoped 測試可直接對來源目錄執行；正式使用時由安裝工具把
  Skill 放入該平台支援的 Skills 位置。

## 11. 文件與授權

- 自行撰寫的程式、Skill、範本及測試使用 Apache-2.0。
- `NOTICE` 明確說明引用的外部標準、論文與網站不受本 repository 授權重新授權。
- `CITATION.cff` 提供本專案引用方式；TMUCRD 背景另引用原始論文。
- `SECURITY.md` 說明若誤提交私有資料，應停止合併、撤下 branch／PR、輪替可能受影響
  的憑證，並依 GitHub 敏感資料清除流程處理。
- `CONTRIBUTING.md` 要求所有 institutional 範例皆為合成資料，且貢獻者聲明具備
  內容授權。

## 12. 驗收標準

公開 Core 第一版只有在下列條件全數成立時才算完成：

- [ ] repository 從全新 Git history 建立，預設分支為 `main`。
- [ ] Git history 中不存在 TMUCRD 內部 codingbook、資料字典匯出或私有 guide。
- [ ] Skill 結構驗證通過。
- [ ] 公開邊界掃描通過。
- [ ] 六類 Evals 的 fixtures、rubric 與回歸測試存在。
- [ ] 所有測試在乾淨環境通過。
- [ ] 打包結果可重現，manifest 雜湊一致。
- [ ] TMUCRD 公開 profile 只引用公開來源，且有 snapshot 與非 schema 聲明。
- [ ] `build-rwe-sap` 為選用相依。
- [ ] `AGENTS.md` 含完整維護命令與禁止事項。
- [ ] 尚未推送 GitHub；由使用者另行核准發布動作。

## 13. 後續階段

1. **Phase 1：公開 Core**

   實作本規格、完成本機 Git commit 與可審查安裝包。
2. **Phase 2：GitHub 發布**

   使用者確認 GitHub 帳號、repository 名稱與可見性後，建立遠端並推送。
3. **Phase 3：私有 TMUCRD Adapter**

   另行設計受管制 repository、權限、版本同步與稽核流程。
4. **Phase 4：Plugin 包裝**

   Core 介面穩定後，再評估是否包裝成可安裝 Plugin。

## 14. 參考資料

- Nguyen, P. A., Hsu, M. H., Chang, T. H., Yang, H. C., Huang, C. W.,
  Liao, C. T., Lu, C. Y., & Hsu, J. C. (2024). Taipei Medical University
  Clinical Research Database: A collaborative hospital EHR database aligned
  with international common data standards. *BMJ Health & Care Informatics,
  31*(1), e100890. https://doi.org/10.1136/bmjhci-2023-100890
- OpenAI. (2026). *Build skills*.
  https://learn.chatgpt.com/docs/build-skills
- OpenAI. (2026). *Custom instructions with AGENTS.md*.
  https://learn.chatgpt.com/docs/agent-configuration/agents-md
- Agent Skills. (2026). *Agent Skills specification*.
  https://agentskills.io/specification
- GitHub. (2026). *Removing sensitive data from a repository*.
  https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
- Open Source Initiative. (2024). *The Open Source Definition*.
  https://opensource.org/osd
