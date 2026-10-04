# Installed Skill Integrity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 對使用者指定的安裝目錄與可信外部 manifest 提供選用、唯讀、限額的內容診斷。

**Architecture:** C1 抽出狹窄套件 primitives，保留 installer／packager 舊 wrapper 與行為；C2 用 B1 strict reader 做 manifest trust validation，再 bounded walk/hash。成功只描述 manifest-file 範圍，不宣稱 host loaded version 或 bytecode/runtime 完整性。

**Tech Stack:** Python 3.11 標準函式庫、既有 pytest；不新裝工具、不啟動 host 或網路。

**Spec:** [已核准設計](../specs/2026-10-04-public-core-usability-design.md)，第四節；[共同執行約束](2026-10-04-public-core-usability.md)。

## Global Constraints

- Manifest 1 MiB、256 records、單檔 10 MiB、總檔案 40 MiB；JSON 深度至多 12。
- 遍歷至多 4,096 entries、深度 32；排除 cache 前仍檢查 link/reparse。
- `--comparison` 為 bytes（預設）或 canonical-text；canonical 規則只正規化有效無 NUL UTF-8 的 CRLF／CR 至 LF。
- Manifest SHA-256 必填；只讀使用者指定目錄，不掃其他 agents、不安裝、不覆寫、不 restart、不連網。
- `loaded_version: not-verified`；不接受 ZIP，所以 archive_sha256 只核對格式。
- 不改 installer 既有版本限制／API，舊 reader 接受行為不變；新診斷可用可信舊 clin-nav manifest。

## Review Focus

1. 可信 hash 對應 empty／非 Skill manifest：C2 拒絕沒有 SKILL.md 的 manifest，不能空集合成功。
2. canonical normalization 吞掉真正二進位差異：C1 測 NUL／invalid UTF-8／Unicode 保持 bytes，C2 分開報結果。
3. 被排除 bytecode 中藏 junction 或 expected manifest member：C2 先安全檢查，宣告的 member 永不被忽略。
4. Manifest filename path 在 Windows 裝置、ADS／NFC/casefold／ancestor 衝突下逸出：C1/C2 在任何 file open 前拒絕。
5. 檔案在 lstat/open/read 間交換或成長：C2 模擬 identity/size/mtime mismatch 與 bounded read，不宣稱原子快照。

---

### Task C1: 狹窄套件 helper 與舊行為相容性

**Files:**
- Create: `scripts/package_contract.py`、`tests/test_package_contract.py`
- Modify: `scripts/install_local.py:58`、`scripts/install_local.py:84`、`scripts/install_local.py:111`、`scripts/install_local.py:146`、`scripts/package_skill.py:51`
- Test: `tests/test_install_local.py`、`tests/test_compare_packages.py`

**Interfaces:**
- Produces: `canonical_package_bytes(data: bytes) -> bytes`
- Produces: `portable_path_key(name: str) -> tuple[str, ...]`
- Produces: `validate_member_name(name: str, *, reject_windows_devices: bool = False) -> None`
- Produces: `manifest_records(manifest: dict, *, max_records: int = 256) -> dict[str, dict]`
- Produces: `hash_stream(stream: BinaryIO, *, max_bytes: int | None = None, chunk_bytes: int = 65536) -> str`
- C2 使用 strict path mode；舊 installer wrapper 明確傳 False，保留錯誤訊息、大小 constants monkeypatch 與 ZIP metadata checks。

- [x] **Step 1: 新增純 helper RED tests**

`test_canonical_bytes_normalize_only_text_line_endings` assert `b'a\r\nb\rc' -> b'a\nb\nc'`；NUL、invalid UTF-8 原樣；不 trim、不 Unicode normalize、不加結尾 LF。`test_strict_paths_reject_portable_aliases_before_open` 參數化 drive-relative、絕對、backslash、empty/dot/dotdot、重複 separator、ADS、尾端點/空白；strict mode 另拒 ASCII controls、DEL 與 Windows device basenames（含副檔名）。`test_manifest_records_reject_bool_size_and_duplicate_paths` 與 max_records 256/257；`test_hash_stream_is_bounded_and_uses_fixed_chunks` 檢查 exact/over與無 unbounded read。

```python
def test_canonical_bytes_normalize_only_text_line_endings():
    assert canonical_package_bytes(b'a\r\nb\rc') == b'a\nb\nc'
    assert canonical_package_bytes(b'a\x00\r\n') == b'a\x00\r\n'
    assert canonical_package_bytes(b'\xff\r\n') == b'\xff\r\n'
    assert canonical_package_bytes(b' a ') == b' a '
```

- [x] **Step 2: RED**

Run `python -m pytest -q tests/test_package_contract.py --basetemp <fresh-external-basetemp>`；期望 module/API 缺失。

- [x] **Step 3: 抽取現有 primitives，不重構 installation 流程**

canonical_bytes 直接採現行 packager演算法；現行 `_canonical_package_bytes(path)` 仍存在，改呼叫 bytes helper。Installer `_portable_path_key`、`_manifest_records`、`_hash_stream` 仍存在，forward既有 constants；`_validate_member` 只共用 name checks，仍保留 ZipInfo 型別／DOS directory／symlink checks與原 unsafe ZIP member訊息。新的strict mode只供diagnostic使用；原 preflight、atomic publish／rollback、PACKAGE_VERSION 與 parser不變。

- [x] **Step 4: GREEN 與位元組相容性**

Run `python -m pytest -q tests/test_package_contract.py tests/test_install_local.py tests/test_compare_packages.py --basetemp <fresh-external-basetemp>` 與 reproducible gate。新增 `test_packager_refactor_preserves_legacy_bytes`：同一 synthetic Skill／版本先正常 build，再用 test-only legacy canonical function 暫時 monkeypatch packager `_canonical_package_bytes` build reference，assert ZIP與manifest bytes完全一致。Reference function 只複製本 task 開始時的原 9 行 canonical 規則，不涉及私人檔案。若舊 tests 失敗，先修抽取／forward相容性，不改測試期待來掩蓋。

- [x] **Step 5: Commit**

Add helper、兩 consumers 與 tests，commit `refactor: share narrow package validation primitives`。

### Task C2: 唯讀 installed Skill 診斷、信任根與雙語文件

**Files:**
- Create: `scripts/verify_installation.py`、`tests/test_verify_installation.py`、`tests/test_verify_installation_cli.py`
- Modify: `docs/installation.md`、`docs/installation.zh-TW.md`、`README.md`、`README.zh-TW.md`
- Test: `tests/test_public_core_docs.py`

**Interfaces:**
- Consumes: B1 `read_bounded_bytes`／`parse_strict_json`，C1 helper，既有 packager SEMVER 與 package-name格式。
- Produces: `validate_installation_manifest(payload: object) -> dict[str, dict]`（無效固定 ValueError）。
- Produces: `verify_installation(skill_dir: Path, manifest_path: Path, *, manifest_sha256: str, comparison: str = "bytes") -> dict`（無效／unsafe／concurrent change 固定 ValueError，CLI安全轉exit2）。
- Produces: `main(argv: list[str] | None = None) -> int`，參數為 `--skill-dir`、`--manifest`、`--manifest-sha256`、`--comparison`；help固定，invalid訊息 `installation verification failed\n`，不回顯 argv／path。

Summary固定為 comparison、manifest_version、status、expected_file_count、matched_file_count、missing_file_count、extra_file_count、different_file_count、ignored_file_count、loaded_version。成功status依模式為 manifest-files-byte-identical／manifest-files-canonical-content-matches；差異 content-differs。只用整數計數，不回傳檔名、本機路徑、檔案內容或 archive-verified 宣告。

- [x] **Step 1: 建立可信 synthetic 安裝fixture與 RED tests**

在test module定義 `make_installed_package(tmp_path: Path, *, version: str = "0.8.0") -> tuple[Path, Path, str]`：建立最小合法 synthetic Skill，以 build_package生成manifest，外部installed目錄填入該package的精確 member bytes；manifest hash用原始bytes計算，輸入都在repo外。`test_exact_manifest_files_match_without_writes` assert成功、loaded_version not-verified、目錄與manifest執行前後bytes／mtime不變；`test_trusted_historical_manifest_is_supported` 用0.7.0，不改installer舊版限制；`test_missing_extra_and_hash_changes_are_differences` assert對應計數及exit3。

同時建立下列 Step 4 的已知 trust／path／limits／race 測試，再進 Step 2，確保未先寫 guards 才補失敗案例。

```python
def test_exact_manifest_files_match_without_writes(tmp_path):
    skill_dir, manifest, digest = make_installed_package(tmp_path)
    result = verify_installation(skill_dir, manifest, manifest_sha256=digest)
    assert result["status"] == "manifest-files-byte-identical"
    assert result["loaded_version"] == "not-verified"
    assert result["missing_file_count"] == result["extra_file_count"] == result["different_file_count"] == 0
```

同測試在呼叫前後 snapshot 該 synthetic fixture 的 bytes／mtime，assert 相同；不要以實際已安裝 Skill 作 fixture。

- [x] **Step 2: RED**

Run `python -m pytest -q tests/test_verify_installation.py --basetemp <fresh-external-basetemp>`；期望新module/API不存在。

- [x] **Step 3: 先驗信任／manifest，再遍歷目錄**

先拒root／manifest leaf links、相同或nested manifest、source-repo內manifest、錯誤hash格式；bounded讀manifest rawbytes核對expected SHA-256後strict parse。頂層恰name/version/archive/archive_sha256/files，name clin-nav、ASCII X.Y.Z、archive與version一致、archive hash64lowerhex；manifest_version至多80字元以避免無界輸出。records閉合、size非bool、至少SKILL.md，size與總數限額；所有path strict checks、NFC/casefold collision與ancestor conflict在任何installed file open前完成。拒絕空manifest不假稱有Skill。

遍歷root相對entries，root depth0、不含root於entry count，4,096/32 exact接受、超過invalid。lstat與Windows reparse flags先查，任何link/reparse均invalid（含cache）；regular未宣告cache只計ignored，宣告的expected member永遠要hash。未宣告普通extra只計數，不讀內容；emptydirs不影響set比對。unsupported special files invalid。

預期普通檔案用64KiB bounded stream與單檔／總檔限額，stat/open-fstat/post-stat核對 identity、size、mtime；發現變動invalid。raw bytes模式不作內容轉換；canonical mode先bounded讀bytes，再用C1同規則，依canonical size/hash比較。此為best-effort，不承諾防止具修改權限的惡意競態。

- [x] **Step 4: 核對 Step 1 已建立的安全／邊界矩陣**

`test_manifest_trust_is_checked_before_member_open`（badexpectedhash、duplicatekeys、未知欄位、emptyfiles、missingSKILL.md、name/version/archive不符）；所有pathmutation先更新fixture manifest hash，真正測trust後的path validation。`test_links_are_rejected_even_under_ignored_cache` 覆蓋root／member／cache link，Windows可建立時測junction；無權限時真實skip，不冒稱測過。`test_declared_bytecode_is_not_ignored`、`test_extra_files_are_not_opened`、`test_directory_entry_and_depth_limits`、`test_canonical_matches_do_not_claim_bytes_identical`，以及openfstat／poststat／growth race三種。用monkeypatch或syntheticstat精確測reparse判斷，另記真實filesystem tests差異。

```python
def test_empty_manifest_cannot_verify_an_empty_installation():
    payload = {"name": "clin-nav", "version": "0.8.0", "archive": "clin-nav-0.8.0.zip",
               "archive_sha256": "0" * 64, "files": []}
    with pytest.raises(ValueError):
        validate_installation_manifest(payload)
```

- [x] **Step 5: 核對剩餘 RED 或已達 GREEN**

Run 安全／邊界 tests；若尚缺 race／limits／path 行為，應有對應 assertion fail；全部已 GREEN 就記錄結果，不先刪除保護製造假 RED。此步前核對矩陣發現新缺失時，先加測試再修補。

- [x] **Step 6: 補齊 safety guards 並 GREEN**

每種manifest/檔案限額測exact與one-over，不以提高threshold讓測試通過。檔案size與mtime變化導致invalid，不計成普通內容差異；全部 core/safety tests pass。

- [x] **Step 7: 新增 CLI 安全輸出 tests**

`test_cli_exit_status_is_zero_three_or_two`、`test_cli_never_echoes_sensitive_input_or_paths` 覆蓋不合法argv、unreadable、unsafepath、manifest未知欄位sentinel；`test_cli_is_read_only_and_does_not_call_network_or_host` 用禁止呼叫guard與外部synthetictree前後比較。

```python
def test_cli_never_echoes_sensitive_unknown_arguments():
    result = subprocess.run([sys.executable, str(CLI), "--unknown", "SYNTH_SECRET"],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "installation verification failed\n"
```

CLI 常數為 ROOT/scripts/verify_installation.py，ROOT 是 test file 的 parents[1]。

- [x] **Step 8: RED**

Run `python -m pytest -q tests/test_verify_installation_cli.py --basetemp <fresh-external-basetemp>`，期望未完成 CLI 安全行為而 assertion fail。

- [x] **Step 9: 實作 CLI 並 GREEN**

safe argparse allow_abbrev false；summary不同result即0或3，所有invalid只有固定訊息與exit2；不追查host、安裝位置或MCP，CLI tests全 pass。

- [x] **Step 10: 新增選用文件 tests**

在 `tests/test_public_core_docs.py` 加 `test_integrity_diagnostic_is_optional_and_cannot_verify_loaded_version`，檢查兩語comparison指令／manifest trust來源／loaded-not-verified／canonical非byteidentical／ignored bytecode限制，以及正常安裝仍不需Python。

```python
@pytest.mark.parametrize("name", ["installation.md", "installation.zh-TW.md"])
def test_integrity_diagnostic_is_optional_and_cannot_verify_loaded_version(name):
    text = (ROOT / "docs" / name).read_text(encoding="utf-8")
    assert "scripts/verify_installation.py" in text
    assert "--manifest-sha256" in text and "--comparison" in text
    assert "loaded_version: not-verified" in text
    assert "canonical-text" in text
```

再按兩語說明核對 optional／no runtime dependency／bytecode caveat，不要求全文字面相同。

- [x] **Step 11: RED**

Run 新 docs test；期望缺工具／說明而 assertion fail。

- [x] **Step 12: 補雙語簡短章節與 README 連結**

不要預填新開發candidate hash、把main當已發布v0.8.0、或建議co-locatedreceipt作信任根。

- [x] **Step 13: Focused GREEN**

Run `python -m pytest -q tests/test_verify_installation.py tests/test_verify_installation_cli.py tests/test_package_contract.py tests/test_install_local.py tests/test_public_core_docs.py --basetemp <fresh-external-basetemp>`、validate_skill、public_boundary、reproducible gate。期望全部pass／exit0。

- [x] **Step 14: Commit並交共同驗收**

Add新工具、測試及實際文件修改，commit `feat: add optional read-only installed skill verification`，再依索引跑完整gates與全分支review。成功只限contract/content checks；不merge、不push、不發布。
