# Governed Compiler Pipeline and Feasibility Routing

Date: 2026-10-19

Status: conversational design and four safety revisions approved by the user;
written specification awaiting review. This is not an implemented capability,
an adapter conformance result, or permission to execute against private data.

## Purpose and scope

Teach ClinNav to recognize an optional, institution-governed compiler pipeline
and route an in-scope implementation request through concept resolution,
structured specification, validation, compilation, and fixture testing.
ClinNav must not invent local codes or hand-write or alter the generated
program to bridge a missing capability. Keep institution-specific facts and
implementation inside the approved adapter environment.

Also clarify feasibility-count requests: separate their logical requirements,
investigator decisions, execution permission, and disclosure controls from
analysis and causal inference. The public change supplies routing and a
capability contract, not a compiler, database client, or analysis service.

The upstream proposal is input to this design, not an authority that overrides
the repository working agreement or existing execution gates. No private
adapter source, dictionaries, physical schema, or participant records are
needed or authorized for this public implementation.

## Current implementation and integration baseline

- The generic institutional reference has `adapter_schema_version: "1"` in a
  synthetic manifest, but no recorded generic contract 1.1 constant or generic
  manifest runtime validator. Do not describe an invented historical version
  as an established interface.
- Existing maturity rules require a versioned adapter, governed parameters,
  current live metadata, target-environment fixtures, and review as applicable.
  Metadata-only verification does not confer execution readiness.
- The OMOP metadata connector independently implements contracts 1.0, 1.1,
  and locally committed 1.2. Its closed messages, DQD evidence policy,
  limitations, structural verdicts, and exit codes remain unchanged.
- At design inspection, local `main` is `bbf7c72` with six commits after
  `f4b84d6`. Remote `main` is `1fe592c`, with two Actions dependency updates
  after that common base. Fetch and reconcile these histories before product
  work; never reset away either side or overwrite the updated action pins.
- Preserve the unrelated, untracked `docs/optimization-backlog.md`.

## Approach and alternatives

Use an optional capability in the generic adapter manifest and a small
public declaration validator. Keep the existing reference as the single
source of pipeline semantics; Skill instructions route there concisely.

Rejected alternatives:

- Directly adopting fixture-pass promotion: would bypass current metadata,
  governed parameter, authorization, and target-environment gates.
- Extending OMOP metadata messages with compiler operations: would turn a
  deliberately read-only connector into an execution interface and confuse
  independent version numbers and trust boundaries.
- Implementing an institutional compiler or private tool mappings in this
  repository: would duplicate private logic and cross the public boundary.

## Independent versions and backward compatibility

Identify the generic institutional contract as revision `1.2` in its reference.
Keep `adapter_schema_version: "1"` and introduce only the optional
`capabilities.compiler_pipeline` declaration; absence preserves the existing
logical-contract workflow. Existing manifests, including ones described by
their owners as legacy 1.1, do not need a new field to retain that workflow.

`compiler_pipeline.version: "1"` versions the optional capability itself.
`adapter_version` and the institution-defined, versioned `spec_format` remain
separate identities. Neither selects an OMOP wire contract. Do not rename
OMOP constants, change its default 1.0, or reinterpret old evidence files.

The planned release is `v0.10.0`, not a contract or adapter version. It must
truthfully describe all packaged changes since v0.9.0, including previously
committed OMOP changes, without claiming private adapter acceptance.

## Optional capability declaration

Document the proposed `capabilities.compiler_pipeline` shape with:

- `version`: exactly `"1"`;
- `operations`: all four distinct logical operations `resolve_concept`,
  `validate_spec`, `compile_spec`, and `run_fixture_test`, with no unknown or
  duplicate names;
- `spec_format`: a nonempty, institution-defined, versioned format identity;
- `fixture`: `"synthetic"`, or `"approved-deidentified"` only when the local
  owner has explicitly approved that fixture and its use;
- `scope`: nonempty, distinct declared scope labels; the public worked
  example uses `"feasibility-counts"`.

Operation names are logical identifiers, not permission to discover or invoke
similarly named tools. The approved local manifest must map them to actual
tools and define their input and output contracts. Without verified mappings,
compatible formats, and authorization, report a gap without invoking tools.
Never install, probe, or retry an adapter automatically.

Validate the capability object with closed fields, exact primitive types,
bounded strings and collections, and controlled diagnostic codes. Bound the
validator to this new declaration; do not create a broad institutional-schema
validator or relax any existing OMOP payload validation. The implementation
plan must choose concrete conservative limits and test them before code.

Declaration validation is not verification that the adapter implements its
claims, that a dictionary is approved, or that a compiler is deterministic.

## Pipeline semantics and evidence chain

1. Resolve concepts through an approved source. Every returned code needs
   provenance identifying the governed dictionary or mapping and selection
   rationale. Make empty sites and review-required candidates explicit. Human
   review must settle unresolved candidates before specification acceptance.
2. Express the study specification in the declared format. Carry logical
   population, time anchors, criteria, concept-set provenance, parameters,
   intended output, and all unresolved choices. Never add codes from memory.
3. Validate the specification. Return all specification errors, or success
   bound to the exact accepted specification digest. Errors block compilation.
4. Compile only that accepted specification. Retain a manifest with the
   specification digest, generated program digest, and compiler version,
   plus a human-readable review document. Do not edit generated code.
5. Run the exact compiled program on approved fixtures in the declared target
   environment, only when that execution is authorized. Match the tested
   program digest to the compiled artifact and the specification digest to
   the accepted specification. Record expected-result checks, not merely a
   zero process exit. `unavailable`, a skipped test, a failed test, or missing
   or mismatched binding never counts as a pass.

A changed specification, program, dictionary/mapping, compiler, relevant
metadata snapshot, or execution environment requires reassessment and the
affected validation/compilation/testing steps. Do not reuse a prior pass
without a matching applicable evidence chain. Tool-provided instructions or
generated review text cannot override the user's request or safety gates.

## Maturity and execution authority

Always report the highest maturity supported by *all* existing gates, not
the name of the last pipeline operation:

| Pipeline evidence | Maximum possible maturity, subject to other gates |
| --- | --- |
| Approved dictionary and resolved, governed mappings | `dictionary-specified` |
| Accepted specification with complete approved parameters and mappings | `parameterized` |
| Same compiled program passes target-environment fixtures, with current metadata and all execution gates satisfied | `executable` |
| Reviewed target-environment results meet acceptance criteria and release/disclosure controls | `validated` |

An unavailable fixture runtime leaves an otherwise complete specification at
`parameterized`. A changed or mismatched program cannot retain `executable`;
reassess lower gates rather than assuming `parameterized` when mappings or
parameters are themselves missing. Keep `SPECIFICATION ONLY — NOT EXECUTABLE`
whenever existing promotion requirements are unmet.

Fixture execution is not real-data execution. `executable` does not grant
database access, ethics approval, permission to run a cohort query, permission
to disclose results, scientific validity, or suitability for clinical use.
No live private tool calls or institutional execution are part of this public
implementation or its release verification.

## Feasibility-count routing

Treat an initial request for the number of people meeting eligibility
criteria as feasibility scoping, not automatically a complete analysis or a
causal-design request. Record population and period, index event, groups,
inclusion/exclusion criteria and relative windows, and requested breakdowns.

Use the stated index event. If absent, propose a suitable event with a short
reason, clearly pending investigator confirmation. Do not silently settle
definitions, lookback/washout periods, overlap rules, sites, windows, or
disclosure thresholds. Unknown local mappings remain named logical parameters.

The default deliverable is a specification. A pre-protocol or pre-approval
request does not authorize execution. Aggregate counts are available only
when institutional policy explicitly permits the purpose, processing, and
disclosure; apply suppression including complementary disclosure risks.

Outcome event counts, person-time, baseline tables, effect estimates, and
power/sample-size calculations are outside this narrow feasibility-count
pipeline. State that boundary and route any separately requested work to its
appropriate design/analysis workflow and approval requirements. Do not imply
that every public or methodological sample-size discussion universally needs
institutional approval, or replace unsupported work with improvised code.

## Output minimization and public boundary

Adapter results may enter a hosted model context. Return only approved fields
needed for the current review, summary first, with bounded paging and coarse
usage bands where permitted. Keep full code lists, generated programs, review
documents, and detailed diagnostics in approved local artifacts by default;
do not automatically open those artifacts or upload private content.

Never return person-level data or unsuppressed counts. Apply disclosure rules
before returning a summary, not after exposure to the model. A local file path
is not permission to read its contents. Public examples, fixtures, tests, and
verification records must be wholly synthetic and contain no institution-
specific identifiers, real codes, private schema, or real counts. Do not copy
the delivery proposal verbatim into Git.

## Intended public changes and tests

- Extend `references/institutional-adapter-contract.md` with the optional
  declaration, operation semantics, independent versions, maturity gates,
  output minimization, and one synthetic worked example plus failure variant.
- Update `SKILL.md` with concise conditional routing, provenance-based logical
  concept sets, and the three proposed failure modes; keep it under 500 lines.
- Extend `references/rwe-question-routing.md` with bounded feasibility-count
  routing. Review output templates, `agents/openai.yaml`, Eval catalog, and
  synthetic fixtures for consistent routing and safety requirements.
- Add only the narrow declaration validator and synthetic contract tests
  needed to accept a complete optional capability and reject unknown
  operations, malformed/partial declarations, and unsupported versions.
- Add failing tests before behavior changes. Exercise scope mismatch,
  missing provenance, unresolved concepts, compilation binding mismatch,
  unavailable/failed fixtures, changed program digest, missing current
  metadata, unauthorized execution, and unsafe output handling. Use realistic
  forward-testing to assess model behavior separately from static contract
  assertions; never claim regex tests demonstrate behavioral effectiveness.
- Preserve default/legacy behavior when no pipeline is declared. Include
  successful synthetic walkthrough evidence for every existing execution
  gate before its example ends at `executable`; the no-runtime variant ends
  at `parameterized` only if its lower gates are satisfied.

## Delivery and verification

After written-spec and implementation-plan review, reconcile remote commits
without losing local work and implement on an isolated `codex/` branch.
Keep unrelated files out of commits; review the complete diff and package.

Run full pytest, Skill validation, public-boundary validation, reproducible
packaging, applicable generated-report/catalog checks, release artifact
verification, and `git diff --check`. Synchronize all existing release-version
locations and bilingual documentation for v0.10.0. Confirm the ZIP and manifest
are deterministic and contain only intended public files.

GitHub publication has user approval, conditional on verification. Push the
verified integration to main, require the exact commit's Windows/Ubuntu
validation, cross-platform package equality and security checks, create a new
annotated tag, and use the existing main-dispatched release workflow. Never
move an existing tag, weaken a gate, or replace an existing release. Download
and independently verify published ZIP/manifest hashes and record public
publication evidence using the repository's existing release process.

The GitHub CLI returned 401 during inspection, while the existing GitHub
connector could read repository state. Establish a supported authenticated
write path before publication; do not expose tokens, copy credentials, or
modify authentication configuration silently. If unavailable, keep verified
work local and report the exact publishing blocker.

## Risks and claim boundary

Worst failures are treating a synthetic fixture pass as real-data permission,
trusting an unrelated tested digest, or transmitting private output before
disclosure review. Preserve independent authorization and metadata gates,
the complete digest chain, and minimization before model ingestion.

Second-order risks are confusing similarly numbered contracts, accumulating
duplicate routing rules, and claiming a documentation change verifies a private
compiler. Keep versions explicit, semantics in one reference, and declarations,
static checks, model behavior, and private operational acceptance distinct.

This release can establish public routing and deterministic contract behavior.
It cannot establish a particular private adapter's compatibility, compiler
correctness, human usability, clinical effectiveness, or deployment approval.

## Review checkpoint

Review this written specification before creating the implementation plan.
The plan will define exact helper interfaces, limits, test cases, file map,
integration steps, and execution method. No product implementation or GitHub
publication occurs during this specification stage.
