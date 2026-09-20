# Synthetic OMOP metadata connector scenarios

This catalog is a deterministic repository behavior contract for the optional
OMOP metadata connector. It is separate from `evals/cases.yaml`, whose twelve
response-evaluation cases remain unchanged.

All payloads use synthetic fixtures and public canonical OMOP names. The
authorized scenarios exercise only the repository's synthetic callable seam;
they are not evidence from a live MCP service, database, clinical setting, or
human-effectiveness study.

`implementation-ready` is a ceiling for connector evidence only. It can apply
only after all other readiness prerequisites are met, and it never makes a
metadata-only result executable or validated. Non-standard deviations are
represented solely by aggregate counts; their names are intentionally absent.
