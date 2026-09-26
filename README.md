# eyetrajectoriespy

**Functional and continuous trajectory analysis for eye-tracking data in Python.**

`eyetrajectoriespy` treats gaze as a function of trial time rather than immediately reducing it to fixation counts, dwell summaries, or symbolic scanpaths. It supports continuous planar paths

```text
G_i(t) = [x_i(t), y_i(t)]^T
```

derived univariate functions, compositional AOI-probability trajectories, repeated-trial multilevel decompositions, explicit registration, and optional elastic phase–amplitude analysis.

> **Status:** early alpha (`0.56.0.dev0`). The scientific contracts and core workflows are tested; methodological review and backend validation remain active.

## What scientific problem does this solve?

`eyetrajectoriespy` is for analyses where the **trajectory itself is a
scientific object**. It keeps temporal structure visible instead of immediately
collapsing gaze into scalar summaries, while making repeated-measures hierarchy,
uncertainty and analytical provenance explicit.

The central design rule is that consequential choices stay visible: no silent
interpolation, missing-to-zero conversion, smoothing, registration, time or
coordinate normalization, family/model selection, denominator inference or
exposure inference.

## Which workflow do I need?

| Scientific question | Start here |
|---|---|
| What are the dominant modes of continuous gaze variation? | [Continuous gaze exploration + FPCA](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/fpca-exploration/) |
| How does an experimental predictor change a continuous functional response? | [Experimental functional regression](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/experimental-functional-regression/) |
| How do repeated participant trials affect functional inference? | [Repeated-trial functional mixed effects](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/repeated-trial-mixed-effects/) |
| How do predictors change repeated binary or count functional responses? | [Generalized binary/count responses](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/generalized-responses/) |
| Is recurrence or nonlinear temporal organization the scientific target? | [Nonlinear/recurrence analysis](https://stefanosbalaskas.github.io/eyetrajectoriespy/workflows/nonlinear-recurrence/) |

The canonical workflow index is the recommended entry point for new analyses.
It separates default routes from advanced, diagnostic and experimental
branches.

## What assumptions does the workflow make?

Every canonical route documents its observation unit, hierarchy, estimand,
uncertainty/resampling unit and major failure conditions. Before interpreting a
result, use the package's [assumptions and diagnostics](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/assumptions/)
and [limitations](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/limitations/)
alongside the workflow-specific page.

The package prefers explicit failure or review over silently manufacturing a
convenient answer.

## Where is the full advanced API?

The README is intentionally no longer the exhaustive function catalogue.

- [Capability inventory](https://stefanosbalaskas.github.io/eyetrajectoriespy/reference/capability-inventory/)
- [Public API](https://stefanosbalaskas.github.io/eyetrajectoriespy/reference/api/)
- [API stability and hierarchy](https://stefanosbalaskas.github.io/eyetrajectoriespy/reference/api-stability/)
- [Mathematical reference](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/mathematical-reference/)
- [Capability status and roadmap](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/status-roadmap/)
- [Reference validation & performance envelope](https://stefanosbalaskas.github.io/eyetrajectoriespy/validation/reference-validation-ledger/)

## Install

```bash
pip install -e .
```

Development and documentation:

```bash
pip install -e ".[dev,docs]"
```

Optional interoperability:

```bash
pip install -e ".[fda]"       # scikit-fda
pip install -e ".[sparse]"    # FDApy sparse/PACE FPCA; Python 3.11–3.12
pip install -e ".[elastic]"   # fdasrsf
```

The core package remains Python 3.11–3.13. The current FDApy 1.0.3 sparse backend is qualified separately on Python 3.11–3.12 because FDApy pins NumPy <2.0, while NumPy 1.26.x does not support Python 3.13.

## Quick start

```python
from eyetrajectoriespy import fit_mfpca, simulate_planar_trajectories, summarise_fpca

gaze = simulate_planar_trajectories(
    n_participants=20,
    trials_per_participant=6,
    random_state=7,
)

fit = fit_mfpca(
    gaze,
    n_components=0.95,
    scaling="dimension_sd",
)

print(summarise_fpca(fit))
```

## Documentation

The repository-level [mathematical contracts](MATHEMATICAL_CONTRACTS.md), generated [function → equation index](FUNCTION_EQUATION_INDEX.md), and [workflow atlas](WORKFLOW_ATLAS.md) render directly on GitHub. The site expands them with assumptions, API mappings, worked examples, and a [Visual gallery](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/visual-gallery/).

The methods site is configured for GitHub Pages:

**https://stefanosbalaskas.github.io/eyetrajectoriespy/**

Use the site for the five canonical workflows, advanced method guides, worked
examples, assumptions/limitations, validation ledger, implementation-matched
mathematical reference, API documentation and reproducible SVG plot gallery.

## Scope boundary

`eyetrajectoriespy` starts once gaze has a scientifically interpretable time
and coordinate representation. Event detection, general gaze QC, survival
analysis, AOI perturbation robustness and symbolic sequence models belong
upstream or in specialist packages.

The generalized observation-family line is intentionally closed at Bernoulli /
grouped-binomial logit and Poisson expected-count/rate GEE. Negative binomial,
zero-inflated, hurdle and Tweedie families are not automatic next features.
Classical Floquet/monodromy and bifurcation analysis remain outside the raw-gaze
API without an explicitly identified dynamical model.

Version 0.55 began the stabilization line; version 0.56 adds evidence-typed
independent/reference validation, an explicit numerical-tolerance policy, and
a repeated runtime/peak-memory reference envelope. Scientific product
qualification now takes priority over estimator count. See the
[release-readiness checklist](https://stefanosbalaskas.github.io/eyetrajectoriespy/release-readiness/).

## Validation

Current local/CI qualification status and the exact pending re-check list are maintained in [VALIDATION.md](VALIDATION.md).

```bash
python -m pytest --cov=eyetrajectoriespy
python -m compileall -q src
python scripts/generate_function_equation_index.py --check
python scripts/generate_docs_gallery.py
python scripts/validate_docs_contracts.py
mkdocs build --strict
```

## License

MIT © 2026 Stefanos Balaskas.
