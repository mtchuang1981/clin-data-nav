from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/clinical-data-research-navigator"
OUTPUT_DEPTHS = {
    "quick explanation",
    "evidence navigation",
    "research design",
    "implementation specification",
}


def test_skill_routes_all_six_references():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    for name in (
        "retrieval-playbook.md",
        "evidence-output-template.md",
        "institutional-adapter-contract.md",
        "tmucrd-public-profile.md",
        "rwe-question-routing.md",
        "output-depths-and-learning-paths.md",
    ):
        assert f"references/{name}" in text


def test_skill_selects_one_safe_least_sufficient_output_depth():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    for depth in OUTPUT_DEPTHS:
        assert f"`{depth}`" in text
    assert "Honor an explicitly requested safe depth" in text
    assert "least sufficient depth" in text
    assert "materially change the deliverable" in text
    assert "exactly one `Output depth: ` line" in text


def test_output_depth_reference_has_all_shapes_and_learning_paths():
    reference = SKILL / "references/output-depths-and-learning-paths.md"
    text = reference.read_text(encoding="utf-8")

    for depth in OUTPUT_DEPTHS:
        assert f"## {depth.title()}" in text
    for path in (
        "learn the terms",
        "assess the evidence",
        "prepare an implementation",
    ):
        assert path in text


def test_quick_shape_stays_light_and_implementation_shape_is_complete():
    reference = SKILL / "references/output-depths-and-learning-paths.md"
    text = reference.read_text(encoding="utf-8")
    quick_shape = text.split("## Quick Explanation", 1)[1].split(
        "## Evidence Navigation", 1
    )[0].lower()
    implementation_shape = text.split(
        "## Implementation Specification", 1
    )[1].lower()

    assert "data contract" not in quick_shape
    for required in (
        "governing artifact",
        "grain",
        "keys",
        "time anchor",
        "missingness",
        "terminology",
        "validation",
        "specification only — not executable",
    ):
        assert required in implementation_shape


def test_build_rwe_sap_is_optional():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()
    assert "optional" in text
    assert "build-rwe-sap" in text
    assert "must install build-rwe-sap" not in text


def test_rwe_question_routing_contract_is_explicit():
    skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    routing_path = SKILL / "references/rwe-question-routing.md"

    assert "references/rwe-question-routing.md" in skill_text
    assert routing_path.is_file()
    routing = routing_path.read_text(encoding="utf-8")
    assert "RWD is not automatically RWE" in routing
    assert "PICO does not establish causal validity" in routing
    assert "causal-comparative" in routing
    assert "TTE is not the default" in routing
    assert "unavailable" in routing
    assert "incompatible" in routing


def test_build_rwe_sap_handoff_and_degraded_operation_are_complete():
    routing_path = SKILL / "references/rwe-question-routing.md"
    assert routing_path.is_file()
    routing = routing_path.read_text(encoding="utf-8")

    for field in (
        "question_intent",
        "population",
        "intervention_or_exposure",
        "comparator",
        "outcomes",
        "time_zero",
        "follow_up",
        "target_estimand",
        "data_sources",
        "measured_confounders",
        "data_limitations",
        "authority_record",
        "validation_gaps",
    ):
        assert f"`{field}`" in routing
    assert "not bundled" in routing
    assert "Do not install or download it automatically" in routing
    assert "Continue the Core workflow" in routing
    assert "complete SAP" in routing

    template = (
        SKILL / "references/evidence-output-template.md"
    ).read_text(encoding="utf-8")
    assert "## Research question and study-design routing" in template
    assert "available, unavailable, or incompatible" in template


def test_skill_forbids_placeholder_sql_without_metadata():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "Do not provide even placeholder SQL" in text


def test_skill_forbids_schema_like_placeholder_names_without_metadata():
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    assert "Do not create snake_case placeholder identifiers" in text


def test_tmucrd_profile_is_public_snapshot_not_schema():
    text = (
        SKILL / "references/tmucrd-public-profile.md"
    ).read_text(encoding="utf-8")
    assert "public source snapshot" in text
    assert "not a data dictionary" in text
    assert "10.1136/bmjhci-2023-100890" in text
    assert "V2.16" not in text


def test_examples_use_only_synthetic_institutional_names():
    for path in (ROOT / "examples").glob("*.md"):
        text = path.read_text(encoding="utf-8")
        assert "SYNTH_" in text
        assert "TMUCRD" not in text
