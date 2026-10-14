# W3 R20 — estimated working covariance from observable gaze observations

**Research numerical preflight, not empirical inference qualification.** Previous R16–R19 numerical validation used the simulation-known participant covariance as a CR2 working target. Such a target is unavailable for observational eye-tracking applications. This draft explores estimating a *restricted additive variance-component family* from the same observed participant response curves without accessing the generating covariance, primitive Gaussian innovation draws or true source mean.

## Fixed, observable-only covariance families

For participant i, native time t, predictor x_i and trial label j, the unweighted covariance family is

`V_i(theta)=theta_a u_a u_aᵀ + theta_b u_b u_bᵀ + theta_trial I(same trial) + theta_sensor I`,
with `u_a(t)=1+0.30 t`; and two **predeclared competing** slope structures, `u_b(t)=1+0.25 t` (shared) or `u_b(t)=x_i(1+0.25 t)` (predictor-scaled). They are intentionally aligned with the simulator's restricted Gaussian covariance shape; neither form is asserted to be universally correct for eye-tracking recordings. No data-dependent oracle model selection is allowed. The four nonnegative variance components are **estimated** using only observed participant times, values, predictors, trial IDs and WLS weights; the source generating random effects and covariance parameters are not read.

The fitted regression residuals are `e=sqrt(W)(y−X beta_hat)`. Because these are attenuated by participant and regression leverage, naive moment matching `e_i e_iᵀ≈V_i` is inappropriate, particularly for the high-leverage conditions under investigation. Instead, for each component k and participant i, compute the exact expected **residual** covariance `D_ik=[(I−H) K_k (I−H)ᵀ]_ii` without constructing a global N×N residual maker, using participant blocks and Gram matrices. Solve a prespecified nonnegative least-squares pooled Frobenius loss `sum_i||e_i e_iᵀ−sum_k theta_k D_ik||²`. This corrects the conditional *expected moment operator* for leverage if the parametric covariance family holds; it does **not** make estimated variance components unbiased in all finite samples, nor account for uncertainty from estimating them when using CR2/Satterthwaite.

Return both covariance-family components and diagnostics: NNLS residual, scaled operator rank and condition number, any regularization/floor intervention, and explicit inference and release flags. For reference CR2 the target must be positive definite. A declared sensor-variance numerical floor is a computational safeguard and **must** be disclosed in the output, rather than being silently treated as empirical evidence. The implementation remains a standalone dense-within-participant research tool, not the library's public API.

## Independent preflight contracts

Compare observed-only constructed design matrices and weights with R17 original-source contracts. Only in numerical **tests**, confirm that the prespecified source family with **true simulation variance coefficients** reconstructs the original known source covariance under matched structural assumptions; the estimator itself cannot access those true coefficients. Require finite nonnegative fitted components and SPD covariance, numerical CR2 matrix identities with both correctly and incorrectly specified predeclared families, and strict rejection of malformed inputs. Run Python 3.11–3.13. Do not infer successful nominal pointwise coverage from these checks.

## Next separate finite-sample experiment

A future independently seeded study should compare oracle-supplied, feasible estimated and deliberately misspecified working targets under **both** slope structures and covariate leverage, reporting component recovery/boundary behavior, estimated-target vs oracle CR2 SE/df, failures and nominal 90% midpoint inclusion with independent-block Wilson Monte Carlo uncertainty. Estimating covariance from the same data makes the conditional Satterthwaite reference degrees of freedom approximate; a separate qualification stage (e.g., independent source replication, bootstrap or nuisance-estimation-aware uncertainty) is required.

Scientific issues #289/#296 remain open. No release, public API, simultaneous band or PyPI publication is authorized.
