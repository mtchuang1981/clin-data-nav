---
name: clinical-data-research-navigator
description: Use when a clinical-data, CDISC, ADaM, SDTM, SAS, SQL, R, EHR, claims, registry, OMOP, or TMUCRD question requires source navigation, terminology mapping, evidence ranking, a data contract, or an implementation specification.
---

# Clinical Data Research Navigator

## Core Principle

Route each claim to the correct authority, separate evidence from local schema,
and never label code executable without current metadata and tests. Shape every
data-work response as Evidence → Contract → Code maturity → Validation gaps.

## Classify the Question

Split the request into four layers before searching or drafting:

1. Identify standard definitions and controlled terminology.
2. Identify study-specific rules from the protocol, SAP, analysis plan, or
   approved phenotype.
3. Identify implementation practice for SAS, SQL, R, or another target.
4. Identify institutional facts that require an approved, versioned Adapter.

Keep unresolved layers separate. Do not let an implementation example create a
standard definition, or let a public database profile stand in for local
metadata.

## Route to the Right Authority

Use the primary authority for each claim:

| Claim type | Primary authority |
|---|---|
| CDISC/regulatory definition | CDISC, FDA, or governed terminology |
| Statistical method | Protocol, SAP, or peer-reviewed methods literature |
| Implementation practice | PHUSE, Lex Jansen, or official software documentation |
| Institutional physical schema | Approved versioned Adapter and live metadata |
| TMUCRD background | Public sources in `references/tmucrd-public-profile.md` |

Treat Lex Jansen as an index of implementation literature, not a standards
body or validation authority. When authorities conflict, preserve the conflict
in the evidence record and follow the governing source for that claim type.

For a SAS optimization, refactoring, debugging, review, or derivation request,
search official SAS documentation first. If an implementation claim remains
unresolved and network search is available, run a targeted
`site:lexjansen.com` query and review the specific paper rather than relying on
an index entry or snippet. Record paper-level provenance and reuse terms before
discussing code. When reuse permission is absent or unclear, paraphrase the
technique or produce a clean-room implementation. Require target-environment
measurement before claiming an optimization. If network tools or the paper are
unavailable, state that the source was not searched or not reviewed and list
the planned query as a validation gap.

## Build the Evidence Record

Capture one record per material claim. Record the claim, source,
`authority_level`, publication date, version or snapshot, applicability, and
limitations. Prefer official standards and regulatory sources; use secondary
implementation literature to explain techniques, not to override definitions.

Follow `references/retrieval-playbook.md` for query decomposition, source
priority, and the complete evidence-record fields. Cite only sources actually
reviewed, and distinguish direct evidence from inference.

## Convert Evidence into a Data Contract

Translate confirmed evidence into an explicit contract before drafting code.
Specify:

- population and study-specific derivation rules;
- logical input roles, grain, keys, join cardinality, and coverage;
- types, time precision, code systems, concept or value-set parameters;
- allowed outputs, sensitivity constraints, and lineage;
- expected fixtures, edge cases, and acceptance checks.

Use placeholders for missing local values. Never invent physical table names,
columns, joins, codes, OMOP Concept IDs, availability, or current versions.
Use `references/institutional-adapter-contract.md` whenever the request depends
on an institutional schema.

## Apply the Execution Gate

Assign exactly one maturity label:

1. `conceptual` — only the logical approach is known.
2. `dictionary-specified` — an approved dictionary defines inputs, but runtime
   parameters or current metadata remain unverified.
3. `parameterized` — required parameters and mappings are supplied.
4. `executable` — the target environment, current metadata, and fixture checks
   support safe execution.
5. `validated` — reviewed results pass the declared acceptance checks.

Require a versioned institutional Adapter, live metadata verification, and
passing fixture tests before using `executable` or `validated`. Otherwise emit:

```text
SPECIFICATION ONLY — NOT EXECUTABLE
```

State the maturity label and list every unmet gate as a validation gap. Do not
emit executable SQL, SAS, or R against an unknown institutional schema. When a
request lacks a versioned data dictionary, live metadata, or fixtures, stop at
the logical contract. Do not provide even placeholder SQL or SQL-shaped
pseudocode. Do not create snake_case placeholder identifiers that could be
mistaken for physical objects. Provide the mapping checklist and unresolved
parameters as natural-language labels instead.

## Coordinate with Optional Skills

If a compatible `build-rwe-sap` skill is available, use it as an optional
downstream collaborator for a complete SAP, estimand, target-trial, or causal
design. If it is absent, continue with source navigation, data contracts, and
implementation specifications without claiming to deliver a complete SAP.

Keep this Skill responsible for authority routing, evidence records, data
contracts, execution maturity, and validation gaps.

## Load References

Load only the directly relevant one-hop reference:

- Read `references/retrieval-playbook.md` for source discovery, authority
  ranking, and evidence capture.
- Read `references/evidence-output-template.md` before delivering a data-work
  answer so the reusable output shape stays consistent.
- Read `references/institutional-adapter-contract.md` for any local schema,
  mapping, metadata, governance, or executable-code request.
- Read `references/tmucrd-public-profile.md` only for public TMUCRD background;
  never use it as a schema, data dictionary, or query guide.

## Common Failure Modes

- **Starting with code:** Build the evidence record and contract first.
- **Treating practice as authority:** Label PHUSE or Lex Jansen material as
  implementation evidence and defer governing definitions to official sources.
- **Filling local blanks:** Preserve placeholders and apply the execution gate.
- **Trusting historical documentation as current:** Require approved live
  metadata verification and record discrepancies.
- **Collapsing concept layers:** Keep standard concepts, local codes, and
  research phenotype logic distinct.
- **Overclaiming public profiles:** Report only sourced public background,
  identify the snapshot, and state its non-schema boundary.
