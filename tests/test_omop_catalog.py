from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "vendor/ohdsi/omop-cdm-v5.4.2/OMOP_CDMv5.4_Field_Level.csv"
PROVENANCE = SOURCE.with_name("SOURCE.json")
CATALOG = ROOT / "skills/clin-nav/references/omop-v5.4-core-catalog.json"
RENDERER = ROOT / "scripts/render_omop_catalog.py"

EXPECTED_PROVENANCE = {
    "license": "Apache License 2.0",
    "retrieved_on": "2026-09-20",
    "source_commit": "aa047a3c620b5c842b4370a0c965e2aa72203b1d",
    "source_path": "inst/csv/OMOP_CDMv5.4_Field_Level.csv",
    "source_repository": "https://github.com/OHDSI/CommonDataModel",
    "source_sha256": "94006d0fac2a3911b5665ce421468fa99af23fb51a633148e5fe6045916ad950",
    "source_size_bytes": 130164,
    "source_tag": "v5.4.2",
}
EXPECTED_TABLES = (
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
TYPE_FAMILIES = {"integer", "decimal", "date", "datetime", "string"}


def _catalog() -> dict[str, object]:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def test_pinned_source_bytes_match_declared_public_provenance():
    """A local export or changed upstream byte stream must fail closed."""
    assert SOURCE.is_file()
    assert PROVENANCE.is_file()
    assert PROVENANCE.read_text(encoding="utf-8") == (
        json.dumps(EXPECTED_PROVENANCE, ensure_ascii=False, indent=2) + "\n"
    )
    source_bytes = SOURCE.read_bytes()
    assert len(source_bytes) == EXPECTED_PROVENANCE["source_size_bytes"]
    assert hashlib.sha256(source_bytes).hexdigest() == EXPECTED_PROVENANCE[
        "source_sha256"
    ]


def test_generated_catalog_has_complete_canonical_public_structure():
    """Dropping, reordering, or locally renaming public OMOP fields is a bug."""
    catalog = _catalog()
    assert set(catalog) == {
        "schema_version",
        "catalog_id",
        "omop_cdm_version",
        "allowlist_id",
        "allowlist_version",
        "source",
        "tables",
    }
    assert catalog["omop_cdm_version"] == "5.4"
    assert catalog["allowlist_id"] == "omop-v54-core-research-v1"
    assert catalog["allowlist_version"] == "1.0.0"
    assert catalog["source"] == EXPECTED_PROVENANCE

    tables = catalog["tables"]
    assert isinstance(tables, list)
    assert [table["canonical_table_name"] for table in tables] == list(
        EXPECTED_TABLES
    )
    assert [len(table["columns"]) for table in tables] == list(
        EXPECTED_COLUMN_COUNTS
    )
    assert sum(len(table["columns"]) for table in tables) == 178

    for table in tables:
        assert set(table) == {"canonical_table_name", "columns"}
        assert table["canonical_table_name"] in EXPECTED_TABLES
        for column in table["columns"]:
            assert set(column) == {
                "canonical_column_name",
                "type_family",
                "nullable",
                "primary_key",
                "foreign_key",
                "foreign_table",
                "foreign_column",
            }
            assert column["canonical_column_name"] == column[
                "canonical_column_name"
            ].upper()
            assert column["type_family"] in TYPE_FAMILIES
            assert isinstance(column["nullable"], bool)
            assert isinstance(column["primary_key"], bool)
            assert isinstance(column["foreign_key"], bool)
            if column["foreign_key"]:
                assert column["foreign_table"] == column["foreign_table"].upper()
                assert column["foreign_column"] == column["foreign_column"].upper()
            else:
                assert column["foreign_table"] is None
                assert column["foreign_column"] is None


def test_renderer_matches_checked_in_lf_catalog_bytes():
    """Manual catalog edits and platform line-ending drift must be detected."""
    renderer = importlib.import_module("scripts.render_omop_catalog")
    rendered = renderer.render_catalog(SOURCE)
    assert rendered == CATALOG.read_bytes()
    assert rendered.endswith(b"\n")
    assert b"\r" not in rendered


def test_renderer_check_mode_detects_changed_checked_in_catalog():
    """The reproducibility gate must fail without rewriting a stale catalog."""
    original = CATALOG.read_bytes()
    try:
        CATALOG.write_bytes(b"stale catalog\n")
        result = subprocess.run(
            [sys.executable, str(RENDERER), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert CATALOG.read_bytes() == b"stale catalog\n"
    finally:
        CATALOG.write_bytes(original)


@pytest.mark.parametrize(
    "mutation",
    (
        lambda text: text.replace(
            "person_id,Yes,integer", "gender_concept_id,Yes,integer", 1
        ),
        lambda text: text.replace("integer", "opaque_type", 1),
        lambda text: text.replace(",Yes,", ",Maybe,", 1),
    ),
)
def test_build_catalog_rejects_malformed_pinned_source_rows(tmp_path, mutation):
    """Unsafe datatype, flag, or duplicate-column mutations must not render."""
    renderer = importlib.import_module("scripts.render_omop_catalog")
    candidate = tmp_path / SOURCE.name
    candidate_bytes = mutation(SOURCE.read_text(encoding="cp1252")).encode("cp1252")
    candidate.write_bytes(candidate_bytes)
    original_hash = renderer.EXPECTED_SOURCE_SHA256
    original_size = renderer.EXPECTED_SOURCE_SIZE
    renderer.EXPECTED_SOURCE_SHA256 = hashlib.sha256(candidate_bytes).hexdigest()
    renderer.EXPECTED_SOURCE_SIZE = len(candidate_bytes)
    try:
        with pytest.raises(ValueError):
            renderer.build_catalog(candidate)
    finally:
        renderer.EXPECTED_SOURCE_SHA256 = original_hash
        renderer.EXPECTED_SOURCE_SIZE = original_size
