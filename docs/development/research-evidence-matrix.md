# Research evidence matrix — unpublished

!!! warning "Stable release versus prototypes"
    **Stable 1.1.0** is available from PyPI. **Research 1.2** (source 1.2.0rc2.dev0) is unpublished. The **27/27** engineering workflow success refers exclusively to [PR #227](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/227) commit d48c939b01fbfa19f0e060902b6a61ebddbe7aa6. It does not certify newer commits or scientific inference.

| Route | Opt-in API | Engineering | Scientific status |
|---|---|---|---|
| F1 sparse independent groups | test_sparse_functional_groups() | Original #227 27/27 | Null size and exchangeability **not qualified** |
| F2 validation targets | summarize_gaze_validation_targets() | Original #227 27/27 | Descriptive, independent target provenance |
| F3 Eye-Tracking-BIDS | from_bids_eyetracking() | Original #227 27/27 | BIDS 1.11.2 narrow subset, not official conformance |
| F4 AOI geometry | compare_aoi_functional_geometries_holdout() | Original #227 27/27 | Not a constrained eigenfunction estimator |
| F5 whole-curve changes | detect_ordered_functional_changepoint() | Original #227 27/27 | Bootstrap p-values **unqualified** |
| F6 weighted L2 | fit_weighted_mfpca() | Original #227 27/27 | Declared weights, no optimal weighting |
| D4 sample-size/power | simulate_functional_study_power() | PR #235 exact-head 27/27 green (013cd05d) | Actual F1 experimental test; no certified power |
| D4 repeatability | fit_functional_reliability() | PR #235 exact-head 27/27 green (013cd05d) | Balanced moments, no generic functional ICC |
| D4 paired groups | compare_repeated_functional_groups() | PR #235 exact-head 27/27 green (013cd05d) | Sign-symmetric participant differences only |
| D2 quality linkage | link_gaze_validation_sessions() | PR #235 exact-head 27/27 green (013cd05d) | Identifier match, no clock or drift proof |
| D2 multi-stream BIDS audit | audit_bids_eyetracking_dataset() | PR #235 exact-head 27/27 green (013cd05d) | Not official bids-validator |

**Open gates:** F1/F5 full type-I error/power/serial-dependence calibration; F2 external validation evidence and session timing; F3 official BIDS conformance and external datasets; F4 constrained AOI eigenspace; F6 weight sensitivity; D4 reliability uncertainty and crossover modelling; D5 fully qualified examples and docs.

[Method finder](method-finder.md) · [Method contracts](research-method-api.md) · [Case studies](research-case-studies.md)

## Retained PR #227 exploratory simulation data (not qualifying)

An exact-head workflow [run #37870154333](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37870154333) retained the following **100-replication** synthetic diagnostic results at alpha = 0.05:

| Pilot | Null rejection | Detection under simulated alternative | Methodological limitation |
|---|---:|---:|---|
| F1 isolated pooled-score permutation kernel | 0.01 | 0.77 | No sparse-PACE refit on each replication |
| F5 independent whole-curve CUSUM | 0.06 | 1.00 | Single independent-generating process and shift |
| F5 AR(1) weak-block CUSUM | 0.01 | 0.99 | One serial-dependence strength/block setting |

The F1 native-pipeline pilot completed only **two refits per each of three regimes**, all fitted successfully. The F4 held-out feasibility produced **144 sensitivity records**. None constitutes scientific calibration. With only 100 simulation replications the null rejection estimates have wide Monte Carlo uncertainty; the 0.01 estimate has approximately 0.002–0.054 Wilson 95% range, and the 0.06 estimate approximately 0.028–0.125. The target nominal 0.05 is not ruled out by these pilots, nor proven by them. Larger design-gridded refit experiments remain mandatory.

## New scientific research development (staged, not published)

The original F1–F6 PR #227 completed 27/27; stacked D1–D5 PR #235 completed
27/27; Bayesian foundation PR #237 completed 32/32; and native learned B6
PR #243 completed 27/27 on their **separate exact GitHub heads**.
[Draft #244](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/244)
also completed its 28/28 exact-head engineering workflows. It adds
six-scenario learned B6 population calibration and full-fit F1/F5 stress
runners. Its short engineering run completed 12 B6 refits, 16 F1 full sparse
refits, and 48 F5 stress evaluations without execution failure.
None of those small-run totals certifies coverage, nominal null size or power.

[Draft #245](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/245)
introduces the learned **joint x/y** Gaussian latent functional factor
posterior on native paired/asynchronous observations. The component columns
remain sign/rotation unidentified; joint covariance is learned, but fully
calibrated eigenfunction inference is **not** established. Its strict
documentation contract was repaired on a later head; retain CI status by
exact head, not by assuming older green matrices apply automatically.

The further B7/B9 research extension predicts genuinely new participants
using learned population posterior draws, a fresh shared x/y latent factor
and channel-specific observation noise. It does not borrow training
participants' fitted scores. See [new participant prediction](b7-prediction-calibration.md)
and the [B6/F1/F5 protocol](b6-f1-f5-calibration-protocol.md).
Prediction intervals are pointwise, **not** jointly calibrated functional
bands. CI passing and synthetic pilot success never change
`scientific_inference_qualified` or publication interlocks.

### Reproducible large-sample calibration preparation

The independent-shard research procedure supports versioned, seed-separated
B6/B7/F1/F5 simulations, audits checksums, rejects repeated scenario/replicate
keys and observed random-seed collisions, and preserves failed fits.
See [calibration batches](scientific-calibration-shards.md). The availability
of a repeatable study framework does **not** establish actual large-sample
simulation evidence or scientific qualification.

## B5–B10 native Bayesian research track

[Draft PR #237](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/237) adds **experimental** backend-independent posterior tools, a *known-population conditional sparse score baseline* (not a learned Bayesian FPCA estimator) and a fixed-noise Gaussian B-spline functional regression prototype. No architecture replacement, inference calibration or publication decision is established. See the [Bayesian research catalogue](bayesian-research-programme.md) and [synthetic fitted-model gallery](bayesian-gallery.md).

The B8 *experimental* Bayesian functional random-intercept Gaussian conjugate model (`fit_bayesian_functional_mixed_effects()`) accepts repeated participants, but conditions on fixed noise and random-effect prior SDs; no random slopes, nested trial effects, serial residual model or learned hyperparameter inference is yet qualified.
