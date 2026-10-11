# B6/B7 rank-two NUTS R3: paired versus asynchronous posterior computation

!!! danger "Two actual rank-two fits; only one passed its exploratory screen"
    Both four-chain PyMC/NUTS models fitted successfully and original evidence was retained, but **one of two independent datasets failed the identified-functionals screen**. This is a *stage-zero computational pilot*, **not** convergence qualification over many datasets, simulation-based calibration, nominal interval coverage, or authorization to publish 1.2.

## Independent original source

The actual PyMC rank-two full posterior and all 30 parameter gradient comparisons were previously validated mathematically in [R2](b6-b7-rank2-pymc-r2-research-protocol.md). The present study is the *next, separate* statistical-computation step, on experimental draft [PR #279](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/279), original scientific source commit `cbfe81680654ab6b2b17265d14b0bf7f4a377042`.

[Original scientific workflow #38096271285](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38096271285) completed the two genuine four-chain PyMC posterior fits, the three Python rotation-invariance research contract environments, and SHA256 verification. The audit reports **two planned datasets, two completed fits, zero fitting exceptions, one exploratory screen pass and one failure**, with no missing evidence artifact. The **original engineering workflow on that commit had an optional ArviZ test-collection failure** (not a numerical sampler error); it was corrected on experimental PR #279 in subsequent commit `fc3dc8329f4e5d46d8758e87ec8d793c3578ddf6`. The mathematical/sampling conclusions here are sourced to the *unchanged original scientific run*; corrected-head overall CI is a distinct status.

The design uses **one new independent matched-Gaussian-prior rank-two dataset in each planar observation design** (paired x/y; genuinely asynchronous x/y timestamps), **four synthetic participants per dataset**, fixed known noise, four NUTS chains with **700 warmup and 400 retained draws per chain**, and target acceptance 0.94. Population means, x and y variances, and x/y cross-covariances at quarter/midpoint/three-quarter grid positions produce **15 sign- and factor-rotation-invariant functionals** per dataset. All source plots and table quantities below were read from original checksum-validated `case.json` artifacts.

![Original rank-two paired versus asynchronous worst convergence and minimum ESS comparison](../assets/research/b6-b7-rank2-nuts-r3-diagnostics-20261011.svg)

| Actual scientific outcome | Paired x/y | Asynchronous x/y |
|---|---:|---:|
| Original fitting artifact | `11686840512` | `11686377461` |
| Actual fit status | Completed | Completed |
| Worst rank-normalized R-hat across 15 identified functionals | **1.00538756** | **1.01397328** |
| Minimum bulk ESS | **454.35** | **326.41** |
| Minimum tail ESS | 693.11 | 540.59 |
| Minimum energy BFMI | 0.69472 | 0.82954 |
| NUTS divergences | 0 | 0 |
| Number failing identified-functionals screen | **0/15** | **6/15** |
| Marginal 90% intervals containing the generating truth (descriptive only) | 15/15 | 10/15 |
| Total fitting time including compilation/tuning/sampling | 668.58 sec (11.1 min) | 2,146.16 sec (35.8 min) |

The separately preserved original [aggregate artifact `11686793076`](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38096271285) verifies both dataset attempts and source hashes. **Fitting succeeded** in both; **computational qualification did not** in the asynchronous one.

## Localization of the asynchronous failure

All **six asynchronous failed population functionals are means**: x and y at each of the quarter, midpoint and three-quarter grid positions. The largest R-hat is **1.01397328** for **x mean at three-quarters**, and the lowest bulk ESS is **326.41** for **y mean at quarter**. All **nine** population variance and x/y covariance functionals in the asynchronous dataset passed their individual numerical screens, despite the overall failure.

This is a targeted diagnostic clue, not a proven general property of asynchronously sampled eye-tracking models. The study has **only one dataset per design and four simulated participants per dataset**. The posterior-mean geometry, asynchronous observation sparsity and identification should be investigated before deciding whether a longer chain, a different parameterization or different sampling design is warranted. No causal comparison of pairing versus asynchrony is established.

The original single-dataset truth-in-90%-interval counts **15/15** and **10/15** must **not** be treated as coverage estimates: the 15 outcomes within each dataset are dependent and one dataset failed the convergence screen. Likewise, the elapsed times are not a matched-hardware cross-architecture speed comparison.

## Scientific decision

Rank-two PyMC log posterior/gradient correctness is verified *in the four earlier mathematical cases*; actual rank-two posterior computation is **feasible in these two attempts but not reliably qualified**, and its asynchronous mean-functionals warning is unresolved. A subsequent rank-two study must prespecify additional independent datasets and assess the failure mechanisms without silently conditioning on successes. Proper SBC, posterior predictive validation, fixed-truth coverage, rank-two interval calibration and matched-compute runtime comparisons remain separate gates.

Research implementation remains in draft PR #279; documentation integration does **not** authorize merging that implementation or replacing native Gibbs in the stable package. [Bayesian blocker #255](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/255) remains open, as does independent [F5 blocker #256](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/256). Published stable **1.1.0** remains unchanged; **1.2 is unreleased**.
