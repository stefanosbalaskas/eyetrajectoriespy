# R22 — scaled Cholesky symmetric CR2 (isolated numerical preflight)

This is an **experimental, research-only independent implementation**, stacked on PR #323's original failure-preserving R21 cleanup. Never changes the original 256-case R20 scientific ledger or its 41 failures.

## Mathematical target and independent numerical construction

For observed WLS residual covariance `D_i` and estimated working target `Φ_i`, construct the **unique symmetric positive-definite** factor solving `A_i D_i A_iᵀ=Φ_i`. For `D_i=L_iL_iᵀ` using Cholesky, set

`A_i=L_i^{-T} [L_iᵀ Φ_i L_i]^{1/2} L_i^{-1}`.

This is algebraically equivalent to the dense original reference's symmetric CR2 factor, but uses separate positive matrix scalings to avoid rejecting well-conditioned targets solely because the absolute eigenvalues of `Φ_i^(1/2)D_iΦ_i^(1/2)` are below the previous `1e-11` absolute cutoff. Does NOT solve poorly identified covariance-model parameters, which can yield directions with untrustworthy relative accuracy.

Use a **fixed numerical refusal policy**: both `Φ_i` and `D_i` must pass unregularized Cholesky, the normalized product must have positive eigenvalues and condition at most **1e11**, the returned factor must remain symmetric SPD and its matrix identity relative Frobenius error must not exceed **3e−7**. On failure, return `UnstableCR2Adjustment`; do not floor eigenvalues, force positive matrices, or report a numerical estimate as calibrated. These thresholds are research preflight settings, not a new statistical model or inference selection rule.

For fully successful small numerical fixtures, compare point estimate, final CR2 SE and coefficient-specific Satterthwaite df against the *previous independent* blockwise reference. Independently check the symmetric adjustment against 75-digit mpmath linear algebra on a nontrivial SPD fixture, absolute common-scale invariance, matrix identity, and refusal for a predeclared excessively ill-conditioned target. The source code is **not in the public package**.

## Next original-source qualification

A separate failure-inclusive audit should reprocess all **256 original R20 model cases** on their original source seed. For each case report original reference result, scaled-Cholesky success or refusal, explicit reason, max product condition and relative adjustment identity error. Validate against the 215 originally successful cases numerically, and preserve the original 41 failures as historical failures regardless of new results. For the 32 sensor-floor boundary cases, passing double precision is insufficient by itself: independent higher-precision agreement or a documented refusal is mandatory. A future external `clubSandwich` comparison for nontrivial well-conditioned correlated targets must precede any numerical qualification.

The fitted covariance components and nuisance-estimation uncertainty have **not** been validated. No 90% pointwise calibration claim, simultaneous bands, main merge, public API, tag or PyPI release; issues #289 and #296 remain open.
