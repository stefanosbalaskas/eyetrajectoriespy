# Bayesian functional analysis — B5–B10 experimental programme

!!! warning "Not in published eyetrajectoriespy 1.1.0"
    The experimental Bayesian layer lives only on [draft PR #237](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/237), stacked on [draft PR #235](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/235). Production release remains disarmed.

The [historical B4 feasibility decision](../articles/bayesian-feasibility-boundary.md) justified further native Bayesian investigation, but did **not** select a Bayesian architecture as replacement for native covariance/PACE. The GPL `bayesFPCA` code remains an external benchmark, not a dependency or a source-code port.

| Stage | Available experimental API | What is **not** implemented or qualified |
|---|---|---|
| B5 evidence infrastructure | `BayesianFunctionalDraws`, `bayesian_credible_band()`, `bayesian_functional_probability()`, prior/posterior predictive checks, `bayesian_diagnostics_frame()`, `bayesian_calibration_study()`, predictive comparison, portable export | No claim of validated posterior coverage, inference-algorithm correctness, or model adequacy |
| B6 sparse Bayesian FPCA | `fit_bayesian_sparse_score_baseline()` | Fixed supplied population mean, eigenfunctions, eigenvalues and noise. **Not** learned Bayesian FPCA, no population-parameter posterior |
| B7 Bayesian x/y multivariate FPCA | Fixed-population shared-score conjugate benchmark via `fit_bayesian_planar_score_baseline()` | Paired and asynchronous observations accepted **conditionally on known functions**; no learned joint Bayesian MFPCA |
| B8 functional regression | `fit_bayesian_function_on_scalar()` independent Gaussian spline posterior | Observation noise SD fixed, no serial covariance, participant random effect or repeated-measures model |
| B9 prediction and groups | `compare_bayesian_functional_groups()` and `predict_bayesian_trajectory()` experimental | Jointly paired posterior draws required for group contrasts; partial completion uses **fixed known population basis** only; no calibrated prediction or group test |
| B10 AOI, registration, observation-process, changepoints | Design only | No fitted probabilistic estimator |

## Scientific definitions and limitations

**B6.** A future sparse Bayesian model must learn population mean, a joint eigenfunction basis, score and observation covariance, along with their uncertainty. The currently implemented B6 baseline instead **conditions on known fixed population functions** and calculates a Gaussian score posterior per subject. It explicitly evaluates those supplied basis functions at actual irregular observation times; it does not resample the observed data or estimate eigenfunctions. Sign/rotation ambiguity, near-tied eigenspaces and full population uncertainty remain open.

**B8.** The provisional function-on-scalar model expands each time-varying coefficient in a cubic B-spline basis and applies a declared zero-mean Gaussian coefficient prior. With analyst-fixed independent Gaussian observation-noise SD, the coefficient posterior is conjugate. It cannot silently treat repeated observations from the same participant as independent; those are rejected. The model can provide draw-based coefficient credible intervals but not scientifically calibrated coverage under misspecified noise or unmodelled autocorrelation.

**Pointwise versus joint posterior bands.** `bayesian_credible_band()` produces equal-tailed pointwise intervals or posterior content for a **finite sampled grid** using a maximum standardized-deviation reference across all times and dimensions. Neither construction implies repeated-sampling 95% confidence coverage or simultaneous validity between observed grid points.

**Posterior probability versus hypothesis testing.** `bayesian_functional_probability()` computes probabilities for predeclared posterior events such as an entire channel exceeding a meaningful threshold; it is not a frequentist p-value or Bayes factor.

**Algorithm diagnostics.** Optional ArviZ summarizes R-hat, bulk/tail ESS, Monte Carlo error and divergences when available. Convergence diagnostics are computational evidence, not evidence of valid likelihoods or priors.

**Calibration and predictive evidence.** Rank-based SBC requires *actual prior-generated truth*, likelihood simulation, and posterior refits across replicates. The B5 helper records ranks and uncertainties but cannot independently verify that the supplied draws satisfy these assumptions. Its held-out Gaussian pointwise log scores require participant/unit disjointness; they are not full joint longitudinal density without modelling the residual covariance.

**Portable evidence.** Posterior values export to a non-executable NumPy NPZ file plus a JSON manifest with explicit priors, diagnostics, provenance, SHA256 and unqualified-status marker.

## Dependencies and research phases

The package root and native FPCA estimators are unchanged. The `bayesian` extra installs ArviZ diagnostics; `bayesian-pymc` additionally installs optional PyMC for future sampler-based models. None is required for standard users, and the current B8 conjugate fitter does not claim to have run MCMC.

B6 learned-eigensystem modelling, B7 **learned-population** paired/asynchronous planar inference, B8 participant/trial hierarchical regression, B9 **learned-population calibrated** partial prediction and B10 AOI/change-point/registration/observation models need independent scientific and engineering gates.

[Bayesian synthetic figures](bayesian-gallery.md) · [Historical B4 evidence](../validation/bayesian-fpca-b2-b3.md) · [Research evidence matrix](research-evidence-matrix.md)

## Exact-model B5 simulation-based calibration pilot

The research CI executes `scripts/run_bayesian_conjugate_sbc_pilot.py`, drawing score truth or spline coefficients from each *implemented* conjugate model prior, constructing observations from its known Gaussian likelihood, then independently refitting each posterior. This creates rank histograms, observed 90% interval inclusion and exact binomial uncertainty for two **restricted baselines** (B6 fixed population and B8 known noise). The default small pilot of 30 replicates per baseline is a pipeline check, not an adequate SBC study; it does not validate learned Bayesian eigenfunctions, participant covariance, asynchronous noise, posterior MCMC, model misspecification or population-level inferential calibration. Every fit failure is retained as its own record.
