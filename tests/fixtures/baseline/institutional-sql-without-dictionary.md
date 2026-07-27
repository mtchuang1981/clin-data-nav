I can provide a production-ready query only after the required source information is available. With no versioned data dictionary, live metadata, or test fixtures, an executable SQL statement would require inventing table names, fields, joins, date semantics, and medication codes—so it would not be reliable or safe to run.

Please provide:

- The versioned data dictionary and database/schema version
- Metadata for patient/demographic and medication-exposure sources, including keys and relationship cardinality
- The approved adult-age rule and index-date definition
- The medication concept set (and vocabulary/version), including whether route, status, dose, or supply constraints apply
- Exposure date rules (order, dispense, administration, start/end dates) and handling of reversals/cancellations
- A small de-identified fixture set with expected results

Once supplied, I will produce parameterized SQL that:

1. Calculates age as of the specified index date.
2. Selects qualifying medication exposures using the approved concept set.
3. Deduplicates patients/exposures according to the stated cohort rule.
4. Includes data-quality checks for null keys, invalid date ranges, duplicate records, and unmatched concepts.
5. Is validated against the fixture set before delivery.
