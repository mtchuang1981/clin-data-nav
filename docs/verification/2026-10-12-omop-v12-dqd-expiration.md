# OMOP 1.2 independent DQD expiration verification

Date: 2026-10-12. Scope: public implementation and synthetic evidence only.

## Delivery and claim boundary

Explicit 1.2 adds `max_dqd_evidence_age_seconds` to capabilities and the hashed
inspection summary. Null policy requires `allow_nonexpiring_dqd=True` or
`--allow-nonexpiring-dqd`; metadata freshness remains finite. Default 1.0 and
explicit 1.1 retain their behavior. DQD attestation cannot change structural
compatibility, mismatch counts or checker exit codes.

No private MCP call, adapter source/config read or change, SQL, data-row access,
DQD execution, benchmark rerun, version bump, tag, release or push was performed.
Private 1.2 implementation and current-snapshot binding audit remain pending.
This record does not claim the private deployment has non-expiring evidence.

## Tests and gates

Tests use the existing local Python 3.11.9 validation runtime, with bytecode
disabled. Full pytest uses `-p no:cacheprovider` to avoid local cache writes.

| Check | Observed result |
| --- | --- |
| Clean writable E-worktree baseline | 1748 passed, 13 skipped; 174.33s; exit 0 |
| Task 1 RED | 19 failed, 11 passed: unsupported policy/version |
| Portable schema RED | 1 failed, 32 passed: 1.2 schema absent |
| Task 1 focused GREEN | 182 passed; 2.45s; exit 0 |
| Task 2 RED | 32 failed, 2 passed: missing consent API/CLI support |
| Tasks 1/2 focused GREEN | 216 passed; 22.76s; exit 0 |
| Full pytest after public changes | 1815 passed, 13 skipped; 171.02s; exit 0 |
| `python scripts/validate_skill.py` | exit 0 |
| `python scripts/check_public_boundary.py` | exit 0 |
| `python scripts/package_skill.py --check-reproducible` | exit 0 |
| `python scripts/render_omop_catalog.py --check` | exit 0 |
| `git diff --check` | exit 0 |

The skips are Windows/environment cases: unavailable symlink/reparse privileges,
case-distinct siblings, trailing-space paths and POSIX dir-fd cleanup. No test
was suppressed to relax the expiration contract.

The initial native C-worktree baseline had one environment failure:
`test_renderer_check_mode_detects_changed_checked_in_catalog` could not write its
temporary stale catalog because the checkout was outside writable roots.
It had 1747 passes and 13 skips. The same test passed in the writable E checkout;
no catalog/test behavior was relaxed. The native checkout was retained detached.

## Scope and manual review

Only packaged validator/assessment/CLI, portable schema, synthetic tests and
connector/installation documentation changed. Legacy fixture bytes, public
catalog, Skill routing, agent metadata, Eval catalog, versions, CHANGELOG and
release assets were not modified. Routing and Eval ownership/execution boundaries
were reviewed for consistency. No raw live responses or private material is
included in this record or Git.

## Execution rulings

1. Manual ledger/task briefs replaced Bash bookkeeping helpers because the local
   tool could not resolve basename/dirname. Risk: bookkeeping drift; reconcile
   against commits and approved task text.
2. Use the ignored E worktree after native C writes were denied. Risk: an extra
   retained checkout; no permissions or validator rules were weakened.
3. Human documentation received manual contract review rather than grep-based
   tests, following writing-good-tests. Risk: prose drift requires review;
   executable behavior has RED/GREEN and subprocess tests.

## Independent review

One fresh-context read-only whole-branch review of base `5398003` through
`19e6bb4` found no Critical or Important issue and judged the branch ready to
merge. The reviewer reran 57 tests and 24 complete synthetic adversarial checks;
it did not rerun full pytest or mutate files. No local merge is authorized by
this record.

Deferred non-blocking minors:

1. New CLI tests exercise the repository wrapper and packaged source entry
   point, not a newly unpacked installation, and compare selected safe fields
   rather than complete stdout/stderr byte equality. Add that installed-artifact
   comparison in a future test improvement; do not claim it was performed here.
2. Standard JSON Schema integer semantics can accept integral `1.0`; the Python
   contract validator rejects floating values. Schema-only success is not full
   contract acceptance. Current strict execution paths reject these inputs;
   future documentation should make the portable-schema limitation explicit.

Final ruling on the reviewer's declined-to-judge item: private consistent-snapshot
binding, DQD execution correctness and evidence invalidation remain private-owner
audit duties — access was prohibited and public attestation cannot establish
them — risk: only public contract readiness, not private conformance, is proven.

Private conformance remains a separate handoff using fresh repository-external
1.2 summaries; never convert old 1.1 artifacts.
