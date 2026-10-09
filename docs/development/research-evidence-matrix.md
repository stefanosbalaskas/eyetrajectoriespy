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
| D4 sample-size/power | simulate_functional_study_power() | Stacked #235 checks pending | Actual F1 experimental test; no certified power |
| D4 repeatability | fit_functional_reliability() | Stacked #235 checks pending | Balanced moments, no generic functional ICC |
| D4 paired groups | compare_repeated_functional_groups() | Stacked #235 checks pending | Sign-symmetric participant differences only |
| D2 quality linkage | link_gaze_validation_sessions() | Stacked #235 checks pending | Identifier match, no clock or drift proof |
| D2 multi-stream BIDS audit | audit_bids_eyetracking_dataset() | Stacked #235 checks pending | Not official bids-validator |

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

## B5–B10 native Bayesian research track

[Draft PR #237](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/237) adds **experimental** backend-independent posterior tools, a *known-population conditional sparse score baseline* (not a learned Bayesian FPCA estimator) and a fixed-noise Gaussian B-spline functional regression prototype. No architecture replacement, inference calibration or publication decision is established. See the [Bayesian research catalogue](bayesian-research-programme.md) and [synthetic fitted-model gallery](bayesian-gallery.md).
