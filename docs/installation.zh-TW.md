# 安裝指南

[English](installation.md)

建議使用 `npx skills add`，把 Skill 安裝在要使用它的專案中。只有需要固定
Release 產物版本時，才使用驗證 ZIP 安裝；開發或稽核本儲存庫時，才使用
原始碼簽出安裝。

## 執行環境界線

安裝後只包含操作指引與參考文件的 Skill 不需要 Python。它由 Markdown、YAML
詮釋資料及代理程式產品讀取的參考文件組成。只有執行本儲存庫的貢獻、驗證、
封裝、發布查核及嚴格原始碼安裝工具時，才需要 Python 3.11；設定方式請見
[CONTRIBUTING.md](../CONTRIBUTING.md)。

## 確認必要條件

建議的安裝方式需要 Node.js 與 npm/npx，也需要支援 Skills 的 Codex 介面。
請在終端機確認下列指令可執行：

```bash
node --version
npm --version
npx --version
```

## 安裝到目前專案

請在要使用此 Skill 的專案根目錄執行：

```bash
npx skills add mtchuang1981/clin-data-nav
```

這個指令會把 Skill 安裝到目前專案的 `.agents/skills`。第三方 Skill 會使用
代理程式的權限執行，使用前請先審閱內容。

`/skills` 與 `$clinical-data-research-navigator` 要輸入在 Codex 對話中，
不是終端機指令。先用 `/skills` 確認已找到 Skill，再明確叫用。若實作輸入
不完整，回覆應先做問題釐清並提供缺少資訊清單，不得臆造 schema 或上線
程式碼。

在 Codex CLI 或 IDE 擴充功能中，請用 `/skills` 確認是否已找到 Skill，再用
`$clinical-data-research-navigator` 明確叫用。ChatGPT 桌面版採用另一套安裝
介面：請開啟 `Skills`；部分介面會將它放在 **Plugins → Skills**。若方案與
工作區允許上傳，請選擇 **Create**，再從電腦上傳 Skill。介面可能更新，請
同時查核 OpenAI 的 [Help Center Skills
說明](https://help.openai.com/en/articles/20001066)與[建立 Skills
文件](https://learn.chatgpt.com/docs/build-skills)。專案內的 `npx` 指令只會
寫入 `.agents/skills`，不會把它安裝到 ChatGPT，也不能證明它已刊登於公開
Plugin 目錄。

## 更新專案內的安裝

請在同一個專案根目錄執行：

```bash
npx skills update clinical-data-research-navigator --project --yes
```

接著再用 `/skills` 確認。若顯示的行為仍是舊版，請依下方對應階段排解，
不要直接重複安裝。

## 從 GitHub Release 驗證 ZIP 後安裝

下一個 Release 的目標版本是 `0.3.0`。下列指令是目標版本範例，不表示
`v0.3.0` 已經發布。請等到儲存庫的 Release 頁面同時提供相符的 ZIP 與
manifest 後再執行。兩個檔案必須來自同一個 Release；先用 manifest 內的
`archive_sha256` 核對 ZIP 的 SHA-256，再解壓縮。以下範例遇到既有目的
目錄時會停止，不會覆寫。

PowerShell：

```powershell
$releaseVersion = "0.3.0"
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
release_version="0.3.0"
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

## 從原始碼簽出安裝

若要使用本儲存庫較嚴格的檢查，請建立封裝檔，並讓 manifest 與 ZIP 位於
同一個目錄。安裝程式會驗證壓縮檔雜湊、成員清單、大小限制、路徑與解壓後
的 Skill。

```bash
package_directory="/absolute/path/you/select/skill-package"
package_output="$(python scripts/package_skill.py --output-dir "$package_directory")"
archive_path="$(printf '%s\n' "$package_output" | sed -n '1p')"
manifest_path="$(printf '%s\n' "$package_output" | sed -n '2p')"
test -f "$archive_path"
test -f "$manifest_path"
python scripts/install_local.py \
  "$archive_path" \
  --destination "$HOME/.agents/skills"
```

本機封裝器會先驗證 Skill，再依序輸出實際 archive 與 manifest 路徑；將它
回報的 archive 交給安裝器，就不會綁死未來的版本常數。目的目錄為
`$HOME/.agents/skills/clinical-data-research-navigator`。只有先檢查並確認要取代
這個安裝時，才使用 `--overwrite`；上方指令未使用 `--overwrite`，所以遇到
既有目的目錄時會拒絕安裝。封裝與安裝程式屬於貢獻者／發布工具，因此這條
路徑需要 Python 3.11 及
[CONTRIBUTING.md](../CONTRIBUTING.md) 所述的環境。

## 疑難排解

請在發生錯誤的階段處理原因。不要略過驗證，也不要在尚未釐清目的目錄內容前
直接刪除。

<a id="troubleshoot-missing-node"></a>
### 找不到 `node`、`npm` 或 `npx`

診斷：重新執行必要條件檢查，並檢查 `PATH`。處理：安裝包含 npm/npx 的
Node.js 發行版，重新啟動終端機讓 `PATH` 重新載入，再確認三個版本指令後
才安裝。

<a id="troubleshoot-install-command-failure"></a>
### `npx skills add` 失敗

診斷：保留完整錯誤訊息，確認儲存庫拼字及目前網路連線，並區分工具／
registry 與 GitHub 存取問題。處理：修正已辨識的原因後，回到預定的專案
根目錄重新執行同一個指令；不要改用未驗證的 ZIP。

<a id="troubleshoot-activation-failure"></a>
### 安裝後找不到 Skill 或無法啟用

診斷：確認目前位於相同的專案根目錄，並檢查
`.agents/skills/clinical-data-research-navigator/SKILL.md` 是否存在，再查看
`/skills`。處理：開啟預定專案，重新啟動 Codex 一次後再查 `/skills`；尚未
查清實際安裝位置前，不要移動目錄。

<a id="troubleshoot-stale-after-update"></a>
### 更新後仍顯示舊內容

診斷：確認 `npx skills update` 在同一個專案執行，再用 `/skills` 查看
偵測結果。處理：針對該專案關閉並重新啟動 Codex，再次檢查後判斷是否需要
更新。

<a id="troubleshoot-download-failure"></a>
### ZIP 或 manifest 下載失敗

診斷：確認指定 tag 有已建立的 Release，且兩個資產名稱都存在。處理：只有
能從同一個 Release 取得 ZIP 與 manifest 時才重新下載；不得混用不同 tag
的資產，也不要使用未完整下載的檔案。

<a id="troubleshoot-manifest-mismatch"></a>
### manifest 與 ZIP 不相符

診斷：SHA-256 mismatch 表示 ZIP 與指定 manifest 不相符。處理：不要解壓縮；
只移除這次下載的兩個檔案，再從同一個已驗證 Release 重新下載。若仍不相符，
請停止並回報。

<a id="troubleshoot-existing-target"></a>
### 目的目錄已存在

診斷：安全範例會拒絕覆寫既有安裝。處理：先檢查確切目錄，判斷是否要保留；
若要比較，請使用另一個目的目錄。
只有經審閱且確定要取代時，才使用嚴格安裝程式的 `--overwrite`。

<a id="troubleshoot-python-setup-failure"></a>
### Python 貢獻者環境設定失敗

診斷：執行 `python --version`，確認 Python 3.11、已啟用的虛擬環境，以及
第一個相依套件安裝錯誤。處理：先辨識原因，再重建虛擬環境，並依
[CONTRIBUTING.md](../CONTRIBUTING.md) 重新執行 editable install。Python 設定
失敗不影響已安裝 Skill 的一般使用。
