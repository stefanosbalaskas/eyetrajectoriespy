# W3 R45 — observed-design propensity weighting and exploratory pointwise interval study

**Prospective research-only inferential pilot.** This protocol prespecifies estimands, source, missingness mechanisms, propensity observability, numerical failure accounting and interval method *before* evaluating the original R45 source data. This is **not** covariance-estimation-aware CR2 calibration, a valid MNAR adjustment, a proof of nominal coverage, a whole-function simultaneous band, or a release-ready public API.

## Why R45 is needed

R44 introduced genuine missing-outcome-dependent point loss and complete-participant selection driven by full latent responses. It documented how the retained-data empirical focal regression slope departs from the original full-cohort empirical target without claiming an observed-data selection correction. A numerically stationary REML nuisance likelihood alone cannot recover the intended full-cohort regression target.

R45 asks the **narrow identified question**: if the trial schedule, time and predictor are available even when a scheduled gaze observation is missing, does observed-data propensity weighting improve estimation of the *generating fixed focal regression slope* under a correctly specified, conditionally observed-design-dependent point-loss process? We also document uncorrected empirical behavior under genuinely outcome-dependent missingness and whole-participant selection, without misleadingly transferring the MAR correction to them.

## Source, estimand, missingness and independence

Use **12 NEW independent Gaussian primitive innovation blocks**, master seed **202610164545** (all distinct from R37–R44), and selection random seed **202610164546**. Nest n=24 and n=48 samples within each independent primitive block; pair ordinary/extreme predictor leverage and generating exact-zero/positive random slopes. Actual generating exact-zero sources are reconstructed by removing the participant-slope innovations; 12 primitive blocks are independent, but nested n/source-state/support conditions are **paired**, not 96 independent replicates.

The primary scientific estimand is the **generating population fixed predictor-slope coefficient at the original prespecified focal time**. Also record the **realized full-cohort WLS focal slope** and each **retained-record estimate** as descriptive realized-sample quantities.

Four prespecified response-observation processes are constructed on the same complete native irregular repeated-trial trajectories:

1. **Complete**: all native participant/trial/time observations retained.
2. **Observable time/predictor-dependent MAR point loss**: an interior timestamp's Bernoulli retention probability is `expit(1.2 - 0.9*abs(x)/(1+abs(x)) - 0.7*t)`, fixed native endpoints retained with probability exactly 1. Point inclusion depends on *observed auxiliary design variables* only. Scheduled timestamps, trial IDs, participants, predictors and retained/missing indicator `R` are available even when the gaze response is missing. No deterministic minimum-trial point rescue is applied; this explicit auxiliary schedule assumption is material and must not be generalized to unrecorded sensor events.
3. **Missing-outcome-dependent MNAR point loss**: an interior timestamp's probability is `expit(1.1 - 1.2*tanh(y))`, based on the potentially unobserved gaze response. Original native trial endpoints have probability 1. The missing `y` influences selection only inside the simulator, never the retained-data estimator or its propensity model.
4. **Latent-outcome-dependent whole-participant selection**: for each complete-source participant, probability of retaining **all their original trials and gaze points** is `expit(0.4 - 0.8*mean(y_latent))`, using the participant's entire latent complete response. The excluded participant's entire schedule is unavailable to the estimator. Original full-cohort denominators and generating truth remain in the **evaluation ledger only**.

These four processes are different **identification problems**. Under the third and fourth, selection odds depend on unobserved outcomes and cannot be recovered using only the specified observed data without additional identifying assumptions. **Do not fit a pseudo-MAR IPW estimator to MNAR or latent participant selection and declare it corrective.**

## Frozen estimation methods

At the original source focal time, fit a Legendre-five function-on-scalar regression using native retained observations only.

For **complete data**, fit participant-balanced observed-data WLS and compute a participant-cluster-robust CR1 90% pointwise interval with the frozen degrees-of-freedom factor and Student-t quantile (`df = observed participants-1`).

For **MAR point loss**, compare three prespecified options:

- **Naïve observed-data WLS CR1**: rebalances each participant's observed trial timepoints exactly as in the existing W3 design; no loss adjustment.
- **Feasible observed-design propensity IPW CR1**: fit a Bernoulli logistic GLM on **every scheduled interior point** using only `(R, abs(x)/(1+abs(x)), t)`. Endpoints are known observed with probability 1. No gaze outcome, Gaussian generating variance or true design propensity enters the fitted propensity model. Combine inverse predicted inclusion probabilities with **fixed full-native-schedule trial weights** `1 / (trials_per_participant * native_trial_length)`, rather than renormalizing by an outcome-selected number of observed timestamps. Clip fitted inclusion probabilities at the prespecified lower bound **0.05**, recording fitted extrema. Logistic Newton fitting has fixed ridge **1e-5** and a **45-step** maximum.
- **Known design-propensity benchmark IPW CR1**: use the MAR generator's known *observed-auxiliary-design-only* Bernoulli probabilities for a **simulation benchmark**, not an empirical-data procedure. The generating probability depends solely on recorded `x,t`, never on unobserved gaze `y`. This is distinct from the feasible fitted estimator and must be labeled as a known-design oracle comparator.

For **MNAR point loss** and **whole-participant latent selection**, fit only the **naïve observed-data WLS CR1 descriptive comparator**. The complete scientific target remains in the external original simulation ledger, and no unidentified selection correction is attempted.

Use the standard participant-level cluster CR1 sandwich `(X'WX)^{-1}[sum_i s_i s_i'](X'WX)^{-1}` with correction `G/(G-1)*(N-1)/(N-p)`; pointwise 90% limits are `c'b ± t_{.95,G-1} SE_CR1`. This is **not CR2**, not fitted-covariance-aware Satterthwaite adjustment, and not a simultaneous functional band. The design does not choose estimators using observed coverage outcomes.

## Frozen denominators and failure-inclusive reporting

**12** genuinely independent primitive blocks × 2 nested n × 2 supports × 2 true random-slope states = **96 paired source variants**; × 4 observation processes = **384 observation cases**. One complete estimator, three MAR estimators, one MNAR naïve estimator and one participant-selection naïve estimator per source = **576 predeclared CR1 pointwise-interval records**. All original source, observation, propensity, WLS, rank-deficiency, interval and participant-selection failures must remain in the case ledger. If a selection process fails, record explicit method refusal slots and do not silently substitute participant draws.

For each method and observation mechanism separately, preserve complete denominators, original participant/source-point retention, mean absolute focal-slope error against generating truth, mean absolute difference from the full realized cohort, mean interval width and **truth-inclusion numerator/denominator**. Do not describe 96 paired cells as 96 statistically independent simulations; the independent primitive-block denominator is only **12**. **A 12-block pilot is inadequate to validate nominal 90% population coverage or select a production inferential estimator**, regardless of observed inclusion fraction. No p-values or formal hypothesis ranking of missingness mechanisms will be computed.

## Next scientific and release gates

If the fitted observed-design MAR propensity model is numerically stable, R46 should independently enlarge the primitive-block source count, include propensity-model misspecification and positivity failures, and evaluate calibrated pointwise interval construction with appropriate accounting for estimating the propensity itself. Cluster CR1 intervals which treat fitted propensity weights as fixed do **not** automatically propagate propensity-estimation uncertainty. Correct 90% function-wide simultaneous inference requires a **separate procedure and simulation**; boundary-variance type-I error/power requires its own independent-null calibration.

Keep [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) **OPEN**. Preserve the original R20/R22/R33–R44 inferential and numerical failures. Do not merge into protected main, promote a public inference API, create a version 1.2 tag or publish to PyPI.
