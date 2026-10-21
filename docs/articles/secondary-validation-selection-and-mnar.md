---
title: The validation sample has its own missingness mechanism
description: R85 methods companion on selective ascertainment and limits of recovery-propensity corrections
---

# The validation sample has its own missingness mechanism

**Methods companion · 21 October 2026 · R85**

The [R84](w3-external-validation-mnar-identification-r84.md) simulator recovered a random fraction of otherwise missing synthetic gaze responses and demonstrated conditional estimation of one parametric MNAR selection coefficient. The word *random* was a crucial modeling assumption: an external instrument or validation procedure could itself fail to measure outcomes in a way related to predictors or the unobserved outcome.

The [independently audited R85 experiment](w3-biased-validation-mnar-r85.md) isolates this second selection process, while leaving the original source and its first-stage MAR/MNAR mechanism intact.

!!! warning "Two observation mechanisms require two separate justifications"
    The **original gaze-loss mechanism** determines which samples the eye tracker retains. The **external validation mechanism** determines which originally missing outcomes are subsequently ascertained. Correcting only the first while incorrectly treating the second as random can distort an estimated outcome-selection parameter. All R85 outcomes are synthetic. No real external gaze recovery is demonstrated, and no confidence band is validated.

## Independent, recorded-covariate-selective and outcome-selective recovery

R85 generates 256 new complete X/Y source conditions from 32 independent primitive blocks per fixed cell and produces paired original MAR and MNAR masks. Then three possible recovery laws share one external random-uniform stream: constant 25% recovery, recovery depending on recorded x/time, and recovery depending on an originally hidden gaze residual.

The source models distinguish what is knowable: a random validation protocol may justify a known sampling fraction; a recorded-x/time recovery protocol can have a known probability if its design is truly enforced and logged; but a validation probability depending on the *unseen true residual* requires an extra identifying model or information. R85's exact version of that probability is available only to the complete-data generator.

## Why five comparisons are needed

- **Independent known** — tests the R84 assumption that 25% of originally missing outcomes can be recovered independently, with inverse recovery probability 4.
- **Recorded naïve versus recorded correct** — uses the **same recovered values** twice and changes only whether weighting uses constant .25 or the stipulated known recorded-covariate probability.
- **Latent naïve versus latent oracle** — likewise uses the **same recovered values**, but compares the unjustified constant weight with a privileged simulator-only propensity based on true conditional mean and recovered Y.

Thus R85 separates actual changes in who is measured from hypothetical changes in how those measurements are weighted. In all five fits, the conditional-mean pilot is obtained from originally visible gaze alone; unrecovered Y never enters the score. The participant, not its three correlated trials, is the independent scientific sampling unit.

![Five recovery strategies under the same original MNAR source](../assets/research/w3-r85-selective-validation-mnar-delta.svg)

*Figure 1.* In the primary adverse source, outcome-selective recovery assumed random produces higher mean fitted original MNAR δ than the correctly known but **not field-available** source oracle.

## The MAR falsification matters

![Naïve outcome-selective secondary recovery creates a positive original selection coefficient from an originally MAR source](../assets/research/w3-r85-mar-false-positive-validation-bias.svg)

*Figure 2.* The original source has **true MAR δ=0**, but naïve weighting of an outcome-selectively validated sample produces source-mean δ about **+.664 for independent curves** and **+.630 for repeated participants**. True-propensity source-oracle weighting yields source means near zero. These values are **not formal hypothesis-test false-positive rates**.

This failure can occur even when the data analysis correctly recognizes that external recovery provides genuinely new measurements. The new measurements themselves may be a selected sample of the missing outcomes.

## Why the source oracle is not a released correction

![Naïve outcome-selective validation versus privileged true propensity oracle across all source conditions](../assets/research/w3-r85-eight-cell-oracle-versus-naive-errors.svg)

*Figure 3.* The independent audit reproduces the marked source-error differences across the eight prospective source cells. Correct weighting depends on knowing the recovery probability, not simply on optimizing a regression after collecting additional values.

An external validation technology that preferentially succeeds under certain gaze positions, movement speeds, calibration quality, occlusion types or physiological states may introduce selection. A statistical correction requires justified information about that second process. R85 provides **no field estimates of those mechanisms**, no demonstrated auxiliary sensor, no nonparametric identification of the latent recovery law and no validated uncertainty.

Even the recorded-x/time corrected method does **not** always minimize realized finite-sample absolute error. The original conditional-mean pilot remains estimated from selected visible outcomes, and the source sample contains only 32 independent generating blocks per fixed condition. "Correct propensity" here means correct **for the stipulated synthetic recovery law**, not a complete proof of consistency of the entire two-stage estimation procedure.

## Provenance and release boundary

Original [R85 numerical study #39629520741](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39629520741) completed 12/12 scientific jobs. Separately coded [R85-A actual original archive #39630863879](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39630863879) completed 4/4 independent audit jobs, replaying 256 source X/Y conditions, 512 paired original masks and 2,560 recovered-sample estimation records.

The result is a **second-stage selection falsification**, not a missing-data-adjusted function-on-scalar regression or 90% confidence-band validation. Stable package 1.1.0 is unchanged, W3 scientific blockers #289 and #296 remain open, and version 1.2/PyPI release is still withheld.

[Full R85 scientific results](w3-biased-validation-mnar-r85.md) · [Complete original and independent evidence](../development/w3-r85-selection-validation-evidence-ledger.md) · [Prior R84 external outcome validation](w3-external-validation-mnar-identification-r84.md)
