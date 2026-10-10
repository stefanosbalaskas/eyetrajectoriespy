# B6/B7 rank-two: independent observed-data marginal likelihood

!!! danger "Rank-two posterior inference is not yet validated"
    This research-only mathematical falsification compares two independently
    implemented likelihood evaluations, not posterior MCMC, SBC or credible
    interval coverage. Protected main, stable 1.1.0 and 1.2 gates are unchanged.

With known channel-wise noise and k=2 Gaussian participant scores, the
observed-data likelihood is N(Xμ, D + (XL)(XL)ᵀ). This study computes each
participant's full observation-space Gaussian log density using a dense
covariance determinant and solve, then checks a separately implemented
Woodbury/determinant-lemma expression using Q = I₂ + (XL)ᵀD⁻¹(XL).

The predeclared contract covers **paired and asynchronous channels**, matched
rank-two Gaussian factor priors, and a **near-tied equal-eigenvalue stress
case outside the matched Gaussian loading prior**. Independent covariance and
likelihood values must be invariant to L → LR for a rank-two orthogonal R.
A single participant's missing channel measurements are excluded rather than
imputed. Each original mathematical run preserves source JSON and SHA256.

Passing numerical equality is necessary but not sufficient: before rank-two
four-chain NUTS, separately check differentiable PyTensor likelihood and
gradients against dense numerical derivatives and verify prior/parameterization
consistency. Rank-two posterior convergence, prior-based SBC, fixed-parameter
coverage and real-data usefulness remain OPEN under scientific issue #255.

## Verified source contract — 11 October 2026

The original [rank-two scientific workflow #38087129154](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38087129154) on draft [PR #273](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/273), exact source commit `f7a3ba6b8fd6dc6022bffdaf55c88b2eb137b10e`, passed **3/3 Python 3.11–3.13 scientific jobs** and preserved independently generated `cases.json`, `evidence.json` and `SHA256SUMS` in three artifacts. Its source ledger reports **four mathematical designs, zero contract failures**. Each Python job re-evaluates the same four prescribed design categories, not four new independent posterior datasets.

| Mathematical test design | Status | Statistical interpretation |
|---|---|---|
| Paired x/y, matched Gaussian rank-two loadings | Passed dense versus Woodbury likelihood and rotation-invariance thresholds | Observed-data numerical identity, not posterior inference |
| Asynchronous x/y, matched Gaussian rank-two loadings | Passed | Native observation-time masks retained |
| Paired x/y, near-tied equal-eigenvalue stress | Passed | Out-of-prior numerical stress, **not** matched-prior SBC |
| Asynchronous x/y, near-tied equal-eigenvalue stress | Passed | Out-of-prior numerical stress, **not** matched-prior SBC |

The original code declares an absolute dense-versus-Woodbury log-likelihood discrepancy threshold **< 10⁻⁷**, factor-rotation log-likelihood discrepancy **< 10⁻⁷** and maximum rotated-population-covariance discrepancy **< 10⁻¹⁰**. All four cases met the prespecified combined contract. **The aggregate logs report passing booleans rather than exact case-level numerical discrepancies**, so this page does not manufacture a numerical difference chart. Consult the retained `cases.json` in the original workflow artifacts for exact values.

Original retained artifacts: Python 3.11 `11681893932`; Python 3.12 `11682179563`; Python 3.13 `11681983569`. The source mathematical study changes no stable API, package version or production-release approval.

**Remaining independent gate:** compare the *actual PyTensor graph* (likelihood, priors, parameter-transform Jacobians and gradients) against external dense-Gaussian analytical or finite-difference references, then run rank-two NUTS with identifiable covariance/mean diagnostics. [Scientific blocker #255](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/255) remains open.
