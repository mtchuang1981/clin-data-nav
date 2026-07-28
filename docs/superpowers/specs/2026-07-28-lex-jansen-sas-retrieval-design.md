# Lex Jansen SAS Retrieval Contract Design

**Date:** 2026-07-28

## Goal

Make SAS optimization and implementation requests trigger a traceable,
domain-restricted Lex Jansen literature search when network tools are
available, without treating historical examples as standards or copying code
whose reuse terms are unknown.

## Scope

This change strengthens the existing declarative Skill. It does not add an
HTTP client, crawler, downloader, or runtime dependency. The host agent remains
responsible for using its available browser or search tools.

The contract applies when a request asks to optimize, refactor, debug, review,
or derive SAS implementation logic. Official standards, regulatory guidance,
the protocol, and the SAP remain authoritative for definitions and
study-specific rules.

## Retrieval Contract

For an unresolved SAS implementation claim, the agent must:

1. Search official SAS documentation and governed sources first.
2. Run a targeted query using the shape
   `site:lexjansen.com <deliverable-or-domain> <technique> SAS`.
3. Open and review the specific paper, not only an index entry or search
   snippet.
4. Record the paper title, authors, conference, publication year, stable URL,
   access date, relevant technique, applicability, platform or version
   caveats, and limitations.
5. Record provenance for any discussed code fragment and inspect its stated
   copyright, license, or reuse terms.
6. Paraphrase the technique or produce a clean-room implementation when reuse
   permission is absent or unclear.
7. Compare the evidence with the governing source and the target program's
   tests, performance evidence, and runtime constraints before recommending an
   optimization.

The agent must not claim that a Lex Jansen paper was reviewed when network
access or the full paper was unavailable. That condition becomes an explicit
validation gap.

## Output Boundary

Lex Jansen remains secondary implementation evidence. It cannot redefine
CDISC terminology, override a protocol or SAP, validate an institutional
schema, or by itself promote code to `executable` or `validated`.

The response should identify the exact reviewed paper and explain how the
technique applies. It must not describe a generic search result as evidence,
silently paste historical SAS code, or claim performance improvement without
measurement.

## Testing

Extend the public eval catalog with a SAS optimization case. A passing response
must include the domain-restricted search, paper-level review, source metadata,
code provenance and reuse terms, performance validation, the secondary-source
boundary, and the no-network validation gap. Unsafe responses that treat the
index as an official authority or allow unattributed copying must fail.

Update catalog-count assertions from six to seven cases. Run the focused eval
tests first, then the complete Python 3.11 suite and all four repository gates.
