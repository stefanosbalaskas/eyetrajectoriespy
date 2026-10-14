# W3 R16 — CR2 coefficient-specific Satterthwaite reference

Research-only conditional Gaussian moment matching for a fixed linear WLS contrast and **prespecified, known** block-diagonal working covariance target. The reference forms each cluster's adjusted score contrast as a linear functional of observed residuals; with residual-maker R=I-H, source covariance Φ, and score vectors q_i, the sandwich variance is a quadratic form in Gaussian errors. Let C have elements q_iᵀΦq_j. Then the moment-matched reference degrees of freedom is **tr(C)² / tr(C²)**. This is a coefficient-specific small-sample calculation, not n−1 and not an empirically qualified inferential procedure.

The test suite checks finite nonnegative eigenvalues, consistency of analytical mean and variance against eigenvalue sums, invariance under scalar target rescaling, and rejection of singular covariance targets. Future validation must compare degrees of freedom to the externally implemented `clubSandwich::coef_test(test="Satterthwaite")` on frozen data, and evaluate interval inclusion with a source covariance target matching the generator. Inference under an estimated covariance target, covariance misspecification, non-Gaussian noise and asynchronous clinical source data remain unqualified.

No public API, protected main merge, release tag or PyPI publication is authorized. Blockers #289 and #296 remain open.
