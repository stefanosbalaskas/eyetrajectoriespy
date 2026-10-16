# W3 R53 — local response influence of fitted Gaussian REML covariance on the CR2 pivot

**Prospectively frozen, research-only differential-method study.** This is not a corrected 90% pointwise confidence interval, a sampling-law derivation, simultaneous functional inference or an eyetrajectoriespy release.

## Scientific motivation

R52 established that the direct known-covariance finite-Gaussian CR2 pivotal critical may differ materially from conditional Satterthwaite under high leverage, even with an oracle working covariance. However, **estimating** the working covariance on the *same* Gaussian outcomes introduces additional dependence not represented by either fixed-covariance reference distribution. The R53 question is: Can the local response influence of the observed Gaussian REML nuisance estimator be derived explicitly and verified numerically, and can its local effect on the CR2 denominator and studentized focal coefficient be separated from the direct residual-score effect?

R53 is intentionally **small and derivative-focused**; it does not rerun R49–R52 bootstrap coverage studies, does not import the source simulator's true covariance into the fitted estimator, and does not assume that an observed REML estimate is a fixed population quantity. It uses Gaussian covariance kernels as a scientific mathematical working model and retains strict numerical refusals.

## Derivation at a smooth interior local REML solution

Let `Z = sqrt(w) X`, `y_w=sqrt(w)y` and `V(theta)=sum_{k=1}^4 theta_k K_k`, where the four fixed native design-weighted Gaussian covariance kernels correspond to participant intercept, predictor-scaled participant slope, trial intercept and sensor variance. Write

`P=V^{-1}-V^{-1}Z(Z'V^{-1}Z)^{-1}Z'V^{-1}`.

The negative restricted Gaussian log-likelihood derivative in **absolute physical variance-component coordinates** is

`s_k(theta,y_w) = (1/2)[tr(P K_k)-y_w' P K_k P y_w]`.

The **observed**, not expected Fisher, Hessian is

`H_{kl}=(1/2)[-tr(P K_l P K_k)+2 (K_l P y_w)' P(K_k P y_w)]`,

while its mixed response derivative is

`d s_k/d y_w = -(P K_k P y_w)'`.

At an **interior locally stationary** four-component REML solution with invertible positive-definite observed Hessian, implicit differentiation of `s(theta_hat(y),y)=0` gives

`D_y theta_hat = H^{-1} B`,

where row `k` of `B` is `(P K_k P y_w)'`. The sign follows from the negative mixed derivative. This response Jacobian is a **local derivative of a selected interior root**, not a global sampling influence function, asymptotic normality theorem, or proof of a unique REML optimum. It is invalid at active parameter-box constraints, singular Hessians, discontinuous local-optimum selection or model misspecification without further derivation.

The original R22 CR2 squared focal standard error is

`q(y_w,theta)=sum_i (h_i(theta)' y_w)^2`,

where `h_i(theta)` is the original scaled-Cholesky cluster-adjustment residual-score vector for the fixed design and working target `V(theta)`. Holding covariance fixed,

`partial_y q|theta = 2 sum_i (h_i' y_w) h_i`.

R53 computes `partial_theta q` using **central physical-component finite differences** of the unchanged R22 CR2 routine at **fixed original observed y_w**, with relative per-component difference step **2×10⁻⁴**. It then calculates the total local response derivative

`D_y q=partial_y q|theta + (partial_theta q) (D_y theta_hat)`.

For `n=c' beta_WLS-c' beta_true` and `T=n/sqrt(q)`, the exact WLS numerator response gradient is `D_y n=Z(Z'Z)^{-1}c`, so

`D_y T=(D_y n)/sqrt(q) - n (D_y q)/(2 q^(3/2))`.

**This formula includes the local first-order covariance-refitting channel through `partial_theta q × D_y theta_hat`. It does not include its full finite-sample nonlinear distribution**, and it is not an analytic nuisance-adjusted CR2 standard error or confidence interval.

## Frozen original sources and independent verification

New generating seed **202610175353** and perturbation-direction seed **202610175354**, distinct from previous stages. Generate **four new independent Gaussian primitive innovation blocks**, each n=24 with native irregular repeated trials and true positive predictor-dependent participant random-slope covariance. Pair ordinary/extreme dependent predictor leverage **within** each block, yielding **eight paired source cases but four independent blocks per leverage stratum**. The projected native-design true focal coefficient enters *only* the evaluation of studentized response derivatives; source oracle covariance and latent source innovations never enter the observed nuisance estimator.

The original nuisance estimate is the **unchanged R49 two-start physical-positive Gaussian REML fit**, accepting only a candidate with optimizer success, reconstructed original likelihood, projected physical KKT **≤0.001** and NLL within **0.001** of the lowest observed two-start likelihood. Refuse a local derivative when any component sits within **20×** the original physical-variance-ratio box boundary, when the observed Hessian is not **strictly positive definite**, when its spectral condition exceeds **10⁹**, or when the original CR2 Cholesky/identity checks refuse. **Never regularize or silently replace a nonpositive Hessian**, reuse the known source covariance, or classify a derivative refusal as an inferential success.

The mathematical regression tests separately compare the direct matrix physical Gaussian REML score against the preexisting analytic score, the observed Hessian against central numerical score derivatives, the mixed response score derivative against symmetric raw weighted-response perturbations, the WLS focal numerator linear form, and both direct-response/fixed-nuisance-parameter squared-CR2 standard-error derivatives against original R22 CR2 computations.

For each accepted local derivative, draw **three** frozen independent participant-aligned Gaussian random perturbation directions on the *weighted observed native responses*, normalized to a deterministic weighted length. The perturbation magnitude in each direction is **0.003×** the original observed weighted response RMS, with minimum scale **0.01**. Refit the original **full four-component two-start physical Gaussian REML estimator** separately on `y_w + h d` and `y_w - h d`. Recompute original R22 CR2 in both refits and compare symmetric centered differences in **all four nuisance components, squared focal CR2 SE and the source-truth-centered studentized focal pivot** against the local implicit derivatives. Record numerical start outcomes, direction seeds, selected KKT/NLL diagnostic values, derivative discrepancies and any refused/unstable fit. Do not retune `h` or suppress direction failures to improve apparent agreement.

This is a **directional local-linear numerical validation**, not a nonparametric bootstrap, calibrated finite-sample Gaussian interval, expected-information estimate or proof that first-order derivatives approximate arbitrarily large perturbations.

## Expected full failure-inclusive denominator

Exactly **4 independent blocks ×2 paired supports = 8 original source cases**. Each has **3 frozen weighted-response perturbation directions**, totaling **24 directional records**. Each direction has a `+` and `−` full four-component nuisance refit, giving **48 prespecified perturbation refit attempt slots**, plus 8 original nuisance fits, **56 planned nuisance fits**, and **112 prespecified individual optimizer-start outcomes**. If an original source, Gaussian REML fit, active-box numerical check, nonpositive/ill-conditioned observed Hessian or CR2 differential step refuses, retain the case and its three *not_attempted* directional records. If any perturbed refit refuses, retain the direction as *refused*, including the attempted plus/minus optimizer starts and the complete planned denominator. Do not simulate replacement sources or convert a numerical refusal into a coverage success.

The original source archive includes `cases.json`, `summary.json`, `source-commit.txt` and `SHA256SUMS`. Report original source count, accepted/refused local derivatives, original accepted two-start fits, executed plus/minus refits versus all 48 planned attempt slots, median observed discrepancy in `D_y theta` and `D_y T` among accepted directions **without hiding refusals**. Scientific inferences cannot be based solely on the accepted smooth-interior subsample.

## Explicit boundaries

R53 only derives the smooth-local Jacobian of an **interior** Gaussian REML estimating root and traces its first-order influence through the original CR2 quadratic residual score. It **does not derive** the full joint sampling distribution of the nonlinear random covariance estimator, the CR2 contrast numerator and the residual quadratic denominator; it **does not calibrate** nominal 90% pointwise confidence intervals, 90% simultaneous whole-trajectory bands or a variance-component-null boundary test. It does not identify response-dependent MAR/MNAR point loss or latent whole-participant dropout, and it does not account for non-Gaussian outcomes or wrong Gaussian covariance kernels. Distinguish a local Hessian numerical pass from global optimum certification and independent sampling-law validation.

Preserve all positive **and unfavorable** original evidence R20/R22/R33–R52. Keep [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) **OPEN**, research branch draft only, and do not merge protected main, promote a public inference API, tag 1.2 or publish PyPI.
