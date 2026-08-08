# GitHub Repository Settings Evidence

- **Evidence recorded:** 2026-08-09 (`Asia/Taipei`)
- **Repository:** `mtchuang1981/clin-data-nav`
- **Settings baseline main commit:**
  `14755a9a0d3daabfd252f6fa12ee7361ef56754f`
- **Authorization:** explicit approval for GitHub external settings 1-4

This report records external repository settings after the approved mutation
and a fresh API re-read. It supersedes only the current-state observation in
the earlier same-day publication report; it does not rewrite that historical
record or change the immutable v0.3.0 publication.

## Pre-change checks

Before changing settings, the authenticated account had repository admin and
push permission. The baseline main commit completed validation successfully:

- workflow run ID: `31266889594`;
- URL:
  `https://github.com/mtchuang1981/clin-data-nav/actions/runs/31266889594`;
- head SHA: `14755a9a0d3daabfd252f6fa12ee7361ef56754f`;
- conclusion: `success`; and
- observed job names: `test (ubuntu-latest)`, `test (windows-latest)`, and
  `compare-packages`.

The repository initially had no topics, no branch protection, rulesets: none,
private vulnerability reporting disabled, vulnerability alerts disabled, and
Dependabot security updates disabled.

## Repository topics

The approved exact topic set was written and then re-read from GitHub:

- `agent-skills`
- `cdisc`
- `clinical-research`
- `omop`
- `rwe`
- `sas`

No extra or missing topic was observed after the write.

## Private vulnerability reporting

Private vulnerability reporting: enabled.

The post-change API returned `enabled: true`. The public security policy now
directs sensitive reports to:

`https://github.com/mtchuang1981/clin-data-nav/security/advisories/new`

Public issues remain limited to non-sensitive coordination requests or
ordinary concerns containing no sensitive material.

## Dependabot

The prerequisite check initially returned HTTP 404 because vulnerability
alerts were disabled. The approved workflow then enabled the prerequisite and
security-update service in that order.

- vulnerability alerts: enabled;
- Dependabot security updates: enabled; and
- paused: false.

The repository `security_and_analysis` response also reported
`dependabot_security_updates.status: enabled`. Enabling this service may cause
GitHub to create future security-update pull requests; maintainers must review
and maintain them rather than treating enablement as completed remediation.

## Main branch protection

The repository uses branch protection rather than a repository ruleset for
the approved required-check policy. Post-change state:

- branch protection: enabled;
- strict: true;
- required checks: `test (ubuntu-latest)`, `test (windows-latest)`, and
  `compare-packages`;
- enforce administrators: false;
- force pushes: disabled;
- branch deletion: disabled;
- pull-request reviews: not required by this rule; and
- rulesets: none.

Keeping `enforce administrators: false` preserves an administrator recovery
route if a required context is renamed or GitHub Actions is unavailable. It
does not weaken the checks for ordinary writers. The rule can be re-read at
`repos/mtchuang1981/clin-data-nav/branches/main/protection` before any future
change.

## Publication boundary

No tag or GitHub Release was changed. In particular, the annotated `v0.3.0`
tag object, peeled release commit, Release page, ZIP, manifest, asset IDs,
sizes, and SHA-256 values remain the immutable publication identities recorded
in `2026-08-09-v0.3.0-publication.md`.

Zenodo integration, DOI metadata, author identity enrichment, Skill icons,
brand assets, and a bundled `build-rwe-sap` remain outside this settings
change.
