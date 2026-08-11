# Effectiveness incident recovery

## 1. Purpose and authority boundary

This workflow computes whether external evidence satisfies the staged recovery
contract after an affected exploratory pilot is stopped. Its output is
not an ethics determination and not recruitment authorization. It does not approve
collection, rating, unlock, analysis, publication, or any institutional action.

## 2. Why the affected batch remains excluded

The affected batch is permanently
`excluded-from-effectiveness-analysis`. Closing its incident cannot repair it,
make it green, pool it with another batch, or supply inputs to later power
analysis. The authoritative incident disposition and restart decision remain
with the responsible external institutional process.

## 3. External recovery record

Start from [recovery-template.json](recovery-template.json) and keep the
completed instance, referenced records, identifiers, hashes, manifests,
assignments, answers, ratings, locks, condition key, task pack, nonce, and
aggregate evidence outside the repository checkout. The checked-in
[synthetic example](examples/synthetic-recovery.json) exercises only the public
schema and is not human evidence. Never commit a real recovery record or any
human-study input.

## 4. Restart check

After the responsible incident owner closes the external incident record and
the authorized institutional decision-maker records a restart decision, run:

```bash
python scripts/validate_effectiveness_recovery.py restart-check --recovery-record <external-path>
```

Only `authorized-for-fresh-batch` satisfies this command. It permits preparation
of new bindings under separate authorization; it does not authorize people or
reuse of the affected batch.

## 5. Collection check

After a completely new study ID, task commitment, assignment version, fixed
`clin-nav` environment, collection closure, and clean integrity attestation are
bound externally, run:

```bash
python scripts/validate_effectiveness_recovery.py collection-check --recovery-record <external-path> --study-manifest <external-path>
```

`ready-for-blinded-rating` means the new collection evidence is internally
consistent enough to enter separately governed, condition-blind rating.

## 6. Rating check

Two independent raters and the responsible data custodian must complete and
lock the blinded score bytes before this check:

```bash
python scripts/validate_effectiveness_recovery.py rating-check --recovery-record <external-path> --study-manifest <external-path> --scores <external-path> --ratings-lock <external-path>
```

`eligible-for-locked-unlock` means the existing completion and agreement gates
pass. It permits only a separately authorized explicit unlock; low agreement
requires a new independent rating round and lock.

## 7. Terminal green check

Only after rating eligibility and explicit external authorization to unlock,
run:

```bash
python scripts/validate_effectiveness_recovery.py green-check --recovery-record <external-path> --study-manifest <external-path> --scores <external-path> --ratings-lock <external-path> --condition-key <external-path> --aggregate-summary <external-path> --unlock-after-ratings-lock
```

The command recomputes the aggregate and can return `evaluation-green` only for
a non-synthetic, clean replacement batch with at least 14 of 16 complete
participants. This is exploratory product-effect evidence, not clinical,
causal, patient-outcome, or general-population validation.

## 8. Interpret states and exit codes

Use the [English checklist](checklist.md) or
[Traditional Chinese checklist](checklist.zh-TW.md) for the six ordered states,
responsible roles, and action boundaries. Exit `0` means the requested stage is
satisfied; only `green-check` at `evaluation-green` is terminal. Exit `3` means
valid evidence is incomplete or blocked. Exit `2` means invalid arguments,
unsafe paths, invalid input, cross-file mismatch, or attempted bypass. No state
replaces external authority.

## 9. Replacement incident recursion

Any environment change, task-pack leakage, or reportable incident in a
replacement batch stops that batch. Keep it in approved external audit custody,
exclude it from effectiveness inference, close the new incident externally,
and begin again with another entirely new batch, task pack, nonce, commitment,
assignment, and environment binding. No favorable result overrides this stop.

## 10. Reporting and power-analysis boundary

Only aggregate, bilingual reporting becomes eligible after
`evaluation-green`; raw inputs stay external. No real replacement pilot was
performed by adding this workflow, so observed human `evaluation-green` remains
pending. The first power analysis is deferred until the first valid replacement
batch reaches `evaluation-green`, uses only that batch, and retains the
predeclared 20-point practical difference with conservative sensitivity
scenarios rather than copying its point estimate.
