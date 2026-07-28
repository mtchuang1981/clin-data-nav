# Clinical Data Research Navigator

English | [繁體中文](README.zh-TW.md)

Clinical Data Research Navigator helps researchers turn clinical-data questions
into source-ranked evidence, a safe data contract, and an explicit execution
maturity assessment.

## Public boundary

This repository is a public Core: it contains reusable guidance, synthetic
examples, tests, and packaging tools. It does not contain private TMUCRD
adapters, codingbooks, data dictionaries, physical schemas, credentials, or
login-gated documents. It is not a TMUCRD data dictionary.

For institutional implementation, mount an approved, versioned private Adapter
outside this repository and verify current metadata in the governed environment.

## New to clinical-data standards?

You do not need prior CDISC knowledge to use this Skill. These three terms
describe different parts of a standards-based clinical-trial data workflow:

| Term | Plain-language meaning | Why it appears here |
|---|---|---|
| [CDISC](https://www.cdisc.org/standards) | The Clinical Data Interchange Standards Consortium and its suite of standards for representing clinical and non-clinical research data. | It provides the standards ecosystem that includes SDTM, ADaM, controlled terminology, and related implementation guides. |
| [SDTM](https://www.cdisc.org/standards/foundational/sdtm) | The Study Data Tabulation Model standardizes how collected or received study data are organized and formatted without changing their original meaning. | It makes study data more consistent for exchange, review, aggregation, and regulatory submission. |
| [ADaM](https://www.cdisc.org/standards/foundational/adam) | The Analysis Data Model defines analysis datasets and metadata that support reproducible statistical analyses. | It helps reviewers trace an analysis result back through analysis data to its SDTM source. |

A common clinical-trial flow can be understood as:

```text
Collected or received study data
→ SDTM: standardized tabulation and review
→ ADaM: analysis-ready data and derivations
→ statistical analyses, tables, figures, and listings
```

This is a simplified mental model; not every clinical-data question must follow
it. EHR, claims, registry, OMOP, and other real-world data may use different
source models. The Skill first determines which standards actually apply, then
keeps official definitions, study-specific rules, implementation techniques,
and institutional mappings separate.

## Supported questions

Use the Skill for clinical-data questions involving:

- CDISC, ADaM, SDTM, or regulatory terminology;
- protocol, SAP, or evidence-source navigation;
- SAS, SQL, R, EHR, claims, registry, or OMOP implementation specifications;
- data contracts, mapping checklists, and code-maturity gates; and
- public TMUCRD background that does not require schema or dictionary details.

Without a versioned Adapter, live metadata, and fixtures, the Skill returns a
specification rather than executable institutional code.

For SAS optimization, refactoring, debugging, review, or derivation requests,
the Skill searches official SAS documentation first. When implementation
evidence is still needed and network tools are available, it runs a targeted
`site:lexjansen.com` search and reviews the specific paper. It records source
and code provenance, checks reuse terms, and requires target-environment
measurement before claiming a performance improvement. If the paper cannot be
reviewed, that limitation is reported as a validation gap.

## Repository and installed Skill layout

The source repository provides governance, tests, scripts, and the canonical
installable Skill source:

```text
clin-data-nav/
├── scripts/                              # validation, packaging, installation
└── skills/clinical-data-research-navigator/  # source Skill
```

Packaging produces a ZIP containing the installable Skill files only. Local
installation places `clinical-data-research-navigator/` beneath a destination
directory you select.

## Does using the Skill require Python?

Using the installed Skill does not require Python. The Skill itself consists of
Markdown, YAML metadata, and reference files that Codex or ChatGPT reads
directly. SAS, SQL, R, and Python may be discussed as target implementation
languages, but none is a runtime dependency for invoking the Skill.

Python 3.11 is required only for contributors who run this repository's tests,
deterministic packager, or strict source-checkout installer. Installing the
published ZIP with the PowerShell or POSIX instructions below does not require
Python.

## Contributor setup (Python 3.11)

The repository's development and release tools support Python 3.11.

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Validate the repository

Run all four checks before proposing a change:

```bash
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

## Install from GitHub Release

Codex discovers personal Skills under `$HOME/.agents/skills`. Download the ZIP
and manifest from the same release, verify the ZIP against the manifest, then
extract it into its own Skill directory. The examples below refuse to replace
an existing installation and install release `v0.1.1`.

PowerShell:

```powershell
$releaseVersion = "0.1.1"
$assetName = "clinical-data-research-navigator-$releaseVersion"
$releaseBase = "https://github.com/mtchuang1981/clin-data-nav/releases/download/v$releaseVersion"
Invoke-WebRequest "$releaseBase/$assetName.zip" -OutFile "$assetName.zip"
Invoke-WebRequest "$releaseBase/$assetName.manifest.json" -OutFile "$assetName.manifest.json"
$manifest = Get-Content "$assetName.manifest.json" -Raw | ConvertFrom-Json
$actualHash = (Get-FileHash "$assetName.zip" -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -ne $manifest.archive_sha256) { throw "SHA-256 mismatch" }
$skillDirectory = Join-Path $HOME ".agents\skills\clinical-data-research-navigator"
if (Test-Path $skillDirectory) { throw "Skill already exists: $skillDirectory" }
New-Item -ItemType Directory -Path $skillDirectory -Force | Out-Null
Expand-Archive "$assetName.zip" -DestinationPath $skillDirectory
Test-Path (Join-Path $skillDirectory "SKILL.md")
```

POSIX shell:

```bash
release_version="0.1.1"
asset_name="clinical-data-research-navigator-$release_version"
release_base="https://github.com/mtchuang1981/clin-data-nav/releases/download/v$release_version"
curl -fLO "$release_base/$asset_name.zip"
curl -fLO "$release_base/$asset_name.manifest.json"
expected_hash="$(grep -o '"archive_sha256":"[0-9a-f]\{64\}"' "$asset_name.manifest.json" | cut -d '"' -f4)"
if command -v sha256sum >/dev/null 2>&1; then
  actual_hash="$(sha256sum "$asset_name.zip" | cut -d ' ' -f1)"
elif command -v shasum >/dev/null 2>&1; then
  actual_hash="$(shasum -a 256 "$asset_name.zip" | cut -d ' ' -f1)"
else
  echo "Install sha256sum or shasum to verify the archive." >&2
  exit 1
fi
test "$actual_hash" = "$expected_hash" || { echo "SHA-256 mismatch" >&2; exit 1; }
echo "SHA-256 OK"
skill_directory="$HOME/.agents/skills/clinical-data-research-navigator"
test ! -e "$skill_directory" || { echo "Skill already exists: $skill_directory"; exit 1; }
mkdir -p "$skill_directory"
unzip "$asset_name.zip" -d "$skill_directory"
test -f "$skill_directory/SKILL.md"
```

Codex detects Skill changes automatically. If the Skill does not appear, restart
Codex and check `/skills` again.

## Install from a source checkout

For the repository's stricter installer checks, create the package and keep its
manifest beside the ZIP. The installer verifies the archive hash, member
manifest, size limits, paths, and extracted Skill before installation.

```bash
python scripts/package_skill.py --output-dir /absolute/path/you/select/skill-package
python scripts/install_local.py \
  /absolute/path/you/select/skill-package/clinical-data-research-navigator-0.1.1.zip \
  --destination "$HOME/.agents/skills"
```

The resulting directory is
`$HOME/.agents/skills/clinical-data-research-navigator`. Use `--overwrite` only
when intentionally replacing that exact installed Skill.

## Use the Skill

In Codex CLI or the IDE extension, run `/skills` to confirm discovery or invoke
the Skill explicitly with `$clinical-data-research-navigator`. In the ChatGPT
desktop app, open **Skills** in the sidebar or type `@` and select
**Clinical Data Research Navigator**. Codex and ChatGPT may also activate it
implicitly when a request matches the Skill description.

Example prompts:

```text
$clinical-data-research-navigator Rank the governing sources for a synthetic
TEAE derivation, then produce Evidence → Contract → Code maturity →
Validation gaps.

$clinical-data-research-navigator Review a synthetic SAS ADAE approach for
optimization. Search official SAS documentation first, then targeted
Lex Jansen implementation literature, and preserve provenance and reuse terms.

$clinical-data-research-navigator Describe a non-executable OMOP-like
phenotype without inventing Concept IDs or institutional schema details.
```

If no approved versioned Adapter, live metadata, or fixtures are available,
expect a specification and validation-gap report rather than executable
institutional code.

## Further documentation

- [Architecture](docs/architecture.md)
- [Release process](docs/release.md)
- [Changelog](CHANGELOG.md)
- [Security response](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Official Codex Skill documentation](https://learn.chatgpt.com/docs/build-skills)
