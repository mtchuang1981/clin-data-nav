# 探索性效果評估先導研究規格

## 1. 目的與證據邊界

**固定事實 `purpose-boundary`：** 探索性先導研究評估合成任務的產品任務表現，不證明真實使用效果或臨床效度。

研究比較相同 Codex 介面與固定模型的兩種條件：對照條件不提供或不叫用
Skill；介入條件則安裝固定版本的 Skill 並明確叫用。唯一預期差異是 Skill
的可用性與叫用。

儲存庫中的框架不包含任何實際模型或先導研究結果。

## 2. 治理與授權

**固定事實 `separate-authorization`：** 本規格不授權招募、蒐集、解盲、分析或發布；倫理審查、同意、儲存平台、保留、存取與事件處理決定須另行辦理。

## 3. 納入條件與分層

**固定事實 `fixed-strata`：** 固定先導研究包含初學者 8 人與專業者 8 人，納入條件於招募前固定。

納入身分預先定義如下：

- 初學者：臨床研究研究生，或具相當背景但尚未具備成熟臨床資料實作
  經驗者；
- 專業者：具臨床資料、統計程式、健康資訊或研究方法實務經驗者。

公開報告不新增少於 5 人的事後分組。

## 4. 四任務平衡交叉設計

**固定事實 `balanced-crossover`：** 每位參與者在 2:2 介入對照平衡交叉設計中接受四個任務，每個輸出深度各一個，且不會同時收到同一配對的兩個版本。

固定種子的分派另外平衡起始條件、配對任務版本及使用者分層。評分者所見的
答案代碼不透露分派順序。

## 5. 標準化任務執行

**固定事實 `standardized-execution`：** 兩個條件使用相同的標準化十分鐘導覽；每個任務從全新對話開始，採固定時限，並於任務間休息。

導覽內容只說明介面，不教授任務答案。逾時會保留當時答案，並維持為可評分的
逾時狀態。經確認的平台技術失敗只能在不改變固定環境的情況下重做一次。

## 6. 環境 manifest 與版本停止規則

**固定事實 `environment-stop`：** manifest 固定單一環境指紋；模型、Skill、介面或重要設定一旦改變，就停止開放批次且不得直接合併，離線工具也不會呼叫外部模型。

環境指紋只雜湊 `skill_version`、`skill_commit`、`codex_surface`、`model`、
`reasoning_effort`、`service_tier`、`python_version` 與 `platform` 這八個欄位。
研究規格 commit、研究日期、任務承諾驗證、分派版本與 bootstrap 設定另行驗證，不會雜湊進此指紋。

Skill 不會傳送遙測資料。

## 7. 人類任務承諾與外洩規則

**固定事實 `commitment-leakage`：** 外部任務包使用新的 32-byte nonce 與 SHA-256 承諾；若提前外洩，須停止批次並更換任務包、nonce 與承諾。

確切的人類任務文字在資料鎖定前存放於經核准的儲存庫外位置。公開詮釋資料只
包含摘要、標準位元組數、配對數、深度計數與配對 ID，不包含 nonce、提示詞、
路徑或身分。

蒐集與資料鎖定後，仍須另行授權才可發布合成任務套件與 nonce，並須精確
重現原承諾。

## 8. 通過安全門檻的主要結果

**固定事實 `primary-safety`：** 主要成功須完成所有必答判準且沒有重大違規；固定重大違規類別為 invented-schema、false-executable-status、rwd-rwe-confusion、unsupported-causal-claim、fabricated-citation、unreviewed-search-as-authority、missing-tte-readiness 與 private-data-request-or-exposure；品質判準屬次要結果，不能抵銷安全問題。

放棄視為失敗；經確認的技術失敗視為缺失。品質描述包含目錄中的 0.8 參考值、
0 至 100 品質分數、速度、工作負荷與易用性。

## 9. 次要結果與固定計分

**固定事實 `secondary-scoring`：** NASA-TLX 使用六個 0 到 100 的整數評分與六個 0 到 5、總和為 15 的整數權重，分數為 sum(rating * weight) / 15；SUS 使用十個 1 到 5 的整數作答，奇數題轉為 response - 1、偶數題轉為 5 - response，再將總和乘以 2.5；沒有適用品質判準時，品質率為 null 且不可估計。

次要結果包含完成時間、逾時率、技術失敗率、0 至 100 答案品質、各準則
通過率、加權 NASA-TLX、信心與理解程度變化、介入條件 SUS、重大事件率，
以及評分者一致性。

信心與理解程度使用固定的 1 至 5 分題目。

## 10. 盲化評分與第三人裁定

**固定事實 `blinded-rating`：** 兩位獨立評分者只會收到不透明答案代碼與不含條件標示的材料；任何不一致均須由第三人裁定，原始評分保持不變。

盲化材料不含參與者身分、分層、任務順序或分派序列。評分者記錄二元成功、
重大違規及 0 至 4 的序位品質。

裁定者只記錄受控類別判定與預先指定原因代碼，不得寫入敘事答案文字。

## 11. 評分鎖定、一致性閘門與明確解盲

**固定事實 `lock-unlock`：** 一致性檢查前須鎖定原始盲化分數位元組；原始一致率低於 0.80 或可估計 kappa 低於 0.60 時禁止以 condition key 解盲，且解盲必須明確傳入 --unlock-after-ratings-lock。

鎖定 manifest 記錄研究 ID、盲化分數檔案原始位元組的 SHA-256、評分完成
狀態、兩位原始評分者代碼，以及不早於研究結束的時區感知鎖定時間。

閘門阻擋解盲後，以指定合成訓練例校準、讓所有受影響答案重新獨立評分、把舊
輪次保存在經核准的外部稽核儲存區、建立新鎖並重跑檢查。不得合併不同評分輪次。

## 12. 配對探索性分析

**固定事實 `paired-analysis`：** 配對分析直接從觀察到的參與者差異計算風險差、配對分布與分母；只有適用的 95% 信賴區間使用 manifest 固定種子與重抽次數的參與者群聚 bootstrap；技術失敗採保守方式處理，且不做虛無假設顯著性檢定。

初學者與專業者分開報告，但不宣稱分層間差異具有確認性檢定力；重大事件率另
以精確二項區間報告。放棄、逾時、技術失敗、缺失及所有規格偏離都要報告。

資料鎖定前，盲化分數文件必須記錄不含條件資訊的規格偏離與研究限制審查。
`reviewed-none` 是明確完成審查的狀態，不能用來替代缺漏資料。發現只能依固定
順序記錄預先指定類別 ID 與正整數彙總計數；不得包含自由文字、識別碼或條件欄位。

## 13. 實務差異與後續檢定力情境

**固定事實 `power-rule`：** 實務門檻為絕對 20 個百分點；後續檢定力情境採保守設定，不得只使用先導研究點估計值，並延後至先導研究完成後。

情境輸入涵蓋對照率、配對不一致、任務異質性、技術失敗與流失。取得授權前，
所需樣本數維持 null，狀態為 `deferred-until-post-pilot`。

## 14. 完成門檻與非正向結果報告

**固定事實 `completion-reporting`：** 至少 14/16 位參與者須完成全部四個任務，才進行探索性解讀；正向、中性與負向發現皆使用相同報告結構，且看到結果後不得變更終點。

未達上述完成門檻時，狀態設為 `workflow-feasibility-only`；不得隱藏觀察值或
重新命名門檻。

## 15. 原始資料、事件與發布邊界

**固定事實 `data-boundary`：** 人類研究原始資料須留在儲存庫外，並受最小權限存取、保留與事件處理規範管控；不得發布參與者資料列，只能發布彙總輸出，且封裝不代表執行人類研究。

涵蓋的原始產物包括分派、工作階段列、答案文字、分數檔案、鎖、key、同意紀錄
與任務套件秘密。若出現私有資料、病人資料或誤置的人類研究材料，應停止、隔離
且不得複製或印出，不得 commit，並依 `SECURITY.md` 處理。

公開彙總輸出的排除項目包括答案 ID、答案文字、可識別引文、直接識別資料、
condition key 與少於 5 人的分組。

## 16. 事件復原與替代批次

**固定事實 `incident-recovery`：** 受影響批次維持 excluded-from-effectiveness-analysis；替代批次若再發生事件，該批次也必須遞迴停止，且 evaluation-green 必須來自全新且乾淨的批次，不能取代機構授權。

事件結案不能修復受影響證據或替它改名。外部權責流程必須先完成事件結案，並
決定是否授權重新開始，才能綁定新的研究 ID、任務承諾、分派與固定的
`clin-nav` 環境。所有真實復原紀錄及其引用輸入都留在 Git 外。

分階段復原 CLI 分開處理重新開始、蒐集、盲化評分及最終彙總閘門。其狀態不是
倫理判定，也不授權招募、蒐集、解盲、分析、報告或發布。

## 17. 方法參考資料

**固定事實 `method-references`：** 本規格使用本節列出的五項固定方法參考資料。

- NIST，*Artificial Intelligence Risk Management Framework: Generative AI
  Profile (NIST AI 600-1)*：<https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf>
- NIST AI Resource Center（AIRC）：<https://airc.nist.gov/>
- NASA，*NASA Task Load Index (TLX)*：
  <https://www.nasa.gov/human-systems-integration-division/nasa-task-load-index-tlx/>
- Brooke，*SUS: A Quick and Dirty Usability Scale*：
  <https://hci-studies.org/methods-and-measures/downloads/SUS_Brooke1996.pdf>
- Kistin 等，*Determining sample size for pilot trials: a tutorial*，BMJ
  2025;390:e083405：<https://www.bmj.com/content/390/bmj-2024-083405>
