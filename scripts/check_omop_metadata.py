"""Run the installable Skill's offline OMOP metadata checker."""

from __future__ import annotations

from pathlib import Path
import sys


SKILL_SCRIPTS = Path(__file__).resolve().parents[1] / "skills/clin-nav/scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))

from check_omop_metadata import main


if __name__ == "__main__":
    main()
