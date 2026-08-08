# Dependabot Version Updates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a bounded weekly Dependabot version-update policy for the
repository's Python and GitHub Actions dependencies, with a regression test and
no automatic merge or Release change.

**Architecture:** A single `.github/dependabot.yml` declares the two current
dependency ecosystems. `tests/test_project_metadata.py` parses the YAML and
enforces the review and noise-control contract independently of GitHub's
external settings.

**Tech Stack:** Dependabot schema v2, YAML, Python 3.11, PyYAML, pytest, GitHub
Actions.

## Global Constraints

- Work only in the isolated `codex/dependabot-config` worktree and branch.
- Preserve the annotated `v0.3.0` tag, GitHub Release, assets, package version,
  changelogs, and citation metadata unchanged.
- Monitor exactly `pip` and `github-actions`, both at directory `/`, weekly,
  with `open-pull-requests-limit: 5`.
- Set `versioning-strategy: increase-if-necessary` only for `pip`.
- Do not configure auto-merge, private registries, target branches, ignore
  rules, grouping, assignees, or reviewers.
- Follow RED→GREEN TDD and use only public repository metadata.

---

### Task 1: Lock the Dependabot policy with a failing metadata test

**Files:**
- Modify: `tests/test_project_metadata.py`
- Test: `tests/test_project_metadata.py`

**Interfaces:**
- Consumes: repository root constant `ROOT` and PyYAML `yaml.safe_load`.
- Produces: `test_dependabot_version_updates_are_bounded_and_reviewable`, the
  executable policy contract for `.github/dependabot.yml`.

- [ ] **Step 1: Add the policy test before the configuration exists**

```python
def test_dependabot_version_updates_are_bounded_and_reviewable():
    path = ROOT / ".github/dependabot.yml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert config["version"] == 2
    assert set(config) == {"version", "updates"}

    updates = config["updates"]
    by_ecosystem = {entry["package-ecosystem"]: entry for entry in updates}
    assert len(updates) == 2
    assert set(by_ecosystem) == {"pip", "github-actions"}

    forbidden_keys = {
        "assignees",
        "groups",
        "ignore",
        "registries",
        "reviewers",
        "target-branch",
    }
    for entry in updates:
        assert entry["directory"] == "/"
        assert entry["schedule"] == {"interval": "weekly"}
        assert entry["open-pull-requests-limit"] == 5
        assert forbidden_keys.isdisjoint(entry)

    assert by_ecosystem["pip"]["versioning-strategy"] == (
        "increase-if-necessary"
    )
    assert "versioning-strategy" not in by_ecosystem["github-actions"]
```

- [ ] **Step 2: Run the focused test and verify RED**

Run:

```text
python -m pytest -q tests/test_project_metadata.py::test_dependabot_version_updates_are_bounded_and_reviewable
```

Expected: FAIL with `FileNotFoundError` for `.github/dependabot.yml`. A syntax,
import, or unrelated failure does not satisfy RED.

### Task 2: Add the minimal Dependabot configuration and reach GREEN

**Files:**
- Create: `.github/dependabot.yml`
- Test: `tests/test_project_metadata.py`

**Interfaces:**
- Consumes: Dependabot configuration schema version 2.
- Produces: weekly version-update requests for root Python metadata and GitHub
  Actions workflows, subject to human review and existing required checks.

- [ ] **Step 1: Add the exact minimal configuration**

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

- [ ] **Step 2: Run the focused test and verify GREEN**

Run:

```text
python -m pytest -q tests/test_project_metadata.py::test_dependabot_version_updates_are_bounded_and_reviewable
```

Expected: `1 passed`.

- [ ] **Step 3: Run the complete metadata test module**

Run:

```text
python -m pytest -q tests/test_project_metadata.py
```

Expected: all metadata tests pass.

### Task 3: Verify the repository and commit the implementation

**Files:**
- Modify: `tests/test_project_metadata.py`
- Create: `.github/dependabot.yml`

**Interfaces:**
- Consumes: the complete repository verification contract.
- Produces: one reviewed implementation commit with no unrelated changes.

- [ ] **Step 1: Run the complete pytest suite and four required gates**

```text
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

Expected: every command exits `0`; pytest reports no failures.

- [ ] **Step 2: Audit the exact diff and immutable Release boundary**

```text
git diff --check
git status --short
git diff -- tests/test_project_metadata.py .github/dependabot.yml
git rev-parse v0.3.0^{tag}
git rev-parse v0.3.0^{commit}
```

Expected: only the test and configuration are uncommitted; the tag object is
`87ca8f379f6751fc465dbcd6ae8f430dabc73523` and the peeled commit is
`6cf9593dd8a520f56e1e6e5b0bf2cb7d40b97791`.

- [ ] **Step 3: Commit only the intended implementation files**

```text
git add -- tests/test_project_metadata.py .github/dependabot.yml
git commit -m "ci: configure Dependabot version updates"
```

### Task 4: Push and validate a draft pull request

**Files:**
- No additional repository files.

**Interfaces:**
- Consumes: committed branch `codex/dependabot-config`.
- Produces: a draft pull request targeting `main`, with hosted check evidence.

- [ ] **Step 1: Confirm authentication, branch scope, and clean status**

```text
gh auth status
git status --short
git log --oneline main..HEAD
```

Expected: authenticated; clean worktree; exactly the design, plan, and
implementation commits are ahead of `main`.

- [ ] **Step 2: Push the branch**

```text
git push -u origin codex/dependabot-config
```

- [ ] **Step 3: Open a draft PR against `main`**

The PR body must explain the two monitored ecosystems, bounded weekly policy,
RED→GREEN evidence, complete local verification, no auto-merge, and unchanged
`v0.3.0` publication.

- [ ] **Step 4: Wait for hosted required checks and inspect annotations**

Expected: `test (ubuntu-latest)`, `test (windows-latest)`, and
`compare-packages` all conclude `success`, with no failure annotations.

- [ ] **Step 5: Re-read PR scope and the immutable Release identities**

Expected: the PR contains only the design, plan, test, and Dependabot
configuration; the published v0.3.0 tag object, peeled commit, Release, assets,
and SHA-256 values remain unchanged.
