# Contributing

Contributions are welcome when they preserve the scientific contracts and stable compatibility boundary of the package.

## Required for a public API change

- explicit input and output semantics;
- deterministic defaults or explicit random seed;
- provenance for transformations;
- informative errors/warnings;
- unit and edge-case tests;
- synthetic-truth tests when feasible;
- API docs;
- when-to-use / when-not-to-use guidance;
- a runnable CI-sized example; and
- an explicit stability-status decision for any new public name.

## Scientific rules

Do not silently impute missing gaze, convert missingness to zero, change units, normalize time, smooth, register, rotate/scale trajectories, or choose a model/component count for the user.

A compatibility fix must not silently change an estimand, uncertainty definition, resampling unit, denominator/exposure contract, or failure/status interpretation.

## Local validation

```bash
python -m pip install -e ".[dev,docs]"
python -m pytest --cov=eyetrajectoriespy
python -m ruff check src tests
python -m compileall -q src
python scripts/validate_docs_contracts.py
mkdocs build --strict
```

## Stable 1.x API compatibility

`1.0.0` is the stable compatibility baseline. Before proposing a new public API, first identify which canonical workflow it belongs to, whether an existing stable/advanced/diagnostic API already represents the scientific object, and why another public name is necessary.

Do not rename or remove an established stable public API merely for stylistic consistency. Follow the [API stability policy](reference/api-stability.md), including the documented deprecation window and exceptional scientific-correctness rule.

The expected versioning posture is:

- **1.0.x** — compatible fixes, documentation, portability, validation and performance work;
- **1.x** — additive capabilities or deliberately governed compatible extensions;
- **2.0** — intentional breaking stable API/scientific-contract changes after explicit deprecation, except when an exceptional correction is required to prevent demonstrably wrong scientific results.

New methodology should be justified by a demonstrated scientific gap rather than the desire to create another milestone.

## Pull-request quality gate

Changes intended for `main` should go through a pull request and pass the applicable cross-platform tests, package build, documentation build, examples, optional-backend qualifications and scientific validation workflows.

The repository's current release/governance posture is documented in the [release-readiness page](release-readiness.md). Ordinary pushes and merges are non-publishing; public publication is separately armed only after exact-version qualification and an exact protected-main matrix.

A technically possible repository action should not be interpreted as project policy when it bypasses that reviewed evidence chain.
