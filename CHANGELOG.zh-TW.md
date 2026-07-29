# 版本紀錄

## 0.2.1 - 2026-07-29

### 文件

- 新增雙語快速開始指令：
  `npx skills add mtchuang1981/clin-data-nav`。
- 說明 `npx` 是專案層級安裝，並保留有版本、manifest 與 SHA-256
  核對的 GitHub Release 流程，作為經驗證的手動安裝方式。

### 驗證

- 擴充 README 契約測試，涵蓋快速開始指令、專案層級安裝邊界、
  Skill 偵測與明確呼叫方式。

## 0.2.0 - 2026-07-28

### 新功能

- 新增 PICO 延伸問題契約，以及描述、預測、因果比較、測量驗證與實作路由。
- 明確區分 RWD 與分析後形成的 RWE，並為因果比較問題加入目標試驗模擬
  readiness gate。
- 定義選配 `build-rwe-sap` 的相容性、交接、降級運作與 execution gate
  契約，不在套件內加入第二個 Skill。

### 文件

- 為第一次接觸臨床資料標準的讀者補充 CDISC、SDTM 與 ADaM 說明。
- 說明使用已安裝的 Skill 不需要 Python，並讓 POSIX Release 安裝核對流程
  不再依賴 Python。
- 補上 RWE、TTE 與選配 `build-rwe-sap` 的雙語操作說明。

### 驗證

- 將離線行為案例由 7 個擴充至 11 個，涵蓋描述性 RWD、TTE 交接、
  因果研究條件不足及選配 Skill 不存在等情境。

## 0.1.1 - 2026-07-28

### 新功能

- 新增可追溯的 Lex Jansen SAS 最佳化檢索契約，涵蓋逐篇論文來源、
  程式碼再利用條款、clean-room 替代方案、無網路狀態揭露，以及目標環境效能驗證。

### 文件

- 新增繁體中文 README。
- 補上 GitHub Release 安裝與 SHA-256 核對、從原始碼安裝、Skill 偵測、
  明確呼叫方式，以及臨床資料提示詞範例。
