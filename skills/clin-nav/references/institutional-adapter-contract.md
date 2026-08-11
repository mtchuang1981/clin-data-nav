# Institutional Adapter Contract

Use an institutional Adapter to supply governed local facts without placing
them in this public Skill. Keep each Adapter in its approved environment.

## Public manifest example

Use this complete synthetic manifest shape:

```yaml
adapter_schema_version: "1"
institution_id: "SYNTH_INSTITUTION"
adapter_version: "0.1.0"
dictionary_version: "SYNTH-2026-01"
effective_date: "2026-01-01"
classification: "synthetic-example"
source_owner: "synthetic-data-governance"
domains: []
metadata_verification:
  required: true
  method: "compare approved catalog metadata with the adapter manifest"
```

Do not replace synthetic values with guessed local values. Require the source
owner to approve the manifest and its effective version.

## Domain contract

For every domain, require:

- **Logical role and grain:** Define what one row represents and the event,
  person, episode, or period boundaries.
- **Keys:** Declare approved primary, foreign, and deduplication keys; state
  whether each is stable across refreshes.
- **Join cardinality:** Declare allowed one-to-one, one-to-many, or many-to-one
  paths and the checks that detect multiplication or loss.
- **Coverage:** Record source system, population, site, and date coverage with
  an owner-approved snapshot; distinguish unavailable from unknown.
- **Types:** Map logical fields to approved physical types and nullability.
- **Time precision:** Declare date, datetime, partial-date, timezone, and
  interval semantics, including censoring or imputation rules.
- **Code systems:** Name the system, release or value-set version, local mapping
  owner, and treatment of unmapped values.
- **PII labels and output constraints:** Use locally governed labels, allowed
  purposes, minimum-cell or disclosure controls, and permitted output forms.
- **Lineage:** Trace each logical element to its governed source and
  transformation owner.

Use synthetic labels such as `SYNTH_RESTRICTED` and
`SYNTH_NO_DIRECT_IDENTIFIER` only in public examples. Never publish an actual
institution's classifications through this contract.

## Live metadata verification

Compare the approved catalog metadata with the Adapter manifest in the target
environment. Check object presence, types, nullability, key uniqueness,
cardinality, code-version compatibility, date ranges, and refresh timestamp.

When live metadata differs from the Adapter:

1. Record the discrepancy and affected contract rule.
2. Stop code promotion.
3. Ask the source owner to revise or reapprove the Adapter.
4. Re-run metadata and fixture checks after resolution.

Historical documentation alone never verifies the current environment.

## Fixture checks

Require de-identified or wholly synthetic fixtures approved for the target
environment. Include:

- expected inclusion and exclusion cases;
- missing keys, duplicate keys, and unexpected join multiplication;
- null, malformed, partial, and boundary timestamps;
- mapped, unmapped, obsolete, and out-of-scope codes;
- empty inputs and zero-result cohorts;
- expected aggregate outputs and prohibited row-level outputs.

Store only synthetic fixtures in a public repository.

## Code maturity

Apply these gates:

| Maturity | Adapter requirement |
|---|---|
| `conceptual` | Logical roles may still be unresolved |
| `dictionary-specified` | Approved dictionary and Adapter version define mappings |
| `parameterized` | Required concept sets, windows, and runtime parameters are supplied |
| `executable` | Live metadata and target-environment fixture checks pass |
| `validated` | Reviewed results meet acceptance criteria and governance controls |

Without a versioned Adapter, live metadata verification, and passing fixtures,
emit `SPECIFICATION ONLY — NOT EXECUTABLE`.
