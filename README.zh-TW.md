# Clinical Data Research Navigator

[English](README.md) | 繁體中文

Clinical Data Research Navigator 協助研究人員將臨床資料問題整理成依來源權威性排序的證據、安全的資料契約，以及明確的執行成熟度評估。

## 快速開始的必要條件

使用 npx 安裝需要 Node.js 與 npm/npx，也需要支援 Skills 的 Codex
介面。請先在終端機確認下列指令可執行：

```bash
node --version
npm --version
```

使用已安裝的 Skill 不需要 Python。Python 3.11 只供後文所述的專案貢獻者
執行測試與發布工具。

## 快速開始

請在要使用此 Skill 的專案根目錄執行：

```bash
npx skills add mtchuang1981/clin-data-nav
```

`npx skills add mtchuang1981/clin-data-nav` 是終端機指令，預設會把 Skill
安裝到目前專案的 `.agents/skills`。`/skills` 與
`$clinical-data-research-navigator` 要輸入在 Codex 對話中，不是終端機指令。
先用 `/skills` 確認 Codex 已找到 Skill，再明確叫用它。第三方 Skill 會使用
代理程式的權限執行，使用前請先審閱內容。

日後若要更新此專案內的安裝，請在終端機執行：

```bash
npx skills update clinical-data-research-navigator --project --yes
```

## 60 秒完成第一次使用

1. 在 Codex 輸入 `/skills`，確認清單中出現 **Clinical Data Research
   Navigator**。
2. 在 Codex 輸入這個最小範例：

   ```text
   $clinical-data-research-navigator 請協助我規劃使用合成真實世界資料的
   醫療利用描述性研究；不要自行猜測 schema 或代碼。
   ```

3. 預期第一份回覆會包含問題釐清、來源與 schema 界線、建議工作流程及
   缺少資訊清單。輸入不完整時，應得到規格與驗證缺口，而不是可上線 SQL、
   完整 SAP 或因果結論。

## 公開邊界

本儲存庫是公開核心（Public Core），內容包含可重複使用的指引、合成範例、測試與封裝工具；不包含私有 TMUCRD Adapter、編碼手冊、資料字典、實體 schema、憑證，或需登入才能存取的文件。本儲存庫不是 TMUCRD 資料字典。

若要導入機構內部環境，請在本儲存庫外掛載經核准且具版本控管的私有 Adapter，並在受治理的環境中確認目前使用的中繼資料。

## 第一次接觸臨床資料標準？

不需要先熟悉 CDISC 才能使用這個 Skill。以下三個名詞分別處理標準化臨床試驗資料流程中的不同部分：

| 名詞 | 白話說明 | 為什麼會在這裡出現 |
|---|---|---|
| [CDISC](https://www.cdisc.org/standards) | Clinical Data Interchange Standards Consortium，以及它所制定的臨床與非臨床研究資料標準體系。 | SDTM、ADaM、受控詞彙與相關實作指南都屬於這套標準體系。 |
| [SDTM](https://www.cdisc.org/standards/foundational/sdtm) | Study Data Tabulation Model，用一致的方式整理及呈現收集或接收的研究資料，同時保留原始意義。 | 讓研究資料更容易交換、審查、彙整與提交主管機關。 |
| [ADaM](https://www.cdisc.org/standards/foundational/adam) | Analysis Data Model，定義分析資料集及其詮釋資料，支援可重現的統計分析。 | 讓審查者能從分析結果追溯至分析資料，再回到 SDTM 來源。 |

常見的臨床試驗資料流程，可以先用這個簡化模型理解：

```text
收集或接收的研究資料
→ SDTM：標準化表列與審查
→ ADaM：分析就緒資料與衍生規則
→ 統計分析、表格、圖形與資料列表
```

這是入門用的心智模型，不是每一個臨床資料問題都必須遵循的固定流程。EHR、理賠資料、登錄資料、OMOP 與其他真實世界資料可能採用不同的來源模型。Skill 會先判斷實際適用的標準，再分開處理官方定義、研究特定規則、實作方法與機構內部對應關係。

## 真實世界證據與因果研究路由

面對 EHR、理賠資料、登錄資料、OMOP 與其他真實世界資料問題時，Skill
會先判斷主要目的屬於描述、預測、因果比較、測量驗證或實作。

- PICO 延伸欄位用來描述研究族群、介入或暴露、比較組、結果、時間起點、
  追蹤期間、場域與預定用途。PICO 能整理問題，但不能證明因果效度。
- [RWD](https://www.fda.gov/science-research/science-and-research-special-topics/real-world-evidence)
  是例行收集的資料；RWE 是分析符合用途的 RWD 後形成的臨床證據。
  RWD 不會自動成為 RWE。
- 只有因果比較問題已充分定義策略、納入條件、時間起點、追蹤期間、結果、
  estimand 與分析計畫時，才會考慮目標試驗模擬（TTE）。TTE 不是每一個
  RWD 問題的預設流程。

`build-rwe-sap` 是選配項目，並未內附於本儲存庫。若環境中另外安裝了相容的
Skill，它可以依已確認的交接紀錄，進一步制定完整 SAP、estimand、目標試驗
protocol 或因果研究設計。clin-data-nav 不會自動安裝它，而且只有名稱相同
不足以證明相容。

一般 Core 功能不需要 `build-rwe-sap`。如果它不存在或不相容，
clin-data-nav 仍會繼續進行證據導航、RWD 適用性檢查與邏輯資料契約，
同時清楚標示缺少的研究設計能力，不會宣稱已完成完整 SAP 或因果分析。

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

## 使用 Skill 需要 Python 嗎？

使用已安裝的 Skill 不需要 Python。Skill 本身由 Markdown、YAML 詮釋資料與參考文件組成，Codex 或 ChatGPT 會直接讀取。SAS、SQL、R 與 Python 可能是討論中的目標實作語言，但都不是呼叫 Skill 時必須安裝的執行環境。

只有要執行本儲存庫的測試、可重現封裝工具或嚴格的原始碼安裝程式時，貢獻者才需要 Python 3.11。依照下方 PowerShell 或 POSIX 指令安裝已發布的 ZIP，不需要 Python。

## 貢獻者環境（Python 3.11）

本儲存庫的開發與發布工具支援 Python 3.11。

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

## 經驗證的 GitHub Release 手動安裝

Codex 會從 `$HOME/.agents/skills` 載入個人 Skill。請從同一個 Release 下載 ZIP 與 manifest，先用 manifest 核對 ZIP，再解壓縮到獨立的 Skill 目錄。以下範例會安裝 `v0.2.2`；遇到既有安裝時會停止，不會直接覆寫。

PowerShell：

```powershell
$releaseVersion = "0.2.2"
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
release_version="0.2.2"
asset_name="clinical-data-research-navigator-$release_version"
release_base="https://github.com/mtchuang1981/clin-data-nav/releases/download/v$release_version"
curl -fLO "$release_base/$asset_name.zip"
curl -fLO "$release_base/$asset_name.manifest.json"
expected_hash="$(grep -o '"archive_sha256":"[0-9a-f]\{64\}"' "$asset_name.manifest.json" | cut -d '"' -f4)"
if command -v sha256sum >/dev/null 2>&1; then
  actual_hash="$(sha256sum "$asset_name.zip" | cut -d ' ' -f1)"
elif command -v shasum >/dev/null 2>&1; then
  actual_hash="$(shasum -a 256 "$asset_name.zip" | cut -d ' ' -f1)"
else
  echo "Install sha256sum or shasum to verify the archive." >&2
  exit 1
fi
test "$actual_hash" = "$expected_hash" || { echo "SHA-256 mismatch" >&2; exit 1; }
echo "SHA-256 OK"
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
  /absolute/path/you/select/skill-package/clinical-data-research-navigator-0.2.2.zip \
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
