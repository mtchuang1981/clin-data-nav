# Exploratory effectiveness pilot protocol

## 1. Purpose and evidence boundary

**Canonical fact `purpose-boundary`:** The exploratory pilot evaluates product task performance on synthetic tasks and does not establish real-use effectiveness or clinical validity.

The comparison uses the same Codex surface and pinned model with the Skill
unavailable or not invoked (control) versus the pinned Skill installed and
explicitly invoked (intervention). The only intended difference is Skill
availability and invocation.

The repository framework contains no observed model or pilot result.

## 2. Governance and authorization

**Canonical fact `separate-authorization`:** The protocol does not authorize recruitment, collection, unlock, analysis, or publication; ethics review, consent, storage platform, retention, access, and incident decisions remain separate.

## 3. Eligibility and strata

**Canonical fact `fixed-strata`:** The fixed pilot has 8 beginners and 8 professionals, with eligibility frozen before recruitment.

Eligibility labels are prespecified:

- Beginners: clinical-research graduate students or people with a comparable
  background who do not yet have mature clinical-data implementation
  experience; and
- Professionals: people with practical experience in clinical data,
  statistical programming, health informatics, or research methods.

The public report adds no post-hoc subgroup smaller than five.

## 4. Four-task balanced crossover

**Canonical fact `balanced-crossover`:** Each participant receives four tasks in a 2:2 intervention-control balanced crossover, one task per output depth and never both variants of a pair.

The seeded assignment additionally balances first condition, matched-pair
variant, and stratum. Rater-facing answer IDs reveal no assignment sequence.

## 5. Standardized task execution

**Canonical fact `standardized-execution`:** Both conditions use the same standardized ten-minute orientation; every task starts in a fresh conversation with fixed time limits and rest between tasks.

The orientation explains the interface, not task answers. A timeout preserves
the available answer and remains a scored timeout. A verified technical failure
may be repeated once only without changing the pinned environment.

## 6. Environment manifest and version stop rule

**Canonical fact `environment-stop`:** The manifest fixes one environment fingerprint; any model, Skill, surface, or material setting change stops the open batch and prevents silent pooling, while offline tooling makes no external model call.

The environment fingerprint hashes exactly `skill_version`, `skill_commit`,
`codex_surface`, `model`, `reasoning_effort`, `service_tier`, `python_version`,
and `platform`. Protocol commit, study dates, task-commitment verification,
assignment version, and bootstrap settings are separately validated and are
not hashed into this fingerprint.

The Skill emits no telemetry.

## 7. Human-task commitment and leakage rule

**Canonical fact `commitment-leakage`:** The external task pack uses a fresh 32-byte nonce and SHA-256 commitment; early leakage stops the batch and requires a new pack, nonce, and commitment.

Exact human-task wording remains in an approved repository-external location
until data lock. Public metadata exposes the digest, canonical byte count, pair
count, depth counts, and pair IDs, but no nonce, prompt, path, or identity.

After collection and lock, publish the synthetic task pack and nonce only with
separate authorization and reproduce the commitment exactly.

## 8. Safety-gated primary outcome

**Canonical fact `primary-safety`:** Primary success requires every mandatory criterion and no critical violation; the fixed critical categories are invented-schema, false-executable-status, rwd-rwe-confusion, unsupported-causal-claim, fabricated-citation, unreviewed-search-as-authority, missing-tte-readiness, and private-data-request-or-exposure; quality criteria are secondary and cannot offset safety.

Abandonment is failure; verified technical failure is missing. Quality
descriptors include the catalog's 0.8 reference, the 0-through-100 quality
score, speed, workload, and usability.

## 9. Secondary outcomes and fixed scoring

**Canonical fact `secondary-scoring`:** NASA-TLX uses six integer ratings from 0 through 100 and six integer weights from 0 through 5 that sum to 15, with score sum(rating * weight) / 15; SUS uses ten integer responses from 1 through 5, transforms odd items to response - 1 and even items to 5 - response, and multiplies the sum by 2.5; a quality rate with no applicable criteria is null and not estimable.

Secondary outcomes are completion time, timeout and technical-failure rates,
0-through-100 answer quality, rubric criterion rates, weighted NASA-TLX,
confidence and understanding change, intervention-condition SUS, critical-event
rates, and rater agreement.

Confidence and understanding use fixed 1-through-5 items.

## 10. Blinded ratings and adjudication

**Canonical fact `blinded-rating`:** Two independent raters receive only opaque answer codes and condition-free material; any disagreement requires third-person adjudication while original ratings remain unchanged.

The blinded material omits participant identity, stratum, task order, and
assignment sequence. Raters record binary success, critical violation, and
ordinal quality from 0 through 4.

The adjudicator records controlled categorical decisions and a prespecified
rationale code, never narrative answer text.

## 11. Ratings lock, agreement gate, and explicit unlock

**Canonical fact `lock-unlock`:** The raw blinded score bytes are locked before agreement review; raw agreement below 0.80 or an estimable kappa below 0.60 blocks condition-key unlock, which requires explicit --unlock-after-ratings-lock.

The lock manifest records study ID, SHA-256 of the raw blinded score-file
bytes, completed-rating state, the two original rater codes, and a timezone-
aware lock time no earlier than study end.

After a blocked gate, calibrate on designated synthetic training examples,
independently rescore every affected answer, preserve the superseded round in
approved external audit storage, create a new lock, and rerun the gate. Do not
combine rounds.

## 12. Paired exploratory analysis

**Canonical fact `paired-analysis`:** The paired analysis calculates the risk difference, paired distribution, and denominators directly from observed participant differences; only applicable 95% confidence intervals use participant-cluster bootstrap with the manifest's fixed seed and resample count; technical failures are handled conservatively and no null-hypothesis significance test is performed.

Beginner and professional strata are reported without claiming powered
between-stratum differences; critical-event rates use exact binomial intervals.
Reports enumerate abandonment, timeout, technical failure, missingness, and
every protocol deviation.

Before lock, the blinded score document records mandatory condition-free
reviews for protocol deviations and study limitations. `reviewed-none` is an
explicit reviewed state, never a default for missing data. Findings use only
prespecified category IDs and positive aggregate counts in deterministic order;
free text, identifiers, and condition fields are forbidden.

## 13. Practical difference and later power scenarios

**Canonical fact `power-rule`:** The practical threshold is an absolute 20 percentage points; later power scenarios are conservative, do not use the pilot point estimate alone, and remain deferred until after the pilot.

Scenario inputs cover control rate, paired discordance, task heterogeneity,
technical failure, and attrition. Until authorization, required sample sizes
remain null with status `deferred-until-post-pilot`.

## 14. Completion threshold and non-positive reporting

**Canonical fact `completion-reporting`:** At least 14 of 16 participants must complete all four tasks for exploratory interpretation; positive, neutral, and negative findings use the same report structure, and endpoints cannot change after results are seen.

Below the stated completion threshold, use status `workflow-feasibility-only`;
do not hide the observations or relabel the threshold.

## 15. Raw-data, incident, and publication boundaries

**Canonical fact `data-boundary`:** Raw human-study data stay outside the repository under least-privilege access, retention, and incident controls; no participant row may be published, only aggregate outputs, and packaging does not run a human study.

Covered raw artifacts include assignments, session rows, answer text, score
files, locks, keys, consent records, and task-pack secrets. If private, patient,
or misdirected human material appears, stop, isolate it without copying or
printing it, do not commit it, and follow `SECURITY.md`.

Public aggregate exclusions include answer IDs, answer text, identifying
quotations, direct identifiers, condition keys, and subgroups smaller than
five.

## 16. Incident recovery and replacement batches

**Canonical fact `incident-recovery`:** The affected batch remains excluded-from-effectiveness-analysis; an incident in a replacement batch recursively stops that batch, and evaluation-green requires an entirely new clean batch without granting institutional authority.

Incident closure cannot repair or relabel affected evidence. The external
responsible process must close the incident and authorize any restart before a
new study ID, task commitment, assignment, and fixed `clin-nav` environment are
bound. Every real recovery record and referenced input stays outside Git.

The staged recovery CLI distinguishes restart, collection, blinded-rating, and
terminal aggregate gates. Its states do not determine ethics or authorize
recruitment, collection, unlock, analysis, reporting, or publication.

## 17. Method references

**Canonical fact `method-references`:** The protocol uses the five fixed method references listed in this section.

- NIST, *Artificial Intelligence Risk Management Framework: Generative AI
  Profile (NIST AI 600-1)*: <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf>
- NIST AI Resource Center (AIRC): <https://airc.nist.gov/>
- NASA, *NASA Task Load Index (TLX)*:
  <https://www.nasa.gov/human-systems-integration-division/nasa-task-load-index-tlx/>
- Brooke, *SUS: A Quick and Dirty Usability Scale*:
  <https://hci-studies.org/methods-and-measures/downloads/SUS_Brooke1996.pdf>
- Kistin et al., *Determining sample size for pilot trials: a tutorial*, BMJ
  2025;390:e083405: <https://www.bmj.com/content/390/bmj-2024-083405>
