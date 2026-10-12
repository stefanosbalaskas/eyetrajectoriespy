# W3 R9: prespecified richer mean bases, participant-cluster uncertainty

!!! danger "Experimental statistical science, not automatic model selection"
    Earlier [W3 R8 research](w3-r8-participant-cluster-model-stress-results.md)
    showed severe noncoverage of the true local slope under an
    insufficient degree-five mean basis—even after using
    participant-cluster uncertainty. R9 tests **three
    fixed, declared models** on **fresh** original source
    datasets. None is selected for the supported API,
    and any improved pointwise inclusion must not be
    promoted as valid simultaneous functional inference.

## Scientific design: independent source blocks and pairing

- **64 NEW independently seeded source blocks**, master seed
  `202610129917`, distinct from R8. Each block generates
  48 independent participants and up to three genuinely
  asynchronous repeated trials per participant.
- Eight *paired* scenarios per block, crossing balanced
  three versus uneven one-to-three supported trials, MCAR
  versus latent-response-dependent recording loss, and
  baseline smooth versus added localized slope truth.
- In the localized truth, the first-dimensional
  condition-slope adds a Gaussian feature of amplitude
  **0.15** centered at time **0.5**, width **0.055**;
  hidden loss probability depends on the generated
  response residual. These are known simulation truths
  unavailable to an empirical analyst.
- Trial timestamps are genuinely jittered per trial.
  Gaps remove the middle eight source observations from
  selected trials; recorded native time and response
  arrays are never interpolated or imputed.
- **512 source scenarios** × three fixed mean models
  = **1,536 prespecified regression fits**. The
  Monte Carlo independent sample size is **64 generating
  blocks**, not 512 or 1,536. Trials, timepoints and
  correlated conditions are not independent blocks.

## Three original, fixed and openly specified bases

The same participant-balanced, observed-source weighted
least-squares regression is used for all models. Every
recorded timepoint of trial j from participant i receives
numerical weight `1/(k_i * n_ij)`, preserving equal total
weight per independent participant. No data-driven smoothing
parameter, cross-validation or post hoc best-model
selection is applied.

| Label | Fixed generating basis | Coefficient count (intercept + slope) |
|---|---|---:|
| `legendre5` | Legendre time polynomial of degree five, R8 comparator | 12 |
| `legendre11` | Legendre polynomial of degree eleven | 24 |
| `cubic_spline13` | Degree-three B-splines, boundary knots repeated four times at zero and one, **nine equally spaced interior knots at 0.1, 0.2, …, 0.9** | 26 |

All parameterizations are fixed before scientific source
results. A more flexible model can reduce deterministic
basis-projection error while also changing variance and
finite-participant leverage. It may introduce its own
undercoverage, especially under correlated observations
or response-dependent recording loss.

The slope function evaluated at the nominal 31-point
grid is explicitly a **model prediction**, not a
reconstructed sensor observation. The predeclared
target is the generating condition-slope at `t=0.5`,
first response dimension; R9 compares **nominal 90%
pointwise** intervals based on participant-cluster
CR1 with 48 independent participants and 47 t
reference degrees of freedom. These are not
whole-function or family-wise bands.

## Required original scientific evidence

The original science run must preserve for every
512 scenario and each of three mean specifications:

- Actual native timepoint/participant membership,
  observed sample count, independent numerical QR
  and participant-score aggregation references,
  complete failures and source identity.
- Known-truth slope-function RMSE and focal pointwise
  signed slope error.
- Separate *known-mean projection error* from the
  true source mean fitted into each declared basis
  at the **same originally observed timestamps**,
  isolating basis misspecification from random
  participant noise.
- Participant CR1 SEs, widths, true-slope inclusion
  in 90% pointwise intervals, and Wilson 95%
  intervals over the **64 independent generating
  blocks** in every factorial source cell.
- Paired model-minus-degree-five bootstrap
  contrasts for pointwise inclusion, projection
  bias and full-slope RMSE, resampling independent
  generating blocks for **2,000 replicates**.
- Original unmodified scientific SVG, source
  recorded `GITHUB_SHA`, complete JSON case
  ledger, evidence summary and SHA256 checksums.

Source failures are part of evidence; exact full-case
completion is an engineering audit gate, but
**coverage, desired RMSE and model preference
are never CI pass criteria**.

## Strict statistical and governance limitations

Participant-weighted OLS with a CR1 variance estimator
does not fit a functional hierarchical random-effects
likelihood. This one-point cluster sandwich stress
cannot establish correct covariance across the
slope function, simultaneously calibrated bands,
Type-I error control over time, or MNAR
identification. Improvement relative to degree five
within this *specific known localized bump* must
not be portrayed as universal statistical superiority.

This R9 source study is scientifically isolated from
protected main and does not change existing
`eyetrajectoriespy` estimators, their public API,
the `IrregularTrajectorySet` fail-closed support
boundary, or automatic preprocessing.

```bash
python -m pip install -e ".[dev]"
python scripts/run_w3_r9_mean_basis_selection_stress.py \
  --out build/w3-r9-original-basis
```

[W3 interval scientific blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
and [missing/irregular support #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
remain OPEN. Published stable **1.1.0**, unreleased
`1.2.0rc2.dev0` and `production_release_ready=false`
remain unchanged; no RC/tag/PyPI publication.
