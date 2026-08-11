# Governance documentation readiness

## Purpose and authority boundary

This public pack helps a study owner check whether twelve categories of
governance documentation have references ready for institutional review. It
does not decide which ethics pathway applies, evaluate the contents of any
document, provide legal advice, or replace an IRB, REC, legal, privacy,
data-owner, security, or other institutional authority.

The validator can report only `incomplete` or
`ready-for-institutional-review`. Its authorization field is always
`not-authorized-to-recruit`. Exit code 0 therefore means documentation
readiness only; it never authorizes recruitment or any human-study activity.

## Public files and external instance

- [readiness-template.json](readiness-template.json) is a valid but
  `incomplete` public template.
- [synthetic-readiness.json](examples/synthetic-readiness.json) demonstrates a
  structurally complete result. Its `SYNTH.*` references are test data, not
  evidence.
- [checklist.md](checklist.md) and
  [checklist.zh-TW.md](checklist.zh-TW.md) describe the same twelve controls in
  English and Taiwan Traditional Chinese.

Copy the template to an approved location outside this repository and complete
it there. A real completed instance, its evidence, and any mapping from opaque
reference tokens to documents must never enter Git. `study-governance/` is
ignored and rejected as a safety net, but an ignored folder inside the checkout
is still not an approved storage location.

## Prepare without authorizing

Record one role-owned evidence reference for each documented control. A
reference is an opaque identifier, not a path, URL, person, institution,
decision, excerpt, or sensitive value. Keep a control `not-documented` with a
null reference until its external documentation exists.

The `protocol_commit` identifies the fixed study protocol version being
prepared. The current public protocol is [protocol.md](../protocol.md), and the
study input boundary is documented in [input-schema.md](../input-schema.md).
The [2026-08-11 offline dry-run evidence](../../../docs/verification/2026-08-11-effectiveness-offline-dry-run.md)
shows pipeline operation without people; it is not governance approval or
effectiveness evidence.

## Validate an external instance

Replace `<external-dir>` with the approved repository-external location:

```bash
python scripts/validate_governance_readiness.py --input <external-dir>/governance-readiness.json
```

The command emits only a sanitized aggregate summary: schema version, readiness
status, constant authorization boundary, documented and required counts, and
missing control IDs. It never prints input paths or evidence references.

## Interpret exit codes

| Exit | Meaning | Required action |
|---|---|---|
| 0 | Valid and `ready-for-institutional-review` | Submit through the institution's applicable process; do not recruit. |
| 3 | Valid but `incomplete` | Complete the listed control categories externally; do not submit or recruit. |
| 2 | Invalid input, unsafe path, unreadable file, or usage error | Stop and correct the external instance without copying it into the repository. |

Every valid result remains `not-authorized-to-recruit`.

## Stop rules

Stop preparation and do not proceed when any required control is undocumented,
the protocol commit is wrong, a real instance is inside the repository, an
evidence reference contains a path or sensitive value, or an institutional
owner has not accepted responsibility for the next step. Follow
[SECURITY.md](../../../SECURITY.md) if sensitive material may have entered the
public checkout.

## Next institutional step

After exit code 0, give the external pack and its separately governed evidence
to the responsible institutional channel. The institution determines the
applicable pathway, required changes, and whether later human-study actions may
occur. Record those outcomes only in the approved external system; this schema
intentionally has no approval or recruitment-authority field.

Return to the [effectiveness evaluation framework](../README.md) only after the
separate authority required for the next stage has been documented externally.
