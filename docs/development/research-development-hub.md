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
