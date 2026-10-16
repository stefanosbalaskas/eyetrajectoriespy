# W3 R52 — prospective finite-Gaussian CR2 joint-numerator/residual-score reference law

**Mathematical research-only reference experiment, not a corrected estimated-covariance confidence interval.** The purpose of this stage is to compute the finite-design Gaussian pivot distribution implied by the original scaled-Cholesky CR2 geometry when the covariance target is frozen, without approximating the entire studentized statistic by a Student-t law. This is the next scientific response to R51's high-leverage finding that Gaussian nuisance-refit bootstrap-t critical values were markedly smaller than conditional Satterthwaite critical values.

## Exact fixed-target Gaussian algebra

Write the native weighted regression as `Y_w=Z beta+epsilon`, with a **fixed full-rank** weighted design `Z=X diag(sqrt(w))`, Gaussian errors `epsilon ~ N(0,V)`, and a fixed pointwise coefficient contrast `c`. Let `K=(Z'Z)^(-1)`, `u=Z K c`. The numerator of the studentized contrast is the **linear Gaussian** variate

`N=c' (beta_hat-beta) = u' epsilon`.

For each participant/cluster `i`, let `Z_i` be their native weighted design and `Phi_i` the **fixed working covariance target**. Using the original R22 scaled-Cholesky CR2 symmetric positive definite adjustment `A_i` (solving `A_i D_i A_i' = Phi_i`), define `g_i=A_i Z_i K c`. If `P_i` selects the cluster's native rows from the stacked trial sample, the adjusted contrast score equals

`S_i = g_i' (P_i - Z_i K Z') epsilon = h_i' epsilon`, with `h_i=P_i' g_i - Z K Z_i' g_i`.

Consequently, for **fixed target, fixed design, and the true Gaussian source covariance** `V` the vector `(N,S_1,...,S_G)'` is jointly zero-mean Gaussian with exactly computable covariance

`Omega = L V L'`,

where the first row of `L` is `u'` and remaining rows are the `h_i'`. The original CR2 coefficient contrast standard error satisfies

`SE_CR2^2 = sum_i S_i^2`.

The finite-Gaussian fixed-design/fixed-target studentized statistic is therefore

`T = N / sqrt(sum_i S_i^2)`.

**The numerator and cluster scores generally need not be independent.** R52 explicitly computes their cross-covariance in `Omega`. Unlike a t-approximation, `T` is a ratio of a (possibly score-correlated) normal linear form and the square root of a Gaussian quadratic form, not automatically an independent normal divided by a scaled chi-square.

The score covariance `C=Omega[1:,1:]` has exactly calculable quadratic moments `E[SE^2]=trace(C)`, `Var(SE^2)=2 trace(C^2)`, and a moment-matched Satterthwaite df `trace(C)^2/trace(C^2)`. Under the **true-covariance oracle target** `Phi=V`, these moments must independently agree with the original R22 CR2 Satterthwaite implementation (numerically, with tolerance **3e-7**), and the independently computed `N` and `SE^2` must match direct CR2 on synthetic centered responses. R52 preserves the original R22 adjustment refusals and never relaxes SPD thresholds.

### What is and is not exact

For an **oracle** target `Phi=V`, and a Gaussian mean truly in the fixed `Z` span, this is an exact analytical characterization of the **known-covariance** coefficient CR2 pivot distribution. The 90th percentile used in a numerical plot is still estimated from finite Monte Carlo draws and has Monte Carlo uncertainty.

For **observed-data REML-fitted** `Phi_hat(Y)`, freezing its observed value and evaluating the same joint Gaussian law using the **generating** `V` is only a **counterfactual frozen-target geometry diagnostic**. This is **not** the sampling distribution of the actual random plug-in CR2 statistic, and it is **not** the distribution conditional on having observed `Phi_hat(Y)=phi`. Conditioning on an estimator changes the law of the outcomes. R52 never describes a frozen fitted covariance as known for inferential validity, and uses source-generating `V` only for oracle/simulation reference; it is unavailable in empirical gaze data.

An additional reference, produced from the same Monte Carlo standard normals, holds `Var(N)` and the complete **cluster-score covariance `C`** fixed but sets the numerator-score cross-covariance to zero. This is an **artificial independence counterfactual**, useful for quantifying how much of the finite-Gaussian critical law difference is associated with numerator-score dependence. It is not a deployable inference procedure.

## Frozen small mechanistic study and numerical quantile uncertainty

**New primitive source seed `202610165252`**, distinct from R17–R51, with **four independently generated Gaussian primitive innovation blocks**, each n=24, true **positive predictor-dependent participant random-slope covariance** and the original native irregular trial design. The ordinary-dependent versus extreme-dependent predictor supports are **paired on the same four source blocks**. There are **eight source/support cases but only four independent Gaussian source blocks per leverage stratum**. Use the original native Legendre-five focal predictor-slope contrast, preserving projected generating mean and raw truth discrepancy.

For each source/support case, compare two frozen covariance targets:
1. The **true Gaussian source covariance oracle**, which supplies the mathematically exact fixed-model pivot geometry and is **simulation-only**.
2. The **four-component observed-only Gaussian REML fitted covariance**, selected by the unchanged R49 two-start positive physical variance-ratio solver and strict physical projected KKT **≤0.001**, within-observed-best NLL gap **≤0.001**, and objective reconstruction **≤1e-6**. This target is frozen as an explicitly counterfactual geometry reference, **not covariance-estimation uncertainty correction**.

For each target construct the exact `(G+1)×(G+1)` joint covariance and the artificial numerator-independent counterpart. With new independent numerical reference seed **`202610165253`**, draw exactly **16,384** IID standard-normal vectors **per target** and use the deterministic eigenvalue-based symmetric square root of each joint covariance. Compute the 90th percentile of `abs(N)/||S||` from the correlated normal model and from the artificially decorrelated model using **the identical standard normal vectors**. Report 95% **order-statistic quantile Monte Carlo bounds** from the binomial ranks in the original 16,384 sampled pivots. These quantify **numerical quantile estimation error only**, not the sampling uncertainty of an inferential coefficient interval. Record the ratio `q90(joint Gaussian)/q90(conditional fitted t-Satterthwaite)` and `q90(joint Gaussian)/q90(artificially independent numerator)`, plus numerator-score correlation and exact score quadratic moments, per source/target.

The original fixed ledger contains **8 source/support cases ×2 covariance targets =16 target records ×2 correlated/decorrelated quantile references =32 quantile slots**. Any Gaussian source failure, physical REML refusal, unstable CR2 adjustment, non-PSD joint matrix or failed quantile must remain recorded as a numerical refusal. Do not select successful cases for a more favorable denominator. Four source blocks supply **only a small mathematical feasibility check**, not an independent-population 90% coverage experiment.

## Scientific interpretation and release boundaries

A direct correlated Gaussian pivot quantile that differs from the conditional Satterthwaite critical can reveal whether **finite-design numerator-score dependence and non-chi-square score quadratic geometry** help explain R51's high-leverage reference-distribution gap. However, the fitted-working-target counterfactual still ignores that the target was estimated from the **same random gaze outcomes**. Even if a fixed-target exact-Gaussian quantile is close to one experimental bootstrap quantile, that does not imply either yields correct empirical 90% coverage. This is not a proof of nuisance-adjusted Satterthwaite degrees of freedom, or an endorsement of omitting Gaussian nuisance refitting.

R52 is not a function-wide **90% simultaneous band** study and does not calibrate random-slope variance boundary tests, Gaussian covariance-family misspecification, MAR/MNAR point loss or latent whole-participant selection. Maintain original R20/R22/R33–R51 unfavorable evidence, keep [scientific issue #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [missingness issue #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) **OPEN** and prohibit stable inference API promotion, protected-main merge, version 1.2 tag or PyPI publication.
