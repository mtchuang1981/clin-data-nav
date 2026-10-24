# Project-wide STE-inspired editing and release design

Status: approved by the user on 2026-10-24, including comprehensive editing and v0.11.0 publication.
Date: 2026-10-24 (Asia/Taipei).
Base: `67682af339a1e4ba7f3eb81940bf89505cdd3235`.

## Request and outcome

The user requests project-wide STE-principle editing followed by a new GitHub
release. Publication is explicitly requested; this design does not request
publication permission again. The user approved the comprehensive editing
boundary and version `v0.11.0`.

The outcome is clearer current English and Traditional Chinese instructions,
not formal ASD-STE100 certification. The new release also includes the already
merged but unreleased STE passages and opt-in bilingual research heading
contract. Do not replace or move `v0.10.0` or its published assets.

## Approaches

1. **Selected breadth: all current public guidance.** The user explicitly
   selected project-wide editing over the earlier four-passage pilot. Review
   every maintained guidance file below. Edit unclear prose, but retain text
   that already satisfies the principles. Coverage does not mean every file
   must change.
2. **Rejected: mechanical rewrite of every repository text file.** This would
   change frozen protocols, benchmark fixtures, fixed output labels and
   historical evidence. It conflicts with existing public and audit boundaries.

The preservation boundary and minor version were the implementer's
recommendations, subsequently approved by the user.

## Current guidance coverage

Track every file as edited, reviewed/retained, or protected, with a short reason.

- Root: `README.md`, `README.zh-TW.md`, `CONTRIBUTING.md`, `SECURITY.md`,
  `.github/pull_request_template.md`, and the repository's tracked `AGENTS.md`.
  Do not change external or machine-level user instructions.
- Current `docs/`: architecture, installation EN/TW, glossary EN/TW,
  learning paths EN/TW, release process and repository settings.
- Installable Skill: all of `skills/clin-nav/SKILL.md` and the nine Markdown
  references. Review `agents/openai.yaml` for consistency, without changing
  discovery/invocation policy or adding features to the UI metadata.
- The three tracked synthetic Markdown examples under `examples/`.
  Preserve their output labels, maturity, safety marker and factual content.
- Current Eval operation READMEs: core, benchmark, compiler pipeline,
  effectiveness, governance, recovery, OMOP connector and research headings.
- Explanatory schema guidance: benchmark `summary-schema.md` and
  effectiveness `input-schema.md`. Preserve every field name and constraint.
- Governance and recovery checklists in English and Traditional Chinese.
  Keep every approval condition and required evidence item unchanged.

The inventory uses tracked public files only. Do not inspect ignored/private
folders, local adapters, consultation ZIPs, human answers, research task packs
or participant materials. Preserve the unrelated, untracked
`docs/optimization-backlog.md`; its presence is not permission to submit it.

## Protected content

- Historical `docs/verification/`, released notes under `docs/releases/`,
  existing design/implementation plans, existing changelog sections and tags.
  Add new release entries/records, not historical rewrites.
- Study protocols, benchmark inputs/attestations/results, response fixtures,
  generated synthetic reports and fixed report templates. These define or
  demonstrate existing contracts; do not rewrite them to meet style targets.
- Program source, executable code blocks, command syntax, paths, URLs,
  citation identities, JSON/YAML schema keys, hashes, identifiers and accepted
  contract vocabularies. Version synchronization is the explicit exception.
- License/third-party attribution text and disclosure rules.

Reviewers may identify an actual behavioral defect. Record it separately;
do not silently change behavior as part of prose editing.

## Writing rules

### English

Use a single action per procedural sentence, conditions before actions,
active voice where its actor is known, short sentences, consistent technical
terms and vertical lists. Use the STE procedural/descriptive length principles
as review signals, not an indiscriminate regex gate over code, tables or labels.
Preserve citations and necessary clinical/scientific distinctions.

Do not mechanically convert `should` or `may` into `must`. Do not apply the
toolkit's absolute vocabulary substitutions when they change normative strength.
Do not replace technical tokens such as `main`, paths or schema fields.

### Traditional Chinese

Use Taiwan terminology, conditions before actions, one action per step,
explicit actors and consistent terms. Synchronize the meaning of English and
Chinese guides. Do not impose English word counts or claim that Chinese text
is formally STE-compliant. Do not create a Chinese Skill clone or translate
fixed English output labels as part of this task.

### Preserve semantics

Before editing a passage, identify its conditions, required/optional actions,
prohibitions, quantities, sequence and failure/stop behavior. Compare those
items after editing. Do not turn authorization-dependent operations into
unconditional numbered steps. Do not turn a missing source into verified evidence,
a fixture pass into permission, or metadata verification into executable maturity.

## Version and delivery

Approved minor version: `0.11.0`, because the published package gains the
previously merged opt-in bilingual heading capability as well as comprehensive
instruction edits. Both heading contracts retain their current behavior:
`legacy-v1` is default and `research-bilingual-v1` remains explicit opt-in.

Use existing version/changelog/packaging/release tools. Synchronize current
metadata, installer/packager, citation metadata, bilingual changelogs, current
README/installation pointers, version tests and new `docs/releases/0.11.0.md`.
Do not claim candidate hashes are published before download verification.
If that tag/version already exists, stop rather than overwrite it.

Use a normal checked PR for main integration; never direct-push main, force
push, use admin bypass or alter protection settings. After main's own gates
pass, create the new annotated tag at that exact commit and dispatch the
existing Release workflow from main. Download and verify exactly the ZIP and
manifest against local reproducible builds and their SHA-256 values.
Publish the verification record/current installation pointers through a normal
post-publication PR without moving the tag or replacing assets.

## Validation and stopping rules

- Use the existing evaluator, synthetic fixtures and four required gates.
  Add a failing test before a behavior change. Do not add wording-only tests
  for human prose or weaken existing semantic/safety checks to fit the rewrite.
- Verify the 36-cell legacy output digest remains
  `6c7db3794be2f5b74107a27ae9dae5e385aa82cfabb98be691bf4b67b72b8757`.
  Keep opt-in heading tests and canonical vocabulary unchanged.
- Run full pytest on official Python 3.11.9, Skill validation, public boundary,
  reproducible packaging, generated-summary/report checks and diff checks.
- Record an inventory with no unexplained coverage gaps and perform a fresh
  independent semantic/English-Chinese consistency review before integration.
- Require Windows and Ubuntu verification, cross-platform package comparison
  and CodeQL on the exact PR/main commits. Require no skipped verification
  step and no unresolved relevant security alert; do not dismiss alerts.
- Two fresh local builds and the downloaded Release pair must match the
  expected bytes/hashes. Verify tag object, peeled commit and asset identities.
- Stop publication on a new failure, unexpected private content, changed
  permissions or a semantic change that cannot be safely resolved as an edit.
  Do not claim the old unexplained Windows cleanup anomaly has been fixed.

## Claim boundary and non-goals

Report document coverage, preserved contracts, test results and artifact
identity. Do not claim formal STE certification, reduced token use, better
model answers, clinical effectiveness or institutional deployment approval.
No model benchmark campaign, private Adapter access, human evaluation,
source-freshness campaign, new research method, new connector behavior or
automatic migration to the new heading contract is included.

## Implementation choice

Recommend inline implementation in staged language/document groups and one
final independent review, using existing tests and release scripts. This
limits repeated context/model cost. The builder may choose paragraph/list
layout and retain already-clear text; it may not change these boundaries.
