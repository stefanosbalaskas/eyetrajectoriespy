# Independent B6/B7 PyMC-NUTS reference posterior — research only

The original native B6/B7 Gibbs posterior has severe nominal 90%
population-coverage underperformance and insufficient R-hat/ESS even after
substantially longer chains. An exact partially collapsed mean update
([source #37978244822](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37978244822))
improved identifiable population mixing in multiple cases, but did not
qualify all rank-2 and paired/asynchronous posterior functionals.

This experiment is the next scientific test: **independently derived
marginal likelihood evaluated in a separate PyMC/NUTS backend**,
with no calls to the native Gibbs Gaussian conditional-update routines.

## Mathematical model and score integration

Under the same fixed known noise, Gaussian population priors and
cubic-B-spline dictionaries as the B6/B7 research experiments:

$$
y_{di} = B_{di}(\mu_d+L_d z_i) + e_{di},\qquad
z_i\sim N(0,I_k),\quad e_{di}\sim N(0,\sigma_d^2I).
$$

PyMC samples **only** mean vectors $\mu_d$ and loading matrices $L_d$
using NUTS. The participant scores $z_i$ are integrated from
the *model likelihood*. For every participant, the determinant lemma
and Woodbury yield, with $G_{di}=B_{di}^\top B_{di}$,

$$
Q_i=I_k+\sum_d\sigma_d^{-2}L_d^\top G_{di}L_d,
\quad
v_i=\sum_d\sigma_d^{-2}L_d^\top B_{di}^\top (y_{di}-B_{di}\mu_d).
$$

The negative twice marginal log likelihood, up to a constant, is

$$
\sum_i\left[
  \sum_d\sigma_d^{-2}\|y_{di}-B_{di}\mu_d\|^2
  -v_i^\top Q_i^{-1}v_i
  +\log|Q_i|+\sum_d n_{di}\log(\sigma_d^2)
\right].
$$

The x/y model uses the same participant's shared score $z_i$ across
native, potentially asynchronous observation clocks. Critically,
$Q_i$ pools **both** channels and preserves their cross-dependence.
No timestamp interpolation or reconstructed fit-as-data is performed.

The separate backend uses the actual PyMC automatic-differentiation
log posterior and NUTS rather than adapting the native conditional
precision sampler. B6/B7 use identical native irregular trajectory
objects, noise SD, spline dictionary, priors and participant units
across the NUTS and Gibbs fits.

## Prespecified experimental comparison

The run is a **diagnostic software reference**, not full Bayesian
qualification: three independent prior-generated datasets
(B6 rank 1, B7 rank 1 paired, B7 rank 1 asynchronous),
2 NUTS chains with 500 tuning and 300 retained draws/chain,
versus 2 exact-partially-collapsed native Gibbs chains with
650 warmup and 350 draws/chain.

For each identifiable midpoint population mean and (co)variance,
archive native and PyMC posterior mean/SD, equal-tailed 90%
interval, truth inclusion and posterior disagreement in units of the
independent reference posterior SD. Also retain native integrated
R-hat/ESS, PyMC R-hat/ESS/divergences and all failed runs.
These are **three independent datasets**, not a coverage study;
even near-identical summaries would not establish a valid posterior
over all configurations. Rank 2, joint covariance, hierarchical trials,
random slopes and observation noise estimation are not covered.

## Next scientific gate

If an independently converged NUTS reference disagrees materially with
native Gibbs, evaluate the native mixing and potential conditional
posterior construction. If both agree while undercoverage persists,
extend independent prior predictive/SBC and verify prior-to-likelihood
generation, particularly finite-chain quantile uncertainty.
NUTS itself must pass adequate convergence diagnostics; a new backend
is **not automatically correct or calibrated**.

The follow-on scientific gate requires numerous independently simulated
prior truths, rank-based SBC for identifiable mean/covariance
functionals, long-chain ESS/R-hat/MCSE, held-out participant predictive
checks, rank-2 planar comparisons and repeated nominal coverage
with prespecified Monte Carlo intervals.

All new reference methods, research data and figures remain in stacked
draft branches. Stable 1.1.0, protected `main`, source 1.2 release
readiness, posterior scientific qualification and public deployment
remain unchanged.
