# Effectiveness recovery checklist

The affected batch remains `excluded-from-effectiveness-analysis`. Every state
below is a computed software status: not an ethics determination and not recruitment authorization.

| State | Required external evidence | Responsible role | Permitted next action | Prohibited action |
|---|---|---|---|---|
| `blocked-incident-open` | Affected-batch exclusion; authoritative closure is absent or incomplete | External incident owner | Complete the governed incident process outside Git | Repair, unlock, pool, analyze, or reuse the affected batch |
| `ready-for-restart-review` | Closed incident record and its hash; restart authorization or new bindings remain incomplete | Authorized institutional decision-maker | Record the controlled restart decision and, if authorized, prepare a new batch | Treat closure as approval or begin recruitment or collection |
| `authorized-for-fresh-batch` | Authorized restart plus new study ID, protocol and `clin-nav` commits, task commitment, assignment version, and environment fingerprint | Study owner and environment custodian | Under separate authorization, prepare and collect only the new batch | Reuse affected identifiers, commitments, assignments, or evidence |
| `ready-for-blinded-rating` | Closed replacement collection, clean integrity attestation, and a matching validated manifest | Collection custodian and blinded-rating lead | Begin separately governed condition-blind rating | Inspect the condition key, combine batches, or overlook an integrity event |
| `eligible-for-locked-unlock` | Complete ratings lock bound to exact score bytes and passing blinded agreement | Ratings custodian and authorized unlock decision-maker | If separately authorized, perform the explicit locked unlock | Unlock early, bypass low agreement, or combine scoring rounds |
| `evaluation-green` | Explicit unlock, exact aggregate recomputation, clean controlled reviews, and at least 14/16 complete participants | Analysis custodian and authorized reporting body | Prepare aggregate-only bilingual exploratory reporting | Claim clinical, causal, patient-outcome, population, ethics, or recruitment validation |

If a replacement incident occurs, exclude that replacement batch and restart
recursively with another new batch. The first power analysis uses only the first
valid replacement batch after `evaluation-green` and retains the predeclared
20-point practical difference with conservative sensitivity ranges.
