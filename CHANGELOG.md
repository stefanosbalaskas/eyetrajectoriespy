# Changelog

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
