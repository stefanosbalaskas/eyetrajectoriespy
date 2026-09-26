# Capability status and roadmap

eyetrajectoriespy is intentionally an **eye-tracking functional-analysis layer**, not a reimplementation of every general FDA estimator.

This page distinguishes implemented scientific contracts from optional interoperability and future work.

## Implemented in the core

| Capability | Status | Primary API |
|---|---|---|
| Common-grid functional gaze objects | implemented | `TrajectorySet` |
| Native curve-specific time grids | implemented | `IrregularTrajectorySet` |
| Sparse univariate covariance FPCA + PACE scores | implemented (optional FDApy backend) | `fit_sparse_fpca_fdapy()` |
| Simultaneous functional mean band | implemented | `multiplier_functional_mean_band()` |
| Function-on-scalar regression | implemented; observed-grid OLS with explicit design and HC1 standard errors | `fit_function_on_scalar_regression()` |
| Function-on-scalar simultaneous coefficient bands | implemented; fixed-design wild bootstrap with coefficient/family scope | `function_on_scalar_simultaneous_bands()` |
| Generalized function-on-scalar regression | implemented; Bernoulli/logit and Poisson/log marginal GEE with participant clusters, explicit B-spline coefficient functions, robust sandwich covariance, participant bootstrap simultaneous bands, optional explicit strictly-positive Poisson exposure, and no automatic working-correlation selection | `fit_generalized_function_on_scalar_regression()` / `generalized_function_on_scalar_simultaneous_bands()` |
| Generalized FoSR fixed-profile prediction | implemented; fixed marginal profiles, extrapolation audit, explicit Poisson rate versus expected-count prediction, participant-bootstrap simultaneous bands, one predeclared probability/rate/count contrast scale, and no automatic target/contrast selection | `generalized_function_on_scalar_predict()` / `generalized_function_on_scalar_prediction_bands()` |
| Functional mixed-effects regression | implemented; one Gaussian response dimension, B-spline fixed effects, participant functional random intercept, optional one guarded participant random functional slope, joint MixedLM fit | `fit_functional_mixed_effects_regression()` |
| Functional mixed-effects simultaneous coefficient bands | implemented; whole-participant case bootstrap, fixed-covariance GLS coefficient refits, coefficient/family observed-grid maxima | `bootstrap_functional_mixed_effects_coefficients()` / `functional_mixed_effects_simultaneous_bands()` |
| Full-refit participant bootstrap | implemented; unique bootstrap group IDs for duplicate participant draws, complete MixedLM refit under fixed declared specification, retained variance-component distributions | `bootstrap_functional_mixed_effects_full_refit()` |
| Participant random functional slope | implemented; one declared predictor, shared random basis size, full unstructured intercept/slope covariance, strict within-participant variation and covariance-complexity guards | `fit_functional_mixed_effects_regression(..., random_slope_predictor=...)` |
| Mixed-effects residual / within-trial dependence diagnostics | implemented; explicit trial ACF/autocovariance, empirical semivariance, exact physical-lag pair audit, participant/overall stratification, and descriptive fit-vs-fit comparison | `functional_mixed_effects_residual_diagnostics()` |
| Trial-level functional random effect | implemented; explicit nested trial identifier, one shared unstructured trial-basis covariance, profiled Gaussian marginal likelihood, separate trial BLUPs/covariance diagnostics, participant-level bootstrap propagation | `fit_functional_mixed_effects_regression(..., trial_random_effect="functional_intercept")` / `functional_trial_random_effect_frame()` |
| Explicit mixed-effects residual covariance + whitening | implemented; physical-time exponential correlation on irregular common grids, signed index-step AR(1) on verified regular grids, block-diagonal trial residual covariance, jointly estimated serial parameter, raw/whitened diagnostics and bootstrap propagation | `fit_functional_mixed_effects_regression(..., residual_correlation=...)` / `functional_mixed_effects_whitened_residuals()` |
| Mixed-effects covariance-structure sensitivity | implemented; predeclared already fitted structures, explicit reference, strict comparability, retained failures, coefficient/band/variance/residual/IC diagnostics, no ranking or automatic winner | `functional_mixed_effects_covariance_sensitivity()` / `functional_mixed_effects_variance_decomposition()` |
| Explicit irregular → common-grid projection | implemented | `resample_irregular_to_grid()` |
| Univariate FPCA | implemented | `fit_fpca()` |
| Joint multivariate FPCA | implemented | `fit_mfpca()` |
| Component reconstruction | implemented | `reconstruct_fpca()` |
| Reconstruction diagnostics | implemented | `fpca_reconstruction_curve()` |
| Held-out reconstruction component selection | implemented | `cross_validate_fpca_reconstruction()` |
| Outcome-tuned FPCA regression selection | implemented | `cross_validate_fpca_regression()` |
| Nested predictive FPCA selection evaluation | implemented | `nested_cross_validate_fpca_regression()` |
| Explicit minimum / one-SE selection rules | implemented | `select_fpca_components_cv()` |
| Bootstrap FPC stability | implemented | `bootstrap_fpca_stability()` |
| Matched pointwise FPC envelopes | implemented | `bootstrap_fpca_component_envelopes()` |
| Bootstrap-calibrated simultaneous FPC-shape bands | implemented | `bootstrap_fpca_component_bands()` |
| Bootstrap FPCA spectrum uncertainty | implemented | `bootstrap_fpca_spectrum_uncertainty()` |
| FPC score basis-resampling uncertainty | implemented | `bootstrap_fpca_score_uncertainty()` |
| Adjacent retained eigengap diagnostics | implemented | `fpca_eigenvalue_gap_table()` |
| Principal-angle FPC subspace comparison | implemented | `compare_fpca_subspaces()` |
| Bootstrap eigenspace stability | implemented | `bootstrap_fpca_subspace_stability()` |
| FPCA anomaly review | implemented | `diagnose_fpca_outliers()` |
| Split-conformal new-trajectory anomaly review | implemented | `split_conformal_fpca_anomaly()` |
| Participant/group influence | implemented | `leave_one_group_out_fpca_influence()` |
| Landmark registration | implemented | `register_to_landmarks()` |
| Phase-function FPCA | implemented | `fit_phase_fpca()` |
| Registered vs unregistered sensitivity | implemented | `compare_registered_unregistered_fpca()` |
| Two-level participant/trial FPCA | implemented | `fit_multilevel_fpca()` |
| Compositional AOI FPCA | implemented | `fit_compositional_fpca()` |
| Functional distances | implemented | `functional_l2_distance()` |
| Discrete Fréchet trajectory distance | implemented; monotone order-preserving coupling, no elapsed-time correspondence | `discrete_frechet_distance()` / `pairwise_discrete_frechet_distances()` |
| Dynamic time warping trajectory distance | implemented; backward-compatible symmetric1 raw cost plus explicit normalizable symmetric2/N+M option and Sakoe-Chiba sample-index band | `dynamic_time_warping_distance()` / `pairwise_dynamic_time_warping_distances()` |
| Trajectory-distance sensitivity | implemented; native-scale L2/Fréchet/DTW matrices, descriptive rank/neighbor agreement, cutoff-tie diagnostics, no automatic winner | `trajectory_distance_sensitivity()` |
| FPCA-score clustering | implemented | `cluster_fpca_scores()` |
| Score-based scalar-on-function regression | implemented | `fit_scalar_on_function_regression()` |
| Paired-bootstrap Gaussian FPCR uncertainty | implemented | `bootstrap_fpca_regression_uncertainty()` |
| Observed-grid simultaneous Gaussian FPCR slope bands | implemented | `fpca_regression_slope_simultaneous_band()` |
| Gaussian FPCR future-outcome prediction intervals | implemented | `fpca_regression_future_prediction_interval()` |
| Heteroscedastic Gaussian FPCR centered-projection intervals | implemented | `wild_bootstrap_fpca_projection()` |
| Familywise simultaneous fixed-target FPCR wild-bootstrap intervals | implemented | `fpca_wild_bootstrap_projection_simultaneous_interval()` |
| Fixed-family FPCR wild-bootstrap hypothesis tests | implemented | `fpca_wild_bootstrap_projection_family_test()` |
| Finite-bootstrap Monte Carlo precision diagnostics | implemented | `fpca_wild_bootstrap_family_test_monte_carlo_diagnostics()` |
| Stabilized-volatility wild-bootstrap h selection | implemented | `scan_wild_bootstrap_fpca_truncations()` / `select_fpca_wild_bootstrap_truncation()` |
| Derived speed/acceleration/distance/path functions | implemented | kinematic helpers |
| Continuous planar trajectory geometry | implemented; wrapped heading, signed curvature, turning rate, explicit tortuosity | `heading_function()` / `signed_curvature_function()` / `turning_rate_function()` / `trajectory_tortuosity()` |
| Delay-coordinate state reconstruction | implemented | `delay_embed_trajectory()` |
| AMI / false-nearest-neighbor diagnostics | implemented, diagnostic-only | `embedding_delay_diagnostics()` / `embedding_dimension_diagnostics()` |
| Sparse recurrence / RQA | implemented | `recurrence_matrix()` / `rqa_metrics()` |
| Recurrence radius / pair-distance profile | implemented; exact declared grid, no automatic threshold selector | `recurrence_radius_profile()` |
| Population mean RQA bootstrap | implemented; curve/participant units, fixed specification, percentile intervals | `bootstrap_rqa_metric_means()` |
| Reconstructed-state RQA parameter sensitivity | implemented; descriptive multiverse, no automatic selector | `rqa_parameter_sensitivity()` |
| Windowed and cross recurrence | implemented | `windowed_rqa()` / `cross_recurrence_matrix()` |
| Synchronized joint recurrence / JRQA | implemented; exact common grid, shared Theiler, independently declared component thresholds, sparse logical intersection | `joint_recurrence_matrix()` / `joint_rqa_metrics()` |
| Sparse recurrence-network topology | implemented; degree, clustering, transitivity, components, no automatic threshold/community/dimension selection | `recurrence_network()` |
| RQA-derived functional trajectories | implemented; descriptive functional bridge | `windowed_rqa_trajectory_set()` |
| Functional RQA window/step sensitivity | implemented; descriptive, no automatic selector | `windowed_rqa_sensitivity()` |
| Functional RQA mean band | implemented; complete curve/participant functions are inference units | `windowed_rqa_functional_mean_band()` |
| Rosenstein local divergence / LLE | implemented with explicit fit interval | `local_divergence_curve()` / `estimate_largest_lyapunov_rosenstein()` |
| Kantz neighborhood divergence / LLE | implemented; fixed radius, explicit minimum neighbors, no adaptive radius expansion | `kantz_divergence_curve()` / `estimate_largest_lyapunov_kantz()` |
| Kantz-LLE parameter sensitivity | implemented; descriptive Cartesian multiverse, no radius/fit optimization | `kantz_parameter_sensitivity()` |
| Rosenstein-LLE parameter sensitivity | implemented; descriptive multiverse, no chaos-probability interpretation | `lyapunov_parameter_sensitivity()` |
| IAAFT surrogate nonlinearity test | implemented | `surrogate_nonlinearity_test()` |
| Multivariate IAAFT surrogate generation/testing | implemented; explicit phase reference, exact marginals, retained power/cross-spectrum errors | `generate_multivariate_iaaft_surrogates()` / `multivariate_surrogate_nonlinearity_test()` |
| Discrete transfer entropy | experimental; integer-coded states, explicit histories/lag, explicit circular-shift null, no causal claim | `discrete_transfer_entropy()` / `transfer_entropy_circular_shift_test()` |
| Transfer-entropy specification sensitivity | implemented; full declared history/lag Cartesian grid, support diagnostics, optional identical circular-shift null, no automatic winner | `transfer_entropy_parameter_sensitivity()` |
| Conditional transfer entropy | implemented; one explicit conditioning process, explicit histories/lags, source-only circular-shift null, support diagnostics, no causal claim | `conditional_transfer_entropy()` / `conditional_transfer_entropy_circular_shift_test()` |
| Empirical Poincare return-map stability | experimental | `poincare_crossings()` / `fit_local_return_map()` / `return_map_stability()` |

## Documentation and mathematical contracts

Versions 0.21–0.32 treat documentation and mathematical metadata as tested package surfaces:

- the repository-level `MATHEMATICAL_CONTRACTS.md` renders the core equations directly on GitHub;
- the site mathematical reference maps those equations to the exact public APIs and scope boundaries;
- a deterministic SVG gallery is generated from seeded synthetic data and the real plotting functions;
- documentation CI regenerates gallery assets and validates navigation, mathematical API mappings, MathJax wiring, and documented public exports before the strict MkDocs build;
- the Material-for-MkDocs line is intentionally constrained to compatible 9.x releases with MkDocs <2 for this tranche.
- version 0.22 adds a public machine-readable mathematical-contract registry plus deterministic GitHub/site function → equation indexes;
- the same tranche adds a rendered workflow atlas and expands the deterministic SVG gallery to eight figures;
- CI checks that generated equation indexes still match the package registry before the strict site build.

A future documentation-platform migration can be evaluated independently of the scientific API. No site-framework migration is allowed to alter numerical or scientific contracts.

## Optional specialist interoperability

| Capability | Backend | Package role |
|---|---|---|
| B-spline/Fourier basis representation | scikit-fda | preserve eye-tracking provenance while delegating basis mathematics |
| Functional boxplot screening | scikit-fda | optional sensitivity/review diagnostic |
| Magnitude-shape outlier screening | scikit-fda | optional sensitivity/review diagnostic |
| Sparse covariance UFPCA + PACE scores | FDApy | preserve native irregular grids while delegating sparse estimation |
| Elastic SRVF trajectory alignment | fdasrsf | specialist phase/amplitude backend |

Optional backends are never imported until the corresponding feature is requested.

## Not silently approximated

The following are **not** replaced with convenient but scientifically weaker substitutes:

### Multilevel FPCA versus likelihood-based functional mixed-effects regression

The multilevel FPCA implementation provides a transparent participant/trial functional decomposition followed by FPCA. It remains a decomposition rather than a likelihood/Bayesian mixed-effects regression model. Separately, the package now includes a likelihood-based Gaussian functional mixed-effects regression layer with participant functional random effects.

### Confirmatory functional outlier tests

Review flags are descriptive diagnostics. The package does not turn them into automatic inferential exclusions.

### Full downstream uncertainty propagation beyond Gaussian FPCR

`bootstrap_fpca_regression_uncertainty()` now refits the common-grid Gaussian FPCR pipeline under paired resampling and propagates basis/regression sampling variability into the reconstructed slope and fitted conditional means.

Still not provided are full uncertainty procedures that jointly include target measurement error, latent-curve uncertainty, preprocessing uncertainty, data-driven component-selection uncertainty, sparse PACE score uncertainty, coverage-optimal automatic wild-bootstrap truncation tuning, heteroscedastic future-outcome prediction, generic arbitrary offsets, denominator/exposure measurement-error models, non-independence generalized working correlations, generalized functional random effects, uncertainty in declared prediction-profile values, or future-response prediction for generalized functional outcomes. Versions 0.51-0.54 provide the guarded marginal Bernoulli/grouped-binomial/Poisson GEE line and fixed-profile marginal inference.

## Research/development candidates

Future tranches may evaluate:

- generalized functional-response extensions only when they answer a distinct validated scientific need beyond the closed 0.51–0.54 Bernoulli/grouped-binomial/Poisson contract;
- richer sparse/irregular functional inference and external validation workflows;
- richer multilevel functional mixed-effects backends only where they answer a distinct scientific need rather than adding another covariance knob;
- explicit system-identification models for gaze dynamics;
- model-based continuation / Floquet analysis only after a validated dynamical-system contract exists.

Classical `floquet_multipliers(gaze)`, monodromy matrices from raw observations, and `detect_bifurcation(gaze)` remain intentionally **not** implemented in 0.31.

A candidate enters the public API only when it can preserve the package rules: explicit estimand, deterministic behavior or seed, provenance, failure diagnostics, synthetic truth tests, documentation, and runnable examples.

## Development status

The current development line is **0.56.0.dev0**. The package remains pre-release while scientific contracts, optional-backend validation, documentation, and cross-platform qualification continue to mature.


### 0.47 residual / within-trial dependence diagnostics

Version **0.47** implements the diagnostic tranche that follows the 0.46
full-refit bootstrap. It reports conditional-residual autocovariance,
autocorrelation, and empirical semivariance by trial over an explicitly declared
maximum index lag; retains physical-lag mean/minimum/maximum separation on the
observed common grid; exposes exact residual-pair contributions on demand; and
provides participant/overall stratification plus descriptive fit-vs-fit
comparisons.

The diagnostic contract is deliberately non-selective. It does not automatically
choose AR(1), a trial-level functional random effect, or another covariance
structure, and it does not treat residual-diagnostic differences as a model
selection test.

### 0.48 trial-level functional random effects

Version **0.48** adds one explicitly declared nested trial functional random
intercept,

```text
participant -> trial -> time
```

with a shared unstructured covariance over analyst-declared trial B-spline
coefficients. The participant covariance remains separate. The nested model is
fitted by a profiled Gaussian marginal likelihood; the historical
`statsmodels.MixedLM` path is unchanged when no trial random effect is
requested.

The 0.48 contract requires an explicit trial identifier, unique trial IDs within
participant, at least two observed trials per participant, a declared trial
basis size, and a minimum trial-count > free trial-covariance-parameter guard.
That count rule is a **minimum complexity guard, not evidence that the trial
covariance is adequately estimated**; eigenvalue, condition-number, boundary,
and bootstrap diagnostics remain essential. The result retains participant and
trial BLUPs separately and keeps whole participants as the bootstrap resampling
unit so all nested trials travel with the participant.

### 0.49 explicit residual covariance and whitening

Version **0.49** adds analyst-declared within-trial residual covariance to the
profiled Gaussian mixed-effects likelihood. Continuous-time exponential
correlation uses actual physical-time separation and is valid on irregular
common grids; signed AR(1) uses index-step lag and is accepted only on a
verified regular grid. The serial parameter is estimated jointly, residual
covariance remains block diagonal by trial, and optimizer-boundary diagnostics
are retained.

The 0.47 residual diagnostics now support `residual_scale="whitened"`.
Raw residual correlation is expected under a correlated-error model; the
whitened ACF/variogram is the relevant diagnostic for remaining serial
structure. Both fixed-covariance and full-refit participant bootstraps propagate
the declared residual covariance without changing its family.

The package explicitly documents possible competition between a long-range
serial process and a smooth trial functional random effect. Large estimated
range, trial-covariance ill-conditioning, or covariance shifts are diagnostics,
not automatic model-selection rules.

### 0.50 covariance-structure sensitivity

Version **0.50** closes the planned Gaussian covariance-engineering sequence.
It compares already fitted, predeclared covariance structures against one
analyst-declared reference under a strict comparability contract. Successful
fits must use the same observations, fixed design/basis, participant mapping,
time grid, response dimension, and ML/REML mode; matching trial IDs/bases are
also required where both fits contain trial functional effects.

The result retains failed declared structures rather than conditioning the
report on converged models only. It reports reference-based fixed coefficient
function differences, supremum and functional-L2 changes, paired simultaneous
band-width ratios when compatible bands are supplied, separate participant
intercept/slope/cross-covariance and trial/residual variance functions, raw and
whitened residual dependence, covariance diagnostics, and auditable
log-likelihood/AIC/BIC calculations.

Information criteria are descriptive and models are never sorted or labelled
as preferred. No naive likelihood-ratio p-values are produced. The central
scientific target is robustness of the substantive fixed-effect conclusions
and covariance attribution across defensible structures.

### 0.51 marginal generalized function-on-scalar regression

Version **0.51** starts a new scientific line rather than reopening Gaussian
covariance engineering. It models repeated Bernoulli or Poisson functional
responses with scalar predictors using population-averaged GEE,

```text
g(E[Y_ij(t) | x_ij]) = x_ij^T beta(t)
```

with analyst-declared clamped B-spline coefficient functions. Participants are
the independent clusters, trial-varying predictors are retained, working
independence is fixed, and robust sandwich covariance is used. The participant
count must exceed the expanded coefficient-parameter count as a minimum
structural guard, not an adequacy theorem.

Whole-participant case bootstrap refits preserve the family/link/basis/working
correlation contract and calibrate observed-grid simultaneous coefficient bands
on the link scale. Duplicate sampled participant occurrences receive distinct
bootstrap group identities; failed replicates are not silently dropped or
redrawn.

The estimand is explicitly marginal/population averaged. Version 0.51 does not
pretend that these coefficients are conditional generalized functional random
effects.

### 0.52 fixed-profile marginal prediction and contrasts

Version **0.52** turns the 0.51 marginal coefficient functions into fixed-profile
marginal response functions without changing the fitted GEE estimand.

For every analyst-declared scalar profile (x_r), it retains the linear
predictor and inverse-link marginal mean, robust delta-method pointwise
uncertainty, observed scalar-predictor range diagnostics, and an explicit
extrapolation flag. Profiles remain fixed scientific targets and are never
resampled or selected automatically.

The existing whole-participant coefficient bootstrap is projected through every
profile using the exact same participant draws. Simultaneous prediction bands
are calibrated on the linear-predictor scale and transformed through the
strictly monotone inverse link, so Bernoulli probability bands remain valid
probabilities and Poisson expected-count bands remain positive without
clipping. Scope can be one profile at a time or the complete predeclared
profile family.

Version 0.52 also supports one predeclared response-scale mean difference using
paired profile projections from the same bootstrap draw. It does not search
across profile pairs or claim multiple-contrast family adjustment. Bernoulli
difference intervals that cross the logical [-1, 1] range are flagged and
retained rather than silently clipped.

These are marginal mean-function intervals, not predictive intervals for future
stochastic Bernoulli/count trajectories, and the simultaneous claim remains on
the observed grid.

### 0.53 explicit Poisson exposure and rate estimand

Version **0.53** adds an explicit exposure-based Poisson rate contract without
changing the marginal GEE interpretation. For \(E_{ij}(t)>0\),

\[
\log \mu_{ij}(t)
=
\log E_{ij}(t)+\mathbf x_{ij}^{\top}\boldsymbol\beta(t),
\]

so the fitted coefficient predictor is a log rate and

\[
\lambda_{ij}(t)=\mu_{ij}(t)/E_{ij}(t)
\]

is retained separately from the expected count. Exposure is supplied explicitly
as a curve-by-time array or as one value per curve that is deliberately
expanded and recorded in provenance. Zero, negative, missing, or non-finite
exposure is rejected. Exposure is never inferred from grid spacing, trial
duration, sample counts, or metadata, and no generic arbitrary-offset API is
introduced.

The whole-participant bootstrap carries exposure with the response/design
bundle under the same sampled participant identity. Exposure is treated as
observed and fixed; its measurement uncertainty is not modeled. The exposure
audit reports minimum/maximum values, within-curve ranges, temporal and
between-curve variation, units, and the global exposure ratio.

For fixed-profile prediction, rate functions require no target exposure.
Expected-count prediction from an exposure-adjusted fit requires an explicit
strictly-positive target exposure and fails rather than silently setting
\(E=1\). One predeclared Poisson contrast scale may be requested:
rate difference, rate ratio, or expected-count difference. Rate-ratio
simultaneous bands are calibrated on the log-rate-ratio scale and exponentiated.

### 0.54 explicit grouped-binomial denominators

Version **0.54** closes the planned generalized observation-family gap with an
explicit grouped-binomial success/denominator contract. The observed functional
response is an integer success-count function \(S_{ij}(t)\), accompanied by a
strictly positive integer denominator \(N_{ij}(t)\) satisfying

\[
0 \le S_{ij}(t) \le N_{ij}(t).
\]

The marginal model is

\[
S_{ij}(t)\sim\operatorname{Binomial}\{N_{ij}(t),p_{ij}(t)\},
\qquad
\operatorname{logit}p_{ij}(t)
=
\mathbf x_{ij}^{\top}\boldsymbol\beta(t).
\]

The public contract accepts integer successes plus an explicit denominator. It
does not accept arbitrary proportions as sufficient grouped-binomial input, so
a numerical value such as 0.67 cannot silently stand for either 2/3 or
670/1000. Internally, the validated successes are converted to proportions and
the denominators are supplied to the GEE backend as observation weights.

The backend pathway is validated directly against a row-expanded Bernoulli GEE
reference under the same participant clustering and working-independence
contract, including agreement of the robust sandwich covariance. Denominators
travel with the complete source-participant response/design bundle in every
bootstrap refit and are treated as observed/fixed rather than resampled or
perturbed independently.

Fixed-profile inference remains on the marginal success-probability scale.
Target denominators are neither required nor inferred because the probability
estimand is denominator-independent. The result retains original successes,
denominators, observed proportions, and denominator-specific fitted expected
successes for the observed data.

### 0.55 canonical workflows and API stabilization

Version **0.55** begins the stabilization line with essentially zero new
statistical methodology.

It establishes five canonical routes:

1. continuous gaze exploration + FPCA;
2. experimental functional regression;
3. repeated-trial functional mixed effects;
4. generalized binary/count functional responses;
5. nonlinear/recurrence trajectory analysis.

The routes are declared in `CANONICAL_WORKFLOWS.json`, linked to dedicated
end-to-end documentation, and tested so canonical/advanced/diagnostic/
experimental references cannot silently drift away from the public API.

The README is deliberately shortened around four questions: what scientific
problem the package solves, which canonical route applies, what assumptions
that route makes, and where the full advanced API lives. The previous exhaustive
capability inventory remains available in the documentation instead of serving
as the primary onboarding surface.

0.55 also introduces an API hierarchy and deprecation policy. Existing public
statistical functions are not mass-renamed or removed. New APIs should follow
the established `fit_*`, `bootstrap_*`, `plot_*`, `*_frame`,
`*_reporting_text`, `random_state`, `confidence_level`,
participant/trial terminology and `*Result` conventions where applicable.
Historical exceptions remain compatible until an individually documented
deprecation path exists.

The release-readiness checklist records repository governance as a scientific
quality gate. At the start of 0.55, GitHub reports `main` as unprotected and
no repository ruleset targets it. Required PR/status-check protection is
therefore explicitly marked as unresolved release-readiness work rather than
silently assumed.

The independent-reference validation ledger is also formalized. The 0.54
grouped-binomial row-expanded Bernoulli comparison is its first qualified
entry and serves as the template for later validation cases.

### 0.56 independent-reference validation and performance qualification

Version **0.56** keeps the 0.55 stabilization operating model and adds no new
statistical method. It formalizes two auditable ledgers.

The independent-reference ledger classifies every selected validation as one
of **analytical truth**, **independent implementation equivalence**, or
**simulation recovery**. Qualified cases cover FPCA, Gaussian functional mixed
effects, Poisson exposure GEE, grouped-binomial GEE, discrete Fréchet, DTW,
RQA, and discrete transfer entropy. The evidence type remains visible because
a seeded recovery simulation is not equivalent to an exact truth or an
independently represented fit.

A separate numerical-tolerance policy prevents `rtol`/`atol` values from
becoming ad hoc. Exact counts and deterministic geometry use tight/exact
contracts; FPCA comparisons use sign/subspace invariants; optimizer-backed
comparisons require matching estimands/specifications and explicit
case-specific tolerances; simulation and Monte Carlo validation use
finite-sample or Monte Carlo reasoning rather than machine precision.

The performance ledger records a single-package reference envelope rather than
a marketing benchmark. Six expensive routes are measured separately using
fresh processes and at least three repetitions, retaining runtime
median/IQR/range, peak process RSS, workload scale, hardware/software versions,
and commit/run identifiers. No claim of superiority over another package is
made and no speed threshold is used to weaken scientific computation.

### Planned stabilization sequence after 0.56

**0.57 — reproducibility, serialization and release hardening**

- environment/software-version capture;
- representative portable scientific-result schemas and round-trip provenance
  tests rather than promises of permanent backend-object pickle compatibility;
- error-message/failure-mode consistency;
- realistic end-to-end examples for all five canonical workflows;
- branch-protection/ruleset closure and release-candidate checklist review.

Only after 0.57 should the project assess a 0.9-style release-candidate phase.
New statistical estimators remain outside the default stabilization sequence.

