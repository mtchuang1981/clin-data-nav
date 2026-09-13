# Evidence Ledger Contract

Use this optional JSON ledger when the user requests a machine-auditable or
repeatable evidence record for an evidence navigation, research design, or
implementation specification. Keep quick explanations concise unless the user
explicitly asks for the ledger.

The ledger records review state; it does not prove that a source is correct,
current, applicable, or sufficient for a clinical decision. Save actual
ledgers outside the Skill and source repository because they may contain
sensitive research context. The checked-in JSON is synthetic structure only.

## Fail-closed rules

- Use schema version `1` and the exact keys shown below. Use JSON `null` for an
  unknown date, version, or stable identifier; never guess or invent a
  surrogate identifier.
- Set `review_status` to `reviewed` only after opening and reviewing the actual
  source. A search result, abstract-only record, snippet, citation, user mention,
  or model memory is `not-reviewed`. Use `unavailable` when access was attempted
  but the source could not be inspected.
- A `reviewed` source requires `reviewed_on`. The other review states require
  `reviewed_on: null`.
- `direct-support` and `partial-support` require at least one reviewed source
  and a specific `evidence_location`. Use `not-assessed` until those conditions
  are met. Use `unsupported` only when the reviewed material does not support
  the recorded claim.
- `review_due_on` is a review policy date, not a claim that the source expires.
  On or after that date, the checker reports `review-due`; the source is not
  automatically invalidated.
- The command-line `--as-of` date controls the audit. It cannot precede the
  ledger's `prepared_on` date, so an old embedded date cannot suppress a due
  review.
- Keep request-provided facts distinct from external facts and inferences.

## Closed JSON shape

```json
{
  "schema_version": "1",
  "ledger_id": "lowercase-hyphenated-id",
  "prepared_on": "YYYY-MM-DD",
  "sources": [
    {
      "source_id": "source-id",
      "title": "Source title",
      "stable_identifier": "DOI, URL, URN, governed document reference, or null",
      "authority_level": "official | study-specific | peer-reviewed | implementation | institutional",
      "publication_date": "YYYY-MM-DD or null",
      "version_or_snapshot": "version string or null",
      "review_status": "reviewed | not-reviewed | unavailable",
      "reviewed_on": "YYYY-MM-DD or null",
      "review_due_on": "YYYY-MM-DD or null",
      "applicability": "Where this source applies",
      "limitations": "Known limitations"
    }
  ],
  "claims": [
    {
      "claim_id": "claim-id",
      "claim": "Material claim",
      "claim_type": "external-fact | request-provided | inference",
      "source_ids": ["source-id"],
      "evidence_location": "page, section, table, or null",
      "support_status": "direct-support | partial-support | unsupported | not-assessed",
      "applicability": "Where the claim applies",
      "limitations": "Known limitations"
    }
  ]
}
```

See `evidence-ledger-example.json` for a public synthetic instance.

## Offline check

From a source checkout or an installed Skill directory:

```text
python scripts/check_evidence_ledger.py --input <external-ledger.json> --as-of YYYY-MM-DD
```

The checker uses no network. It emits only counts, record IDs, and status—not
claim or source text. Exit `0` means the ledger is structurally valid with no
recorded review item due; exit `3` means the ledger is valid but review remains;
exit `2` means invalid input. Exit `0` is not evidence of scientific validity,
clinical appropriateness, source truth, or deployment readiness.
