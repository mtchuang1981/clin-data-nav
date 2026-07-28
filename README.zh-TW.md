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

## 從 GitHub Release 安裝

Codex 會從 `$HOME/.agents/skills` 載入個人 Skill。請從同一個 Release 下載 ZIP 與 manifest，先用 manifest 核對 ZIP，再解壓縮到獨立的 Skill 目錄。以下範例會安裝 `v0.1.1`；遇到既有安裝時會停止，不會直接覆寫。

PowerShell：

```powershell
$releaseVersion = "0.1.1"
$assetName = "clinical-data-research-navigator-$releaseVersion"
$releaseBase = "https://github.com/mtchuang1981/clin-data-nav/releases/download/v$releaseVersion"
Invoke-WebRequest "$releaseBase/$assetName.zip" -OutFile "$assetName.zip"
Invoke-WebRequest "$releaseBase/$assetName.manifest.json" -OutFile "$assetName.manifest.json"
$manifest = Get-Content "$assetName.manifest.json" -Raw | ConvertFrom-Json
$actualHash = (Get-FileHash "$assetName.zip" -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -ne $manifest.archive_sha256) { throw "SHA-256 mismatch" }
$skillDirectory = Join-Path $HOME ".agents\skills\clinical-data-research-navigator"
if (Test-Path $skillDirectory) { throw "Skill already exists: $skillDirectory" }
New-Item -ItemType Directory -Path $skillDirectory -Force | Out-Null
Expand-Archive "$assetName.zip" -DestinationPath $skillDirectory
Test-Path (Join-Path $skillDirectory "SKILL.md")
```

POSIX shell：

```bash
release_version="0.1.1"
asset_name="clinical-data-research-navigator-$release_version"
release_base="https://github.com/mtchuang1981/clin-data-nav/releases/download/v$release_version"
curl -fLO "$release_base/$asset_name.zip"
curl -fLO "$release_base/$asset_name.manifest.json"
python -c "import hashlib,json,pathlib; z=pathlib.Path('$asset_name.zip'); m=json.loads(pathlib.Path('$asset_name.manifest.json').read_text()); assert hashlib.sha256(z.read_bytes()).hexdigest()==m['archive_sha256'], 'SHA-256 mismatch'; print('SHA-256 OK')"
skill_directory="$HOME/.agents/skills/clinical-data-research-navigator"
test ! -e "$skill_directory" || { echo "Skill already exists: $skill_directory"; exit 1; }
mkdir -p "$skill_directory"
unzip "$asset_name.zip" -d "$skill_directory"
test -f "$skill_directory/SKILL.md"
```

Codex 會自動偵測 Skill 變更；若 Skill 沒有出現，請重新啟動 Codex，再用 `/skills` 檢查。

## 從原始碼安裝

若要使用本儲存庫較嚴格的安裝檢查，請自行建立封裝檔，並讓 manifest 與 ZIP 放在同一個目錄。安裝程式會驗證壓縮檔雜湊、檔案清單、大小限制、路徑與解壓後的 Skill。

```bash
python scripts/package_skill.py --output-dir /absolute/path/you/select/skill-package
python scripts/install_local.py \
  /absolute/path/you/select/skill-package/clinical-data-research-navigator-0.1.1.zip \
  --destination "$HOME/.agents/skills"
```

安裝完成後的目錄為 `$HOME/.agents/skills/clinical-data-research-navigator`。只有在確定要取代這個既有 Skill 時，才使用 `--overwrite`。

## 使用 Skill

在 Codex CLI 或 IDE 擴充功能中，可先執行 `/skills` 確認 Skill 已被偵測，再用 `$clinical-data-research-navigator` 明確呼叫。使用 ChatGPT 桌面版時，可從側邊欄開啟 **Skills**，或輸入 `@` 後選擇 **Clinical Data Research Navigator**。若問題符合 Skill 的描述，Codex 與 ChatGPT 也可能自動啟用。

提示詞範例：

```text
$clinical-data-research-navigator 請排序合成 TEAE 衍生規則的權威來源，
並依序產出「證據 → 資料契約 → 程式碼成熟度 → 驗證缺口」。

$clinical-data-research-navigator 請審查一段合成 SAS ADAE 邏輯的最佳化方向。
先查 SAS 官方文件，再針對 Lex Jansen 實作文獻精準搜尋，並保留來源與再利用條款。

$clinical-data-research-navigator 請描述不可執行的 OMOP 類型 phenotype，
不要猜測 Concept ID 或機構內部 schema。
```

若沒有經核准且具版本控管的 Adapter、即時中繼資料或測試資料，預期輸出會是規格與驗證缺口，而不是可直接在機構環境執行的程式碼。

## 延伸文件

- [架構說明](docs/architecture.md)
- [發布流程](docs/release.md)
- [版本紀錄](CHANGELOG.zh-TW.md)
- [安全性回報](SECURITY.md)
- [貢獻指南](CONTRIBUTING.md)
- [Codex 官方 Skill 文件](https://learn.chatgpt.com/docs/build-skills)
