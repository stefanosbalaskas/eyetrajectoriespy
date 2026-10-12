# W3 R8: participant-cluster pointwise uncertainty under mean-basis stress

!!! danger "Source-prespecified statistical stress study, not confidence-band approval"
    W3's native genuinely asynchronous participant/trial regression
    remains an experimental research comparator. This R8 simulation
    evaluates whether standard errors constructed at the independent
    **participant** level behave differently from estimates that treat
    recordings or timepoints as independent. It deliberately introduces
    an unmodelled localized slope feature. Neither a pointwise 90%
    result nor green CI qualifies a simultaneous band, functional
    mixed-effects estimator, MAR/MNAR correction or public API.

## Independence and paired source design

Following [R7](w3-r7-repeated-trial-asynchronous-results.md), R8
has a fresh seed family `202610125903`, **64 independently seeded
generating blocks**, each with **48 independent participants** and
genuinely jittered trial timepoints. The participant condition and
random intercept/slope effects are shared across up to three trials.
The eight generating scenarios are **matched within each block**:

| Factor | Prespecified conditions |
|---|---|
| Trial allocation | Three trials per participant; or one-to-three trials |
| Observation mechanism | MCAR short gaps; latent-response-dependent gaps |
| Generating slope truth | R7-style smooth baseline; the same truth with a narrowly localized added slope bump |

There are **512 attempted scenario-fit cases**, but **64 independent
source generating blocks**, not 512 exchangeable replicates.
The source uses the same original participant x, random effects,
time jitter, trial effects, measurement innovations and gap uniforms
across all paired conditions. The changed truth is one extra
known-condition slope feature in the first response dimension:

`0.15 * exp(-0.5 * ((t - 0.5)/0.055)^2)`.

The bump is intentionally sharper than the fixed degree-five
Legendre mean model readily represents. Thus an apparently
small standard error can fail to cover the **true** slope because
the mean model is misspecified, even if the covariance formula
matches the intended independent sampling unit.

## Prespecified inference comparison

All three comparisons use the **same** genuinely recorded native
observations and the same fixed-degree-five participant-balanced
weighted regression. Each participant has total weight one,
distributed across their recorded trials and time samples. The
single prespecified estimand is the slope function at nominal
time `t=0.5` in response dimension `x`, estimated from
model coefficients. This is a **pointwise** rather than
family-wise/whole-function estimand.

Compare:

1. **Naive observation HC1:** each gaze timepoint contributes a
   separate sandwich score and approximate t critical value with
   `n_rows - 1` degrees of freedom. This ignores repeated
   timepoints and repeated trials as dependence sources.
2. **Trial-cluster CR1:** sum the weighted scores within each trial,
   use the finite-trial-group sandwich adjustment and
   `n_trials - 1` degrees of freedom. This still ignores the
   correlation of repeated trials within participants.
3. **Participant-cluster CR1:** sum weighted scores across **all
   trials and time samples from each independent participant**,
   apply an explicit CR1 small-sample scaling and critical value
   with **47** degrees of freedom.

The point estimates are identical in these contrasts; only
the independently calculated uncertainty/reference critical
values change. All three use the original weighted least
squares estimator, and the numerator coefficients must
agree with a separate QR numerical reference. Cluster-score
aggregation is also verified by an independent per-group
summation implementation. Original source records must retain
48 independent participant IDs under all scenarios; the
supported complete-grid W3 workflow must reject the raw
native irregular inputs, without interpolation.

### Evidence planned before seeing simulation results

For every prespecified scenario report:
- **64 independently generated source cases** attempted,
  completed, missing and failed, preserving every exception.
- Nominal **90% pointwise inclusion** of *known generating truth*
  with Wilson 95% Monte Carlo intervals per method and scenario.
- Mean pointwise standard errors and interval widths for naive
  gaze-point HC1, trial-cluster CR1 and participant-cluster CR1.
- Signed observed slope error versus generating truth, plus
  the deterministic **known-mean projection error** from fitting
  the declared degree-five basis to source-known mean values at
  the actual observed timestamps. The latter measures
  model-projection misspecification, not sampling uncertainty.
- Original source, exact natural participant/trial ID hierarchy,
  complete 512-case ledger, source-derived original scientific
  SVG, git checkout source identity and full SHA256 checksums.

No desired nominal coverage, winner, method ordering, or
evidence outcome will be an automated CI pass criterion. An
undercovering cluster-robust interval is a scientific result, not
a software-contract failure.

## Essential scope limits

This is **one selected pointwise coefficient contrast**;
it does not establish 90% *simultaneous* slope-function or
family-wide intercept/slope confidence bands. CR1 with
48 independent participants has finite-sample limitations,
especially under leverage, observation-process selection and
mis-specified mean functions. Clustered covariance estimation
does **not** repair a biased conditional mean or identify
latent-response-dependent missingness.

No participant random-effects likelihood, native
functional GLMM, Bayesian posterior interval, calibrated
bootstrap-t, model-selection routine or automatic missing-gaze
handling is introduced. A separately prespecified
participant-level bootstrap study with fresh source blocks
will be needed before any broader inferential architecture
can be considered.

```bash
python -m pip install -e ".[dev]"
python scripts/run_w3_r8_cluster_inference_model_stress.py \
  --out build/w3-r8-participant-cluster
```

Original work remains in [draft R7 PR #299](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/299)
and open scientific issues
[missing/irregular gaze #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
and [simultaneous-band calibration #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289).
Published stable **1.1.0** and unreleased development
**`1.2.0rc2.dev0`** remain unchanged, with
`production_release_ready=false`; no tag, RC,
production statistical API or PyPI release.
