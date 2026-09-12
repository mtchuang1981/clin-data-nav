from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/clin-nav"
OUTPUT_DEPTHS = {
    "quick explanation",
    "evidence navigation",
    "research design",
    "implementation specification",
}
COMMON_HEADER_FIELDS = (
    "Decision:",
    "Confirmed facts:",
    "Assumptions:",
    "Limitations:",
    "Sources actually consulted:",
)


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


def test_skill_routes_observed_ambiguous_requests_by_primary_deliverable():
    """Code words must not override source, profile, phenotype, or handoff intent."""
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8").lower()

    expected_routes = (
        ("implementation literature", "evidence navigation"),
        ("doi or dated public snapshot", "evidence navigation"),
        ("standard, local, and research phenotype", "research design"),
        ("optional collaborator availability", "research design"),
    )
    for trigger, depth in expected_routes:
        line = next(line for line in text.splitlines() if trigger in line)
        assert f"`{depth}`" in line

    assert re.search(r"primary deliverable\s+takes precedence", text)
    assert re.search(r"mentions code, optimization, or\s+implementation", text)


def test_skill_has_positive_completion_slots_for_every_output_depth():
    """Observed omissions need explicit slots, not a growing prohibition list."""
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    completion = text.split("## Complete the Selected Shape", 1)[1].split(
        "## Classify the Question", 1
    )[0]

    for depth in OUTPUT_DEPTHS:
        assert f"`{depth}`" in completion
    for required_slot in (
        "expand named acronyms",
        "source identity and provenance",
        "network or access status",
        "RWD/RWE claim boundary",
        "analysis plan and data limitations",
        "optional-collaborator status",
        "governing authority",
        "live-metadata and fixture gaps",
    ):
        assert required_slot in completion


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

    assert "natural short prose" in quick_shape
    assert "fixed headings" in quick_shape
    assert "```text" not in quick_shape
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


def test_depth_templates_share_the_approved_header_and_distinct_mode_contracts():
    """Formal header fields and the distinct depth contracts must remain explicit."""
    template = (
        SKILL / "references/evidence-output-template.md"
    ).read_text(encoding="utf-8")
    depth_reference = (
        SKILL / "references/output-depths-and-learning-paths.md"
    ).read_text(encoding="utf-8")

    for text in (template, depth_reference):
        common = text.split("## Quick Explanation", 1)[0]
        for field in COMMON_HEADER_FIELDS:
            assert field in common

        quick = text.split("## Quick Explanation", 1)[1].split(
            "## Evidence Navigation", 1
        )[0]
        assert "natural" in quick.lower()
        assert "fixed header" in quick.lower() or "common header" in quick.lower()
        assert "```text" not in quick
        for forbidden in ("Evidence table", "Data contract", "Code maturity"):
            assert f"## {forbidden}" not in quick

        evidence = text.split("## Evidence Navigation", 1)[1].split(
            "## Research Design", 1
        )[0]
        for required in (
            "Search scope",
            "Authority-ordered route",
            "Evidence table",
            "Conflicts and unreviewed gaps",
        ):
            assert required in evidence

        research = text.split("## Research Design", 1)[1].split(
            "## Implementation Specification", 1
        )[0]
        for required in (
            "Primary intent and design route",
            "Design fields and time anchors",
            "Data suitability and claim boundary",
            "Bias and validation gaps",
            "Analysis or diagnostics",
        ):
            assert required in research

        implementation = text.split(
            "## Implementation Specification", 1
        )[1]
        for required in (
            "Governing evidence",
            "Data contract",
            "Code maturity",
            "Validation gaps",
            "Execution gate",
        ):
            assert required in implementation


def test_quick_defaults_to_natural_prose_while_formal_contracts_keep_the_header():
    """Quick simplification must not weaken the three formal deliverables."""
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    template = (
        SKILL / "references/evidence-output-template.md"
    ).read_text(encoding="utf-8")

    assert "keep the depth choice internal" in skill
    assert "Common header" not in next(
        line for line in skill.splitlines() if "`quick explanation`" in line
    )
    assert "## Common Header for Formal Deliverables" in template

    quick = template.split("## Quick Explanation", 1)[1].split(
        "## Evidence Navigation", 1
    )[0]
    assert "```text" not in quick
    assert "Output depth:" not in quick
    assert "## Direct answer" not in quick

    formal = template.split("## Evidence Navigation", 1)[0]
    assert "Output depth: [one approved depth]" in formal
    for field in COMMON_HEADER_FIELDS:
        assert field in formal

    for section in (
        "## Evidence Navigation",
        "## Research Design",
        "## Implementation Specification",
    ):
        assert section in template


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
    assert "Research question and study-design routing" in template
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
