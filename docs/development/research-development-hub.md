# Research development — experimental methods and evidence

!!! warning "Research site ≠ published release"
    **The current published stable package is eyetrajectoriespy 1.1.0.** These pages document **unreleased 1.2 research** from separate draft GitHub pull requests. **The methods are not necessarily present in the installed stable package or in `main`, and statistically unqualified inference must not be used as validated hypothesis testing.** Documentation publication does not merge research implementations or authorize a 1.2 release.

This research library preserves **successful, inconclusive and negative** results, original source figures, reproducible simulation evidence and open scientific gates. Green CI verifies engineering contracts and completion of documented computations; it is not a scientific inference guarantee.

[Scientific evidence dashboard](research-scientific-dashboard.md) · [Original figures](research-original-figures.md) · [Reproducibility from source](research-reproducibility.md) · [Full source evidence matrix](research-evidence-matrix.md)

## Research programmes

| Programme | Research capabilities under investigation | Scientific boundary |
|---|---|---|
| F1 sparse group inference | Participant-level sparse-PACE group testing; 6,000 actual fitted tests | Tested null size encouraging; sensitivity to moderate effects limited; broader exchangeability and covariance assumptions unqualified |
| F2 gaze measurement quality | Target-based error, precision, sampling loss, coordinate/unit provenance | Target, participant/session and hardware traceability require further validation |
| F3 Eye-Tracking-BIDS | Schema checks and eye-tracking stream provenance | Official validator, real BIDS datasets and multi-stream interoperability pending |
| F4 constrained AOI FPCA | Compositional log-ratio and projection approaches | Independent constrained estimator and uncertainty not validated |
| F5 functional change-point inference | Block/AR(1)/AR(2) nulls, independently trained nuisance estimates and stress tests | AR(2), MA(1), baseline-size and nonstationary null failures; not a calibrated unknown-dependence test |
| F6 weighted functional geometry | Unit-aware weights and quadrature | Independent reconstruction, weighting and scale sensitivity pending |
| B5–B10 Bayesian layer | Diagnostic evidence, learned B6/B7 population covariance, research prediction and specialized models | Poor native covariance mixing, small posterior reference study and absent rank-based SBC/coverage qualification |

See [F1–F6 method inventory](f1-f6-scientific-expansion.md), [experimental API contracts](research-method-api.md), and [B5–B10 development overview](bayesian-research-programme.md). **None of these pages promotes new stable root-level APIs.**

## R84: independent recovery of missing synthetic Y and conditional selection identification (21 October 2026)

R83 found that varying assumed δ on the same observed sample does not identify the missingness mechanism. R84 newly asks whether *genuinely additional* missing-response measurements help estimate one prespecified outcome-dependent selection parameter. Thirty-two NEW independent primitive blocks per fixed design/support/variance cell generated 256 complete X/Y conditions, 512 paired MAR/MNAR masks and **1,536** 0%/25%/50% randomly validated source records. Original [science workflow #39581392688](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39581392688) **12/12 PASS**, independent [R84-A exact real archive #39582618020](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39582618020) **4/4 PASS**. At zero recovery δ is not estimated; at positive recovery MAR source means near 0 and MNAR means near 1.0 (true generator 1.1), but error is not universally improved by more recovery and the visible-only pilot remains model dependent. This does **not** imply feasible gaze remeasurement or valid functional 90% bands.

[R84 full scientific article](../articles/w3-external-validation-mnar-identification-r84.md) · [Identification methods companion](../articles/external-gaze-validation-identifiability.md) · [Original numeric evidence/plots](w3-r84-validation-identification-evidence-ledger.md). Issues #289/#296 stay OPEN, main inference code unchanged, v1.2 release HOLD.

## R83: independently audited nonidentified MNAR assumption sensitivity (21 October 2026)

R83 freezes **five externally supplied outcome-dependent selection coefficient assumptions** δ=-1.1, -.55, 0, .55, 1.1 on the same visible source-mask data, with a separately labeled **simulator-only true-propensity oracle** unavailable to field analysts. The 32 NEW independent generating blocks per fixed condition yield **256 X/Y source conditions, 1,024 paired masks and 3,328 analysis configurations**, not 3,328 independent experiments. [Original science #39575847765](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39575847765) **12/12 PASS**, independently coded [R83-A actual original #39576738539](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39576738539) **4/4 PASS**. In the adverse MNAR condition, δ endpoint slope spread on jointly estimable grid points is **.00453 curves / .00841 participants**, but no MNAR parameter is identified; no general missingness-adjusted 90% confidence method follows.

[Read R83 source-grounded study](../articles/w3-mnar-selection-sensitivity-r83.md) · [Observed-only assumption methods](../articles/independent-gaze-MNAR-sensitivity-and-selection.md) · [Original figure and immutable evidence ledger](w3-r83-mnar-sensitivity-evidence-ledger.md). Issues #289/#296 OPEN, protected main estimator unchanged, v1.2/PyPI release HOLD.

## R82: independently audited observation-process feasibility (21 October 2026)

The next prospective falsification now changes **the observation process**, not the complete-source error covariance. Thirty-two new independent primitive source blocks per condition generate 256 true Student-t5+skew synthetic X/Y source conditions, each tested under paired **complete, MCAR, recorded-input MAR and hidden-outcome-dependent MNAR** masks: **1,024 source observation-process evaluations**. Stable public regression still **refuses NaNs**. A separate descriptive available-case pointwise OLS demands n≥8 independent units and surviving both ±4 predictor anchors at every time/coordinate location; it does not claim any band or correction. [Original source workflow #39571308151](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39571308151) **12/12 science PASS** and [independent R82-A #39572315409](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39572315409) **4/4 actual original archive PASS**. In the two-anchor curve heteroskedastic MNAR source, **83.1% sample retention** coexists with **33.56/62 refused grid positions**. Numerical evidence is verified but cannot justify 90% MNAR-adjusted bands.

[R82 full scientific article](../articles/w3-response-dependent-gaze-loss-r82.md) · [MCAR/MAR/MNAR methods guide](../articles/independent-gaze-loss-and-pointwise-feasibility.md) · [Original source and three plots](w3-r82-observation-process-evidence-ledger.md). W3 #289/#296 OPEN, protected main inference unchanged, v1.2 release HOLD.

## R81: independent source-audited rare skewed unit contamination (20 October 2026)

The R81 protocol froze a combined **unit-wise shared Student-t5 radial** and centered rare Bernoulli asymmetric event (probability .08, amplitude .16, signed time profile), while keeping original W3, residual HC3 and previously fixed λ=.25/.50 covariance regularization unchanged. The known generating reference was correctly recomputed as a source-conditional **non-Gaussian t5 plus skew mixture**, with true variance adjusted for the Bernoulli shock. Original [R81 #39490888383](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39490888383) **12/12 science PASS**; independent [R81-A #39491187099](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39491187099) **4/4 real source replay PASS**, verifying **256/256 source cases, 0 refusals and all 1,278,720 raw maximum arrays**. Adverse two-extreme-unit heteroskedastic whole 31×2 slope inclusion under frozen λ=.50 was **24/32 independent curves and 24/32 repeated participants**, still not general nominal-90%-calibrated inference.

[Read scientific results and plots](../articles/w3-skew-unit-contamination-r81.md) · [Methods explanation](../articles/independent-unit-skew-contamination-and-simultaneous-inference.md) · [Original numerical source ledger](w3-r81-skewed-unit-evidence-ledger.md). W3 blockers #289/#296 OPEN, protected main estimator unchanged, release 1.2 HOLD.

## R80: independently audited unit-level Student-t5 heavy-tail stress (20 October 2026)

R80 prospectively preserved the R79 Gaussian *conditional covariance* and the two frozen source-observable HC3 covariance regularizations while adding one **Student-t5 radial scale per independent observation unit**, shared across all 62 grid coordinates and participant trials. The source-known comparison was correctly changed to a non-Gaussian **independent-unit conditional mixture**, not a Gaussian reference. [Original science #39487449656](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39487449656) passed **12/12** and [independent R80-A #39487811433](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39487811433) passed **4/4 actual-original-archive jobs**, verifying **256/256 source cases, zero refusals, 1,278,720 conditional maxima**. In the adverse two-anchor design, λ=.50 whole-function inclusion was **23/32 independent curves, 24/32 repeated participants**, not nominal-90%-qualified inference.

[Read the R80 scientific article and original plots](../articles/w3-student-t5-heavy-tail-inference-r80.md) · [Student-t source methods companion](../articles/independent-unit-student-t-functional-uncertainty.md) · [Exact original evidence ledger](w3-r80-student-t5-evidence-ledger.md). Inference blockers #289/#296 remain OPEN, v1.2 RELEASE HOLD.

## R79: independently audited nonseparable coordinate covariance stress (20 October 2026)

Original R79 changed the Gaussian generating law's cross-coordinate correlation to **q(t)=.15+.65t** while keeping trial temporal AR1 rho .72, within-trial time-varying scale, and the two fixed HC3 regularization candidates unchanged. [The original experiment](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39483619384) passed **12/12 scientific jobs**; the mandatory [R79-A independent source replay](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39483939543) passed **4/4**, independently verifying **256/256 source cases, zero refusals and all 1,278,720 raw reference maxima**. Under adverse two-anchor heteroskedasticity, λ=.50 attained **24/32 full-grid curve inclusions** and **20/32 repeated-participant inclusions**, still well below nominal 90%.

[Read the R79 methods/results article](../articles/w3-nonseparable-coordinate-covariance-r79.md) · [Understand nonseparability](../articles/understanding-nonseparable-gaze-covariance.md) · [Open all three original figures](w3-r79-nonseparable-covariance-evidence-ledger.md). Inference #289 and missingness #296 remain open, version 1.2 unreleased.

## R78: independent temporal covariance falsification and three original plots (20 October 2026)

R78 prospectively held both previously tested HC3 covariance-shrinkage strengths fixed and replaced within-trial independent Gaussian innovations with **time-varying Gaussian AR(1)** (rho .72). The original experiment passed **12/12** science jobs and the separately implemented R78-A passed **4/4 actual-source audit jobs**, independently reproducing **256 original source cases, zero refusals and 1,278,720 maximum-statistic values**. In the two-anchor predictor-heteroskedastic setting, full-grid inclusion under frozen λ=.50 was **22/32 independent curves** and **19/32 repeated-participant datasets**. This is **not** generally nominal-90%-calibrated inference, and it says nothing about MNAR gaze loss.

[Read R78 original study](../articles/w3-temporal-covariance-robustness-r78.md) · [Read independent source-audit interpretation guide](../articles/interpreting-w3-coverage-and-source-audits.md) · [View the original vector figure ledger](w3-r77-r78-temporal-covariance-figure-ledger.md). Blockers #289/#296 remain open; no inference code or stable package release change.

## R77: independent source-audited covariance regularization stress (20 October 2026)

[R77's prospective HC3 covariance shrinkage research](../articles/covariance-regularization-and-w3-coverage.md) retained 256 fully observed new Gaussian source cases (32 independent primitive generating blocks per condition), with **12/12 original scientific jobs passed** and **4/4 independent original-source audit jobs passed**, reproducing all **1,278,720 conditional maximum-statistic values**. Two fixed λ=.25/.50 candidates improved observed slope truth inclusion under extreme leverage and heteroskedasticity but **did not establish calibrated nominal-90% inference**. The original W3 issue #289 and response-dependent loss issue #296 stay open. [View the two original R77 scientific figures](research-original-figures.md).

## New W3 research articles and original evidence plots (20 October 2026)

**Numerical verification is not interval calibration.** R71–R75 independent source audits expose substantial undercoverage of nominal-90% full-grid functional slope bands under high leverage and heteroskedasticity. R76 and R76-A independently reconstructed **512/512 complete source cases and 1,534,464 maximum-statistic values**; increasing independent extreme predictor support coincided with improved estimated-HC3 whole-band truth inclusion in the tested Gaussian setting, but does not yield a qualified 90% procedure.

[**Why W3 simultaneous bands under-cover**](../articles/when-w3-simultaneous-bands-undercover.md) · [**R76 leverage support and lower-tail SE evidence**](../articles/how-independent-leverage-support-affects-coverage.md) · [**Original W3 figure and source-audit gallery**](w3-r70-r76-evidence-plot-gallery.md)

**Research blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain open.** Their research implementations are separate draft PRs; publishing these articles and static SVGs to the website does not merge an estimator or release version 1.2.

## New workflow-level scientific evidence

- [W3 independent known-truth functional regression benchmark](w3-functional-regression-known-truth-results.md): 24 generating blocks, 48 workflow fits, independent OLS-oracle agreement within numerical precision, transparent participant-versus-trial accounting, and original source-derived recovery SVG. This is an implementation/recovery validation under simulated designs, **not** inferential calibration or authentic data.

## Evidence worth reading first

- [F1 — 6,000 full sparse-PACE null/power fits](f1-high-precision-native-null-power.md): failure-inclusive scenario results and a limitation-oriented power assessment.
- [B6/B7 — independent PyMC/NUTS posterior](b6-b7-identifiable-reference-diagnostics.md): identifiable mean and covariance diagnostics, raw loading sign ambiguity and inadequate native ESS.
- [B6/B7 — nine-fit longer-chain Gibbs versus independent NUTS](b6-b7-longchain-identified-covariance-geometry.md): source-verified B6, B7 paired and B7 asynchronous covariance mixing diagnostics, original figure and failure-inclusive reference evidence. All native covariance chains fail exploratory mixing; both B7 NUTS runs pass the diagnostic screen without establishing nominal coverage.
- [B6/B7 — six four-chain independent NUTS references (R1)](b6-b7-four-chain-nuts-r1-reference.md): two fresh datasets per design; all identified population diagnostics passed a prespecified *exploratory* mixing screen, with zero divergences, and original evidence/figure retained. Rank-two validity, simulation-based calibration and posterior interval coverage remain unqualified.
- [B6/B7 — rank-two independent Gaussian/Woodbury likelihood identity](b6-b7-rank2-marginal-mathematics.md): paired, asynchronous, rotation and near-tied dense Gaussian/Woodbury identities verified; this mathematical prerequisite alone did not check the PyMC graph.
- [B6/B7 — actual rank-two PyMC full log posterior and gradients](b6-b7-rank2-pymc-r2-research-protocol.md): four tested mathematical configurations pass independent dense-log-posterior and 30-gradient numerical checks; actual NUTS sampling, rank SBC and interval coverage remain *unqualified*.
- [B6 — first independent-NUTS prior-SBC pilot](b6-rank1-prior-sbc-stage0.md): four independent datasets, eight primary truth ranks, one diagnostic-screen failure, and original source visualization; formal SBC uniformity and interval coverage remain unqualified.
- [B6 — full-budget refit of the *same* problematic SBC dataset (R2)](b6-rank1-sbc-r2-same-dataset-evidence.md): all six population-functionals passed after longer sampling on the identical dataset (worst R-hat improved from 1.0158 to 1.0053), but this is not an additional independent SBC replication.
- [B6/B7 — first actual rank-two NUTS paired versus asynchronous pilot (R3)](b6-b7-rank2-four-chain-nuts-r3-evidence.md): two actual four-chain posterior fits, paired screen pass and asynchronous **mean-functionals screen failure** (6/15); graph correctness does not establish rank-two computational reliability or posterior coverage.
- [B6/B7 — joint-loading elliptical-slice experiment](b6-b7-joint-score-marginal-loading-ess.md): a valid research transition that **failed to improve covariance mixing consistently**.
- [F5 — independent-baseline unknown AR(1)](f5-independent-baseline-unknown-phi.md), [training baseline sensitivity](f5-baseline-size-nuisance-sensitivity.md) and [AR(2)/MA(1)/nonstationarity falsification](f5-independent-baseline-ar2-model-falsification.md).
- [Research figures](research-original-figures.md): original checked-in scientific SVGs, including negative results.

## Qualification and governance

**Currently blocked:** [Bayesian population uncertainty #255](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/255) and [F5 dependent-null inference #256](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/256). Other F/B/D methods remain under independent scientific review. A green branch matrix must not be reinterpreted as approval to merge experimental estimators, close scientific issues, or release 1.2.

**Evidence policy:** Every numerical statement should identify the underlying GitHub workflow, dataset count, unit of independence, failure count, comparison condition and interpretation limits. Simulation evidence is not a substitute for independent eye-tracking recordings, and illustrations derived from simulations must be labelled accordingly. See [the scientific dashboard](research-scientific-dashboard.md) for original artifact IDs and links.
