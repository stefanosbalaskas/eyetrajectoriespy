# W3 R47 — prospective independent-block pointwise Monte Carlo audit of MAR propensity uncertainty

**Research-only, prespecified original-source calibration audit.** W3 R46 observed greater exploratory fixed-truth inclusion with participant-bootstrap propensity refits versus fixed-IPW CR1, but its nominal 90% counts arose from 32 independent primitive blocks crossed with nonindependent paired support/slope source variants. The R47 sampling unit and denominator are fixed **before original new-source simulation**. Do **not** treat R47 as fitted-covariance CR2 validation, a 90% whole-function simultaneous band, or version 1.2 release qualification.

## Independently replicated fixed generating design

New independent Gaussian primitive source seed **202610164747**, observation Bernoulli seed **202610164748**, full-participant bootstrap seed **202610164749**, all distinct from R37–R46. Generate **256 independent Gaussian primitive blocks**, precisely **one native irregular-trajectory dataset per block**, **n=24 participants, ordinary dependent predictor support, and true positive Gaussian participant random-slope variation**. No alternative support, exact-zero state or nested sample is included in R47; those design extensions belong in later independent studies. The *same* primitive source is paired across three observation regimes, which are therefore **not three separate groups of 256 independent source draws**.

The estimand is the original simulator's **fixed generating predictor-slope coefficient at the prespecified original focal time** (Legendre-five function-on-scalar basis). All intervals are evaluated against this generating truth, not against an outcome-dependent retained-only empirical target. Each primitive block is independent of other blocks, so within **any one regime**, the denominator of planned truth-inclusion outcomes is **256 independent blocks**. Comparisons between regimes and between methods are paired by block.

Regimes:
1. **Complete native observations:** observed participant-balanced WLS with one nominal 90% participant-cluster CR1 Student-t pointwise interval.
2. **Correctly specified observed-design MAR:** original Bernoulli interior retention `logit p=1.2-0.9q-0.7t` with `q=|x|/(1+|x|)`, native first/last trial timestamps deterministically retained.
3. **Severe weak-overlap observed-design MAR:** original interior retention `logit p=-1.5-2q-2.5t`, same endpoints retained. As in R46, fitted propensity probabilities are clipped at the prespecified **0.05** floor, which can break unbiased inverse probability weighting despite yielding finite weights.

The original native trial schedule, predictor and observed indicator **R** are available even if a gaze response is missing. Missing `y` is explicitly overwritten to `NaN`; neither missing gaze outcomes nor original true propensity values enter any fitted estimator. The three observation regimes are paired on each source and retain all original participants and native trial identities.

## Frozen interval methods

Complete sources: **naïve observed WLS**, participant-cluster **CR1** with Student-t at `df=n_participants-1`, nominal 90% pointwise interval.

Each of the two MAR regimes:
- Naïve **observed WLS CR1** without propensity adjustment.
- **Fitted observed-design MAR IPW fixed-weight CR1**: observed Bernoulli logistic `(R,q,t)` on scheduled interior timestamps only, original additive three-coefficient propensity contract, 0.05 fitted inclusion probability floor, inverse probability weights on fixed full native trial schedules; propensity uncertainty omitted from the CR1 covariance.
- **Fitted MAR IPW full participant-pairs bootstrap percentile**: sample whole participants with replacement including their entire scheduled `(R,x,t)` and observed-native `y`, relabel sampled identities, **refit the propensity on each resample**, and refit the functional weighted slope. Exactly **79** frozen replicates, no redraw on failures, with 5th and 95th empirical percentile limits constructed *only* when all 79 bootstrap replicates and the original fitted propensity succeed. This is a **percentile** interval, not bootstrap-t, not CR2 and not an entire-function band.

**Full original planned denominator:** 256 independent primitive blocks ×3 paired regimes = **768 original observation-process cases**; 256 complete intervals +256×2×3 MAR intervals = **1,792 interval records**; and 256×2×79 = **40,448 individual bootstrap-refit records**. Every planned block, regime, interval and replicate is recorded; failed fits and subsequent refusals count as noncoverage in the **primary all-planned independent-block denominator**. No success-only deletion or redraw is permitted.

## Prespecified diagnostics and Monte Carlo precision

For each fixed regime/method (not across pooled paired regimes), report:
- Count of independent primitive blocks that produced a valid interval, failed or refused interval, and **truth included among all 256 planned blocks**; report inclusion fraction treating missing intervals as noncoverage.
- **95% Wilson binomial interval** for this independent-block inclusion fraction, with nominal 0.90 shown explicitly as inside or outside that interval. This is a Monte Carlo uncertainty diagnostic, **not** scientific certification; its approximate half-width around 0.90 for n=256 is about four percentage points. Coverage conditional on successful intervals may be reported separately but cannot replace the failure-inclusive denominator.
- Mean absolute fixed-truth point error among successful fits, interval width, original observed interior retention, and count of failed/omitted bootstrap refits. Preserve individual seeds, outcomes and original source checkout digest.
- Original method comparisons are **paired within block**. No naïve two-sample significance tests or treating the 768 regime observations as independently generated.

A 95% Wilson interval containing 0.90 **does not establish** exact nominal 90% coverage, particularly under severe positivity clipping, 79-replicate percentile intervals and CR1 estimation of a non-diagonal Gaussian covariance process. If 0.90 is outside Wilson, the observed study supplies a clearer *negative* numerical calibration signal under this fixed source; otherwise it only fails to reject a nominal inclusion level at this Monte Carlo resolution.

## Boundary from prior W3 qualification programme

R47 does **not** fit an estimated Gaussian covariance model or validate fitted-nuisance-adjusted functional CR2/Satterthwaite pointwise inference. It does not address outcome-driven MNAR point loss, latent complete-participant selection, or additional participant sizes/source supports. It does not calculate **simultaneous whole-function 90% confidence bands**, random-slope boundary variance-component null Type-I error or power, and it cannot justify supported public API promotion, protected-main merge or PyPI publication.

Preserve all original unfavorable evidence R20/R22/R33–R46 and keep scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) OPEN.
