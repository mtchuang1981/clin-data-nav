# Beginner Glossary

[繁體中文](glossary.zh-TW.md)

These definitions are an orientation, not a substitute for the current
standard, guidance, protocol, statistical analysis plan (SAP), or approved
institutional metadata. A model tells you how information can be represented;
an implementation still needs source review, mapping decisions, and
validation.

<a id="clinical-research"></a>
## Clinical research

[Clinical research](https://www.nih.gov/health-information/nih-clinical-research-trials-you/basics)
is medical research involving people. Clinical trials are one type of clinical
research; the term also includes observational and epidemiologic studies. The
research question and intended use determine which design and evidence rules
apply.

<a id="cdisc"></a>
## CDISC

The [Clinical Data Interchange Standards Consortium
(CDISC)](https://www.cdisc.org/standards) develops a family of standards for
clinical and non-clinical research data. CDISC is the organization and
standards ecosystem; it is not a single dataset format. Always identify the
specific standard, implementation guide, controlled terminology, and version
that govern the work.

<a id="sdtm"></a>
## SDTM

The [Study Data Tabulation Model
(SDTM)](https://www.cdisc.org/standards/foundational/sdtm) standardizes how
collected or received study data are organized and formatted while preserving
their original meaning. SDTM organizes study data for regulatory submission
and other review, exchange, and reuse purposes. It is not the original data
collection form and does not decide whether a source value is correct.

<a id="adam"></a>
## ADaM

The [Analysis Data Model
(ADaM)](https://www.cdisc.org/standards/foundational/adam) defines standards
for analysis datasets and metadata. ADaM supports analysis by making the
content and purpose of analysis data explicit and by supporting traceability
from results to analysis data and SDTM. It does not replace the protocol, SAP,
or study-specific derivation decisions.

<a id="omop-cdm"></a>
## OMOP CDM

The [Observational Medical Outcomes Partnership Common Data Model (OMOP
CDM)](https://ohdsi.github.io/CommonDataModel/) is an open community standard
for the structure and content of observational health data. OMOP CDM
standardizes observational data so common analytic methods can be applied
across conforming data sources. Each organization still has to design and
validate its extract-transform-load mappings, vocabulary mappings, and data
fitness for the research question.

SDTM, ADaM, and OMOP CDM standardize representation or support a defined use.
None of these standards makes source data automatically valid. Accuracy,
completeness, provenance, local transformation, and fitness for purpose still
need separate evidence and checks.

<a id="rwd"></a>
## RWD

[Real-world data
(RWD)](https://www.fda.gov/science-research/science-and-research-special-topics/real-world-evidence)
are data about patient health status or health-care delivery that are
routinely collected from sources such as electronic health records, claims,
registries, and digital health technologies. “Real-world” describes where and
how data arise; it does not certify their quality or relevance to a question.

<a id="rwe"></a>
## RWE

[Real-world evidence
(RWE)](https://www.fda.gov/science-research/science-and-research-special-topics/real-world-evidence)
is clinical evidence about a medical product's use and potential benefits or
risks, derived from analysis of RWD. RWD is an input; RWE is an evidentiary
result. A dataset does not become RWE until a defined question, fit-for-purpose
data, an appropriate design and analysis, and transparent limitations support
the claim.

<a id="pico"></a>
## PICO

[PICO](https://www.cochrane.org/authors/handbooks-and-manuals/handbook/current/chapter-02)
is a question-framing aid: Population, Intervention, Comparator, and Outcome.
The fields help make a comparison explicit, but they are not a complete
protocol. Observational or causal work usually also needs time zero,
follow-up, data source, intended use, and a clearly defined effect of interest.

<a id="target-trial-emulation"></a>
## Target trial emulation

[Target trial
emulation](https://www.nice.org.uk/corporate/ecd9/chapter/methods-for-real-world-studies-of-comparative-effects)
designs a non-randomized study to mimic the randomized trial that would
ideally answer a comparative-effect question. Eligibility, treatment
strategies, assignment, follow-up, outcomes, causal contrast, and analysis
must be specified together. Emulation can expose time-related and selection
biases; it cannot automatically remove confounding, measurement error, or
missing data.

<a id="estimand"></a>
## Estimand

An [estimand](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/e9r1-statistical-principles-clinical-trials-addendum-estimands-and-sensitivity-analysis-clinical)
is a precise description of the treatment effect a study intends to estimate.
Under ICH E9(R1), it connects the objective to the population, treatment
conditions, outcome, handling of intercurrent events, and population-level
summary. The estimator and analysis method should target that estimand; they
are not the estimand itself.

<a id="phenotype"></a>
## Phenotype

In observational health-data research, a [phenotype or cohort
definition](https://ohdsi.github.io/TheBookOfOhdsi/Cohorts.html) describes an
observable clinical state and the operational logic used to identify it in
recorded data. A code list may be one input, but timing, inclusion, exclusion,
entry, and exit logic can also matter. A phenotype must be reviewed and
validated for its intended question and data source.

<a id="data-contract"></a>
## Data contract

In this project, a [data
contract](../skills/clinical-data-research-navigator/references/evidence-output-template.md#implementation-specification)
is the logical agreement an implementation must satisfy: grain, keys, joins,
coverage, types, time anchors, terminology, missingness, precedence, lineage,
and acceptance fixtures. It describes what is required without inventing an
institution's physical table or column names.

<a id="governing-artifact"></a>
## Governing artifact

A [governing
artifact](../skills/clinical-data-research-navigator/references/retrieval-playbook.md)
is the highest-authority current source that controls a decision in context,
such as an applicable standard, regulator guidance, protocol, SAP, or approved
institutional metadata. A search result, tutorial, or older implementation
paper may help discovery, but it cannot silently override the governing
artifact. Record its identity, version or date, applicability, and provenance.

<a id="sas"></a>
## SAS

[SAS](https://www.sas.com/en_us/software/stat.html) is a software environment
and programming language used for data management and statistical analysis.
In this project, a request for SAS can lead to an explanation, evidence route,
or implementation specification. It leads to executable code only when the
required metadata, parameters, approved Adapter, and fixtures satisfy the
execution gate.

<a id="validation-gap"></a>
## Validation gap

A [validation
gap](../skills/clinical-data-research-navigator/references/evidence-output-template.md#implementation-specification)
is a missing source, decision, metadata item, check, or acceptance result that
blocks a stronger claim or code-maturity level. Naming the gap does not prove
the work is invalid; it states exactly what remains unverified and what
evidence would close it.
