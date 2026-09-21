# Tutorial gallery

Choose a tutorial by the scientific problem rather than by the function name.

<div class="grid cards" markdown>

-   **Continuous 2-D viewing strategy**

    Preserve horizontal and vertical location jointly and identify dominant whole-trajectory modes.

    [2-D evidence inspection](../examples/evidence-inspection.md)

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
