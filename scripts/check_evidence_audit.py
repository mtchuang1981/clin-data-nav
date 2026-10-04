"""Run the installable Skill's offline companion-audit checker."""
from pathlib import Path
import sys

SKILL_SCRIPTS = Path(__file__).resolve().parents[1] / "skills/clin-nav/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
from check_evidence_audit import main

if __name__ == "__main__":
    raise SystemExit(main())
