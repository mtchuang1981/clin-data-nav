# Installation

[繁體中文](installation.zh-TW.md)

The recommended path is a project-local installation with `npx skills add`.
Use the verified ZIP path only when you need a pinned Release artifact, and
use the source-checkout path only when developing or auditing this repository.

## Runtime boundary

The instruction-only installed Skill does not require Python. It consists of
Markdown, YAML metadata, and references read by the supporting agent product.
Python 3.11 is required only for this repository's contributor, validation,
packaging, release-verification, and strict source-checkout installation tools;
see [CONTRIBUTING.md](../CONTRIBUTING.md).

## Check prerequisites

The recommended installation needs Node.js with npm/npx and a Codex interface
that supports Skills. Check the commands in a terminal:

```bash
node --version
npm --version
npx --version
```

## Install in the current project

From the root of the project where you want to use the Skill, run:

```bash
npx skills add mtchuang1981/clin-data-nav
```

The command installs the Skill under the current project's `.agents/skills`.
Review third-party Skills before use because they run with your agent's
permissions.

`/skills` and
`$clin-nav` are entered in
Codex; they are not terminal commands. Use `/skills` to confirm discovery,
then invoke the Skill explicitly. A request with incomplete implementation
inputs should receive question clarification and a missing-information list,
not invented schema or production code.

In Codex CLI or the IDE extension, use `/skills` for discovery and
`$clin-nav` for explicit invocation. The ChatGPT
desktop app has a separate installation surface: open `Skills` through
**Plugins → Skills → Create → Upload from computer**. This interface may vary
by plan, workspace permissions, or rollout; continue only when your plan and
workspace allow uploads. Check both OpenAI's [Help Center Skills
guide](https://help.openai.com/en/articles/20001066-skills-in-chatgpt) and [Build Skills
documentation](https://learn.chatgpt.com/docs/build-skills) for the current
surface. The project-local `npx` command writes to `.agents/skills`; it does
not install it into ChatGPT or establish a public Plugin-directory listing.

## Migrate from the previous Skill ID

The installed Skill ID changed from `clinical-data-research-navigator` to
`clin-nav`. Inspect the exact existing
`.agents/skills/clinical-data-research-navigator` directory before removing or archiving anything,
and confirm that it is the previous Skill installation in
the intended project.

Remove or archive only that verified directory with a safe file operation for
your platform. Never delete a broad or unresolved path. Do not use a recursive
deletion command from this guide.

Rerun the project-local installation:

```bash
npx skills add mtchuang1981/clin-data-nav
```

Confirm `.agents/skills/clin-nav/SKILL.md` exists. Then restart the Skill host if required,
inspect `/skills`, and invoke `$clin-nav`.

## Update a project-local installation

Run this command from the same project root:

```bash
npx skills update clin-nav --project --yes
```

Confirm discovery again with `/skills`. If the displayed behavior is stale,
follow the stage-specific recovery below instead of reinstalling blindly.

## Verified ZIP installation from a GitHub Release

The current verified Release is `v0.4.0`. It is the current published release;
this section preserves its historical artifact names until a later v0.5.0 publication is authorized.
Download both the ZIP and manifest
from that same Release, verify the ZIP's SHA-256 against `archive_sha256`, and
only then extract it. These examples refuse to overwrite an existing
destination.

PowerShell:

```powershell
$releaseVersion = "0.4.0"
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
release_version="0.4.0"
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

## Install from a source checkout

For the repository's stricter checks, build a package and keep its manifest
beside the ZIP. The installer verifies the archive hash, member manifest, size
limits, paths, and extracted Skill before installation.

```bash
package_directory="/absolute/path/you/select/skill-package"
package_output="$(python scripts/package_skill.py --output-dir "$package_directory")"
archive_path="$(printf '%s\n' "$package_output" | sed -n '1p')"
manifest_path="$(printf '%s\n' "$package_output" | sed -n '2p')"
test -f "$archive_path"
test -f "$manifest_path"
python scripts/install_local.py \
  "$archive_path" \
  --destination "$HOME/.agents/skills"
```

The local packager validates the Skill and prints the exact archive path,
followed by its manifest path. Passing that reported archive avoids coupling
the instructions to a future version constant. The destination is
`$HOME/.agents/skills/clin-nav`. Use `--overwrite`
only after you have inspected that exact installation and intentionally chosen
to replace it; the command above omits `--overwrite`, so an existing target is
refused. The packager and installer are contributor/release tooling, so this
path requires Python 3.11 and the setup in
[CONTRIBUTING.md](../CONTRIBUTING.md).

## Troubleshooting

Treat each failure at the stage where it occurs. Do not bypass verification or
delete an unresolved destination blindly.

<a id="troubleshoot-missing-node"></a>
### `node`, `npm`, or `npx` is missing

Diagnosis: run the prerequisite checks again and inspect `PATH`. Recovery:
install a supported Node.js distribution that includes npm/npx, restart the
terminal so `PATH` is refreshed, then rerun all three version checks before
install.

<a id="troubleshoot-install-command-failure"></a>
### `npx skills add` fails

Diagnosis: retain the full diagnostic, confirm the repository spelling and
current network access, and distinguish a registry/tool failure from a GitHub
access failure. Recovery: correct the identified cause, then retry the same
command from the intended project root; do not switch to an unverified ZIP.

<a id="troubleshoot-activation-failure"></a>
### The installed Skill is not discovered or activation fails

Diagnosis: confirm you are in the same project root, verify
`.agents/skills/clin-nav/SKILL.md` exists, and check
`/skills`. Recovery: open the intended project, restart Codex once, and check
`/skills` again. Do not move the directory until its actual install location
is understood.

<a id="troubleshoot-stale-after-update"></a>
### Discovery is stale after update

Diagnosis: confirm `npx skills update` ran in the same project and use
`/skills` to inspect discovery. Recovery: close and restart Codex for that
project, then recheck before attempting another update.

<a id="troubleshoot-download-failure"></a>
### ZIP or manifest download fails

Diagnosis: confirm the requested tag has a published Release and that both
asset names exist. Recovery: retry only when the ZIP and manifest can be
downloaded from the same release; do not mix assets across tags or use a
partial download.

<a id="troubleshoot-manifest-mismatch"></a>
### The manifest and ZIP do not match

Diagnosis: a SHA-256 mismatch means the ZIP does not match the selected
manifest. Recovery: do not extract it; remove only the two downloaded files,
then download both again from the same verified Release. If the mismatch
persists, stop and report it.

<a id="troubleshoot-existing-target"></a>
### The target already exists

Diagnosis: the safe examples refuse to overwrite an existing installation.
Recovery: inspect the exact target and decide whether it is the installation
you intend to keep; use a different destination for comparison. Use the strict
installer's `--overwrite` only for a deliberate, reviewed replacement.

<a id="troubleshoot-python-setup-failure"></a>
### Python contributor setup fails

Diagnosis: run `python --version` and confirm Python 3.11, the active virtual
environment, and the first dependency installation error. Recovery: recreate
the virtual environment only after identifying the cause, then repeat the
editable install from [CONTRIBUTING.md](../CONTRIBUTING.md). Python failure
does not block normal use of the installed instruction-only Skill.
