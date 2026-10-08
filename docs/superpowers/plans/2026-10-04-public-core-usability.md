# ClinNav Public-Core Usability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 依已核准規格完成五項公開端優化，不改既有 ledger schema、發布資產或私有 adapter。

**Architecture:** 分為三份有明確相依的子計畫，各自產生可測試的交付。文件／缺口／回饋先完成，audit 新增共用安全 JSON reader，安裝診斷再使用該 reader 與狹窄的既有套件 helper。共同驗收不把本機測試當成遠端 CI 或真人效果證據。

**Tech Stack:** Python 標準函式庫、既有 pytest／PyYAML、Markdown、GitHub Issue Forms；不新增第三方 runtime dependency。

**Spec:** [2026-10-04-public-core-usability-design.md](../specs/2026-10-04-public-core-usability-design.md)，使用者於 2026-10-04 回覆「繼續」，核准進入實作計畫。

## Global Constraints

- 保留 evidence ledger schema `1`、既有 checker 判定與退出碼。
- 不修改私有 adapter、不讀私有結構或資料、不與 OMOP 1.1 分支混合。
- 不執行真人或模型 campaign、不啟動自動網路查證或排程。
- 不變更版本號、CHANGELOG、已發布 tag 或 Release assets；merge、push 與發布不包含在本規格中。
- 只使用合成資料；實際 ledger／audit、來源副本及 raw responses 不進 Git。
- Python 仍不是一般安裝或日常使用的必要條件；新增工具僅標準函式庫。
- 專案 `pyproject.toml` 要求 `>=3.11,<3.12`；既有本機 3.13 基線是診斷資訊，不能代替受支援 runtime 驗證。
- 所有行為變更先 RED，再 GREEN；RTK 不替代退出碼、完整 diff 或雜湊。

## Review Focus

1. 混合歷史版本文件會讓使用者下載錯誤資產：A1 的版本區段測試限制範圍，不改正當的歷史說明。
2. 有效但未評估的證據被過早升級：B2 的 union／scope／request-provided N/A 負向測試保留 review。
3. 重複 JSON keys／巨大數字讓解析與雜湊分歧：B1 的嚴格 parser 與 bounded-read 測試拒絕，不回顯輸入。
4. bytecode 排除、路徑正規化或讀取競態讓安裝診斷過度承諾：C2 驗證 manifest 範圍、ignored count 與 fail-closed。
5. 回饋入口被誤當研究資料收集或強迫虛構問題：A3 驗證 optional textarea、no default、雙語警語與匿名角色界線。

---

## 子計畫與執行順序

| 順序 | 計畫 | 交付與相依 |
| --- | --- | --- |
| 1 | [A：文件、缺口與回饋](2026-10-04-public-core-docs-feedback.md) | A1 文件修正；A2 缺口／範例；A3 雙語 Issue Forms。三項可獨立 review，但共享文件修改要依序落地。 |
| 2 | [B：公開 evidence audit](2026-10-04-public-evidence-audit.md) | B1 strict JSON reader；B2 audit、CLI、契約與路由。B2 使用 B1；template／Skill 路由以 A2 為基底。 |
| 3 | [C：安裝完整性診斷](2026-10-04-installed-skill-integrity.md) | C1 窄套件 helper 與相容性；C2 唯讀診斷與文件。C2 使用 B1、C1。 |
| 4 | 本文件的共同驗收 | 完整 gates、aggregate-only 紀錄、全分支 review；不自動合併或發布。 |

執行前先讀 Spec、此索引與該子計畫。工作區固定使用既有、已附加的 `codex/public-core-usability` 隔離分支；基底 main 為 `a8b9976dbbf62fec250fb7c571f3e714ce0b360f`，設計 commit 為 `aa012c665f20e01e5eb3e254dbd3473fe65a84d9`。不要在 `codex/omop-connector-1-1` 或 E 槽原 checkout 修改產品檔案。

使用者已核准 Native 執行；A1–C2 已於本機隔離分支完成。一次獨立全分支
review 發現的 URL 邊界問題以 RED→GREEN 修補；共同驗收與限制記錄於
[本機驗證紀錄](../../verification/2026-10-04-public-core-usability-local.md)。
本輪不 merge、push 或發布；main 與既有發布資產保持不變。

## 測試執行環境

- [x] 確認分支、乾淨工作樹與只有預期的本機規格／計畫 commits；保存 `git status --short --branch` 與 `git rev-parse HEAD` 的結果。
- [x] 以唯讀方式確認既有 Python 3.11（例如 `py -0p`，或已配置的 dependency runtime）。若沒有可用版本，不下載、不安裝，記錄未完成的受支援 runtime gate，請求後續方向；不得把 3.13 通過當作等效。
- [x] pytest 的 basetemp 必須是所有 Git repository 之外、尚不存在的專用 GUID 目錄；在 Windows 可使用既有 writable visualization root 下的專用目錄。不可重用未知非空目錄，pytest 可能移除既有 basetemp。
- [x] 後續 RED／GREEN 指令中的 `<fresh-external-basetemp>` 每次替換成新的絕對路徑。執行 `rtk proxy <python3.11> -m pytest ... --basetemp <fresh-external-basetemp>`；使用支援 runtime，不改測試以遷就環境。

已知另案待辦：空的 nested `.git` 位於有效祖先 repo 內時，public-boundary checker 可能接受祖先的 Git 成功結果，未檢查實際 top-level。此計畫不修補此問題、不弱化兩項既有測試；所有 baseline 使用 repo 外 basetemp，交付限制明示該變體未修復。

## 共同驗收與 aggregate-only 交付

**Files:**
- Create: `docs/verification/2026-10-04-public-core-usability-local.md`
- Review: 三份子計畫列出的程式、Skill、references、tests、docs、forms；`agents/openai.yaml`、Eval catalog、evaluator 與 fixtures。

**Interfaces:**
- Consumes: A1–C2 的本機 commits、新 audit 與 installation CLI、既有 report renderers。
- Produces: 僅含 commit/runtime、命令、退出碼、計數、套件雜湊、限制的驗證紀錄；不保存輸入、回答、來源文字或私有路徑。

- [x] **Step 1: 在受支援 Python 3.11 執行完整驗證**

```text
python -m pytest -q --basetemp <fresh-external-basetemp>
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
python scripts/render_eval_summary.py --check
python scripts/render_effectiveness_report.py --summary evals/effectiveness/examples/synthetic-summary.json --english evals/effectiveness/examples/synthetic-report.md --traditional-chinese evals/effectiveness/examples/synthetic-report.zh-TW.md --check
python scripts/render_simulation_benchmark.py --summary evals/benchmark/examples/synthetic-summary.json --english evals/benchmark/examples/synthetic-report.md --traditional-chinese evals/benchmark/examples/synthetic-report.zh-TW.md --check
git diff --check
```

每個指令分別檢查退出碼，不能以最後指令掩蓋前面的失敗。期望全部 exit `0`；pytest 的平台 skips 各別列明。若現行 deterministic Eval snapshots 漂移，先查根因，不重算門檻、不重寫歷史 benchmark，停止完成宣告。

- [x] **Step 2: 驗證 source／packaged CLI parity 與重新包裝**

用純合成 repository 外資料分別執行 source 與解壓後 Skill 的 audit CLI：完整紀錄 `0`、待審閱 `3`、invalid `2` 三種狀態的摘要／退出碼一致；ZIP 解壓後在外部測試目錄執行，不讀已安裝的真實私人 Skill。重建兩次 development candidate，逐位元比較 ZIP／manifest；不可覆寫外部已發布 v0.8.0 產物。

- [x] **Step 3: 檢閱完整 diff 並完成全分支 review**

核對無私有內容、raw answers／logs／實際 audit 入 Git；無版本、CHANGELOG、release.yml、OMOP 1.1 或 benchmark 歷史意外變動。Native 執行方式在此採一次獨立全分支 review；Subagent-driven 另有逐 task review。Reviewer 只讀公開材料，不執行未授權外部系統存取。

- [x] **Step 4: 保存 aggregate-only 紀錄與本機 commit**

紀錄只聲稱契約／deterministic checks 與已實際驗證的 runtime。明示 checker 不驗證來源真實／語意、安裝工具不證明 loaded version、root-discovery 另案未修，以及遠端 Windows／Ubuntu CI 尚未執行。`git add -- docs/verification/2026-10-04-public-core-usability-local.md` 後 commit `docs: record public-core local verification`；核對乾淨工作樹，回報待外部授權的 merge／push／CI，不自動執行。
