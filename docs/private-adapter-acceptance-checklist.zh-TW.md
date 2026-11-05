# 私有 Adapter 驗收交接清單

日期：2026-11-05。文件狀態：公開交接清單；尚未執行私有端驗收。

本清單供機構負責人、實作人員及驗收人員使用，將既有公開契約整理為證據與停止條件。
它不新增契約要求，也不證明任何私有部署已符合契約。若本清單與原契約不一致，
以原契約與相符版本的驗證器為準，先記錄差異，再修正文檔。

主要依據：

- [機構 Adapter 契約](../skills/clin-nav/references/institutional-adapter-contract.md)：版本、權限、編譯管線及程式成熟度。
- [OMOP metadata connector 契約](../skills/clin-nav/references/omop-metadata-connector.md)：唯讀邊界、1.2 DQD 政策及輸出限制。
- [OMOP 1.2 核准設計](superpowers/specs/2026-10-11-omop-v12-dqd-expiration-design.md)：獨立證據期限及私有端責任。

## 使用方式與保管

將空白清單複製到機構核准的環境，再填寫負責人、授權紀錄、證據位置與實際判定。
填寫後的副本、私有回應與詳細稽核資料全部留在該環境；不要填回這份公開檔案。

公開 repo 與其 CI 不讀取私有 Adapter、字典、實體 schema、原始回應、憑證、病人資料
或機構內部文件。不要因工具回傳檔案路徑，就自動開啟完整程式、報告或診斷資料。
回傳給模型的彙總也須先經機構揭露規則檢查；彙總人數不代表一定可以公開。

本清單沒有授予任何存取或執行權限。以下私有端操作須在另行授權的環境執行。

## 一、確認範圍與責任

- [ ] 機構負責人已核准本輪用途、目標環境、Adapter 版本與驗收負責人。
- [ ] 本輪明確選擇 OMOP 唯讀路徑、選用編譯管線，或兩者；不把選用管線設為 OMOP 驗收的前提。
- [ ] 已分開記錄唯讀 metadata 存取、無期限 DQD 政策同意、fixture 執行及真實資料執行的權限；缺一項時不推定其他項目已獲准。
- [ ] 已決定證據保管、保留與揭露方式；機構版紀錄與原始產物不進入公開 repo。

各版本須分開記錄，不以其中一個版本推定其他版本：

| 項目 | 本清單引用的公開契約 |
| --- | --- |
| OMOP connector wire contract | 明確選用 `1.2`；預設仍是 `1.0` |
| 通用機構契約 | revision `1.2` |
| Adapter manifest schema | `"1"` |
| 選用 compiler pipeline capability | version `"1"` |
| Adapter、字典、spec format、compiler、套件 | 各自的核准版本；不能互相替代 |

## 二、OMOP 1.2 公開契約檢查

第二、三節僅適用於本輪明確選用 OMOP 1.2 的情況。其他 live metadata 驗證方式仍依
機構契約辦理，不因此被要求啟用這個選用 connector。

### 能力與授權閘門

- [ ] 本輪已有明確的唯讀 metadata 存取授權；僅提到機構、OMOP 或工具名稱不算授權。
- [ ] 先取得明確選用 `1.2` 的 `get_capabilities`，確認唯讀、無資料列存取、無 SQL 執行及無原始 schema 匯出。
- [ ] 回應符合既有封閉欄位、型別、大小上限、固定 allowlist 與公開 catalog 規則。
- [ ] 能力不安全、不完整、拒絕、格式錯誤或不支援版本時立即停止；不呼叫 inspection、不自動降版或重試。
- [ ] `max_snapshot_age_seconds` 仍是有限期限；不因 DQD 無期限而放寬 metadata 時效。
- [ ] `max_dqd_evidence_age_seconds` 為契約允許的正整數或 `null`。`null` 須另有明確同意；缺少同意時在 inspection 前停止。有限期限不能用同意旗標覆寫。

### 取得與核對本輪摘要

- [ ] 通過能力與授權閘門後，才以固定的六個公開欄位呼叫 `inspect_omop_schema`。
- [ ] 不在要求中加入查詢、使用者篩選、DSN、憑證、資料庫名或私有物件名稱；不替換固定公開 catalog。
- [ ] 使用新產生、完整且已遮蔽的 `1.2` 摘要；不把舊 `1.1` 回應改寫成 `1.2`。
- [ ] capabilities 與已雜湊摘要的 DQD 期限政策一致；`summary_sha256`、公開 catalog 與確切 FK 需求集合雜湊符合契約。
- [ ] metadata 觀察時間仍有效，時間不在未來，且 `checked_at` 不晚於 `observed_at`。
- [ ] FK 證據涵蓋完整確切集合、失敗數為零，並具強綁定；僅有相同表數或檢查總數不算完整集合證據。
- [ ] 以完整 checker 驗證語意，不只看 JSON Schema。Schema 可能接受 `1.0`，Python 契約驗證器會拒絕浮點數。

私有端操作者可在另行授權的環境使用相符版本的離線 checker；以下僅示範無期限政策的呼叫格式：

尖括號為佔位符，須替換為該環境已核准的實際路徑與檢查時間。

```text
python <approved-skill-directory>/scripts/check_omop_metadata.py --capabilities <external-capabilities.json> --input <external-inspection.json> --as-of <current-RFC-3339-timestamp> --contract-version 1.2 --allow-nonexpiring-dqd
```

實際輸入保留在機構核准的位置，且位於 repo 與安裝 Skill 目錄外。這個 checker 不探索、
安裝或聯絡 connector。公開合成測試見 [1.2 契約測試](../tests/test_omop_metadata_v12.py)
與 [CLI／解壓安裝測試](../tests/test_omop_metadata_v12_cli.py)；這些測試不能代替私有端驗收。

### 分開記錄判定

| 觀察結果 | 驗收處理 |
| --- | --- |
| 結構 `compatible` 或 `compatible-with-deviations` | 記錄原判定與仍存在的偏差；不推定研究適用性或執行權限。 |
| 結構 `incompatible`，即使 DQD 為 `accepted-attestation` | 保留結構不相容與退出碼 3；限制碼或 DQD 證據不能改成通過。 |
| metadata `stale` | 停止本輪使用；無期限 DQD 不能補救過期 metadata。 |
| DQD 為 `weak-binding`、`stale`、`incomplete-coverage`、`failed-checks` 或 `unavailable` | 不記為已接受 DQD 證據，缺口交回機構負責人處理。 |
| 不支援版本、缺少證據或操作不可用 | 記錄受控狀態與缺口；不降版、補造或自動重試。 |
| `invalid-response`，或 failed／partial scan 導致的 `unavailable` | 只依契約回報受控狀態及允許的代碼；不回傳回應衍生的數量、時間、雜湊、缺口清單或原始錯誤。 |

`accepted-attestation` 僅表示宣告滿足公開契約的綁定與涵蓋條件，不能獨立證明私有端
雜湊生成、不可變儲存或檢查引擎正確；這些仍須完成下一節的機構端稽核。

## 三、由機構負責人查核快照與證據

下列證據須在機構端獨立查核。公開 checker 通過，不代表本節完成。

- [ ] 每次 inspection 都能確認「本次實際檢查的一致快照」，再與原 DQD 證據比對。
- [ ] 強綁定來自該快照的內容 SHA-256，或受治理且不可重用的不可變快照識別碼雜湊。
- [ ] 不以檔案大小、mtime、名稱或新摘要中的舊 digest 代替當前快照身分查核。
- [ ] 無法確認當前身分時，回傳 `dqd_foreign_key_evidence: null`，不沿用未確認的舊證據。
- [ ] 以下任一變更發生時，重新計算 DQD：資料／相關 schema、ETL 產生的快照、公開 catalog／FK 集合，以及會使證據失效的私有檢查邏輯／環境變更。
- [ ] 保留原始 `checked_at`；不更新時間戳來取得通過，也不把「無時間期限」解讀為可套用至未來所有快照。
- [ ] 綁定來源、逐項 FK 檢查結果與失效處理均有機構端稽核證據，且未輸出原始內容至公開 repo 或模型。

## 四、選用編譯管線的追加驗收

僅在本輪範圍包含管線時適用。沒有宣告時維持原有邏輯契約流程；不因此判定 OMOP 路徑失敗。

- [ ] 機構負責人已核准 Adapter、字典、spec format、操作映射、適用 scope 與各項操作權限。
- [ ] capability 符合既有 [純宣告驗證器](../skills/clin-nav/scripts/compiler_pipeline.py)。只傳入 capability 物件，不把完整私有 manifest 交給此 helper。
- [ ] 空的錯誤 tuple 只表示宣告格式符合要求；機構負責人另確認版本意義、實際工具映射及輸入／輸出相容性。
- [ ] 不把 compiler capability 加進 OMOP capabilities，也不以 metadata 唯讀授權推定可以編譯或執行 fixture。
- [ ] `resolve_concept` 的每個代碼均有核准字典／映射來源與選取理由；待確認概念交由人工審查，不從模型記憶補代碼。
- [ ] `validate_spec` 已回報完整錯誤清單或綁定確切規格 digest 的成功結果；仍有錯誤、未解映射或必要參數缺口時不編譯。
- [ ] `compile_spec` 只編譯已接受的規格；manifest 綁定規格 digest、程式 digest 及 compiler 版本。完整程式與審查文件留在核准位置，不自動讀入模型，也不手改生成程式補缺口。
- [ ] `run_fixture_test` 已另獲執行授權，使用核准 fixture 與目標環境，測試的程式 digest 等於編譯產物 digest。
- [ ] fixture 涵蓋[既有情境清單](../skills/clin-nav/references/institutional-adapter-contract.md#fixture-checks)，包含納入／排除、鍵值缺漏／重複、join 倍增、時間與代碼邊界、空輸入及預期彙總／揭露規則。
- [ ] fixture 核對預期結果，不只看退出碼；未執行、略過、失敗、缺少綁定或 digest 不同都不算通過。
- [ ] 規格、程式、映射／字典、compiler、相關 metadata 快照或環境改變後，重新評估並重跑受影響步驟，不沿用不相干的通過結果。
- [ ] 去識別化 fixture 已另獲機構核准；公開 repo 的 fixture 仍只使用完全合成資料。

規格、編譯產物與 fixture 的綁定規則，以[既有操作契約](../skills/clin-nav/references/institutional-adapter-contract.md#operations-and-artifact-binding)
及[公開合成測試](../tests/test_compiler_pipeline.py)為準。不要把操作清單的排列次序當成已執行紀錄。

## 五、交付判定與失效後處理

- [ ] 分開記錄公開契約檢查、結構判定、DQD 證據判定、機構端稽核、fixture 結果及案件負責人的決定，不合併成一個「全部通過」。
- [ ] 依既有[程式成熟度閘門](../skills/clin-nav/references/institutional-adapter-contract.md#code-maturity)判定；不由 capability、metadata 或 DQD 通過自動升為 `executable`／`validated`。
- [ ] 判定 `executable` 前，確認已版本化 Adapter、核定研究參數、當前 live metadata 與目標環境 fixture 均符合閘門；`validated` 還須結果審查及治理／揭露條件通過。
- [ ] 缺少升級條件時，列出每一個缺口並保留 `SPECIFICATION ONLY — NOT EXECUTABLE`。不因規格看似完整，就推定必要參數、映射與執行條件齊備。
- [ ] fixture 執行與真實資料執行分開核准；`executable` 不是資料庫存取、倫理核准、揭露許可或臨床適用性的證明。
- [ ] 發現資料或環境漂移、授權撤回、證據失效或 digest 不一致時，停止受影響步驟並交回負責人；修正後依契約重驗，不覆寫原始失敗紀錄。

機構端交接紀錄至少包含：本輪範圍、負責角色、各項授權紀錄、相符版本、證據位置、
各項原判定、缺口、失效條件及負責人的決定。填寫於核准的機構端副本，不能據此要求
將私有文件、完整 manifest、程式或真實資料提供給本公開 repo。

如需對外回報，先完成機構揭露審查，只使用契約允許的受控狀態、代碼及獲准的彙總欄位。
失敗結果仍遵守更嚴格的失敗輸出限制。本清單全部勾選也不代替機構核准、研究有效性或臨床驗證。
