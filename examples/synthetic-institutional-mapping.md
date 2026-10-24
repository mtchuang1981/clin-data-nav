# SYNTH_INSTITUTION Encounter Mapping

Output depth: implementation specification
Decision: Specify logical encounter-to-person mapping without executable institutional code.
Confirmed facts: This is a fictional mapping request, not a current institution-owned contract.
Assumptions: The synthetic scenario supplies an approved dictionary describing logical encounters and persons; this hypothetical approved dictionary is not verified real-world approval.
Limitations: Adapter approval, live metadata, coverage and target-environment fixtures remain unverified.
Sources actually consulted: Current request only; SYNTH identifiers are fictional scenario artifacts, not reviewed private documents.

## Governing evidence

Only an approved versioned Adapter may establish physical mappings. The assumed
dictionary supplies logical roles, not live availability or execution authority.

| Claim | Governing source to review | Authority | Applicability | Limitation |
| --- | --- | --- | --- | --- |
| Encounter grain | SYNTH dictionary | Institutional dictionary | Fictional encounter role | Approval assumed; live comparison absent |
| Allowed join | SYNTH Adapter | Institutional Adapter | Encounter-to-person | Version/cardinality unverified |
| Output restriction | SYNTH governance rule | Institutional governance | Aggregate output | Scope needs explicit approval |

## Data contract

- Grain: one logical record per approved encounter occurrence.
- Keys: encounter/person identity are logical roles. Physical names and
  nullability remain pending owner confirmation.
- Join: many encounters to one person. Non-null person keys match at most one
  person. The join must not multiply encounter records.
- Time precision: day-level is a synthetic assumption. An approved Adapter must
  establish actual precision and start/end precedence.
- Coverage: require a dated site/coverage snapshot. Missing/out-of-scope values
  remain unknown, not absent.
- Sensitivity/output: restricted inputs and approved aggregates only. No
  row-level identifiers or direct-identifier output.
- Lineage: retain approved Adapter, dictionary, governance and transformation
  version identifiers outside the public repository.
- Acceptance: unique/orphan keys, multiplying joins, boundary dates and
  prohibited outputs. Compare presence, types, nullability, precision and
  coverage to approved current metadata. If there are discrepancies, use this sequence:
  1. Stop.
  2. Request owner-approved corrections.
  3. Retest.

## Code maturity

`dictionary-specified` under the synthetic dictionary assumption above.

## Validation gaps

| Gap | Blocks | Next safe action | Responsible role | Completion evidence |
| --- | --- | --- | --- | --- |
| Current Adapter unavailable | Physical mapping | Obtain authorized version summary | Adapter owner, pending confirmation | Versioned approved contract |
| Live comparison not reviewed | Maturity upgrade | Seek metadata-only authorization; resolve discrepancies | Data owner | Approved current comparison, no raw schema in Git |
| Precision/coverage unknown | Analysis scope | Confirm logical requirements with source owner | Source owner | Dated coverage/precision approval |
| Output approval pending | Aggregate delivery | Confirm release scope | Governance reviewer | Explicit scoped approval |
| Fixtures not run | Acceptance claim | Prepare cases for authorized testing | Implementation reviewer | Passing cases and review |

Work still possible: refine the logical checklist and acceptance cases without
guessing physical objects, obtaining patient rows or executing joins.

## Execution gate

Unmet. Before promotion, reassess all relevant execution gates. Closing one gap
does not upgrade maturity or expand metadata-only permission.

SPECIFICATION ONLY — NOT EXECUTABLE
