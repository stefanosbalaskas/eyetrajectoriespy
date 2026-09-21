# eyetrajectoriespy

**Functional and continuous trajectory analysis for eye-tracking data in Python.**

`eyetrajectoriespy` treats gaze as a function of trial time rather than immediately reducing it to fixation counts, dwell summaries, or symbolic scanpaths. It supports continuous planar paths

```text
G_i(t) = [x_i(t), y_i(t)]^T
```

derived univariate functions, compositional AOI-probability trajectories, repeated-trial multilevel decompositions, explicit registration, and optional elastic phase–amplitude analysis.

> **Status:** early alpha (`0.7.0.dev0`). The scientific contracts and core workflows are tested; methodological review and backend validation remain active.

## Scientific design

The package deliberately avoids hidden analytical decisions:

- no silent interpolation or missing-to-zero conversion;
- no automatic smoothing;
- no automatic registration;
- no silent time normalization;
- no silent coordinate conversion;
- no silent multichannel scaling;
- provenance is carried with transformed trajectories.

Registration is especially explicit because latency can itself be psychologically meaningful.

## Main capabilities

- typed `TrajectorySet` objects with metadata, units, coordinate semantics, and provenance;
- common-grid import plus first-class native irregular trajectories with explicit overlap/union projection;
- optional FDApy covariance UFPCA with PACE conditional-expectation scores for genuinely sparse univariate trajectories;
- opt-in short-gap interpolation and smoothing;
- FPCA and joint multivariate FPCA for `[x(t), y(t)]`;
- component scores, reconstruction, variance summaries, component trajectories, and reconstruction-error diagnostics;
- leakage-aware held-out reconstruction CV with curve- or participant/group-level folds;
- explicit minimum-RMSE and one-standard-error component-count selection;
- bootstrap FPC stability with curve- or participant-level resampling and matched component functions;
- matched, sign-aligned pointwise descriptive envelopes for FPC shape uncertainty;
- adjacent eigengap diagnostics and principal-angle FPCA subspace stability for near-tied components;
- simultaneous functional-mean bands with curve- or equal-weight participant-level inference;
- FPCA reconstruction/robust score-space review diagnostics and leave-one-group-out influence analysis;
- participant → trial → time multilevel FPCA;
- compositional FPCA for AOI probability functions with simplex-preserving reconstruction;
- landmark registration with retained warping functions, phase FPCA, and registered-versus-unregistered sensitivity analysis;
- optional elastic SRVF curve analysis through `fdasrsf`;
- optional B-spline/Fourier basis projection and functional outlier screening through `scikit-fda` with retained provenance;
- continuous speed, acceleration, landmark-distance, and path-length functions;
- integrated functional L2 distances;
- deterministic FPCA-score clustering;
- scalar-on-function regression through FPCA scores;
- reproducible synthetic datasets and manuscript-oriented reporting helpers.

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

## Choose the representation before the estimator

| Scientific object | Representation | Entry point |
|---|---|---|
| Continuous gaze location | `[x(t), y(t)]` | `fit_mfpca()` |
| Native irregular gaze | curve-specific time grids | `from_irregular_long_dataframe_native()` |
| Genuinely sparse univariate gaze | covariance UFPCA + PACE scores | `fit_sparse_fpca_fdapy()` |
| Genuinely sparse univariate gaze | native irregular grid + PACE scores | `fit_sparse_fpca_fdapy()` |
| One derived continuous outcome | `X(t)` | `fit_fpca()` |
| Repeated participant trials | `G_ij(t)` | `fit_multilevel_fpca()` |
| AOI probabilities | simplex-valued `P(t)` | `fit_compositional_fpca()` |
| Similar path, different traversal timing | amplitude + phase | `register_to_landmarks()` / `fit_phase_fpca()` / `fit_elastic_fpca()` |
| Component-count selection | held-out reconstruction CV | `cross_validate_fpca_reconstruction()` |
| Component robustness | bootstrap-matched eigenfunctions | `bootstrap_fpca_stability()` |
| Component shape uncertainty | matched bootstrap envelopes | `bootstrap_fpca_component_envelopes()` |
| Near-tied component blocks | principal-angle eigenspace stability | `bootstrap_fpca_subspace_stability()` |
| Mean trajectory uncertainty | observed-grid Gaussian multiplier band | `multiplier_functional_mean_band()` |
| Functional anomaly review | reconstruction + score-space diagnostics | `diagnose_fpca_outliers()` |
| Group influence | leave-one-group-out matched FPCs | `leave_one_group_out_fpca_influence()` |
| Scalar outcome predicted by gaze | FPCA-score approximation | `fit_scalar_on_function_regression()` |

## Documentation

The methods site is configured for GitHub Pages:

**https://stefanosbalaskas.github.io/eyetrajectoriespy/**

It includes a tutorial gallery, representation selection, native irregular and sparse PACE workflows, FPCA/MFPCA interpretation, leakage-aware component selection, matched-bootstrap FPC uncertainty, eigengap/subspace stability, bootstrap stability, phase analysis, registration cautions, multilevel and compositional workflows, basis/elastic interoperability, failure cases, pre-registration/reporting guidance, limitations, worked examples, and API documentation.

## Scope boundary

`eyetrajectoriespy` starts once gaze has a scientifically interpretable time and coordinate representation. Event detection, general gaze QC, survival analysis, AOI perturbation robustness, and sequence models belong upstream or in specialist packages.

## Validation

Current local/CI qualification status and the exact pending re-check list are maintained in [VALIDATION.md](VALIDATION.md).

```bash
python -m pytest --cov=eyetrajectoriespy
python -m compileall -q src
mkdocs build --strict
```

## License

MIT © 2026 Stefanos Balaskas.
