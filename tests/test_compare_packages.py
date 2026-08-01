import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.compare_packages import compare_package_directories, main


ZIP_NAME = "candidate.zip"
MANIFEST_NAME = "candidate.manifest.json"


def _write_package(
    directory: Path,
    *,
    zip_name: str = ZIP_NAME,
    manifest_name: str = MANIFEST_NAME,
    zip_bytes: bytes = b"zip bytes",
    manifest_bytes: bytes = b'{"archive":"candidate.zip"}',
) -> None:
    directory.mkdir()
    (directory / zip_name).write_bytes(zip_bytes)
    (directory / manifest_name).write_bytes(manifest_bytes)


def _matching_packages(tmp_path: Path) -> tuple[Path, Path]:
    first = tmp_path / "first"
    second = tmp_path / "second"
    _write_package(first)
    _write_package(second)
    return first, second


def _root_symlink_or_root_with_symlink_flag(
    tmp_path: Path, target: Path, monkeypatch
) -> Path:
    """Return a root symlink, or deterministically exercise its check."""
    linked_root = tmp_path / "linked-root"
    try:
        linked_root.symlink_to(target, target_is_directory=True)
    except OSError:
        monkeypatch.setattr(
            Path,
            "is_symlink",
            lambda path: path == target,
        )
        return target
    return linked_root


def test_identical_packages_return_sorted_file_names(tmp_path):
    first, second = _matching_packages(tmp_path)

    assert compare_package_directories(first, second) == (
        MANIFEST_NAME,
        ZIP_NAME,
    )


def test_missing_directory_is_rejected_with_a_stable_label(tmp_path):
    first, second = _matching_packages(tmp_path)
    for entry in second.iterdir():
        entry.unlink()
    second.rmdir()

    with pytest.raises(ValueError, match=r"^second: directory does not exist$"):
        compare_package_directories(first, second)


@pytest.mark.parametrize(
    ("position", "label"),
    ((0, "first"), (1, "second")),
)
def test_root_directory_symlink_is_rejected_for_each_input(
    tmp_path, monkeypatch, position, label
):
    first, second = _matching_packages(tmp_path)
    packages = [first, second]
    packages[position] = _root_symlink_or_root_with_symlink_flag(
        tmp_path,
        packages[position],
        monkeypatch,
    )

    with pytest.raises(
        ValueError,
        match=rf"^{label}: directory must not be a symlink$",
    ):
        compare_package_directories(*packages)


def test_entry_symlink_remains_rejected(tmp_path, monkeypatch):
    first, second = _matching_packages(tmp_path)
    zip_path = first / ZIP_NAME
    zip_path.unlink()
    try:
        zip_path.symlink_to(second / ZIP_NAME)
    except OSError:
        zip_path.write_bytes(b"zip bytes")
        monkeypatch.setattr(
            Path,
            "is_symlink",
            lambda path: path == zip_path,
        )

    with pytest.raises(
        ValueError,
        match=r"^first: unexpected entry: candidate\.zip$",
    ):
        compare_package_directories(first, second)


def test_missing_zip_is_rejected(tmp_path):
    first, second = _matching_packages(tmp_path)
    (first / ZIP_NAME).unlink()

    with pytest.raises(
        ValueError,
        match=r"^first: expected exactly one \.zip file, found 0$",
    ):
        compare_package_directories(first, second)


def test_missing_manifest_is_rejected(tmp_path):
    first, second = _matching_packages(tmp_path)
    (first / MANIFEST_NAME).unlink()

    with pytest.raises(
        ValueError,
        match=r"^first: expected exactly one \.manifest\.json file, found 0$",
    ):
        compare_package_directories(first, second)


def test_extra_file_is_rejected_with_its_relative_name(tmp_path):
    first, second = _matching_packages(tmp_path)
    (first / "notes.txt").write_text("unexpected", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=r"^first: unexpected entry: notes\.txt$",
    ):
        compare_package_directories(first, second)


def test_nested_directory_is_rejected_with_its_relative_name(tmp_path):
    first, second = _matching_packages(tmp_path)
    (first / "nested").mkdir()

    with pytest.raises(
        ValueError,
        match=r"^first: nested directory: nested$",
    ):
        compare_package_directories(first, second)


def test_two_zips_are_rejected(tmp_path):
    first, second = _matching_packages(tmp_path)
    (first / "second.zip").write_bytes(b"another zip")

    with pytest.raises(
        ValueError,
        match=r"^first: expected exactly one \.zip file, found 2$",
    ):
        compare_package_directories(first, second)


def test_renamed_zip_is_rejected(tmp_path):
    first, second = _matching_packages(tmp_path)
    (second / ZIP_NAME).rename(second / "renamed.zip")

    with pytest.raises(
        ValueError,
        match=r"^package file names differ: candidate\.zip != renamed\.zip$",
    ):
        compare_package_directories(first, second)


def test_renamed_manifest_is_rejected(tmp_path):
    first, second = _matching_packages(tmp_path)
    (second / MANIFEST_NAME).rename(second / "renamed.manifest.json")

    with pytest.raises(
        ValueError,
        match=(
            r"^package file names differ: "
            r"candidate\.manifest\.json != renamed\.manifest\.json$"
        ),
    ):
        compare_package_directories(first, second)


def test_zip_byte_mismatch_is_rejected_with_its_file_name(tmp_path):
    first, second = _matching_packages(tmp_path)
    (second / ZIP_NAME).write_bytes(b"different zip bytes")

    with pytest.raises(ValueError, match=r"^byte mismatch: candidate\.zip$"):
        compare_package_directories(first, second)


def test_manifest_byte_mismatch_is_rejected_with_its_file_name(tmp_path):
    first, second = _matching_packages(tmp_path)
    (second / MANIFEST_NAME).write_bytes(b'{"archive":"other.zip"}')

    with pytest.raises(
        ValueError,
        match=r"^byte mismatch: candidate\.manifest\.json$",
    ):
        compare_package_directories(first, second)


def test_cli_prints_sorted_file_names_and_sha256_values_on_success(
    tmp_path, capsys
):
    first, second = _matching_packages(tmp_path)

    assert main(["--first", str(first), "--second", str(second)]) == 0

    output = capsys.readouterr().out.splitlines()
    assert output == [
        f"{MANIFEST_NAME} "
        f"{hashlib.sha256((first / MANIFEST_NAME).read_bytes()).hexdigest()}",
        f"{ZIP_NAME} {hashlib.sha256((first / ZIP_NAME).read_bytes()).hexdigest()}",
    ]


def test_cli_returns_nonzero_and_one_error_on_invalid_package(tmp_path):
    first, second = _matching_packages(tmp_path)
    (first / ZIP_NAME).unlink()

    result = subprocess.run(
        [
            sys.executable,
            "scripts/compare_packages.py",
            "--first",
            str(first),
            "--second",
            str(second),
        ],
        capture_output=True,
        check=False,
        cwd=Path(__file__).resolve().parents[1],
        text=True,
    )

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == "first: expected exactly one .zip file, found 0\n"
