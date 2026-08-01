# Public Trust Repair v0.2.2 Design

**Date:** 2026-07-29  
**Status:** Approved design  
**Target release:** `v0.2.2`

## 1. Purpose

Repair the public trust boundary identified by the new-user assessment before
expanding the Skill's clinical-research behavior. The release must prove that a
fresh contributor environment can install the declared development
dependencies, that all tests and gates run on Linux and Windows, and that a
GitHub Release can be created only through a fail-closed validation path.

This is the first phase of a larger optimization effort. The second phase,
targeting `v0.3.0`, will separately design the four output depths, broader
beginner information architecture, glossary expansion, and additional Eval
coverage. Those items are not abandoned; they are excluded here so that a
patch release does not mix public-build repairs with unvalidated behavior
changes.

## 2. Verified baseline

The following facts were revalidated on 2026-07-29:

- Local `main` is clean at commit
  `047eb61306b02c9f20eab762881fa28aefa93647`, which is tagged `v0.2.1`.
- The current `pyproject.toml` has project and development dependencies but no
  PEP 517 build backend or explicit package discovery rule.
- A fresh editable install fails because setuptools discovers multiple
  top-level flat-layout directories, including `evals` and `skills`.
- `.github/workflows/validate.yml` runs only on Ubuntu. Its install step fails,
  so the test suite and the three later repository gates are skipped.
- The native Windows suite has 168 collected tests: 164 pass and four platform
  simulation tests fail because `_rename_no_replace()` chooses the Windows
  branch from the real `os.name` before the tests' simulated `sys.platform`.
- `evals/cases.yaml` contains 11 catalog cases while `evals/README.md` reports
  only the three cases with checked-in baseline and forward result fixtures.
- `.baoyu-skills/baoyu-translate/EXTEND.md` is tracked but is unrelated to the
  public project.

These are release-blocking evidence gaps. Passing historical local tests or
having a public `v0.2.1` Release does not override them.

## 3. Scope

### 3.1 In scope

- Make `python -m pip install -e ".[dev]"` succeed in fresh Python 3.11
  environments.
- Preserve the existing atomic, no-overwrite local installer while making its
  platform tests portable.
- Run the complete verification set on both Ubuntu and Windows in GitHub
  Actions.
- Add a manually dispatched, fail-closed GitHub Release workflow.
- Add a 60-second first-success path and explicit command/runtime boundaries to
  both READMEs.
- Clarify the 11-case Eval catalog versus the three checked-in scored fixture
  pairs and prevent documentation drift.
- Remove the unrelated `.baoyu-skills` configuration.
- Add a dated `v0.2.1` revalidation report without altering the historical
  `v0.1.0` verification record.
- Synchronize all repository version surfaces to `0.2.2` and prepare release
  notes.

### 3.2 Out of scope

- Creating, moving, or overwriting a Git tag or GitHub Release.
- Pushing commits to GitHub without separate user approval.
- Changing GitHub branch-protection settings automatically.
- Adding institution-specific schemas, adapters, data dictionaries, or
  production SQL.
- Automatically installing the optional `build-rwe-sap` Skill.
- Redesigning the Skill's four output depths or claiming broader clinical
  validity from the existing Eval fixtures.

## 4. Architecture and components

### 4.1 Python packaging

Add a PEP 517 setuptools build declaration and an explicit package list to
`pyproject.toml`:

- use `setuptools.build_meta`;
- require a maintained setuptools version compatible with Python 3.11;
- install only the existing `scripts` Python package;
- retain `PyYAML` as the runtime dependency and `pytest` in the `dev` extra.

The repository directories `skills`, `evals`, `docs`, and `tests` are project
content, not importable Python packages. Explicit discovery prevents a future
top-level content directory from silently changing editable-install behavior.
The implementation must not solve the failure by bypassing project metadata
and installing `PyYAML` and `pytest` directly in CI; that would leave the
documented contributor command broken.

### 4.2 Platform decision seam

Add one internal helper in `scripts/install_local.py` that classifies the real
host as Windows, Linux, Darwin, or unsupported. `_rename_no_replace()` will
branch on that helper:

- Windows continues to use the existing no-overwrite `os.rename` behavior.
- Linux continues to require `renameat2(..., RENAME_NOREPLACE)`.
- Darwin continues to require `renamex_np(..., RENAME_EXCL)`.
- Any unsupported host or missing native primitive raises `ENOTSUP`.

Unit tests will replace only this helper when simulating another platform.
They must not mutate process-wide `os.name` or rely on the actual test runner
platform. A native Windows test still exercises the real Windows path.

No generic rename, copy-and-delete, delete-before-move, or overwrite fallback
is permitted. A platform-test fix that weakens this invariant is invalid even
if it makes the suite green.

### 4.3 Validation workflow

Update `.github/workflows/validate.yml` to use an operating-system matrix with
`ubuntu-latest` and `windows-latest`, both on Python 3.11. Each matrix job must:

1. check out the repository;
2. upgrade pip;
3. run `python -m pip install -e ".[dev]"`;
4. run `python -m pytest -q`;
5. run `python scripts/validate_skill.py`;
6. run `python scripts/check_public_boundary.py`;
7. run `python scripts/package_skill.py --check-reproducible`.

The workflow retains top-level `contents: read`, contains no project secrets,
and does not use `continue-on-error`. The full suite and all three
repository-specific checks must execute independently on both platforms.

### 4.4 Release workflow

Add `.github/workflows/release.yml` with `workflow_dispatch` and a required tag
input. A pushed annotated tag is a precondition; merely pushing a tag does not
publish automatically.

The workflow has three boundaries:

1. **Preflight on Ubuntu with read-only permissions**
   - fetch full tag and `main` history;
   - reject a lightweight tag;
   - require an exact `vX.Y.Z` tag matching project version `X.Y.Z`;
   - require the tag commit to be reachable from `origin/main`;
   - reject a version that already has a GitHub Release.
2. **Validation matrix with read-only permissions**
   - check out the exact annotated tag;
   - run the fresh editable install and the same four-command verification set
     on Ubuntu and Windows.
3. **Publish on Ubuntu with `contents: write`**
   - run only after preflight and both validation jobs succeed;
   - build the deterministic ZIP and manifest from the tag commit;
   - verify the manifest archive SHA-256 and all file records against the ZIP;
   - create a new GitHub Release from `docs/releases/X.Y.Z.md` and upload
     exactly that ZIP and manifest.

The publish job must not update an existing Release, force-move a tag, or
continue after any mismatch. Documentation will retain a manual local path for
inspection, but the workflow is the official GitHub publishing path.

Branch protection remains an external repository setting. The revalidation
report will identify the required Ubuntu and Windows validation checks and
explain how to verify the setting, but the implementation will not mutate it.

## 5. Documentation and first-success flow

Update `README.md` and `README.zh-TW.md` in aligned order and meaning.

### 5.1 Prerequisites and command boundaries

Before the npx quick start:

- identify Node.js and npm/npx as prerequisites for that installation path;
- provide `node --version` and `npm --version` checks;
- state that Node.js with npm/npx is required without claiming an unverified
  minimum version;
- identify a Codex interface that supports Skills.

The documentation must distinguish:

- `npx skills add mtchuang1981/clin-data-nav` as a terminal command;
- `/skills` and `$clinical-data-research-navigator` as text entered in Codex,
  not in PowerShell or a POSIX shell;
- the default project-local `.agents/skills` installation from the verified
  manual `$HOME/.agents/skills` path;
- initial installation, discovery verification, invocation, and later update.

### 5.2 Sixty-second first success

Add a compact path immediately after installation:

1. install the repository Skill;
2. verify discovery in Codex;
3. invoke the Skill with one minimal clinical-research question;
4. explain the expected first response: question clarification, source and
   schema boundaries, recommended workflow, and missing-information list.

The example must not promise a production-ready SAP, executable
institution-specific SQL, or causal conclusion from incomplete input.

Existing explanations of CDISC, SDTM, ADaM, PICO, RWD/RWE, TTE, and
`build-rwe-sap` remain authoritative content. This phase improves entry and
navigation rather than duplicating those explanations.

## 6. Eval evidence contract

`evals/README.md` will explicitly state:

- `evals/cases.yaml` currently defines 11 catalog cases;
- only three cases have checked-in baseline and forward fixture pairs and are
  listed in the score table;
- deterministic rules-based fixture scores are regression evidence, not proof
  of semantic correctness, clinical validity, or complete coverage.

A repository contract test will derive the catalog count and fixture-pair
count from the filesystem and require the README to report both values. It
will also require every scored table row to correspond to an actual baseline
and forward fixture pair. This turns future catalog or fixture additions into
an explicit documentation update instead of allowing the numbers to drift.

## 7. Clinical and source-authority boundaries

The optimization preserves the existing safety contracts:

- Do not guess a schema, table, field, join, date definition, medication code,
  or institution-specific mapping.
- LexJansen is a SAS literature discovery source, not automatic authority to
  copy or apply code. Recommendations must retain source provenance, original
  context, and applicability limits.
- RWD is not automatically RWE.
- A causal-comparative RWE request without adequate target-trial information
  returns a TTE readiness and gap assessment, not a causal claim.
- If `build-rwe-sap` is unavailable or its required input is incomplete, say
  so explicitly and continue only with the supported Core handoff; never
  silently install it or substitute a generic template.

No P0 change may weaken these boundaries merely to increase Eval scores or
produce a more complete-looking answer.

## 8. Error handling and permissions

- Installation errors identify the failed stage and supported recovery action
  without printing secrets, credential values, or unnecessary private path
  contents.
- Missing native no-replace primitives and unsupported platforms fail with
  `ENOTSUP`.
- Validation jobs have read-only repository permissions.
- Only the final publish job has `contents: write`, and only after all
  prerequisites succeed.
- Tag, version, ancestry, reproducibility, manifest, SHA-256, or existing
  Release mismatches stop the release before any GitHub mutation.
- The release workflow never overwrites an existing tag, Release, or asset.

## 9. Test strategy

Implementation follows red-green-refactor:

1. Add or tighten tests that reproduce the packaging, Windows platform
   simulation, CI matrix, Eval documentation, README, release workflow, and
   release-asset verification gaps.
2. Confirm each new test fails for the intended reason.
3. Apply the smallest production or documentation change that satisfies the
   approved design.
4. Run focused tests after each change and the complete acceptance matrix at
   the end.

The existing 168 tests may not be deleted, skipped, xfailed, or weakened.
Because new contract tests are required, the final collected count must exceed
168.

## 10. Acceptance criteria

The work is complete only when all of the following evidence exists:

- Fresh Python 3.11 editable installation succeeds on native Windows and a
  clean Linux environment.
- All existing and new tests pass on native Windows and clean Linux.
- On both platforms, all four commands exit zero:

  ```bash
  python -m pytest -q
  python scripts/validate_skill.py
  python scripts/check_public_boundary.py
  python scripts/package_skill.py --check-reproducible
  ```

- The `main` commit intended for release has successful Ubuntu and Windows
  GitHub Actions validation jobs with no skipped verification steps.
- Two independent package builds from the same commit produce byte-identical
  ZIP and manifest files.
- The manifest's archive SHA-256 matches the ZIP, every manifest file record
  matches the archived bytes, and no undeclared public file appears.
- `README.md` and `README.zh-TW.md` pass aligned prerequisite, command-boundary,
  and first-success contract tests.
- `evals/README.md` truthfully distinguishes 11 catalog cases from three scored
  fixture pairs and passes its filesystem-derived contract test.
- The unrelated `.baoyu-skills` file is absent from the tracked tree.
- `docs/verification/2026-07-29-v0.2.1-assessment.md` records every assessment
  item as confirmed, fixed, still open, or deferred, with its verification
  evidence.
- Current version fields, new changelog entries, package names, current
  documentation examples, and proposed release notes consistently use
  `0.2.2`/`v0.2.2`; historical release records retain their original versions.

## 11. Deliverables and publication boundary

The implementation will deliver:

- packaging and platform portability fixes;
- dual-platform validation and guarded release workflows;
- aligned README and Eval evidence documentation;
- focused regression and contract tests;
- the `v0.2.1` revalidation report;
- synchronized `v0.2.2` version metadata and bilingual changelog entries;
- proposed `v0.2.2` Release notes at `docs/releases/0.2.2.md`;
- a remaining P1/P2 list, with `v0.3.0` as the recommended next feature
  milestone.

The implementation may be committed locally after verification. Push, tag,
workflow dispatch, and GitHub Release creation remain separate external
actions requiring explicit user approval after the implementation evidence is
reviewed.

## 12. As-built amendments and post-release follow-up

- **Amendment date:** 2026-08-01
- **Original design commit:** `6150412`
- **Status:** As-built clarification plus an Unreleased follow-up

This section preserves Sections 1–11 as the design and authorization boundary
approved on 2026-07-29. It records later hardening and publication evidence
without presenting those changes as part of the original approval.

### 12.1 As-built Release trust boundary

The three logical boundaries in Section 4.4 were implemented as four jobs:

1. **`preflight` with read-only permissions** verifies the annotated tag,
   version, peeled commit, reachability from `origin/main`, and absence of an
   existing Release. Checkout credentials are not persisted.
2. **`validate` with read-only permissions** checks out the verified commit and
   runs the four-command verification set independently on Ubuntu and Windows.
3. **`build` with read-only permissions** checks out the verified commit,
   builds and verifies the ZIP and manifest, copies static Release notes, writes
   transit checksums, and uploads the bundle under the returned artifact ID.
4. **`publish` is the only job with `contents: write`**. It has no source
   checkout, Python setup, dependency installation, or repository-code
   execution. It downloads the exact artifact ID, verifies the checksum-file
   digest and every bundled file, rechecks the remote annotated tag object and
   peeled commit, refuses an existing Release, and then creates a new Release.

Third-party GitHub Actions are pinned to full commit SHAs. The writer cannot
rebuild source, edit an existing Release, or publish after a tag, transit,
asset, or remote-state mismatch. This subsection supersedes Section 4.4 only
as the description of the final as-built workflow; it does not rewrite the
original implementation scope.

### 12.2 Publication result

After separate explicit approval, annotated tag `v0.2.2` was published on
2026-08-01 through the guarded workflow. The tag object
`fcb2c0151a267a392f844f670342253dd3a6781d` peels to commit
`3da87f2e0b08b1a0c331d5a606bc59d099e9f3c8`. The successful workflow and
public Release are:

- <https://github.com/mtchuang1981/clin-data-nav/actions/runs/30700016113>
- <https://github.com/mtchuang1981/clin-data-nav/releases/tag/v0.2.2>

The Release contains exactly the ZIP and manifest. Independent download and
verification confirmed ZIP SHA-256
`f2c2ea5e354b866e2d4f62f6e8ab99981be156d210a96b9bb10b1efa71c7e7ca`
and manifest SHA-256
`6632e310e9c7c637a5dc8f4c8f53b155029e5e2d1c3a99a663854624604641c1`.
The complete command and job evidence remains in
`docs/verification/2026-07-29-v0.2.1-assessment.md`.

Branch protection was separately checked and remained unconfigured. No
repository setting, published tag, Release, or Release asset was overwritten.

### 12.3 Post-release canonical packaging

The published Ubuntu artifact used LF source bytes, but the original packager
at the `v0.2.2` tag read checkout bytes directly. A Windows checkout therefore
produced different package hashes for six CRLF text files even though each
platform independently passed `--check-reproducible`.

Post-release maintenance commit
`35587f0699be4c0e8737a299fa9a7a02e01ceddc` addresses the root cause by
canonicalizing CRLF and CR to LF for valid UTF-8 files without NUL bytes before
hashing and archiving. Files containing a NUL byte or invalid UTF-8 retain
their original bytes. Manifest file hashes and sizes describe the canonical
bytes stored inside the ZIP, not necessarily the raw bytes in a Windows
checkout.

Regression tests require byte-identical ZIP and manifest output for equivalent
LF and CRLF Skills and require both non-text cases to remain byte-identical to
their sources. A native-Windows build from the maintenance commit reproduced
both published Ubuntu hashes in Section 12.2 exactly. At amendment time this
commit was Unreleased and had not been pushed; it is not part of the immutable
`v0.2.2` tag.

### 12.4 Reproducibility acceptance layers

Future verification and claims must distinguish three levels:

1. **Same-checkout repeatability:** two builds from one checkout produce
   byte-identical ZIP and manifest files. The existing
   `--check-reproducible` gate enforces this level.
2. **Checkout line-ending independence:** equivalent LF and CRLF UTF-8 inputs
   produce byte-identical packages while NUL-containing or invalid UTF-8 files
   remain unchanged. The post-release regression tests enforce this level.
3. **Cross-runner artifact identity:** Windows and Ubuntu jobs upload their
   built artifacts and a dependent CI job compares them directly. This remains
   P2 before making a general guarantee across future Python and zlib runner
   combinations.

The native-Windows versus published-Ubuntu hash match proves Levels 1 and 2
for the current seven-file payload. It is evidence for the current package,
not a substitute for the continuing Level 3 CI control.

### 12.5 Change control

The historical baseline, original in-scope and out-of-scope lists, and
publication approval boundary remain unchanged. Any GitHub Release that
represents the post-release packaging fix must use a new patch version and
repeat the guarded release process after explicit approval; the published
`v0.2.2` tag and Release must never be moved or overwritten.
