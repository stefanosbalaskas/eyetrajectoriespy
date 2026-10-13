# W3 R12 — source-verified complete-data variance diagnostics

!!! danger "Controlled simulation, not a confidence-band calibration certificate"
    In a **new independent source study** with fully observed genuinely
    asynchronous repeated trials and a sufficiently represented mean,
    participant-cluster CR1 pointwise truth inclusion was **89.6–91.7%**.
    An analytic conditional Gaussian oracle covered **89.6–93.8%**.
    The result did **not reproduce** the comparatively low 80–83%
    complete-source coverage in R11, but neither proves
    universal pointwise calibration nor validates whole-function
    simultaneous confidence bands. The generating designs and
    random seed families differ across R11 and R12.

## Original source, design and verification

The original [scientific workflow #38349342996](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38349342996)
completed **576/576** original cases with **zero
fitting, source-integrity, numerical-oracle or
failure-ledger exceptions**. All Python 3.11,
3.12 and 3.13 tests, including an independent
**dense covariance-matrix oracle comparison**,
passed. Original scientific artifact **`11790091707`**,
`w3-r12-original-complete-variance-oracle-evidence`,
was independently downloaded; **all four original
SHA256 checksums matched**. The complete source
ledger, JSON evidence, original Matplotlib plot
`source-complete-cluster-oracle.svg`, source
identity and `SHA256SUMS` were retained.

The original workflow recorded checkout SHA
`8ddba77891ae6d8266fe33b2cc156d531ceb2cbe`,
which may be a transient GitHub pull-request
checkout identity.

The fresh original source has **96 independently
seeded generating blocks** (`202610131212`).
Within each block, a nested set of 24, 48 or 96
participants is analysed with two prespecified
predictor-spread regimes. Every participant
contributes one to three *complete*, genuinely
asynchronously timed original trials. There
is **no deliberately missing gaze** and no
localized-bump generating truth. The fixed
degree-five Legendre mean specification
represents the smooth generating slope to
essentially numerical precision.

The first response dimension is the measured
generating signal in this diagnostic; the second
is a fixed zero-valued companion dimension
required by the trajectory container.
This test is **not** a two-dimensional
real-device accuracy assessment.

Each original observation keeps its authentic
generated native timestamp. No interpolation,
participant deletion or timepoint-level
resampling occurs. There are **576
scenario fits but only 96 independent source
generating blocks**, since sample sizes are
nested and predictor support is paired within
blocks. Independent groups for inferential
variance are the recruited **participants**,
not their timepoints or trials.

## True midpoint slope inclusion of nominal 90% intervals

All entries are the number of **96 independent
generating blocks** in which the interval
included the known true smooth midpoint slope.

| People | Predictor support | Participant CR1 / t | Same CR1 / normal | Delete-one-participant jackknife / t | Known Gaussian oracle / normal |
|---:|---|---:|---:|---:|---:|
| 24 | Broad | 86/96 (89.6%) | 86/96 (89.6%) | 86/96 (89.6%) | 86/96 (89.6%) |
| 48 | Broad | 88/96 (91.7%) | 88/96 (91.7%) | 88/96 (91.7%) | 90/96 (93.8%) |
| 96 | Broad | 88/96 (91.7%) | 87/96 (90.6%) | 88/96 (91.7%) | 89/96 (92.7%) |
| 24 | Narrow | 87/96 (90.6%) | 83/96 (86.5%) | 87/96 (90.6%) | 90/96 (93.8%) |
| 48 | Narrow | 88/96 (91.7%) | 87/96 (90.6%) | 89/96 (92.7%) | 90/96 (93.8%) |
| 96 | Narrow | 88/96 (91.7%) | 87/96 (90.6%) | 88/96 (91.7%) | 87/96 (90.6%) |

![W3 R12 complete source pointwise coverage for participant CR1, normal, delete-one jackknife and known conditional Gaussian oracle](../assets/research/w3-r12-complete-source-cluster-oracle-coverage-20261013.svg)

*This figure is reconstructed directly from
verified original source-audit case counts;
the original Matplotlib SVG is preserved
unchanged in scientific artifact 11790091707.
No model is qualified for 90% simultaneous
functional confidence bands.*

The source supports **no general inference that
jackknife clustering is better** than CR1.
For broad support at 48 participants, both
included the true slope in 88 of 96 independent
generating blocks. The 95% Wilson Monte Carlo
interval for **88/96** is approximately
**84.4–95.7%**, wide enough that small
differences among methods should not drive
a selection decision. The original JSON
retains all per-cell Wilson intervals and
prespecified 3,000-resample paired block
Monte Carlo contrasts.

## Estimated variance compared with the known source covariance

The source generator contains independent
normal participant random intercepts,
random participant slopes, trial-level
intercepts and sample noise. Their actual
generating standard deviations are
respectively 0.08, 0.045, 0.025 and 0.045.
Consequently, **within this simulation only**,
we can calculate a conditional analytic
Gaussian slope sampling variance from the
full, known original participant and trial
covariance, with no fitted covariance
parameter estimation. The oracle is not
available to an empirical analyst without
additional verified modelling assumptions.

The mean ratio of estimated slope standard
error to known conditional oracle standard
error was:

| Independent people | Broad: CR1 | Broad: jackknife | Narrow: CR1 | Narrow: jackknife |
|---:|---:|---:|---:|---:|
| 24 | 0.946 | 1.029 | 0.955 | 1.037 |
| 48 | 0.973 | 1.013 | 0.981 | 1.020 |
| 96 | 0.984 | 1.003 | 0.986 | 1.005 |

In this source, the **participant jackknife
tended to give slightly larger standard
errors**, while CR1 was somewhat smaller
than the known variance oracle on average.
Both approached the oracle's scale with
larger independent participant counts.
These are mean *ratios* across generating
blocks, not calibration proof or a
formal estimator ranking.

The empirical standard deviation of
source-block slope errors was also close
to the mean known oracle SE:

| Participants | Broad: empirical SD / oracle SE | Narrow: empirical SD / oracle SE |
|---:|---:|---:|
| 24 | 0.03864 / 0.03917 | 0.09992 / 0.10020 |
| 48 | 0.02510 / 0.02730 | 0.06391 / 0.06976 |
| 96 | 0.01895 / 0.01919 | 0.04737 / 0.04902 |

Reducing predictor spread produced larger
absolute uncertainty in the slope, despite
no observation gaps. The estimates remained
identifiable with the prespecified 12
intercept-and-slope basis coefficients.

Original source **known-mean projection
error at the midpoint was less than
1e-8 in absolute average magnitude**
across all six settings. That strongly
supports the intended test boundary:
the observed standard-error behavior
was not driven by the R11 deliberately
misrepresented localized mean or by
unrecorded gaze.

## How this changes the R11 interpretation

The earlier **R11** source reported **80/96
(83.3%)** for complete, smooth, degree-five
mean and **77/96 (80.2%)** for the fixed
spline. **R12** independently tested
a different fresh generating source, a
fixed degree-five mean and explicit known
Gaussian covariance. At 48 participants
its CR1/t interval included known truth
in **88/96 (91.7%)** under both broad
and narrow covariate support.

The new result means it would be an
overstatement to claim that the complete
asynchronous repeated-trial design
**systematically** produces severe
CR1 undercoverage. The independent
generating seed families, participant
distributions and variance-model
details differ, and Monte Carlo
uncertainty remains substantial.

The source supports a **more precise
scientific next step**: reproduce R11's
exact generating mechanism with a
known-source conditional covariance
oracle, or otherwise perform an exact
matched-design finite-sample audit,
before attributing the two experiments'
coverage differences to sample size,
critical values or covariance estimation.

## Boundaries and research decision

R12 evaluates one **pointwise** slope
contrast with smooth, complete,
Gaussian-simulation source data only.
It does not validate simultaneous
90% whole-trajectory bands,
multiple-comparison error rates,
latent-MNAR correction,
asynchronous sensor validity, a
fitted functional mixed-effects
likelihood or a new production API.
The conditional Gaussian variance
oracle uses hidden generating
variance parameters and cannot be
presented as an empirical estimator.

No CR1, delete-person jackknife or
known-oracle architecture was
selected for general use. New
source replications, non-Gaussian
responses, heteroscedastic participant
clusters, mean misspecification
and observation loss require
independent validation.

[Prespecified R12 protocol](w3-r12-complete-cluster-variance-oracle-protocol.md)
· [Open W3 inferential blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
· [Open missing/native support blocker #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296).

Stable published **1.1.0**, unreleased
development **`1.2.0rc2.dev0`** and
`production_release_ready=false`
remain unchanged. Draft research only:
no root estimator, tag, release
candidate or PyPI publication.
