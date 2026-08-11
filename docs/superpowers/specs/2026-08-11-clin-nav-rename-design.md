# ClinNav Skill Rename Design

- **Status:** approved design
- **Design date:** 2026-08-11 (Asia/Taipei)
- **Baseline commit:** `845c39fe06283509e1e3de75297836084a8b5b79`
- **Target version:** `0.5.0`

## 1. Decision

Rename the single installable Skill from `clinical-data-research-navigator` to
`clin-nav`. The repository remains `clin-data-nav`, and the formal project name
remains Clinical Data Research Navigator. The shorter Skill ID is the public
invocation and installation identity; the OpenAI UI display name becomes
`ClinNav`.

This is a complete cutover, not an alias. The repository must contain exactly
one installable Skill at `skills/clin-nav/`, with frontmatter name `clin-nav`
and explicit invocation `$clin-nav`.

## 2. Evaluated approaches

### 2.1 Complete cutover — selected

Rename the directory, metadata, active documentation, scripts, package names,
workflows, and tests together. Preserve immutable historical evidence under its
original names and provide an explicit migration procedure for existing local
installs.

This avoids duplicate discovery, ambiguous triggers, and two copies of the same
clinical-safety guidance.

### 2.2 Dual-name compatibility Skill — rejected

Keeping both names would make `npx skills add` discover two equivalent Skills,
duplicate maintenance, and allow the two safety contracts to drift. A future
agent could invoke the stale copy without realizing it.

### 2.3 Documentation-only nickname — rejected

Changing only README text would leave the installed directory, metadata,
default prompt, package artifacts, and explicit invocation unchanged. It would
not solve the user-facing problem and would make the documentation inaccurate.

## 3. Naming and version invariants

Active surfaces use these exact values:

| Surface | Value |
|---|---|
| Skill directory | `skills/clin-nav/` |
| Skill frontmatter name | `clin-nav` |
| Explicit invocation | `$clin-nav` |
| OpenAI display name | `ClinNav` |
| Repository | `mtchuang1981/clin-data-nav` |
| Formal project title | `Clinical Data Research Navigator` |
| Target package version | `0.5.0` |
| ZIP | `clin-nav-0.5.0.zip` |
| Manifest | `clin-nav-0.5.0.manifest.json` |

The version moves from `0.4.0` to `0.5.0` because changing the Skill ID,
directory, explicit invocation, local install target, and artifact names is a
breaking public-interface change in a pre-1.0 project. No tag or Release is
created by this design or its implementation plan without a later explicit
publication authorization.

## 4. Active and historical surfaces

The implementation must classify occurrences before editing them.

Active surfaces include:

- `skills/`, current README files, installation guides, architecture, glossary,
  learning paths, and current release instructions;
- validators, packagers, local installers, public-boundary checks, workflows,
  current tests, and current examples; and
- current project metadata that describes how to invoke or package the Skill.

Historical surfaces include released notes, dated verification evidence, old
release assets and digests, and completed implementation plans whose literal
commands describe versions `0.1.0` through `0.4.0`. These remain unchanged.
Tests must use an explicit historical allowlist rather than a global text
replacement.

## 5. Skill content and metadata

Move the complete installable directory without changing its clinical method,
authority hierarchy, public/private boundary, output-depth behavior, or safety
gates. The rename itself must not silently add new clinical guidance.

Because `SKILL.md` changes, the implementation must also review and synchronize:

- `skills/clin-nav/agents/openai.yaml`;
- every Eval or acceptance contract that invokes the Skill; and
- every reference route inside the Skill and from active repository documents.

The validator must derive the expected invocation from the supplied Skill
directory name instead of retaining a second hard-coded old identifier. The
repository entry point still validates the single canonical directory
`skills/clin-nav/`.

## 6. Packaging and installation

Packaging, verification, and local installation use `clin-nav` as the canonical
name. Archive members remain relative to the Skill root, so the ZIP contains no
redundant top-level directory. Reproducibility, canonical line endings, sorted
manifest rows, member SHA-256 values, path containment, overwrite protection,
and rollback behavior remain unchanged.

The active quick start remains:

```text
npx skills add mtchuang1981/clin-data-nav
```

After discovery, it installs the single `clin-nav` Skill. Existing users must
remove the old installed directory and install the repository again. Migration
guidance must name both directories explicitly, require inspection before
removal or overwrite, and never delete an unresolved or broad path.

## 7. Backward-compatibility boundary

Existing local installations of `clinical-data-research-navigator` do not
automatically become `clin-nav`. They continue to exist locally until the user
chooses to migrate. The repository does not ship a redirect Skill because a
redirect would itself be a second discoverable Skill and could retain obsolete
safety content.

The v0.4.0 annotated tag, GitHub Release, asset names, manifest, digests, and
publication evidence remain immutable. A later v0.5.0 Release, if authorized,
is a new release line with new artifact names and digests.

## 8. Test-driven implementation

Before moving or editing production files, add failing tests that require:

- exactly one installable directory named `clin-nav`;
- matching directory and frontmatter names;
- `$clin-nav` in the default prompt and active invocation examples;
- `ClinNav` as the UI display name;
- active scripts, package names, and version metadata synchronized at `0.5.0`;
- active documentation free of the old Skill ID except in the migration section;
- historical evidence preserving the old ID and released asset names;
- every internal active link resolving after the directory move;
- install, overwrite, rollback, and package verification behavior using the new
  name; and
- deterministic `clin-nav-0.5.0` ZIP and manifest output.

Skill behavior tests must demonstrate that the renamed Skill is still
discoverable and applies the same safety, evidence-ranking, output-depth, and
public-boundary rules. The rename is successful only if behavior remains
equivalent apart from the intended identity and invocation changes.

## 9. Verification

The final implementation must run:

```text
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

It must also run the bilingual render checks, `git diff --check`, review the
complete diff, build the new artifacts from a clean output directory, validate
the manifest and every ZIP member independently, and perform an isolated
local-source `npx skills add` smoke test against the candidate worktree without
modifying the repository checkout. The GitHub-source command
`npx skills add mtchuang1981/clin-data-nav` is verified only after an authorized
push makes the candidate commit reachable from remote `main`.

## 10. Failure handling

- Any second discovered Skill stops the migration.
- Any unresolved active link or old active invocation stops packaging.
- Any historical evidence mutation stops the change.
- Any Skill behavior regression stops the change.
- Any package, manifest, digest, public-boundary, or cross-runtime mismatch
  stops publication.
- A successful local build does not authorize a push, tag, or Release.

## 11. Inversion and second-order controls

The rename fails most seriously if the old and new Skills coexist and later
diverge. A single canonical directory and an active-surface contract prevent
that failure. It also fails if a broad replacement rewrites released evidence;
the historical allowlist prevents loss of provenance.

The second-order maintenance risk is duplicated name constants across scripts.
The implementation should retain one explicit canonical identity per component
and test cross-component synchronization, without introducing a new framework
solely for configuration. The user-facing migration cost is accepted once in
exchange for a shorter stable invocation.

## 12. Acceptance criteria

- The repository exposes exactly one installable Skill, `clin-nav`.
- `$clin-nav` works in active examples and the OpenAI metadata.
- The formal project and repository names remain unchanged.
- Active paths, scripts, tests, documentation, packages, and workflows agree.
- Released v0.1.0–v0.4.0 evidence remains byte-for-byte unchanged.
- Existing clinical behavior and safety boundaries pass their application
  tests after the move.
- All required gates and isolated installation checks pass.
- No push, tag, or Release occurs without its own authorized execution stage.
