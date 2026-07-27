# Contributing

Contributions must preserve the public Core boundary and remain useful across
institutions.

## Before you contribute

- Use synthetic institutional schemas, values, and examples only.
- Submit only content that you are entitled to license for Apache-2.0 use.
- Do not include a private Adapter, credentials, institutional data, or a
  login-gated document.
- Add or update a failing test before changing behavior, then make it pass.
- If `SKILL.md` changes, review the associated Evals, UI metadata, and
  references for consistency.

## Before opening a pull request

Run the complete validation set:

```bash
python -m pytest -q
python scripts/validate_skill.py
python scripts/check_public_boundary.py
python scripts/package_skill.py --check-reproducible
```

The boundary scan is required before every pull request. Explain any change to
the public/private boundary in the pull request description.
