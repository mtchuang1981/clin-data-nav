# OMOP connector 1.1 private conformance checkpoint

This record contains only reviewed aggregate outcomes, public identifiers,
timestamps, and hashes. Exported responses and private diagnostics remain
outside the repository.

## Scope

- Public implementation: `e92203006397045f2163c5850c91d387e529f251`.
- Explicit contract: `1.1`; OMOP CDM version: `5.4`.
- Allowlist: `omop-v54-core-research-v1`, version `1.0.0`.
- Public catalog SHA-256:
  `300646898e87297b8b75b013fd8398b361e0426e89ec8bfe698757d5f57b0e1e`.
- A new redacted export was generated using the existing private exporter.
- The existing offline checker evaluated that export without changing its
  contract, status rules, or exit codes.
- Inspection observation: `2026-10-01T23:59:19+08:00`.
- DQD check time: `2026-10-01T15:16:06+08:00`.

## Verified outcomes

| Check | Result |
|---|---|
| Live capabilities | Contract 1.1; metadata read-only; no row access, SQL execution, or raw-schema export |
| Inspection scan | Complete |
| Closed contract and summary validation | No validation codes |
| Offline structural status | `incompatible`; checker exit `3` |
| Missing required tables / columns | 0 / 0 |
| Type / primary-key differences | 0 / 0 |
| Table-level foreign-key status differences | 13: 12 `missing`, 1 `unknown` |
| Column nullability differences | 5 |
| Unexpected tables / columns | 1 / 0 |
| DQD FK requirements expected / checked / failed | 79 / 79 / 0 |
| DQD evidence status | `weak-binding` |
| Snapshot binding kind | `size-mtime`; no strong binding digest |

The table-level FK count is not a count of violated data rows or failed DQD
checks. The zero DQD failure count does not establish database-enforced FK
constraints. DQD results were reused from their recorded check time; this
export and checker run did not execute DQD again.

Controlled limitations are `constraint-metadata-limited` and
`tbls-normalization-limited`.

## Integrity

- Capabilities file SHA-256:
  `7c8aa3c640f6924426124ab22f1c54f7f5b6698d6344e483408b7a1f98168bfb`.
- Inspection file SHA-256:
  `2d257f3d00a72594fc8ad159a117022ea4c7e9cb1e71f90dc933f86cf92601a9`.
- Contract `summary_sha256`:
  `45b78290d07d0ba1f89f45c565b29243b33e463eb69af54e851e7b9b68d6570b`.

The file hash covers the exported file bytes; `summary_sha256` covers the
contract's canonical object with the summary hash field omitted. They serve
different purposes and need not be equal.

## Remaining acceptance work

1. The earlier two-failure aggregate has been traced to two failed
   supplementary vocabulary FK checks in the historical audit. A category-only
   audit filter excluded them. The private operator must still establish
   snapshot lineage and the change that removed those violations.
2. Bind the inspection and DQD evidence to the same immutable snapshot or
   content hash, retain the supporting evidence privately, and export a new
   summary. Do not create a digest from size and modification time and label it
   as strong binding.
3. Resolve or explicitly document the five nullability differences, the
   missing/unknown FK declarations, and the unexpected-object count in the
   private environment. Preserve truthful structural reporting.
4. Run the existing checker on the resulting external export and report
   structural status and DQD evidence status independently.

## Private operator acceptance handoff

Use the existing exporter and checker for the next run. The private operator
must retain the following evidence outside the public repository:

- A stable snapshot for both DQD and metadata inspection. Use an immutable
  snapshot identifier supplied by the private storage system, or a content hash
  of a frozen snapshot. Hashing a database while ETL can still change it does
  not establish a common snapshot.
- A record that identifies how the binding was produced and establishes that
  both inspection and DQD used that snapshot. The two contract binding digests
  must match; a new digest alone cannot repair evidence from a different
  snapshot.
- Per-requirement execution results for the exact 79 public FK requirements,
  with the expected set digest, check time, and aggregate failure count.
- Snapshot and change lineage for the historical two-failure aggregate. The
  failed checks have been located, but their transition to passing results
  does not establish the underlying remediation or snapshot equivalence.
- Private disposition of the structural differences and unexpected-object
  count, followed by a new complete redacted export.

After the new export, run the checker with `--contract-version 1.1` and a
current RFC 3339 timestamp such as `YYYY-MM-DDTHH:MM:SS+08:00`. Acceptance of
DQD attestation requires strong binding, exact coverage, current evidence, and
zero failures. Structural compatibility still requires the existing structural
checks to pass. An accepted DQD attestation can coexist with `incompatible`
structure and exit `3`; documenting a constraint limitation does not change
that outcome.

The next public record should contain only the two computed statuses,
contract-approved counts, timestamps, controlled limitations, and hashes.

## Historical audit reconciliation follow-up

An explicitly authorized read-only follow-up on 2026-10-02 inspected retained
audit results across all check categories, rather than limiting the query to
one category. The audit generated at `2026-09-28T21:31:09` contains two failed
supplementary vocabulary FK checks. Those checks were excluded by the earlier
category filter, which explains why that query could not locate them.

The audit generated at `2026-10-01T20:48:31` reports the corresponding two
checks as passing, with zero violations. No private target names, row counts,
diagnostic text, or audit payloads are recorded here. This result locates the
historical failures and corrects the earlier audit-query interpretation; it
does not prove which private remediation changed the result.

The follow-up live inspection at `2026-10-02T00:20:53+08:00` still reports
79 checked FK requirements, zero failed checks, `size-mtime` binding, and no
strong snapshot binding digest. The existing offline structural verdict
remains the latest validated structural outcome; the follow-up live response
was not substituted for the exported bytes checked above.

## Engineering verification

The full suite passed: **1,379 passed, 5 skipped** in 226.85 seconds. The skips
cover filesystem symlink/reparse-point support (four tests) and a POSIX-only
directory-descriptor cleanup contract (one test).

The following checks also exited `0`:

- `python scripts/validate_skill.py`;
- `python scripts/check_public_boundary.py` (repeated after adding this record);
- `python scripts/package_skill.py --check-reproducible`;
- `python scripts/render_omop_catalog.py --check`;
- `git diff --check`.

Automated connector tests use synthetic institutional inputs and the pinned
public catalog; they do not call the private MCP. The private checkpoint above
is a separate, explicitly authorized external-response validation.

## Claim boundary

The connection and closed metadata contract are usable for integration testing.
This checkpoint does not establish structural compatibility, accepted strong
DQD attestation, study fitness, clinical validity, or analysis execution
readiness. No merge, push, tag, or release is part of this verification run.
