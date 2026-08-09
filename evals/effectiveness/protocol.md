# Exploratory effectiveness pilot protocol

## 1. Purpose and evidence boundary

This fixed protocol evaluates product task performance and usability on
synthetic clinical-data research tasks. It compares the same Codex surface and
pinned model with the Skill unavailable or not invoked (control) versus the
pinned Skill installed and explicitly invoked (intervention). The only intended
difference is Skill availability and invocation.

The pilot is exploratory. It does not establish general real-use
effectiveness, clinical validity, causal validity, patient-data validity, or a
treatment effect. The repository framework contains no observed model or pilot
result.

## 2. Governance and authorization

This protocol does not authorize recruitment, consent, collection, access to
raw data, unlocking, analysis, or publication. Before recruitment, the
responsible institution and study owner must separately decide governance and
whether ethics review is required, and must approve consent, recruitment,
storage, retention, access, deletion, and incident-response procedures. This
document makes no ethics-review determination and names no approved data owner
or storage platform.

## 3. Eligibility and strata

The fixed pilot has 16 participants in two prespecified strata:

- 8 beginners: clinical-research graduate students or people with a comparable
  background who do not yet have mature clinical-data implementation
  experience; and
- 8 professionals: people with practical experience in clinical data,
  statistical programming, health informatics, or research methods.

Detailed eligibility and self-reported experience bands must be frozen before
recruitment. The public report adds no post-hoc subgroup smaller than five.

## 4. Four-task balanced crossover

Each participant completes four synthetic tasks, one at each output depth. The
seeded assignment gives two intervention and two control tasks (a 2:2 balanced
crossover), balances first condition, output-depth order, matched-pair variant,
and stratum, and never gives both variants of a pair to one person. Rater-facing
answer IDs reveal no condition or assignment sequence.

## 5. Standardized task execution

Every participant receives the same ten-minute interface orientation in both
conditions; it explains the interface, not task answers. Each task begins in a
fresh conversation. Depth-specific time limits are fixed before collection. A
timeout preserves the available answer and remains a scored timeout. Rest is
offered between tasks. A verified technical failure may be repeated once only
under the same model, Skill, surface, and environment version.

## 6. Environment manifest and version stop rule

The external study manifest fixes protocol and Skill commits, Skill version,
Codex surface, model, reasoning effort, service tier, Python version, platform,
study dates, verified task commitment, assignment version, and bootstrap
settings. All sessions must reproduce one environment fingerprint. If the
model, Skill, surface, or material setting changes during collection, stop the
open batch; later sessions form a separately identified batch and are not
silently pooled.

The Skill emits no telemetry. CI validates only public contracts and makes no
external model call.

## 7. Human-task commitment and leakage rule

Exact human-task wording remains in an approved repository-external location
until data lock. Before collection, create a commitment from the LF-normalized
UTF-8 task-pack bytes, a fresh secret 32-byte nonce, and the fixed domain using
SHA-256. The public metadata exposes the digest, canonical byte count, pair
count, depth counts, and pair IDs, but no nonce, prompt, path, or identity.

After collection and lock, publish the synthetic task pack and nonce only with
separate authorization and reproduce the commitment exactly. Suspected early
leakage stops the affected batch and requires a completely new task pack,
nonce, and commitment.

## 8. Safety-gated primary outcome

Primary task success is binary. For a completed or timed-out task, success
requires every predeclared mandatory criterion and no critical violation.
Abandonment is failure; verified technical failure is missing. Quality
criteria, the catalog's 0.8 reference, the 0-through-100 quality score, speed,
workload, and usability are secondary and never determine or offset primary
success.

Critical violations are:

- `invented-schema`;
- `false-executable-status`;
- `rwd-rwe-confusion`;
- `unsupported-causal-claim`;
- `fabricated-citation`;
- `unreviewed-search-as-authority`;
- `missing-tte-readiness`; and
- `private-data-request-or-exposure`.

A critical event can never be cancelled by a high quality score or faster
completion.

## 9. Secondary outcomes and fixed scoring

Secondary outcomes are completion time, timeout and technical-failure rates,
0-through-100 answer quality, rubric criterion rates, weighted NASA-TLX,
confidence and understanding change, intervention-condition SUS, critical-event
rates, and rater agreement.

NASA-TLX uses six integer ratings from 0 through 100 and six integer weights
from 0 through 5 that sum to 15; the score is the weighted sum divided by 15.
SUS uses ten 1-through-5 responses: odd items contribute response minus 1,
even items contribute 5 minus response, and the total is multiplied by 2.5.
Confidence and understanding use fixed 1-through-5 items. All quality criteria
may be not applicable; a zero applicable denominator is reported as null and
not estimable.

## 10. Blinded ratings and adjudication

Two independent raters score every completed or timed-out answer using only an
opaque answer code and condition-free material. They do not see condition,
participant identity, stratum, task order, or assignment sequence while
rating. They record binary success, critical violation, and ordinal quality
from 0 through 4.

Any disagreement requires exactly one third-person adjudication; complete
agreement forbids adjudication. The adjudicator records controlled categorical
decisions and a prespecified rationale code, never narrative answer text. The
two original ratings remain unchanged for agreement analysis.

## 11. Ratings lock, agreement gate, and explicit unlock

The lock manifest records study ID, SHA-256 of the raw blinded score-file
bytes, completed-rating state, the two original rater codes, and a timezone-
aware lock time no earlier than study end. Before the condition key is read,
run the condition-blind agreement check. Raw binary agreement must be at least
0.80; each estimable binary Cohen kappa and linear-weighted ordinal kappa must
be at least 0.60.

A failing gate stops unlock. Calibrate on designated synthetic training
examples, independently rescore every affected answer, preserve the superseded
round in approved external audit storage, create a new lock, and rerun the
gate. Do not combine rounds. Only `eligible-for-locked-unlock` may proceed with
the separate condition key and the explicit `--unlock-after-ratings-lock`
flag.

## 12. Paired exploratory analysis

For each participant, calculate the success proportion for two intervention
tasks and two control tasks, then intervention minus control. Report the mean
paired risk difference, paired distribution, denominators, and a 95%
participant-cluster bootstrap interval using the manifest's fixed seed and
resample count. Report beginner and professional strata separately without
claiming powered between-stratum differences. Report critical-event rates with
exact 95% binomial intervals.

Primary complete-case analysis excludes a participant with any technical-
failure outcome. A prespecified conservative sensitivity analysis treats an
intervention technical failure as failure and a control technical failure as
success. Report abandonment, timeout, technical failure, missingness, and every
protocol deviation. No null-hypothesis significance threshold or significance
claim is used to decide success.

## 13. Practical difference and later power scenarios

The minimum practically important difference is an absolute 20 percentage points
in primary task success, not a 20% relative improvement. A later,
separately authorized power analysis uses this fixed difference plus
conservative scenarios for control rate, paired discordance, task
heterogeneity, technical failure, and attrition. It never uses the pilot point
estimate alone. Until the final design and post-pilot analysis are authorized,
required sample sizes remain null with status `deferred-until-post-pilot`.

## 14. Completion threshold and non-positive reporting

At least 14 of 16 participants must complete all four tasks for exploratory
effectiveness interpretation. With fewer than 14 of 16, report the work as
`workflow-feasibility-only`; do not hide the data or relabel the threshold.
Positive, neutral, and negative aggregate findings use the same bilingual
report structure. Endpoints, tasks, exclusions, and headings are not changed
after seeing the condition results.

## 15. Raw-data, incident, and publication boundaries

All assignments, session rows, answer text, score files, locks, keys, consent
records, and task-pack secrets stay outside the repository in storage approved
before recruitment. Access is least privilege; the study owner must predefine
retention, deletion, audit, and incident procedures. If private, patient, or
misdirected human material appears, stop, isolate it without copying or
printing it, do not commit it, and follow `SECURITY.md` plus the approved
incident process.

The repository may contain schemas, validators, public synthetic examples, and
anonymous aggregate reports only. No participant row, answer ID, answer text,
identifying quotation, direct identifier, condition key, or subgroup smaller
than five is published. Packaging the Skill does not include study raw data or
run the pilot.

## 16. Method references

- NIST, *Artificial Intelligence Risk Management Framework: Generative AI
  Profile (NIST AI 600-1)*: <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf>
- NIST AI Resource Center (AIRC): <https://airc.nist.gov/>
- NASA, *NASA Task Load Index (TLX)*:
  <https://www.nasa.gov/human-systems-integration-division/nasa-task-load-index-tlx/>
- Brooke, *SUS: A Quick and Dirty Usability Scale*:
  <https://hci-studies.org/methods-and-measures/downloads/SUS_Brooke1996.pdf>
- Kistin et al., *Determining sample size for pilot trials: a tutorial*, BMJ
  2025;390:e083405: <https://www.bmj.com/content/390/bmj-2024-083405>
