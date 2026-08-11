# 初學者詞彙表

[English](glossary.md)

這份詞彙表用來快速入門，不能取代現行標準、指引、試驗計畫書、統計分析計畫
（SAP）或經核准的機構詮釋資料。模型說明資訊可以如何呈現；實際導入時，仍要
審查來源、決定對應方式並完成驗證。

<a id="clinical-research"></a>
## 臨床研究（clinical research）

[臨床研究](https://www.nih.gov/health-information/nih-clinical-research-trials-you/basics)
是涉及人的醫學研究。臨床試驗只是臨床研究的其中一類；觀察性研究與流行病學
研究也可能屬於臨床研究。要採用哪一種設計與證據要求，取決於研究問題及預定
用途。

<a id="cdisc"></a>
## CDISC

[Clinical Data Interchange Standards Consortium
（CDISC）](https://www.cdisc.org/standards)制定臨床與非臨床研究資料的一系列
標準。CDISC 是組織及標準體系，不是單一資料集格式。執行工作前，要確認適用
的標準、實作指南、受控詞彙及版本。

<a id="sdtm"></a>
## SDTM

[Study Data Tabulation Model
（SDTM）](https://www.cdisc.org/standards/foundational/sdtm)會在保留原始意義的
前提下，統一整理及呈現所收集或接收的研究資料。SDTM 會整理提交主管機關的研究資料，
也可支援審查、交換與再利用。它不是原始資料收集表單，也不會判定
來源值是否正確。

<a id="adam"></a>
## ADaM

[Analysis Data Model
（ADaM）](https://www.cdisc.org/standards/foundational/adam)定義分析資料集與
詮釋資料的標準。ADaM 支援分析，讓分析資料的內容及目的更明確，並支援從
分析結果追溯至分析資料與 SDTM。它不能取代試驗計畫書、SAP 或研究特定的
衍生規則。

<a id="omop-cdm"></a>
## OMOP CDM

[Observational Medical Outcomes Partnership Common Data Model（OMOP
CDM）](https://ohdsi.github.io/CommonDataModel/)是由開放社群維護的觀察性健康
資料結構與內容標準。OMOP CDM 將觀察性資料標準化，讓共用分析方法可套用到
符合規範的資料來源。各機構仍須自行設計並驗證擷取、轉換與載入流程、詞彙
對應，以及資料是否適合回答研究問題。

SDTM、ADaM 與 OMOP CDM 只會標準化資料呈現方式，或支援特定用途。
這些標準都不會讓來源資料自動變成有效資料。準確性、完整性、資料來源、機構內
轉換方式及目的適用性，都要另外提出證據並檢查。

<a id="rwd"></a>
## RWD

[真實世界資料（real-world data，
RWD）](https://www.fda.gov/science-research/science-and-research-special-topics/real-world-evidence)
是從多種來源例行收集、與病人健康狀態及／或醫療服務提供相關的資料，例如
電子健康紀錄、申報資料、登錄資料及數位健康科技資料。「真實世界」說明資料
的產生情境，不代表資料品質已通過驗證，也不代表適合特定研究問題。

<a id="rwe"></a>
## RWE

[真實世界證據（real-world evidence，
RWE）](https://www.fda.gov/science-research/science-and-research-special-topics/real-world-evidence)
是分析 RWD 後，針對醫療產品的使用情形及潛在效益或風險所產生的臨床證據。
RWD 是輸入資料，RWE 是證據結果。只有在研究問題明確、資料適合目的、設計與
分析方法適當，而且限制揭露清楚時，資料分析才可能支持一項 RWE 主張。

<a id="pico"></a>
## PICO

[PICO](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-02)
是整理研究問題的工具，分別代表族群（Population）、介入（Intervention）、
比較（Comparator）與結果（Outcome）。這些欄位能讓比較問題更明確，但不是
完整的研究計畫。觀察性或因果研究通常還要定義 time zero、追蹤期間、資料
來源、預定用途，以及要估計的效果。

<a id="target-trial-emulation"></a>
## 目標試驗模擬（target trial emulation）

[目標試驗模擬](https://www.nice.org.uk/corporate/ecd9/chapter/methods-for-real-world-studies-of-comparative-effects)
是把非隨機研究設計成盡量貼近理想隨機試驗，用來回答比較效果問題。納入條件、
治療策略、分派方式、追蹤期間、結果、因果對比及分析方法必須一起定義。這個
方法有助於辨識時間相關偏差與選擇偏差，但不會自動消除混雜、測量誤差或
遺漏資料問題。

<a id="estimand"></a>
## 估計目標（estimand）

[Estimand](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/e9r1-statistical-principles-clinical-trials-addendum-estimands-and-sensitivity-analysis-clinical)
是研究要估計之治療效果的精確描述。依 ICH E9(R1)，它把研究目的連結到
目標族群、治療條件、結果、介入後事件的處理方式，以及族群層級的彙總方式。
估計方法與分析方法應對準 estimand，但兩者本身不是 estimand。

<a id="phenotype"></a>
## 表現型（phenotype）

在觀察性健康資料研究中，[phenotype 或 cohort
definition](https://ohdsi.github.io/TheBookOfOhdsi/Cohorts.html)描述要辨識的可觀察
臨床狀態，以及用紀錄資料辨識該狀態的操作邏輯。代碼清單可能只是其中一項
輸入；時間、納入、排除、進入與離開條件也可能影響定義。Phenotype 需依
預定研究問題及資料來源審查與驗證。

<a id="authority-level"></a>
## 權威層級（authority level）

權威層級表示某項來源對特定主張有多大的主導力。例如，適用的官方標準可主導
名詞定義；研討會論文通常只能補充實作經驗。這是選擇來源的標示，不保證來源
中的每句話都正確或仍適用。

<a id="data-contract"></a>
## 資料契約（data contract）

在本專案中，[資料契約](../skills/clin-nav/references/evidence-output-template.md#implementation-specification)
是實作必須符合的邏輯約定，包括資料粒度、鍵值、連結、涵蓋範圍、型別、時間
錨點、術語、遺漏值、優先順序、資料沿襲及驗收 fixture。它說明需要哪些條件，
但不會臆造機構的實體資料表或欄位名稱。

<a id="execution-gate"></a>
## 執行閘門（execution gate）

執行閘門是把程式標示為可執行前必須具備的最低證據：核准的 Adapter、現行
詮釋資料、已提供的參數，以及在目標環境通過的 fixture。缺少任何一項時，
工作都應停在邏輯規格。

<a id="code-maturity"></a>
## 程式成熟度（code maturity）

程式成熟度用一個標籤說明實作已驗證到哪個階段：`conceptual`、
`dictionary-specified`、`parameterized`、`executable` 或 `validated`。
不能只因為程式已寫出來就提高成熟度；相關證據與檢查也必須完成。

<a id="fixture"></a>
## 測試案例（fixture）

Fixture 是一小組受控輸入與預期結果，用來測試規則。公開的安全範例可以用
`SYNTH_PERSON_A` 測試年齡邊界，並明列這筆合成紀錄是否應納入。Fixture 是
測試證據，不是真實病人資料。

<a id="adapter"></a>
## Adapter

Adapter 是經核准且具版本控管的私有契約，用來把邏輯角色對應到機構受治理的
實作與查核步驟。本公開儲存庫只說明 Adapter 必須證明什麼，不包含也不臆測
任何機構的 Adapter。

<a id="governing-artifact"></a>
## 主導依據（governing artifact）

[Governing
artifact](../skills/clin-nav/references/retrieval-playbook.md)
是在特定情境下主導一項決策，且目前有效的最高權威來源，例如適用標準、主管
機關指引、試驗計畫書、SAP 或經核准的機構詮釋資料。搜尋結果、教學文章或
舊版實作論文可作為找資料的線索，但不能逕自推翻主導依據。引用時要記錄文件
識別資訊、版本或日期、適用範圍及來源。

<a id="provenance"></a>
## 來源脈絡（provenance）

來源脈絡記錄主張、資料元素或程式技巧從哪裡來，包括來源識別、版本或快照、
存取或審閱日期，以及轉換或再利用限制。搜尋結果只能證明找到一條線索，不能
證明已審閱線索指向的原始來源。

<a id="grain"></a>
## 資料粒度（grain）

資料粒度說明一列或一筆紀錄在邏輯上代表什麼，例如每位合成人物的一次用藥
事件。先定義粒度，可避免計數、去重與連結在不知不覺中改變意義。

<a id="key-and-join-cardinality"></a>
## 鍵值與連結基數（key and join cardinality）

鍵值用來識別邏輯紀錄；連結基數說明紀錄預期是一對一、一對多或多對多，並
指出要檢查的筆數膨脹或遺失。欄位名稱本身不能證明它具有唯一性或可安全連結。

<a id="time-zero"></a>
## 起始時間點（time zero）

Time zero 是讓納入資格、治療或暴露分派與追蹤起點對齊的明確時點。對齊錯誤
可能造成選擇偏差或不死時間偏差；設計需要時必須先定義，不能拿任一現成日期
代替。

<a id="specification-only-versus-executable"></a>
## 僅規格與可執行輸出（specification-only versus executable）

僅規格輸出會列出邏輯需求與尚未完成的檢查，不能直接執行。可執行輸出則已在
指定的現行目標環境通過執行閘門。因此 `SPECIFICATION ONLY — NOT EXECUTABLE`
是安全狀態，不是把未完成的規格包裝成程式。

<a id="sas"></a>
## SAS

[SAS](https://www.sas.com/en_us/software/stat.html)是用於資料管理與統計分析的
軟體環境及程式語言。在本專案中，使用者要求 SAS 內容時，可能只需要名詞
說明、證據導覽或實作規格。只有在必要詮釋資料、參數、核准的 Adapter 與 fixture 都通過執行
閘門後，才會進入可執行程式碼階段。

<a id="validation-gap"></a>
## 驗證缺口（validation gap）

[驗證缺口](../skills/clin-nav/references/evidence-output-template.md#implementation-specification)
是尚缺的來源、決策、詮釋資料、檢查或驗收結果；在補齊之前，不能提高主張
強度或程式成熟度。列出缺口不等於證明工作無效，而是明確交代哪些事項尚未
驗證，以及需要什麼證據才能補上。
