# W3 R13: reproduce R11 exactly, then replicate its complete-source covariance

!!! danger "Research-only simulation oracle, not an empirical interval method"
    R11 reported lower-than-nominal *pointwise* participant CR1
    coverage in a complete-data smooth-mean setting. R12 used
    a separately coded Gaussian generator, different master
    seeds and a known conditional covariance oracle; its
    observed coverage was closer to nominal. R13 first
    reproduces R11's **identical original complete-source
    participants, covariates, random effects, trial timings
    and measurement innovations**, then independently
    replicates the **same R11-generating design** with
    new seeds. It changes **only the generating master seed**
    for the fresh cohort, not model assumptions or trial support.

## Two independently generated cohorts

| Cohort | Generating blocks | Known-source conditions |
|---|---:|---|
| Exact historical R11 | 96 | R11 original master seed `202610131107`; call the unmodified `original_full_source(block, "baseline")` |
| Fresh R11-DGP replication | 96 | New master seed `202610139137`, otherwise copied R11 smooth complete-source generator |

All 192 independent generating blocks contain **48 independent
participants** with **unequal 1–3 genuinely asynchronous trials**.
All source recordings are complete; there is no imputed, selected,
masked or deleted sensor coordinate. Participant random intercepts,
random slopes, trial random intercepts and sensor-point
noise are independent Gaussian innovations with source
standard deviations **0.08, 0.045, 0.025, 0.045**, respectively.
The source first-dimensional conditional mean and random-
effect time scalings are *exactly those used in R11*,
not the different alternative source designs of R12.

A source reproduction test verifies that a separately
programmed R11 generator, supplied the historical
master seed, yields **exactly the same** original
R11 timestamps, two-dimensional values, conditional
means, participant predictors, trial counts,
dropout uniforms and source truth for fixed
blocks. Dropout uniforms are generated but **not**
used to hide any source records in R13.

Each block fits **two prespecified mean bases** on the
same original complete values: degree-five Legendre
and a 13-term fixed-knot cubic spline.
There are **384 model/source cases** but **192**
independent source blocks across both cohorts; the
two fitted mean bases within a block are paired,
not additional independent replications.

## Prespecified pointwise uncertainty

The target is the **known original generating
condition slope at t=0.5** in the first
response dimension. Every model uses the same
original participant-balanced WLS point
estimator and two nominal **90% POINTWISE**
uncertainty constructions:

1. **Original R11 participant CR1/t:** original
   weighted regression coefficient, independently
   checked participant score-sandwich standard
   error, and Student `t(47)` critical value.
2. **Known conditional Gaussian oracle/normal:**
   the *same fitted point estimate*, an analytical
   Gaussian variance conditional on every exact
   original participant predictor, trial allocation,
   true jittered timestamp and numerical weight,
   and the true generating participant/trial/sensor
   variance parameters. Reference critical value
   is standard normal.

To independently reconstruct the oracle, sum
the known trial-level and timepoint-level
innovation covariance contributions within
each participant. **Sum shared participant
random intercept and random-slope score
contributions over all trials BEFORE taking
outer products**. This preserves the actual
repeated-trial dependence, unlike timepoint
or trial independence.

Every source/model fit must satisfy:
- Independent source-level weighted normal
  equations agree with a separate weighted
  least-squares/QR regression.
- Grouped residual participant scores agree
  with direct summation over each source
  participant's original observations.
- The CR1 point estimate and standard error
  agree with the independently implemented
  R11 numerical reference.
- Real observed source native time/values
  remain unchanged and the supported
  common-grid W3 continues to **reject**
  genuine irregular sources.
- The exact historical original R11 cohort
  reproduces the previously recorded smooth,
  complete-case CR1 inclusion counts:
  **80/96 degree five** and **77/96 spline**.
  This is an independent *historical
  reproducibility contract*, not a desired
  new-dataset coverage success threshold.

## Original source outputs

Report per cohort and mean basis:
- CR1/t and oracle/normal **90% pointwise**
  known-true slope inclusion from the 96
  independent generating blocks, with
  95% Wilson Monte Carlo intervals.
- Participant CR1 standard error divided
  by known-source Gaussian oracle standard
  error, and mean widths for both intervals.
- True slope error and deterministic
  known-mean projection error separately,
  to avoid attributing a mean-model
  problem to the covariance formula.
- Standardized error using the simulation
  oracle, as well as a standardized error
  centered on the fitted known-mean
  projection. Neither assumes fitted
  residuals are independent timepoints.
- Paired original-block comparisons of
  truth inclusion between CR1 and the
  exact source covariance, with a
  prespecified 3,000-resample
  block Monte Carlo interval.
- Failure-inclusive original 384-case
  JSON ledger, complete summary,
  original Matplotlib SVG, checkout
  SHA, and independently checkable
  SHA256 digests.

No new-cohort coverage result, method
ranking, preferred interval width or
p-value is an automated success gate.
An oracle coverage deviation is a
scientific outcome to preserve, not a
reason to retune the generator or
remove cases.

## Boundaries

Because the oracle uses **true simulation
variance parameters** it is not an
empirical method for human eye tracking,
a functional random-effects likelihood
fit, an automatic variance estimator
or a valid latent-MNAR correction.
Comparing two pointwise interval methods
does not provide simultaneous
full-trajectory coverage, multiparameter
Type-I control, or generalized
statistical calibration. The 96 original
blocks are reused *only to reproduce*
a previously recorded outcome; the
96 fresh blocks supply an independent
matched-DGP replication.

```bash
python -m pip install -e ".[dev]"
python scripts/run_w3_r13_exact_r11_conditional_oracle.py \
  --out build/w3-r13-original
```

This is an isolated research-only descendant
of [R12](w3-r12-complete-cluster-variance-oracle-results.md).
W3 inferential blocker
[#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
and missing/irregular-support blocker
[#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
remain open. Published **1.1.0**
and unreleased development
**`1.2.0rc2.dev0`** remain unchanged,
`production_release_ready=false`.
No tag, RC, PyPI upload or public
estimator promotion is authorized.
