# B6/B7 rank-two R4: controlled observation-schedule experiment

!!! danger "Controlled computational research, not Bayesian qualification"
    The purpose is to test sampling sensitivity to paired versus asynchronous
    measurement while preserving negative evidence. Four model fits on one
    nested/common-random-number generating configuration cannot establish
    posterior calibration, a population-level schedule effect or release suitability.

## Prespecified identification

The R3 pilot compared *different prior-generated datasets*, so its paired
versus asynchronous convergence contrast was confounded with the realized
population coefficients, participant factors and observation schedule.

R4 generates one common matched-prior set of population mean/loading
coefficients and **twelve** fixed latent participant scores. The n=4 level
uses the first four participants from the same draw; n=12 uses all twelve.
The same x-channel observation times, values, and noise draws are retained
*exactly* under both schedules. Each participant's y observation **count**
and Gaussian noise innovations are retained, while the paired schedule measures
y at the original x times and the asynchronous schedule measures y at
independently drawn times. This changes observed y values as a consequence of
the timing intervention while preserving the latent trajectory. Thus it
isolates the schedule as the manipulated design element within each n,
though a single Monte Carlo realization is not generalizable.

The 2 × 2 design is **schedule** (paired/asynchronous) × **participant count**
(4/12). Both factors are declared before computation; participant n=4 is
nested inside n=12, **not a second independent sample**. The sampling budget
is exactly 4 chains, 700 tuning and 400 retained draws/chain with target
accept 0.94 in all cells. Same PyMC model and initial random seed within each
n; no post-hoc sampler adjustment. Evaluation uses 15 rotation-invariant
population mean, variance and x/y cross-covariance functionals at quarter,
midpoint and three-quarter positions.

## Evidence and falsifiable expectations

Compare, separately by n, the paired minus asynchronous worst R-hat,
minimum bulk/tail ESS, BFMI, divergences, functional-specific failures
and elapsed full fit time. The previous R3 population-mean failure suggests
where to inspect, but **no improvement is presumed**. Maintain distinctions
between x/y means, x/y variances and xy covariance; zero divergences alone
is not proof of mixing.

Retain four original case/evidence JSON pairs, SHA256SUMS and aggregate audit.
All attempt, fit-error and nonconvergence denominators remain visible.
No refit is selected/excluded after seeing diagnostics. Repeated independent
generating draws and larger participant-size levels would be necessary for
a statistically precise design-effect conclusion.

Scientific blocker #255 stays open. Research code, production API, root
dependencies, stable 1.1.0 and 1.2 publication settings remain untouched.
