from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return " ".join((ROOT / relative_path).read_text(encoding="utf-8").split())


def test_bilingual_readmes_preserve_the_optional_metadata_only_boundary():
    """An install guide must not turn optional metadata checks into data access."""
    english = _read("README.md")
    traditional_chinese = _read("README.zh-TW.md")

    for text, phrases in (
        (
            english,
            (
                "Optional OMOP metadata connector",
                "explicitly authorizes read-only metadata access in the current request",
                "OMOP CDM v5.4",
                "v5.4.2",
                "13-table allowlist",
                "public Skill owns",
                "private `tmucrd-adapter` owns",
                "tbls schema inspection and redaction",
                "no row access or SQL execution",
                "metadata-only",
                "cannot produce `executable` or `validated`",
            ),
        ),
        (
            traditional_chinese,
            (
                "選用的 OMOP 中繼資料連接器",
                "在目前請求中明確授權唯讀中繼資料存取",
                "OMOP CDM v5.4",
                "v5.4.2",
                "13 個資料表的允許清單",
                "公開 Skill 負責",
                "私有 `tmucrd-adapter`",
                "tbls 的 schema 檢查與遮蔽",
                "不得存取資料列或執行 SQL",
                "僅限中繼資料",
                "不能產生 `executable` 或 `validated`",
            ),
        ),
    ):
        for phrase in phrases:
            assert phrase in text


def test_bilingual_installation_docs_keep_normal_install_instruction_only():
    """Optional offline checking must not add Python or connector setup to normal use."""
    english = _read("docs/installation.md")
    traditional_chinese = _read("docs/installation.zh-TW.md")

    for text, phrases in (
        (
            english,
            (
                "npx skills add mtchuang1981/clin-data-nav",
                "does not require Python",
                "Optional OMOP v5.4 metadata connector",
                "outside this repository and the installed Skill",
                "python .agents/skills/clin-nav/scripts/check_omop_metadata.py --capabilities <external-capabilities.json> --input <external-inspection.json> --as-of <RFC-3339-timestamp>",
                "The packaged checker validates those external files offline",
                "synthetic",
            ),
        ),
        (
            traditional_chinese,
            (
                "npx skills add mtchuang1981/clin-data-nav",
                "不需要 Python",
                "選用的 OMOP v5.4 中繼資料連接器",
                "本儲存庫與已安裝 Skill 之外",
                "python .agents/skills/clin-nav/scripts/check_omop_metadata.py --capabilities <external-capabilities.json> --input <external-inspection.json> --as-of <RFC-3339-timestamp>",
                "封裝的檢查器會離線驗證這些外部檔案",
                "合成",
            ),
        ),
    ):
        for phrase in phrases:
            assert phrase in text


def test_architecture_assigns_public_and_private_connector_ownership():
    """Public documentation must keep raw inspection and credentials with the private owner."""
    architecture = _read("docs/architecture.md")

    for phrase in (
        "ClinNav request + explicit authorization",
        "private tmucrd-adapter get_capabilities",
        "private tbls schema inspection/redaction",
        "closed metadata summary",
        "public ClinNav validator/status",
        "logical mapping gaps; never automatic execution",
        "OMOP CDM v5.4",
        "v5.4.2",
        "13-table allowlist",
        "no row access or SQL execution",
        "raw schema",
        "DSNs",
        "credentials",
        "metadata-only",
        "cannot produce `executable` or `validated`",
    ):
        assert phrase in architecture
