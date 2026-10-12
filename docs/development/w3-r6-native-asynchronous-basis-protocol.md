# W3 R6: genuinely asynchronous native observations and a declared time-basis model

!!! danger "Experimental modelling comparison—not missingness or inference qualification"
    W3's supported function-on-scalar workflow requires complete finite
    common-grid trajectories. This research-only module fits **actual
    asynchronous observations** using a separately prespecified polynomial
    time basis. Its smooth predictions on a common evaluation grid are
    **model-based estimates**, not interpolated recorded gaze coordinates,
    recovered unmeasured samples, valid confidence bands or a stable API.

## Why R6 differs from R5

The preceding [native-time support pilot R5](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/297)
considered missing timestamps that were exact subsets of a shared
original grid. It found that available-time least squares could
preserve unaffected observations outside missing windows but could
**not** cure latent-response selection bias inside gaps.

In the present R6 experiment, **each independent curve has its own
strictly increasing measurement times**. The nominal 31-location
source grid is perturbed with independent clipped Gaussian timing
jitter (standard deviation .006 time units, absolute cap ±.010),
while preserving start/end locations and monotonic ordering.
No two independently generated curves are required to share
intermediate timestamps. The time-coordinate change alters the
actual location at which the generating true response is measured.

The prespecified design uses **96 independently seeded generating
blocks** with n=96 independent source curves each. The same original
jittered source, participant-level random response deviations,
observation noise, experimental condition, and observation-loss
uniforms are reused **within block** across three paired loss
mechanisms:

- MCAR: 0.35 probability of an eight-observation gap.
- Condition-dependent MAR: logistic(−0.62 + 1.30 × x).
- Latent-response-dependent MNAR: logistic(−0.62 + 1.30 × x +
  2.70 × hidden midpoint residual / .105).

There are **288 scenario-fit evaluations but only 96 independent
source blocks**, never 288 independent generating replications.
These are simulated independent curves, not repeated participant
trials or real human eye-tracking recordings.

## Prespecified model and weighting contrast

For curve i observed at its **own** recorded times t_ij, the
experimental regression is

\[
Y_i(t_{ij}) = B(t_{ij})^\top\gamma_0 +
x_i B(t_{ij})^\top\gamma_1 + e_i(t_{ij}),
\]

where B is an explicit **degree-five Legendre polynomial basis**
constructed once from `2t−1` and kept fixed for all generating
blocks and conditions. No degree selection, hyperparameter tuning,
time interpolation, trajectory exclusion or fitted missingness
probability model is performed after observing results.

The independent-unit estimand is the condition-effect function.
The methods compared are:

1. **Full jittered-source basis benchmark:** fit the exact same
   declared basis to all *genuinely generated source timepoints*.
   This is an oracle source benchmark, not an implementable
   full-data analysis when recording gaps exist.
2. **Native observed-data curve-balanced least squares:** fit the
   same model to only recorded samples, with observation
   weights `1/n_i` so each independently sampled curve has
   equal total contribution.
3. **Native observed-data sample-weighted least squares:** the
   same source samples and model, each observed point receiving
   equal weight. Curves retaining more samples then contribute
   more to the fitting objective.

The *source* gaze measurements remain untouched. Predicted
functions on the public illustration grid arise from fitted
basis coefficients, not filled-in sensor data. Scientific validity
of those predictions depends on the **specified polynomial mean
model** being sufficiently suitable for the true functions.

Both experimental numerical fits must agree at tolerance 2e−8
with an independently derived **QR/triangular-solve reference**,
not merely run the same OLS routine twice.

## Outcomes and guardrails

For every source block and loss mechanism, record:

- Exact original and retained native timestamps and coordinates,
  full/retained sample counts, monotonicity and source integrity.
- The unchanged current W3 workflow's **explicit rejection** of
  native irregular trajectories (no implicit promotion).
- Original complete-jitter basis slope RMSE, curve-balanced
  observed-source slope RMSE, and equal-sample-weight
  observed-source slope RMSE versus known true slope on the
  31-point illustration grid across two dimensions.
- Signed fitted slope changes at the nominal midpoint relative
  to the same block's full-jitter benchmark; independent-source
  2000-resample Monte Carlo intervals.
- A complete **288-case failure-inclusive JSON ledger**,
  original scientific SVG, source identity, SHA256 fingerprints,
  and three-Python-version numerical-oracle tests.

No desired method ordering, significance or apparent calibration
is an engineering CI pass criterion. A higher or lower RMSE is
an empirical result and does not establish one weighting rule
as broadly preferable. We will retain null, adverse or ambiguous
results in the original source audit.

## Scientific limits

The present basis can be misspecified relative to real gaze
dynamics, saccades, discontinuities or individual functional
trajectories. It does not estimate robust independent-curve
standard errors, confidence bands, longitudinal participant random
effects, MAR/MNAR identification or calibrated 90% inference.
It is a **research comparator**, not a replacement for existing
sparse functional regression, PACE, covariance smoothing or mixed
functional models. Repeated participant trials, multiple
time-varying regressors and real device dropout require separate
validated work.

The analysis makes a transparent model-based prediction at times
where measurements might be absent; **that prediction must never
be described as a directly observed or deterministically recovered
gaze coordinate**.

```bash
python -m pip install -e ".[dev]"
python scripts/run_w3_r6_asynchronous_basis.py \
  --out build/w3-r6-native-async
```

Keep [observation-loss scientific issue #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
and the separate [W3 confidence-band issue #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
OPEN. Stable published **1.1.0** and unreleased development
`1.2.0rc2.dev0` remain unchanged; `production_release_ready=false`.
No new public estimator, release candidate, tag or PyPI upload.
