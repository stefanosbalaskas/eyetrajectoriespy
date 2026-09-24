# eyetrajectoriespy

**Functional and continuous trajectory analysis for eye-tracking data in Python.**

`eyetrajectoriespy` treats gaze as a function of trial time rather than immediately reducing it to fixation counts, dwell summaries, or symbolic scanpaths. It supports continuous planar paths

```text
G_i(t) = [x_i(t), y_i(t)]^T
```

derived univariate functions, compositional AOI-probability trajectories, repeated-trial multilevel decompositions, explicit registration, and optional elastic phase–amplitude analysis.

> **Status:** early alpha (`0.38.0.dev0`). The scientific contracts and core workflows are tested; methodological review and backend validation remain active.

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
- explicit minimum-RMSE and one-standard-error reconstruction component-count selection;
- outcome-tuned FPCA regression selection with Gaussian or binomial held-out losses and nested/grouped CV;
- bootstrap FPC stability with curve- or participant-level resampling and matched component functions;
- matched, sign-aligned pointwise descriptive envelopes for FPC shape uncertainty;
- bootstrap-calibrated observed-grid simultaneous FPC-shape bands with component-wise or familywise scope;
- adjacent eigengap diagnostics and principal-angle FPCA subspace stability for near-tied components;
- matched-bootstrap uncertainty for eigenvalues, explained-variance ratios, and cumulative explained variance;
- basis-resampling uncertainty for FPC scores of fixed training or compatible external target trajectories;
- paired-bootstrap uncertainty for Gaussian scalar-on-function FPCR slopes and fixed-target conditional means;
- observed-grid studentized simultaneous bands for reconstructed Gaussian FPCR slopes;
- marginal future-outcome prediction intervals for Gaussian FPCR fixed targets under centered empirical residual resampling;
- fixed-regressor studentized wild-bootstrap intervals for centered Gaussian FPCR target projections under heteroscedastic response errors;
- familywise max-|t| post-calibration across predeclared fixed FPCR target families using the exact stored wild-bootstrap roots;
- fixed-family two-sided wild-bootstrap hypothesis tests with target-wise, single-step maxT-adjusted, and complete-family global bootstrap p-values;
- finite-bootstrap Monte Carlo precision diagnostics with exceedance counts, MCSEs, exact binomial intervals, and decision-stability flags without changing the underlying test decisions;
- stabilized-volatility scans and target-specific selection of the wild-bootstrap inference truncation `h` with shared multipliers and analyst-declared stability thresholds;
- simultaneous functional-mean bands with curve- or equal-weight participant-level inference;
- function-on-scalar regression for experimental predictors with observed-grid coefficient functions, HC1 pointwise standard errors, fixed-design wild-bootstrap coefficient replicates, and coefficient-wise or familywise simultaneous bands;
- fail-closed repeated-trial handling for function-on-scalar regression: participant aggregation is allowed only for participant-constant predictors;
- joint Gaussian functional mixed-effects regression for trial-varying predictors, using explicit B-spline fixed coefficient functions and a participant functional random intercept fitted in one stacked MixedLM rather than separate pointwise models;
- FPCA reconstruction/robust score-space review diagnostics and leave-one-group-out influence analysis;
- split-conformal marginal anomaly p-values for new common-grid trajectories using explicit proper-training and calibration partitions;
- participant → trial → time multilevel FPCA;
- compositional FPCA for AOI probability functions with simplex-preserving reconstruction;
- landmark registration with retained warping functions, phase FPCA, and registered-versus-unregistered sensitivity analysis;
- optional elastic SRVF curve analysis through `fdasrsf`;
- optional B-spline/Fourier basis projection and functional outlier screening through `scikit-fda` with retained provenance;
- continuous speed, acceleration, landmark-distance, and path-length functions;
- continuous wrapped heading, signed curvature, turning-rate functions, and explicit path-length/displacement tortuosity with low-speed undefinedness retained;
- integrated functional L2 distances;
- discrete Fréchet trajectory distance and pairwise matrices with auditable monotone couplings and no elapsed-time matching;
- dynamic time warping (DTW) with backward-compatible symmetric1 raw cost, explicit normalizable symmetric2 weighting, optional N+M normalization, auditable monotone index paths, and declared Sakoe-Chiba sample-index bands;
- trajectory-distance sensitivity across declared L2, discrete Fréchet, and DTW contracts, retaining native-scale matrices, pair-distance rank agreement, nearest-neighbor overlap, and cutoff-tie diagnostics without selecting a preferred metric;
- deterministic FPCA-score clustering;
- scalar-on-function regression through FPCA scores;
- explicit delay-coordinate reconstruction with AMI/autocorrelation and false-nearest-neighbor diagnostics;
- sparse continuous-state recurrence matrices, RQA, windowed RQA, and cross-recurrence analysis;
- exact recurrence-radius profiles exposing RR(radius) and pair-distance shell mass over analyst-declared thresholds without dense distance matrices or automatic radius selection;
- percentile bootstrap uncertainty for population-average fixed-specification RQA metrics with curve- or equal-weight participant-level resampling and no trial pseudo-replication;
- first-class RQA-derived functional trajectories for FDA of time-varying RR/DET/LAM and related metrics, with explicit overlap/dependence provenance;
- declared window/step sensitivity grids for functional RQA with source-sample reuse diagnostics, exact-shared-center profile comparisons, and no automatic tuning selection;
- simultaneous functional-RQA mean bands that resample complete curve- or equal-weight participant-level functions rather than overlapping window rows;
- declared reconstructed-state RQA parameter multiverses over embedding, delay, threshold, Theiler, and line-length choices with no automatic selector;
- Rosenstein-style local divergence / largest-Lyapunov estimation with analyst-declared fit intervals;
- named Kantz fixed-radius neighborhood divergence / largest-Lyapunov estimation with explicit radius, minimum-neighbor, Theiler, and fit contracts;
- declared Rosenstein-LLE sensitivity over reconstruction, Theiler, and fit-interval choices with descriptive sign/magnitude stability summaries;
- seeded IAAFT surrogate nonlinearity tests using plus-one Monte Carlo p-values;
- cross-spectrum-aware multivariate IAAFT surrogates for planar/multichannel gaze, with exact per-channel marginal rank preservation, analyst-declared phase reference, retained power/cross-spectrum mismatch diagnostics, and multichannel surrogate nonlinearity testing;
- experimental empirical Poincare return maps and local cycle-to-cycle contraction/expansion diagnostics;
- reproducible synthetic datasets and manuscript-oriented reporting helpers;
- implementation-matched LaTeX mathematical contracts rendered in both GitHub and the methods site;
- deterministic documentation plot gallery regenerated from the real package plotting APIs in CI;
- public function → LaTeX mathematical-contract registry with deterministic generated repository/site indexes;
- GitHub- and website-rendered workflow atlases connecting representation, inference, functions, equations, examples, and figures.

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
| Continuous planar geometry | `heading(t)`, signed curvature, turning rate, tortuosity | `heading_function()` / `signed_curvature_function()` / `turning_rate_function()` / `trajectory_tortuosity()` |
| Ordered trajectory similarity | discrete Fréchet bottleneck distance | `discrete_frechet_distance()` / `pairwise_discrete_frechet_distances()` |
| Elastic sequence-index similarity | explicit symmetric1 raw or symmetric2/N+M-normalized DTW alignment cost | `dynamic_time_warping_distance()` / `pairwise_dynamic_time_warping_distances()` |
| Similarity robustness across defensible distance contracts | descriptive pair-rank and local-neighbor agreement across declared L2 / Fréchet / DTW specifications | `trajectory_distance_sensitivity()` |
| Native irregular gaze | curve-specific time grids | `from_irregular_long_dataframe_native()` |
| Genuinely sparse univariate gaze | covariance UFPCA + PACE scores | `fit_sparse_fpca_fdapy()` |
| One derived continuous outcome | `X(t)` | `fit_fpca()` |
| Repeated participant trials | `G_ij(t)` | `fit_multilevel_fpca()` |
| AOI probabilities | simplex-valued `P(t)` | `fit_compositional_fpca()` |
| Similar path, different traversal timing | amplitude + phase | `register_to_landmarks()` / `fit_phase_fpca()` / `fit_elastic_fpca()` |
| Reconstruction component-count selection | held-out trajectory reconstruction | `cross_validate_fpca_reconstruction()` |
| Predictive component-count selection | held-out scalar outcome loss / nested CV | `cross_validate_fpca_regression()` |
| Component robustness | bootstrap-matched eigenfunctions | `bootstrap_fpca_stability()` |
| Component shape uncertainty | matched bootstrap envelopes | `bootstrap_fpca_component_envelopes()` |
| Simultaneous FPC-shape uncertainty | matched studentized bootstrap maximum | `bootstrap_fpca_component_bands()` |
| Near-tied component blocks | principal-angle eigenspace stability | `bootstrap_fpca_subspace_stability()` |
| FPCA spectrum uncertainty | matched studentized bootstrap | `bootstrap_fpca_spectrum_uncertainty()` |
| FPC score basis uncertainty | matched/sign-aligned basis bootstrap | `bootstrap_fpca_score_uncertainty()` |
| Gaussian FPCR regression uncertainty | paired full-pipeline bootstrap | `bootstrap_fpca_regression_uncertainty()` |
| Gaussian FPCR simultaneous slope band | studentized maximum over paired-bootstrap slopes | `fpca_regression_slope_simultaneous_band()` |
| Gaussian FPCR future-outcome prediction | paired-bootstrap means + independent centered residual draws | `fpca_regression_future_prediction_interval()` |
| Heteroscedastic Gaussian FPCR projection inference | fixed-regressor studentized wild bootstrap | `wild_bootstrap_fpca_projection()` |
| Simultaneous heteroscedastic Gaussian FPCR target inference | familywise max-|t| post-calibration over fixed targets | `fpca_wild_bootstrap_projection_simultaneous_interval()` |
| Fixed-family heteroscedastic Gaussian FPCR hypothesis testing | target-wise + single-step maxT-adjusted bootstrap tail probabilities | `fpca_wild_bootstrap_projection_family_test()` |
| Wild-bootstrap inference truncation selection | stabilized interval center/width across consecutive `h` values | `scan_wild_bootstrap_fpca_truncations()` / `select_fpca_wild_bootstrap_truncation()` |
| Mean trajectory uncertainty | observed-grid Gaussian multiplier band | `multiplier_functional_mean_band()` |
| Functional anomaly review | reconstruction + score-space diagnostics | `diagnose_fpca_outliers()` |
| New-trajectory conformal anomaly review | split-conformal FPCA nonconformity | `split_conformal_fpca_anomaly()` |
| Group influence | leave-one-group-out matched FPCs | `leave_one_group_out_fpca_influence()` |
| Scalar outcome predicted by gaze | FPCA-score approximation | `fit_scalar_on_function_regression()` |
| Functional gaze predicted by experimental variables | observed-grid function-on-scalar OLS + wild-bootstrap simultaneous bands | `fit_function_on_scalar_regression()` / `function_on_scalar_simultaneous_bands()` |
| Repeated-trial functional response with trial-varying predictors | joint B-spline functional mixed-effects regression with participant functional random intercept | `fit_functional_mixed_effects_regression()` |
| Planar/multichannel surrogate null | multivariate IAAFT with retained inter-channel phase differences and spectral diagnostics | `generate_multivariate_iaaft_surrogates()` / `multivariate_surrogate_nonlinearity_test()` |
| Recurrent gaze-state structure | sparse recurrence / RQA | `recurrence_matrix()` / `rqa_metrics()` |
| Recurrence-threshold diagnostics | exact RR(radius) curve and pair-distance shell profile | `recurrence_radius_profile()` |
| RQA robustness across analysis choices | declared reconstruction/threshold/Theiler/line-length multiverse | `rqa_parameter_sensitivity()` |
| Population uncertainty for RQA summaries | percentile bootstrap over independent curves or equal-weight participant averages | `bootstrap_rqa_metric_means()` |
| Time-varying recurrent dynamics | sliding full-window RQA | `windowed_rqa()` |
| RQA dynamics as functional outcomes | window-center RQA metric trajectories with retained overlap/radius provenance | `windowed_rqa_trajectory_set()` |
| Functional RQA parameter sensitivity | declared window/step grid with overlap/reuse and exact-center profile diagnostics | `windowed_rqa_sensitivity()` |
| Functional RQA mean uncertainty | whole-function curve/participant multiplier band | `windowed_rqa_functional_mean_band()` |
| Reconstructed nonlinear state | delay coordinates with explicit (m, τ) | `delay_embed_trajectory()` |
| Local state-space divergence | Rosenstein nearest-neighbor divergence | `local_divergence_curve()` / `estimate_largest_lyapunov_rosenstein()` |
| Neighborhood-based maximal Lyapunov estimate | Kantz fixed-radius local-neighborhood divergence | `kantz_divergence_curve()` / `estimate_largest_lyapunov_kantz()` |
| Kantz LLE robustness multiverse | Declared radius/min-neighbor/reconstruction/Theiler/fit sensitivity, no optimizer | `kantz_parameter_sensitivity()` / `plot_kantz_sensitivity()` |
| LLE robustness across analysis choices | declared reconstruction/Theiler/fit-interval multiverse | `lyapunov_parameter_sensitivity()` |
| Nonlinearity vs linear-stochastic null | IAAFT surrogate test | `surrogate_nonlinearity_test()` |
| Repeated approximate cycles | empirical Poincare return map (experimental) | `poincare_crossings()` / `fit_local_return_map()` |

## Documentation

The repository-level [mathematical contracts](MATHEMATICAL_CONTRACTS.md), generated [function → equation index](FUNCTION_EQUATION_INDEX.md), and [workflow atlas](WORKFLOW_ATLAS.md) render directly on GitHub. The site expands them with assumptions, API mappings, worked examples, and a [Visual gallery](https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/visual-gallery/).

The methods site is configured for GitHub Pages:

**https://stefanosbalaskas.github.io/eyetrajectoriespy/**

It includes a tutorial gallery, representation selection, nonlinear state-space reconstruction, recurrence/RQA, local-divergence and surrogate workflows, experimental return-map stability, native irregular and sparse PACE workflows, FPCA/MFPCA interpretation, leakage-aware component selection, matched-bootstrap FPC uncertainty, simultaneous FPC-shape bands, spectrum uncertainty, score basis-resampling uncertainty, Gaussian FPCR bootstrap uncertainty, simultaneous slope bands, future-outcome prediction intervals, heteroscedastic wild-bootstrap projection inference, simultaneous fixed-target wild-bootstrap intervals, eigengap/subspace stability, bootstrap stability, phase analysis, registration cautions, multilevel and compositional workflows, basis/elastic interoperability, failure cases, pre-registration/reporting guidance, limitations, worked examples, and API documentation, an implementation-matched mathematical reference, and a reproducible SVG plot gallery.

## Scope boundary

`eyetrajectoriespy` starts once gaze has a scientifically interpretable time and coordinate representation. Event detection, general gaze QC, survival analysis, AOI perturbation robustness, and sequence models belong upstream or in specialist packages. Versions 0.31–0.34 add provenance-aware continuous planar geometry plus two distinct ordered-trajectory similarity contracts: discrete Fréchet bottleneck distance and cumulative dynamic time warping. Version 0.35 shifts the development line from adding more trajectory metrics toward functional inference for experimental predictors through function-on-scalar regression and simultaneous coefficient bands. Version 0.38 adds a descriptive robustness layer across the already-implemented distance contracts rather than adding another metric. The nonlinear/RQA layers from 0.23–0.30 remain intact. Classical Floquet/monodromy analysis and numerical bifurcation continuation remain outside the raw-gaze API because they require an explicitly identified dynamical model.

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
