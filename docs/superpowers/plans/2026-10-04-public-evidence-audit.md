# Public Evidence Audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增加可選、離線、強綁定的 companion audit，忠實保存來源查閱與 claim-fit 的人工判斷。

**Architecture:** B1 提供 leaf strict JSON reader，B2 在既有 ledger validator／summary 上做相容的獨立 audit。Repository wrapper 與 installable CLI 使用同一份純函式；來源真假與 notes 語意仍由人工審閱，不靠 regex 或網路自動查核。

**Tech Stack:** Python 3.11 標準函式庫、既有 pytest；不新增依賴。

**Spec:** [已核准設計](../specs/2026-10-04-public-core-usability-design.md)，第一節；[共同執行約束](2026-10-04-public-core-usability.md)。

## Global Constraints

- 保留 evidence ledger schema `1`、既有 checker 判定與退出碼；不得改舊 parser 的接受集合。
- Audit 每個輸入至多 262,144 bytes，最多 100 sources、100 claims，100 checks/claim、20 entry points/source，JSON 深度至多 12。
- ID 至多 80 字元、URL 至多 2,048 字元、位置／notes 至多 4,000 字元。
- `prepared_on <= checked_on <= --as-of`；日期未知不可猜，實際審閱／查找日期不得晚於 checked_on。
- stdout/stderr 不回顯 URL、title、claim、notes、未知欄位、輸入路徑或 exception。
- 更正／撤稿採人工 notes 與 claim-fit 審閱；不另建 integrity 狀態機，不改 pilot-failed 歷史結果。

## Review Focus

1. escape 字串中的括號或巨大 nesting 被 depth scanner 算錯：B1 測試 escaped quote／brace 與 12/13 邊界。
2. `1e999` 合法 JSON 轉成 infinity、duplicate key 被 last-value-wins：B1 必須 fail closed。
3. claim 引用兩個來源卻只驗一個 locator：B2 必須 invalid，集合恰好相符，不能由一個布林值掩蓋。
4. historical scope 把 not-performed 偽裝成不適用：B2 各 scope 都留 review；current not-applicable 為 invalid。
5. request-provided N/A 或 audit appropriate 洗掉 ledger 原有 review items：B2 的 union 測試保留 exit 3，包括 partial-support。

---

### Task B1: 可重用的 bounded strict JSON reader

**Files:**
- Create: `skills/clin-nav/scripts/bounded_json.py`、`tests/test_bounded_json.py`

**Interfaces:**
- Produces: `read_bounded_bytes(path: Path, *, max_bytes: int, chunk_bytes: int = 65536) -> bytes`
- Produces: `parse_strict_json(data: bytes, *, max_bytes: int, max_depth: int = 12) -> object`
- Produces: `read_strict_json(path: Path, *, max_bytes: int, max_depth: int = 12) -> object`
- 三者對格式／限額錯誤 raise `ValueError`（固定無內容訊息）；OS errors 交由呼叫 CLI 安全轉換。max_bytes/max_depth 必須正整數、拒絕 bool。沒有 network 或 write。

- [x] **Step 1: 新增失敗測試**

`test_limit_accepts_exact_bytes_and_rejects_one_extra` assert `{}` 在 max_bytes=2 接受、1 拒絕；`test_strict_json_rejects_duplicate_keys_and_nonfinite_numbers` 參數化 duplicate keys、NaN、Infinity、-Infinity、1e999。`test_depth_counts_containers_not_escaped_text` assert 12 層接受、13 層拒絕；含 escaped quote／brace 的字串不增加 depth。`test_reader_never_uses_unbounded_read` 用 guarded file object assert 每次 read 大小為正且不超過 chunk_bytes／remaining+1；檔案成長超限時仍拒絕。另測 invalid UTF-8、BOM、trailing JSON、非常長整數、錯誤參數與敏感 sentinel 不進 exception 字串。

```python
@pytest.mark.parametrize("raw", [b'{"a":1,"a":2}', b'NaN', b'Infinity', b'-Infinity', b'1e999'])
def test_strict_json_rejects_duplicate_keys_and_nonfinite_numbers(raw):
    with pytest.raises(ValueError):
        parse_strict_json(raw, max_bytes=262144, max_depth=12)

def test_limit_accepts_exact_bytes_and_rejects_one_extra():
    assert parse_strict_json(b'{}', max_bytes=2) == {}
    with pytest.raises(ValueError):
        parse_strict_json(b'{}', max_bytes=1)
```

- [x] **Step 2: RED**

Run `python -m pytest -q tests/test_bounded_json.py --basetemp <fresh-external-basetemp>`；期望新 module 尚不存在，不是 pytest 環境錯誤。

- [x] **Step 3: 實作 reader**

先 bounded bytes 與 UTF-8 decode，再用 string-aware scan 核對 container 深度（根 object/array 深度為 1），最後 json.loads 以 object_pairs_hook 拒絕 duplicate keys、parse_constant 拒絕非有限常數，並迭代檢查溢出 float 的 isfinite。統一捕捉解析／遞迴錯誤為固定 ValueError；不輸出 raw exception。不要用全檔無限 read，不修改既有 ledger／installer reader。

- [x] **Step 4: GREEN**

Run `python -m pytest -q tests/test_bounded_json.py tests/test_evidence_ledger.py tests/test_install_local.py --basetemp <fresh-external-basetemp>`；期望新 reader pass、舊 consumers 接受行為不變。

- [x] **Step 5: Commit**

Add 兩新檔，commit `feat: add bounded strict JSON input reader`。

### Task B2: Audit 契約、離線 CLI 與可選 Skill 路由

**Files:**
- Create: `skills/clin-nav/scripts/evidence_audit.py`、`skills/clin-nav/scripts/check_evidence_audit.py`、`scripts/check_evidence_audit.py`
- Create: `skills/clin-nav/references/evidence-audit.md`、`skills/clin-nav/references/evidence-audit-example.json`
- Create/Test: `tests/test_evidence_audit.py`、`tests/test_evidence_audit_cli.py`
- Modify: `skills/clin-nav/SKILL.md`、`skills/clin-nav/references/evidence-ledger.md`、`skills/clin-nav/references/evidence-output-template.md`
- Review/Test: `skills/clin-nav/agents/openai.yaml`、`tests/test_evidence_ledger.py`、`tests/test_skill_contract.py`

**Interfaces:**
- Consumes: B1 reader；既有 `validate_evidence_ledger(payload: object, *, as_of: str) -> list[str]` 與 `summarize_evidence_ledger(payload: dict, *, as_of: str) -> dict`。
- Produces: `audit_ledger_sha256(ledger: dict) -> str`（呼叫者先驗合法 ledger）；`validate_evidence_audit(ledger: object, audit: object, *, as_of: str) -> list[str]`（固定 code diagnostics）；`summarize_evidence_audit(ledger: dict, audit: dict, *, as_of: str) -> dict`（invalid 則固定 ValueError）。
- Produces: installable `main(argv: list[str] | None = None) -> int`；兩 CLI 接受 `--ledger`、`--audit`、`--as-of`，退出碼 0/3/2，錯誤訊息固定 `evidence audit validation failed\n`。

摘要頂層固定為 schema_version、ledger_id、as_of、status、ledger_status、source_count、claim_count、source_review_items、claim_review_items。Items 為 `{source_id|claim_id, reasons}`，IDs／reason codes 按字典序排序去重，無原始 text 或 URLs。status 為 recorded-checks-complete／needs-review；ledger_status 保留 complete／review-required。

Audit reason codes：source-not-opened、scope-not-assessed、version-unknown、status-basis-missing、newer-search-unavailable、newer-search-not-performed、current-source-superseded、current-source-in-development、current-newer-found、locator-not-verified、authority-insufficient、authority-conflicted、authority-not-assessed、support-overstated、support-understated、support-not-assessed。原 ledger summary 的 source lists 依序映為 ledger-review-due、ledger-freshness-unknown、ledger-source-not-reviewed、ledger-source-unavailable、ledger-source-unidentified；claim lists 映為 ledger-partial-support、ledger-unsupported、ledger-not-assessed。任一 item 存在即 needs-review。

- [x] **Step 1: 新增正向與綁定的 RED tests**

在 `tests/test_evidence_audit.py` 定義 `complete_pair() -> tuple[dict, dict]`，用純 SYNTH、example.org、2026-10-01 ledger、2026-10-02 checked、future due、current/opened/current/no-newer-found／全部 locator verified/fit appropriate。`test_complete_pair_has_recorded_checks_complete` assert validator=[]、status 完成。`test_hash_ignores_object_key_order_but_not_array_or_claim_changes` assert dict key reorder digest 相同，text／array reorder 不同；改文字不更新 audit hash 應含固定 code ledger-hash-mismatch。`test_audit_requires_exact_ids_and_per_source_locators` 參數化 missing/extra/duplicate sources、claims、source_checks，全部 invalid；兩來源各有 locator 才完整。

同時建立下列 Step 4 的全部已知 core／安全測試，再進 Step 2；不得先寫完整 guards 才補其測試。

```python
def test_complete_pair_has_recorded_checks_complete():
    ledger, audit = complete_pair()
    assert validate_evidence_audit(ledger, audit, as_of="2026-10-02") == []
    assert summarize_evidence_audit(ledger, audit, as_of="2026-10-02")["status"] == "recorded-checks-complete"
```

- [x] **Step 2: RED**

Run `python -m pytest -q tests/test_evidence_audit.py --basetemp <fresh-external-basetemp>`；期望新 module／API 缺失。不要先寫 stub 讓測試忽略功能。

- [x] **Step 3: 實作純函式契約與判定**

精確欄位與 enums 逐一採 Spec 第一節，不增 optional 欄位；hash 用指定 UTF-8 sorted-key JSON、保留 array 順序。先驗 ledger、限額、closed rows、dates、URLs、ID 集合與 access 相容矩陣，再算 summary。URL 只做字串／urlsplit 語法檢查，不 DNS resolve；拒絕 credentials、query、fragment、localhost、IP、單節點 host，未知 retrieval/status basis 允許 null。不要解析 notes 判斷真偽。

- [x] **Step 4: 核對 Step 1 已建立的狀態／負向／限額矩陣**

`test_ledger_review_items_are_never_cleared_by_audit` 覆蓋 due、partial-support、unsupported、not-assessed、未知 identifier；request-provided 無來源 N/A 仍 needs-review。`test_freshness_is_scope_aware`：historical/superseded + no-newer-found 完成，current/superseded needs-review；所有 scope not-performed needs-review；current/not-applicable invalid；historical/newer-found 不單獨阻擋。`test_recorded_overstatement_is_valid_but_needs_review` 保留 row 並回3；access 矩陣矛盾與 verified 無位置 invalid。參數化每個 Spec 限額的 exact/over 邊界、日期倒序、非 ISO、未來 observed date、未知欄位、bool／非字串 enums／空必要文字，verify不截斷。

Historical／development 的 fixture 同時在 ledger applicability 明示範圍並重算 audit hash，不示範沒有依據的 scope 改標。此步核對覆蓋；發現新遺漏才新增測試，不能在修補前先改 body。

```python
def test_recorded_overstatement_is_valid_but_needs_review():
    ledger, audit = complete_pair()
    audit["claims"][0]["support_fit"] = "overstated"
    assert validate_evidence_audit(ledger, audit, as_of="2026-10-02") == []
    summary = summarize_evidence_audit(ledger, audit, as_of="2026-10-02")
    assert summary["status"] == "needs-review"
    assert "support-overstated" in summary["claim_review_items"][0]["reasons"]
```

- [x] **Step 5: 核對剩餘 RED 或已達 GREEN**

Run core test module；若仍缺狀態處理，應有對應 assertion fail。全部已 GREEN 就記錄結果；不先削弱實作製造假 RED。

- [x] **Step 6: 補齊純函式規則並 GREEN**

只補前一步證明缺失的契約／summary 規則，core tests 全 pass。用參數化縮短測試，勿把每個 enum 寫成一次相同流程。

- [x] **Step 7: 新增 CLI tests**

`test_repository_and_packaged_cli_have_same_summary_and_exit` 對 complete/review/invalid 三狀態跑兩入口。`test_cli_never_opens_network_or_echoes_input` 以 synthetic sentinel 放在 claim/notes／unknown field／argv，assertstdout+stderr無 sentinel 或 path，invalid exactly固定訊息。`test_cli_rejects_inputs_inside_repository_or_installed_skill` 覆蓋兩輸入各自 protected-root 及 resolved path；外部 regular inputs 才接受。

```python
def test_cli_never_echoes_unknown_arguments():
    result = subprocess.run([sys.executable, str(CLI), "--unknown", "SYNTH_SECRET"],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == "evidence audit validation failed\n"
```

CLI 常數定義為 ROOT/scripts/check_evidence_audit.py，ROOT 為測試檔的 parents[1]；packaged CLI 用 ROOT/skills/clin-nav/scripts/check_evidence_audit.py。

- [x] **Step 8: RED**

Run `python -m pytest -q tests/test_evidence_audit_cli.py --basetemp <fresh-external-basetemp>`，期望未實作 CLI／安全訊息的 assertions fail。

- [x] **Step 9: 實作安全 CLI 並 GREEN**

CLI 只用 B1 reader、core APIs 和既有可信 script-directory import pattern；main return int，兩入口 __main__ 都 `raise SystemExit(main())`。未識別參數與 abbreviation 拒絕，不回顯 ArgParse error 原文；CLI tests 全 pass。

- [x] **Step 10: 新增契約文件、純合成 example 與可選路由 tests**

`test_audit_reference_example_is_synthetic_valid_and_packaged`：example ledger 使用既有 evidence-ledger-example.json，checked_on 不早於其 prepared_on，hash 實際核對、配對 source/claim IDs 恰好一致；不是重做真實 pilot。`test_audit_route_is_optional_and_preserves_old_ledger_contract` 檢查 quick 沒有 audit 必填、舊 ledger JSON／schema 不變、Skill 只在 requested freshness/citation audit route 讀新 reference。

```python
def test_audit_reference_example_is_synthetic_valid_and_packaged():
    refs = ROOT / "skills/clin-nav/references"
    ledger = json.loads((refs / "evidence-ledger-example.json").read_text(encoding="utf-8"))
    audit = json.loads((refs / "evidence-audit-example.json").read_text(encoding="utf-8"))
    assert audit["ledger_sha256"] == audit_ledger_sha256(ledger)
    assert validate_evidence_audit(ledger, audit, as_of=audit["checked_on"]) == []
```

同測試再 build synthetic candidate，assert ZIP包含兩個新 scripts、bounded_json 與 audit reference/example。

- [x] **Step 11: RED**

Run 新 doc/example/route tests，期望缺文件／路由失敗。

- [x] **Step 12: 新增 reference、example、必要路由並 GREEN**

例子明示全部假設人工結果是合成契約資料。套件應自動包含 scripts/references，不變更 agents policy.products 或 implicit invocation；相關測試全 pass。

- [x] **Step 13: 完整 focused GREEN、parity 與相容性**

Run `python -m pytest -q tests/test_bounded_json.py tests/test_evidence_audit.py tests/test_evidence_audit_cli.py tests/test_evidence_ledger.py tests/test_skill_contract.py --basetemp <fresh-external-basetemp>`、validate_skill、public_boundary、reproducible package；期望全 pass／exit0。

- [x] **Step 14: Commit**

Add 本 task 新檔與實際修改的路由／tests，commit `feat: add opt-in offline evidence audit`。不得改既有 pilot aggregate record 或 raw external artifacts。
