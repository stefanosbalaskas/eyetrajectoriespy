# Research evidence matrix — unpublished

!!! warning "Stable release versus prototypes"
    **Stable 1.1.0** is available from PyPI. **Research 1.2** (source 1.2.0rc2.dev0) is unpublished. The **27/27** engineering workflow success refers exclusively to [PR #227](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/227) commit d48c939b01fbfa19f0e060902b6a61ebddbe7aa6. It does not certify newer commits or scientific inference.

## Further exact-source scientific findings — 9 October 2026

**Scientific qualification remains failed/unestablished, irrespective of green CI.**

- **B6/B7 exact conditionals:** [PR #257](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/257) independently constructed dense observation-row Gaussian reference posteriors; loading/mean/asynchronous shared-score conditional precision and mean tests passed on Python 3.11, 3.12 and 3.13. This is **conditional-update algebra**, not proof that the whole Gibbs posterior mixes or has nominal coverage.
- **B6/B7 scale interweaving:** [source run #37976468861](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37976468861) completed **72** matched-prior genuine Gibbs refits with no exceptions. A mathematically reversible likelihood-invariant MH factor-scale proposal had **no consistent R-hat or ESS improvement**, and most rank-2/asynchronous comparisons deteriorated. The implementation remains opt-in and unqualified. [Detailed results](b6-b7-reversible-scale-interweaving.md).
- **F5 fresh independent nulls:** [source study #37975560959](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37975560959), SHA256 recovered in [#37976469318](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37976469318), produced 1,800 real hypothesis tests, with no fitting exceptions and no recovery refits. At alpha .05, true phi=.8 null rejection was **99/200 = 49.5%** for old block-4 but **16/200 = 8.0%** for the reference using **known oracle phi**. This is an improvement in one conditional simulation regime, **not** a calibrated test for unknown serial dependence. [Detailed model and limits](independent-core-computation-and-f5-ar1-reference.md).
- **F1 higher-precision study completed:** [draft #259](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/259) completed an independent, full native sparse-PACE **4,000 null + 2,000 moderate alternative** simulation programme ([original complete source run #37977625803](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37977625803), 5/5 study jobs green; original combined artifact **11640464273**), zero fit exceptions. At α=.05 the null rejection rates were **4.9%, 5.1%, 5.2%, 4.4%** (1,000 independent datasets each) and moderate-effect detection **15.8%, 18.2%, 19.2%, 14.2%** (500 datasets each). This suggests nominal size in the tested configurations, **not universal validity or useful general power**.
- **Bayesian partially collapsed mean:** [draft #260](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/260) implemented opt-in *exact* score-marginalized B6 and joint x/y cross-channel B7 mean conditionals. Its [original complete science run #37978244822](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37978244822) passed all 4 numerical/scientific jobs and **72/72 paired fits**, zero failures; B7 rank-1 asynchronous median worst monitored R-hat improved **1.470→1.067** and minimum ESS **4.07→15.35**, while B7 rank-2 paired remained poorly mixed (**1.937→1.537**, ESS **2.92→3.81**). No adequate full posterior convergence or 90% coverage certification. The original sampler remains default. [Mathematical protocol](b6-b7-exact-collapsed-mean-gibbs.md).

The earlier [B6/B7 blocker #255](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/255)
and [F5 dependence blocker #256](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/256)
stay open. **Stable 1.1.0 is unchanged; 1.2 research and its source pages are
not a production release or independently deployed public website.**

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

## Actual 13,600-attempt scientific calibration (9 October 2026)

!!! warning "Large empirical simulation did not qualify Bayesian or dependent F5 inference"
    [Original full simulation #37965949039](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37965949039)
    performed **13,600** native fitted-model/test attempts in six independent
    shards with **zero fitting exceptions**. Bayesian B6 and B7 aggregate
    jobs passed; F1/F5 original aggregate had an evidence-schema defect,
    then [recovery run #37969068128](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37969068128)
    verified and recovered all **9,600** archived F1/F5 tests without
    refitting models. This evidence is **not** 1.2 release authorization.

- **B6 (400 genuine refits per scenario):** under matched priors, nominal
  90% population mean/covariance intervals covered **70.75%/77.00%**
  (rank 1) and **62.00%/67.00%** (rank 2), with zero exceptions.
- **B7 (400 refits per scenario):** paired rank-1 x/y mean intervals covered
  **61.50%/67.00%**, joint x/y cross-covariance **74.00%**;
  asynchronous rank-2 x/y means covered **57.50%/59.50%**,
  cross covariance **67.75%**. Held-out person average pointwise
  predictive inclusion was **86.41%–87.59%**, not a simultaneous band.
  Severe undercoverage cannot be attributed to implementation versus
  poor MCMC mixing until long-chain diagnostic [#253](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/253)
  and independent reference comparisons finish.
- **F1 (300 attempts per truth/design):** α=.05 null rejection **4.33%–7.67%**;
  no nominal-size qualification or general-power claim. Alternative
  detection **98%–99.33%** under the deliberately strong simulated effect.
- **F5 (300 per scenario, α=.05):** true strong AR(1) stationary
  **no-change** false rejection was **100%** (block 2),
  **42.67%** (block 4), and **2.33%** (block 8).
  Dependence-calibrated p-values fail under the tested regimes and
  cannot be recommended as nominally calibrated.

See [complete design-by-regime scientific evidence](first-empirical-calibration-findings.md)
and governance issues [Bayesian undercoverage #255](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/255)
and [F5 null-size failure #256](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/256).
**Scientific inference, stable API, deployment and publication gates stay false.**

## B5–B10 native Bayesian research track

[Draft PR #237](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/237) adds **experimental** backend-independent posterior tools, a *known-population conditional sparse score baseline* (not a learned Bayesian FPCA estimator) and a fixed-noise Gaussian B-spline functional regression prototype. No architecture replacement, inference calibration or publication decision is established. See the [Bayesian research catalogue](bayesian-research-programme.md) and [synthetic fitted-model gallery](bayesian-gallery.md).

The B8 *experimental* Bayesian functional random-intercept Gaussian conjugate model (`fit_bayesian_functional_mixed_effects()`) accepts repeated participants, but conditions on fixed noise and random-effect prior SDs; no random slopes, nested trial effects, serial residual model or learned hyperparameter inference is yet qualified.
