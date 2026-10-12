# W3 R10: independent whole-participant bootstrap under asynchronous repeated trials

!!! danger "Exploratory, pointwise and deliberately failure-inclusive"
    A participant pairs bootstrap is not automatically a calibrated
    inferential solution. This study compares whole-participant
    resampling against the original participant-cluster CR1
    interval using **fresh** independently generated original
    source blocks, under correct and misspecified mean functions
    and response-dependent recording loss. No public API,
    simultaneous band, missing-data correction, selected
    estimator or release follows.

## Prespecified source independence and repeated observations

- **64 independently seeded generating blocks**, using a new R10
  seed family `20261012105731`; 48 independent participants
  per source block and genuinely jittered observed trial
  timestamps.
- Four source dimensions crossed to form **eight paired scenarios
  per block**: three versus one-to-three trials, MCAR versus
  unobserved-response-dependent eight-point recording gaps,
  and smooth baseline versus localized true slope feature
  of width 0.055 and amplitude 0.15.
- Within generating block, participant conditions,
  random intercepts and slopes, trial effects, native timing,
  sensor innovations and observation-loss uniforms are
  paired across the scenarios. Loss assignment may still
  produce a different *recorded subset* by mechanism,
  and it does not make all 512 scenario fits independent.
- Two **fixed** models, without tuning or adaptive selection:
  degree-five Legendre mean function and thirteen-term
  cubic B-spline with the nine knots fixed in R9.
  Each model uses equal total numerical regression
  weight per *independent participant*, not trial.

The source work comprises **512 generating source scenarios,
1,024 original participant-weighted regression fits, and
199 entire-participant bootstrap refits per model-case**
(**203,776** bootstrap refits planned). Inference over
replicated generating datasets has **64 independent
source blocks per scenario**, *not* the number of
resampled participants, recorded trials or gaze points.

## Two participant-level uncertainty approaches

The functional condition-slope is evaluated **at one
prespecified midpoint, time 0.5, first response
dimension**. The confidence level is nominal 90%
**pointwise**, not family-wise or simultaneous.

1. **Participant CR1 with t(47):** original
   participant-weighted least-squares coefficient
   estimator, sandwich score sums aggregated over
   each of the 48 independent participants, explicit
   finite-cluster scaling and 47-degree t
   critical value. Repeated native observations
   and trials are not treated as independent
   groups.
2. **Whole-participant pairs bootstrap:** draw exactly
   48 participant IDs *with replacement* on each of
   **199** prespecified bootstrap replicates.
   A repeated participant carries *all* original
   observed trials and actual timepoints, with
   their original normalized per-person
   regression contribution. No timepoint-level
   resampling or deleted native records.
   Report both equal-tail percentile and
   basic reflected percentile intervals.

The basic bootstrap reflects the finite bootstrap
deviations around the original point estimate;
the percentile bootstrap takes direct empirical
bootstrap quantiles. Neither is a studentized
bootstrap-t, BCa, constrained bootstrap or
a simultaneously calibrated process. Under
bias from mean-model misspecification or latent
response-dependent missingness, both may
continue to under-cover the **known truth**.
A bootstrap centered on a biased estimator
does not make the estimator unbiased.

## Reproducibility and numerical independence

For each participant, the script constructs
original weighted normal-equation crossproducts
`Q_i = sum_j w_ij X_ij'X_ij`,
`v_i = sum_j w_ij X_ij'Y_ij`
over all genuinely recorded trials/timepoints.
The source fit solves `sum_i Q_i beta =
sum_i v_i`. A separate original weighted
least-squares calculation must agree numerically.
Original participant residual-score sums must
agree with an independent source-observation
grouping oracle.

Each pairs-bootstrap draw is a **48-count
multinomial multiplicity vector over entire
participants**, applied to the same original
participant-level crossproducts. One source
replicate is independently recomputed in tests
from the explicit recorded multiplicity vector.
No source trial or timepoint is independently
drawn after the participant selection.

Each original case must preserve:
- Source recorded participant and trial counts,
  native observations/timestamps, and explicit
  unchanged-source/fail-closed dense-W3 flags.
- Original estimate, known true slope, known-mean
  projection bias and true-point signed error.
- Three interval endpoints, widths and known
  truth-inclusion indicators; independent
  Wilson 95% Monte Carlo limits over the
  **64 source blocks** in every cell.
- Exactly 199 planned/finished participant
  bootstrap refits per model, bootstrap
  standard deviation, and the first source
  draw's 48 sampled IDs, participant
  multiplicities and numerical fitted slope.
- An original failure-inclusive 512-scenario
  JSON ledger, original Matplotlib figure,
  source checkout identity and SHA256 checksums.

**Statistical coverage values are not engineering CI gates.**
A simulated undercoverage result is a finding, not a reason to
delete a case or adjust parameters in response to the result.
All fitting/source failures remain recorded in denominators.

## Scientific limitations

Even if one procedure's observed pointwise inclusion
approaches 90% under these source conditions, its Wilson
Monte Carlo interval remains broad at 64 independent
generating blocks. A nominal pointwise result is not
a functional 90% simultaneous band, a statement
about family-wise false positive rates or evidence
for general uncertainty calibration.

Pairs bootstrapping whole participants avoids treating
their repeated trials as independent, but does **not**
identify latent observation selection, repair a
misspecified mean function, fit a full mixed-effects
likelihood, or validate a Bayesian posterior.
Only two fixed mean bases and 199 resamples per
case are compared; that inner bootstrap budget
has its own Monte Carlo error. Higher-budget,
new-data replication is a separate future task.

```bash
python -m pip install -e ".[dev]"
python scripts/run_w3_r10_participant_pairs_bootstrap.py \
  --out build/w3-r10-participant-pairs
```

The work remains isolated on an exploratory research
branch stacked after
[R9 source validation](w3-r9-prespecified-mean-basis-results.md).
Keep independent
[simultaneous-band calibration blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
and [missing/irregular observation blocker #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
OPEN. Published stable **1.1.0**, unpublished development
`1.2.0rc2.dev0` and
`production_release_ready=false` remain
unchanged; no tag, RC, PyPI release or
public statistical API promotion.
