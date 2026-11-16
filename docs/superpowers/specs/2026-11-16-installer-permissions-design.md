# Installer destination-permission repair

The user approved regression-first repair and GitHub publication on 2026-11-16.
The scope is the observed owner-restricted Windows staging ACL, not the unrelated
historical intermittent cleanup anomaly. Existing approved consultation changes
are included in the same patch release, v0.11.1, after fresh verification.

## Approaches and implementation decision

Post-publication recursive ACL repair leaves an unreadable/partially repaired
installation visible and complicates rollback. Changing all parent ACLs broadens
scope. Instead, before extraction, read the selected destination DACL and copy
it to the installer-owned empty temporary container as a protected DACL. Newly
created staged descendants inherit that policy just as normal destination
children do. Do not copy owner/SACL or grant fixed principals. Windows APIs
GetNamedSecurityInfoW/SetNamedSecurityInfoW provide bounded native operations;
free their security-descriptor allocation with LocalFree. Other platforms retain
existing modes and atomic rename behavior. This implementation choice is the
agent's within the user-approved repair, not a separate user selection.

Fail before publishing or moving an existing installation if permission setup
fails; preserve parent policies, competing targets and rollback ownership.
A null destination DACL is rejected rather than installing with unrestricted
access. Tests force restrictive temporary ACLs so Python 3.11 and 3.13 exercise
the same failure. Test both new and overwrite installs and descendant reads.

Reference: Microsoft Learn GetNamedSecurityInfoW and SetNamedSecurityInfoW.
No new dependency or shell ACL utility is required by the installer.
