# eyetrajectoriespy

[![PyPI version](https://img.shields.io/pypi/v/eyetrajectoriespy.svg)](https://pypi.org/project/eyetrajectoriespy/)
[![GitHub Release](https://img.shields.io/github/v/release/stefanosbalaskas/eyetrajectoriespy)](https://github.com/stefanosbalaskas/eyetrajectoriespy/releases)
[![Python](https://img.shields.io/pypi/pyversions/eyetrajectoriespy.svg)](https://pypi.org/project/eyetrajectoriespy/)
[![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://stefanosbalaskas.github.io/eyetrajectoriespy/)

**Functional and continuous trajectory analysis for eye-tracking data in Python.**

`eyetrajectoriespy` treats gaze as a function of trial time rather than immediately reducing it to fixation counts, dwell summaries, or symbolic scanpaths. It supports continuous planar paths

```text
G_i(t) = [x_i(t), y_i(t)]^T
```

derived univariate functions, compositional AOI-probability trajectories, repeated-trial multilevel decompositions, explicit registration, and optional elastic phase–amplitude analysis.

> **Current stable release:** `0.11.0` was published on 29 September 2026 from exact protected-main commit `2616675ad2dfc095bf17a442c1d350ba88fd030a`. Production release workflow #13 completed successfully, including GitHub Release creation, production PyPI Trusted Publishing, digital attestations, and a fresh `eyetrajectoriespy==0.11.0` production-PyPI installation smoke test.
>
> **Current development line:** `0.12.0.dev0` is the unreleased post-0.11 source line. It is not the PyPI stable release and publication remains disarmed while the sparse multivariate planar FPCA tranche is integrated and requalified.
>
> **Scientific promotion boundary:** final `0.11.0` promotes the publicly qualified `0.11.0rc1` simulation/recovery laboratory without adding an estimator, numerical method, generalized family, API expansion, hidden analytical default, or post-0.11 research feature. Published `0.11.0rc1` remains an immutable prerelease record.
>
> **RC observation evidence:** before final promotion, the exact production-PyPI `0.11.0rc1` artifact was independently exercised outside the source checkout on Python 3.11–3.13. Exact protected-main observation commit `a37214653c2f72839e356d603c4f87a514f01056` passed deterministic simulation replay, recovery qualification, threshold-free stress retention, mixed-effects and registration recovery, portable export/load, reporting, and plotting.

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

Current stable release:

```bash
pip install eyetrajectoriespy==0.11.0
# or: pip install eyetrajectoriespy
```

The immutable qualified release candidate remains available for reproducibility:

```bash
pip install --pre eyetrajectoriespy==0.11.0rc1
```

Final `0.11.0` was qualified independently under its own exact package identity; the published rc1 artifacts were not relabeled.

Development checkout:

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
pip install -e ".[sparse]"    # transitional FDApy sparse/PACE compatibility backend
pip install -e ".[elastic]"   # fdasrsf
```

The core package remains Python 3.11–3.13. The native `fit_sparse_fpca()` path is backend-independent. The optional FDApy 1.0.3 compatibility/reference backend is qualified separately on Python 3.11–3.12 because FDApy pins NumPy <2.0, while NumPy 1.26.x does not support Python 3.13.

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

Version 0.55 began the stabilization line; version 0.56 added
evidence-typed independent/reference validation, an explicit numerical-tolerance
policy, and a repeated runtime/peak-memory reference envelope. Version 0.57 adds
portable scientific-result snapshots, explicit environment capture, five
qualified canonical end-to-end examples, and coordinated GitHub/PyPI release
machinery. Version 0.9.0 is the first stable pre-1.0 release. The 0.10 line adds the native sparse/irregular FPCA + PACE tranche; rc2 corrects the diagonal-difference measurement-noise estimator, and final 0.10.0 promotes that corrected candidate after exact-version requalification. The 0.11 line adds the known-truth simulation/recovery laboratory. Published `0.11.0rc1` completed production-installed observation, and final `0.11.0` was independently requalified and published without scientific/API expansion. Scientific product qualification remains more important than estimator count. See the
[release-readiness checklist](https://stefanosbalaskas.github.io/eyetrajectoriespy/release-readiness/).

- [Portable scientific results](https://stefanosbalaskas.github.io/eyetrajectoriespy/reproducibility/portable-results/)
- [Reproducibility bundle checklist](https://stefanosbalaskas.github.io/eyetrajectoriespy/reproducibility/checklist/)
- [Release process](https://stefanosbalaskas.github.io/eyetrajectoriespy/release-process/)

## Validation

Current qualification, release, and public-artifact evidence are maintained in [VALIDATION.md](VALIDATION.md).

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
