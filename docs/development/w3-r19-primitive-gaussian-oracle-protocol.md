# R19 — original Gaussian primitive-innovation reconstruction audit

**Diagnostic research only; no new R18 generating blocks or amended original outcomes.** [R18 PR #319](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/319) reran n=96 Gaussian-oracle coverage for 192 newly seeded independent source blocks, two ordinary-support covariance mechanisms and Legendre-5/cubic-spline-13 bases. All 768 source/model cases completed; some normal-oracle rates again fell below 90%, with original standardized-error SD ~1.075–1.090. Both the original R16 source covariance and R18 direct block covariance calculations agreed numerically. This does not yet demonstrate a stochastic mechanism failure.

## Frozen originals and mathematically independent reconstruction

All 768 original R18 native asynchronous observation sets, predictor/trial mappings, Gaussian innovation draws, WLS weights, generated mean and midpoint truth remain identical; seed **202610142621** unchanged. Reference JSON `docs/development/w3-r18-original-gaussian-oracle-coverage-contract.json` freezes the **16 original truth/projection × normal/t coverage counts across four cells**, copied from original scientific run #38619203614 and commit `18701edf`. Any count difference makes the audit fail.

For each original source/model case let `q = W X (Xᵀ W X)⁻¹ c` denote observation-level influence weights for focal contrast `c`. Reconstruct `qᵀ(y−μ)` independently as sums over original **primitive Gaussian innovations**:

- participant random-intercept coefficients `a_i = Σ_{rows i} q_r σ_intercept(1+0.30t_r)`;
- participant random-slope coefficients `b_i = Σ_{rows i} q_r σ_slope(x_i or 1)(1+0.25t_r)`;
- trial coefficients `g_ij = σ_trial Σ_{rows ij} q_r`;
- sensor coefficients `h_r = σ_sensor q_r`.

Since these innovations were generated as independent standard normals, the exact conditional variance under the stated Gaussian source is `Σa_i² + Σb_i² + Σg_ij² + Σh_r²`. Compare it to both direct native response/mean residual weighting and the pre-existing R16 Gaussian source oracle variance. Any numerical mismatch causes an original-source failure recorded in the ledger.

Independently, at source block indices **0, 37 and 191** crossed with both ordinary covariance modes and both fixed bases (12 frozen designs), draw **1,024 new conditional innovation vectors per fixed design** from separate seed `202610142723` and check Gaussian-standardized mean, variance and 90% normal-critical inclusion. These additional Monte Carlo draws are conditional on selected designs and **must not be pooled with or rebranded as independent replications of the 192-block source experiment**.

## Decision boundary

The reconstruction tests the actual original generating error mechanism and exact variance, not only agreement between two covariance estimators. Even if it passes completely, 90% inclusion deficits in prior independent source runs remain recorded and warrant careful assessment of correlated Monte Carlo fluctuations, source-stream reproducibility and fresh-independent-block sampling. It does not qualify CR2 with an estimated covariance, pointwise empirical uncertainty or simultaneous bands. Issues #289/#296 remain open; no protected main merge, public API promotion, release tag or PyPI upload.
