# W3 R24 — population moment operator versus finite Gaussian sample noise

Research-only analytic and conditional-simulation diagnostic stacked on the [R23 component-identifiability study](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/325). R23 successfully computed all **576 paired model-family cases**, but numerous positive generating variance components were estimated at the nonnegative least-squares boundary (84 intercept, 192 slope, 282 trial estimates of zero). The raw outer-product moment residual fit was often high. This does **not** establish whether the *population* residual-moment operator is misspecified or whether finite-sample moment noise and NNLS constraints are responsible.

## Frozen design and scientific identity

Reuse two **original R23** independently generated source blocks **0 and 7**, with nested n=24 and 96, original ordinary-support independent/dependent covariance source mechanisms, fixed Legendre-5 mean basis and **matched** predeclared shared versus predictor-scaled slope covariance family. Exactly **8 frozen source-design configurations, not 8 new independent generating blocks**. All native times, WLS design matrices, weights, participant/trial labels, and covariance structures remain unchanged from R23. No original observations are removed or relabeled.

For each fixed native design, construct the original R20 residual-moment design operator `A`, whose component columns for each participant are `vec(D_ik)` with `D_ik = [(I−H)K_k(I−H)ᵀ]_ii`. Independently derive `D_i` from the **actual generating block covariance** and verify `vec(D) = A theta_true` at relative error below `5e−9`. Solve the population **exact expected moment** equation using unchanged four-component NNLS: with a full-rank operator, the known positive components must be recovered to relative error below `5e−8`. This is an **oracle algebra/identification contract** in a mathematical reference experiment, not an empirical estimation method.

The same observed data are then used to verify that the reconstructed moment operator exactly reproduces the original R20 observation-only NNLS component estimates, allowing only its previously declared sensor-floor intervention.

## Prespecified finite sample noise

For each of the **8 fixed source designs**, generate **128 new independent conditional Gaussian innovation vectors** (seed `202610153401`, separate from R23 generating seed), each with the **same** known within-person covariance and native design; whitened WLS residualization is re-applied exactly. Fit the unchanged four-component NNLS moment estimator to the resulting noisy participant residual outer products **without** oracle coefficients being passed to the fit.

Report component-wise frequencies of zero estimates, 95% Wilson Monte Carlo intervals on **conditional boundary probabilities**, mean and median relative component errors, and the analytical Gaussian expectation of outer-product residual noise. For e_i ~ N(0,D_i), the exact second moment identity is `E||e_i e_iᵀ−D_i||_F² = (tr D_i)² + tr(D_i²)`. This highlights the irreducible one-outer-product-per-cluster noise, which can make raw Frobenius moment fits appear poor even with a correct working covariance family.

All 1,024 conditional draws are **NOT** 1,024 independent R23 source-design replications. Source-design independence remains only two generating blocks. No endpoint coverage, estimated-target inferential calibration, nuisance-estimation-aware Satterthwaite degrees of freedom, or simultaneous function-wide intervals are tested or qualified. Keep original R23 component boundary results unchanged and scientific issues #289 and #296 open. No public API, protected main, tags or PyPI release.
