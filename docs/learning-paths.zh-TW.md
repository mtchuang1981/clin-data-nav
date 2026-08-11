# 初學者學習路徑

[English](learning-paths.md)

請選擇最接近目前決策需求的路徑。得到足夠的說明或完成證據審查後，就可以
停下來；不是每條路徑都要以程式碼收尾。若需求確實進入實作階段，仍須通過
執行閘門。

<a id="learn-the-terms"></a>
## learn-the-terms：臨床試驗與 CDISC

**目標：** 了解臨床研究、CDISC、SDTM、ADaM、試驗計畫書、統計分析計畫
（SAP）與實作證據之間的關係。

**先備條件：** 準備一個想了解的臨床試驗名詞、交付項目或決策即可；不需要
程式能力或機構資料。

**起始提示：**「請用 `quick explanation` 深度說明 SDTM 是什麼、它與 ADaM
有何關係，以及這兩項標準都不能證明哪些來源資料品質。」

**預期深度：** 先用 `quick explanation`。只有在需要確認適用標準版本、實作
指南、主管機關要求或研究特定的主導依據時，才進入 `evidence navigation`。

**無法證明：** 這條路徑不能證明來源資料品質、研究特定對應、提交就緒度或
實作效度。

**接著閱讀：** 查看[詞彙表中的 CDISC、SDTM 與
ADaM](./glossary.zh-TW.md#cdisc)、[安裝指南](./installation.zh-TW.md)、合成資料
的 [TEAE-to-SAS 範例](../examples/teae-to-sas-spec.md)，以及 Skill 的[輸出深度
指南](../skills/clin-nav/references/output-depths-and-learning-paths.md)。

**停止或升級條件：** 名詞與限制已足以回答問題時即可停止。要選擇版本或提交
規則前，應升級為證據導覽；只有需要對應或衍生規格時，才升級為實作規格。
不得從通用標準推測機構內的資料對應。

<a id="assess-the-evidence"></a>
## assess-the-evidence：RWD、RWE 與研究設計

**目標：** 把寬泛的真實世界資料問題整理成範圍明確的證據路徑，再判斷應採
描述性設計，或因果比較研究設計。

**先備條件：** 說明研究目的、預定用途、族群或情境，以及考慮中的 RWD
來源類型；尚不確定的內容可以明列為未知。

**起始提示：**「請用 `evidence navigation` 深度找出這項 RWD 問題的主導
來源、區分 RWD 與預定 RWE 主張，並列出尚缺的設計資訊。」

**預期深度：** 先用 `evidence navigation` 尋找來源並依權威層級排序。問題
明確到可以定義 PICO 或 estimand、time zero、追蹤期間、資料適用性、偏差及
診斷項目後，再進入 `research design`。只有因果比較問題才需要評估目標試驗
模擬。

**無法證明：** 這條路徑不能證明因果效度、資料適用性、測量效度或分析已
完成。

**接著閱讀：** 查看[詞彙表中的 RWD、RWE、PICO、目標試驗模擬、estimand
與 phenotype](./glossary.zh-TW.md#rwd)、[安裝指南](./installation.zh-TW.md)、
合成資料的 [OMOP phenotype 範例](../examples/omop-phenotype-to-sql-spec.md)，
以及 Skill 的 [RWE 問題路由
參考](../skills/clin-nav/references/rwe-question-routing.md)。

**停止或升級條件：** 如果任務只需尋找或比較來源，完成證據導覽即可停止；
需要明確界定研究問題時，再升級為研究設計。混雜、測量、資料來源或驗證缺口尚未
處理前，不得宣稱已具因果效度、資料已適用，或分析已完成。

<a id="prepare-an-implementation"></a>
## prepare-an-implementation：機構實作

**目標：** 把公開證據與已定義的決策轉成邏輯資料契約，不臆造機構的實體
資料表結構。

**先備條件：** 準備已定義的決策、主導證據，以及獲准可公開討論的邏輯需求；
機構自有詮釋資料仍須留在核准的私有流程。

**起始提示：**「請用 `implementation specification` 深度，只使用公開合成
範例準備邏輯衍生規格，並列出仍需哪些經核准的詮釋資料與 fixture。」

**預期深度：** 使用 `implementation specification`。在核准的 Adapter、
經現況查核的詮釋資料、參數與驗收 fixture 都通過執行閘門之前，輸出維持
`SPECIFICATION ONLY — NOT EXECUTABLE`。缺少這些輸入時，不必產生原始碼。

**無法證明：** 邏輯規格不能證明本地對應仍為現行版本、fixture 已通過、
程式可執行或結果已驗證。

**接著閱讀：** 查看[詞彙表中的資料契約、governing artifact、SAS 與驗證
缺口](./glossary.zh-TW.md#data-contract)、[安裝指南](./installation.zh-TW.md)、
合成資料的[機構對應範例](../examples/synthetic-institutional-mapping.md)、Skill 的
[Adapter 契約](../skills/clin-nav/references/institutional-adapter-contract.md)，
以及[實作輸出範本](../skills/clin-nav/references/evidence-output-template.md#implementation-specification)。

**停止或升級條件：** 執行閘門未完備時，應停在邏輯規格。只有在取得授權，
且確實需要現行詮釋資料或 fixture 時，才透過核准的私有流程升級處理；不得把
這些內容複製到公開儲存庫。必要檢查通過後，才能提高程式成熟度。
