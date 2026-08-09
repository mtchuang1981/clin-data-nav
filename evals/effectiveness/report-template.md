# Effectiveness pilot aggregate report template

This template contains no result. Populate it only from a validated aggregate
summary. Publish a positive, negative or neutral finding with the same headings,
denominators, precision, safety separation, and limitations.

## Executive summary

State the aggregate product-evaluation finding, exploratory status, synthetic
task boundary, and that the pilot does not prove clinical validity.

## Methods

Report protocol commit, study dates, model/Skill environment, assignment
version, task-commitment verification, and participant-cluster bootstrap setup.
Quality criteria are secondary and never determine primary task success; a
zero applicable denominator is not estimable.

## Participant flow

Report assigned and completed participants, both strata, incomplete-task events,
primary complete pairs, and interpretation status.

## Primary outcome

Report both condition denominators and rates, intervention-minus-control paired
risk difference, 95% interval, paired distribution, and the absolute 20-point
minimum practical difference.

## Stratified results

Report beginner and professional aggregates separately without claiming powered
between-stratum comparisons.

## Safety

Report critical-event counts, denominators, rates, and exact 95% intervals for
each condition. Never offset safety events with quality or speed.

## Secondary outcomes

Report paired time, quality, NASA-TLX, confidence, and understanding results;
intervention SUS; timeout and technical-failure rates; and criterion aggregates.

## Rater agreement

Report original pre-adjudication raw binary and ordinal agreement, Cohen kappa,
linear weighted kappa, critical disagreements, adjudications, and unlock status.

## Missing data and sensitivity

Report complete-case and prespecified conservative-missingness denominators and
estimates.

## Power-analysis scenarios

Report all conservative scenarios. Until separately authorized post-pilot
analysis, show `deferred-until-post-pilot` and JSON null sample sizes; do not
invent a power result from the pilot point estimate.

## Protocol deviations

Report the mandatory controlled review status. `reviewed-none` means the review
was completed and the controlled item list is empty. Otherwise report every
prespecified category ID and positive aggregate count in deterministic order.

## Limitations

Report the mandatory controlled review status and every prespecified limitation
category and positive aggregate count. Preserve the product-effectiveness
versus clinical-validity boundary.

## Field dictionary

| Field | Meaning |
|---|---|
| `protocol_commit` | Versioned protocol implementation used for the study |
| `environment` | Fixed model, Skill, platform, dates, task commitment, and bootstrap settings |
| `participant_flow` | Aggregate allocation, completion, missingness, and interpretation status |
| `primary` | Safety-gated paired task-success aggregates and sensitivity analysis |
| `safety` | Critical-event counts, rates, and exact intervals by condition |
| `secondary` | Paired continuous outcomes, SUS, failures, and criterion aggregates |
| `agreement` | Original pre-adjudication agreement and pre-unlock status |
| `power_scenarios` | Prespecified conservative inputs and deferred/calculated state |
| `protocol_deviations` | Controlled review status and aggregate category counts only |
| `limitations` | Controlled review status and material limitation category counts |
