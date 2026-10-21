# W3 R83 original and independently audited MNAR sensitivity evidence ledger

**Research-only numerical provenance · 21 October 2026**

!!! danger "Five sensitivity values do NOT identify MNAR or qualify inference"
    The five outcome-dependent selection coefficients are hypothetical externally specified assumptions. True selection parameters and conditional response mean are available only in simulation. R83 supplies descriptive pointwise weighted least-squares results, **no validated confidence intervals or general nominal-90% simultaneous bands**. Issues #289/#296 stay open; stable 1.1.0 API unchanged, unreleased v1.2/PyPI HOLD.

## Evidence identity and replication count

| Contract | Actual evidence |
|---|---|
| Prospectively frozen original source and hypotheses | [Research-only draft PR #423](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/423) |
| Original dedicated science workflow | [#39575847765](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39575847765), **12/12 successful dedicated jobs** |
| Original source SHA256 archive | [Artifact #12333573581](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39575847765/artifacts/12333573581) |
| Original source checkout | 4aaf792457c789b3fafd218e3dd94ae46af47e86 |
| Separately implemented numerical audit | [R83-A research draft PR #424](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/424) |
| Original archive replay workflow | [#39576738539](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39576738539), **4/4 dedicated independent jobs successful** |
| Separately retained audit report | [Artifact #12334118238](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39576738539/artifacts/12334118238) |
| New genuinely independent primitive source blocks | **32 per fixed unit-design/predictor-support/variance cell** |
| Original complete X/Y source conditions | **256** (32×2×2×2) |
| Paired original complete/MCAR/MAR/MNAR masks | **1,024** (four per original X/Y source condition) |
| Independent audited descriptive source-analysis records | **3,328** (13 per source; NOT 3,328 independent replications) |
| Five MNAR sensitivity assumptions | δ=−1.1, −.55, 0, +.55, +1.1 |
| True simulation-only MNAR reference | Original δ=+1.1 with simulator-known true conditional mean, NOT a field-data model |
| Native public regression | Missing gaze correctly refused, not imputed |
| Real missingness inference | **Not calibrated**, no supported MNAR estimator, interval, or release |

The complete generating law is the R81-family independent-unit shared Student-t5 radial and centered rare asymmetric unit shock on a nonseparable two-coordinate Gaussian functional process. R83 uses **new seed streams** source 202610218380 and observation 202610218381, distinct from R82. The original mask uniforms are paired across complete/MCAR/MAR/MNAR mechanisms within a source.

## Figure 1 — observed-only assumption sensitivity

![Independently source-replayed five-delta pointwise slope sensitivity](../assets/research/w3-r83-assumed-delta-slope-sensitivity.svg)

*Figure 1.* Mean source-specific absolute pointwise slope shift from complete data, among *estimable positions*, for two influential units and predictor-dependent source variance.

| Frozen assumed δ | Curves, MAR mask | Curves, MNAR mask | Participants, MAR mask | Participants, MNAR mask |
|---:|---:|---:|---:|---:|
| −1.10 | .003733 | .004444 | .011936 | .012811 |
| −0.55 | .003160 | .003797 | .011293 | .011845 |
| 0 | .003015 | .003481 | .011032 | .011190 |
| +0.55 | .003253 | .003527 | .011135 | .010913 |
| +1.10 | .003901 | .003926 | .011657 | .011048 |

*Within the identical MNAR mask*, comparing slope functions under the two endpoint assumptions at grid positions estimable under both yields **mean source absolute endpoint spread 0.004530** for curves and **0.008409** for participants. This is neither an inferential interval nor a causally identified selection effect. The source-known true-propensity oracle's mean shift from complete was **.004475 curves and .011453 participants**; its error does not necessarily have to be the smallest finite-source realized error.

## Figure 2 — original observation retention and independent signed-anchor support

![Observed original mask sample fractions and pointwise refusal](../assets/research/w3-r83-unchanged-mask-support-refusal.svg)

*Figure 2.* All sensitivity values applied to a given mask have the **same observed fraction and underlying independent-unit support**. Under two extreme predictor units and heteroskedasticity:

| Original source mask | Curves: fraction retained | Curves: mean refused grid /62 | Participants: fraction retained | Participants: mean refused /62 |
|---|---:|---:|---:|---:|
| COMPLETE | 1.0000 | 0.00 | 1.0000 | 0.00 |
| MCAR | .8800 | 13.44 | .8805 | .31 |
| MAR | .8423 | 31.81 | .8094 | 5.47 |
| MNAR | .8304 | 32.16 | .7906 | 10.53 |

The diagnostic refuses each of 62 grid positions without n≥8 independent units, rank-two pointwise design and both signed ±4 original predictor anchors. The oracle and weighting cannot restore unavailable signed extremes.

## Figure 3 — weights and cluster information

![Source-averaged assumed inverse observation weights across R83 MNAR delta](../assets/research/w3-r83-selection-weight-sensitivity.svg)

*Figure 3.* The missingness mask remains fixed, but weights change under the hypothetical δ. In the primary adverse MNAR condition:

| δ | Curves: mean max inverse observation weight | Curves: mean effective independent cluster n | Participants: mean max weight | Participants: mean effective cluster n |
|---:|---:|---:|---:|---:|
| −1.10 | 2.664 | 59.55 | 3.504 | 31.33 |
| −0.55 | 1.977 | 60.39 | 2.468 | 32.36 |
| 0 | 1.597 | 60.64 | 1.902 | 32.86 |
| +0.55 | 1.895 | 60.50 | 2.447 | 33.02 |
| +1.10 | 2.489 | 59.89 | 3.476 | 32.76 |

Independent curve design has n=72 units; repeated-trial participant design has n=36 units. These are descriptive effective-cluster and maximum weight summaries, **not calibrated uncertainty estimators**.

## Complete prespecified eight-cell MNAR diagnostic summary

The table reports the MNAR mask only, the δ=0 observed-only pointwise slope absolute shift from the matched complete source, and the *source mean within-mask absolute endpoint slope spread* for δ=−1.1 versus +1.1 on jointly estimable positions.

| True independent design | Extreme units | Error variance | MNAR observed fraction | Refused grid /62 | δ=0 mean absolute shift | Endpoint δ slope spread |
|---|---:|---|---:|---:|---:|---:|
| Curves | 2 | Constant | .8334 | 31.69 | .001692 | .001396 |
| Curves | 2 | Heteroskedastic | .8304 | 32.16 | .003481 | .004530 |
| Curves | 16 | Constant | .8064 | 0.00 | .001594 | .001235 |
| Curves | 16 | Heteroskedastic | .8021 | 0.00 | .006367 | .005656 |
| Participants | 2 | Constant | .7941 | 8.69 | .003491 | .003095 |
| Participants | 2 | Heteroskedastic | .7906 | 10.53 | .011190 | .008409 |
| Participants | 16 | Constant | .7361 | 0.00 | .002066 | .002176 |
| Participants | 16 | Heteroskedastic | .7282 | 0.00 | .007858 | .008502 |

These quantities are **conditioned on the mechanism-specific estimable grid**, not comparable as if they were complete functional confidence-band coverage or between-law causal treatment effects. The archive separately retains all source X/Y and mask checksums, individual pilot fits, 62-grid support/refusal matrices, source absolute/signed slope errors, MCAR and MAR controls, oracle truth diagnostics, inverse weights, and original release-withheld qualification flags.

## Scientific boundary and publication decisions

The independent R83-A original evidence audit reproduced each original source, each paired missingness mask and **3,328 weighted or complete-data pointwise diagnostic records**, including checksums and refusal accounting, using an independent sufficient-statistic weighted-slope implementation. It establishes *numerical reproducibility of this chosen simulation law and hypothetical selection family*.

It does **not** establish that δ or the missing-outcome selection mechanism can be learned from actual gaze data; it does not provide a justified sensitivity interval with confidence guarantees, participant-cluster standard errors, valid missingness-dependent full-function uncertainty or general 90% simultaneous coverage. A simulator-known true-propensity oracle remains infeasible in field data.

**No estimator code/API merge; #289/#296 OPEN, stable eyetrajectoriespy 1.1.0 unchanged, unreleased 1.2/PyPI RELEASE HOLD.**

[Full R83 scientific article](../articles/w3-mnar-selection-sensitivity-r83.md) · [Methods companion](../articles/independent-gaze-MNAR-sensitivity-and-selection.md) · [R82 observation-process source ledger](w3-r82-observation-process-evidence-ledger.md)
