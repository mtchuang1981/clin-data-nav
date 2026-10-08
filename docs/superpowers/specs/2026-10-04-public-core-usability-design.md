# ClinNav 公開核心：證據審閱、缺口行動與使用診斷

日期：2026-10-04

狀態：書面規格與計畫已核准；已依 Native 完成本機實作與驗證，未合併或發布

隔離分支：`codex/public-core-usability`

基線：`a8b9976dbbf62fec250fb7c571f3e714ce0b360f`

## 目的與範圍

使用者已同意五項公開端優化：選用的證據審閱 audit、文件與範例一致性、可行動的驗證缺口、唯讀安裝完整性診斷，以及雙語使用回饋入口。本輪讓研究者更容易辨識「還缺什麼」與「實際檢查了什麼」，不把紀錄完整性當成科學正確性，也不增加日常簡短問答的負擔。

採最小、可分開驗收的擴充：保留 evidence ledger schema `1`、既有 checker 判定與退出碼；另增 audit。安裝診斷放在 repository 工具層，Python 仍不是一般安裝或日常使用的必要條件。驗證缺口沿用既有正式輸出區段，不建立另一套任務系統。

本輪不修改私有 adapter、不讀私有結構或資料、不與 OMOP 1.1 分支混合、不執行真人或模型 campaign、不啟動自動網路查證或排程、不變更版本號、CHANGELOG、已發布 tag 或 Release assets。交付先停在本機隔離分支；merge、push 與發布不包含在本規格中。

### 選擇理由

首選是「相容的 companion audit + 小型選用工具」。直接把 audit 欄位塞進 ledger schema `1` 會破壞封閉欄位驗證與歷史消費端；全自動擷取網頁或 DOI 狀態則會增加網路依賴，仍不能證明來源支持主張。這兩種方案本輪不採用。

### 既有證據

`docs/verification/2026-09-19-v0.8.0-public-evidence-ledger-pilot.md` 記錄 `pilot-failed`：四個來源新鮮度判定及十二個 claim-fit 判定都需要 companion audit，另有一筆過度支持判斷。四例 packaged/repository checker parity 通過，並不代表 frozen-exit gate 或語意審閱通過。本輪新增能力，不回頭更改該結果或門檻。

現有 `evidence-ledger.md` 明定 checker 離線運作，exit `0` 不代表來源真實、科學有效或部署就緒。現有 installer 已有串流雜湊、套件限額、路徑與覆寫保護；診斷應沿用這些防線，不另寫較弱的驗證器。

## 一、選用的 evidence audit

### 元件與使用方式

- `skills/clin-nav/references/evidence-audit.md`：封閉契約、欄位意義、判定與限制。
- `skills/clin-nav/references/evidence-audit-example.json`：純合成的完整例子，不是已查閱的真實來源紀錄。
- `skills/clin-nav/scripts/evidence_audit.py`：純函式驗證、摘要與狀態計算。
- `skills/clin-nav/scripts/bounded_json.py`：audit 與安裝診斷共用的限額／嚴格 JSON reader，依既有 repository wrapper import 模式取得。
- `skills/clin-nav/scripts/check_evidence_audit.py`：與現有 ledger CLI 相同的安全、外部路徑與輸出模式。
- `scripts/check_evidence_audit.py`：沿用 repository wrapper 模式，不複製驗證邏輯。

指令介面：

```text
python scripts/check_evidence_audit.py --ledger <external-ledger.json> --audit <external-audit.json> --as-of YYYY-MM-DD
```

CLI 僅讀取使用者明確指定的兩份 repository／安裝 Skill 以外的 JSON，不開啟來源 URL、不呼叫 MCP、不寫回或自動修復輸入。先呼叫現有 ledger validator 與 review-state evaluator，再驗證 companion；existing ledger CLI 的行為不變。

### 綁定與封閉欄位

Audit 頂層只允許 `schema_version`、`ledger_id`、`ledger_sha256`、`checked_on`、`sources`、`claims`。`schema_version` 為字串 `1`，代表 audit 自己的版本，不改 ledger 版本。`ledger_id` 必須相同。

`ledger_sha256` 是已通過結構驗證的 ledger JSON，以 UTF-8、`ensure_ascii=False`、`sort_keys=True`、`separators=(",", ":")` 序列化後的 SHA-256。保留 array 順序與文字內容，不做 Unicode 或語意正規化。空白、物件鍵順序與檔案換行不影響綁定；文字、引用與陣列順序變動會使綁定失敗。CLI 在執行 ledger parser 前以 bounded JSON loader 拒絕重複鍵、NaN、Infinity、無效 UTF-8 與過深巢狀；不改既有 CLI 的 parser。

每個 ledger source／claim 均恰有一筆 audit row，不能有遺漏、重複或額外 ID。ID 沿用 ledger 格式，不用人工填寫 `present_in_ledger` 取代集合比對。

Source row 的精確欄位如下：

| 欄位 | 規則 |
| --- | --- |
| `source_id` | 對應 ledger source |
| `retrieval_url` | 已嘗試的公開 HTTPS URL，未知為 `null`；不得含帳密、token 或私有位址 |
| `access_status` | `opened`、`abstract-only`、`unavailable`、`conflicted`、`not-attempted` |
| `authority_role` | `governing`、`official-product`、`peer-reviewed-method`、`implementation`、`discovery-only` |
| `use_scope` | `current`、`historical`、`development`、`not-assessed`；依 ledger applicability 與主張範圍人工判斷，不由檔案年齡推定 |
| `version_status` | `current`、`superseded`、`in-development`、`unknown` |
| `status_basis_url` | 公開 HTTPS 狀態依據，未查得為 `null` |
| `newer_source_search` | 精確包含 `performed_on`、`entry_points`、`result`、`notes` |
| `notes` | 非空說明，包含適用範圍、衝突、已知更正／撤稿及如何處理，或未完成原因，不放來源全文 |

`newer_source_search.result` 只允許 `no-newer-found`、`newer-found`、`unavailable`、`not-performed`、`not-applicable`。`performed_on` 是 ISO 日期或 `null`，`entry_points` 是不重複的公開 HTTPS URL 陣列。

- `no-newer-found`、`newer-found`、`unavailable` 表示已嘗試查找，必須有日期、至少一個 entry point 與非空 notes。
- `not-performed`、`not-applicable` 的日期為 `null`、entry points 為空；notes 必須說明原因。
- `current` scope 不接受 `not-applicable`；其他 scope 的 `not-applicable` 只代表較新版本不是該歷史／開發範圍的判準，仍須查閱實際來源、版本適用性與必要的更正狀態。

Claim row 的精確欄位如下：

| 欄位 | 規則 |
| --- | --- |
| `claim_id` | 對應 ledger claim |
| `source_checks` | 每個該 claim 的 `source_ids` 恰有一筆；空 source_ids 對應空陣列 |
| `authority_fit` | `appropriate`、`insufficient`、`conflicted`、`not-assessed`、`not-applicable` |
| `support_fit` | `appropriate`、`overstated`、`understated`、`not-assessed`、`not-applicable` |
| `notes` | 非空審閱說明，不放整段模型回答或來源全文 |

每筆 `source_checks` 精確包含 `source_id`、`evidence_location`、`locator_status`。位置為非空文字或 `null`；`locator_status` 為 `verified`、`not-verified`、`unavailable`。`verified` 必須有位置且對應來源實際開啟，不能用一個全域 locator boolean 掩蓋多來源漏查。人工在不同引用位置間確認 ledger 與 audit 相容；checker 不自行讀懂段落。

`not-applicable` 的 authority/support fit 只允許在無來源且 `claim_type=request-provided` 的 row 使用，notes 說明這是請求提供的事實，不是查證過的外部事實。凡聲稱已評估支持度的其他 claim，fit 欄位不得用此值。此情況不能解除原 ledger 的 not-assessed review item，union 判定仍回 `3`。

### 日期、限額與一致性

- `prepared_on <= checked_on <= --as-of`；所有實際審閱與查找日期不得晚於 `checked_on`。未來 review policy due date 仍可保留；到期依原 ledger checker 回報。
- 每個輸入至多 262,144 bytes，最多 100 sources、100 claims；每個 claim 至多 100 source checks，每個來源至多 20 search entry points。JSON 深度至多 12，超限在語意處理前拒絕。
- ID 至多 80 字元、URL 至多 2,048 字元、位置／notes 至多 4,000 字元。限額驗證不得截斷輸入後繼續接受。
- URL 僅作紀錄；拒絕 credentials、query、fragment、localhost、IP literals 與單節點 host；不能保證普通網域屬公開系統，因此使用者仍須遵守公開資料界線。需要 signed URL 時只記無機密的公開入口，不保存可登入連結。
- 不接受附加欄位、錯誤型別、布林值冒充整數或空白必要文字。所有欄位在各狀態仍必須存在，未知用契約允許的 `null` 或閉集合值，不猜值。
- 開啟狀態與 ledger review-status 依下表驗證，不把未嘗試存取當成 unavailable。

| Audit access | 允許的 ledger review-status | 是否允許 verified locator |
| --- | --- | --- |
| `opened` | `reviewed` | 是，且必須提供位置 |
| `abstract-only` | `not-reviewed` | 否，abstract 不替代主張所需的實際來源 |
| `unavailable` | `unavailable` | 否 |
| `not-attempted` | `not-reviewed` | 否 |
| `conflicted` | `reviewed` | 是，來源已開啟但判斷仍有衝突；整體仍回 needs-review |

更正／撤稿採人工 notes 與 claim-fit 審閱，不建立新的 integrity 子狀態機。審閱者須確認使用修正版是否足以支持該主張，並區分「引用撤稿內容當實證」與「描述撤稿事件」；checker 不解析 notes、查更正資料庫或宣稱這部分已被獨立驗證。無法完成時誠實填 authority/support 的 not-assessed 或 conflicted 等適用值，保留 needs-review。

### 判定

| Exit | 狀態 | 意義 |
| --- | --- | --- |
| `2` | `invalid-input` | 格式、限額、外部路徑、日期、ID／雜湊綁定或相互矛盾的紀錄不合法 |
| `3` | `needs-review` | 輸入合法，但原 ledger 有 review item，或 audit 有未查閱、漏驗位置、未知／衝突、支持程度需修正等項目 |
| `0` | `recorded-checks-complete` | 本次適用的檢查均記錄完成；不代表來源或人工判斷一定正確 |

Audit 判定優先 invalid，之後 union 原 ledger 與 audit 的 review items。overstated／understated 是應保留的有效審閱結果，回 `3`，不是為求通過而拒收這筆證據。

需要 review 的來源條件：非 opened、scope not-assessed、version unknown、缺少 status basis，以及任何 scope 的 newer search unavailable／not-performed。current scope 的 superseded/in-development 或發現 newer source 都需要 review。historical／development scope 的 superseded/in-development／newer-found 不單獨觸發失敗，須與 ledger 明示範圍一致；checker 只記錄此自陳，不能證明該範圍真的合理。只有契約允許且有理由的 not-applicable 才可免除較新來源搜尋，不豁免實際來源或引用審閱。

需要 review 的 claim 條件：未完成 locator、authority 不足／衝突／未評估、support 過度／不足／未評估。`appropriate` 指與 ledger 記錄的支持程度相符，不等於 claim 成立；原 ledger 的 unsupported/not-assessed 仍會留下 review item。

stdout/stderr 僅顯示固定狀態、計數、已驗證格式的 record IDs 與固定 reason codes。不回顯 URL、title、claim、notes、未知欄位、輸入路徑或 exception；兩次相同輸入與 as-of 產生相同摘要。

### 整合界線

在 `SKILL.md`、輸出 template 與 ledger reference 加上選用 audit 路由：使用者要求來源新鮮度／引用審閱紀錄時才建立；不要求每次回答產生 audit。仍需使用已授權研究工具實際查閱後填寫；checker 自己不連網。

審閱語意不能靠 regex 或 audit 自陳證明。測試只檢查契約、跨紀錄一致性及判定；本輪不做新的成效研究，也不重新解讀失敗 pilot。歷史外部 companion audit 不做隱式遷移或自動補值。

## 二、文件與三個正式範例

修正 `docs/installation.md` 與 `.zh-TW.md` 的 v0.8.0 段落資產名稱，保持兩種語言的版本／命令相符，不把 main 未發布內容稱為 v0.8.0 資產。修正 `docs/architecture.md`：release workflow 從 main dispatch，執行程式的 job checkout `github.sha`；tag 只作驗證與發布識別，不控制 checkout。

更新 README 已連結的三個例子：

- `examples/teae-to-sas-spec.md`
- `examples/omop-phenotype-to-sql-spec.md`
- `examples/synthetic-institutional-mapping.md`

三者使用 `implementation specification`、完整非空共同 header，以及 Governing evidence、Data contract、Code maturity、Validation gaps、Execution gate。原有 evidence table 收進 Governing evidence，不混用 evidence navigation 的章節契約。

保留原成熟度：TEAE／合成機構 mapping 為 dictionary-specified；OMOP phenotype 為 conceptual。前兩者必須在 Assumptions 明示「純合成情境假設已提供核准字典」，不將虛構核准寫入 Confirmed facts。Gate 一律 unmet，保留 `SPECIFICATION ONLY — NOT EXECUTABLE`。SYNTH 識別是情境提供的虛構標記，不宣稱真的查閱文件、執行 fixture 或驗證 institution schema；不新增 SQL／SAS 等形狀的實體 placeholder。

測試以章節、有效深度、成熟度、標記與入口的一致性為準，不把所有敘述鎖成精確字串。安裝文件對目前公開 release 固定驗證；release CI 描述對 workflow 實際 checkout/ref 與 dispatch gate 驗證。

## 三、可行動的 Validation gaps

延續 Implementation 的 `Validation gaps` 與 Research 的 `Bias and validation gaps`，每個未完成項目包含五欄：

| 欄位 | 要求 |
| --- | --- |
| Gap | 依實際狀態區分 unknown、unavailable、not reviewed、已知失敗、待核准或衝突，不混用 |
| Blocks | 阻擋哪項交付、主張或成熟度升級 |
| Next safe action | 下一個安全且已授權的動作；需新授權時先指出，不自動執行 |
| Responsible role | 責任角色，不猜人名；角色未知寫待確認 |
| Completion evidence | 可接受的核准、版本、檢查或審閱證據，不要求私有原始資料或日誌 |

表格後說明「目前仍可完成的工作」。涉及程式成熟度升級時，單一缺口完成後仍須重跑全部相關 execution gates，不能自動升級 executable；metadata-only connector 也不因此取得資料或程式執行權限。Research 的描述性／偏差缺口採該設計適用的審閱條件，不因此強加中繼資料或 fixture 要求。

同步 `SKILL.md`、`references/evidence-output-template.md`、`references/output-depths-and-learning-paths.md`，避免彼此規則不同。Evidence navigation 沿用 Conflicts and unreviewed gaps，必要時提供安全下一步，但不加 Data contract、Code maturity 或固定五欄要求。Quick explanation 不增加必填表頭或表格。

同步檢閱 `agents/openai.yaml`、Eval catalog、evaluator 與 fixtures。只修改確實受新正式缺口規則影響的斷言或樣例；不重寫既有 benchmark fixture、放寬安全 gate 或改寫歷史結果。

## 四、選用的唯讀安裝完整性診斷

新增 repository 工具 `scripts/verify_installation.py` 與雙語文件／測試。介面：

```text
python scripts/verify_installation.py --skill-dir <selected-directory> --manifest <trusted-external-manifest.json> --manifest-sha256 <published-sha256> --comparison bytes
```

`--comparison` 接受 `bytes`（預設）或 `canonical-text`。工具只比對使用者指定的一個安裝目錄，不掃描其他 agents 目錄、不連網、不安裝、不覆寫、不 restart host。Manifest 與其 expected SHA-256 必須來自使用者信任的公開發布依據；同一可修改目錄中的自製 receipt 不視為信任根。

Manifest 先以 bounded stream 讀取並核對原始 bytes SHA-256，再透過共用 strict JSON reader 拒絕 duplicate keys、NaN／Infinity 與深度超過 12，最後做封閉契約驗證；expected hash 必填且為小寫 64 位 hex。不改既有 installer 的 JSON parser 行為。Manifest 必須位於 selected skill-dir 與 source repository 以外，輸入根與 manifest 不可是 symlink／junction／reparse。這防止讀取可替換 receipt，但不能證明使用者提供的 hash 真的是官方 hash。

保留 installer 的 manifest 形狀：頂層恰有 name、version、archive、archive_sha256、files；name 必須 clin-nav，version 為既有 `X.Y.Z` 格式，archive 名須與 version 相符。可驗證舊版可信 manifest，不硬綁目前 PACKAGE_VERSION；不修改 installer 既有版本限制與 API。

沿用狹窄共用 helper 的 record/path/hash 安全邏輯，必要的抽取保留原 wrapper 與測試。不可直接信任只有 record 型別檢查卻尚未通過 ZIP path preflight 的 manifest path。開檔前檢查所有路徑：拒絕絕對／drive-relative／`..`、backslash、重複分隔、ADS、尾端點或空白、NFC/casefold collision、檔案與子路徑衝突，以及 Windows 保留裝置名。

限額沿用 installer：manifest 1 MiB、256 records、單檔 10 MiB、總檔案 40 MiB；禁止 bool 冒充 size。目錄遍歷至多 4,096 entries、深度 32，不跨 symlink／junction／reparse，超限回 invalid。額外檔案僅計數，不讀內容；`__pycache__` 與 `.pyc`／`.pyo` 是固定排除項，但仍遍歷其 entries 以核對 link/reparse 安全與計數，不讀 bytecode 內容；先做安全檢查再排除。不用使用者自訂 glob 掩蓋差異。空目錄不屬於套件 manifest，不影響檔案集合比對。

對 manifest 預期的每個普通檔案串流雜湊與核對 size；先 lstat、開啟後 fstat、讀完後再次比對 identity／size／mtime，發現變動回 invalid。這是 best-effort concurrent-change 偵測，不宣稱防住具有本機修改權限的惡意競態或原子檔案系統快照。

bytes 模式比較原始檔案 bytes。canonical-text 模式僅使用與 package builder 相同的規則：無 NUL 且有效 UTF-8 的檔案將 CRLF／CR 轉 LF，其餘 bytes 不變，沒有 trim、Unicode 或語意正規化；依 canonical size/hash 比對。共用 bounded bytes helper，不讓 packager 全檔讀取方式繞過診斷限額。

| Exit | 結果 |
| --- | --- |
| `0` | `manifest-files-byte-identical` 或 `manifest-files-canonical-content-matches`，依明確選用的 comparison 模式區分 |
| `3` | `content-differs`：missing、extra、size 或 hash 差異 |
| `2` | `invalid-input`：未信任 manifest、非法路徑、超限、讀取失敗或 concurrent change |

固定輸出 comparison、manifest version、計數（包含 ignored-file count）、結果與 `loaded_version: not-verified`，不回顯檔案內容或本機路徑。canonical 模式不能標示 bytes 相同；兩種成功結果都只代表 manifest 範圍，不證明 bytecode 或執行環境完整性。工具不接收 ZIP，所以 archive_sha256 只檢查形狀，不宣稱已核對 archive。若 host 未重新載入、仍有同名 Skill 或只快取舊指令，需由 host 層另行確認；本工具無法證明。

README／installation docs 清楚區分「可選完整性診斷」與正常 Skill 安裝。不要求所有使用者為此安裝 Python，也不把 Python 診斷誤當 host 通用自測功能。

## 五、雙語低負擔使用回饋

保留英文 `.github/ISSUE_TEMPLATE/usability-feedback.yml`，新增 `usability-feedback.zh-TW.yml`；README 中英文各加可直接開啟對應 Issue Form 的入口，不連到 YAML 原始碼。兩版欄位 ID、順序、選項語義、community-reported 標籤一致，語言可不同；使用版本、安裝方法、agent、OS、任務類別與完成結果沿用既有欄位。

`problem_reproduction` 改為選填。有問題時填至多約 1,000 字的公開／合成工作流程摘要；「無問題完成」可留白，不強迫 N/A 或虛構問題。completion outcome 不預選；不新增 raw-log、response、prompt、screenshot 或 upload 欄位。唯一 textarea 設 `render: text`，敏感資訊確認 checkbox option 設 `required: true`。

兩版都提示不要貼原始提示、模型回答、日誌、附件、病人資料、機構 schema、憑證或 API keys。GitHub 官方 [issue form schema](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-githubs-form-schema) 沒有 textarea max_length 或條件式 required；1,000 字是指示，不是可強制的 schema 屬性。render 可減少附件／Markdown 展開，不能保證攔下敏感內容。

所有回饋是未驗證的 community self-report，不能混入正式成效彙總、當作具代表性的效果估計或臨床有效性證據。本輪不更動 benchmark-result 表單、不蒐集使用者答案或建立新的研究流程。

## 失敗情境與二階影響

- 把 audit exit 0、installed-content match 或單一 gap 完成當成 readiness：以不同狀態名稱、固定限制訊息與負向測試防止。
- 把歷史／開發文件一律判為過期，或以 scope 宣告掩蓋未審閱：範圍感知判定與人工責任並存，不假裝離線 validator 懂語意。
- Manifest/path bypass、讀取目錄外機密或額外檔內容：驗證所有 paths 後才開檔，拒絕 links，bounded traversal，stdout 不洩漏。
- 新增一套重複規格或安全 helper，日後兩邊漂移：正式 gap 規則與 audit 規格各集中於單一 reference，其他文件僅必要路由／摘要；小範圍共享 helper 與相容測試。
- 改用新的 audit 後錯稱 v0.8.0 pilot 通過：歷史紀錄不改，新的工具驗證另寫日期與 aggregate-only 紀錄。
- 較友善的回饋入口變成私有資料入口：最低必要欄位、雙語警語、確認項；不能承諾 UI 完全防洩漏，不增加自動 log ingestion。

## 驗收與交付

每項先新增會失敗的合成契約／行為測試再實作。優先沿用 tests/test_evidence_ledger.py、test_install_local.py、test_skill_contract.py、test_project_metadata.py 的慣例；新增專用 audit／installation test modules，避免讓既有大型 metadata 測試繼續膨脹。

最低測試矩陣包含：

- 舊 ledger API／退出碼／fixtures 不變；new audit 的強綁定、缺失／額外／重複 ID、多來源 locators、日期與限額、未知欄位、duplicate JSON keys、未評估／過度支持／衝突、scope-aware version 狀態、內容不回顯及離線行為。
- 診斷可信新／舊 manifest、兩種 comparison、missing/extra/tamper、二進位檔、換行差異、symlink/junction/reparse、portable collisions、非法 device paths、超限、streaming、讀取競態、機密 sentinel 不外洩與零寫入。
- 三範例正式契約、五欄 gaps、quick 無額外必填規則、metadata-only 不升級；文件版本/ref 一致性。
- 雙語表單 ID／選項語義 parity、可無問題完成、optional textarea、required checkbox、no defaults／upload 欄位、README 入口。

完成公開端修改後執行：

```text
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
python scripts/render_eval_summary.py --check
python scripts/render_effectiveness_report.py --summary evals/effectiveness/examples/synthetic-summary.json --english evals/effectiveness/examples/synthetic-report.md --traditional-chinese evals/effectiveness/examples/synthetic-report.zh-TW.md --check
python scripts/render_simulation_benchmark.py --summary evals/benchmark/examples/synthetic-summary.json --english evals/benchmark/examples/synthetic-report.md --traditional-chinese evals/benchmark/examples/synthetic-report.zh-TW.md --check
git diff --check
```

另外在 Windows／Ubuntu 的既有 CI 範圍驗證新 CLI 與 canonical package parity；本機檢查不冒充遠端 CI。若新工具導致套件位元組改變，這只是未發布的開發候選，不覆寫或重新命名已發布的 v0.8.0 資產。最後檢閱 diff，確認沒有 raw response、audit 實例、來源副本、私有資料或實體機構 schema 入 Git。

實作計畫依序交付文件／範例／回饋、audit、gap 與整合、安裝診斷，再做全套驗證與 review。彼此可平行的工作採小量 subagent，完成即結束；不要為每一個測試建立持久化智慧體。

這份規格不聲稱五項已實作。書面規格審閱後才建立詳細 implementation plan 與選擇執行方式；這是本機開發準備，不是發布核准。

## 實作前基線紀錄與剩餘風險

規格階段僅新增本文件，沒有修改 Skill 或 Python 行為。針對 installer、ledger、Skill contract 的基線為 104 passed；validate-skill、public-boundary 與 reproducible-package 三項獨立 gate 通過。

預設 pytest 暫存目錄因 Windows ACL 無法使用；改用全新的專用路徑，不修改 ACL。第一次完整執行使用另一個 Git checkout 下的暫存目錄，結果為 1,367 passed、5 skipped、2 failed。兩項失敗都是 public-boundary 的 Git metadata failure 測試。

根因已確認：測試建立的空 `.git` 不被 Git 當作有效 repository，但 `git rev-parse --is-inside-work-tree` 會往上找到暫存目錄的有效祖先 repository；現有 checker 未核對實際 Git top-level 就接受成功。把相同兩項測試的暫存路徑移到所有 repository 以外後，2/2 通過。

最後以 repository 外的全新專用 basetemp 重跑完整基線：1,369 passed、5 skipped、exit `0`；三項獨立 gate 與 staged diff-check 也全部 exit `0`。略過項目為目前 Windows 檔案系統的 symlink／reparse 建立能力與 POSIX dir-fd cleanup 契約；沒有執行遠端 Windows／Ubuntu CI。本次使用既有本機 Python 3.13，不宣稱已重新驗證官方 Python 3.11.9。

一般 repo 外基線通過不能證明上述「無效 nested `.git` + 有效祖先」變體已修復。此 root-discovery 邊界問題另列待辦；不在五項功能中順手改 public-boundary 行為或弱化測試。本輪測試使用 repository 外專用 basetemp，並保留該風險，不將環境差異當成全面安全保證。
