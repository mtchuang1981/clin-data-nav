# Contributing

Contributions must preserve the public Core boundary and remain useful across
institutions. Installing and using the instruction-only Skill does not require
this Python environment; these steps are for repository development and
release tooling.

## Before you contribute

- Use synthetic institutional schemas, values, and examples only.
- Submit only content that you are entitled to license for Apache-2.0 use.
- For each contribution, provide auditable provenance and license-right
  evidence appropriate to the material: a source URL or identifier plus the
  applicable license, permission, or attestation. Do not submit private or
  login-gated documents as evidence.
- Do not include a private Adapter, credentials, institutional data, or a
  login-gated document.
- Add or update a failing test before changing behavior, confirm the expected
  failure, and then make it pass.
- If `SKILL.md` changes, review the associated Evals, UI metadata in
  `agents/openai.yaml`, and references for consistency.

## Contributor setup with Python 3.11

The repository's development and release tools support Python 3.11. Create a
virtual environment and use an editable install so tests run against the
current checkout.

POSIX shell:

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If environment creation or dependency installation fails, stop at the first
error and use the [stage-specific Python setup
troubleshooting](docs/installation.md#troubleshoot-python-setup-failure).

## Required validation gates

Run all four checks before opening a pull request:

```bash
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

All four gates are independent. A successful package build does not imply the
test suite, Skill validator, or public-boundary scan passed. Review `git diff`
after validation and before committing.

The boundary scan is required before every pull request. Explain any change to
the public/private boundary in the pull request description. Release
publication remains a separate approved operation described in
[docs/release.md](docs/release.md).
