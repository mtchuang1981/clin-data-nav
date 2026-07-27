from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_ci_has_read_only_permissions_and_required_commands():
    workflow = yaml.safe_load(
        (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    )
    assert workflow["permissions"] == {"contents": "read"}
    rendered = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    for command in (
        "python -m pytest -q",
        "python scripts/validate_skill.py",
        "python scripts/check_public_boundary.py",
        "python scripts/package_skill.py --check-reproducible",
    ):
        assert command in rendered
    assert "secrets." not in rendered


def test_citation_and_license_metadata():
    citation = yaml.safe_load(
        (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    )
    assert citation["title"] == "Clinical Data Research Navigator"
    assert citation["version"] == "0.1.0"
    assert citation["license"] == "Apache-2.0"
    assert "Apache License" in (ROOT / "LICENSE").read_text(encoding="utf-8")


def test_citation_has_required_cff_1_2_schema_shape_and_author():
    citation = yaml.safe_load(
        (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    )
    assert isinstance(citation, dict)
    assert citation["cff-version"] == "1.2.0"
    assert citation["type"] == "software"
    for field in ("message", "title", "version", "license"):
        assert isinstance(citation[field], str) and citation[field].strip()
    assert citation["authors"] == [
        {"name": "Clinical Data Research Navigator contributors"}
    ]
    for author in citation["authors"]:
        assert isinstance(author, dict)
        assert (
            isinstance(author.get("name"), str)
            and author["name"].strip()
        ) or (
            isinstance(author.get("family-names"), str)
            and author["family-names"].strip()
        )


def test_contribution_provenance_evidence_is_required_without_private_documents():
    contributing = " ".join(
        (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8").split()
    )
    pr_template = " ".join(
        (ROOT / ".github/pull_request_template.md").read_text(
            encoding="utf-8"
        ).split()
    )
    for text in (contributing, pr_template):
        assert "auditable provenance" in text
        assert "source URL or identifier" in text
        assert "license, permission, or attestation" in text
        assert (
            "do not submit private or login-gated documents as evidence"
            in text.lower()
        )


def test_architecture_separates_independent_gates_from_packaging():
    architecture = " ".join(
        (ROOT / "docs/architecture.md").read_text(encoding="utf-8").split()
    )
    assert "Scanner --> Packager" not in architecture
    assert "Evaluator --> Packager" not in architecture
    assert "independent verification gates" in architecture
    assert "only validator is the packager's direct dependency" in architecture
    assert "does not imply that the boundary scan or evaluator passed" in architecture


def test_architecture_describes_ci_network_boundary_accurately():
    architecture = " ".join(
        (ROOT / "docs/architecture.md").read_text(encoding="utf-8").split()
    )
    assert "CI is offline" not in architecture
    assert "credential-free" in architecture
    assert "After dependency acquisition" in architecture
    assert "no institutional or external LLM network calls" in architecture
