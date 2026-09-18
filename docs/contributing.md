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
