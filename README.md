English | [繁體中文](README.zh-TW.md)

# Clinical Data Research Navigator

This installable Agent Skill turns clinical-data questions into source-ranked guidance without supplying private schemas or claiming validated clinical conclusions.

[![Validation](https://github.com/mtchuang1981/clin-data-nav/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/mtchuang1981/clin-data-nav/actions/workflows/validate.yml?query=branch%3Amain)

## Install in a project

```bash
npx skills add mtchuang1981/clin-data-nav
```

See the [installation guide](docs/installation.md) for Node.js prerequisites, updates, verified ZIP installation, and troubleshooting.

## First success

Enter this prompt in Codex:

```text
$clinical-data-research-navigator What is ADaM, why does it matter, and what does it not prove about source-data quality?
```

Expected first line: `Output depth: quick explanation`

- A direct plain-language definition and why ADaM matters in context.
- One or two common confusions or limits, followed by a short governing-source list.

## Choose an output depth

| Depth | Use it for | It does not silently add |
|---|---|---|
| `quick explanation` | Definitions, comparisons, and beginner questions | A full evidence matrix or implementation contract |
| `evidence navigation` | Finding, ranking, and comparing governing sources | Unreviewed search snippets presented as evidence |
| `research design` | Framing descriptive, predictive, or causal-comparative studies | A completed SAP, estimand, or causal result |
| `implementation specification` | Data contracts, mappings, derivations, and validation rules | Executable institutional code when the execution gate is incomplete |

An explicit depth request is honored unless it conflicts with a safety gate.
Otherwise, the Skill selects the least intensive depth that fully answers the
request and offers a deeper next step instead of combining every depth.

## Choose a learning path

- [Clinical trials and CDISC](docs/learning-paths.md#learn-the-terms): CDISC → SDTM → ADaM → protocol/SAP → implementation evidence.
- [RWD and RWE](docs/learning-paths.md#assess-the-evidence): intent → PICO-informed fields → RWD fitness → RWE claim → TTE readiness when causal-comparative.
- [Institutional implementation](docs/learning-paths.md#prepare-an-implementation): public evidence → logical data contract → approved Adapter → live metadata → fixtures → executable/validated status.

## Agent Skill and Plugin boundary

OpenAI's documentation says a Skill packages instructions, resources, and
optional scripts so ChatGPT or Codex can follow a workflow. A Plugin is a
separate distribution package for reusable Skills and connectors. This
repository distributes an installable Agent Skill from GitHub and does not
claim a public Plugin-directory listing; installing it does not create or
publish a Plugin.

## Documentation

| Need | Go to |
|---|---|
| Install, update, verified ZIP, or troubleshooting | [Installation](docs/installation.md) |
| Definitions | [Beginner glossary](docs/glossary.md) |
| Guided progression | [Learning paths](docs/learning-paths.md) |
| Synthetic worked examples | [TEAE to SAS](examples/teae-to-sas-spec.md), [OMOP phenotype to SQL specification](examples/omop-phenotype-to-sql-spec.md), and [institutional mapping](examples/synthetic-institutional-mapping.md) |
| Evidence shape and limitations | [Evidence output template](skills/clinical-data-research-navigator/references/evidence-output-template.md) and [architecture](docs/architecture.md) |
| Contribute and validate | [Contributing](CONTRIBUTING.md) |
| Report a security concern | [Security](SECURITY.md) |
| Prepare an approved release | [Release process](docs/release.md) |
| Review v0.3.0 changes | [Static release notes](docs/releases/0.3.0.md) and [changelog](CHANGELOG.md) |
| Check current product guidance | [OpenAI Skills in ChatGPT](https://help.openai.com/en/articles/20001066) and [Codex Skill documentation](https://learn.chatgpt.com/docs/build-skills) |

## Evidence, public boundary, and limitations

The Skill ranks governing sources ahead of implementation literature and keeps
confirmed facts, assumptions, limitations, and provenance visible. The
repository's deterministic Evals check response contracts; they do not prove
source accuracy, clinical validity, causal validity, or complete real-world
coverage.

This public Core contains reusable guidance, synthetic examples, tests, and
packaging tools. It contains no private TMUCRD Adapter, codingbook, data
dictionary, physical schema, linkage rule, PII classification, credential, or
login-gated document, and it is not a TMUCRD data dictionary. Institutional
work requires an approved, versioned private Adapter outside this repository
and current metadata checked in the governed environment.

The [glossary](docs/glossary.md) explains CDISC, SDTM, ADaM, RWD, and RWE.
RWD is not automatically RWE. Target trial emulation is considered only for a
causal-comparative question with the required design fields. `build-rwe-sap`
is optional and not bundled; clin-data-nav never installs it automatically.

Without an approved Adapter, current metadata, parameters, and fixtures, an
implementation request remains `SPECIFICATION ONLY — NOT EXECUTABLE` and must
not invent local tables, columns, joins, codes, or production-ready logic.
Incomplete requests receive question clarification and a missing-information
list rather than fabricated certainty. Using the installed instruction-only
Skill does not require Python; Python 3.11 is for repository contributor and
release tooling described in [CONTRIBUTING.md](CONTRIBUTING.md).
