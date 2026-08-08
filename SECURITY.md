# Security policy

## Supported versions

The newest published release line receives security fixes. As of 2026-08-09,
that line is `0.3.x`.

| Version | Supported |
|---|---|
| `0.3.x` | Yes |
| `< 0.3` | No |

Support and response timing are best effort. This project does not promise an
acknowledgement or remediation service level.

## Report a vulnerability

Never put secrets, credentials, personally identifiable information (PII),
protected health information, private data dictionaries, private Adapter
contents, login-gated documents, or an exploit payload containing such
material in a public issue.

On 2026-08-09 (Asia/Taipei), GitHub's read-only repository API reported that
private vulnerability reporting is enabled for this repository. Submit a
private report through
`https://github.com/mtchuang1981/clin-data-nav/security/advisories/new`; do not
put vulnerability details, samples, or sensitive payloads in a public issue.
If the private form is unavailable to a reporter, open a public issue
containing only a non-sensitive request for private coordination. A maintainer
can then arrange a private channel before details are exchanged. An ordinary
security concern that contains no sensitive material may be reported in a
public issue.

Repository state can change. Maintainers must re-read the setting rather than
treat this dated observation as current proof.

## Accidental private-data response

Do not submit private institutional data, credentials, Adapter contents, or
login-gated documents to this repository. If such material is submitted or
suspected, treat the event as an incident and follow this response immediately:

1. Stop merge and distribution of the affected material.
2. Remove branch or pull request access where possible.
3. Notify repository maintainers and the governing data owner.
4. Rotate potentially affected credentials.
5. Use GitHub's sensitive-data removal procedure.
6. Do not rely on a later deletion commit to erase history.

Coordinate disclosure and remediation with the governing data owner before
resuming normal review or distribution.
