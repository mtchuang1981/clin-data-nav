# Effectiveness Incident Recovery and Green-Gate Design

- **Status:** approved design
- **Design date:** 2026-08-11 (Asia/Taipei)
- **Baseline commit:** `845c39fe06283509e1e3de75297836084a8b5b79`
- **Dependency:** complete the approved `clin-nav` rename before freezing a
  replacement human-pilot environment

## 1. Decision

Add a repository-native, fail-closed recovery contract for moving an
incident-affected exploratory human pilot toward a new, clean evidence batch.
The contract never converts the affected batch into valid effectiveness
evidence. It records its external disposition, validates restart prerequisites,
and reuses the existing environment, task commitment, assignment, blinded
rating, agreement, lock, unlock, aggregate-analysis, and reporting contracts.

The target terminal status is `evaluation-green`. This is a computed evidence
status, not an ethics determination, recruitment authorization, clinical claim,
or independent verification that an external authority's record is truthful.

## 2. Current state and evidence boundary

The user reported all three stop conditions for the completed 16-person batch:

- an environment change was detected;
- task-pack leakage was detected; and
- a reportable incident was detected.

These are user-provided operational assertions, not repository-verified facts.
Under the fixed protocol, they require a hard stop. The affected batch remains
in approved external audit custody and is permanently
`excluded-from-effectiveness-analysis`. It must not be unlocked, pooled,
analyzed for product effect, used for power analysis, or relabeled green.

No incident narrative, participant row, answer, score, condition key, consent
record, institutional decision text, task wording, nonce, assignment, or
private path may enter this repository.

## 3. Evaluated approaches

### 3.1 Fail-closed recovery contract plus orchestration — selected

Provide public schemas, synthetic examples, a pure validator, a content-free
CLI, and bilingual guidance. The new code orchestrates existing validators and
calculations rather than reimplementing their logic.

### 3.2 Manual recovery checklist only — rejected

A checklist cannot prevent a user from skipping the agreement gate, reusing a
compromised commitment, mixing study IDs, or calling an incomplete batch green.

### 3.3 Override the affected batch — rejected

No administrative override may turn environment change, leakage, or a
reportable incident into valid effectiveness evidence. This would violate the
protocol and destroy the credibility of later conclusions.

## 4. Architecture

Public components live under `evals/effectiveness/recovery/` and `scripts/`:

- an incomplete recovery-record template;
- a fully populated synthetic example that remains clearly non-human evidence;
- English and Traditional Chinese recovery checklists;
- a pure recovery-record schema validator and status calculator;
- a content-free CLI with stage-specific subcommands;
- tests using only synthetic records and repository-external temporary inputs;
  and
- navigation from the effectiveness README and protocol.

Real instances and all referenced evidence remain outside the checkout. The
repository stores neither a completed real recovery record nor external
evidence content.

## 5. External recovery record

The closed JSON contract records only controlled values, timestamps, hashes,
and safe opaque identifiers. It contains no free text. Its logical groups are:

1. identity: schema version, synthetic-example flag, affected study ID, and
   replacement study ID;
2. affected-batch disposition: the literal
   `excluded-from-effectiveness-analysis` and the affected task-commitment
   SHA-256;
3. incident closure: status, timezone-aware closure time, and SHA-256 of the
   externally governed closure record;
4. restart decision: controlled decision value, decision time, and SHA-256 of
   the external decision record;
5. replacement bindings: protocol commit, `clin-nav` Skill commit and version,
   new task-commitment SHA-256, assignment version, and environment
   fingerprint; and
6. replacement collection closure: the controlled closure state,
   timezone-aware closure time, and SHA-256 of the external closure record; and
7. replacement integrity attestation: the three controlled booleans for
   environment change, task-pack leakage, and reportable incident, plus a
   timezone-aware attestation time and SHA-256 of its external record.

Fields that do not yet exist are null in a valid incomplete record. Validators
enforce exact keys, types, safe identifier patterns, lowercase digests, aware
timestamps, chronological ordering, and null/value relationships. The affected
and replacement study IDs and task commitments must differ.

Hashes establish immutability and cross-file binding; they do not prove that an
institutional decision was correct. The responsible external process remains
authoritative.

## 6. Computed states

The status calculator returns exactly one of these ordered states:

| State | Minimum computed condition |
|---|---|
| `blocked-incident-open` | Affected batch is excluded but incident closure is absent or incomplete |
| `ready-for-restart-review` | Incident is closed, but an authorized replacement-batch decision or replacement bindings are incomplete |
| `authorized-for-fresh-batch` | External restart decision is bound and all new pre-collection identities, commits, environment, assignment, and commitment are fixed |
| `ready-for-blinded-rating` | Replacement collection is closed, integrity attestation has no adverse flag, and the external study manifest validates |
| `eligible-for-locked-unlock` | Ratings bytes are locked and the existing condition-blind agreement gate passes |
| `evaluation-green` | Explicit unlock and recomputation produce the supplied real aggregate summary, at least 14 of 16 participants completed all four tasks, and every green invariant passes |

The input never contains a status or green boolean. Both are derived. Missing
later-stage files leave the record at the highest earlier valid state rather
than converting absence into success.

## 7. CLI and data flow

Use stage-specific subcommands so optional files cannot accidentally weaken a
later check:

```text
python scripts/validate_effectiveness_recovery.py restart-check --recovery-record <external-path>
python scripts/validate_effectiveness_recovery.py collection-check --recovery-record <external-path> --study-manifest <external-path>
python scripts/validate_effectiveness_recovery.py rating-check --recovery-record <external-path> --study-manifest <external-path> --scores <external-path> --ratings-lock <external-path>
python scripts/validate_effectiveness_recovery.py green-check --recovery-record <external-path> --study-manifest <external-path> --scores <external-path> --ratings-lock <external-path> --condition-key <external-path> --aggregate-summary <external-path> --unlock-after-ratings-lock
```

Every path must resolve outside the repository checkout. Output is canonical
JSON containing only schema version, computed status, passed gate IDs, missing
or blocked gate IDs, and safe aggregate counts already allowed by the public
report contract. It never echoes paths, identifiers, hashes, source values, or
exception text.

Exit codes are:

- `0`: the requested stage is fully satisfied; only `green-check` with status
  `evaluation-green` represents the terminal evidence gate;
- `2`: malformed arguments, unsafe paths, invalid JSON, schema mismatch,
  cross-file mismatch, or attempted bypass; and
- `3`: valid evidence is incomplete or a fixed stop condition blocks progress.

## 8. Reuse of existing gates

The recovery implementation calls the existing contracts for:

- study-manifest validation and environment fingerprint matching;
- task-commitment verification and fixed assignment layout;
- blinded score and controlled review validation;
- ratings-lock byte hashing and rater completion;
- raw agreement and kappa thresholds;
- explicit condition-key unlock;
- participant-level paired aggregation and completion threshold; and
- bilingual aggregate report schema validation.

It must not duplicate agreement formulas, success calculation, bootstrap
logic, or report calculations. `green-check` recomputes the aggregate summary
from the external inputs and compares canonical structures; it does not trust a
precomputed status in the supplied summary.

## 9. Terminal green invariants

`evaluation-green` requires all of the following:

- the affected batch is excluded and never appears in replacement inputs;
- incident closure and replacement authorization are present as external
  record hashes and controlled decisions;
- the replacement study ID and task commitment differ from the affected ones;
- the replacement Skill is `clin-nav` version `0.5.0` at its frozen commit;
- all 16 expected participant slots belong to one replacement environment and
  assignment version;
- the replacement integrity attestation reports no environment change, task
  leakage, or reportable incident;
- the controlled reviews contain no environment-consistency or task-pack-
  integrity deviation and no environment-batch-change or task-pack-leakage
  limitation for the replacement batch;
- ratings are complete and locked to the exact blinded-score bytes;
- raw agreement is at least `0.80`, and each estimable kappa is at least `0.60`;
- explicit unlock succeeds and study IDs match across every input;
- at least 14 of 16 participants completed all four tasks;
- the aggregate summary is real (`synthetic_example: false`) and exactly
  reproducible from the external inputs; and
- the public claim remains exploratory product-effect evidence, not clinical,
  causal, patient-outcome, or general-population validation.

No quality score or favorable effect estimate can offset an integrity, safety,
lock, agreement, or completion failure.

## 10. Power-analysis boundary

The affected batch contributes no effect estimate, variance, discordance,
attrition, or task-heterogeneity parameter. After the first valid replacement
batch reaches `evaluation-green`, a later power-analysis step may use that
batch's paired variation and uncertainty together with the predeclared
20-percentage-point minimum practical difference.

The result must remain a scenario table with conservative sensitivity ranges,
not a single sample-size claim copied from the observed point estimate. Overall
and independently powered stratum conclusions remain separate scenarios.

## 11. Test-driven implementation

Before production changes, failing tests must cover:

- exact recovery schema, null/value transitions, safe tokens, digest and
  timestamp formats, and deterministic ordering;
- all six states and every permitted adjacent transition;
- rejection of an input-supplied status, green flag, approval shortcut, or
  unknown field;
- rejection of reused study IDs, reused task commitments, mixed commits,
  environment fingerprints, assignments, or study IDs;
- hard stops for each adverse replacement integrity flag;
- hard stops for replacement controlled-review findings that contradict clean
  collection;
- repository-internal paths and content-free error behavior;
- ratings-lock mutation, low agreement, premature condition-key access, and
  missing explicit unlock;
- fewer than 14 complete participants;
- synthetic summaries, stale summaries, and any recomputation mismatch;
- preservation of the affected batch's excluded disposition; and
- a complete synthetic RED-to-GREEN path that proves the orchestration without
  claiming a human study occurred.

Mutation tests must show that removing or changing every critical field causes
the intended failure. Tests use synthetic data only and never read an external
real recovery instance.

## 12. Documentation and public boundary

English and Traditional Chinese guidance must explain:

- why the affected batch cannot be repaired into evidence;
- who must complete external incident closure and restart decisions;
- how to create an entirely new batch after the `clin-nav` migration;
- how each CLI state differs from authorization;
- what `evaluation-green` does and does not prove;
- when rating, unlock, aggregate reporting, and power analysis become eligible;
  and
- which files must never enter Git.

The public-boundary scanner must reject completed real recovery records,
incident material, human inputs, condition keys, task packs, nonces, and
assignments without printing their content.

## 13. Verification

The implementation must pass:

```text
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

It must also pass focused recovery mutation tests, bilingual renderer checks,
synthetic end-to-end status checks, `git diff --check`, complete diff review,
and the official Python 3.11 runtime check used by the release process.

Actual human evidence is not a CI requirement. CI proves that the gate is
fail-closed and computable, not that a real replacement pilot occurred.

## 14. Failure handling

- Any unresolved incident leaves `blocked-incident-open`.
- Any missing or non-authorizing restart record leaves
  `ready-for-restart-review` or blocks the request.
- Any reuse of affected identifiers or commitments is invalid, not merely
  incomplete.
- Any replacement environment change, leakage, or reportable incident stops
  that replacement batch and requires another new batch.
- Low agreement blocks condition-key access and requires a new independently
  locked rating round.
- A stale or mismatched aggregate summary is invalid.
- No failed or incomplete gate may be overridden by a favorable outcome.

## 15. Inversion and second-order controls

The design fails most seriously if a status tool becomes a machine-generated
substitute for institutional authority. Controlled external decision fields,
record hashes, explicit limitations, external-only instances, and the
distinction between authorization and evidence status reduce that risk.

It also fails if the contaminated batch influences later power calculations.
The explicit exclusion and cross-study inequality checks prevent this indirect
reuse. A further replacement incident recursively returns to the hard-stop
path; the system never accumulates exceptions that weaken later batches.

The second-order maintenance risk is parallel validation logic. Orchestration
must call existing validators and compare canonical outputs rather than copy
their rules. Changes to agreement, completion, or analysis contracts then fail
the recovery tests until the orchestration is intentionally synchronized.

## 16. Acceptance criteria

- The affected batch is permanently excluded from effectiveness inference.
- No direct input can claim or force `evaluation-green`.
- A replacement batch cannot begin before the `clin-nav` environment is fixed.
- Every recovery state is deterministic, content-free, and fail-closed.
- Existing study, lock, agreement, unlock, aggregation, and reporting rules are
  reused rather than duplicated.
- Only a clean, sufficiently complete, locked, agreement-eligible, explicitly
  unlocked, reproducible replacement batch can reach `evaluation-green`.
- The first power analysis uses only the first valid replacement batch and
  retains the predeclared practical-difference rule.
- No real governance, incident, participant, task, rating, or condition content
  enters the repository.
- All repository and official-runtime verification gates pass.
