# Dependabot Version Updates Design

- **Date:** 2026-08-09
- **Target branch:** `codex/dependabot-config`
- **Base branch:** `main`
- **Release impact:** repository maintenance only; do not change `v0.3.0`,
  package metadata, tags, or GitHub Releases

## 1. Objective

Add a small, auditable Dependabot version-update policy for the two dependency
surfaces present in this public repository:

1. Python packaging metadata in the repository root; and
2. GitHub Actions references in `.github/workflows/`.

GitHub repository settings already enable vulnerability alerts and Dependabot
security updates. Those settings can create security-update pull requests
without a configuration file. The new `.github/dependabot.yml` adds scheduled
version updates and gives the repository an explicit, testable update policy.

## 2. Considered Approaches

### A. Security updates only

Keep the current GitHub settings and add no file. This has the smallest change
surface, but it does not schedule non-security version updates or proactively
refresh pinned GitHub Actions commits.

### B. Minimal weekly version updates — selected

Add one root `pip` entry and one `github-actions` entry, both scheduled weekly,
with at most five open version-update pull requests per ecosystem. This covers
all current dependency surfaces while keeping review volume bounded.

### C. Heavily grouped and automatically merged updates

Group packages, assign reviewers and labels, and auto-merge passing changes.
This reduces manual work but couples unrelated upgrades and can turn a
compromised or behavior-changing update into an unattended `main` change. It
is disproportionate for a repository with three declared Python dependencies
and is rejected.

## 3. Configuration Contract

Create `.github/dependabot.yml` with Dependabot schema `version: 2` and exactly
two update entries:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    versioning-strategy: "increase-if-necessary"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

The Python strategy avoids unnecessary lower-bound churn when the existing
constraint already permits a current compatible release. Security updates
remain governed by the enabled repository setting and can still raise a pull
request when a declared range is vulnerable.

The configuration must not include:

- automatic merge behavior;
- private registries or credentials;
- a non-default target branch;
- ignore rules that suppress security fixes;
- labels or reviewers that may not exist in the repository; or
- grouping that combines unrelated dependency changes.

## 4. Safety and Failure Modes

The most damaging failure would be treating dependency automation as approval
to merge. Dependabot may propose a valid version change that alters package or
workflow behavior. Every pull request must therefore remain subject to the
existing strict required checks:

- `test (ubuntu-latest)`;
- `test (windows-latest)`; and
- `compare-packages`.

Passing checks establish repository-contract compatibility, not supply-chain
trust or clinical validity. A maintainer must still inspect the upstream
release, the exact diff, and the pinned GitHub Actions commit before merging.

The second-order maintenance risk is PR noise. Weekly scheduling and a limit of
five open PRs per ecosystem bound that noise. Grouping and auto-merge can be
considered later only after real update volume is observed.

## 5. Verification Design

Extend `tests/test_project_metadata.py` before adding the configuration. The
test must parse `.github/dependabot.yml` using the existing PyYAML dependency
and verify:

- schema version is integer `2`;
- the ecosystem set is exactly `{"pip", "github-actions"}`;
- each entry uses directory `/`, weekly scheduling, and limit `5`;
- the `pip` entry uses `increase-if-necessary`;
- no entry sets `target-branch`, `ignore`, `registries`, `groups`, `assignees`,
  or `reviewers`; and
- no top-level `registries` block exists.

The test must first fail because `.github/dependabot.yml` is absent. After the
minimal configuration is added, run the focused test, the complete pytest
suite, and all required repository gates:

```text
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

Finally, push `codex/dependabot-config`, open a draft pull request against
`main`, and wait for all three hosted required checks. Do not modify the
annotated `v0.3.0` tag or its Release.

## 6. Success Criteria

- The configuration matches the exact contract above.
- The new test demonstrates a RED failure before implementation and passes
  afterward.
- All local tests and four gates pass with no unrelated changes.
- The draft pull request targets `main` and all hosted required checks pass.
- No tag, Release, release asset, package version, or private institutional
  material changes.

## 7. Authoritative References

- GitHub Docs, `About the dependabot.yml file`:
  <https://docs.github.com/en/code-security/concepts/supply-chain-security/about-the-dependabot-yml-file>
- GitHub Docs, `Configuring Dependabot version updates`:
  <https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/configuring-dependabot-version-updates>
- GitHub Docs, `Keeping your actions up to date with Dependabot`:
  <https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/auto-update-actions>
