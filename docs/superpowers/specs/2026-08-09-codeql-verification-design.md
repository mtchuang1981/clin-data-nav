# CodeQL Default Setup Verification Design

- **Date:** 2026-08-09
- **Target branch:** `codex/codeql-verification`
- **Base branch:** `main`
- **Baseline commit:** `0aff8038bb52457e9868fab9ea9a43dda9b4235c`
- **Release impact:** repository guidance and evidence only; do not change the
  immutable `v0.3.0` publication

## 1. Objective

Record the approved CodeQL default-setup state and its first successful scan
as durable, testable repository evidence. Use the documentation pull request
to observe CodeQL behavior on a real PR before considering any change to
`main` branch protection.

The external setting is already enabled. This change must not create an
advanced CodeQL workflow, reconfigure default setup, dismiss alerts, or make
CodeQL a required status check.

## 2. Considered Approaches

### A. Keep the evidence only in GitHub

This creates no repository change, but later maintainers cannot distinguish a
verified setting from an undocumented UI state or reconstruct the approval and
initial-scan evidence from the repository.

### B. Add a guide update, dated evidence, and metadata contract — selected

Add a short CodeQL section to the existing repository-settings guide, create a
separate dated verification record, and protect the factual contract with a
metadata test. A draft PR then supplies a real PR-level CodeQL observation.

### C. Add CodeQL to required checks now

This would enforce the new checks immediately. It is rejected because only one
`main` scan has been observed, check names and availability have not yet been
validated on a repository-owned pull request, and an unstable required context
could block maintenance.

## 3. Repository Changes

### 3.1 Settings guidance

Update `docs/repository-settings.md` with a `CodeQL default setup` section that
states the approved and API-verified configuration:

- state: `configured`;
- languages: `actions` and `python`;
- query suite: `default`;
- threat model: `remote`;
- runner type: `standard`;
- schedule: `weekly`; and
- CodeQL checks are intentionally not included in current required checks.

The guide must explain that a successful scan and zero results do not prove
the repository secure. Maintainers must inspect alerts and scan health, and
must not dismiss an alert solely to obtain a green check.

### 3.2 Dated verification evidence

Create `docs/verification/2026-08-09-codeql-default-setup.md`. Keep it separate
from `2026-08-09-github-settings.md`, which remains the historical evidence for
the earlier approved settings 1–4.

The new record must identify:

- explicit user approval to enable CodeQL;
- baseline and scanned commit
  `0aff8038bb52457e9868fab9ea9a43dda9b4235c`;
- default-setup configuration listed in section 3.1;
- initial dynamic run ID `31269886134` and its GitHub URL;
- successful jobs `Analyze (actions)` (`93133943497`) and
  `Analyze (python)` (`93133943498`);
- Actions analysis ID `1590243272`, 17 rules, zero results;
- Python analysis ID `1590243578`, 43 rules, zero results;
- zero open code-scanning alerts and zero job annotations, warnings, or
  failures at the final API re-read; and
- the unchanged current required contexts: `test (ubuntu-latest)`,
  `test (windows-latest)`, and `compare-packages`.

The report must preserve the immutable v0.3.0 tag, Release, ZIP, manifest, and
SHA-256 boundary. It must distinguish historical observation from a promise
that future scans remain clean.

### 3.3 Metadata contract

Extend `tests/test_project_metadata.py` before changing the two documentation
files. The test must read the guide and dated record as UTF-8 text and enforce
the durable facts that would otherwise become easy to remove or misstate:

- the guide has a CodeQL default-setup section and identifies both languages,
  `default`, `remote`, `standard`, and `weekly`;
- the guide explicitly states that CodeQL is not currently a required check;
- the dated evidence contains the exact commit, run URL, job IDs, analysis
  IDs, rule counts, and zero-result/zero-alert observations above;
- the evidence identifies all three unchanged required contexts; and
- neither document claims that zero findings prove security.

The focused test must first fail because the dated evidence does not exist and
the settings guide has no CodeQL section. Only then may the documentation be
added.

## 4. Pull Request Observation

After local verification, push `codex/codeql-verification` and open a draft PR
against `main`. The PR is successful only if the following complete without
failure annotations:

- `test (ubuntu-latest)`;
- `test (windows-latest)`;
- `compare-packages`;
- `Analyze (actions)`; and
- `Analyze (python)`.

If one or both CodeQL checks do not appear, fail, or report an alert, stop and
record the actual state. Do not change CodeQL configuration, dismiss an alert,
or add a required context as a workaround.

Passing this PR establishes only that default setup executes successfully on
one repository-owned PR. CodeQL must remain outside required checks until the
user separately approves that branch-protection mutation after additional
observation.

## 5. Verification

Follow RED→GREEN for the metadata contract, then run:

```text
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

Before commit and PR creation, review `git diff`, run `git diff --check`, and
confirm only the design, implementation plan, settings guide, dated evidence,
and metadata test are in scope.

## 6. Failure Modes and Safeguards

- **Historical evidence drift:** exact IDs and configuration are asserted by
  the metadata contract; future state belongs in a new dated record.
- **False assurance:** both guide and evidence explicitly reject interpreting
  zero results as proof of security.
- **Branch lockout:** CodeQL is not added to required contexts in this change.
- **Alert suppression:** no alert dismissal is authorized.
- **Public-boundary breach:** record only public repository settings and scan
  metadata; do not add institutional schema, adapters, or private metadata.
- **Release mutation:** do not edit, move, replace, or republish `v0.3.0`.

## 7. Success Criteria

- The guide and dated record accurately reflect fresh GitHub API evidence.
- The metadata test demonstrates the expected RED failure and then passes.
- The complete local suite and all four gates pass.
- The draft PR runs all three existing checks and both CodeQL language checks
  successfully with no failure annotations.
- Required contexts and the v0.3.0 publication remain unchanged.

## 8. Authoritative References

- GitHub Docs, `Configuring default setup for code scanning`:
  <https://docs.github.com/code-security/code-scanning/automatically-scanning-your-code-for-vulnerabilities-and-errors/setting-up-code-scanning-for-a-repository>
- GitHub Docs, `CodeQL query suites`:
  <https://docs.github.com/en/code-security/concepts/code-scanning/codeql/codeql-query-suites>
- GitHub REST API, `Update a code scanning default setup configuration`:
  <https://docs.github.com/en/rest/code-scanning/code-scanning>
