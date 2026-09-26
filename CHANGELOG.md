# Changelog

## 0.55.0.dev0

- Begin a stabilization line with no new statistical family or estimator.
- Add `CANONICAL_WORKFLOWS.json` as a machine-readable map of five recommended scientific routes: FPCA/exploration, experimental functional regression, repeated-trial mixed effects, generalized binary/count responses, and nonlinear/recurrence analysis.
- Add dedicated end-to-end canonical workflow guides that start from the scientific question/data contract and end with uncertainty, interpretation, reporting, and explicit "do not use" boundaries.
- Add CI tests that require every canonical/advanced/diagnostic/experimental function named by the manifest to remain a public export with an existing documentation target.
- Refocus the README on four onboarding questions and move the exhaustive capability/representation inventory to the documentation.
- Add a public API hierarchy, forward naming conventions, compatibility-first deprecation policy, and a 0.55 consistency audit without mass-renaming historical APIs.
- Establish a minimum two-minor-release deprecation window before pre-1.0 public API removals unless retaining an API would be scientifically incorrect or insecure.
- Add a pre-1.0 release-readiness checklist covering repository governance, canonical workflows, independent validation, performance, reproducibility and serialization.
- Record the current repository-policy gap explicitly: `main` is unprotected and no repository ruleset is active at the start of 0.55.
- Rename the documentation CI job from generic `build` to unique `docs-build` so it can be selected unambiguously as a required status check.
- Add an independent-reference validation ledger seeded by the 0.54 grouped-binomial versus row-expanded Bernoulli GEE coefficient/covariance comparison.
- Keep the configured 90% coverage floor unchanged; stabilization prioritizes independent-reference validation quality rather than optimizing for a higher line-coverage percentage alone.
- Document the intended post-0.55 sequence: 0.56 external-reference validation + runtime/memory qualification, then 0.57 reproducibility/serialization + release hardening before assessing a 0.9-style release-candidate phase.

## 0.54.0.dev0

- Add an explicit grouped-binomial contract to `fit_generalized_function_on_scalar_regression()` through `binomial_denominator=`, with the trajectory response interpreted as integer success counts rather than arbitrary proportions.
- Require finite, strictly positive integer denominators aligned as `(n_curves, n_time)`; allow `(n_curves,)` only through explicit time expansion recorded in provenance.
- Require non-negative integer successes satisfying `0 <= successes <= denominator` everywhere and reject proportion-like fractional responses.
- Fit grouped binomial responses through statsmodels GEE using success proportions as the backend response and denominators as observation weights while preserving the package-level success-count representation.
- Retain integer successes, denominators, observed success proportions, and fitted expected-success functions separately in `GeneralizedFunctionOnScalarResult`.
- Validate the grouped-binomial backend directly against a row-expanded Bernoulli GEE reference and require agreement in both coefficient estimates and robust sandwich covariance.
- Resample denominators with the complete source-participant response/design bundle in the whole-participant bootstrap; denominators are treated as observed/fixed and denominator measurement uncertainty is not modeled.
- Keep fixed-profile prediction on the marginal success-probability scale; grouped-binomial prediction does not require or infer a target denominator.
- Preserve Bernoulli 0/1, Poisson expected-count, and Poisson exposure/rate behavior from 0.51-0.53.
- Explicitly avoid a generic proportion-input API: a value such as 0.67 is not accepted as grouped binomial unless represented by integer successes and an explicit integer denominator.
- Update mathematical contracts, generated function-to-equation indexes, methods/examples, assumptions, limitations, reporting, preregistration, roadmap, quick start, and package metadata for 0.54.
- Close the planned generalized observation-family expansion after 0.54. Negative binomial, zero inflation, hurdle, Tweedie, generalized random effects, and automatic working-correlation selection are not queued as automatic follow-ons.
- Redirect the post-0.54 roadmap toward stabilization: API consistency, canonical workflows, external-reference validation, performance benchmarks, serialization/reproducibility, error-message consistency, realistic examples, documentation hierarchy, and release readiness.

## 0.53.0.dev0

- Add an explicit Poisson `exposure` contract to `fit_generalized_function_on_scalar_regression()` without exposing a generic arbitrary-offset API.
- Require finite, strictly positive exposure values aligned as `(n_curves, n_time)`; allow `(n_curves,)` only through explicit time expansion recorded in provenance.
- Retain exposure, log exposure, marginal rate functions, rate-scale linear predictors, count-scale linear predictors, and exposure-specific expected-count functions separately.
- Preserve the no-exposure Poisson path as an expected-count model rather than retroactively relabeling its coefficients as rates.
- Add `generalized_function_on_scalar_exposure_frame()` with per-curve and global exposure range, temporal/between-curve variation, units, and maximum/minimum ratio auditing.
- Resample exposure with the complete source-participant response/design bundle in every participant-bootstrap refit while treating exposure as observed/fixed and not modeling exposure measurement uncertainty.
- Extend fixed-profile prediction with explicit `prediction_scale="rate"` and `"expected_count"`; exposure-adjusted rate predictions require no target exposure, whereas expected-count predictions require explicit strictly-positive `exposure_profiles` and never silently assume unit exposure.
- Retain fixed target exposure through all prediction-bootstrap draws without resampling or perturbing it.
- Extend the one-predeclared-contrast contract to `rate_difference`, `rate_ratio`, and `expected_count_difference` for exposure-adjusted Poisson models.
- Calibrate rate-ratio simultaneous bands on the log-rate-ratio scale and exponentiate the endpoints, preserving positivity.
- Keep Bernoulli probability prediction/contrast behavior and no-exposure Poisson expected-count behavior backward compatible.
- Document the substantive exposure assumption (E[Y\mid x,E]=E\lambda(x)): exposure must represent a defensible amount of observation time/opportunity rather than an arbitrary normalization factor.
- Explicitly record that exposure is never inferred from grid spacing, trial duration, sample counts, or metadata.
- Update the mathematical registry, generated function-to-equation indexes, method/reference pages, examples, public API/version contracts, changelog, and roadmap for the 0.53 rate estimand.
- Continue to defer grouped-binomial denominators to 0.54 pending direct backend validation; generic offsets, negative-binomial/zero-inflated families, generalized random effects, and automatic working-correlation selection remain outside 0.53.

## 0.52.0.dev0

- Add `generalized_function_on_scalar_predict()` for fixed analyst-declared scalar predictor profiles under the 0.51 marginal Bernoulli/logit or Poisson/log function-on-scalar GEE.
- Retain both link-scale linear-predictor functions and directly interpretable marginal response functions: probabilities for Bernoulli models and expected counts for Poisson models under the current no-offset contract.
- Map the retained robust GEE basis-parameter covariance to fixed-profile linear-predictor standard errors and use the inverse-link delta method for pointwise marginal-mean standard errors.
- Audit scalar-predictor support for every target profile; profiles outside any observed predictor range are retained and explicitly flagged as extrapolations rather than silently clipped or rejected.
- Add `bootstrap_generalized_function_on_scalar_predictions()`, projecting every existing whole-participant coefficient-bootstrap draw through all fixed profiles without drawing a second bootstrap sample or resampling target covariates.
- Add `generalized_function_on_scalar_prediction_bands()` with profile-specific or complete-profile-family observed-grid simultaneous calibration on the linear-predictor scale.
- Transform simultaneous linear-predictor endpoints through the strictly monotone inverse link, guaranteeing Bernoulli marginal-mean bands remain within the probability range and Poisson marginal-mean bands remain positive without clipping.
- Add `generalized_function_on_scalar_mean_difference_band()` for one predeclared paired response-scale profile difference; the same participant-bootstrap coefficient draw is propagated through both profiles so their prediction dependence is retained.
- For Bernoulli mean differences, retain rather than clip any simultaneous interval extending outside the logical [-1, 1] range and expose an explicit physical-bound diagnostic.
- Add prediction/contrast frames, plots and manuscript-oriented reporting helpers.
- Make the inferential boundary explicit: 0.52 estimates marginal mean functions, not future stochastic Bernoulli/count response trajectories; fixed target-profile uncertainty and between-grid simultaneous coverage are not propagated.
- Add tests for exact reproduction of fitted means at observed profiles, inverse-link transformation, extrapolation flags, participant-bootstrap reuse, profile/family simultaneous calibration, paired mean differences, Poisson positivity, plotting/reporting and fail-closed profile contracts.
- Continue to defer grouped-binomial denominators, Poisson exposure offsets, alternative working correlations, generalized functional random effects and multiple-contrast family adjustment.

## 0.51.0.dev0

- Add `fit_generalized_function_on_scalar_regression()` for marginal non-Gaussian functional responses with scalar predictors and repeated participant trials.
- Support explicit Bernoulli/logit and Poisson/log response families only; binary responses must be coded exactly 0/1 and Poisson responses must be non-negative integers.
- Represent each time-varying coefficient in an analyst-declared clamped B-spline basis and fit the full trial-by-time response through one stacked marginal GEE.
- Treat participants as the independent clusters while allowing predictors to vary across trials within participant.
- Fix the 0.51 working dependence contract to independence and use robust sandwich covariance; no working correlation, family, link, basis size, interaction, or model is selected automatically.
- Make the estimand explicitly population averaged / marginal rather than conditional on functional random effects.
- Add a conservative structural guard requiring the participant count to exceed the expanded coefficient-parameter count; document that this is not an adequacy theorem for sandwich covariance estimation.
- Add whole-participant case-bootstrap refits through `bootstrap_generalized_function_on_scalar_coefficients()`; duplicate sampled participant occurrences receive unique bootstrap cluster IDs and failed replicates are raised rather than silently dropped/redrawn.
- Add observed-grid link-scale simultaneous coefficient bands through `generalized_function_on_scalar_simultaneous_bands()` with coefficient or full-family scope.
- Add coefficient frames, plotting and manuscript-oriented reporting helpers.
- Preserve fitted marginal means and linear predictors separately from the link-scale coefficient functions.
- Explicitly defer aggregated binomial proportions/denominators, Poisson offsets, negative-binomial/zero-inflated families, sparse response grids, non-independence working correlations, generalized functional random effects and automatic smoothing-parameter selection.
- Add truth-known Bernoulli and Poisson validation, trial-varying predictor coverage, participant-bootstrap reproducibility/auditing, simultaneous-band tests, response-domain guards, cluster-count guards and public-API coverage.
- Advance the post-0.50 roadmap from Gaussian covariance engineering to a genuinely distinct marginal generalized functional-response capability.

## 0.50.0.dev0

- Add `FunctionalMixedEffectsCovarianceSpecification` and `functional_mixed_effects_covariance_sensitivity()` for descriptive comparison of already fitted, predeclared covariance structures against one analyst-declared reference.
- Keep model fitting and sensitivity comparison separate: 0.50 never generates covariance combinations, refits a model, ranks structures, returns a best model, or performs an automatic likelihood-ratio test.
- Enforce strict comparability across successful fits: identical source observations/order, observed response functions, fixed-effect design, fixed basis/knots, participant random basis/knots, participant mapping, time grid/unit, response dimension, spline degree, and ML/REML choice; matching trial IDs/bases are additionally required when both fits contain trial functional effects.
- Retain failed predeclared covariance structures explicitly with `status="failed"`, `converged=False`, a failure reason, and NaN numerical comparison fields rather than silently dropping them.
- Add reference-based fixed coefficient sensitivity with complete observed-grid differences, supremum absolute differences, and trapezoidal functional L2 differences.
- Add optional simultaneous-band width sensitivity using width ratios to the declared reference; supplied bands must use the same confidence/scope/bootstrap contract and identical participant bootstrap draws.
- Add `functional_mixed_effects_variance_decomposition()` and `plot_functional_variance_decomposition()`, retaining participant-intercept variance, participant-slope variance, intercept/slope cross-covariance, trial variance, and residual variance as separate functional components.
- Add side-by-side raw and whitened residual ACF/variogram summaries, global residual RMS, pair counts, maximum positive-lag whitened ACF magnitude, and summed squared whitened ACF as descriptive diagnostics rather than selection objectives.
- Add auditable likelihood/AIC/BIC fields only after comparability passes. ML information criteria use total fixed+covariance parameter count; REML uses the restricted-likelihood covariance-parameter count under an identical fixed design/basis. BIC explicitly records `n_curves × n_time` as its conventional observation-count definition.
- Report reference-based log-likelihood/AIC/BIC differences without sorting models or labeling a preferred structure.
- Exclude naive likelihood-ratio p-values because covariance components and serial parameters can lie on boundaries and many declared comparisons are not regular nested models.
- Add trial-versus-serial decomposition diagnostics through trial covariance traces, full trial variance curves, residual variance/range parameters, condition/boundary diagnostics, and raw/whitened residual structure without automatic deletion of competing covariance components.
- Add `plot_covariance_sensitivity_coefficients()`, `plot_covariance_sensitivity_band_widths()`, and `functional_mixed_effects_covariance_sensitivity_reporting_text()`.
- Add synthetic M1–M4 covariance sensitivity validation, retained failed-model behavior, information-criterion auditing, paired-bootstrap band sensitivity, comparability failures, reporting, plotting, and public-API coverage.
- Close the planned Gaussian covariance-engineering sequence at 0.50; subsequent development should prioritize distinct scientific capabilities rather than additional covariance knobs.

## 0.49.0.dev0

- Add explicit within-trial residual correlation to `fit_functional_mixed_effects_regression()` through `residual_correlation="iid"|"exponential"|"ar1"`; no covariance family is selected automatically.
- Make continuous-time exponential correlation the primary physical-time serial model: \(R_\phi(t,s)=\exp\{-|t-s|/\phi\}\), \(\phi>0\), with \(\phi\) estimated jointly and reported in the trajectory time unit.
- Add index-step AR(1), \(R_{rs}=\rho^{|r-s|}\), \(-1<\rho<1\), only for verified equally spaced common grids; negative AR(1) correlation is supported and is not represented as an exponential model.
- Keep residual covariance block diagonal by source curve/trial so serial dependence never crosses trial boundaries.
- Generalize the profiled Gaussian likelihood so participant-only serial models, participant+trial iid models, and participant+trial serial models share the same covariance engine while the historical participant-only iid `statsmodels.MixedLM` path remains backward compatible.
- Parameterize \(\phi=\exp(\eta_\phi)\) and \(\rho=\tanh(\eta_\rho)\), retain natural/transformed optimizer bounds in provenance, and flag fitted residual-correlation parameters at or near numerical bounds.
- Add an explicit practical exponential-independence diagnostic when the fitted within-trial correlation matrix is effectively identity on the observed grid (maximum absolute off-diagonal correlation <= 0.05), because the likelihood can become flat toward the iid limit before the numerical phi bound is reached.
- Retain the residual-correlation family, estimated parameter/name/unit, within-trial correlation matrix, eigenvalues, condition number, grid-regularity diagnostics, raw residual functions, and within-trial whitened residual functions.
- Add `functional_mixed_effects_whitened_residuals()` and extend `functional_mixed_effects_residual_diagnostics(..., residual_scale="raw"|"whitened")`; raw residual correlation is expected under a correlated-error model, whereas whitened residual diagnostics assess remaining structure after the declared residual covariance.
- Extend the fixed-covariance participant bootstrap to condition on the fitted residual correlation and extend the full-refit participant bootstrap to re-estimate \(\phi\) or \(\rho\), participant covariance, optional trial covariance, and residual variance in every replicate.
- Extend `functional_mixed_effects_variance_bootstrap_frame()` with residual-correlation parameter, condition-number, and boundary diagnostics.
- Add truth-known validation for irregular-grid exponential correlation, positive and negative AR(1), AR(1) irregular-grid rejection, trial-boundary blocking, fixed-effect recovery, whitening, combined participant random slope + trial functional random effect + residual correlation, iid-boundary behavior, and both bootstrap contracts.
- Document the covariance-decomposition warning that a long-range residual process can compete with a smooth trial functional random effect; diagnose large \(\hat\phi\), ill-conditioned \(\Psi_{\mathrm{trial}}\), or major covariance shifts rather than treating them as automatic model-selection evidence.
- Keep covariance-structure selection out of 0.49. Version 0.50 remains the planned descriptive sensitivity layer for predeclared covariance structures.


## 0.48.0.dev0

- Add an explicit nested trial-level functional random intercept to `fit_functional_mixed_effects_regression()` through `trial_column`, `trial_random_effect="functional_intercept"`, and analyst-declared `trial_random_basis_size`.
- Preserve the historical `statsmodels.MixedLM` backend unchanged when no trial functional random effect is requested; 0.48 uses a separate profiled Gaussian marginal-likelihood backend only for the nested participant→trial→time covariance model.
- Estimate one shared unstructured trial-basis covariance `Psi_trial` across trials rather than one covariance per trial or an independent scalar variance-component approximation.
- Use the participant-block marginal covariance `V_i = Z_i Psi_participant Z_i' + sum_j W_ij Psi_trial W_ij' + sigma^2 I`, with Cholesky-parameterized participant/trial covariance matrices and GLS-profiled fixed effects.
- Require an explicit trial identifier, uniqueness of trial IDs within participant, at least two observed trials per participant, fixed declared trial basis size, and a minimum trial-count > free trial-covariance-parameter guard.
- Retain trial covariance eigenvalues, condition number, covariance-parameter count, boundary/singularity diagnostics, trial BLUP coefficients/functions, and exact curve→participant→source-trial mappings.
- Add `functional_trial_random_effect_frame()` and `plot_functional_trial_random_effects()` for direct inspection of estimated trial-specific smooth departures.
- Extend the 0.47 residual ACF/variogram workflow to the 0.48 fitted residuals so analysts can diagnose whether smooth trial-specific dependence was actually removed.
- Extend the fixed-covariance participant bootstrap so both participant and trial covariance components are held fixed in the participant-block GLS reconstruction.
- Extend the full-refit participant bootstrap so whole participants remain the resampling unit, all nested trials travel with the sampled participant, duplicate participant draws receive distinct bootstrap participant IDs, duplicate source trials receive distinct bootstrap trial IDs, and both participant/trial covariance matrices plus residual variance are re-estimated.
- Add `functional_mixed_effects_full_refit_trial_audit_frame()` and trial covariance diagnostics to the variance-bootstrap frame.
- Add synthetic validation for fixed-effect recovery, trial-BLUP recovery, residual-dependence reduction, zero-trial-variance boundary behavior, participant/trial identifiability, fixed-covariance bootstrap propagation, and full-refit hierarchical resampling identity.
- Keep residual serial covariance out of 0.48. The next planned tranche is 0.49 explicit physical-time residual covariance, followed by 0.50 covariance-structure sensitivity/comparison.

## 0.47.0.dev0

- Add `functional_mixed_effects_residual_diagnostics()` for explicit within-trial residual autocovariance, autocorrelation, and empirical semivariance through an analyst-declared maximum index lag.
- Diagnose the conditional residual functions from the fitted likelihood-based mixed model; do not reinterpret them as marginal residuals or refit the model inside the diagnostic layer.
- Retain every trial, including exact-zero residual-variance trials; their autocorrelation is marked undefined rather than replacing it with zero or silently dropping the trial.
- Retain mean/minimum/maximum physical time separation for every index lag without assuming an equally spaced common grid or creating hidden physical-lag bins.
- Add `functional_mixed_effects_residual_pair_frame()` to expose the exact physical lag, residual pair, centered-product contribution, and semivariance contribution for any declared index lag.
- Add participant- and overall-level pair-count-weighted descriptive summaries while retaining the number of trials with defined ACF values.
- Add `compare_functional_mixed_effects_residual_diagnostics()` for before/after model sensitivity comparisons without ranking fits, selecting a covariance structure, or performing an automatic hypothesis test.
- Add residual ACF and empirical-variogram plotting plus manuscript-oriented reporting with explicit time-unit, lag, aggregation, and no-auto-selection provenance.
- Add synthetic/manual validation for exact lag calculations, physical-lag auditing, zero-variance retention, plotting/reporting, comparison invariance, and fail-closed lag validation.
- Keep structural modeling separate: 0.47 does not automatically choose AR(1), a trial-level functional random effect, or another residual covariance model. The next structural extension remains contingent on the diagnosed residual pattern.

## 0.46.0.dev0

- Add `bootstrap_functional_mixed_effects_full_refit()` as a second, explicitly distinct whole-participant bootstrap for the likelihood-based functional mixed-effects layer.
- Assign every sampled participant occurrence a unique bootstrap group identity, even when the same source participant is drawn multiple times, and retain both source and bootstrap participant IDs for every replicate/draw.
- Refit fixed coefficient functions, the complete random-effect covariance, random-intercept/slope covariance blocks, and residual variance in every bootstrap replicate under the unchanged declared model specification.
- Keep basis sizes, spline degree, common-grid knot construction, preprocessing, response dimension, predictors, random-slope structure, REML/ML choice, optimizer, and iteration limit fixed; “full refit” does not mean automatic model reselection.
- Retain complete bootstrap distributions for random-effect covariance matrices, eigenvalues, condition numbers, boundary/singularity flags, residual variance, log likelihood, convergence state, backend warnings, and slope-specific covariance diagnostics.
- Add `functional_mixed_effects_full_refit_audit_frame()` and `functional_mixed_effects_variance_bootstrap_frame()` for participant-identity and variance-component stability auditing.
- Allow `functional_mixed_effects_simultaneous_bands()` to calibrate either the original fixed-covariance bootstrap or the new full-refit bootstrap while preserving the distinction in provenance/reporting.
- Add `compare_functional_mixed_effects_bootstraps()` and `plot_functional_mixed_effects_bootstrap_comparison()` to compare coefficient/time-specific full-refit versus fixed-covariance simultaneous-band widths.
- Keep `failed_replicate_policy="raise"`; failed bootstrap fits are not silently discarded or redrawn.
- Clarify that the 0.45 participant-count rule is a minimum covariance-complexity guard, not an adequacy guarantee, and retain the stricter requirement that the random-slope predictor vary within every participant.
- Revise the roadmap so 0.47 is residual/within-trial dependence diagnostics before choosing trial-level functional random effects versus explicit serial residual covariance.

## 0.45.0.dev0

- Extend `fit_functional_mixed_effects_regression()` with exactly one explicitly declared `random_slope_predictor`; `None` preserves the existing random-functional-intercept model.
- Represent the participant random intercept and the one random slope with the same declared B-spline basis size q and one unstructured covariance over the stacked 2q random-basis coefficient vector.
- Make covariance dimensionality explicit: the one-slope model estimates `(2q)(2q+1)/2` free random-effect covariance parameters; with the default q=4 this is 36 parameters.
- Add a conservative 0.45 guard requiring the participant count to exceed the number of free unstructured covariance parameters before a random-slope fit is attempted.
- Require the named random-slope predictor to be one of the declared fixed predictors and to vary within every participant; no automatic slope selection or intercept-only fallback is allowed.
- Retain the complete random-effect design matrix, full covariance, intercept/slope covariance blocks, eigenvalues, covariance condition number, covariance parameter count, boundary/singularity diagnostics, and exact slope-predictor provenance.
- Retain participant BLUP intercept and slope basis coefficients and reconstructed functions separately; preserve the historical `random_effect_functions` alias as the random-intercept function for backward compatibility.
- Add `functional_random_effect_frame()` and `plot_functional_random_effects()` for direct participant-level inspection of random-intercept or random-slope functions.
- Keep the 0.44 participant-cluster simultaneous-band bootstrap available with random slopes while explicitly conditioning on the fitted full intercept/slope covariance and residual variance rather than refitting variance components.
- Add demanding synthetic tests for known slope heterogeneity, correlated intercept/slope structure, zero-slope truth, within-participant identifiability failure, covariance-complexity failure, explicit-predictor validation, backward compatibility, and fixed-covariance bootstrap reuse.
- Add mathematical contracts, methodology/worked/executable examples, plotting/gallery support, and full documentation/site integration.
- Set the next inference tranche to full-refit participant bootstrap sensitivity (0.46), followed by explicit residual serial-correlation structures (0.47).

## 0.44.0.dev0

- Add `bootstrap_functional_mixed_effects_coefficients()` using whole-participant case resampling so every selected participant contributes the complete repeated-trial/time bundle.
- Re-estimate fixed B-spline coefficients in every bootstrap replicate through the participant-block GLS equations implied by the fitted mixed model while holding the reference random-effect covariance, residual variance, and declared bases fixed.
- Verify before resampling that the fixed-covariance GLS reconstruction reproduces the stored MixedLM fixed coefficients; fail rather than bootstrap under an inconsistent covariance contract.
- Fail the complete bootstrap if any resampled participant information matrix becomes rank deficient or unsolvable; no failed replicate is silently redrawn or discarded.
- Add `functional_mixed_effects_simultaneous_bands()` with coefficient-wise or full fixed-effect-family studentized supremum calibration over the observed time grid.
- Use participant-bootstrap pointwise standard deviations as the band scale and center calibration on the bootstrap mean while centering reported bands on the reference mixed-model estimate; no automatic bootstrap bias correction is applied.
- Add `FunctionalMixedEffectsBootstrapResult` and `FunctionalMixedEffectsBandResult`, optional simultaneous columns in `functional_mixed_effects_coefficient_frame()`, simultaneous-band plotting, and manuscript-oriented reporting.
- Add deterministic participant-resampling tests, coefficient/family scope tests, explicit failure contracts, mathematical metadata, a methodology guide, worked/executable example, and site/gallery integration.
- Keep the inferential boundary explicit: simultaneous coverage is over the observed grid and conditional on the fitted covariance model and declared bases; variance-component, basis-selection, preprocessing, and between-grid uncertainty are not included.
- Close the current simultaneous-inference gap before moving to participant random functional slopes / richer covariance structures.

## 0.43.0.dev0

- Add `conditional_transfer_entropy()` for empirical discrete conditional mutual information (I(X_{t-d}^{(l)};Y_t\mid Y_{t-1}^{(k)},Z_{t-c}^{(m)})) in bits.
- Require explicit target/source/conditioning history lengths and explicit source/conditioning lags in sample-index units; no automatic discretization, history/lag selection, smoothing, interpolation, support filtering, or causal interpretation is introduced.
- Retain every local conditional-TE contribution, effective sample index, original integer-coded source/target/conditioning series, exact reconstructed histories, observed target/conditioning/source+conditioning/full-joint support counts, singleton fraction, minimum/maximum/mean joint-history cell counts, and full provenance.
- Add `conditional_transfer_entropy_circular_shift_test()` using only analyst-declared nonzero circular shifts of the source while holding target and conditioning processes fixed.
- Retain the full surrogate conditional-TE distribution, surrogate mean, surrogate-centered conditional TE, plus-one upper-tail Monte Carlo p-value, attainable p-value resolution, exact shift set, shifted/fixed process metadata, and null provenance.
- Add exact validation for constant-conditioning equivalence to ordinary TE, a constructed common-driver collapse, retained direct contribution under common drive, directionality, an exact manual contingency-count example, source-shift null behavior, and sparse-history support collapse.
- Keep the interpretation boundary explicit: conditioning addresses the explicitly supplied process but does not establish causal influence or guarantee adjustment for unmeasured common drivers.
- Add result objects, local-history frame, plotting/reporting helpers, mathematical contract, methodology guide, worked/executable example, and full API/site integration.
- Deliberately stop short of conditional-TE specification sensitivity, TE networks, automatic causal discovery, and time-windowed TE; the next inferential priority returns to simultaneous inference for functional mixed-effects coefficient functions.

## 0.42.0.dev0

- Add `transfer_entropy_parameter_sensitivity()` for a full Cartesian multiverse over analyst-declared target-history, source-history, and source-lag grids.
- Retain one auditable row per specification with empirical TE, effective-transition support, observed target/joint-history counts, singleton-history fraction, and minimum/maximum/mean joint-history cell counts.
- Optionally reuse one identical analyst-declared circular-shift set for every specification and retain surrogate mean, surrogate-centered TE, plus-one upper-tail p-value, attainable p-value resolution, and shift count per row.
- Fail the complete sensitivity analysis when any declared specification is invalid; no failed row is silently removed or replaced.
- Add descriptive variation summaries only; do not rank, optimize, or automatically select histories/lags and do not reinterpret the specification table as a sampling or posterior distribution.
- Add `plot_transfer_entropy_sensitivity()`, which requires an explicit one-parameter slice and refuses hidden averaging over any other multi-valued sensitivity dimension.
- Add `TransferEntropySensitivityResult`, manuscript-oriented reporting, deterministic directional-lag tests, direct agreement tests against the 0.41 base estimator/surrogate test, fail-closed grid/plot tests, mathematical contract, method guide, worked/executable example, and site integration.
- Document Vicente et al. (2011) parameter sensitivity and Zhang et al. (2024) direct head-eye TE precedent while preserving the package's no-automatic-causal-interpretation boundary.

## 0.41.0.dev0

- Add `discrete_transfer_entropy()` as empirical plug-in conditional mutual information for analyst-supplied integer-coded state sequences, reported in bits.
- Require explicit target-history length, source-history length, and source lag in sample-index units; no automatic discretization, history selection, lag selection, smoothing, interpolation, or scaling is introduced.
- Retain local transfer-entropy contributions, exact effective sample indices, source/target state arrays, state/history support diagnostics, and provenance.
- Add `transfer_entropy_circular_shift_test()` using only analyst-declared nonzero circular source shifts with a conservative plus-one upper-tail Monte Carlo p-value.
- Retain the surrogate TE distribution, surrogate mean, surrogate-centered TE, attainable p-value resolution, complete shift set, and null-model provenance.
- Add result objects, local-history frame, null-distribution plotting, manuscript reporting helpers, deterministic reference-value and directional synthetic tests, failure-contract tests, a mathematical contract, method guide, worked/executable example, and full API/site integration.
- Keep transfer entropy explicitly experimental: positive TE or a small surrogate p-value is directed predictive-information evidence under the declared representation/null, not standalone evidence of causal influence.

## 0.40.0.dev0

- Add `recurrence_network()` for sparse undirected, unweighted graph topology induced by one declared symmetric auto-recurrence matrix.
- Retain node degree/normalized degree, local clustering, graph density, transitivity, connected-component labels and sizes, largest-component fraction, isolated-node fraction, source recurrence object, and full provenance.
- Keep graph density (all unordered node pairs) explicitly distinct from Theiler-conditioned source recurrence rate.
- Count triangles without materializing a dense adjacency or all-pairs shortest-path matrix.
- Return transitivity as undefined when no connected triples exist rather than silently replacing it with zero; use an explicit local-clustering convention of zero for degree < 2.
- Reject cross-recurrence, asymmetric adjacency, self-loops, and edges inside the declared Theiler exclusion.
- Do not tune recurrence thresholds, optimize communities, add edge weights, infer graph layouts, or automatically interpret clustering/transitivity as dynamical dimension or chaos.
- Add `RecurrenceNetworkResult`, node/global summary frames, degree plotting, reporting text, deterministic known-graph tests, mathematical contracts, methodology/worked examples, and full site integration.

## 0.39.0.dev0

- Add `joint_recurrence_matrix()` for sparse synchronized joint recurrence as the elementwise logical intersection of at least two declared auto-recurrence matrices.
- Preserve each component's own state dimension, distance metric, radius/target-RR policy, achieved recurrence rate, source provenance, and label rather than pooling subsystems into one hidden state space.
- Require identical square matrix shape, exact common time grid, and one shared Theiler exclusion; no interpolation, resampling, lag shifting, synchronization repair, threshold harmonization, or recurrence re-estimation is performed automatically.
- Define JRR over the same eligible unordered-pair denominator used by the synchronized component auto-recurrences.
- Add `joint_rqa_metrics()`, reusing the package's existing line-counting conventions on the joint matrix while retaining the regular-grid requirement for line-based RQA.
- Add `JointRecurrenceResult`, component-contract frame, sparse plotting, manuscript-oriented reporting, mathematical contracts, deterministic tests, worked/executable examples, and complete documentation/site integration.
- Keep the interpretation boundary explicit: joint recurrence measures coincident within-system recurrence and is not cross-recurrence, transfer entropy, directionality, or evidence of causal coupling.

## 0.38.0.dev0

- Add `trajectory_distance_sensitivity()` for descriptive robustness analysis across at least two explicitly declared integrated-L2, discrete-Fréchet, and/or DTW specifications.
- Retain every native-scale pairwise distance matrix and every unique curve-pair distance/rank; do not z-score, range-normalize, average, or otherwise create a hidden consensus distance.
- Quantify global pair-order agreement with descriptive Spearman rank correlation plus mean/median/maximum absolute rank differences.
- Quantify local sensitivity with per-curve top-k neighbor Jaccard overlap, exact top-k set agreement, and nearest-neighbor identity agreement.
- Use deterministic stable tie handling while explicitly flagging ties at the k/k+1 neighborhood cutoff.
- Retain raw-scale Pearson distance correlation only as a secondary descriptive diagnostic.
- Do not compute ordinary correlation p-values for dependent upper-triangle distance entries and do not identify a preferred or "best" trajectory metric.
- Add `TrajectoryDistanceSensitivityResult`, comparison/neighbor frames, a rank-agreement heatmap, manuscript-oriented reporting text, mathematical contracts, tests, docs, and executable examples.

## 0.37.0.dev0

- Add `generate_multivariate_iaaft_surrogates()` for cross-spectrum-aware multichannel surrogate generation.
- Preserve each selected channel's empirical marginal value set exactly through rank remapping while jointly targeting original per-channel Fourier amplitudes and inter-channel Fourier phase differences.
- Require an explicit `reference_dimension`; never choose the MIAAFT phase reference automatically.
- Retain per-surrogate convergence iterations, per-channel relative spectrum errors, and per-channel-pair relative complex cross-spectrum errors rather than claiming exact final spectral preservation after rank remapping.
- Add `multivariate_surrogate_nonlinearity_test()` for multichannel largest-Lyapunov testing under the identical declared embedding/divergence/fit contract for observed and surrogate trajectories.
- Use plus-one Monte Carlo p-values and fail if any requested surrogate or surrogate statistic fails under the declared contract.
- Add `MultivariateIAAFTResult`, `MultivariateSurrogateNonlinearityResult`, diagnostics-frame, plotting, and reporting helpers.
- Add deterministic marginal-preservation, spectral/cross-spectral diagnostic, reproducibility, failure-contract, plotting/reporting, and public-API tests.
- Add mathematical contracts, methodology guide, worked/executable example, evidence references, assumptions/limitations/preregistration/reporting guidance, API/object docs, roadmap/site integration, and gallery diagnostics.

## 0.36.0.dev0

- Add `fit_functional_mixed_effects_regression()` for one selected Gaussian common-grid functional response with scalar fixed predictors and a participant-specific functional random intercept.
- Fit all curve-by-time observations jointly in one `statsmodels.MixedLM`; do not approximate repeated-measures functional regression by unrelated pointwise mixed models.
- Represent fixed coefficient functions and participant random functions with explicitly sized clamped B-spline bases; no automatic basis selection or smoothing penalty is introduced.
- Allow trial-varying predictors while preserving participant clustering directly in the mixed-effects likelihood.
- Estimate an unstructured covariance across participant random-basis coefficients and retain BLUP random-effect functions, residual variance, fixed-parameter covariance, basis matrices/knots, rank diagnostics, convergence status, backend warnings, and provenance.
- Fail on non-convergence rather than interpreting an invalid fit; flag near-boundary random-effect covariance estimates.
- Add pointwise fixed-effect standard errors, coefficient tables, plotting, and reporting helpers with an explicit no-simultaneous-coverage boundary.
- Add synthetic truth/repeated-measures tests, rank/basis/participant failure contracts, executable example, methodology guide, mathematical contract, references, API/object documentation, and site integration.

## 0.35.0.dev0

- Add `fit_function_on_scalar_regression()` for observed-grid functional-response regression with an explicit scalar design matrix and one intercept.
- Return `FunctionOnScalarResult` with coefficient functions, fitted/residual functions, the exact inference-unit responses, design matrix/rank, residual degrees of freedom, HC1 pointwise sandwich standard errors, time/dimension semantics, and provenance.
- Require numeric finite predictors with no automatic dummy coding, centering, scaling, interaction construction, smoothing, basis expansion, regularization, or predictor selection.
- Support genuinely independent curve-level inference or equal-weight participant aggregation when predictors are constant within participant; trial-varying predictors fail explicitly because 0.35 is not a functional mixed-effects model.
- Add `bootstrap_function_on_scalar_coefficients()` using fixed-design whole-function wild bootstrap with Rademacher or normal multipliers and deterministic seeding.
- Add `function_on_scalar_simultaneous_bands()` with coefficient-wise or declared-family observed-grid maximum calibration.
- Add `function_on_scalar_coefficient_frame()`, `plot_function_on_scalar_coefficients()`, and `function_on_scalar_reporting_text()`.
- Add synthetic truth, reproducibility, repeated-trial guardrail, rank/alignment/failure, plotting, reporting, and public-API tests.
- Add mathematical contracts, guide, worked/executable example, references, reporting/preregistration/limitations guidance, site navigation, workflow integration, and visual documentation.

## 0.34.0.dev0

- Harden dynamic time warping with an explicit `step_pattern` contract while preserving the 0.33 `symmetric1` raw-cost default.
- Add `symmetric2` weighting, where diagonal advances contribute two local-cost units and horizontal/vertical advances contribute one.
- Add explicit `normalize=True` support only for `symmetric2`, using the path-independent `N+M` denominator; reject normalization for `symmetric1` rather than inventing a denominator.
- Extend `DynamicTimeWarpingResult` with raw and normalized distances, step pattern, normalization denominator, per-path step weights, and weighted local costs that reproduce the raw optimum.
- Propagate step-pattern and normalization choices through pairwise DTW matrices without changing existing default calls.
- Add `plot_dynamic_time_warping_alignment()` and `dynamic_time_warping_reporting_text()` for auditable diagnostics and manuscript-oriented reporting.
- Expand tests for backward compatibility, symmetric2 weighting, normalization, path-cost reconstruction, pairwise behavior, failure contracts, plotting, and reporting.
- Refresh mathematical contracts, worked examples, visual documentation, assumptions, limitations, preregistration/reporting guidance, references, API/object docs, and site integration.

## 0.33.0.dev0

- Add `dynamic_time_warping_distance()` for exact dynamic-programming DTW between complete ordered point sequences, including unequal sequence lengths.
- Add `DynamicTimeWarpingResult` with one deterministic optimal monotone path, aligned local distances, path length, mean local distance, window settings, and provenance.
- Add `pairwise_dynamic_time_warping_distances()` for complete `TrajectorySet` collections with explicit dimension selection.
- Use weighted Euclidean local costs and the symmetric diagonal/up/left recurrence; the public scalar is the unnormalized cumulative path cost rather than a silently path-length-normalized variant.
- Add an optional explicit Sakoe-Chiba `window_radius` in sample-index units and fail when the declared band cannot connect unequal-length endpoints.
- Preserve sequence order while deliberately excluding recorded timestamps from the recurrence; no interpolation, resampling, smoothing, coordinate normalization, simplification, missing-value deletion, or automatic band selection is introduced.
- Document deterministic tie handling for non-unique optimal paths and retain the boundary that DTW may align away latency/index-shift differences that are scientifically meaningful.
- Add hand-computable, shift-versus-window, symmetry, weighting, pairwise-dimension, path-monotonicity, and fail-closed input tests.
- Add mathematical contracts, method/worked/executable examples, assumptions, limitations, preregistration/reporting guidance, evidence references, API/object docs, site navigation, and examples CI.

## 0.32.0.dev0

- Add `discrete_frechet_distance()` for exact dynamic-programming discrete Fréchet distance between complete ordered point sequences, including unequal sequence lengths.
- Add `DiscreteFrechetResult` with one deterministic optimal monotone coupling, coupled local distances, dimensionality, and provenance.
- Add `pairwise_discrete_frechet_distances()` for complete `TrajectorySet` collections with explicit dimension selection.
- Preserve sequence order without backtracking while deliberately excluding elapsed-time correspondence from the recurrence.
- Add explicit optional dimension weights with no hidden normalization; no interpolation, resampling, smoothing, coordinate normalization, path simplification, or outlier removal is introduced.
- Document deterministic tie handling for non-unique optimal couplings and retain the boundary that the returned coupling is one optimum rather than a unique alignment claim.
- Add hand-computable unequal-length, symmetry, bottleneck-outlier, weighting, pairwise-dimension, coupling-monotonicity, and fail-closed input tests.
- Add mathematical contract, API docs, method/worked/executable examples, reporting/preregistration/limitations guidance, references, README/status integration, and examples CI.

## 0.31.0.dev0

- Add `heading_function()`, `signed_curvature_function()`, `turning_rate_function()`, and `trajectory_tortuosity()` for continuous planar gaze geometry.
- Resolve named planar dimensions explicitly; default `x`/`y` is used only when those names exist, and arbitrary alternate channel names must be supplied.
- Use observed-grid numerical derivatives with `numpy.gradient(..., edge_order=2)`; no smoothing, interpolation, coordinate scaling, angle unwrapping, or denominator epsilon is introduced.
- Add explicit `min_speed` and `undefined_policy` contracts for heading/curvature/turning rate; low-speed undefined samples remain NaN or fail the analysis rather than becoming zero.
- Define tortuosity as observed polyline path length divided by endpoint displacement, with explicit `min_displacement` and undefined-policy handling for closed or near-closed paths.
- Preserve sample-level undefined counts/fractions, source coordinate semantics, selected planar dimensions, units, and derivative decisions in provenance.
- Correctly scope curvature sign to the recorded coordinate-axis orientation; the package does not assume screen y increases upward.
- Add analytic straight-line, circle, low-speed, dimension-selection, closed-path, and two-point tortuosity tests.
- Add mathematical contracts, API docs, method guidance, worked/executable examples, reporting/preregistration/limitations guidance, literature context, and deterministic gallery integration.

## 0.30.0.dev0

- Add `kantz_parameter_sensitivity()` for the complete analyst-declared Cartesian grid of embedding dimension, delay, fixed radius, minimum neighbors, Theiler window, and fit interval.
- Reuse each resolved Kantz divergence curve across declared fit intervals without changing the estimator.
- Retain exponent/fit diagnostics plus initial supported-reference fraction and minimum reference/pair support inside each fitted interval.
- Fail the entire sensitivity analysis when any declared specification is invalid; no failed radius/minimum-neighbor combination is silently dropped or enlarged.
- Add `KantzParameterSensitivityResult`, `plot_kantz_sensitivity()`, and `kantz_parameter_sensitivity_reporting_text()`.
- Plotting requires an explicit one-parameter slice and refuses hidden averaging across unspecified sensitivity dimensions.
- Positive-specification fractions and support fractions remain descriptive properties of the declared grid; they are not chaos probabilities, confidence intervals, or model weights.
- Extend the mathematical contract, API reference, nonlinear-sensitivity guide/worked example/executable example, reporting/preregistration/limitations guidance, references, README/status surfaces, and tests.

## 0.29.0.dev0

- Add `kantz_divergence_curve()` as a named fixed-radius neighborhood local-divergence estimator alongside the existing Rosenstein nearest-neighbor path.
- Add `estimate_largest_lyapunov_kantz()` with the same explicit analyst-declared fit-interval requirement and no automatic linear-region selection.
- Add `KantzDivergenceResult` retaining radius, minimum-neighbor requirement, initial neighbor counts, per-horizon contributing-reference/pair counts, and zero-mean-neighborhood counts.
- The Kantz radius is never expanded, tuned, or selected automatically; insufficient support excludes that reference/horizon and zero support at horizon zero fails the analysis.
- Keep Rosenstein and Kantz family-specific: the named fitters reject the wrong divergence-result type rather than silently treating the methods as aliases.
- Keep the existing IAAFT surrogate test Rosenstein-based in this tranche; adding Kantz does not silently change the hypothesis-test statistic.
- Generalize local-divergence plotting/reporting so the estimator family remains visible and positive slopes are still not described as standalone evidence of deterministic chaos.
- Add hand-counted neighborhood tests, fail-closed parameter tests, family-mismatch tests, logistic-map regression tests, plotting/reporting coverage, method guidance, worked/executable examples, references, mathematical contracts, and site integration.

## 0.28.0.dev0

- Add `bootstrap_rqa_metric_means()` for percentile-bootstrap uncertainty in population-average curve-level RQA summaries under one fixed recurrence specification.
- Support `unit="curve"` and equal-weight `unit="participant"`; participant mode averages selected trial-level RQA metrics within participant before resampling, preventing trial pseudo-replication.
- Retain per-curve realized radius, achieved RR, resolved Theiler window, selected metrics, the actual bootstrap-unit table, all bootstrap mean replicates, bias/SE, and percentile intervals.
- Under target-recurrence-rate mode, reject RR as an inferential outcome because recurrence density is controlled by design.
- Fail closed when any selected curve-level RQA metric is undefined; curves are never silently dropped, imputed, or assigned zero.
- Make the scope explicit: between-unit population sampling uncertainty only; no within-single-trajectory recurrence-line bootstrap, moving/block bootstrap, hierarchical trial bootstrap, measurement-error model, or parameter-selection uncertainty.
- Add `RQAMeanBootstrapResult`, `plot_rqa_metric_mean_bootstrap()`, and `rqa_metric_mean_bootstrap_reporting_text()`.
- Add reproducibility, equal-weight participant, target-RR, undefined-metric, embedding, design-error, plotting, and reporting tests.
- Add a dedicated mathematical contract, methods page, worked/executable example, preregistration/reporting guidance, assumptions, limitations, references, API docs, gallery figure, and CI integration.

## 0.27.0.dev0

- Add `recurrence_radius_profile()` for an exact recurrence-rate curve over a strictly increasing analyst-declared radius grid.
- Interpret RR(radius) explicitly as the empirical CDF of eligible pairwise state-space distances under the same inclusive threshold and Theiler-denominator contract as `recurrence_matrix()`.
- Add shell pair counts/fractions so the same table exposes binned pair-distance mass between consecutive declared radii.
- Apply Theiler exclusions exactly to cumulative pair counts without materializing a dense N x N distance matrix.
- Record eligible-pair count, partial/full distance-distribution coverage, state dimension, metric, source provenance, and the no-automatic-selection contract.
- Reject sorting, deduplication, boolean/string coercion, or other silent repairs of the declared radius grid.
- Add `plot_recurrence_rate_curve()` and `recurrence_radius_profile_reporting_text()`.
- Add hand-count, base-estimator-equivalence, zero-distance, Theiler, embedded-state, typing, plotting/reporting, and failure-contract tests.
- Add a dedicated threshold-diagnostics methods page, worked/executable example, scalable benchmark, mathematical-contract registration, API/docs integration, and preregistration/reporting/limitations guidance.
- No universal RR/radius recommendation or “optimal epsilon” selector is introduced.

## 0.26.0.dev0

- Add `rqa_parameter_sensitivity()` for a fully declared Cartesian multiverse over embedding dimension, delay, fixed-radius or target-RR threshold policy, Theiler window, and minimum diagonal/vertical line lengths.
- Require exactly one RQA threshold family and retain requested plus resolved delay, radius, recurrence-rate, Theiler, line-threshold, metric, and qualifying-line/count information for every specification.
- Add descriptive RQA variation summaries (finite fraction, quartiles, range, and SD) without ranking or selecting a preferred parameter combination.
- Add `lyapunov_parameter_sensitivity()` over embedding dimension, delay, Theiler window, and analyst-declared Rosenstein fit intervals while reusing divergence curves across fit intervals for the same reconstruction.
- Retain exponent, fit R², slope SE, fitted-point count, usable-pair support, zero-distance counts, and descriptive positive/negative slope frequencies across the declared LLE grid.
- State explicitly that positive-specification frequency is not a probability of deterministic chaos and that sensitivity-grid summaries are not sampling distributions.
- Fail the entire sensitivity call when any declared specification is invalid rather than silently dropping, repairing, or replacing problematic combinations.
- Add explicit one-parameter sensitivity plotting helpers that refuse hidden averaging across unspecified parameter dimensions.
- Keep RQA sensitivity memory-bounded by retaining tidy metrics/provenance rather than one sparse recurrence matrix per grid point.
- Add result contracts, reporting helpers, tests, executable/worked examples, mathematical-contract registration, preregistration/reporting guidance, limitations, and site navigation.

## 0.25.0.dev0

- Add `windowed_rqa_sensitivity()` for predeclared window/step sensitivity grids without automatic tuning selection.
- Quantify deterministic overlap through analyzed-source coverage, reused-sample fraction, mean/max window membership, window span, profile-grid spacing, support, and tail diagnostics.
- Compare functional RQA profiles across specifications only at exact shared window centers; no interpolation or hidden alignment is used.
- Add descriptive per-curve/per-metric sensitivity summaries plus pairwise RMSE, absolute-difference, and correlation diagnostics where exact common centers exist.
- Add `windowed_rqa_functional_mean_band()`, which derives finite functional RQA trajectories and reuses the package's simultaneous Gaussian multiplier band at explicitly declared curve or equal-weight participant units.
- Preserve complete derived functions during inference rather than resampling overlapping window rows; participant-level inference averages repeated trial curves within participant before weighting participants equally.
- State explicitly that source-sample reuse diagnostics do not estimate an effective independent sample size and that the new band is not a within-single-trajectory block bootstrap.
- Add plotting/reporting helpers, result contracts, tests, a worked sensitivity/dependence example, expanded API/site guidance, and methodological references for RQA parameter sensitivity and independent-unit functional inference.

## 0.24.0.dev0

- Freeze cross-library RQA conventions in code, tests, and documentation: inclusive radius threshold, LOI/Theiler policy, recurrence-rate denominators, 0-1 ratio scale, entropy denominator, and explicit uncorrected border-line handling.
- Keep multivariate gaze surrogates deferred until a joint MIAAFT/multivariate-Fourier null can preserve and diagnose cross-channel structure; scalar IAAFT remains explicitly univariate.
- Add a reproducible sparse-recurrence benchmark harness and avoid unsupported wall-clock expectations in the methodological contract.
- Add `windowed_rqa_trajectory_set()` to convert declared sliding-window RQA summaries across source curves into a native functional `TrajectorySet` while retaining every per-curve window table.
- Record window overlap, tail handling, metric units, radius policy, undefined-value handling, and the explicit non-independence of window rows.
- Reject recurrence rate as a downstream functional outcome when target-recurrence-rate mode controls recurrence density by design.
- Add `WindowedRQAFunctionalResult`, `plot_windowed_rqa_trajectories()`, and `windowed_rqa_functional_reporting_text()`.
- Add a worked RQA → functional trajectories → MFPCA workflow and a deterministic gallery figure.
- Tighten the nonlinear evidence chain with verified direct eye-movement LLE precedent and surrogate-null references.
- Verify and expand the nonlinear evidence chain with direct eye-movement RQA/CRQA/LLE sources, corrected Kantz bibliographic metadata, and an explicit rule that negative searches do not establish novelty.
- Tighten temporal-sampling contracts: AMI/FNN diagnostics fail closed on irregular physical-time grids; spatial recurrence remains available for irregular observations, while standard line-based RQA requires a regular grid and cross-RQA requires matching sampling steps.

## 0.23.0.dev0 — 2026-09-22

Twenty-third development tranche.

- multivariate delay-coordinate reconstruction with explicit state dimensions, embedding dimension, delay, units, finite-data validation, and provenance;
- diagnostic-only average-mutual-information/autocorrelation lag curves and Kennel-style false-nearest-neighbor dimension curves with no automatic parameter selection;
- sparse SciPy-CSR recurrence matrices using explicit fixed-radius or target-recurrence-rate policies, Euclidean/cityblock/Chebyshev norms, and explicit Theiler exclusion;
- line-based RQA metrics including recurrence rate, determinism, diagonal entropy, laminarity, trapping time, line maxima, counts, and auto-recurrence CORM;
- sliding full-window RQA with explicit trailing-tail accounting plus sparse cross-recurrence / cross-RQA;
- Rosenstein-style nearest-neighbor local-divergence curves retaining usable-pair and zero-distance counts, followed by an analyst-declared LLE fit interval with slope, units, standard error, and R²;
- seeded IAAFT surrogate nonlinearity testing with identical observed/surrogate analysis settings, plus-one Monte Carlo p-values, retained convergence iterations, and no silent failed-surrogate replacement;
- experimental interpolated Poincare crossings, explicit local affine return-map fitting, and eigenvalue/spectral-radius contraction/expansion diagnostics;
- explicit prohibition on describing empirical return-map eigenvalues as classical Floquet multipliers or the fitted Jacobian as a monodromy matrix;
- nonlinear plotting helpers, synthetic truth/edge/contract tests, executable examples, methodological guide, assumptions, limitations, preregistration/reporting guidance, references, LaTeX contracts, API documentation, and expanded deterministic gallery;
- classical raw-gaze Floquet/monodromy analysis and numerical bifurcation continuation remain outside the public API until an explicit identified dynamical model exists.

## 0.22.0.dev0 — 2026-09-22

Twenty-second development tranche.

- public `MathematicalContract` metadata object plus `list_mathematical_contracts()`, `get_mathematical_contract()`, and `mathematical_contract_frame()`;
- one machine-readable function → LaTeX registry linking scientific APIs to implementation equations, stable site anchors, and explicit scope boundaries;
- deterministic generated `FUNCTION_EQUATION_INDEX.md` for GitHub and website `reference/function-equation-index.md`, with CI freshness validation;
- executable and worked examples demonstrating lookup by function/key and tidy function-level export;
- Mermaid workflow atlas for representation choice, FPCA validation, Gaussian FPCR inference branches, and function → equation → figure documentation flow;
- website gallery expanded from five to eight deterministic SVG figures with FPCA variance, registration displacement, and fixed-family test plots;
- native Material Mermaid configuration and updated homepage/tutorial/API/README navigation;
- documentation validator raised to require the expanded gallery, 0.22 integration, generated equation indexes, and all mathematical deep links;
- scientific estimators, inferential defaults, coverage gate, and optional-backend contracts unchanged.

## 0.21.0.dev0 — 2026-09-22

Twenty-first development tranche.

- implementation-matched mathematical reference with LaTeX equations for quadrature weighting, FPCA/MFPCA, reconstruction, functional L2 distance, multilevel decomposition, compositional ALR, registration, simultaneous mean inference, Gaussian FPCR, heteroscedastic wild bootstrap, max-|t| calibration, family testing, Monte Carlo precision, and split conformal anomaly review;
- repository-level `MATHEMATICAL_CONTRACTS.md` so equations render directly on GitHub as well as on the methods website;
- MathJax 3 configuration upgraded for Material instant navigation with explicit re-typesetting after client-side page changes;
- deterministic SVG visual gallery generated from the real package plotting APIs and synthetic seeded data;
- gallery generation uses a non-interactive backend, deterministic SVG hashing, and timestamp-free metadata;
- dedicated visual-gallery page linking each plot to its public API, worked example, and mathematical equation;
- documentation contract validator checks MkDocs nav targets, equation/API mappings, MathJax wiring, generated gallery assets, README integration, and documented public API exports;
- docs CI now regenerates the gallery and validates documentation contracts before the unchanged strict MkDocs build;
- executable mathematical-contract example numerically checks quadrature-domain length, FPCA reconstruction identity, L2 symmetry, and ALR round-trip behavior;
- homepage/tutorial UX refreshed with mathematical-reference and gallery entry points, corrected legacy equation markup, and removal of duplicate sparse-FPCA cards;
- documentation dependencies constrained to the compatible Material-for-MkDocs 9.x / MkDocs 1.x line and raised to the 2026 security-fixed Material release floor.

## 0.20.0.dev0 — 2026-09-22

Twentieth development tranche.

- finite-bootstrap Monte Carlo precision diagnostics for the 0.19 fixed-family Gaussian FPCR wild-bootstrap hypothesis-test layer;
- target-wise, single-step maxT-adjusted, and complete-family global bootstrap exceedance counts are recovered from the exact retained root matrix without any new resampling;
- raw exceedance fractions r/B are reported only as diagnostic binomial quantities and never replace the configured plus-one/raw hypothesis-test p-values;
- plug-in binomial Monte Carlo standard errors are accompanied by Clopper-Pearson exact intervals, including boundary cases with zero or B exceedances;
- conservative decision-stability flags require the full Monte Carlo interval to lie on the same side of alpha as the already reported test decision;
- diagnostics never reverse or recompute the 0.19 rejection indicators;
- provenance distinguishes Monte Carlo simulation precision from scientific sampling uncertainty and records that no additional strong-FWER, clustered-bootstrap, component-selection, or sequential-stopping guarantee is added;
- dedicated table, plot, reporting helper, methodological guide, worked example, references, preregistration guidance, limitations, FAQ, and executable CI example;
- deterministic hand-calculated count/interval tests plus validation, public-API, plotting, reporting, and provenance tests.

## 0.19.0.dev0 — 2026-09-22

Nineteenth development tranche.

- two-sided hypothesis tests for a predeclared family of fixed Gaussian FPCR centered projections;
- arbitrary finite scalar or target-specific null projection values, with zero as the explicit default;
- observed statistics use the stored heteroscedastic reference standard errors and fail explicitly for non-zero null discrepancies paired with zero standard error;
- target-wise bootstrap tail probabilities use each target's absolute studentized root distribution;
- single-step maxT-adjusted values use the replicate-wise maximum absolute studentized root over the complete target family;
- complete-family global max-statistic test is reported from the same joint root distribution;
- conservative plus-one Monte Carlo correction is the default, with the uncorrected empirical exceedance proportion available explicitly;
- no FPCA fit, score regression, residual calculation, multiplier draw, or bootstrap replicate is rerun;
- provenance states that the bootstrap is not explicitly null-enforced and that strong FWER control for arbitrary subset nulls is not claimed without additional subset-pivotality conditions;
- table, plotting, reporting, public-API, deterministic, hand-calculated truth, edge-case, and regression tests.
## 0.18.0.dev0 — 2026-09-22

Eighteenth development tranche.

- familywise simultaneous inference across a predeclared set of fixed Gaussian FPCR target projections;
- post-calibration reuses the exact studentized wild-bootstrap roots from the 0.16/0.17 fixed-regressor engine and does not rerun FPCA, score regression, residual estimation, or multiplier generation;
- one maximum absolute studentized root is computed across the complete target family within each bootstrap replicate;
- the familywise critical value is the requested quantile of those replicate maxima using the same conservative higher empirical-quantile convention;
- target-wise critical values at the same confidence level are retained for direct audit and comparison;
- a one-target family exactly reduces to the corresponding target-wise calibration;
- simultaneous intervals are never narrower than the same-level target-wise intervals apart from floating-point tolerance;
- simultaneity applies only to the fixed target trajectories present in the supplied base result and does not extend to future outcomes, unlisted targets, clustered dependence, or component-selection uncertainty;
- table, plotting, reporting, public-API, regression, and synthetic invariant tests.

## 0.17.0.dev0 — 2026-09-22

Seventeenth development tranche.

- stabilized-volatility selection of Gaussian FPCR wild-bootstrap inference truncation h;
- residual truncation k remains explicit and bootstrap pseudo-truth uses g=k;
- consecutive h candidate grids with h>=g are required;
- one fixed FPCA/MFPCA basis is fitted at the largest candidate h;
- identical wild multiplier draws are reused across every candidate h within each bootstrap replicate, preventing independent Monte Carlo noise from masquerading as truncation volatility;
- target-wise interval centers and widths are retained for every candidate;
- analyst-supplied absolute width and center thresholds define stable transitions; the paper's 0.01 simulation setting is not silently imposed as a package default;
- the paper run parameter r is explicit and requires r+1 consecutive stable transitions;
- the earliest qualifying h is selected separately for each target;
- absent stable runs fail by default, with explicit warn/ignore alternatives that retain unselected targets rather than silently choosing the largest h;
- scan/selection result objects, long-form diagnostics, plotting/reporting helpers, synthetic truth/regression tests, executable example, and expanded methodological/site guidance.


## 0.16.0.dev0 — 2026-09-22

Sixteenth development tranche.

- fixed-regressor multiplier wild-bootstrap inference for centered Gaussian FPCR projections under possible heteroscedastic response errors;
- residual estimation and bootstrap pseudo-truth use k=g FPCs, while target inference uses an explicitly declared h>=g truncation;
- normal and mathematically mean-zero/unit-variance Mammen two-point multipliers;
- bootstrap-level heteroscedastic studentization recomputed from every wild pseudo-fit;
- symmetrized studentized target-wise intervals centered on the h-component reference projection;
- FPCA/MFPCA basis remains fixed during wild resampling, matching the fixed-regressor construction rather than paired-bootstrap refit semantics;
- explicit rejection of declared repeated/clustered unit IDs because clustered wild-bootstrap validity is outside this tranche;
- intervals target centered projections relative to the training functional mean and are neither future-outcome prediction intervals nor simultaneous target intervals;
- deterministic seeded behavior, provenance, table/plot/reporting helpers, focused tests, executable example, and expanded methodological/site guidance.


## 0.15.0.dev0 — 2026-09-21

Fifteenth development tranche.

- split-conformal marginal anomaly p-values for new common-grid functional trajectories;
- explicit proper-training, calibration, and target partitions with disjoint curve-ID checks;
- FPCA/MFPCA reference fitting occurs on the proper-training set only;
- reconstruction-RMSE nonconformity for deviations poorly represented by the proper-training FPC span;
- optional score-space Mahalanobis nonconformity with an explicitly selected empirical or robust covariance estimator;
- conservative greater-than-or-equal tie handling and exact finite calibration-grid p-value resolution;
- review flags at an explicit alpha level never trigger automatic exclusions;
- provenance explicitly limits validity claims to exchangeable curve-level inliers and records that calibration-conditional adjustment, multiple-testing correction, and FDR control are not implemented in this tranche;
- table, plotting, reporting helpers, synthetic truth tests, executable example, and expanded methodological/site guidance.


## 0.14.0.dev0 — 2026-09-21

Fourteenth development tranche.

- marginal future-outcome prediction intervals for fixed Gaussian FPCR target trajectories;
- prediction reuses the exact paired-bootstrap conditional-mean distribution from bootstrap_fpca_regression_uncertainty();
- an independent centered empirical residual draw is added to each bootstrap mean prediction to represent future response noise;
- the centered residual pool and every sampled residual are retained for auditability;
- the method is explicitly restricted to an exchangeable/common residual distribution and does not claim heteroscedasticity robustness;
- prediction intervals are marginal per target and do not claim simultaneous or joint coverage across multiple target trajectories;
- conditional-mean uncertainty remains separately available from the underlying 0.12 result;
- deterministic seeded residual resampling, table/plot/reporting helpers, tests, executable example, and expanded methodological/site guidance.


## 0.13.0.dev0 — 2026-09-21

Thirteenth development tranche.

- studentized maximum-deviation simultaneous bands for reconstructed Gaussian FPCR slopes;
- post-calibration reuses the exact paired-bootstrap slope replicates from bootstrap_fpca_regression_uncertainty() rather than running a second resampling scheme;
- global calibration uses one maximum across the full observed time-by-dimension slope grid;
- dimension calibration uses a separate maximum over observed time within each functional predictor dimension;
- exact zero-variance handling: zero-width cells are allowed only when bootstrap discrepancy is also negligible, while contradictory zero-SE/non-zero-deviation cells fail explicitly;
- simultaneous coverage claims are restricted to the observed grid and do not extend between sampled time points;
- the band is explicitly distinct from the operator-scaled FPCR significance test in recent 2026 theory;
- long-form band tables, plotting/reporting helpers, tests, executable example, and expanded methodological/site guidance.


## 0.12.0.dev0 — 2026-09-21

Twelfth development tranche.

- paired nonparametric bootstrap uncertainty for Gaussian scalar-on-function functional principal-component regression;
- FPCA/MFPCA and the score regression are refitted together in every bootstrap replicate;
- curve- or participant-level paired resampling keeps the functional predictor and scalar outcome coupled;
- reconstructed functional slopes are returned in original trajectory coordinate units with explicit correction for MFPCA dimension scaling;
- fixed-target bootstrap intervals target the fitted conditional mean response and are explicitly not future-outcome prediction intervals;
- component count remains fixed across bootstrap replicates; component-selection uncertainty is not silently mixed into the inferential target;
- full-rank regression designs are required for the reference and every bootstrap replicate; invalid replicates fail explicitly rather than being discarded;
- FPC label matching is intentionally unnecessary for slope/mean-response targets because each complete FPCR refit is reconstructed in its own internally consistent basis;
- Gaussian-only scope is explicit; binomial inference is not generalized without dedicated methodology;
- plotting/reporting helpers, tests, executable example, and expanded methodological/site guidance.


## 0.11.0.dev0 — 2026-09-21

Eleventh development tranche.

- basis-resampling uncertainty summaries for FPC scores of fixed target trajectories;
- training-curve or compatible external-target projections through bootstrap-refitted FPCA/MFPCA bases;
- maximum-absolute-similarity component matching and explicit sign alignment before comparing target scores;
- curve- or participant-level basis resampling for repeated-trial designs;
- percentile score envelopes and bootstrap standard deviations retained as descriptive decomposition-uncertainty summaries;
- explicit rejection of incompatible target grids, dimensions, coordinate systems, and time units rather than silent coercion;
- provenance states that the result does not include target measurement error, latent-curve uncertainty, future-curve variability, preprocessing uncertainty, or full downstream uncertainty propagation;
- plotting/reporting helpers, tests, executable example, and expanded methodological/site guidance.


## 0.10.0.dev0 — 2026-09-21

Tenth development tranche.

- matched nonparametric bootstrap uncertainty for FPCA eigenvalues, explained-variance ratios, and cumulative explained variance;
- component matching by maximum absolute functional similarity before attaching spectrum estimates to reference FPC identities;
- explicit curve- or participant-level resampling for repeated-trial designs;
- studentized component-wise or familywise calibration across requested components within each spectrum metric;
- familywise semantics explicitly do not claim joint calibration across eigenvalues, per-component ratios, and cumulative ratios simultaneously;
- no silent clipping of eigenvalue or variance-ratio uncertainty intervals to mathematical support;
- deterministic seeded behavior, zero-variance/degenerate-bootstrap safeguards, plotting/reporting helpers, tests, worked example, and expanded methodological/site guidance.


## 0.9.0.dev0 — 2026-09-21

Ninth development tranche.

- matched, sign-aligned nonparametric bootstrap uncertainty for individual FPC shapes;
- studentized maximum-deviation calibration over the observed time-by-dimension grid;
- explicit component-wise or familywise simultaneous calibration across requested FPCs;
- curve- or participant-level resampling for independent-unit control in repeated-trial studies;
- optional analyst-supplied relative eigengap screen with explicit error/warn/ignore behavior and no package-imposed near-tie threshold;
- zero-variance/degenerate-bootstrap guardrails and deterministic seeded behavior;
- long-form band tables, visualization, manuscript-reporting helpers, tests, worked example, and expanded methodological/site guidance;
- explicit limitation that observed-grid bootstrap calibration does not establish continuous-domain coverage or unique interpretation of near-tied FPC axes.


## 0.8.0.dev0 — 2026-09-21

Eighth development tranche.

- outcome-tuned FPC-count selection for scalar-on-function regression;
- FPCA mean/scaling/eigenfunctions and scalar regression refitted inside every training fold;
- curve- or participant/group-level folds for repeated-trial prediction;
- Gaussian RMSE/MAE and binary log-loss/Brier objectives;
- explicit minimum-loss and one-standard-error component-selection rules;
- nested CV that separates inner FPC-count selection from outer predictive-performance evaluation;
- explicit failures for one-class binomial training folds, perfect separation, non-convergence, invalid probabilities, non-numeric/non-finite covariates, and rank-deficient designs;
- retained fold assignments, candidate predictions, inner summaries, and provenance;
- plots, reporting helpers, worked repeated-trial example, methodological guide, assumptions, limitations, preregistration, reporting, FAQ, references, and API documentation.


## 0.7.0.dev0 — 2026-09-21

Seventh development tranche.

- studentized Gaussian multiplier simultaneous bands for common-grid functional means;
- simultaneous calibration across the observed time-by-dimension grid using the maximum absolute standardized mean process;
- explicit curve-level versus equal-weight participant-level inference units;
- repeated-trial participant aggregation that prevents participants with more trials from receiving greater inferential weight;
- exact handling of zero-variance grid points without division artifacts;
- explicit rejection of direct Euclidean bands for probability-simplex trajectories;
- long-form band tables, visualization, and manuscript-reporting helpers;
- methodological guidance distinguishing observed-grid simultaneous bands from continuous-domain confidence claims;
- worked repeated-trial example, assumptions, limitations, preregistration, reporting, FAQ, and API documentation.


## 0.6.0.dev0 — 2026-09-20

Sixth development tranche.

- optional FDApy interoperability for genuinely sparse irregular univariate functional trajectories;
- direct conversion from `IrregularTrajectorySet` to FDApy `IrregularFunctionalData` without common-grid interpolation;
- covariance-operator UFPCA with PACE conditional-expectation score recovery;
- explicit fit/score smoothing settings, PACE tolerance, normalization flag, evaluation grid, mean/covariance smoothing kwargs, and backend-version provenance;
- selected-dimension sparse sampling diagnostics and metadata-preserving sparse-FPC score frames;
- non-finite sparse observations rejected rather than silently dropped or interpolated;
- backend-independent fake-FDApy contract tests plus a dedicated real-FDApy integration workflow for Python 3.11–3.12; core eyetrajectoriespy support remains Python 3.11–3.13;
- native sparse-observation plotting and manuscript-reporting helpers;
- revised sparse-irregular decision guidance, worked PACE example, interpretation, assumptions, limitations, preregistration, reporting, references, and API documentation.


## 0.5.0.dev0 — 2026-09-19

Fifth development tranche.

- adjacent retained-eigenvalue gap diagnostics with no default near-tie threshold;
- optional explicit relative-gap review flags when a study-specific threshold is supplied;
- principal-angle comparison of corresponding FPCA eigenspaces;
- normalized projection-operator distance for rotation-invariant subspace comparison;
- curve- or participant-level bootstrap eigenspace stability;
- subspace diagnostics that remain stable under sign changes, swaps, and rotations within a selected component block;
- plotting and manuscript-reporting helpers for eigengap and subspace diagnostics;
- synthetic rotation truth tests demonstrating unstable individual labels with an unchanged two-dimensional subspace;
- methodological guidance for near-tied eigenvalues, interpretation, limitations, preregistration, and reporting.


## 0.4.0.dev0 — 2026-09-19

Fourth development tranche.

- leakage-aware held-out reconstruction cross-validation for FPCA/MFPCA component counts;
- grouped cross-validation that keeps repeated participant/group trials out of both train and test simultaneously;
- explicit minimum-RMSE and one-standard-error component-selection rules;
- fold assignment and reconstruction-error diagnostics with retained provenance;
- matched, sign-aligned bootstrap pointwise envelopes for functional principal-component shapes;
- participant- or curve-level bootstrap resampling with deterministic seeds;
- explicit descriptive-only envelope semantics; no simultaneous confidence-band claim;
- plotting and manuscript-reporting helpers for component selection and component-shape uncertainty;
- worked grouped-CV/bootstrap example, methodological guidance, interpretation, limitations, preregistration, and API documentation.


## 0.3.0.dev0 — 2026-09-18

Third development tranche.

- FPCA anomaly screening combining integrated reconstruction error and FPC score-space Mahalanobis distance;
- robust Minimum Covariance Determinant or explicit empirical score covariance;
- participant-/group-aware leave-one-group-out FPCA influence analysis;
- matched component-shape and explained-variance sensitivity summaries;
- functional review flags that never trigger automatic exclusion;
- optional scikit-fda functional boxplot and magnitude-shape outlier screening;
- plotting and manuscript-reporting helpers for outlier/influence diagnostics;
- synthetic truth example with an injected atypical trajectory;
- sparse-irregular FPCA decision guidance and expanded pre-registration/reporting safeguards;
- backend-independent basis-family/B-spline contract validation before optional scikit-fda import.

## 0.2.0.dev0 — 2026-09-18

Second development tranche.

- native `IrregularTrajectorySet` objects preserve curve-specific sampling without forced interpolation;
- explicit overlap/union common-grid construction and gap-protected irregular-to-grid projection;
- bootstrap FPCA component stability with curve- or participant-level resampling and deterministic seeds;
- matched functional-component similarity and reconstruction diagnostics;
- phase functions and phase FPCA from registration warpings;
- registered-versus-unregistered FPCA sensitivity diagnostics;
- provenance-preserving optional B-spline/Fourier projection through scikit-fda;
- expanded examples for irregular data, stability, phase analysis, and basis interoperability;
- tutorial gallery, pre-registration checklist, and expanded methods/site navigation;
- optional FDA interoperability CI.

## 0.1.0.dev0 — 2026-09-18

Initial development release.

- canonical functional trajectory data model with provenance;
- long-format gaze import and explicit coordinate/time semantics;
- conservative resampling, gap handling, smoothing, and time normalization;
- grid-based univariate and multivariate FPCA;
- reconstruction, score extraction, and component interpretation helpers;
- multilevel participant/trial FPCA decomposition;
- compositional AOI-probability FPCA with simplex-preserving inverse transform;
- landmark registration and explicit phase/amplitude outputs;
- optional elastic SRVF integration through `fdasrsf`;
- functional L2 distances, FPCA-score clustering, and scalar-on-function regression;
- synthetic trajectory generators and manuscript-oriented reporting helpers;
- MkDocs methods site, worked examples, interpretation guidance, and CI workflows.
