# W3 R7: genuinely asynchronous repeated-trial source validation

!!! danger "Participant-balanced fitting is not hierarchical inferential calibration"
    This source-verified experiment supports a practical distinction:
    **the participant is the independent generating unit**, even when
    that participant contributes multiple unevenly observed trials.
    Giving each participant equal total regression weight reduced
    mean slope RMSE in the tested unequal-trial generator. It is
    **not** a validated functional mixed-effects method, cluster
    standard-error procedure, MAR/MNAR correction, or public API.

## Original study and source-integrity audit

The original [GitHub Actions scientific workflow #38222095846](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38222095846)
completed **256/256 prespecified scientific cases** with **zero
source, fitting and independent numerical-reference failures**.
The retained artifact **`11734479698`**,
`w3-r7-original-hierarchical-async-evidence`, holds the complete
`case-ledger.json`, `evidence.json`, original Matplotlib plot
`source-r7-hierarchical-async.svg`, source checkout identity and
`SHA256SUMS`. The original ZIP was independently downloaded and
**all 4/4 source SHA256 entries matched**. Its recorded
`GITHUB_SHA` is
`3bf87d53f81e5fc6da6f3ace019051d833a4312f` (a possible
transient pull-request checkout commit).

The original source study has **64 independently seeded generating
blocks**. Each contains **48 independent participants**, with
smooth shared participant random intercept/slope terms across
repeated trials, genuinely jittered curve-specific recording times
and noise at the trial level. Four scenarios are *paired* on each
generating source: either three trials for every participant or a
declared one-to-three-trial allocation, crossed with MCAR and
latent-response-dependent eight-sample recording gaps. Therefore
256 numerical fits **are not 256 independent generating blocks**.

Every original study case preserved its native recorded timestamps
and samples. The existing supported W3 common-grid workflow rejected
native irregular input, and all three research least-squares
fitting objectives agreed with independent QR solutions.
Source contracts passed on Python 3.11, 3.12 and 3.13.

## Complete known-truth functional slope recovery

All numbers below are the mean of each of the 64 independently generated
datasets' **full-grid functional slope RMSE** relative to known truth,
evaluated after fitting a prespecified degree-five time basis to
genuinely observed native samples.

| Trial allocation and observation loss | Full-source participant-balanced reference | Observed sample-weighted | Observed trial-balanced | Observed participant-balanced |
|---|---:|---:|---:|---:|
| Three trials each · MCAR | 0.02511 | 0.02576 | **0.02554** | **0.02554** |
| Three trials each · Latent-response-dependent | 0.02511 | 0.02598 | **0.02573** | **0.02573** |
| Unequal 1–3 trials · MCAR | 0.02537 | 0.02746 | 0.02712 | **0.02634** |
| Unequal 1–3 trials · Latent-response-dependent | 0.02537 | 0.02733 | 0.02707 | **0.02610** |

![Original-source summary of W3 R7 asynchronous repeated-trial functional slope RMSE under unequal observation support](../assets/research/w3-r7-hierarchical-async-rmse-20261012.svg)

*Original source-derived figure, not measured human eye-tracking
accuracy. The independent generating block, not participant trial
or gaze timestamp, is the Monte Carlo replication unit.*

### Why balanced weighting changes the numerical result

For each participant with k recorded trials and n_j genuinely
recorded time points in trial j, the three explicitly compared
least-squares objectives assign point weights:

| Objective | Weight of an observed point | Total weight per participant |
|---|---|---|
| Sample-weighted | `1` | Total recorded gaze points |
| Trial-balanced | `1/n_j` | Number of supported trials |
| Participant-balanced | `1/(k n_j)` | 1 |

No participants are deleted by these fitting objectives.
The underlying independent source unit remains the
**participant**, not each gaze point or repeated trial.

When every participant has exactly three trials,
trial-balanced and participant-balanced weights differ
only by the common scalar 1/3. Hence they yielded
**identical numerical fitted coefficients** across all
128 balanced-trial source cases, satisfying the source
numerical invariant. With unequal trial support, the
two objectives differ and the participant-balanced fit
showed modestly lower *average* RMSE in both selected
generating conditions. That does not establish an
optimal empirical weighting rule.

Mean original trial count per dataset was **144** under
balanced trial support and **95.97** under unequal
trial support. Mean recording-gap trial counts were
respectively **42.31** and **28.88** under MCAR;
**54.53** and **37.52** under latent-response-dependent
loss. Recorded trial and participant counts are available
per source block in the original ledger.

## Signed midpoint shifts and their Monte Carlo uncertainty

The scientific reference is the *same block's complete,
pre-gap, participant-balanced native-basis fit*, rather than
an empirical gaze observation at a hidden timestamp.

| Trial design and observation mechanism | Mean participant-balanced slope shift | 95% independent-block bootstrap Monte Carlo interval |
|---|---:|---:|
| Three trials · MCAR | −0.00009 | −0.00169 to +0.00156 |
| Three trials · Latent-response-dependent | **−0.00703** | **−0.00952 to −0.00469** |
| Unequal 1–3 trials · MCAR | −0.00046 | −0.00304 to +0.00214 |
| Unequal 1–3 trials · Latent-response-dependent | **−0.00578** | **−0.00843 to −0.00303** |

The same paired generating block drives the comparisons
within each trial design and recording-loss condition.
A nonzero mean shift under this latent-MNAR mechanism
is **a source-dependent simulation result**; it neither
identifies the missingness process in real gaze nor proves
similar shifts across different devices, tasks or
psychological populations.

The participant-balanced regression changes how
individuals contribute to a functional *point estimate*.
It does **not** make the trial-level residuals independent,
estimate participant random effects or their covariance,
provide cluster-robust standard errors, demonstrate Type-I
error control, or validate simultaneous confidence bands.

## Boundaries for subsequent qualification

These results establish computational and data-integrity
contracts for a fixed degree-five basis under 48 simulated
participants and at most three truly asynchronous trials.
They do not cover data-driven basis selection, sharp
saccadic changes, nonignorable trial assignment, clusters
of widely varying participant sizes, crossover predictors,
nonlinear participant-condition responses, missingness
estimation, irregular longitudinal covariance, or
empirical sensor uncertainty.

A later independent validation must compare
**participant-level robust/sandwich or hierarchical
uncertainty**, not merely numerical regression weighting;
it must also examine misspecified mean functions and
larger source-block counts. The current study is not
a model-selection certificate or a publication gate.

[Prespecified R7 protocol](w3-r7-repeated-trial-asynchronous-protocol.md)
· [Observation-process scientific blocker #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
· [Independent W3 confidence-band blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289).

Published stable **1.1.0** remains unchanged, and unreleased
development identity is **`1.2.0rc2.dev0`** with
`production_release_ready=false`. No root API promotion,
release tag, release candidate or PyPI publication follows.
