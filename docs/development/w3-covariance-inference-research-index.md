# W3 CR2 and estimated-covariance research: source-evidence index (R16–R29)

**Status: research development only.** The eyetrajectoriespy 1.2 covariance inference work has not been promoted into the supported public API, and neither the proposed pointwise intervals nor simultaneous 90% functional bands are statistically qualified. This index preserves **numerical verification**, **source-level finite-sample evidence**, **identified failures**, and **subsequent explanations** as distinct levels of evidence.

All stages here use original source code and scientific workflows in draft research pull requests. Green CI means the *specified execution and reproducibility contract* passed; it does **not** turn negative numerical or statistical findings into positive inference results.

## Scientific progression and original evidence

| Stage | Evidence and result | Scientific boundary |
|---|---|---|
| R16–R17 | CR2 covariance and Satterthwaite numerical references; original finite-cluster simulations expose nonuniform 90% coverage under high leverage and covariance conditions | Independent numerical agreement is not empirically calibrated inference |
| R18 | [Independent Gaussian oracle replication](w3-r18-independent-gaussian-oracle-results.md), 192 independent generating blocks, 768 paired calculations | Some oracle coverage remained below nominal; not attributed to mean-basis projection |
| R19 | [Primitive Gaussian source reconstruction](w3-r19-primitive-gaussian-oracle-results.md), all 768 original source cases recovered exactly | Source covariance and noise reconstruction do not qualify general inference |
| R20 | [Original fitted-target feasibility pilot](w3-r20-estimated-target-pilot-original-failures.md), **215/256 completed, 41 numerical failures** | Original failures retained, not deleted or retroactively relabeled |
| R21 | [Original failed-case spectral audit](w3-r21-estimated-target-spectral-results.md), 32 near-boundary product matrices plus nine positive-but-subthreshold products | Diagnoses numerical conditioning; not a statistical solution |
| R22 | [Scaled-Cholesky symmetric CR2 numerical reference](w3-r22-scaled-cholesky-results.md); external R and high-precision checks; 9 newly computable but **32 explicit refusals** | The original R20 historical 41 failures remain; stable matrix calculation is not calibrated CI |
| R23 | [New-source fitted-covariance component identifiability](w3-r23-estimated-target-identifiability-results.md), 576 paired cases, frequent random-slope and trial NNLS zeros | Rank-four covariance kernels did not ensure finite-sample recovery |
| R24 | [Population moment and finite Gaussian noise diagnostic](w3-r24-population-moment-noise-results.md), exact population recovery yet common noisy boundary estimates | Conditional noise draws are not new independent source replications |
| R25 | [First Gaussian REML versus NNLS pilot](w3-r25-reml-vs-nnls-results.md), four independent blocks and 64 paired cases | REML showed promising trial/sensor recovery; too few blocks for method selection |
| R26 | [Independent 16-block REML/NNLS replication](w3-r26-independent-estimator-recovery-results.md), 384 paired cases, block bootstrap | REML trial/sensor improvement supported under the matched Gaussian source, slope/intercept not established |
| R27 | [Gaussian REML variance-component Fisher information](w3-r27-reml-information-results.md), eight fixed native designs, 1,024 conditional Gaussian draws | Random-slope log variance has weak local expected information despite positive information rank |
| R28 | [Hypothetical predictor spread sensitivity](w3-r28-predictor-information-results.md), exact negative-control invariance and 32 design information calculations | Counterfactual Gaussian information only, not recruitment or empirical design advice |
| R29 | [Independent-source predictor-spread Gaussian recovery](w3-r29-counterfactual-predictor-recovery-results.md), 12 independent blocks and 192 paired primitive-noise-reconstructed outcomes | Predictor-dependent slope variance recovery improves on average with wider x spread, but limited source blocks, hypothetical predictor ranges and no CI qualification |

## What is currently supported scientifically

The **specified, well-conditioned CR2 adjustment** has mathematical and external-reference support. A separately estimated working covariance introduces both numerical instability (original R20 pilot) and weak finite-sample component recovery (R23–R28). An independent Gaussian REML estimator has stronger *trial and sensor component* recovery in the tested source, but this does not establish a method winner for all covariance components or account for estimated-nuisance uncertainty in the conditional Satterthwaite degrees of freedom.

For the original ordinary-support Gaussian information designs, at n=96 the local asymptotic log random-slope variance SE remained about **1.9–2.2**, far larger than the trial-variance (~0.155) or sensor-variance (~0.0185) analogues. A separate *hypothetical* predictor-dependent covariance spread experiment showed information improvements when predictor span was scaled, but did not collect new observations or validate prospective recruitment or within-person measurement strategies.

## Open statistical and release gates

Scientific issue [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain open. Needed evidence includes a reliable variance-component model under realistic irregular observation and physiological errors; independent estimation and uncertainty qualification for working covariance; failure-inclusive, independently seeded 90% pointwise interval calibration with Monte Carlo uncertainty; and **separate simultaneous function-wide band calibration**.

**Do not interpret any research figure or table as certification of the version 1.2 stable API.** All research pull requests remain isolated from protected main; version 1.2 publication, release tags and PyPI uploads remain unauthorized.
