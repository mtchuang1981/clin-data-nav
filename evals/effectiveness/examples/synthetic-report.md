# Effectiveness pilot aggregate report — synthetic example

## Executive summary

This exploratory product evaluation summarizes safety-gated task performance. It does not prove clinical validity, causal validity, or patient-outcome validity.
Its objective is to compare the same model and surface with and without the pinned Skill.
This is an illustrative synthetic example, not observed pilot evidence.

## Methods

- Protocol commit: `4776d35c4138c0966c57888528936e7aae6388a4`.
- Study period: 2026-09-01T09:00:00+08:00 to 2026-09-02T17:00:00+08:00.
- Model/Skill environment: Codex desktop; model fixed-model-snapshot; reasoning medium; service tier priority; Skill 0.3.0 at `1b4eeb2ca2272cfd05ecdd50708c4fea714db0d3`; Python 3.11.9 on Windows.
- Assignment version: synthetic-pilot-v1-assignments.
- Task commitment: verified (`cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc`).
- Participant-cluster bootstrap: seed 20260809, 20000 resamples; the same method provides 95% intervals for continuous paired secondary outcomes.

## Participant flow

Assigned 16 participants; completed 16; 8 beginners and 8 professionals. Abandonments: 0; timeouts: 0; technical failures: 0. Primary complete pairs: 16. Interpretation status: `eligible-for-exploratory-interpretation`.

## Primary outcome

Control: 16/32 (50.0%); intervention: 24/32 (75.0%). The paired risk difference was 25.0% (intervention minus control), with an illustrative 95% interval of [5.0%, 45.0%], based on 16 complete pairs.
The predeclared minimum practical difference is an absolute 20.0 percentage points (the 20-point minimum difference); it is not a relative improvement and the pilot point estimate is not used alone for power.

## Stratified results

- Beginners: 8 participants; control 7/16 (43.8%), intervention 12/16 (75.0%), paired difference 31.25 percentage points.
- Professionals: 8 participants; control 9/16 (56.2%), intervention 12/16 (75.0%), paired difference 18.75 percentage points.
These strata are exploratory and are not powered confirmatory comparisons.

## Safety

- Control: 0/32 (0.0%); exact 95% interval [0.0%, 10.9%].
- Intervention: 0/32 (0.0%); exact 95% interval [0.0%, 10.9%].
Critical safety events are reported separately and cannot be offset by quality or speed.

## Secondary outcomes

- Time (seconds): 16 complete pairs; mean difference -110.0; median difference -120.0; 95% interval [-180.0, -40.0].
- Quality (points): 16 complete pairs; mean difference +10.0; median difference +10.0; 95% interval [+4.0, +16.0].
- NASA-TLX (points): 16 complete pairs; mean difference -8.0; median difference -8.0; 95% interval [-12.0, -4.0].
- Confidence change: 16 complete pairs; mean difference +1.0; median difference +1.0; 95% interval [+0.5, +1.5].
- Understanding change: 16 complete pairs; mean difference +1.0; median difference +1.0; 95% interval [+0.5, +1.5].
- Intervention SUS: 16 participants; mean 78.0; median 78.0.
- Timeout rate: 0/64 (0.0%).
- Technical-failure rate: 0/64 (0.0%).

### Criterion results

| Criterion | Control met/applicable | Control rate | Intervention met/applicable | Intervention rate |
|---|---:|---:|---:|---:|
| correct-output-depth | 28/32 | 87.5% | 30/32 | 93.8% |
| answers-requested-decision | 24/32 | 75.0% | 28/32 | 87.5% |
| states-confirmed-assumed-limited | 25/32 | 78.1% | 29/32 | 90.6% |
| authority-appropriate-sources | 18/24 | 75.0% | 22/24 | 91.7% |
| actionable-next-step | 24/32 | 75.0% | 28/32 | 87.5% |
| beginner-readable | 6/8 | 75.0% | 7/8 | 87.5% |
| pico-and-time-zero | 5/8 | 62.5% | 7/8 | 87.5% |
| tte-readiness | 3/4 | 75.0% | 4/4 | 100.0% |
| logical-data-contract | 6/8 | 75.0% | 8/8 | 100.0% |
| execution-status | 6/8 | 75.0% | 8/8 | 100.0% |
| citation-verifiable | 5/8 | 62.5% | 7/8 | 87.5% |
| validation-gaps | 20/32 | 62.5% | 27/32 | 84.4% |

## Rater agreement

Original pre-adjudication ratings covered 64 answers. Raw binary agreement was 87.5% (Cohen kappa: 0.75); raw ordinal agreement was 87.5% (linear weighted kappa: 0.80). Critical disagreements: 0; adjudications: 8; pre-unlock status: `eligible-for-locked-unlock`.

## Missing data and sensitivity

The complete-case primary analysis used 16 participant pairs. The conservative missingness analysis used 16 pairs and estimated 25.0% with a 95% interval [5.0%, 45.0%].

## Power-analysis scenarios

| Scenario | Control rate | Paired discordance | Attrition | Alpha | Target power | Method | Required complete pairs | Required recruits | Status |
|---|---:|---:|---:|---:|---:|---|---:|---:|---|
| lower-control-rate | 30.0% | 35.0% | 15.0% | 0.05 | 80.0% | paired-binary-or-participant-task-clustered-design | deferred-until-post-pilot | deferred-until-post-pilot | deferred-until-post-pilot |
| mid-control-rate | 50.0% | 50.0% | 15.0% | 0.05 | 80.0% | paired-binary-or-participant-task-clustered-design | deferred-until-post-pilot | deferred-until-post-pilot | deferred-until-post-pilot |
| higher-control-rate | 70.0% | 35.0% | 15.0% | 0.05 | 80.0% | paired-binary-or-participant-task-clustered-design | deferred-until-post-pilot | deferred-until-post-pilot | deferred-until-post-pilot |

Every scenario uses the predeclared 20.0 percentage points plus conservative discordance, heterogeneity, failure, and attrition inputs; no confirmatory sample size is invented before the post-pilot design decision.

## Protocol deviations

Protocol deviations: 0.

## Limitations

- The 16-person pilot design is exploratory and not confirmatory.
- Synthetic tasks and a controlled environment limit real-world generalizability.
- Product task performance does not prove clinical validity, causal validity, or patient-outcome validity.
- This aggregate-only file is an illustrative synthetic example and not observed pilot evidence.
- Negative and neutral findings must use this same structure and must not be suppressed.
