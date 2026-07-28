# Retrieval Playbook

Use this playbook to convert a clinical-data question into a traceable evidence
record without confusing public guidance with local implementation facts.

## Decompose the question

Separate every material claim into four layers:

| Layer | Resolve with | Typical output |
|---|---|---|
| Standard | Official standards, regulators, governed terminology | Definition, variable semantics, terminology version |
| Study-specific | Protocol, SAP, analysis plan, approved phenotype | Population, endpoint, window, censoring, derivation |
| Implementation | PHUSE, Lex Jansen, official software documentation, reviewed methods papers | Technique, pseudocode, platform caveat |
| Institutional | Approved versioned Adapter and live metadata | Grain, physical mapping, keys, coverage, runtime validation |

Do not resolve one layer with evidence from another. In particular, do not use
a conference implementation paper to redefine an official standard or use a
public institutional description to infer a physical schema.

## Search in authority order

1. Search official standards and regulatory sources first.
2. Search the protocol, SAP, and other approved study documents for
   study-specific rules.
3. Search official software documentation and peer-reviewed methods sources.
4. Search PHUSE and Lex Jansen for implementation experience and examples.
5. Request an approved versioned Adapter and live metadata for institutional
   facts.

Treat Lex Jansen as an implementation-literature index. It is not a
standards-setting organization, regulator, or validation authority. Verify the
paper itself and preserve its conference year and scope.

## Search Lex Jansen for SAS implementation evidence

Use this contract when a request asks to optimize, refactor, debug, review, or
derive SAS implementation logic and official sources do not resolve the
implementation claim.

When network search is available:

1. Run at least one targeted query in this form:
   `site:lexjansen.com <deliverable-or-domain> <technique> SAS`.
2. Open the specific paper from `https://www.lexjansen.com/` or its linked
   original source. Do not treat an index record, result title, or snippet as a
   reviewed paper.
3. Record the actual query, search date, paper title, authors, conference,
   publication year, stable paper URL, access date, relevant section or page,
   applicability, SAS platform or version caveats, and limitations.
4. For any code fragment, record its paper and page provenance, whether it is
   quoted, adapted, or independently reimplemented, and the stated copyright,
   license, or reuse terms.
5. When permission to reuse code is absent or unclear, describe the technique
   or create a clean-room implementation instead of copying the fragment.
6. Compare the technique with governing definitions and with the target
   program's fixtures, logs, benchmarks, and runtime constraints. Do not claim
   that code is faster or optimized without target-environment measurement.

When network search or the full paper is unavailable, write `not searched` or
`not reviewed` in the evidence record, preserve the planned query, and list the
missing review as a validation gap. Do not convert an unavailable search into a
claim that no evidence exists.

## Build search units

Create one search unit per unresolved claim. Combine:

- the domain or deliverable, such as `ADAE`, `SDTM`, `OMOP`, or `claims`;
- the exact concept, such as treatment emergence or observation window;
- the authority class, such as CDISC, FDA, protocol, or official software
  documentation;
- a version, publication date, or snapshot when the claim can change.

Stop searching once the governing claim is supported and limitations are
known. Do not collect broad background that does not change the contract.

## Record evidence

Capture these fields for every evidence item:

```yaml
claim: "SYNTH_CLAIM"
source: "SYNTH_SOURCE"
authority_level: "official | study-specific | peer-reviewed | implementation | institutional"
publication_date: "YYYY-MM-DD or unknown"
version_or_snapshot: "SYNTH_VERSION_OR_SNAPSHOT"
applicability: "SYNTH_APPLICABILITY"
limitations: "SYNTH_LIMITATIONS"
```

Use a stable source link, identifier, or owner-approved document reference.
Write `unknown` rather than guessing. Mark a statement as inference when the
source supports the premises but not the exact claim.

## Reconcile conflicts

For each conflict:

1. Identify which layer owns the claim.
2. Prefer the primary authority for that layer.
3. Preserve both sources and explain why one governs.
4. Convert the decision into a contract rule.
5. List unresolved version, applicability, or metadata questions as validation
   gaps.

For institutional discrepancies, treat approved live metadata as the current
technical observation and the versioned Adapter as the governed interpretation.
Escalate disagreement to the source owner; do not silently choose a mapping.

## Apply the delivery boundary

Deliver evidence and a logical contract when institutional mappings are
missing. Use placeholders for physical objects and emit
`SPECIFICATION ONLY — NOT EXECUTABLE`. Advance maturity only after the required
Adapter, parameters, live metadata, and fixtures are supplied.
