# Beginner Learning Paths

[繁體中文](learning-paths.zh-TW.md)

Choose the path closest to your current decision. You can stop after a useful
explanation or evidence review. Not every path ends in code. When a request
does reach implementation, the execution gate still applies.

<a id="learn-the-terms"></a>
## learn-the-terms — Clinical trials and CDISC

**Goal:** Understand the relationship among clinical research, CDISC, SDTM,
ADaM, the protocol, the statistical analysis plan (SAP), and implementation
evidence.

**Starting prompt:** “In `quick explanation` depth, what is SDTM, how does it
relate to ADaM, and what does neither standard prove about source-data
quality?”

**Expected depth:** Start with `quick explanation`. Move to `evidence
navigation` only when you need an applicable standard version, implementation
guide, regulator requirement, or study-specific governing artifact.

**Next reading:** Review [CDISC, SDTM, and ADaM in the
glossary](./glossary.md#cdisc), the [installation guide](./installation.md),
the synthetic [TEAE-to-SAS example](../examples/teae-to-sas-spec.md), and the
Skill's [output-depth
guide](../skills/clinical-data-research-navigator/references/output-depths-and-learning-paths.md).

**Stop or escalate when:** Stop when the definitions and limits answer your
question. Escalate to evidence navigation before choosing a version or
submission rule, and to implementation specification only when you need a
mapping or derivation contract. Do not infer a local mapping from a standard.

<a id="assess-the-evidence"></a>
## assess-the-evidence — RWD, RWE, and study design

**Goal:** Turn a broad real-world-data question into a scoped evidence route,
then decide whether a descriptive or causal-comparative research design is
warranted.

**Starting prompt:** “In `evidence navigation` depth, identify the governing
sources for this RWD question, separate RWD from the RWE claim, and list the
design information still missing.”

**Expected depth:** Use `evidence navigation` to locate and rank sources. Move
to `research design` after the question is clear enough to specify PICO or an
estimand, time zero, follow-up, data fitness, bias, and diagnostics. Target
trial emulation is considered only for a causal-comparative question.

**Next reading:** Review [RWD, RWE, PICO, target trial emulation, estimand, and
phenotype](./glossary.md#rwd), the [installation guide](./installation.md), the
synthetic [OMOP phenotype example](../examples/omop-phenotype-to-sql-spec.md),
and the Skill's [RWE question-routing
reference](../skills/clinical-data-research-navigator/references/rwe-question-routing.md).

**Stop or escalate when:** Stop after evidence navigation if the task is only
to find or compare sources. Escalate to research design when a study question
must be framed. Do not claim causal validity, data fitness, or a completed
analysis when confounding, measurement, provenance, or validation gaps remain.

<a id="prepare-an-implementation"></a>
## prepare-an-implementation — Institutional implementation

**Goal:** Convert public evidence and a defined decision into a logical data
contract without inventing an institution's physical schema.

**Starting prompt:** “In `implementation specification` depth, prepare a
logical derivation specification using only public synthetic examples, and
list what approved metadata and fixtures are still required.”

**Expected depth:** Use `implementation specification`. The result remains
`SPECIFICATION ONLY — NOT EXECUTABLE` until the approved Adapter, current live
metadata, parameters, and acceptance fixtures satisfy the execution gate.
Generating source code is not required when those inputs are absent.

**Next reading:** Review [data contract, governing artifact, SAS, and
validation gap](./glossary.md#data-contract), the [installation
guide](./installation.md), the synthetic [institutional mapping
example](../examples/synthetic-institutional-mapping.md), the Skill's
[Adapter contract](../skills/clinical-data-research-navigator/references/institutional-adapter-contract.md),
and [implementation output
template](../skills/clinical-data-research-navigator/references/evidence-output-template.md#implementation-specification).

**Stop or escalate when:** Stop at a logical specification whenever the
execution gate is incomplete. Escalate only through an approved private
workflow when authorized current metadata or fixtures are needed; do not copy
them into this public repository. Raise code maturity only after the required
checks pass.
