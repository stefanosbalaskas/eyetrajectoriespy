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
## Stabilization and API compatibility

Version 0.55 prioritizes canonical workflows and compatibility over namespace
redesign. Before proposing a new public API, first identify which canonical
workflow it belongs to and why an existing advanced/diagnostic API is
insufficient.

Do not rename or remove an established public API merely for stylistic
consistency. Follow the [API stability policy](reference/api-stability.md),
including the documented deprecation window.

## Pull-request quality gate

Changes intended for `main` should go through a pull request and pass the
cross-platform tests, package build, documentation build, examples and optional
backend qualifications. The target repository ruleset is documented in the
[release-readiness checklist](release-readiness.md).

At the start of 0.55, that GitHub ruleset is not yet enforced, so contributors
must not interpret a technically possible direct push as project policy.

