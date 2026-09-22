# Contributing

Contributions are welcome when they preserve the scientific contracts of the package.

## Required for a public API change

- explicit input and output semantics;
- deterministic defaults or explicit random seed;
- provenance for transformations;
- informative errors/warnings;
- unit and edge-case tests;
- synthetic-truth tests when feasible;
- API docs;
- when-to-use / when-not-to-use guidance;
- a runnable CI-sized example.

## Scientific rules

Do not silently impute missing gaze, convert missingness to zero, change units, normalize time, smooth, register, rotate/scale trajectories, or choose a model/component count for the user.

## Local validation

```bash
python -m pip install -e ".[dev,docs]"
python -m pytest --cov=eyetrajectoriespy
python -m ruff check src tests
python -m compileall -q src
mkdocs build --strict
```

## Methodological evidence rules

For a new methodological claim or evidence-sensitive public API:

- prefer primary papers, authoritative publisher records, PubMed/PMC, or another scholarly index over blogs, Wikipedia, or tertiary summaries;
- record what the source directly supports and what it does **not** support;
- distinguish direct behavioral-gaze evidence from eye/pupil signal evidence and from general methodological precedent;
- never infer novelty, nonexistence, or absence of prior software from a failed search;
- keep an unverified candidate citation out of ordinary guides/references until it is independently verified;
- when a generated evidence registry exists for the method family, update the registry and regenerate its derived pages rather than editing generated pages by hand.

For the nonlinear-dynamics layer, run:

```bash
python scripts/generate_nonlinear_evidence_audit.py --check
python scripts/validate_nonlinear_evidence.py
```

