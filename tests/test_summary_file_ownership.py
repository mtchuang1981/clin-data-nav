from pathlib import Path
from types import SimpleNamespace
import os

import pytest

from summary_file_ownership import SummaryFileOwnership


def prepared(tmp_path):
    tracker = SummaryFileOwnership()
    backup = tmp_path / '.summary.backup-owned.tmp'
    stage = tmp_path / '.summary.stage-owned.tmp'
    output = tmp_path / 'summary.json'
    backup.write_bytes(b'prior')
    stage.write_bytes(b'next')
    tracker.capture('backup', backup)
    tracker.capture('stage', stage)
    return tracker, backup, stage, output


def test_commit_retains_stage_identity_and_retires_backup(tmp_path):
    tracker, backup, stage, output = prepared(tmp_path)
    backup.unlink()
    stage.rename(output)
    tracker.assert_committed(output)


@pytest.mark.parametrize('same_name', [False, True])
def test_foreign_objects_are_preserved_even_at_the_old_backup_name(tmp_path, same_name):
    tracker, backup, stage, output = prepared(tmp_path)
    # Keep the foreign inode allocated while retiring the real backup, so the
    # test does not depend on an allocator avoiding inode reuse.
    foreign = tmp_path / (backup.name.upper() + '.tmp')
    foreign.write_bytes(b'foreign')
    before = foreign.lstat()
    backup.unlink()
    stage.rename(output)
    if same_name:
        foreign = foreign.rename(backup)
    tracker.assert_committed(output)
    assert foreign.read_bytes() == b'foreign'
    assert (foreign.lstat().st_dev, foreign.lstat().st_ino) == (before.st_dev, before.st_ino)


@pytest.mark.parametrize('name', [None, 'ordinary.bin', '.SUMMARY.BACKUP-OWNED.TMP.tmp'])
def test_real_backup_leak_fails_even_after_rename(tmp_path, name):
    tracker, backup, stage, output = prepared(tmp_path)
    stage.rename(output)
    if name:
        backup = backup.rename(tmp_path / name)
    with pytest.raises(AssertionError, match='owned transaction file remains'):
        tracker.assert_committed(output)
    assert backup.read_bytes() == b'prior'


def test_stage_hardlink_alias_fails_even_with_an_unrelated_name(tmp_path):
    tracker, backup, stage, output = prepared(tmp_path)
    alias = tmp_path / 'ordinary-alias.bin'
    try:
        os.link(stage, alias)
    except OSError:
        pytest.skip('filesystem cannot create hardlinks')
    backup.unlink()
    stage.rename(output)
    with pytest.raises(AssertionError, match='owned transaction file remains'):
        tracker.assert_committed(output)
    assert alias.read_bytes() == output.read_bytes() == b'next'


def test_matching_content_cannot_substitute_for_the_stage_identity(tmp_path):
    tracker, backup, stage, output = prepared(tmp_path)
    backup.unlink()
    stage.rename(tmp_path / 'real-stage.bin')
    output.write_bytes(b'next')
    with pytest.raises(AssertionError, match='output identity'):
        tracker.assert_committed(output)


def test_missing_output_fails(tmp_path):
    tracker, backup, stage, output = prepared(tmp_path)
    backup.unlink()
    with pytest.raises(AssertionError, match='cannot inspect'):
        tracker.assert_committed(output)


def test_zero_identity_fails_instead_of_falling_back_to_names(tmp_path, monkeypatch):
    path = tmp_path / 'stage'
    path.write_bytes(b'next')
    original = Path.lstat
    monkeypatch.setattr(Path, 'lstat', lambda self: SimpleNamespace(st_dev=1, st_ino=0)
                        if self == path else original(self))
    with pytest.raises(AssertionError, match='unavailable identity'):
        SummaryFileOwnership().capture('stage', path)


def test_unreadable_foreign_entry_fails_closed(tmp_path, monkeypatch):
    tracker, backup, stage, output = prepared(tmp_path)
    backup.unlink()
    stage.rename(output)
    foreign = tmp_path / 'foreign'
    foreign.write_bytes(b'foreign')
    original = Path.lstat

    def lstat(self):
        if self == foreign:
            raise PermissionError('synthetic metadata denial')
        return original(self)

    monkeypatch.setattr(Path, 'lstat', lstat)
    with pytest.raises(AssertionError, match='cannot inspect'):
        tracker.assert_committed(output)


def test_disappearing_foreign_entry_does_not_require_retries(tmp_path, monkeypatch):
    tracker, backup, stage, output = prepared(tmp_path)
    backup.unlink()
    stage.rename(output)
    foreign = tmp_path / 'foreign'
    foreign.write_bytes(b'foreign')
    original = Path.lstat

    def lstat(self):
        if self == foreign:
            raise FileNotFoundError('synthetic disappearance after enumeration')
        return original(self)

    monkeypatch.setattr(Path, 'lstat', lstat)
    tracker.assert_committed(output)
    assert foreign.read_bytes() == b'foreign'


def test_missing_capture_fails(tmp_path):
    output = tmp_path / 'summary.json'
    output.write_bytes(b'next')
    with pytest.raises(AssertionError, match='stage was not captured'):
        SummaryFileOwnership().assert_committed(output)


def test_capture_rejects_duplicate_roles_and_different_parents(tmp_path):
    tracker, backup, stage, output = prepared(tmp_path)
    with pytest.raises(AssertionError, match='already captured'):
        tracker.capture('stage', stage)
    other = tmp_path / 'other'
    other.mkdir()
    elsewhere = other / 'stage'
    elsewhere.write_bytes(b'next')
    fresh = SummaryFileOwnership()
    fresh.capture('backup', backup)
    with pytest.raises(AssertionError, match='different parent'):
        fresh.capture('stage', elsewhere)


def rollback_prepared(tmp_path, prior_output):
    if prior_output:
        return prepared(tmp_path)
    tracker = SummaryFileOwnership()
    stage = tmp_path / '.summary.stage-owned.tmp'
    stage.write_bytes(b'next')
    tracker.capture('stage', stage)
    return tracker, None, stage, tmp_path / 'summary.json'


def complete_rollback(backup, stage, output):
    stage.unlink()
    if backup is not None:
        backup.rename(output)


@pytest.mark.parametrize('prior_output', [False, True])
def test_rollback_checks_the_explicit_original_output_state(tmp_path, prior_output):
    tracker, backup, stage, output = rollback_prepared(tmp_path, prior_output)
    complete_rollback(backup, stage, output)
    tracker.assert_rolled_back(output, prior_output=prior_output)


@pytest.mark.parametrize('prior_output', [False, True])
@pytest.mark.parametrize('old_stage_name', [False, True])
def test_rollback_preserves_foreign_objects(tmp_path, prior_output, old_stage_name):
    tracker, backup, stage, output = rollback_prepared(tmp_path, prior_output)
    foreign = tmp_path / (stage.name.upper() + '.tmp')
    foreign.write_bytes(b'foreign')
    before = foreign.lstat()
    complete_rollback(backup, stage, output)
    if old_stage_name:
        foreign = foreign.rename(stage)
    tracker.assert_rolled_back(output, prior_output=prior_output)
    assert foreign.read_bytes() == b'foreign'
    assert (foreign.lstat().st_dev, foreign.lstat().st_ino) == (before.st_dev, before.st_ino)


@pytest.mark.parametrize('prior_output', [False, True])
@pytest.mark.parametrize('name', [None, 'ordinary.bin', '.SUMMARY.STAGE-OWNED.TMP.tmp'])
def test_rollback_detects_owned_stage_under_any_name(tmp_path, prior_output, name):
    tracker, backup, stage, output = rollback_prepared(tmp_path, prior_output)
    if backup is not None:
        backup.rename(output)
    if name:
        stage = stage.rename(tmp_path / name)
    with pytest.raises(AssertionError, match='owned transaction file remains'):
        tracker.assert_rolled_back(output, prior_output=prior_output)
    assert stage.read_bytes() == b'next'


@pytest.mark.parametrize('prior_output', [False, True])
def test_rollback_detects_a_stage_alias_after_its_original_name_is_retired(tmp_path, prior_output):
    tracker, backup, stage, output = rollback_prepared(tmp_path, prior_output)
    alias = tmp_path / 'ordinary-alias.bin'
    try:
        os.link(stage, alias)
    except OSError:
        pytest.skip('filesystem cannot create hardlinks')
    complete_rollback(backup, stage, output)
    with pytest.raises(AssertionError, match='owned transaction file remains'):
        tracker.assert_rolled_back(output, prior_output=prior_output)
    assert alias.read_bytes() == b'next'


def test_rollback_rejects_same_content_with_the_wrong_restored_identity(tmp_path):
    tracker, backup, stage, output = prepared(tmp_path)
    backup.rename(tmp_path / 'retained-original.bin')
    stage.unlink()
    output.write_bytes(b'prior')
    with pytest.raises(AssertionError, match='output identity'):
        tracker.assert_rolled_back(output, prior_output=True)


def test_rollback_rejects_a_missing_required_output(tmp_path):
    tracker, backup, stage, output = prepared(tmp_path)
    stage.unlink()
    with pytest.raises(AssertionError, match='cannot inspect output'):
        tracker.assert_rolled_back(output, prior_output=True)


@pytest.mark.parametrize('kind', ['file', 'directory', 'broken-symlink'])
def test_rollback_requires_real_absence_when_there_was_no_output(tmp_path, kind):
    tracker, backup, stage, output = rollback_prepared(tmp_path, False)
    complete_rollback(backup, stage, output)
    if kind == 'file':
        output.write_bytes(b'unexpected')
    elif kind == 'directory':
        output.mkdir()
    else:
        try:
            output.symlink_to(tmp_path / 'missing-target')
        except OSError:
            pytest.skip('filesystem cannot create a symlink')
        assert not output.exists()
    with pytest.raises(AssertionError, match='output should be absent'):
        tracker.assert_rolled_back(output, prior_output=False)


@pytest.mark.parametrize('prior_output', [False, True])
def test_rollback_prior_state_must_agree_with_backup_capture(tmp_path, prior_output):
    tracker, backup, stage, output = rollback_prepared(tmp_path, prior_output)
    complete_rollback(backup, stage, output)
    with pytest.raises(AssertionError, match='backup capture'):
        tracker.assert_rolled_back(output, prior_output=not prior_output)


def test_rollback_requires_stage_capture(tmp_path):
    with pytest.raises(AssertionError, match='stage was not captured'):
        SummaryFileOwnership().assert_rolled_back(tmp_path / 'summary.json', prior_output=False)


def test_rollback_rejects_an_unavailable_final_output_identity(tmp_path, monkeypatch):
    tracker, backup, stage, output = prepared(tmp_path)
    complete_rollback(backup, stage, output)
    original = Path.lstat
    monkeypatch.setattr(Path, 'lstat', lambda self: SimpleNamespace(st_dev=1, st_ino=0)
                        if self == output else original(self))
    with pytest.raises(AssertionError, match='unavailable identity'):
        tracker.assert_rolled_back(output, prior_output=True)


@pytest.mark.parametrize('prior_output', [False, True])
def test_rollback_cannot_ignore_unreadable_foreign_metadata(tmp_path, monkeypatch, prior_output):
    tracker, backup, stage, output = rollback_prepared(tmp_path, prior_output)
    foreign = tmp_path / 'foreign'
    foreign.write_bytes(b'foreign')
    complete_rollback(backup, stage, output)
    original = Path.lstat

    def lstat(self):
        if self == foreign:
            raise PermissionError('synthetic metadata denial')
        return original(self)

    monkeypatch.setattr(Path, 'lstat', lstat)
    with pytest.raises(AssertionError, match='cannot inspect'):
        tracker.assert_rolled_back(output, prior_output=prior_output)


@pytest.mark.parametrize('prior_output', [False, True])
def test_rollback_inspects_a_disappearing_foreign_entry_once(tmp_path, monkeypatch, prior_output):
    tracker, backup, stage, output = rollback_prepared(tmp_path, prior_output)
    foreign = tmp_path / 'foreign'
    foreign.write_bytes(b'foreign')
    complete_rollback(backup, stage, output)
    original = Path.lstat
    attempts = 0

    def lstat(self):
        nonlocal attempts
        if self == foreign:
            attempts += 1
            raise FileNotFoundError('synthetic disappearance')
        return original(self)

    monkeypatch.setattr(Path, 'lstat', lstat)
    tracker.assert_rolled_back(output, prior_output=prior_output)
    assert attempts == 1
    assert foreign.read_bytes() == b'foreign'


def test_rollback_cannot_ignore_required_output_disappearing_during_scan(tmp_path, monkeypatch):
    tracker, backup, stage, output = prepared(tmp_path)
    complete_rollback(backup, stage, output)
    original = Path.lstat
    attempts = 0

    def lstat(self):
        nonlocal attempts
        if self == output:
            attempts += 1
            if attempts == 2:
                raise FileNotFoundError('synthetic output disappearance')
        return original(self)

    monkeypatch.setattr(Path, 'lstat', lstat)
    with pytest.raises(AssertionError, match='cannot inspect output'):
        tracker.assert_rolled_back(output, prior_output=True)


def test_rollback_detects_output_appearing_after_the_absence_check(tmp_path, monkeypatch):
    tracker, backup, stage, output = rollback_prepared(tmp_path, False)
    complete_rollback(backup, stage, output)
    original = Path.iterdir

    def iterdir(self):
        if self == tmp_path:
            output.write_bytes(b'unexpected')
        return original(self)

    monkeypatch.setattr(Path, 'iterdir', iterdir)
    with pytest.raises(AssertionError, match='output should be absent'):
        tracker.assert_rolled_back(output, prior_output=False)


def test_rollback_rejects_forbidden_output_that_vanishes_after_enumeration(tmp_path, monkeypatch):
    tracker, backup, stage, output = rollback_prepared(tmp_path, False)
    complete_rollback(backup, stage, output)
    original = Path.iterdir

    def iterdir(self):
        if self == tmp_path:
            output.write_bytes(b'unexpected')
            entries = list(original(self))
            output.unlink()
            return iter(entries)
        return original(self)

    monkeypatch.setattr(Path, 'iterdir', iterdir)
    with pytest.raises(AssertionError, match='output should be absent'):
        tracker.assert_rolled_back(output, prior_output=False)
    assert not output.exists()
