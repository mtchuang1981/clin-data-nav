"""Run the installable Skill's offline evidence-ledger checker."""

from __future__ import annotations

from pathlib import Path
import sys


SKILL_SCRIPTS = Path(__file__).resolve().parents[1] / "skills/clin-nav/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from check_evidence_ledger import main


if __name__ == "__main__":
    main()
