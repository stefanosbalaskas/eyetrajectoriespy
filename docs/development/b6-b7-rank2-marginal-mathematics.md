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
