# Clinical Data Research Navigator

[English](README.md) | 繁體中文

Clinical Data Research Navigator 協助研究人員將臨床資料問題整理成依來源權威性排序的證據、安全的資料契約，以及明確的執行成熟度評估。

## 公開邊界

本儲存庫是公開核心（Public Core），內容包含可重複使用的指引、合成範例、測試與封裝工具；不包含私有 TMUCRD Adapter、編碼手冊、資料字典、實體 schema、憑證，或需登入才能存取的文件。本儲存庫不是 TMUCRD 資料字典。

若要導入機構內部環境，請在本儲存庫外掛載經核准且具版本控管的私有 Adapter，並在受治理的環境中確認目前使用的中繼資料。

## 支援的問題

此 Skill 適合處理下列臨床資料問題：

- CDISC、ADaM、SDTM 或法規用語；
- 試驗計畫書、統計分析計畫（SAP）或證據來源導引；
- SAS、SQL、R、EHR、理賠資料、登錄資料或 OMOP 的實作規格；
- 資料契約、對應檢查清單與程式碼成熟度關卡（gate）；以及
- 不需要 schema 或資料字典細節的公開 TMUCRD 背景資料。

若缺少具版本控管的 Adapter、即時中繼資料與測試資料（fixture），此 Skill 只會提供規格，不會產生可在機構環境直接執行的程式碼。

處理 SAS 最佳化、重構、除錯、審查或衍生邏輯時，此 Skill 會先搜尋 SAS 官方文件。若仍需要實作證據，且執行環境具備網路工具，便會使用 `site:lexjansen.com` 進行精準搜尋並審閱特定論文。Skill 會記錄來源與程式碼出處、檢查再利用條款，並要求在目標環境完成量測後，才能宣稱效能有所改善；若無法審閱論文，則會將此限制列為驗證缺口。

## 儲存庫與已安裝 Skill 的結構

原始碼儲存庫包含治理文件、測試、腳本，以及可安裝 Skill 的標準來源：

```text
clin-data-nav/
├── scripts/                              # 驗證、封裝與安裝
└── skills/clinical-data-research-navigator/  # Skill 原始碼
```

封裝後的 ZIP 只包含可安裝的 Skill 檔案。本機安裝時，會將 `clinical-data-research-navigator/` 放在你指定的目的目錄下。

## 設定 Python 3.11 環境

本專案第一版支援 Python 3.11。

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## 驗證儲存庫

提出變更前，請完整執行以下四項檢查：

```bash
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

## 封裝與安裝

請先選擇你有權限管理的絕對路徑，再將下列指令中的範例路徑替換成實際位置。安裝程式不會假設特定平台的 Skill 路徑。

```bash
python scripts/package_skill.py --output-dir /absolute/path/you/select/skill-package
python scripts/install_local.py \
  /absolute/path/you/select/skill-package/clinical-data-research-navigator-0.1.0.zip \
  --destination /absolute/path/you/select/installed-skills
```

安裝完成後的目錄為 `/absolute/path/you/select/installed-skills/clinical-data-research-navigator`。只有在確定要取代既有安裝時，才使用 `--overwrite`。

## 延伸文件

- [架構說明](docs/architecture.md)
- [發布流程](docs/release.md)
- [安全性回報](SECURITY.md)
- [貢獻指南](CONTRIBUTING.md)
