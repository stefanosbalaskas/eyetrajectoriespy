# F5: independent-baseline length × nuisance-estimation ablation

This is a **research-only falsification and diagnosis experiment** stacked on
the independently trained F5 method in draft PR #263. It changes no
root-stable API, default inference method, threshold, or publication gate.

## Scientific question

The prior 2,520-fit source experiment
([workflow #37987935105](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37987935105),
artifact `11643259568`) reduced strong AR1 false-positive
rejections but was conspicuously conservative under iid and weak-AR1
true nulls (0.8% and 1.7% at nominal 5%, n=120 per regime).
Its AR2 misspecification stress rejected 8.3%.
This follow-on tries to **separate baseline sampling uncertainty from
baseline duration**. It does not assume that either mechanism is the
explanation before testing.

The existing method draws a coefficient for every null trajectory
from a bias-adjusted bootstrap approximation to the coefficient
estimation distribution. A new opt-in ablation
`null_coefficient_policy="baseline_plugin"` retains the same
independently estimated baseline innovations and nuisance fitting
routine but simulates every null using the unadjusted
baseline-only OLS coefficient. Default
`"baseline_uncertainty"` behavior and its original RNG stream
are unchanged. The plug-in is explicitly **not** a validated method:
fixing a noisy estimate can be anti-conservative and the confidence
distribution used in the default route is itself only approximate.

## Prespecified matched design

There are four data-generating processes: Gaussian iid, AR1
$\phi=.35$, AR1 $\phi=.80$, and misspecified Gaussian AR2
$(\phi_1=.64,\phi_2=.24)$.
Each process has 100 independently generated no-change test sequences
and 50 sequences with the same prespecified sinusoidal break of
amplitude 0.12. Each test sequence has 36 ordered whole functions;
all participants are independent within the generator.

Each test sequence is reused *without alteration* across three
independent stationary baseline lengths of 40, 80 and 160 whole
functions. For each baseline, two coefficient-uncertainty policies
run on the **exact same training and test observations** with
paired random sequences. Baseline and test seeds are independent,
and all tests use a seed namespace disjoint from earlier studies.

The complete first wave is **600 independent test sequences** ×
3 baseline lengths × 2 coefficients policies = **3,600 actual
F5 full tests**, including 2,400 null-method attempts and 1,200
fixed-break attempts. Every method fits its own baseline-only
nuisance model, with 99 baseline parametric bootstrap refits
and 119 whole-function null simulations.

The design preregisters alpha=.01/.05/.10, conditional rejection,
failure-inclusive rejection, exact 95% Monte Carlo intervals,
independent baseline estimated coefficients and uncertainty widths.
It cannot estimate universal power, prove calibration for arbitrary
ARMA processes, or establish transferability to real eye-tracking
designs. The 100 null replications per crossed cell yield substantial
Monte Carlo uncertainty; apparent differences within a few percentage
points should not be overinterpreted. Notably, **each cell is paired
in source data** but the independent data-generating units are the
unique test sequences, not the 3,600 model attempts.

## Governance and experimental decision

An individual baseline length or coefficient policy will **not**
be selected by observing which happens to have the closest null size.
These are causal-mechanism diagnostics for a follow-up independent
qualification study; p-values remain exploratory. No post hoc
threshold tuning, automatic method default change, inference
qualification, or release publication may follow from the first wave.

Full data seeds, SHA256-verified original per-process artifacts,
failed fits, all 3,600 expected attempts and a combined source audit
are retained by the science workflow. Its heavy scientific job
executes only upon initial draft PR opening or deliberate manual
dispatch, not every documentation push.

Scientific issue [#256](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/256)
remains open. Stable 1.1.0 and protected `main` remain unchanged.
