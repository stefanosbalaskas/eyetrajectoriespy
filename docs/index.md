---
title: Functional gaze trajectories, without hidden analytical decisions
---

<div class="et-hero" markdown>
<div class="et-kicker">eyetrajectoriespy 0.3 · continuous eye-tracking FDA</div>

# Model the viewing process, not only its summaries

eyetrajectoriespy provides a vendor-neutral scientific layer for continuous gaze paths, multivariate FPCA, native irregular trajectories, repeated-trial functional decomposition, phase analysis, compositional AOI trajectories, and explicit validation of component stability.

<span class="et-pill">2-D x(t), y(t)</span><span class="et-pill">native irregular grids</span><span class="et-pill">FPCA / MFPCA</span><span class="et-pill">bootstrap stability</span><span class="et-pill">outlier / influence review</span><span class="et-pill">multilevel</span><span class="et-pill">phase</span><span class="et-pill">elastic SRVF</span>
</div>

<div class="grid cards" markdown>

-   **Choose the scientific object first**

    Decide whether the object is a planar path, irregularly sampled process, repeated-trial process, AOI composition, registered amplitude, or phase function before choosing an estimator.

    [:octicons-arrow-right-24: Analysis decision map](concepts/decision-map.md)

-   **Keep irregular sampling visible**

    Preserve curve-specific sample times, inspect gaps, then make common-grid projection an explicit decision.

    [:octicons-arrow-right-24: Native irregular trajectories](guides/irregular-trajectories.md)

-   **Ask whether the FPCs are reproducible**

    Bootstrap curves or participants, match component functions, inspect reconstruction error, and check whether one participant dominates the basis.

    [:octicons-arrow-right-24: Stability & influence](guides/stability-validation.md)

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

- **Do stable participant strategies differ from trial fluctuations?**  
  Use multilevel FPCA.

- **Do viewers follow similar spatial routes at different times?**  
  Compare unregistered, registered, and phase representations.

- **Are my components stable enough to interpret?**  
  Use participant-aware bootstrap matching plus reconstruction diagnostics.

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

## New in 0.3 development

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
