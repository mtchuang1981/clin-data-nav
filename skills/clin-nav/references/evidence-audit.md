# Optional Evidence Audit

Use only when the user requests source-freshness or citation review records.
Both artifacts stay outside the repository and installed Skill. Quick answers
do not require them. The ledger schema `1` and existing checker remain unchanged.
Historical external audits are not migrated or filled automatically.

This closed contract records human checks, not truth verification. Actually
open sources with authorized research tools before recording review. The checker
does not browse URLs, call MCP, interpret notes or write inputs. The v0.8.0
`pilot-failed` result remains unchanged; examples are synthetic, not a new pilot.

## Binding and limits

Top-level keys are exactly schema_version, ledger_id, ledger_sha256, checked_on,
sources, claims. Audit schema_version is string `1`; ledger_id must match.
Hash the structurally valid ledger as UTF-8 JSON with ensure_ascii=False,
sort_keys=True, separators=(",", ":"), then SHA-256. Object-key order and file
formatting are irrelevant; array order and text are preserved without Unicode
normalization. Each ledger source and claim has exactly one audit row, no extra,
duplicate or missing IDs.

`prepared_on <= checked_on <= --as-of`. Publication, actual review and performed
search dates cannot follow checked_on. Future policy due dates remain allowed;
the old ledger evaluator still decides due review. Unknown dates are not guessed.

Each input is at most 262,144 bytes, container depth 12; maximum 100 sources,
100 claims, 100 source checks per claim, 20 entry points per source. IDs use the
ledger lowercase-hyphen format, at most 80 characters; URLs 2,048; audit notes
and locations 4,000. Reject, never truncate. Reject duplicate keys, nonfinite
numbers including overflow, invalid UTF-8/BOM, trailing JSON, unknown fields,
wrong types and empty required text. All keys are required even for unknowns.

## Source rows

Exact keys and values:

| Key | Value |
| --- | --- |
| source_id | Matching ledger source |
| retrieval_url | Public HTTPS or null if unknown |
| access_status | opened / abstract-only / unavailable / conflicted / not-attempted |
| authority_role | governing / official-product / peer-reviewed-method / implementation / discovery-only |
| use_scope | current / historical / development / not-assessed |
| version_status | current / superseded / in-development / unknown |
| status_basis_url | Public HTTPS status basis or null |
| newer_source_search | Object below |
| notes | Nonempty scope/conflict/correction handling or incomplete-work reason; no source full text |

newer_source_search has exactly performed_on (ISO date or null), entry_points
(unique public HTTPS list), result and nonempty notes. no-newer-found,
newer-found and unavailable mean an attempted search: date and at least one
entry point required. not-performed and not-applicable require null date, empty
entries and explanatory notes. Current scope cannot use not-applicable. Other
scopes may, but that never waives actual source, citation or correction review.

URL syntax checks reject credentials, query, fragment, localhost, IP literals
and single-label hosts. No DNS: an ordinary domain is NOT proof of public access.
Never provide private/login/signed URLs or tokens; use a non-secret public entry
point. Null retrieval/status URL is allowed; absent status basis needs review.

| Access | Required ledger review_status | Verified locator allowed |
| --- | --- | --- |
| opened | reviewed | Yes, with location |
| conflicted | reviewed | Yes, but needs-review remains |
| abstract-only | not-reviewed | No |
| unavailable | unavailable | No |
| not-attempted | not-reviewed | No |

use_scope must reflect ledger applicability and claims. The checker cannot prove
this human assertion. Historical/development superseded, in-development or
newer-found alone does not require review. All scopes need review for non-opened
access, unknown version, unassessed scope, missing status basis or unavailable/
not-performed search. Current scope also needs review for superseded,
in-development or newer-found.

## Claim rows

Exact keys: claim_id, source_checks, authority_fit, support_fit, notes (nonempty).
authority_fit: appropriate / insufficient / conflicted / not-assessed /
not-applicable. support_fit: appropriate / overstated / understated /
not-assessed / not-applicable.

Each source_checks row has exactly source_id, evidence_location (nonempty text
or null), locator_status (verified / not-verified / unavailable). IDs must match
that claim's source_ids exactly, including empty sets. Verified requires a
location and opened/conflicted access. One global boolean cannot replace each
cited source's locator check. Humans reconcile locations and notes with ledger
text; the checker does not interpret paragraphs.

Fit not-applicable is allowed only for request-provided claims without sources;
notes explain this is request-provided, not a verified external fact. The ledger
not-assessed gap still remains. Appropriate means fit to recorded support, not
claim truth. Overstated/understated are valid findings retained for review.

Humans assess authority, applicability, locators and corrections/retractions.
Explain handling in notes without pasting source full text or raw answers. If
incomplete, record not-assessed/conflicted as appropriate. No separate integrity
state machine, regex truth check or automatic correction database query exists.

## CLI and results

```text
python scripts/check_evidence_audit.py --ledger <external-ledger.json> --audit <external-audit.json> --as-of YYYY-MM-DD
```

Repository and packaged CLI share implementation. Exit 2 is invalid-input
(fixed stderr `evidence audit validation failed`); exit 3 is needs-review;
exit 0 is recorded-checks-complete. Completion only means applicable checks are
recorded complete, not source correctness, scientific validity, clinical
effectiveness, deployment readiness or independently verified human judgment.
Invalid takes precedence, then union ALL old ledger gaps with audit gaps.

Summary keys: schema_version, ledger_id, as_of, status, ledger_status,
source_count, claim_count, source_review_items, claim_review_items. Items contain
only source_id/claim_id and sorted unique reasons; IDs sorted. ledger_status
stays complete/review-required. No URL/text/path/unknown key/exception is echoed.
Identical inputs/as-of give identical summaries.

Audit reasons: source-not-opened, scope-not-assessed, version-unknown,
status-basis-missing, newer-search-unavailable, newer-search-not-performed,
current-source-superseded, current-source-in-development, current-newer-found,
locator-not-verified, authority-insufficient, authority-conflicted,
authority-not-assessed, support-overstated, support-understated,
support-not-assessed. Legacy reasons: ledger-review-due, ledger-freshness-unknown,
ledger-source-not-reviewed, ledger-source-unavailable, ledger-source-unidentified,
ledger-partial-support, ledger-unsupported, ledger-not-assessed.

evidence-audit-example.json pairs with the unchanged evidence-ledger-example.json.
ALL review, search, locator and fit results are synthetic assumptions, not actual
checks of example.org. Copy examples outside protected roots for a demonstration.
