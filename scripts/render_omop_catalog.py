"""Render the pinned public OMOP v5.4 core catalog deterministically."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "vendor/ohdsi/omop-cdm-v5.4.2/OMOP_CDMv5.4_Field_Level.csv"
CATALOG_PATH = ROOT / "skills/clin-nav/references/omop-v5.4-core-catalog.json"
EXPECTED_SOURCE_SHA256 = (
    "94006d0fac2a3911b5665ce421468fa99af23fb51a633148e5fe6045916ad950"
)
EXPECTED_SOURCE_SIZE = 130164
ALLOWLIST = (
    "PERSON",
    "OBSERVATION_PERIOD",
    "VISIT_OCCURRENCE",
    "CONDITION_OCCURRENCE",
    "DRUG_EXPOSURE",
    "PROCEDURE_OCCURRENCE",
    "MEASUREMENT",
    "OBSERVATION",
    "DEATH",
    "CDM_SOURCE",
    "VOCABULARY",
    "CONCEPT",
    "CONCEPT_RELATIONSHIP",
)
EXPECTED_COLUMN_COUNTS = (18, 5, 17, 16, 23, 16, 23, 21, 7, 11, 5, 10, 6)
EXPECTED_HEADER = (
    "cdmTableName",
    "cdmFieldName",
    "isRequired",
    "cdmDatatype",
    "userGuidance",
    "etlConventions",
    "isPrimaryKey",
    "isForeignKey",
    "fkTableName",
    "fkFieldName",
    "fkDomain",
    "fkClass",
    "unique DQ identifiers",
)
TYPE_FAMILIES = {
    "integer": "integer",
    "float": "decimal",
    "date": "date",
    "datetime": "datetime",
}
SOURCE_PROVENANCE = {
    "license": "Apache License 2.0",
    "retrieved_on": "2026-09-20",
    "source_commit": "aa047a3c620b5c842b4370a0c965e2aa72203b1d",
    "source_path": "inst/csv/OMOP_CDMv5.4_Field_Level.csv",
    "source_repository": "https://github.com/OHDSI/CommonDataModel",
    "source_sha256": EXPECTED_SOURCE_SHA256,
    "source_size_bytes": EXPECTED_SOURCE_SIZE,
    "source_tag": "v5.4.2",
}


def _canonical(value: str) -> str:
    return value.upper()


def _yes_no(value: str, field: str) -> bool:
    if value == "Yes":
        return True
    if value == "No":
        return False
    raise ValueError(f"invalid {field} flag: {value!r}")


def _type_family(datatype: str) -> str:
    normalized = datatype.casefold()
    if normalized.startswith("varchar(") and normalized.endswith(")"):
        return "string"
    try:
        return TYPE_FAMILIES[normalized]
    except KeyError as error:
        raise ValueError(f"unknown OMOP datatype: {datatype!r}") from error


def _read_rows(source: Path) -> list[dict[str, str]]:
    source_bytes = source.read_bytes()
    actual_hash = hashlib.sha256(source_bytes).hexdigest()
    if actual_hash != EXPECTED_SOURCE_SHA256:
        raise ValueError("pinned OMOP source SHA-256 does not match")
    if len(source_bytes) != EXPECTED_SOURCE_SIZE:
        raise ValueError("pinned OMOP source size does not match")

    reader = csv.DictReader(io.StringIO(source_bytes.decode("cp1252")))
    if tuple(reader.fieldnames or ()) != EXPECTED_HEADER:
        raise ValueError("OMOP source CSV header does not match")
    rows = list(reader)
    if any(row is None or None in row for row in rows):
        raise ValueError("OMOP source CSV contains malformed rows")
    return rows


def build_catalog(source: Path) -> dict[str, object]:
    """Build the approved public OMOP catalog from an immutable source file."""
    rows = _read_rows(source)
    public_columns: dict[str, set[str]] = {}
    for row in rows:
        table_name = _canonical(row["cdmTableName"])
        public_columns.setdefault(table_name, set()).add(
            _canonical(row["cdmFieldName"])
        )

    tables: list[dict[str, object]] = []
    for table_name, expected_count in zip(ALLOWLIST, EXPECTED_COLUMN_COUNTS):
        table_rows = [
            row for row in rows if _canonical(row["cdmTableName"]) == table_name
        ]
        if not table_rows:
            raise ValueError(f"required OMOP table is absent: {table_name}")

        seen_columns: set[str] = set()
        columns: list[dict[str, object]] = []
        for row in table_rows:
            column_name = _canonical(row["cdmFieldName"])
            if column_name in seen_columns:
                raise ValueError(
                    f"duplicate OMOP column: {table_name}.{column_name}"
                )
            seen_columns.add(column_name)

            foreign_key = _yes_no(row["isForeignKey"], "isForeignKey")
            if foreign_key:
                foreign_table = _canonical(row["fkTableName"])
                foreign_column = _canonical(row["fkFieldName"])
                if (
                    foreign_table == "NA"
                    or foreign_column == "NA"
                    or foreign_table not in public_columns
                    or foreign_column not in public_columns[foreign_table]
                ):
                    raise ValueError(
                        f"non-public OMOP foreign key target: "
                        f"{foreign_table}.{foreign_column}"
                    )
            else:
                foreign_table = None
                foreign_column = None

            columns.append(
                {
                    "canonical_column_name": column_name,
                    "type_family": _type_family(row["cdmDatatype"]),
                    "nullable": not _yes_no(row["isRequired"], "isRequired"),
                    "primary_key": _yes_no(row["isPrimaryKey"], "isPrimaryKey"),
                    "foreign_key": foreign_key,
                    "foreign_table": foreign_table,
                    "foreign_column": foreign_column,
                }
            )

        if len(columns) != expected_count:
            raise ValueError(
                f"unexpected OMOP column count for {table_name}: {len(columns)}"
            )
        tables.append({"canonical_table_name": table_name, "columns": columns})

    if sum(len(table["columns"]) for table in tables) != 178:
        raise ValueError("unexpected total OMOP column count")
    return {
        "schema_version": "1",
        "catalog_id": "omop-cdm-v5.4.2-core-research",
        "omop_cdm_version": "5.4",
        "allowlist_id": "omop-v54-core-research-v1",
        "allowlist_version": "1.0.0",
        "source": SOURCE_PROVENANCE,
        "tables": tables,
    }


def render_catalog(source: Path) -> bytes:
    """Return canonical UTF-8 JSON bytes with exactly one final LF."""
    return (
        json.dumps(
            build_catalog(source),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the checked-in catalog differs from generated bytes",
    )
    args = parser.parse_args(argv)
    rendered = render_catalog(SOURCE_PATH)
    if args.check:
        return 0 if CATALOG_PATH.is_file() and CATALOG_PATH.read_bytes() == rendered else 1
    CATALOG_PATH.write_bytes(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
