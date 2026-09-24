# Tutorial gallery

Choose a tutorial by the scientific problem rather than by the function name.

<div class="grid cards" markdown>

-   **See the methods before running them**

    Browse deterministic figures generated from the package's plotting API, with direct links to worked examples and equations.

    [Visual gallery](../methods/visual-gallery.md)

-   **Read the implementation-matched equations**

    Use the LaTeX mathematical reference to connect public functions to the exact estimands, transformations, studentization, and calibration implemented in code.

    [Mathematical reference](../methods/mathematical-reference.md)

-   **Query equations from Python**

    Inspect the same function → LaTeX contracts programmatically and export a tidy function-level table.

    [Function → equation registry](../examples/function-equation-registry.md)

-   **See the decision flow**

    Follow rendered diagrams from representation choice through validation and inferential scope.

    [Workflow atlas](../methods/workflow-atlas.md)


-   **Analyze recurrence and nonlinear state-space dynamics**

    Reconstruct state space explicitly, quantify recurrent structure, inspect time-varying RQA, estimate local divergence, and compare with IAAFT surrogates.

    [Nonlinear trajectory dynamics](../examples/nonlinear-dynamics.md)

-   **Inspect recurrence geometry as a sparse network**

    Convert one declared auto-recurrence plot to an undirected sparse graph and
    inspect degree, clustering, transitivity, and connected components without
    retuning the recurrence threshold.

    [Recurrence-network worked example](../examples/recurrence-networks.md)

-   **Joint recurrence across synchronized systems**

    Keep gaze, pupil, physiology, or other synchronized subsystem state spaces
    separate, build their recurrence plots under explicit contracts, then
    inspect their logical intersection and JRQA summaries.

    [Joint recurrence worked example](../examples/joint-recurrence.md)


-   **Preserve planar linear structure in surrogate testing**

    Generate joint x/y MIAAFT surrogates, inspect retained power/cross-spectrum mismatch, and evaluate a multichannel nonlinear statistic without independently randomizing gaze dimensions.

    [Multivariate surrogate testing](../examples/multivariate-surrogates.md)

-   **Study repeated-cycle return stability**

    Define an explicit Poincare section and fit an experimental local return map without calling the result classical Floquet stability.

    [Empirical return-map stability](../examples/return-map-stability.md)

</div>

<div class="grid cards" markdown>

-   **Continuous 2-D viewing strategy**

    Preserve horizontal and vertical location jointly and identify dominant whole-trajectory modes.

    [2-D evidence inspection](../examples/evidence-inspection.md)

-   **Compare ordered gaze trajectories elastically**

    Contrast discrete Fréchet bottleneck separation with cumulative DTW alignment, compare the predeclared symmetric1 or symmetric2/N+M contract, inspect the path/coupling, and keep timing assumptions explicit.

    [DTW worked example](../examples/dynamic-time-warping.md) · [Discrete Fréchet example](../examples/discrete-frechet.md)

-   **Check whether trajectory similarity depends on the distance contract**

    Compare predeclared L2, discrete Fréchet, and DTW specifications using pair-distance rank agreement and local top-k neighbor overlap without selecting a winner.

    [Trajectory-distance sensitivity](../examples/trajectory-distance-sensitivity.md)

-   **Irregular sampling**

    Keep native sample times, audit gaps, then choose an explicit common-grid projection.

    [Native irregular trajectories](../examples/native-irregular.md)

-   **Repeated trials**

    Separate stable participant-level trajectory variation from trial-level deviation.

    [Multilevel FPCA](../examples/multilevel.md)

-   **Are my FPCs stable?**

    Bootstrap people or curves, match component functions, and inspect reconstruction error.

    [FPCA stability](../examples/fpca-stability.md)

-   **How many FPCs should I retain?**

    Use leakage-safe held-out reconstruction CV, then inspect matched-bootstrap FPC shape uncertainty.

    [Selection & FPC uncertainty](../examples/fpca-selection-uncertainty.md)

-   **Which FPC count predicts an external outcome?**

    Tune ordinary FPC regression inside folds and use nested participant-grouped CV when predictive performance is itself a result.

    [Predictive FPCA regression](../examples/predictive-fpca-regression.md)

-   **Do my FPC labels rotate inside a stable subspace?**

    Inspect adjacent eigengaps, principal angles, and bootstrap projector distance for a component block.

    [Near-tied FPC subspaces](../examples/near-tied-subspace.md)

-   **Do I need uncertainty for the mean trajectory?**

    Use a studentized Gaussian multiplier maximum over the full observed time × dimension grid, with participant-level units for repeated trials.

    [Functional mean bands](../examples/functional-mean-bands.md)

-   **What did registration remove?**

    Analyze warping functions as phase outcomes and compare spatial FPCs before and after alignment.

    [Phase FPCA](../examples/phase-fpca.md)

-   **AOI allocation as a composition**

    Respect the probability simplex instead of treating AOI probabilities as independent channels.

    [Compositional trajectories](../examples/compositional.md)

-   **Trajectory to behavioral outcome**

    Use retained FPC scores as a transparent low-dimensional approximation for scalar prediction.

    [Functional regression](../examples/regression.md)

-   **Experimental predictors to continuous gaze response**

    Estimate coefficient functions for condition or participant variables and calibrate observed-grid simultaneous bands without silently treating repeated trials as independent.

    [Function-on-scalar regression](../examples/function-on-scalar.md)

-   **Repeated trials with trial-varying predictors**

    Fit one joint Gaussian functional mixed model with a participant-specific functional random intercept instead of averaging trials or running separate pointwise models.

    [Functional mixed-effects regression](../examples/functional-mixed-effects.md)

-   **Basis representation**

    Project a selected functional dimension to B-spline or Fourier coordinates through scikit-fda.

    [Basis representations](../guides/basis-representations.md)

-   **Is one participant driving the FPCA?**

    Combine reconstruction/score-space review diagnostics with participant-level omission sensitivity.

    [Outlier & influence diagnostics](../examples/outlier-influence.md)

-   **Are my irregular curves too sparse to interpolate?**

    Keep curve-specific grids and use optional FDApy covariance UFPCA with PACE conditional-expectation scores.

    [Sparse PACE FPCA](../examples/sparse-pace-fpca.md)

</div>


### Simultaneous FPC-shape uncertainty

Use [Simultaneous FPC bands](../examples/simultaneous-fpc-bands.md) when the scientific claim concerns an entire estimated eigenfunction rather than pointwise descriptive variation. The example uses participant-level resampling, compares component-wise and familywise calibration, and shows the near-tie identifiability screen.


### FPCA spectrum uncertainty

Use [FPCA spectrum uncertainty](../examples/fpca-spectrum-uncertainty.md) when eigenvalues or explained-variance summaries need uncertainty rather than point estimates alone. The worked example distinguishes matched individual spectrum quantities from rank-ordered cumulative variance and compares component-wise with familywise calibration.


### FPC score basis-resampling uncertainty

Use [FPC score basis uncertainty](../examples/fpca-score-uncertainty.md) when score coordinates themselves need a stability/uncertainty analysis rather than being treated as fixed after FPCA. The worked example keeps targets fixed, resamples participants to refit the basis, matches/sign-aligns bootstrap components, and distinguishes basis uncertainty from measurement or downstream-model uncertainty.


### Gaussian FPCR bootstrap uncertainty

Use [Gaussian FPCR bootstrap uncertainty](../examples/fpcr-bootstrap-inference.md) when a scalar-on-function Gaussian regression result needs uncertainty that propagates re-estimation of the FPCA basis. The worked example uses participant-level paired resampling, reconstructs the slope in original x/y units, and separates conditional-mean intervals from future-outcome prediction intervals.


### Gaussian FPCR simultaneous slope bands

Use [Gaussian FPCR simultaneous slope bands](../examples/fpcr-simultaneous-slope-band.md) after a paired-bootstrap Gaussian FPCR fit when one observed-grid band is required for the reconstructed slope. The tutorial compares global and dimension-wise calibration and emphasizes that the result is neither a continuous-domain band nor the operator-scaled FPCR significance test.


### Gaussian FPCR future-outcome prediction

Use [Gaussian FPCR future-outcome prediction](../examples/fpcr-future-prediction.md) when the scientific target is a future observed scalar response rather than only its fitted conditional mean. The worked example keeps the underlying paired-bootstrap mean distribution visible and adds response noise through centered empirical residual resampling.


### Conformal FPCA anomaly review

Use [Conformal FPCA anomaly review](../examples/conformal-fpca-anomaly.md) when genuinely new common-grid trajectories must be assessed relative to a reference population. The example keeps proper training, calibration, and targets disjoint; demonstrates exact finite p-value resolution; and contrasts reconstruction versus score-space nonconformity.


### Heteroscedastic Gaussian FPCR wild bootstrap

Use [Heteroscedastic FPCR wild bootstrap](../examples/fpcr-wild-bootstrap.md) when the functional regressors are treated as fixed but scalar response variance may be heterogeneous. The example uses one trajectory per participant, makes k=g and h explicit, recomputes the heteroscedastic studentization scale in each pseudo-fit, and distinguishes target projection inference from future-outcome prediction.


### Simultaneous fixed-target FPCR wild bootstrap

Use [Simultaneous fixed-target FPCR wild bootstrap](../examples/fpcr-wild-bootstrap-simultaneous.md) when one declared family of fixed target projections needs familywise rather than separate target-wise calibration. The example reuses the exact heteroscedastic wild-bootstrap root matrix, compares target-wise with max-|t| simultaneous intervals, and makes the fixed-target scope explicit.


### Fixed-family FPCR wild-bootstrap hypothesis tests

Use [Fixed-family FPCR wild-bootstrap tests](../examples/fpcr-wild-bootstrap-family-tests.md) when a declared set of fixed target projections needs explicit two-sided testing rather than confidence intervals alone. The example compares target-wise and single-step maxT-adjusted bootstrap probabilities, reports the complete-family global test, and makes the subset-pivotality boundary explicit.


### Wild-bootstrap Monte Carlo precision

Use [Wild-bootstrap Monte Carlo precision](../examples/fpcr-wild-bootstrap-monte-carlo.md) after a fixed-family test when the finite number of retained bootstrap replicates needs an explicit precision audit. The example reports exceedance counts, raw tail fractions, MCSEs, exact binomial intervals, and stability flags without changing the original plus-one/raw test probabilities.

### Stabilized-volatility FPCR wild-bootstrap selection

Use [Stabilized-volatility wild-bootstrap selection](../examples/fpcr-wild-bootstrap-selection.md) when k=g is fixed but the target-inference truncation h needs a declared data-driven tuning rule. The example scans consecutive h values with shared multipliers, plots target-specific interval stability, applies explicit rho_w/rho_c/r criteria, and demonstrates the no-silent-fallback failure contract.

## Directed dependence

For already-discrete source/target state sequences, continue with the
[transfer-entropy method guide](../methods/transfer-entropy.md) and
[worked example](../examples/transfer-entropy.md). The workflow requires
explicit histories, lag, and—when used—an explicit surrogate shift set.

For robustness across several defensible discrete-TE histories or lags, continue
with the
[transfer-entropy sensitivity guide](../methods/transfer-entropy-sensitivity.md)
and
[worked sensitivity example](../examples/transfer-entropy-sensitivity.md).
