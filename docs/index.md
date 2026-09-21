---
title: Functional gaze trajectories, without hidden analytical decisions
---

<div class="et-hero" markdown>
<div class="et-kicker">eyetrajectoriespy 0.12 · continuous eye-tracking FDA</div>

# Model the viewing process, not only its summaries

eyetrajectoriespy provides a vendor-neutral scientific layer for continuous gaze paths, multivariate FPCA, native irregular trajectories, repeated-trial functional decomposition, phase analysis, compositional AOI trajectories, and explicit validation of component stability.

<span class="et-pill">2-D x(t), y(t)</span><span class="et-pill">native irregular grids</span><span class="et-pill">sparse PACE FPCA</span><span class="et-pill">sparse PACE FPCA</span><span class="et-pill">FPCA / MFPCA</span><span class="et-pill">grouped reconstruction CV</span><span class="et-pill">bootstrap stability</span><span class="et-pill">eigenspace stability</span><span class="et-pill">mean-band inference</span><span class="et-pill">outlier / influence review</span><span class="et-pill">multilevel</span><span class="et-pill">phase</span><span class="et-pill">elastic SRVF</span>
</div>

<div class="grid cards" markdown>

-   **Choose the scientific object first**

    Decide whether the object is a planar path, irregularly sampled process, repeated-trial process, AOI composition, registered amplitude, or phase function before choosing an estimator.

    [:octicons-arrow-right-24: Analysis decision map](concepts/decision-map.md)

-   **Keep irregular sampling visible**

    Preserve curve-specific sample times, inspect gaps, then make common-grid projection an explicit decision.

    [:octicons-arrow-right-24: Native irregular trajectories](guides/irregular-trajectories.md)

-   **Use sparse FDA instead of manufacturing dense curves**

    For genuinely sparse trajectories, preserve native observation times and use optional covariance UFPCA with PACE conditional-expectation scores.

    [:octicons-arrow-right-24: Sparse PACE FPCA](guides/sparse-irregular-fpca.md)

-   **Use sparse PACE when interpolation would invent most of the curve**

    Preserve native curve-specific times and delegate univariate sparse covariance estimation plus conditional scores to FDApy.

    [:octicons-arrow-right-24: Sparse PACE FPCA](guides/sparse-irregular-fpca.md)

-   **Ask whether the FPCs are reproducible**

    Bootstrap curves or participants, match component functions, inspect reconstruction error, and check whether one participant dominates the basis.

    [:octicons-arrow-right-24: Stability & influence](guides/stability-validation.md)

-   **Select dimension without leaking held-out trajectories**

    Refit FPCA inside each fold, keep repeated participant trials together, and make the minimum-RMSE or one-SE rule explicit.

    [:octicons-arrow-right-24: Component selection](guides/component-selection.md)

-   **Tune FPC count for an external outcome without leakage**

    Fit FPCA and scalar regression inside every training fold; use nested grouped CV when predictive performance is a scientific result.

    [:octicons-arrow-right-24: Predictive FPCA selection](guides/predictive-component-selection.md)

-   **Calibrate simultaneous uncertainty for FPC shape**

    Match/sign-align bootstrap FPCs and calibrate studentized maximum deviations over the observed grid, with explicit component-wise or familywise scope.

    [:octicons-arrow-right-24: Simultaneous FPC bands](guides/simultaneous-fpc-bands.md)

-   **Inspect uncertainty in FPC shape**

    Match and sign-align bootstrap components before interpreting pointwise variation in an estimated eigenfunction.

    [:octicons-arrow-right-24: FPC shape uncertainty](guides/component-uncertainty.md)

-   **Distinguish unstable axes from a stable eigenspace**

    Inspect adjacent eigengaps and principal-angle stability when FPC labels swap or rotate across resamples.

    [:octicons-arrow-right-24: Near-tied FPC subspaces](guides/subspace-stability.md)

-   **Infer the mean trajectory with the right sampling unit**

    Calibrate one observed-grid band across time and dimensions, using equal-weight participant means for repeated-trial designs.

    [:octicons-arrow-right-24: Simultaneous mean bands](guides/simultaneous-mean-bands.md)

-   **Flag unusual trajectories without auto-deleting them**

    Combine reconstruction, robust score-space distance, and participant-aware omission diagnostics. Review flags never become exclusions automatically.

    [:octicons-arrow-right-24: Outliers & influence](guides/outliers-influence.md)

-   **Treat timing deformation as data**

    Registration warpings can be analyzed with phase FPCA, and spatial FPCs can be compared before and after alignment.

    [:octicons-arrow-right-24: Phase FPCA](guides/phase-fpca.md)

</div>

## A functional gaze workflow

<div class="et-flow" markdown>
<span>native gaze</span><b>→</b><span>functional representation</span><b>→</b><span>explicit preprocessing</span><b>→</b><span>FPCA / registration</span><b>→</b><span>stability & diagnostics</span><b>→</b><span>scientific interpretation</span>
</div>

The package is designed around the principle that **the path to an FPC score is part of the estimand**. Missingness, time support, channel scaling, registration, basis projection, and resampling unit are therefore visible choices rather than invisible conveniences.

## Start from your research question

<div class="grid cards" markdown>

- **Where does gaze move over trial time?**  
  Use joint 2-D MFPCA.

- **Are sample times irregular across trials?**  
  Preserve them in an <code>IrregularTrajectorySet</code> before choosing a projection.

- **Would interpolation create much of the analyzed curve?**  
  Use sparse univariate covariance UFPCA with PACE scores rather than pretending the path was densely observed.

- **Would interpolation create most of each curve?**  
  Use univariate sparse covariance UFPCA with PACE conditional-expectation scores rather than manufacturing a dense trajectory.

- **Do stable participant strategies differ from trial fluctuations?**  
  Use multilevel FPCA.

- **Do viewers follow similar spatial routes at different times?**  
  Compare unregistered, registered, and phase representations.

- **How many components should I retain for reconstruction?**  
  Use leakage-safe reconstruction CV with the correct fold unit and an explicit selection rule.

- **How many FPC scores should predict an external outcome?**  
  Use outcome-tuned FPCA regression CV; use nested CV to estimate performance after selection.

- **Are my components stable enough to interpret?**  
  Use participant-aware bootstrap matching, reconstruction diagnostics, and descriptive component-shape envelopes.

- **Do FPC1/FPC2 rotate or swap while their span stays stable?**  
  Inspect retained eigengaps and bootstrap principal-angle subspace stability.

- **Is one participant or curve driving the basis?**  
  Use functional review diagnostics plus leave-one-group-out FPCA influence.

- **Does gaze allocation among AOIs evolve as a composition?**  
  Use simplex-aware compositional FPCA.

</div>

[Browse the tutorial gallery](tutorials/index.md){ .md-button .md-button--primary }
[Open the pre-registration checklist](methods/preregistration.md){ .md-button }

## Minimal 2-D analysis

    from eyetrajectoriespy import fit_mfpca, simulate_planar_trajectories

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

    print(fit.explained_variance_ratio)

## What the package refuses to hide

<div class="grid cards" markdown>

- **Missingness stays missing** until interpolation or exclusion is explicitly requested.
- **Smoothing is opt-in** because abrupt gaze transitions can be genuine.
- **Registration is opt-in** because latency can carry theory.
- **Irregular-to-grid projection is explicit** because overlap, union, and gap rules change the observed process.
- **Basis projection is explicit** because basis family and size constrain representable shape.
- **Bootstrap resampling unit is explicit** because repeated trials are not independent participants.
- **Provenance travels with transformations** so a result can be traced back to analytical choices.

</div>

!!! important "Not a replacement for event analysis"
    Whole-trajectory FDA answers different questions from fixation, saccade, AOI-transition, and latency analyses. eyetrajectoriespy complements those methods rather than replacing them.

## New in 0.12 development

- paired curve- or participant-level bootstrap for Gaussian scalar-on-function FPCR;
- FPCA/MFPCA and the scalar regression refitted together in every bootstrap replicate;
- functional slope uncertainty reconstructed in original trajectory coordinate units;
- fixed-target uncertainty for the fitted conditional mean response;
- explicit distinction between conditional-mean uncertainty and future-outcome prediction intervals;
- fixed component count across bootstrap replicates with no silent model-selection uncertainty;
- full-rank bootstrap-design checks with explicit failure instead of discarded replicates;
- no unnecessary FPC label matching for slope/mean-response targets.

## Added in 0.11 development

- bootstrap basis-resampling uncertainty for FPC scores of fixed target trajectories;
- training-curve or compatible external-target score projections;
- component matching and sign alignment before score comparison;
- participant-aware basis resampling for repeated trials;
- explicit compatibility checks for target grid, dimensions, coordinate system, and time unit;
- explicit exclusion of measurement-error, latent-curve, future-curve, preprocessing, and full downstream-model uncertainty claims.

## Added in 0.10 development

- matched-bootstrap uncertainty for FPCA eigenvalues and variance decomposition;
- component-wise or familywise studentized calibration within each spectrum metric;
- participant-aware resampling for repeated-trial designs;
- matched reference-FPC identity for individual eigenvalues/ratios;
- descending-rank semantics retained for cumulative explained variance;
- explicit no-clipping and no-automatic-retention-rule safeguards.

## Added in 0.9 development

- matched/sign-aligned bootstrap simultaneous FPC-shape uncertainty bands;
- observed-grid studentized maximum calibration;
- component-wise or familywise simultaneous scope;
- participant-aware resampling for repeated trials;
- optional analyst-supplied eigengap screen with explicit error/warn/ignore behavior;
- no default near-tie threshold and no continuous-domain coverage claim.

## Added in 0.8 development

- leakage-safe outcome-tuned FPCA regression component selection;
- Gaussian RMSE/MAE and binomial log-loss/Brier scoring;
- participant/group-aware predictive folds;
- explicit minimum-loss and one-standard-error selection;
- nested CV for performance after component-count tuning;
- convergence, separation, probability, covariate, and rank safeguards.

## Added in 0.7 development

- simultaneous studentized Gaussian multiplier bands for common-grid functional means;
- explicit curve versus equal-weight participant inference units;
- joint calibration over the observed time × functional-dimension grid;
- exact zero-variance handling and simplex-geometry guardrails;
- worked example plus reporting, preregistration, assumptions, limitations, and API guidance.

## Added in 0.6 development

- optional FDApy sparse functional interoperability;
- direct native-irregular → FDApy conversion without common-grid interpolation;
- covariance UFPCA with PACE conditional-expectation scores;
- explicit smoothing, tolerance, normalization, and backend provenance;
- sparse sampling diagnostics, score tables, plotting, reporting, and worked-example guidance.

## Added in 0.5 development

- adjacent retained-eigenvalue gap diagnostics with no automatic near-tie threshold;
- principal-angle comparison of FPC eigenspaces;
- normalized projection-operator distance;
- participant-aware bootstrap subspace stability;
- rotation-invariant interpretation guidance for close eigenvalues.

## Added in 0.4 development

- leakage-aware held-out FPCA reconstruction cross-validation;
- participant/group folds for repeated-trial designs;
- explicit minimum-RMSE and one-standard-error component-selection rules;
- matched, sign-aligned pointwise bootstrap FPC envelopes;
- dedicated reporting, interpretation, limitations, and worked-example guidance.

## Added in 0.3 development

- FPCA reconstruction + robust score-space anomaly screening;
- participant-aware leave-one-group-out FPC influence;
- optional scikit-fda functional boxplot and magnitude-shape screening;
- explicit review-flag versus exclusion guidance;
- sparse-irregular FPCA decision guidance.

## Added in 0.2 development

- native irregular functional trajectory objects;
- explicit common-overlap/union grid construction;
- curve- and participant-level bootstrap FPC stability;
- integrated reconstruction diagnostics;
- phase FPCA and landmark timing tables;
- registered-versus-unregistered FPC sensitivity;
- provenance-preserving B-spline/Fourier interoperability;
- expanded tutorial, pre-registration, and failure-case guidance.

For manuscript preparation, use the [reporting checklist](methods/reporting.md), [assumptions and diagnostics](methods/assumptions.md), and [limitations](methods/limitations.md).
