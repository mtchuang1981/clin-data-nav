# Repository settings operator checklist

This is an operator checklist for an explicitly approved change. This
documentation is not proof that a setting is enabled. Do not
change an external setting, topic, integration, or repository rule merely
because it appears here. Capture the pre-change state, apply only the approved
change, and complete a post-change re-read from GitHub or Zenodo.

Repository used in the examples:
`mtchuang1981/clin-data-nav`. Commands are read-only unless a separately
approved change procedure explicitly says otherwise.

## Required status checks

Before changing a branch rule or ruleset, confirm that the target workflow has
completed successfully on `main`, that an administrator recovery route exists,
and that the check names shown by GitHub are exact. The required status checks
include both platform checks and the package-identity comparator:

- `test (ubuntu-latest)`
- `test (windows-latest)`
- `compare-packages`

GitHub UI path: **Settings → Rules → Rulesets** (or **Settings → Branches** for
an existing branch-protection rule) → the rule targeting `main` → **Require
status checks to pass**. Select only check names that have actually run on the
target commit. Requiring a stale or misspelled name can block every merge.

Read-only verification after an approved change:

```bash
gh api --method GET repos/mtchuang1981/clin-data-nav/branches/main/protection \
  --jq '.required_status_checks'
gh api --method GET repos/mtchuang1981/clin-data-nav/rulesets
```

Also re-open the rule in the UI and verify that the Ubuntu, Windows, and
`compare-packages` checks are all required. The comparator is the stable
workflow job name that proves the two package candidates are byte-identical.
A successful workflow run alone does not prove that a branch rule requires
these checks.

## Repository topics

The proposed exact topic set is:

- `clinical-research`
- `rwe`
- `cdisc`
- `omop`
- `sas`
- `agent-skills`

GitHub UI path: repository main page → **About** gear → **Topics**. Topic names
are public, including topics attached to a private repository, so review the
list before an approved change.

Read-only post-change re-read:

```bash
gh api --method GET repos/mtchuang1981/clin-data-nav/topics --jq '.names'
```

Require exact set equality; a locally documented list is not evidence of the
remote topic state.

## Private vulnerability reporting

GitHub UI path: **Settings → Security → Advanced Security → Private
vulnerability reporting**. Before enabling it, confirm who will receive and
triage private reports. After an approved change, verify both the API state and
the repository **Security → Advisories** page.

```bash
gh api --method GET \
  repos/mtchuang1981/clin-data-nav/private-vulnerability-reporting \
  --jq '{enabled: .enabled}'
```

If the API returns `false`, reporters must follow the non-sensitive
coordination route in [SECURITY.md](../SECURITY.md); never ask them to move a
sensitive payload into a public issue.

## Dependabot security updates

GitHub UI path: **Settings → Security → Advanced Security → Dependabot →
Dependabot security updates**. Confirm the dependency graph and Dependabot
alerts prerequisites before an approved change. Enabling a setting can create
pull requests, so review notification and maintenance capacity first.

Read-only post-change re-read:

```bash
gh api --include --method GET \
  repos/mtchuang1981/clin-data-nav/automated-security-fixes
```

GitHub returns `204 No Content` when automated security fixes are enabled and
`404 Not Found` when they are disabled or unavailable to the caller. Confirm
the UI state as well; an unreadable API response is not evidence of either
state.

## Optional Zenodo evaluation

Treat this as an optional Zenodo evaluation, not a release requirement. Record
these decision inputs before connecting anything:

1. **citation goal** — whether a persistent software-record DOI materially
   improves the project's citation and preservation goals;
2. **maintainer account/integration** — which authorized Zenodo account and
   GitHub integration would own and operate the connection;
3. **deposition ownership** — who controls the record, metadata corrections,
   versioning, and long-term maintenance; and
4. **DOI verification** — how the published deposition and DOI will be re-read
   before any repository metadata claims it.

Zenodo UI path after separate approval: profile menu → **GitHub** → sync the
repository list → enable the selected repository. After a GitHub Release is
archived, open the Zenodo record and verify its owner, files, version, and DOI.
This checklist makes no DOI claim: no DOI is claimed without a verified
deposition. A draft or planned integration is not a DOI record.

Official references:

- [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches)
- [GitHub repository topics](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)
- [GitHub private vulnerability reporting](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository)
- [GitHub Dependabot security updates](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/configure-security-updates)
- [Zenodo GitHub integration](https://help.zenodo.org/docs/github/enable-repository/)
- [Zenodo GitHub release archiving](https://help.zenodo.org/docs/github/archive-software/github-upload/)
