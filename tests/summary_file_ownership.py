"""Metadata-only assertions for synthetic summary transaction tests."""
from pathlib import Path


class SummaryFileOwnership:
    def __init__(self) -> None:
        self.parent: Path | None = None
        self.identities: dict[str, tuple[int, int]] = {}

    @staticmethod
    def _identity(path: Path) -> tuple[int, int]:
        metadata = path.lstat()
        assert metadata.st_ino != 0, 'unavailable identity'
        return metadata.st_dev, metadata.st_ino

    def capture(self, role: str, path: Path) -> None:
        assert role in ('stage', 'backup'), 'unknown transaction role'
        assert role not in self.identities, f'{role} already captured'
        assert self.parent is None or path.parent == self.parent, 'different parent'
        try:
            identity = self._identity(path)
        except OSError as error:
            raise AssertionError(f'cannot inspect captured {role}') from error
        assert identity not in self.identities.values(), 'transaction identities alias'
        self.parent = path.parent
        self.identities[role] = identity

    def assert_committed(self, output: Path) -> None:
        assert 'stage' in self.identities, 'stage was not captured'
        assert output.parent == self.parent, 'different parent'
        try:
            output_identity = self._identity(output)
        except OSError as error:
            raise AssertionError('cannot inspect output') from error
        assert output_identity == self.identities['stage'], 'output identity changed'
        owned = set(self.identities.values())
        try:
            entries = list(output.parent.iterdir())
        except OSError as error:
            raise AssertionError('cannot inspect transaction parent') from error
        assert output in entries, 'cannot inspect output in transaction parent'
        for entry in entries:
            try:
                identity = self._identity(entry)
            except FileNotFoundError as error:
                if entry == output:
                    raise AssertionError('cannot inspect output') from error
                continue
            except OSError as error:
                raise AssertionError('cannot inspect transaction parent entry') from error
            if entry == output:
                assert identity == self.identities['stage'], 'output identity changed'
            else:
                assert identity not in owned, f'owned transaction file remains: {entry.name}'
