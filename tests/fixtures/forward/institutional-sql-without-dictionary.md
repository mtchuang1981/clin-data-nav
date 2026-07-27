## Decision

We cannot provide SQL against the institution’s unknown schema.

**SPECIFICATION ONLY — NOT EXECUTABLE**

Code maturity: `conceptual`

Confirmed: the requested cohort consists of adult patients with a qualifying medication exposure. No assumptions are made about the adult definition, medication codes, physical schema, joins, or date logic. An approved, versioned institutional Adapter, live metadata verification, and passing fixtures are required before SQL can be classified as executable.

## Evidence table

| Claim | Source | Authority level | Publication date | Version or snapshot | Applicability | Limitations |
|---|---|---|---|---|---|---|
| The requested population is adult patients with a medication exposure. | Institutional request | Requester-provided requirement | Not provided | Current request | Defines the high-level cohort | Does not define adulthood, medication qualification, or timing |
| No local tables, fields, keys, or mappings can be established from the supplied materials. | Materials supplied with the request | Institutional implementation evidence | Not provided | No approved snapshot supplied | Determines code maturity | A current data dictionary and live catalog were not available |
| Executable SQL requires approved mappings, current metadata, and successful fixture checks. | Institutional Adapter governance contract | Implementation governance | Not provided | Current methodology | Governs promotion to executable code | Does not itself supply institution-specific mappings |

## Data contract

**Population**

Include a person only when:

1. The person satisfies the institution-approved definition of “adult” at the approved age anchor.
2. The person has at least one qualifying medication exposure from the approved medication concept or value set.
3. The exposure falls within the approved observation window.
4. Any required enrollment, encounter, site, or data-completeness conditions are satisfied.

**Logical inputs**

- Person or demographic information: one governed person record or an approved method for resolving multiple records.
- Medication exposure events: one row per governed exposure event, prescription, order, dispense, administration, or other explicitly approved event type.
- Medication terminology mapping: the approved code system, release, value-set version, and handling of local or unmapped codes.
- Observation coverage, if required: the period during which medication exposure can be assessed reliably.

**Required institutional mappings**

- Physical source objects for each logical input
- Stable person key and approved linkage path
- Birth information and permitted precision
- Adult age threshold
- Age anchor, such as exposure date or cohort-entry date
- Medication exposure date or interval fields
- Included exposure event types
- Medication identity and approved value set
- Code system and terminology release
- Observation-window boundaries
- Deduplication rules
- Join cardinalities and multiplication checks
- Null, partial-date, and conflicting-record rules
- Source coverage and refresh timestamp
- Permitted output fields and disclosure controls

**Expected output**

At minimum, a governed cohort-level person identifier and the qualifying exposure evidence needed for auditability. Direct identifiers and unnecessary row-level clinical details should be excluded unless explicitly approved.

**Acceptance fixtures**

Fixtures should cover:

- A patient exactly at the adult age boundary
- Patients immediately below and above that boundary
- Missing or partial birth information
- Exposure exactly on each observation-window boundary
- Qualifying and nonqualifying medication codes
- Local, obsolete, unmapped, and out-of-scope codes
- Duplicate exposure records
- Multiple qualifying exposures for one patient
- Missing linkage keys and unexpected join multiplication
- Empty inputs and an expected zero-result cohort

## Code maturity

`conceptual`

**SPECIFICATION ONLY — NOT EXECUTABLE**

No placeholder SQL is supplied because SQL-shaped examples could be mistaken for valid institutional implementation.

## Validation gaps

- Approved and versioned institutional data dictionary
- Approved Adapter version and effective date
- Exact adult definition and age anchor
- Medication identity and governed value set
- Exposure-event semantics and observation window
- Physical mappings, keys, types, and join cardinalities
- Code-system and terminology versions
- Coverage and refresh information
- Live verification of objects, types, nullability, uniqueness, and date ranges
- Approved synthetic or de-identified fixtures
- Passing boundary, mapping, duplication, and zero-result tests
- Output-governance and disclosure review
- Reviewed cohort results and acceptance criteria

## Sources

- Institutional request, current submission; no versioned supporting artifacts supplied.
- Clinical Data Research Navigator, “Institutional Adapter Contract,” current local methodology.
