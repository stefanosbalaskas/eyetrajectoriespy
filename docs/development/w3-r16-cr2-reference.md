# W3 R16 — research-only CR2 numerical reference

This standalone implementation computes a **working-identity** CR2 bias-reduced linearization adjustment for clustered weighted least squares. The chosen working covariance target is identity *after observation-weight whitening*, not the true correlated within-participant source covariance in R16.

For each participant i, weighted design Z_i = W_i^(1/2) X_i, G = sum Z_iᵀ Z_i and G = L Lᵀ, with adjusted score L(I − L⁻¹Z_iᵀZ_i L⁻ᵀ)⁻¹/²L⁻¹ Z_iᵀ e_i. CR2 covariance is G⁻¹ times the sum of adjusted score outer products times G⁻¹.

An independently computed numerical comparator builds the entire participant observation-space hat block H_ii = Z_i G⁻¹ Z_iᵀ and transforms the observed weighted residual with (I−H_ii)⁻¹/². The two routes are tested against each other. Their agreement confirms this particular linear algebra implementation, **not** statistical calibration in the correlated R16 generator or equivalence to a fully independently implemented external package.

This tranche has no R16 outcome-generating run, Satterthwaite degrees of freedom, generalized working covariance, or package API promotion. A further matched study must independently compare the implementation with the R `clubSandwich` CR2 estimator and appropriately compute coefficient-specific small-sample reference degrees of freedom. In particular, substituting t(n−1) without validating degrees of freedom is not a qualified CR2 inferential method.

R16 research remains draft; version 1.2 unreleased; scientific blockers #289 and #296 remain open; `production_release_ready=false`.
