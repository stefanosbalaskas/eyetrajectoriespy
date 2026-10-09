# B6/B7 independent posterior: population-functional convergence and MCSE

The first successful independent reference posterior comparison in
[original workflow #37988738287](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37988738287)
used three exact-prior matched B6/B7 rank-one datasets and produced 3/3
actual PyMC NUTS fits (source artifact `11645572128`, zero
divergences) after replacing the overlarge PyTensor expression with
a participant-vectorized rank-one marginal likelihood.

**That first comparison is not a successful convergence qualification.**
PyMC worst *raw-parameter* Rhat was 1.836 (B6 rank one), 1.020
(B7 rank-one paired), and 1.033 (B7 rank-one asynchronous);
native Gibbs worst monitored Rhat was respectively
1.381, 1.109 and 1.691. Some native bulk ESS minima were 3.2–14.3.
The reference B6 loading may exhibit an unresolved
\(\lambda\mapsto-\lambda,\ z_i\mapsto-z_i\) symmetry: raw
loading Rhat is not the right **scientific** convergence criterion
for the identified population covariance \(L L^\top\). This
hypothesis must be tested rather than assumed to explain bad Rhat.

## Source-verified original posterior comparisons

| Design | Identifiable midpoint outcome | Native mean | PyMC mean | Difference (PyMC posterior SD units) |
|---|---|---:|---:|---:|
| B6 rank1 | Population mean | -0.03574 | -0.04064 | +0.136 |
| B6 rank1 | Variance | 0.03002 | 0.02898 | +0.124 |
| B7 rank1 paired | x population mean | -0.24826 | -0.24935 | +0.127 |
| B7 rank1 paired | x/y cross-covariance | 0.001908 | 0.001952 | -0.056 |
| B7 rank1 asynchronous | x population mean | -0.08352 | -0.08251 | -0.036 |
| B7 rank1 asynchronous | x/y cross-covariance | 0.02818 | 0.02187 | +0.963 |

All equal-tailed 90% posterior intervals overlap. Nevertheless,
both implementations' cross-covariance intervals missed the
known-generating cross-covariance in the **one paired B7 dataset**.
The asynchronous B7 cross-covariance discrepancy is nontrivial relative
to its independent-reference posterior SD, but the native MCMC has
exceptionally poor ESS. These facts are not evidence of adequate
calibration or same-posterior equality.

## Additional independent convergence diagnostics

This focused research follow-up calculates **rank-normalized split
Rhat, bulk ESS, tail ESS and Monte Carlo standard error of the
posterior mean** on each *identified* midpoint functional in each
actual sampler: B6 population mean and variance; B7 x population
mean and x/y cross-covariance. It also reports the difference
between native and independent posterior means in units of their
combined MCSE, with a conspicuous warning that MCSE and marginal
overlap cannot qualify a nonconverged chain.

For transparency, raw-parameter worst NUTS Rhat is still retained
even though it can reflect factor-sign nonidentifiability rather
than marginal covariance mixing. The test suite deliberately creates
two chains with opposite rank-one loading signs but matching
loading-squared distributions, asserting that the scientific
Rhat is computed on the *identified covariance*, not raw factors.

A prespecified diagnostic flag requires **both** population-functional
Rhat \(\leq 1.01\) and bulk ESS \(\geq 400\) per pair before
even considering the summaries numerically trustworthy; this is a
diagnostic screen, **not** a scientific inference or posterior coverage
qualification. No failed fit is excluded from the attempt ledger.

## Future statistical qualification still required

Before opening the native B6/B7 gate: distinguish
nonidentifiability from nonconvergence; assess MCSE of posterior
interval endpoints, not only means; run independent multi-dataset
prior predictive simulation-based calibration for identified
functionals; evaluate rank-two loading geometry, heterogeneous
irregular clocks and measurement noise; and demonstrate
held-out participant predictive coverage. Any appropriate
computational threshold must be specified before looking at
the numerical results, never retrospectively adjusted to obtain
green CI.

All work remains in stacked draft PRs, with production
`main`, stable 1.1.0, public root exports and release flags unchanged.
