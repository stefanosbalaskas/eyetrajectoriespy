# W3 R11 — paired complete-source versus observation-process findings

!!! danger "Complete source is a simulation oracle, not recovered human gaze"
    This research isolates changes associated with retaining or losing
    records from the **same** underlying generated trajectories. It
    confirms a distinct finite-participant uncertainty problem even
    in the complete-data setting, severe localized mean-model
    misspecification and additional observation-process effects
    under the simulated latent outcome-dependent loss. It does
    **not** qualify an empirical MNAR correction, a 90% whole-function
    band, or a new public estimator.

## Original independent source and verification

The original [GitHub scientific workflow #38310729733](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38310729733)
completed **768/768 prespecified source cases** with **zero
scientific fitting, independent numerical-oracle, native
source-integrity or missing-case failures**. Artifact
**`11775040218`** (`w3-r11-original-paired-observation-process`)
contains the full `case-ledger.json`, `evidence.json`,
original Matplotlib scientific figure
`source-paired-observation-process.svg`, original
`source-commit.txt`, and `SHA256SUMS`. The original ZIP
was downloaded independently; **all 4/4 source SHA256
checksums passed**. The original workflow-recorded checkout
identity was `d53fd49836da1d50909fea6bb3a4da694a073ae1`,
which may be a transient PR checkout SHA.

The source seed family is `202610131107`, with **96 NEW
independently generated blocks of 48 independent participants**,
each providing one to three genuinely jittered asynchronous
trials. Within every generating block, four observation
regimes use identical generating participant traits, responses,
random effects, trial timing, measurement innovations and
recording-loss uniforms. Only the **recording mask** differs;
retained native timestamps/coordinates remain exactly equal
to their original *complete* simulated source. Two paired
generating truths compare a relatively smooth functional
condition effect with the same original source plus a
known localized condition-slope bump.

There are **96 independent source blocks**, not 768 independent
datasets. Complete source is available because this is a
known generating simulation: it is **not** an inference
procedure available for empirical missing measurements.
Original source integrity and independent QR/participant
score-reference checks passed in **96/96 source cases for
each of the eight paired factorial cells**. Both original
fixed mean bases use a participant-balanced least-squares
objective: degree-five Legendre and the same 13-function
fixed-knot cubic spline as R9–R10. Existing supported
complete-grid W3 explicitly rejected every native irregular
source case.

## Nominal 90% pointwise true-slope inclusion

All fractions are successes from **96 independent generating
blocks** at the single source midpoint time 0.5 in the first
slope response dimension. These are **pointwise** intervals
with participant-cluster CR1, not 90% simultaneous whole-slope
or multi-outcome confidence bands.

| True function | Observation mechanism | Degree-five Legendre | Fixed cubic spline |
|---|---|---:|---:|
| Smooth | **Complete source** | 80/96 (83.3%) | 77/96 (80.2%) |
| Smooth | MCAR | 78/96 (81.3%) | 82/96 (85.4%) |
| Smooth | Observed-x MAR | 79/96 (82.3%) | 81/96 (84.4%) |
| Smooth | Latent-response MNAR | 76/96 (79.2%) | **61/96 (63.5%)** |
| Localized bump | **Complete source** | **5/96 (5.2%)** | 79/96 (82.3%) |
| Localized bump | MCAR | 5/96 (5.2%) | 81/96 (84.4%) |
| Localized bump | Observed-x MAR | 5/96 (5.2%) | 81/96 (84.4%) |
| Localized bump | Latent-response MNAR | **2/96 (2.1%)** | **61/96 (63.5%)** |

![W3 R11 original-source verified paired observation-process pointwise coverage comparison](../assets/research/w3-r11-observation-process-coverage-20261013.svg)

*The original scientific Matplotlib figure and all 768 source-case
outcomes are retained in artifact 11775040218. The figure above
is source-ledger-derived and limited to **one pointwise
condition-slope contrast**. Nominal target = 90%.*

The 90% nominal target was not consistently achieved **even with
zero missing observations**. For the smooth true function
under the complete source, observed pointwise inclusion was
83.3% (degree five, 95% Wilson Monte Carlo interval
**74.6–89.5%**) and 80.2% (cubic spline,
**71.1–86.9%**). The independent source size of 96
allows only modest precision, but these results do
**not** establish nominal general calibration.

## Paired observation-loss displacement against the identical complete source

The matched contrast is the difference between a source-block
fitted midpoint slope under a missing-record mechanism and
the **same block's fitted complete-source slope**, not
an empirical reconstruction of unobserved real gaze.

| Generating function / loss | Degree-five mean paired slope shift | Fixed cubic spline paired slope shift |
|---|---:|---:|
| Smooth · MCAR | +0.00124 | +0.00228 |
| Smooth · Observed-x MAR | −0.00011 | −0.00027 |
| Smooth · Latent-response MNAR | **−0.00675** | **−0.02128** |
| Local bump · MCAR | **−0.00752** | +0.00192 |
| Local bump · Observed-x MAR | **−0.01031** | −0.00069 |
| Local bump · Latent-response MNAR | **−0.01921** | **−0.02179** |

The original complete-source reference is exactly zero for
each paired displacement, by construction and verified
source numerics. The prespecified **3,000 independent-block
resampling Monte Carlo intervals** illustrate the more
important differences:

- Smooth truth, latent-response MNAR, spline:
  **−0.02128**, 95% block-bootstrap interval
  **[−0.02577, −0.01675]**.
- Local-bump truth, latent-response MNAR, spline:
  **−0.02179**, 95% interval **[−0.02627, −0.01686]**.
- Smooth truth, observed-x MAR, spline:
  **−0.00027**, interval **[−0.00424, +0.00367]**.
- Local-bump truth, observed-x MAR, degree five:
  **−0.01031**, interval **[−0.01244, −0.00828]**.

The last row is an important model-assumption result:
even if recording selection is based on an *observed* predictor,
changing the distribution of supported records can
change the **pseudo-true projection of a misspecified
mean model**. The same observed-x MAR mechanism shifted
the degree-five local-bump *known conditional-mean
projection* by approximately **−0.01021**, while
the fixed spline's shift was approximately
**−0.00042**. Therefore a nonzero paired
observed-source shift should not automatically
be attributed to unidentified latent MNAR bias.

Average trial counts with recording gaps were
**0** (complete), **29.07** (MCAR), **30.07**
(observed-x MAR), and **36.79**
(latent-response MNAR) per original block,
over the same originally recruited participant
and trial allocation. The source does not
silently discard entire participants.

## Separating mean approximation from remaining inference problems

The localized condition-effect bump was not represented
well by the fixed degree-five mean basis. The
true-source conditional-mean midpoint projection
was **−0.08295** with complete data, versus
**−0.00340** with the spline. Even with *complete
simulated recordings*, nominal 90% pointwise
true-slope inclusion was **5/96 (5.2%)**
for degree five but **79/96 (82.3%)**
for the spline. Covariance or bootstrap
reweighting alone cannot correct this
model-projection error.

By contrast, under the smooth complete-source
generator, the known conditional-mean projection
error was effectively zero for **both** fixed
models (less than (10^{-6}) in absolute average
magnitude). Yet observed pointwise
true-slope inclusion was **only 80–83%**
in the present source. This identifies a
distinct remaining finite-participant covariance/
critical-value/model-sampling calibration
question even before observation loss.

Under smooth **latent MNAR** recording loss,
the spline's known-mean projection error
remained close to zero (about
**+0.00000003**), but its actual
midpoint slope error averaged **−0.02350**,
versus **−0.00221** under complete data.
That discrepancy is consistent with the
generating observation mechanism changing which
noisy responses are recorded; a correctly
approximated conditional mean alone does
not remove selection effects.

## Scientific gate and release boundaries

This source-controlled experiment supports a
more precise, **three-part validation programme**:
test mean-function adequacy, characterize the
recording-observation mechanism (including
nonidentifiability of latent loss), and evaluate
sampling uncertainty **under genuinely
independent participants**. It does not
identify a universal covariance estimator,
justify a model-selected spline, or
certify 90% simultaneous confidence bands.
A complete-source simulation comparator is
not a feasible missing-data correction
on real device recordings.

These results do **not** authorize a
functional mixed model, Bayesian posterior
coverage, Type-I error control over time,
MNAR identification, automatic interpolation,
resampling method selection or root/public
API promotion.

[Prespecified R11 protocol](w3-r11-paired-observation-process-protocol.md)
· [Open W3 simultaneous-band blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
· [Open native missing/irregular blocker #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296).

Protected main and stable published **1.1.0**
remain separate. Development
`1.2.0rc2.dev0` is not released and
`production_release_ready=false`.
No candidate tag, public estimator, release
or PyPI upload was performed.
