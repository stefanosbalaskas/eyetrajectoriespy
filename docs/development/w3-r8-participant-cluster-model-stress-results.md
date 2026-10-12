# W3 R8 — participant-cluster uncertainty and mean-model misspecification

!!! danger "Pointwise finite-sample evidence; no simultaneous inferential qualification"
    This prespecified simulation establishes a **specific undercoverage
    problem** when native asynchronously sampled repeated-trial gaze
    is treated as independent measurements or trials. Participant
    clustering materially improves pointwise truth inclusion under
    the tested smooth generating mean, but **does not cure systematic
    coefficient projection error from a misspecified time basis**.
    These are neither simultaneous functional bands nor evidence
    that an irregular-data inference API is ready for publication.

## Original source and independent evidence

Original [scientific workflow #38240534823](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38240534823)
retained artifact **`11742673021`**,
`w3-r8-original-cluster-uncertainty-evidence`. The original
artifact contains `case-ledger.json`, `evidence.json`,
`source-cluster-pointwise.svg`, `source-commit.txt`
and `SHA256SUMS`. It was downloaded independently and **all
4/4 SHA256 source hashes matched**. The source-run checkout SHA
recorded in the original artifact is
`7eafc0c5ef2d1a3f7a061e6f03cd9953552ae3e2` (which may
be a GitHub pull-request checkout identity).

**512/512 planned source cases completed**, with **zero fitting,
numerical-reference or source-contract failures**, and no
missing ledger rows. The complete script uses a new original
seed family `202610125903`, with **64 independent generating
blocks of 48 independent participants**, up to three genuinely
asynchronously timed trials, and matched within-block
comparisons across balanced/unequal trials, MCAR/latent-outcome
recording loss and baseline/localized-bump generating truths.
Thus **512 fits are not 512 independent source datasets**.

The analysis fits an explicit **degree-five Legendre time-basis
participant-balanced regression** to originally observed native
times/coordinates; every participant's aggregate numerical
weight is one. The pointwise condition-slope target is the
known coefficient at time `0.5` in response dimension `x`.

## Original 90% pointwise truth inclusion

Every count is from **64 independent generating blocks per
scenario**. The same point estimate is used across all three
uncertainty constructions; only source score grouping and
reference critical values differ.

| Trial design, loss, generating truth | Naive gaze-observation HC1 | Trial-cluster CR1 | Participant-cluster CR1 |
|---|---:|---:|---:|
| Balanced three trials · MCAR · baseline | 17/64 (26.6%) | 40/64 (62.5%) | **55/64 (85.9%)** |
| Balanced three trials · latent loss · baseline | 25/64 (39.1%) | 48/64 (75.0%) | **54/64 (84.4%)** |
| Unequal 1–3 trials · MCAR · baseline | 21/64 (32.8%) | 51/64 (79.7%) | **55/64 (85.9%)** |
| Unequal 1–3 trials · latent loss · baseline | 32/64 (50.0%) | 53/64 (82.8%) | **55/64 (85.9%)** |
| Balanced three trials · MCAR · localized bump | 0/64 (0.0%) | 2/64 (3.1%) | **5/64 (7.8%)** |
| Balanced three trials · latent loss · localized bump | 0/64 (0.0%) | 1/64 (1.6%) | **2/64 (3.1%)** |
| Unequal 1–3 trials · MCAR · localized bump | 0/64 (0.0%) | 4/64 (6.3%) | **9/64 (14.1%)** |
| Unequal 1–3 trials · latent loss · localized bump | 0/64 (0.0%) | 1/64 (1.6%) | **2/64 (3.1%)** |

![Original-source-audit-derived R8 comparison across all eight pointwise coverage scenarios](../assets/research/w3-r8-pointwise-cluster-coverage-20261012.svg)

*Nominal target: **90% pointwise** coverage at one time and one
slope response dimension. The chart reproduces every original
case-ledger-derived coverage count; the original Matplotlib SVG
is retained unchanged in the source artifact. These simulated
observations are not empirical eye-tracking measurements.*

For example, **55/64 = 85.9%** has a Wilson 95% Monte Carlo interval
approximately **75.4–92.4%**. The finite 64-block source
cannot establish that observed 85.9% means the method is
universally calibrated at 90%. The original evidence JSON retains
the Wilson interval for every individual method/cell.

## Why grouping rather than nominal sample count matters

The independent generating unit is the **participant**.
Repeated trial observations and native gaze timepoints share
participant-level random intercept and slope contributions.
Treating those records as independent can greatly understate
regression coefficient uncertainty.

Observed **mean interval widths** in two baseline MCAR
conditions illustrate the precision cost:

| Trial support | Naive HC1 | Trial-cluster CR1 | Participant-cluster CR1 |
|---|---:|---:|---:|
| Balanced three trials | 0.0212 | 0.0551 | **0.0893** |
| Unequal 1–3 trials | 0.0284 | 0.0736 | **0.0928** |

The wider participant-cluster intervals yielded considerably
higher full-source pointwise truth inclusion, but a wider
interval is not automatically a valid calibrated interval.
The actual independent count was 48 participants per
dataset. Trial-cluster and participant-cluster CR1 employ
explicit group-score aggregation, finite-cluster corrections
and corresponding t reference critical values. The
ordinary observation-HC1 comparator incorrectly treats
each gaze timepoint as its own variance-sampling unit.

All coefficient fits matched independent QR least-squares
numerical oracles, and participant/trial grouped sandwich
scores were cross-checked against an independent group-by-group
sum. Existing supported common-grid W3 explicitly **rejected
each native irregular input**. No auto-interpolation,
participant exclusion or API replacement occurred.

## Deliberately adverse truth: cluster covariance cannot fix mean bias

The localized-bump generator adds a known condition-slope feature
with amplitude `0.15` near time 0.5 and width `0.055`
to the first response dimension. It is not well represented
by the **fixed degree-five Legendre basis**, even if all
original source mean values were known.

The average *known-mean projection bias* at the focal point,
computed by projecting the **true generating conditional mean**
onto the specified basis at actual recorded timestamps, was
approximately:

| Recording mechanism | Baseline truth | Localized-bump truth |
|---|---:|---:|
| MCAR | Near zero (less than 0.000001 in magnitude) | **−0.0913** |
| Latent-response-dependent loss | Near zero (less than 0.000001 in magnitude) | **−0.0949** |

The sampling estimate also inherits this misspecification.
For example, balanced-MCAR mean signed estimate error
changed from approximately **+0.0041** with the baseline
truth to **−0.0872** with the localized bump. Under
latent-response-dependent missingness and the localized
bump, the corresponding mean signed error was about
**−0.0958**.

As a result, the best observed participant-cluster pointwise
inclusion in the bump scenarios was only **9/64 (14.1%)**;
in the more adverse latent-MNAR cases it fell to
**2/64 (3.1%)**. This is an explicit scientific
*falsification* of any claim that simply using the correct
independent cluster level guarantees nominal 90% inference
under an inadequate mean model.

## Limits and next qualification gates

- **No simultaneous inference:** these are one-time,
  one-dimension *pointwise* 90% intervals. Whole-slope
  and intercept+slope-family bands and Type-I error
  remain unqualified.
- **No verified missingness correction:** the latent
  recording-loss mechanism uses a hidden response residual
  in the generator and cannot be inferred from the
  recorded-only data without additional assumptions.
- **No full functional mixed model:** random participant
  effects exist in simulation, but the regression uses a
  fixed-basis participant-weighted point estimator
  and alternative sandwich formulas, not a fitted
  participant random-effects likelihood.
- **Basis robustness is unresolved:** a later
  independently seeded study should compare predeclared
  richer/spline/basis configurations and evaluate
  their selection/regularization implications,
  *before* using their uncertainty bands in production.
- **Cluster bootstrap/robust inference is unresolved:**
  fresh block and participant-resampling validation are
  needed under correct and misspecified models.
  Successful engineering CI alone cannot select a
  statistical estimator or prove nominal coverage.

[Prespecified R8 protocol](w3-r8-participant-cluster-model-stress-protocol.md)
· [Missingness/irregular support issue #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
· [Independent simultaneous-band blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289).

Stable **1.1.0** remains published; development
**`1.2.0rc2.dev0`** remains unpublished, with
`production_release_ready=false`. No new root API,
method winner, release tag, RC or PyPI upload is authorized.
