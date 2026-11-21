"""Test-only launcher and metadata reader for summary subprocess assertions."""

import json
from pathlib import Path
import sys

from summary_file_ownership import SummaryFileOwnership


def read_observation(path: Path, output: Path, *, prepared: bool) -> SummaryFileOwnership:
    with path.open("rb") as stream:
        payload = stream.read(1025)
    assert len(payload) <= 1024, "oversized transaction observation"
    data = json.loads(payload)
    assert type(data) is dict and set(data) == {"started", "identities"}
    assert type(data["started"]) is int and data["started"] == int(prepared), (
        "unexpected transaction construction count"
    )
    identities = data["identities"]
    assert type(identities) is dict
    assert set(identities) == ({"stage", "backup"} if prepared else set()), (
        "unexpected captured transaction roles"
    )
    observation = SummaryFileOwnership()
    observation.parent = output.parent
    for role, identity in identities.items():
        assert type(identity) is list and len(identity) == 2
        device, inode = identity
        assert type(device) is int and device >= 0 and type(inode) is int and inode > 0
        observation.identities[role] = (device, inode)
    assert len(set(observation.identities.values())) == len(identities)
    return observation


def main() -> int:
    sidecar, mode, *arguments = sys.argv[1:]
    assert mode in {"observe", "retain-backup"}
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from scripts import evaluate_simulation_benchmark as evaluator

    transaction_class = evaluator._SummaryTransaction
    original_init = transaction_class.__init__
    original_prepare = transaction_class.prepare
    original_delete = transaction_class._delete_owner
    started = 0
    observation = SummaryFileOwnership()
    retained = None

    def observe_init(transaction, *args):
        nonlocal started
        started += 1
        original_init(transaction, *args)

    def observe_prepare(transaction, payload):
        original_prepare(transaction, payload)
        observation.capture("stage", transaction.parent_path / transaction.stage_name)
        if transaction.backup_name is not None:
            observation.capture("backup", transaction.parent_path / transaction.backup_name)

    def retain_backup(transaction, owner, name):
        nonlocal retained
        if owner == transaction.backup_owner:
            assert retained is None
            retained = transaction.parent_path / name
            return
        original_delete(transaction, owner, name)

    transaction_class.__init__ = observe_init
    transaction_class.prepare = observe_prepare
    if mode == "retain-backup":
        transaction_class._delete_owner = retain_backup
    status = evaluator.main(arguments)
    if mode == "retain-backup":
        assert status == 0 and retained is not None
        retained.rename(retained.with_name("synthetic-retained-backup.bin"))
    with Path(sidecar).open("x", encoding="utf-8") as stream:
        json.dump({"started": started, "identities": observation.identities}, stream)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
