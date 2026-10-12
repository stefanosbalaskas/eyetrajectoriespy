# W3 R10 — independent whole-participant bootstrap uncertainty evidence

!!! danger "Negative original scientific evidence: no calibrated bootstrap method established"
    The original source study completed **all 512 planned
    scenarios and all 203,776 prespecified participant-pairs
    bootstrap refits**. Neither a simple percentile nor a
    basic whole-participant bootstrap consistently achieved
    nominal 90% **pointwise** true-slope inclusion. Correct
    resampling units did not remove localized mean projection
    bias or latent-response-dependent recording-loss bias.
    These outcomes do **not** validate simultaneous functional
    inference or a new public estimator.

## Original source and audit trail

[Original scientific workflow #38308085262](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38308085262)
completed **512/512** original source scenario cases, with **zero
scientific fitting/source/numerical-oracle failures or missing
ledger entries**. Its GitHub Actions artifact
**`11774040581`**,
`w3-r10-original-participant-pairs-bootstrap`, contains
the complete `case-ledger.json`, `evidence.json`,
original Matplotlib
`source-pairs-bootstrap-pointwise.svg`,
`source-commit.txt` and
`SHA256SUMS`. The original ZIP was independently downloaded;
**all four SHA256 entries were independently verified**.
The source checkout SHA recorded in the original artifact is
`716f568416e854d258aa18faefe6d044f4f009ac`
(which may reflect a transient GitHub pull-request checkout).

The generating seed family is `20261012105731`,
**64 independently seeded blocks of 48 independent
participants each**, with up to three genuinely
asynchronous native trial recordings. All eight paired
source regimes cross balanced versus uneven
one-to-three trial support, MCAR versus
latent-response-dependent short recording
gaps, and baseline smooth versus localized-bump
true condition-slope function. The 512 source
scenarios are *correlated within block*, not
512 independent Monte Carlo replications.

The prespecified original analysis used two fixed
mean bases, Legendre degree five and the thirteen-term
cubic spline, each with equal total numerical
weight per independent participant. For every
original model/source case it computed a
participant CR1 90% interval and **199 whole-participant
resampling fits**, generating both percentile and
basic 90% pairs-bootstrap intervals.
Consequently there were **1,024 original fitted
model/source cases and 203,776 completed cluster
bootstrap refits**, not additional independent
generating datasets.

Original source data and all genuine native time
coordinates were unchanged throughout. Existing
supported common-grid W3 continued to reject
irregular sources. Source weighted OLS coefficients,
participant sandwich scores and one explicitly
recorded participant-bootstrap refit were
checked against independent numerical calculations.
All Python 3.11–3.13 reference tests passed.

## Full 90% pointwise truth-inclusion comparison

Every numerator below counts inclusion of the known
generating *midpoint condition slope*, not coverage
of a simultaneously estimated trajectory. The
denominator is **64 independent generating blocks
per cell**.

| Trial support / loss / true mean | Mean basis | Participant CR1 | Participant pairs percentile | Participant pairs basic |
|---|---|---:|---:|---:|
| 3 trials · MCAR · smooth | Legendre-5 | 53/64 (82.8%) | 50/64 (78.1%) | 52/64 (81.3%) |
| 3 trials · MCAR · smooth | Cubic spline | 51/64 (79.7%) | 50/64 (78.1%) | 51/64 (79.7%) |
| 3 trials · MCAR · local bump | Legendre-5 | 4/64 (6.3%) | 4/64 (6.3%) | 4/64 (6.3%) |
| 3 trials · MCAR · local bump | Cubic spline | 50/64 (78.1%) | 51/64 (79.7%) | 50/64 (78.1%) |
| 3 trials · latent loss · smooth | Legendre-5 | 51/64 (79.7%) | 50/64 (78.1%) | 51/64 (79.7%) |
| 3 trials · latent loss · smooth | Cubic spline | 45/64 (70.3%) | 45/64 (70.3%) | 47/64 (73.4%) |
| 3 trials · latent loss · local bump | Legendre-5 | 1/64 (1.6%) | 1/64 (1.6%) | 2/64 (3.1%) |
| 3 trials · latent loss · local bump | Cubic spline | 43/64 (67.2%) | 40/64 (62.5%) | 42/64 (65.6%) |
| Unequal trials · MCAR · smooth | Legendre-5 | 53/64 (82.8%) | 54/64 (84.4%) | 52/64 (81.3%) |
| Unequal trials · MCAR · smooth | Cubic spline | 53/64 (82.8%) | 51/64 (79.7%) | 52/64 (81.3%) |
| Unequal trials · MCAR · local bump | Legendre-5 | 5/64 (7.8%) | 3/64 (4.7%) | 4/64 (6.3%) |
| Unequal trials · MCAR · local bump | Cubic spline | 51/64 (79.7%) | 51/64 (79.7%) | 51/64 (79.7%) |
| Unequal trials · latent loss · smooth | Legendre-5 | 50/64 (78.1%) | 49/64 (76.6%) | 49/64 (76.6%) |
| Unequal trials · latent loss · smooth | Cubic spline | 48/64 (75.0%) | 49/64 (76.6%) | 51/64 (79.7%) |
| Unequal trials · latent loss · local bump | Legendre-5 | 1/64 (1.6%) | 0/64 (0%) | 1/64 (1.6%) |
| Unequal trials · latent loss · local bump | Cubic spline | 43/64 (67.2%) | 44/64 (68.8%) | 47/64 (73.4%) |

![Original-source R10 bootstrap, participant CR1, pointwise coverage across paired generating conditions](../assets/research/w3-r10-participant-bootstrap-pointwise-20261012.svg)

*The figure is a representation of the independently
verified original JSON evidence. The original
Matplotlib SVG is retained unmodified in the
GitHub artifact. All numbers concern
simulated normalized gaze coordinates and
one pointwise contrast.*

No procedure consistently attained the
nominal 90% target, even when the mean function
was relatively smooth. For example, under
balanced MCAR and smooth truth with degree
five, participant CR1 included the true slope
in **53/64 (82.8%)**, percentile pairs bootstrap
in **50/64 (78.1%)**, and basic pairs
bootstrap in **52/64 (81.3%)**.
The CR1 result has Wilson 95% Monte Carlo
interval approximately **71.8–90.1%**
at 64 independent generating blocks:
finite Monte Carlo precision limits general
claims even in this favorable source scenario.

The same analysis under balanced latent
recording loss with the cubic spline gave
**45/64 (70.3%)** participant CR1,
**45/64 (70.3%)** percentile and
**47/64 (73.4%)** basic true-point
inclusion for the smooth truth. Adding the
localized slope feature yielded
**43/64 (67.2%)**, **40/64 (62.5%)**,
and **42/64 (65.6%)**, respectively.
There was **no reliable generic bootstrap
advantage** in the tested conditions.

## Known source mean projection versus observation bias

The experiment separated two distinct errors:
the basis-projection difference when the **true
generating conditional mean** is fitted into
the fixed model at genuine observed times,
and the full point-estimate difference
from the generating truth including noise
and selective missingness.

Under balanced MCAR and localized-bump
truth, degree-five model mean projection
bias was **−0.09144** at the focal point,
versus **−0.00376** for the cubic spline.
The degree-five signed estimated slope
error averaged **−0.09761**, versus
**−0.01002** with the spline.
Using whole-person resampling **did not
resolve the degree-five projection
error**, and all its bootstrap methods
remained near-zero coverage in the bump
generator.

Under balanced latent-response-dependent
recording loss, cubic-spline projection
bias remained relatively small:
approximately **−0.00392** in the bump
generator and essentially zero in the
smooth generator. Yet its actual mean
estimated slope error was approximately
**−0.03179** for the localized bump
and **−0.02787** for the baseline
smooth truth. This residual error is
consistent with **selective observation
bias and source noise**; a flexible mean
basis or ordinary whole-participant
bootstrap cannot identify the hidden
dropout mechanism.

## Width, independence and limitations

Balanced MCAR smooth mean interval widths
for degree five were approximately
**0.09114** (CR1),
**0.08870** (percentile) and
**0.08870** (basic).
The basic and percentile intervals
have identical widths by construction
but different locations; they
cannot be assumed to have identical
coverage. Similarly, more bootstrap
draws might reduce inner-quantile
Monte Carlo error but would **not**
necessarily remove mean or observation
selection bias.

The source code samples 48 original
participant identities *with replacement*
per replicate, carrying the entire
original repeated-trial record,
original timing and original
within-participant numerical weights.
It does not resample individual gaze
time samples or treat repeated
trials as independent source units.

This study does **not** establish
whole-function 90% simultaneous-band
coverage, a functional mixed-effects
covariance estimator, valid family-wise
testing, a corrected MNAR mechanism,
a Bayesian posterior guarantee, an
optimal time basis, or a generally
calibrated bootstrap. The 199-draw
inner bootstrap and 64 independent
outer generating blocks are
modest evidence budgets that
must be replicated on fresh
datasets and broader plausible
observation mechanisms before any
inferential architecture decision.

[Prespecified R10 protocol](w3-r10-whole-participant-bootstrap-protocol.md)
· [W3 calibration blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
· [Missing and irregular support blocker #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296).

All work remains in a research draft.
Stable published **1.1.0** and
unreleased development
**`1.2.0rc2.dev0`**
remain unchanged, with
`production_release_ready=false`.
No public estimator, production
qualifier, tag, RC or PyPI upload
is authorized.
