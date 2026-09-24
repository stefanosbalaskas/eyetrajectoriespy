---
title: Functional gaze trajectories, without hidden analytical decisions
---

<div class="et-hero" markdown>
<div class="et-kicker">eyetrajectoriespy 0.35 · continuous eye-tracking inference</div>

# Model the viewing process, not only its summaries

eyetrajectoriespy provides a vendor-neutral scientific layer for continuous gaze paths, multivariate FPCA, native irregular trajectories, repeated-trial functional decomposition, phase analysis, compositional AOI trajectories, and explicit validation of component stability.

<span class="et-pill">2-D x(t), y(t)</span><span class="et-pill">function-on-scalar inference</span><span class="et-pill">Fréchet + audited DTW</span><span class="et-pill">native irregular grids</span><span class="et-pill">sparse PACE FPCA</span><span class="et-pill">FPCA / MFPCA</span><span class="et-pill">LaTeX contracts</span><span class="et-pill">reproducible plots</span><span class="et-pill">grouped reconstruction CV</span><span class="et-pill">bootstrap stability</span><span class="et-pill">eigenspace stability</span><span class="et-pill">mean-band inference</span><span class="et-pill">outlier / influence review</span><span class="et-pill">multilevel</span><span class="et-pill">phase</span><span class="et-pill">elastic SRVF</span>
</div>

<div class="grid cards" markdown>

-   **Estimate when experimental predictors change a functional gaze response**

    Fit observed-grid function-on-scalar models, retain explicit participant/curve inference units, and calibrate wild-bootstrap simultaneous coefficient bands without hidden smoothing or trial pseudo-replication.

    [:material-chart-bell-curve: Function-on-scalar guide](guides/function-on-scalar.md)

-   **Read the equations behind the API**

    Follow implementation-matched LaTeX from quadrature weighting and FPCA through wild-bootstrap studentization, max-(|t|) testing, Monte Carlo precision, and split conformal p-values.

    [:material-function-variant: Mathematical reference](methods/mathematical-reference.md)

-   **Browse reproducible scientific figures**

    Every gallery figure is generated from seeded synthetic data by the public plotting API during documentation CI.

    [:material-chart-line: Visual gallery](methods/visual-gallery.md)

-   **Find the equation for a public function**

    Query the package registry or browse the generated function → equation index. Every registered function maps to LaTeX, an expanded reference anchor, and an explicit scope boundary.

    [:material-function: Function → equation index](reference/function-equation-index.md)

-   **Follow the analysis decision flow**

    Use rendered workflow diagrams to move from sampling structure and scientific object to representation, diagnostics, inference, equations, and plots.

    [:material-family-tree: Workflow atlas](methods/workflow-atlas.md)

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

    Combine reconstruction, robust score-space distance, participant-aware omission diagnostics, and split-conformal p-values for genuinely new curves. Review flags never become exclusions automatically.

    [:octicons-arrow-right-24: Outliers & influence](guides/outliers-influence.md)

-   **Calibrate anomaly evidence for new trajectories**

    Fit the FPCA reference on a proper-training set, reserve a disjoint calibration set, and convert reconstruction or score-space nonconformity into marginal conformal p-values.

    [:octicons-arrow-right-24: Conformal FPCA anomaly review](guides/conformal-fpca-anomaly.md)

-   **Treat timing deformation as data**

    Registration warpings can be analyzed with phase FPCA, and spatial FPCs can be compared before and after alignment.

    [:octicons-arrow-right-24: Phase FPCA](guides/phase-fpca.md)

-   **Compare ordered gaze paths without hiding the alignment rule**

    Use discrete Fréchet for bottleneck separation or DTW for cumulative elastic index alignment, now with explicit symmetric1/symmetric2 step weighting, optional N+M normalization, coordinate weights, and no hidden time/preprocessing claims.

    [:octicons-arrow-right-24: DTW guide](methods/dynamic-time-warping.md) · [Discrete Fréchet guide](methods/discrete-frechet.md)

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

- **How does the path bend and turn over trial time?**  
  Use continuous heading, signed curvature, and turning-rate functions with explicit low-speed handling.

- **Are sample times irregular across trials?**  
  Preserve them in an <code>IrregularTrajectorySet</code> before choosing a projection.

- **Would interpolation create much of the analyzed curve?**  
  Use sparse univariate covariance UFPCA with PACE scores rather than pretending the path was densely observed.

- **Do stable participant strategies differ from trial fluctuations?**  
  Use multilevel FPCA.

- **Do viewers follow similar spatial routes at different times?**  
  Compare unregistered, registered, and phase representations.

- **Are two ordered paths geometrically similar after monotone index alignment?**  
  Use discrete Fréchet for worst coupled separation or DTW for cumulative alignment cost; keep a time-preserving analysis when latency matters.

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
[Open the visual gallery](methods/visual-gallery.md){ .md-button }
[Read the equations](methods/mathematical-reference.md){ .md-button }
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

## New in 0.24 development

- `windowed_rqa_trajectory_set()` turns explicitly configured sliding-window RQA summaries into native functional trajectories across source curves;
- full per-curve window tables remain attached, preserving solved radii and window-level diagnostics rather than flattening away the RQA audit trail;
- overlap, source/functional time support, edge spans, trailing-tail handling, metric units, and the non-independence of window rows are explicit provenance;
- target-recurrence-rate mode cannot silently turn its controlled recurrence density into RR as a downstream functional outcome;
- undefined RQA metrics fail closed by default or remain explicit `NaN` under an opt-in keep policy; they are never zero-filled or interpolated;
- the new derived `TrajectorySet` enters the existing FPCA/MFPCA/regression ecosystem without a special adapter;
- evidence wording now distinguishes direct eye-movement RQA and LLE precedent from genuinely experimental return-map work.
## New in 0.23 development

- explicit multivariate delay-coordinate reconstruction with diagnostic-only AMI/autocorrelation and false-nearest-neighbor curves;
- sparse recurrence/RQA, full-window time-varying RQA, and cross-recurrence analysis with fixed-radius or target-recurrence-rate contracts;
- Rosenstein nearest-neighbor local divergence and largest-Lyapunov estimation with an analyst-declared fit interval and retained fit diagnostics;
- deterministic IAAFT surrogate nonlinearity testing with plus-one Monte Carlo p-values and no silent failed-surrogate replacement;
- experimental Poincare-section / local return-map stability with an explicit warning that empirical Jacobian eigenvalues are not classical Floquet multipliers;
- twelve-figure deterministic documentation gallery, nonlinear worked examples, equations, assumptions, limitations, reporting guidance, and public API reference.

## New in 0.22 development

- public `MathematicalContract` registry linking scientific functions to implementation-matched LaTeX, stable documentation anchors, and scope statements;
- deterministic GitHub and website function → equation indexes generated from that registry and checked for drift in CI;
- a Mermaid workflow atlas covering representation choice, FPCA validation, Gaussian FPCR inference branches, and the function → equation → figure documentation path;
- visual gallery expanded from five to eight deterministic SVG outputs, adding FPCA variance, registration displacement, and fixed-family wild-bootstrap testing;
- executable and worked examples showing contract lookup by function/key and tidy registry export;
- public API, homepage, tutorial gallery, README, and documentation validation updated so formulas are discoverable from code as well as prose.

## New in 0.21 development

- implementation-matched LaTeX mathematical contracts in both the GitHub repository and the methods site;
- deterministic SVG plots generated from the real public plotting API during documentation CI;
- a visual gallery connecting each figure to its method, worked example, API, and equation;
- MathJax re-typesetting compatible with instant site navigation;
- documentation contract checks for nav targets, mathematical API mappings, gallery assets, and exported API references;
- an executable numerical example that checks selected equations against package calculations.

## New in 0.20 development

- finite-bootstrap Monte Carlo precision diagnostics for fixed-family wild-bootstrap tests;
- target-wise, maxT-adjusted, and global exceedance counts recovered from the exact retained root matrix;
- raw r/B tail estimates, plug-in binomial MCSEs, and Clopper-Pearson exact intervals;
- conservative decision-stability flags relative to the already reported alpha-level decision;
- no new multiplier draws, no refits, and no changes to the configured 0.19 p-values or rejection indicators;
- explicit boundary between simulation precision and scientific sampling uncertainty, plus no sequential-stopping or stronger-FWER claim.

## Added in 0.19 development

- explicit two-sided tests for fixed Gaussian FPCR centered projections against scalar or target-specific null values;
- target-wise bootstrap tail probabilities from each stored studentized-root distribution;
- single-step maxT-adjusted probabilities from the replicate-wise maximum across the declared family;
- complete-family global max-statistic test from the same joint root matrix;
- conservative plus-one Monte Carlo correction by default, with raw empirical exceedance available explicitly;
- exact reuse of the certified heteroscedastic wild-bootstrap roots with no second FPCA fit or resampling run;
- explicit boundary: no null-enforced resampling and no strong-FWER claim for arbitrary subset nulls without additional subset-pivotality conditions.

## Added in 0.18 development

- familywise simultaneous intervals across a predeclared fixed-target FPCR family;
- one maximum absolute studentized root per bootstrap replicate across all declared targets;
- exact reuse of the 0.16/0.17 wild-bootstrap root matrix with no second FPCA fit or bootstrap;
- retained same-level target-wise critical values for transparent multiplicity comparison;
- exact reduction to the target-wise calibration when the family contains one target;
- explicit scope boundary: fixed target projections only, not future outcomes, clustered rows, unlisted targets, or component-selection uncertainty.

## Added in 0.17 development

- shared-multiplier wild-bootstrap scans over consecutive inference truncations h;
- fixed residual/pseudo-truth truncation k=g with all candidate h>=g;
- retained interval centers, widths, limits, heteroscedastic SEs, critical values, and studentized roots for every target × h;
- stabilized-volatility selection using analyst-supplied absolute width and center thresholds;
- explicit paper run parameter r, requiring r+1 consecutive stable transitions;
- earliest qualifying h selected separately per target;
- no hard-coded 0.01 threshold and no silent largest-h fallback when stability is absent.

## Added in 0.16 development

- fixed-regressor multiplier wild-bootstrap inference for centered Gaussian FPCR target projections under heteroscedastic response errors;
- explicit k residual truncation, g=k bootstrap pseudo-truth, and h>=g inference truncation;
- standard-normal or mean-zero/unit-variance Mammen two-point multipliers;
- bootstrap-level heteroscedastic studentization recomputed in every pseudo-sample;
- fixed FPCA/MFPCA basis during wild resampling;
- explicit rejection of declared repeated/clustered unit IDs;
- target-wise symmetrized intervals only: no future-outcome or simultaneous-target claim.

## Added in 0.15 development

- marginal split-conformal anomaly p-values for new common-grid functional trajectories;
- explicit proper-training, calibration, and target partitions;
- proper-training-only FPCA/MFPCA reference fitting;
- reconstruction-RMSE or explicitly configured score-space Mahalanobis nonconformity;
- conservative tie handling and visible minimum attainable p-value;
- review flags that never become automatic exclusions;
- curve-level exchangeability and clean-reference assumptions recorded in provenance;
- no calibration-conditional adjustment, multiple-testing correction, or FDR claim in this first conformal tranche.

## Added in 0.14 development

- future observed scalar-outcome prediction intervals for fixed Gaussian FPCR target trajectories;
- exact reuse of the paired-bootstrap conditional-mean predictions from the 0.12 FPCR uncertainty object;
- independent centered empirical residual draws added to each bootstrap mean prediction;
- retained residual pool and sampled residuals for auditability;
- deterministic seeded residual resampling;
- explicit exchangeable/common residual-distribution assumption;
- no heteroscedasticity-robust, simultaneous-target, or joint-target coverage claim.

## Added in 0.13 development

- studentized maximum-deviation bands for reconstructed Gaussian FPCR slopes;
- exact reuse of the paired-bootstrap slope replicates from the 0.12 regression-inference object;
- global scope across the full observed time × functional-dimension grid;
- dimension scope across observed time separately within each functional dimension;
- exact zero-variance handling without artificial epsilon inflation;
- explicit observed-grid-only coverage semantics;
- explicit distinction from the operator-scaled FPCR significance test in recent theory.

## Added in 0.12 development

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
