# R28 — hypothetical predictor-range sensitivity of Gaussian random-slope information

**Research-only design sensitivity:** [draft PR #330](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/330), [original frozen-design scientific workflow #38728238771](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38728238771), source head `009caeccaf34205f8b40e16e07ce500335f217ff`. Both the exact mathematical invariance test and the original fixed-design calculations PASSED: **32/32 complete, zero failures**. Uses the exact native participant/trial/time mapping of only **TWO independent original R26 generating blocks**, with n24/n96 and ordinary predictor-independent/dependent covariance mechanisms. It creates **no new participants, trajectory observations, trial series or independent generating blocks**, and does not fit REML or NNLS or estimate CI coverage.

The hypothesis was frozen before running: a hypothetical participant predictor rescaling of **0.5×, 1×, 2× and 4×** on each unchanged native design; scale the predictor-related fixed-effect columns and, for predictor-dependent source covariance, the matching random-slope Gaussian covariance kernel consistently. Variance-component parameters themselves remain at their original true Gaussian reference values. For predictor-independent random-slope covariance, predictor scaling is solely an invertible fixed-mean parameterization; the full Gaussian restricted-information operator should be **invariant**, serving as the predeclared negative control.

## Full prespecified Gaussian expected-information results

Values are median across the **two original frozen source blocks** per cell. These are local asymptotic Gaussian **log random-slope variance standard errors**, computed using the exact expected restricted Fisher information at source-known covariance and no fitted covariance estimation.

| Participants | Original source mechanism | Spread 0.5× | Spread 1× | Spread 2× | Spread 4× | 4× / original local slope SE |
|---|---|---:|---:|---:|---:|---:|
| 24 | independent | 4.531 | 4.531 | 4.531 | 4.531 | 1.000 |
| 24 | dependent | 16.665 | 4.573 | 1.521 | 0.708 | 0.155 |
| 96 | independent | 2.196 | 2.196 | 2.196 | 2.196 | 1.000 |
| 96 | dependent | 7.199 | 1.986 | 0.670 | 0.320 | 0.161 |

## Negative-control and information interpretation

In both predictor-independent covariance conditions (n24 and n96), all four hypothetical predictor multipliers returned identical random-slope information to numerical precision. This is the expected invariance of covariance variance-component information under an invertible rescaling of the fixed-mean predictor columns, and rules out a coding artifact in which larger x values always mechanically improve reported information.

In the **predictor-dependent** source model, scaling x also changes the magnitude of the random-slope covariance term `theta_slope * x_i² * f(t)f(t')`. Thus it changes the Gaussian covariance signal relative to the other components. The Gaussian reference log-slope SE at n24 is approximately **4.57 at the observed original x range**, **1.52 with a 2× hypothetical spread** and **0.71 with 4×**. At n96 the corresponding values are **1.99**, **0.67**, and **0.32**. Conversely halving spread sharply weakens slope information. Trial-variance local SE remained nearly constant over these scenarios; information gains were concentrated in the predictor-dependent slope mechanism.

**Do not interpret these numbers as estimated REML error or measured coverage.** They are exact local expected Gaussian-information calculations at simulation-known true parameters, conditional on the frozen native designs. The experiment intentionally modifies predictor span without changing observed gaze or collecting new participant samples. It cannot establish prospective feasibility, robustness to non-Gaussian gaze errors, a causal design effect, or safe extrapolation to future participants.

A defensible study-design programme could now investigate realistic predictor heterogeneity, participant/sample size, trial structure, and longer observation windows jointly, but it would need independent source data and prespecified practical constraints. Under the predictor-independent covariance mechanism, changing span alone **cannot** remedy weak random-slope information in this local model.

`hypothetical_information_contract_passed=true`; `empirical_design_qualified=false`; `estimated_target_covariance_inference_qualified=false`; `pointwise_or_simultaneous_band_qualified=false`; `release_authorized=false`. Scientific blockers #289/#296 remain OPEN. Historical R20 41/256 failures and R22 32 numerical refusals are unchanged, all research PRs draft, protected main/API and 1.2 tag/PyPI unmodified.
