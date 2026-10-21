---
title: When missing gaze makes functional regression unestimable
description: Independently audited R82 complete, MCAR, MAR and MNAR observation-process diagnostics
---

# When missing gaze makes functional regression unestimable

**Scientific research article · 21 October 2026 · Original R82 and independent R82-A audit**

!!! danger "Observation-process diagnosis, not missingness-robust inference"
    This study concerns synthetic data and deliberately naive pointwise available-case OLS. It does **not** estimate an MNAR correction, impute data, perform inverse-probability weighting, derive a confidence band, or validate general nominal-90% inference. The stable package's function-on-scalar model **correctly refuses missing trajectories**. The source and audit implementations remain in research [PR #420](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/420) and [PR #421](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/421); version 1.2 remains unreleased.

## The observation-process problem

Prior R79–R81 experiments examined nonseparable covariance, independent-unit Student-t5 shocks and asymmetric contamination while retaining complete two-coordinate trajectories. They did not test whether inference was even feasible after gaze samples were lost. The public common-grid function-on-scalar regression intentionally requires finite complete observations rather than silently interpreting missing values as zeros or imputed data.

R82 therefore studies **selection, independent-unit support, and descriptive functional-slope reconstruction**, not a new missingness-aware estimator. The [prespecified R82 protocol](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/research/w3-r82-observation-process-mcar-mar-mnar-20261021/docs/development/w3-r82-prospective-observation-process-decomposition.md) freezes 32 **new independent primitive source blocks** across two original independent-unit designs (72 curves versus 36 participants with three trials), two influential predictor-support counts (2 versus 16 x=±4 independent units), and constant versus predictor-dependent unit scales.

The source family retains R81's complete synthetic Student-t5 unit radial, rare mean-zero asymmetric unit shock and nonseparable time/coordinate Gaussian covariance over a **31-time × 2-coordinate slope grid**. There are **256 complete-source condition datasets**, each evaluated under four paired observation mechanisms, for **1,024 observation-process evaluations**. The statistical denominator remains **32 independent generated source blocks per fixed design/support/variance cell**, not 1,024 replications.

## Four frozen observation laws

One uniform random-number field is shared across the four observation masks for each original complete dataset:

| Mechanism | Selection probability |
|---|---|
| COMPLETE | Zero missing samples |
| MCAR | Constant 12% missing probability |
| MAR | Logistic model with logit −2.2 + \|x\|/4 + 0.7t + 0.2(trial index), depending only on **recorded** predictor/time/trial |
| MNAR | MAR logit plus 1.1 tanh[(Y−true mean)/.08], additionally depending on the **subsequently unobserved true outcome residual** |

The true source Y remains identical across masks. These are simulated selection rules, not fitted gaze-detector models; in particular, the MNAR residual is an oracle simulator quantity unavailable to an empirical analyst.

![Analytic probability curves for complete, MCAR, MAR and MNAR missing-gaze mechanisms](../assets/research/w3-r82-analytic-mcar-mar-mnar-loss-laws.svg)

*Figure 1.* The specified source selection probabilities at normalized trial time .5, trial index zero and two predictor magnitudes. The MNAR curve changes with the latent outcome residual, whereas MAR remains fixed when recorded predictors and time are held constant.

## A deliberately naive pointwise diagnostic, with refusal

R82 fits **separate available-case OLS slopes at each time and coordinate**, using the original true predictor. Independent curves enter only when observed at that location. For repeated participants, the procedure first averages only **observed trials within the participant and location**; a participant is still one independent unit, never three.

At each grid location, the diagnostic refuses a slope if there are fewer than eight independent units, the intercept/predictor design is not rank two, or either sign of the x=±4 extreme independent-unit support is missing. It **does not fill refused grid positions**, and calculates no confidence interval or joint critical. Its source-specific slopes can be compared with the same generated dataset's complete-source pointwise slope only at locations that pass the support gate.

## Results: sample retention is not slope estimability

![Observed samples and refused functional grid locations under complete, MCAR, MAR and MNAR](../assets/research/w3-r82-missingness-retention-and-grid-refusal.svg)

*Figure 2.* Original new-source averages across 32 independent primitive blocks per design. Primary adverse case: only two independent extreme units and predictor-dependent variance. A refused grid position is not imputed or included in an interval.

| Primary adverse case | COMPLETE | MCAR | MAR | MNAR |
|---|---:|---:|---:|---:|
| Curves: samples retained (%) | 100.0 | 87.9 | 84.3 | **83.1** |
| Curves: mean refused grid positions /62 | 0 | 14.91 | 31.84 | **33.56** |
| Participants: samples retained (%) | 100.0 | 88.1 | 81.0 | **78.3** |
| Participants: mean refused grid positions /62 | 0 | 0.25 | 5.13 | **8.38** |

Although **83.1%** of curve-level gaze samples remain under MNAR, the support requirement refuses an average **33.56 of the 62 slope positions**. With only two influential units, losing either the negative or positive anchor at one time/coordinate destroys the stipulated full support for that local diagnostic even when many central-predictor observations remain.

At the participant level, repeated observed trials partially protect within-participant pointwise availability. This is not evidence for trial-level independence: the analysis keeps **36 independent participants** and aggregates available trials before estimating the slope.

In the **16-anchor** predictor-dependent-variance controls, the support gate retained essentially all 62 grid positions under every observation law in both designs, even though mean MNAR retention was **80.4% for curves and 71.4% for participants**. Retaining grid support is **not** evidence of unbiased slope estimation or simultaneous-band calibration.

Every incomplete source passed the stable public regression's intended **missing-gaze rejection** check; native fitting was not silently relaxed.

## Descriptive masked-versus-complete slope movement

![Source-mean absolute pointwise slope changes from matched complete data under MCAR, MAR and MNAR](../assets/research/w3-r82-available-case-slope-deviation.svg)

*Figure 3.* Mean absolute masked-versus-complete slope change, **conditional on the masked grid positions that remain estimable**. A greater change does not independently identify MNAR bias because the compared grid positions and overall retention vary.

| Predictor-dependent-variance cell | MCAR | MAR | MNAR |
|---|---:|---:|---:|
| Curves, 2 anchors | .00212 | .00260 | .00302 |
| Participants, 2 anchors | .00310 | .00642 | .00684 |
| Curves, 16 anchors | .00325 | .00625 | .00654 |
| Participants, 16 anchors | .00199 | .00510 | .00690 |

The signed and absolute errors with respect to the generating truth are preserved separately in the full source archive. Their means may compare **different selected subsets of the 62 grid points**: a mechanism that refuses difficult positions could show a lower average error without actually improving estimation. R82 therefore treats grid refusal as an inseparable component of the scientific result, rather than selecting favorable observed-error comparisons.

## Complete independent numerical verification

Original [R82 science workflow #39571308151](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39571308151) passed **12/12 dedicated scientific jobs**, including three Python source/observation contracts, eight disjoint new-source shards and a SHA256 aggregate. Its [immutable original archive #12331563201](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39571308151/artifacts/12331563201) records source checkout **06d1bb888468f1f85eee3875ae14ee5070a12400**, all **256 new X/Y complete-source conditions** and **1,024 paired masks and descriptive evaluations**.

The separately implemented [R82-A actual original-source audit #39572315409](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39572315409) passed **4/4 dedicated audit jobs**. It recreated source X/Y, all original masks, source/mask digests, participant-unit aggregation, grid-specific independent-unit/anchor refusal, pointwise slopes and full-source comparisons. The [independent evidence #12332990886](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39572315409/artifacts/12332990886) reports **256 independently replayed X/Y source conditions and 1,024 replayed masks**, while explicitly withholding missingness correction and inference qualification.

This confirms numerical reproducibility of the stipulated synthetic observation process, **not identifiability or correction of MNAR gaze loss**.

## Implications and research boundary

R82 localizes an actionable scientific problem: moderately missing gaze samples can leave apparently ample total observations but insufficient **independent high-leverage predictor support across the functional domain**. Repeated trials can protect observed participant-level grid availability, not repair the selection law. The naive available-case procedure does not justify full-function inference when any grid position is unsupported.

Future work must establish and validate an observation model, estimand, assumptions for nonignorable loss and a genuine missingness-aware uncertainty procedure. The R82 simulations do **not** qualify such a method.

**Release decision:** scientific issues #289 and #296 remain OPEN. Stable release 1.1.0 and the public inference API are unchanged; version 1.2 and PyPI remain on **RELEASE HOLD**.

[Observation-process methods companion](independent-gaze-loss-and-pointwise-feasibility.md) · [Full original and independent evidence/figure ledger](../development/w3-r82-observation-process-evidence-ledger.md)
