# RWE Question Routing

Use this reference for RWD, RWE, PICO, causal, comparative-effectiveness,
estimand, SAP, or target-trial questions. It defines routing and handoff
boundaries, not a complete causal-analysis method.

## Classify the intent

Assign one primary intent before choosing a study-design path:

1. `descriptive` — frequency, characteristics, utilisation, or natural history;
2. `predictive` — prognosis, classification, or risk prediction;
3. `causal-comparative` — effects or safety under two or more strategies;
4. `measurement` — phenotype, variable, outcome, or data-quality validation;
5. `implementation` — mapping confirmed evidence and rules into SAS, SQL, R,
   or another target.

Preserve secondary intents, but do not let them silently change the primary
question. A request for an implementation can still contain unresolved
measurement or causal-design questions.

## Frame intervention or exposure questions

For an intervention or exposure question, record:

- population;
- intervention or exposure;
- comparator;
- outcomes;
- time zero and follow-up horizon;
- care setting and data source;
- intended use; and
- target estimand when the intent is causal.

Label a genuinely irrelevant field `not applicable`. Preserve unknown
study-specific or institutional values as unresolved.

PICO does not establish causal validity. It structures a question but does not
prove data fitness, exchangeability, correct time alignment, or identification
of a causal effect.

## Keep RWD and RWE distinct

RWD are routinely collected data about health status or health-care delivery,
including EHR, claims, registry, and other relevant sources. RWE is clinical
evidence about use, benefits, or risks that results from analysing
fit-for-purpose RWD.

RWD is not automatically RWE. Do not label a database, OMOP instance, extract,
table, or cohort as evidence merely because it contains real-world data.

Before stating that an analysis may generate RWE, record:

- provenance, approval status, and governed snapshot;
- relevance to the research question and intended use;
- population and care-setting coverage;
- availability and operational validity of exposures, comparators, outcomes,
  confounders, censoring events, competing events, and time anchors;
- completeness, missingness, linkage, and temporal limitations; and
- the intended clinical, policy, or regulatory context.

Use the versioned institutional Adapter and live metadata for physical schema
facts. Never infer local mappings from an RWD source description.

## Apply the TTE readiness gate

TTE is not the default. Consider target trial emulation only when the primary
intent is `causal-comparative` and the user seeks the effect or safety of
well-defined strategies.

Check whether these target-trial components can at least be specified:

1. eligibility criteria;
2. treatment or intervention strategies;
3. assignment procedure and its observational analogue;
4. time zero and follow-up period;
5. outcomes;
6. causal contrast or estimand; and
7. analysis plan.

Record relevant unresolved concerns about confounding, positivity, consistency,
missing data, measurement error, selection, censoring, immortal-time bias, and
interference. Missing information is a validation gap. Do not silently invent
an assumption to make the request appear TTE-ready.

Do not route descriptive, predictive, measurement, natural-history,
utilisation, signal-detection, or implementation-only questions to TTE merely
because they use RWD.

## Hand off to optional build-rwe-sap

`build-rwe-sap` is an optional collaborator and is not bundled with this Core.
The name alone does not prove that an available Skill is compatible.
Do not install or download it automatically.

Treat it as compatible only when its own documentation states that it accepts
the fields below, supports complete SAP, estimand, target-trial, or
causal-design work, and returns assumptions, methods, data requirements, and
validation gaps without claiming access to unverified institutional metadata.

Pass confirmed values and explicit unresolved values:

| Field | Content |
|---|---|
| `question_intent` | `causal-comparative` for a TTE handoff |
| `population` | Eligibility concept and unresolved local mappings |
| `intervention_or_exposure` | Well-defined strategy and timing |
| `comparator` | Active or other justified comparison strategy |
| `outcomes` | Clinical meaning, ascertainment window, and validation status |
| `time_zero` | Alignment of eligibility, assignment, and follow-up |
| `follow_up` | Start, end, censoring events, and competing events |
| `target_estimand` | Population, strategies, outcome measure, time horizon, and causal contrast |
| `data_sources` | RWD provenance, snapshot, coverage, and Adapter status |
| `measured_confounders` | Available concepts and unresolved confounding requirements |
| `data_limitations` | Missingness, measurement, linkage, temporal, selection, and positivity concerns |
| `authority_record` | Reviewed methods, regulatory, protocol, and institutional sources |
| `validation_gaps` | Every unmet design, metadata, fixture, approval, or review gate |

Never add an unverified physical table, column, code, OMOP Concept ID, or local
mapping to make the handoff look complete.

A compatible collaborator may return a proposed target-trial protocol,
estimand, confounding and censoring strategy, statistical analysis plan,
sensitivity and bias analyses, additional data requirements, and
design-specific validation gaps.

## Continue when the optional Skill is unavailable

If `build-rwe-sap` is absent, record its status as `unavailable`. If its
declared interface does not meet the compatibility contract, record
`incompatible`.

Continue the Core workflow for evidence navigation, question framing, RWD
fitness review, and logical data-contract work. State that a complete SAP, TTE,
estimand, or causal analysis was not delivered. Normally keep incomplete causal
work at `conceptual` or `dictionary-specified`.

The optional Skill must never block ordinary source navigation, terminology
mapping, data contracts, or implementation specifications.

## Reapply the execution gate

Convert only confirmed collaborator requirements into the Core data contract.
Then reapply the existing execution-maturity gate.

A proposed SAP or target-trial design does not make code `executable` or
`validated`. Those labels still require the approved versioned Adapter, current
metadata, parameters, fixtures, target-environment checks, and reviewed
results.

## Primary sources

- FDA, Real-World Evidence:
  <https://www.fda.gov/science-research/science-and-research-special-topics/real-world-evidence>
- FDA, Assessing EHR and Medical Claims Data:
  <https://www.fda.gov/regulatory-information/search-fda-guidance-documents/real-world-data-assessing-electronic-health-records-and-medical-claims-data-support-regulatory>
- NICE, Methods for real-world studies of comparative effects:
  <https://www.nice.org.uk/corporate/ecd9/chapter/methods-for-real-world-studies-of-comparative-effects>
- EMA, Real-world evidence:
  <https://www.ema.europa.eu/en/about-us/how-we-work/data-regulation-big-data-other-sources/real-world-evidence>
- Hernán, M. A., and Robins, J. M. (2016). Using big data to emulate a target
  trial when a randomized trial is not available. *American Journal of
  Epidemiology, 183*(8), 758–764. <https://doi.org/10.1093/aje/kwv254>
