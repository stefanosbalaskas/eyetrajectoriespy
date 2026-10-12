# W3 R9 — richer prespecified time bases, new independent source study

!!! danger "Simulation findings, not approved statistical inference"
    A flexible fixed cubic-spline mean model substantially reduced
    deterministic projection bias from a known, localized slope feature.
    Nevertheless **90% pointwise participant-cluster truth inclusion
    was not uniformly nominal**, especially under simulated
    latent-response-dependent observation loss. No mean basis was
    automatically selected, and no simultaneous confidence band,
    missingness correction or supported irregular-data estimator
    is qualified by this study.

## Original source, audit and scientific independence

The original [scientific workflow #38292511576](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38292511576)
completed all **512/512** prespecified original source scenarios
with **zero fitting/evidence failures**: eight matched factorial
scenarios per **64 newly seeded independent generating blocks**,
each comprising 48 participants and up to three repeated
trials with genuinely asynchronous native timestamps.
All 512 original cases compared **three predeclared mean
models**, yielding 1,536 original model fits. There were
**64 independent source blocks, not 1,536 independent samples**.

Original artifact **`11767316830`**,
`w3-r9-original-prespecified-basis-evidence`, contains the
entire case ledger, model/cell statistics, original
`original-mean-basis-coverage.svg`, source identity
and `SHA256SUMS`. It was independently downloaded:
**4/4 original source hashes matched**. The action
recorded source checkout SHA
`9ac1d61ff1be1137d9d79abfc5192e646f26033d`
(potentially a transient PR checkout ref). The complete
simulation is original synthetic known-truth evidence,
not recorded human eye tracking.

Three independently specified models used exactly the
same observed native measurements, 48 genuine
participant clusters and participant-balanced numerical
weights:

| Model | Fixed mean-function basis | Parameters |
|---|---|---:|
| Degree-five Legendre | Polynomial order 5 (prior R8 comparator) | 12 |
| Degree-eleven Legendre | Polynomial order 11 | 24 |
| Cubic B-spline | 13 basis terms, 9 equally spaced interior knots (0.1–0.9) | 26 |

All numerical coefficient fits and independent
participant-score aggregation were checked against
separately derived oracles; the current supported dense
W3 estimator continued to **reject native irregular
timestamps**. The models predict functions at a
designated evaluation grid; they do **not** interpolate,
zero-fill or reconstruct lost sensor measurements.

## Prespecified 90% pointwise known-truth inclusion

These are **pointwise** participant-cluster CR1 intervals
for one focal condition-slope coordinate at time 0.5.
Each cell's denominator is **64 independent
generating blocks**, with exact success counts:

| Trial allocation / observation loss / generating truth | Legendre-5 | Legendre-11 | Cubic spline-13 |
|---|---:|---:|---:|
| 3 trials · MCAR · baseline | 56/64 (87.5%) | 57/64 (89.1%) | 57/64 (89.1%) |
| 3 trials · MCAR · localized bump | 4/64 (6.3%) | 44/64 (68.8%) | **60/64 (93.8%)** |
| 3 trials · latent loss · baseline | 59/64 (92.2%) | 53/64 (82.8%) | 50/64 (78.1%) |
| 3 trials · latent loss · localized bump | 0/64 (0%) | 23/64 (35.9%) | **48/64 (75.0%)** |
| 1–3 trials · MCAR · baseline | 59/64 (92.2%) | 56/64 (87.5%) | 58/64 (90.6%) |
| 1–3 trials · MCAR · localized bump | 6/64 (9.4%) | 46/64 (71.9%) | **59/64 (92.2%)** |
| 1–3 trials · latent loss · baseline | 58/64 (90.6%) | 53/64 (82.8%) | 53/64 (82.8%) |
| 1–3 trials · latent loss · localized bump | 0/64 (0%) | 27/64 (42.2%) | **50/64 (78.1%)** |

![W3 R9 original-source-audit-derived pointwise true slope inclusion for three prespecified mean bases](../assets/research/w3-r9-basis-pointwise-coverage-20261012.svg)

*Figure redrawn from the verified original source ledger.
The unmodified original-source Matplotlib SVG is retained
in the workflow artifact. Nominal target 90% **at one
point**, not 90% whole-function coverage.*

The prespecified source study did **not** make
high coverage a software success condition. The
64-block Wilson 95% Monte Carlo intervals are included
per original source cell in `evidence.json`, alongside
the completed and attempted counts. These
intervals limit precision of nominal-coverage statements.

## Separate mean projection bias and statistical uncertainty

At the hidden midpoint, fitting the **known true generating
conditional mean** at originally observed source times
to each fixed basis produced the following average
deterministic *projection biases* in the localized
slope generating condition:

| Observation scenario | Degree-five | Degree-eleven | Cubic spline |
|---|---:|---:|---:|
| Balanced · MCAR | −0.09116 | −0.03399 | **−0.00375** |
| Balanced · latent loss | −0.09482 | −0.03518 | **−0.00389** |
| Unequal · MCAR | −0.09139 | −0.03408 | **−0.00376** |
| Unequal · latent loss | −0.09496 | −0.03524 | **−0.00390** |

Thus the spline considerably reduced **this
specified basis approximation error**. Compared
with degree five, its paired complete-function
slope RMSE was lower by approximately
**0.0144–0.0156** in the localized-bump scenarios;
the precomputed independent-block Monte Carlo 95%
intervals for those reductions all excluded zero.

The within-source pointwise coverage increase for
spline versus degree five in localized-bump truth
was **+87.5 percentage points** under balanced MCAR
(95% independent-block bootstrap interval
**+76.6 to +96.9 points**) and **+75.0 points**
under balanced latent loss (**+64.1 to +85.9 points**).
These are Monte Carlo contrasts for the specified
generating truth, **not** universal proof that a
particular knot schedule is optimal.

For the well-represented **baseline** truth, the
richer models did not consistently improve
pointwise coverage or full-slope recovery. Under
balanced latent recording loss, baseline coverage
fell from **92.2% with degree five** to **78.1%
with the spline**, despite the spline having
essentially zero deterministic baseline projection
bias. This is direct evidence that reducing mean
approximation bias alone does not ensure calibrated
cluster-level uncertainty in the presence of
unobserved-response-dependent recording gaps.

Richer fits can also produce larger intervals:
balanced MCAR mean interval widths under baseline
truth were **0.0916** (degree five), **0.0976**
(degree eleven) and **0.0972** (cubic spline).
These precision costs are part of the scientific
record, not an engineering test failure.

## What remains scientifically unresolved

1. **No universal basis choice:** models and knots
   were prespecified, not independently selected or
   externally validated. This study's localized
   bump is known in simulation; real gaze
   functions need not share that shape.
2. **No missingness correction:** even the more
   flexible spline yielded only **75.0–78.1%**
   observed pointwise coverage under the
   localized-bump, latent-response-dependent
   dropout cases. The hidden source residual is
   not available to an empirical observer.
3. **No simultaneous bands:** one focal
   pointwise CR1 interval cannot justify
   whole-function or multiple-outcome inference.
   Family-wise calibration and Type-I rates remain open.
4. **No validated hierarchical covariance:** the
   analysis applies a participant-level sandwich
   variance to a weighted fixed-basis point
   estimator; it is not a fitted functional
   random-effects likelihood, longitudinal
   mixed model or cluster bootstrap.
5. **No public API promotion:** neither model
   nor degree/knots were selected as a
   production winner. Follow-up requires
   independently seeded cluster bootstrap
   or other reference-based uncertainty
   studies with correctly specified and
   misspecified mean functions.

[Predeclared R9 protocol](w3-r9-prespecified-mean-basis-protocol.md)
· [W3 inference blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
· [Missing and irregular observation blocker #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296).

Protected `main` remains separate; stable
published **1.1.0**, development
**`1.2.0rc2.dev0`** and
`production_release_ready=false` are unchanged.
No tag, release candidate, API promotion or
PyPI upload is authorized.
