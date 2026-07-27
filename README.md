# Clinical Data Research Navigator

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

## Supported questions

Use the Skill for clinical-data questions involving:

- CDISC, ADaM, SDTM, or regulatory terminology;
- protocol, SAP, or evidence-source navigation;
- SAS, SQL, R, EHR, claims, registry, or OMOP implementation specifications;
- data contracts, mapping checklists, and code-maturity gates; and
- public TMUCRD background that does not require schema or dictionary details.

Without a versioned Adapter, live metadata, and fixtures, the Skill returns a
specification rather than executable institutional code.

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

## Python 3.11 setup

This first release supports Python 3.11.

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

## Package and install

Choose absolute directories under your control, then substitute them in these
commands. The installer does not assume a platform-specific Skill location.

```bash
python scripts/package_skill.py --output-dir /absolute/path/you/select/skill-package
python scripts/install_local.py \
  /absolute/path/you/select/skill-package/clinical-data-research-navigator-0.1.0.zip \
  --destination /absolute/path/you/select/installed-skills
```

The resulting installed directory is
`/absolute/path/you/select/installed-skills/clinical-data-research-navigator`.
Use `--overwrite` only when intentionally replacing that installed Skill.

## Further documentation

- [Architecture](docs/architecture.md)
- [Release process](docs/release.md)
- [Security response](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
