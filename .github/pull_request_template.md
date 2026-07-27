## Public Core checklist

- [ ] This change contains no institutional data or login-gated documents.
- [ ] If this changes `SKILL.md`, I reviewed the related Evals, UI metadata,
      and references.
- [ ] Any institutional schema or values added are synthetic only.
- [ ] I ran all four commands: `python -m pytest -q`,
      `python scripts/validate_skill.py`,
      `python scripts/check_public_boundary.py`, and
      `python scripts/package_skill.py --check-reproducible`.
