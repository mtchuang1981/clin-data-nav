# SYNTH_PHENOTYPE_001 OMOP-to-SQL Specification

## Decision

Keep three layers distinct:

1. A standard concept is a vocabulary-governed meaning selected from the
   approved OMOP vocabulary release.
2. `SYNTH_LOCAL_CODE` is a source-system value that requires an approved
   mapping.
3. `SYNTH_PHENOTYPE_001` is a research rule combining concepts, time windows,
   exclusions, and observation requirements.

Never invent or infer Concept IDs. Accept identifiers only from a supplied,
versioned `SYNTH_CONCEPT_SET`.

## Evidence table

| Claim | Source | Authority level | Publication date | Version or snapshot | Applicability | Limitations |
|---|---|---|---|---|---|---|
| Standard-concept semantics | Official OMOP/OHDSI documentation | Official implementation standard | Confirm from source | `SYNTH_VOCAB_VERSION_SLOT` | Vocabulary selection | Does not define the research phenotype |
| Local-code mapping | `SYNTH_ADAPTER_001` | Institutional | `SYNTH_EFFECTIVE_DATE` | `SYNTH_ADAPTER_VERSION` | `SYNTH_LOCAL_CODE` | Requires live verification |
| Inclusion and exclusion logic | `SYNTH_PHENOTYPE_PROTOCOL_001` | Study-specific | `SYNTH_APPROVAL_DATE` | `SYNTH_APPROVED_VERSION` | `SYNTH_PHENOTYPE_001` | Requires clinical review |

## Data contract

Parameter slots:

```yaml
phenotype_id: "SYNTH_PHENOTYPE_001"
vocabulary_version: "SYNTH_VOCAB_VERSION_SLOT"
concept_set: "SYNTH_CONCEPT_SET_REQUIRED"
local_mapping_version: "SYNTH_MAPPING_VERSION_SLOT"
index_window: "SYNTH_INDEX_WINDOW_SLOT"
lookback_window: "SYNTH_LOOKBACK_WINDOW_SLOT"
minimum_observation: "SYNTH_OBSERVATION_SLOT"
exclusions: "SYNTH_EXCLUSION_SET_SLOT"
```

Require logical input roles for person, observation period, qualifying events,
and exclusions. Obtain their physical mappings, grain, keys, date semantics,
and allowed joins from `SYNTH_ADAPTER_001`.

SQL specification:

```text
resolve the supplied SYNTH_CONCEPT_SET against SYNTH_VOCAB_VERSION_SLOT
map SYNTH_LOCAL_CODE only through SYNTH_MAPPING_VERSION_SLOT
identify qualifying events inside SYNTH_INDEX_WINDOW_SLOT
apply SYNTH_OBSERVATION_SLOT and SYNTH_LOOKBACK_WINDOW_SLOT
apply SYNTH_EXCLUSION_SET_SLOT
deduplicate according to SYNTH_PHENOTYPE_PROTOCOL_001
```

Do not substitute numeric identifiers, local values, physical objects, or
executable SQL for any unresolved slot.

## Code maturity

Current maturity is `conceptual` while the concept set is absent. Assign
`parameterized` only after the versioned `SYNTH_CONCEPT_SET` and every required
window, mapping, and exclusion parameter are supplied.

```text
SPECIFICATION ONLY — NOT EXECUTABLE
```

## Validation gaps

- Supply and clinically review `SYNTH_CONCEPT_SET`.
- Confirm vocabulary and local-mapping versions.
- Approve `SYNTH_PHENOTYPE_PROTOCOL_001`.
- Verify live physical mappings, join cardinalities, and date semantics.
- Test positive, negative, boundary-window, unmapped-code, and zero-result
  synthetic fixtures.

## Sources

List the reviewed official OMOP/OHDSI documentation,
`SYNTH_PHENOTYPE_PROTOCOL_001`, and the approved `SYNTH_ADAPTER_001` identifier.
