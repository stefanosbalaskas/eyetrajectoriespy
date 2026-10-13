# W3 R12 — isolating finite-cluster uncertainty with complete native data

!!! danger "Research-only known-covariance simulation"
    R11 observed 80–83% inclusion of known true midpoint slopes
    by nominal 90% pointwise intervals under smooth *complete*
    native-source recordings. R12 removes deliberate observation
    gaps and localized generating mean-model misspecification,
    and introduces a **known generating Gaussian covariance
    oracle**. This oracle depends on simulation-known variance
    components that are **not supplied by real gaze recordings**.

## Prespecified design and independent units

**96 new independently seeded generating blocks** (`202610131212`),
with up to 96 participants and genuinely jittered original
native timestamps. Participant sizes **24, 48 and 96**
are nested within each generating block. Two paired
observed-predictor dispersion regimes use
`x ~ Uniform(-0.95,+0.95)` and
`x ~ Uniform(-0.35,+0.35)`.
All conditions use **one to three complete trials per person**,
the original 31 sensor timestamps *per trial*, and the
smooth mean function approximated essentially exactly by a
**prespecified degree-five Legendre intercept and slope**.

The simulation includes independent Gaussian
participant random intercepts (`sigma=0.08`),
participant random functional slopes (`sigma=0.045`),
trial intercepts (`sigma=0.025`) and
sensor noise (`sigma=0.045`). Original participant
intercept and slope effects are correlated **within**
repeated trials by construction but sampled independently
between people. The fully observed generating mean,
random variables and per-trial timestamps are retained
as source truth. No interpolation or deletion occurs.

There are **96 independent generating blocks × three
nested participant sample sizes × two predictor-support
designs = 576 scenario fits**, but **96 independent
source blocks**, not 576 independent Monte Carlo
replications. Nested designs deliberately share
underlying participant effects and noise within block.

## Fixed point-estimator and variance contrasts

Fit the same **degree-five Legendre time basis**
to actually recorded, completely observed native
timestamps with participant-balanced WLS:
each person's total numerical weight is exactly one,
distributed over their recorded original trials
and timepoints. The only inferential target is the
known condition slope at **t = 0.5 in the first
response dimension**. A fitted value on the
illustration grid is model-based, not a new
observed sensor coordinate.

Four **predeclared nominal 90% pointwise** intervals
share the same fitted coefficient:

| Interval | Uncertainty source and critical value |
|---|---|
| Participant **CR1/t** | Original grouped participant-score sandwich, finite-cluster correction, Student `t(n_people−1)` |
| Participant **CR1/normal** | Exactly the same CR1 variance, normal critical value |
| Whole-participant **delete-one jackknife/t** | Refit the same participant-weighted WLS with each of the independent people deleted in turn, use `(G−1)/G` times leave-one-person slope sum-of-squares, Student `t(G−1)` |
| **Known conditional Gaussian oracle/normal** | Analytic covariance of fitted slope from simulation-known participant intercept/slope, trial random intercept and timepoint sensor-noise variances, normal critical value |

The known oracle is computed *conditional on each
original complete time design, covariate pattern,
participant trial allocation and participant weights*.
It can isolate finite-participant sandwich and
critical-value behavior because the original conditional
Gaussian mean is prespecified and the true covariance
is analytically known. The oracle is **unavailable
from empirical data without strong covariance assumptions**,
and its statistical properties under model misspecification
are deliberately **not** evaluated.

## Independent numerical and source validation

The software validates original source integrity,
the current supported W3 failure to accept genuinely
irregular trial timestamp vectors, and three
independent calculation contracts:

1. Participant-aggregated weighted normal equations
   agree with source-observation WLS and independent
   least-squares reference coefficients.
2. Grouped participant residual scores agree with
   direct independent observation-level source
   summation within each person.
3. The analytic Gaussian participant score-covariance
   formula agrees in a cross-version test with a
   separate explicit dense covariance matrix using
   same-trial and same-participant block correlations,
   computed from the known generating variances.

Results include source-block denominators and
exceptions, 90% pointwise known-truth inclusion
and Wilson 95% Monte Carlo intervals, mean interval
widths and **estimated standard error divided by
known-variance oracle standard error**, the
empirical across-block slope error standard
deviation, and block-paired bootstrap intervals
for method coverage differences. **No desired
coverage or method ordering is a software pass
criterion.** The original complete 576-case JSON
ledger, source Matplotlib figure and SHA256 checksums
must be retained, including any failures.

## Limits and release restrictions

Even an oracle close to 90% in this controlled
complete Gaussian experiment cannot certify
whole-curve **simultaneous** inference, other
non-Gaussian data, dropout, leverage
extremes, time-varying predictors or a functional
mixed-model likelihood. An apparent improvement
from a leave-one-participant estimator does not
select a generally valid uncertainty architecture.
Follow-up must separately test clustered variance
under missed mean features, outcome-dependent
gaze recording and fresh empirical data.

```bash
python -m pip install -e ".[dev]"
python scripts/run_w3_r12_complete_cluster_variance_oracle.py \
  --out build/w3-r12-original
```

This new source work is **stacked on experimental
R11**, and W3 interval-science blocker
[#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
and native observation blocker
[#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
remain OPEN. Stable published **1.1.0**,
unreleased development **`1.2.0rc2.dev0`**,
`production_release_ready=false`;
no public estimator, release candidate, tag
or PyPI upload.
