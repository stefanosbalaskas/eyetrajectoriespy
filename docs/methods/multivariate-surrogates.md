# Multivariate IAAFT surrogate testing

Version 0.37 adds a cross-spectrum-aware surrogate layer for planar or
multichannel gaze trajectories.

The key rule is that `x(t)` and `y(t)` are **not** surrogate-generated
independently. Their within-channel spectra and between-channel Fourier phase
relationships are treated jointly.

## Scientific target

For channel \(k\),

$$
F_k(\omega)=A_k(\omega)e^{i\phi_k(\omega)}.
$$

Relative to an explicitly declared reference channel \(r\), the algorithm
retains the observed phase difference

$$
\Delta\phi_{kr}(\omega)=\phi_k(\omega)-\phi_r(\omega).
$$

At each Fourier-adjustment step, a randomized reference phase is combined with
those original phase offsets. This targets each channel's original power
spectrum and the multivariate cross-spectrum.

After inverse transformation, each channel is rank-remapped to its exact
observed marginal value set. The rank and Fourier constraints are then iterated.

## Generate planar surrogates

~~~python
from eyetrajectoriespy import generate_multivariate_iaaft_surrogates

surrogates = generate_multivariate_iaaft_surrogates(
    gaze,
    curve="trial_01",
    dimensions=("x", "y"),
    reference_dimension="x",
    n_surrogates=199,
    max_iterations=1000,
    tolerance=1e-8,
    random_state=2026,
)
~~~

The reference dimension is required. The package does not choose it
automatically because the reference-anchored finite-sample iteration can depend
on that choice.

## What is preserved

The final surrogate preserves exactly:

- the empirical marginal value set of every selected channel.

The algorithm targets, but does not claim exact final preservation of:

- each channel's Fourier amplitude spectrum;
- every selected channel pair's complex cross-spectrum.

The final rank-remapping step perturbs Fourier coefficients. For that reason,
`MultivariateIAAFTResult` retains per-surrogate:

- convergence iterations;
- relative per-channel spectrum mismatch;
- relative per-pair complex cross-spectrum mismatch.

A surrogate that fails the declared convergence rule raises rather than being
accepted silently.

## Diagnostics

~~~python
from eyetrajectoriespy import (
    multivariate_iaaft_diagnostics_frame,
    plot_multivariate_iaaft_diagnostics,
)

diagnostics = multivariate_iaaft_diagnostics_frame(surrogates)
ax = plot_multivariate_iaaft_diagnostics(surrogates)
~~~

Inspect the retained errors rather than assuming that "MIAAFT" implies perfect
cross-spectrum preservation.

## Multichannel nonlinearity test

~~~python
from eyetrajectoriespy import multivariate_surrogate_nonlinearity_test

test = multivariate_surrogate_nonlinearity_test(
    gaze,
    curve="trial_01",
    dimensions=("x", "y"),
    reference_dimension="x",
    statistic="largest_lyapunov",
    embedding_dimension=2,
    delay=2,
    theiler_window=15,
    max_horizon=12,
    fit_start=1,
    fit_end=5,
    n_surrogates=199,
    alternative="greater",
    max_iterations=1000,
    tolerance=1e-8,
    random_state=2026,
)
~~~

The observed and surrogate trajectories use the **same** multichannel
embedding, Theiler exclusion, divergence horizon, and LLE fit interval.

The Monte Carlo p-value uses the plus-one correction. Version 0.37 currently
supports the multichannel Rosenstein largest-Lyapunov statistic in this helper.

## Interpretation

A rejection means that the declared statistic is unusual under the specific
multivariate surrogate null that approximately preserves auto/cross-spectral
linear structure and exactly preserves each channel's empirical marginal
distribution.

It does **not** establish:

- deterministic chaos;
- one unique nonlinear mechanism;
- causality between gaze dimensions;
- a validated low-dimensional dynamical system.

Surrogate testing should therefore be described as a falsification-style test
against a declared stochastic null, not as a direct classifier of "chaotic
gaze."

## Why not generate x and y independently?

Independent univariate IAAFT destroys between-channel linear structure. For
planar gaze, that can make the surrogate null artificially easy to reject
because the surrogate ensemble no longer reproduces observed x/y
cross-correlations.

Prichard and Theiler's multivariate phase-randomization principle was designed
to retain cross-correlative structure. The 0.37 implementation extends that
principle through iterative rank remapping so the observed marginal
distributions are restored channel by channel.

## Reference-dimension sensitivity

The current MIAAFT implementation is reference-anchored. A defensible analysis
should either:

1. pre-specify the reference dimension from the representation contract; or
2. repeat the analysis across plausible reference dimensions as a sensitivity
   analysis.

Do not choose the reference dimension after inspecting which one gives the
smallest p-value.

## No hidden analytical decisions

Version 0.37 does not automatically:

- scale dimensions;
- smooth or interpolate trajectories;
- choose dimensions;
- choose a reference dimension;
- choose embedding dimension or delay;
- choose a Theiler window;
- choose the LLE fit interval;
- discard failed surrogates;
- relax convergence tolerances.

## Evidence basis

Prichard and Theiler (1994) introduced multivariate phase-randomized surrogate
generation specifically to retain both autocorrelations and cross-correlations
among simultaneously observed series. Schreiber and Schmitz (1996) introduced
the iterative amplitude-adjusted strategy for preserving an observed
distribution together with linear correlation structure. Keylock (2012)
describes multivariate IAAFT construction through retained inter-series Fourier
phase differences and discusses its finite-sample behavior.

Version 0.37 does not claim novelty for MIAAFT. The package contribution is the
explicit reference-channel contract, exact marginal audit, retained
power/cross-spectrum errors, deterministic seeding, and fail-closed integration
with the existing nonlinear-analysis APIs.
