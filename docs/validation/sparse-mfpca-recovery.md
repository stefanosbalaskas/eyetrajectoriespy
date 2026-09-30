---
title: Native sparse MFPCA recovery validation
---

# Native sparse MFPCA recovery validation

This page defines the PR D known-truth evidence contract for the native two-channel sparse MFPCA estimator. Truth is supplied only after fitting.

## Identification-aware recovery

The public component arrays use time-major functional geometry, while covariance is retained as named channel blocks. Covariance recovery is therefore evaluated block by block rather than by flattening the channel-major operator through generic multivariate recovery code.

For each block pq,

$$
ISE_{pq}=\sum_{g,h}[\widehat C_{pq}(t_g,t_h)-C_{pq}(t_g,t_h)]^2w_gw_h.
$$

The joint covariance error is

$$
ISE_{\mathbf C}=ISE_{xx}+ISE_{xy}+ISE_{yx}+ISE_{yy}.
$$

The evaluator records all four named blocks explicitly so storage ordering cannot change the estimand.

## Tied eigenspaces

Individual eigenfunctions and score coordinates are not identified inside a tied eigenspace. The recovery evaluator therefore does not emit component_absolute_similarity, score_correlation, or score_rmse for truth components inside an identified tied block.

Instead it records principal cosines/angles for that eigenspace and score_subspace_procrustes_rmse after optimal orthogonal alignment of fitted and generating score coordinates.

The deterministic qualification family contains exact ties at rho_xy=0. A relative truth-eigenvalue tolerance of 1e-8 is retained in assessment provenance. A fitted truncation that splits a tied truth eigenspace fails recovery evaluation rather than treating an arbitrary component as uniquely identified.

## Deterministic qualification family

The fixed-marginal planar family uses rho_xy = -0.6, 0, 0.3, 0.6, 0.9 with the same marginal x/y covariance across rho. Negative rho reverses the cross-channel covariance sign while leaving the marginal covariance unchanged.

A separate asymmetric case uses two orthonormal scalar modes u and v:

$$
\psi_1(t)=\frac{1}{\sqrt 2}[u(t),v(t)]^\top,\qquad
\psi_2(t)=\frac{1}{\sqrt 2}[u(t),-v(t)]^\top,
$$

with unequal eigenvalues. Its truth satisfies

$$
C_{xy}(s,t)=\frac{\lambda_1-\lambda_2}{2}u(s)v(t)\ne C_{xy}(t,s)
$$

while retaining C_{yx}(s,t)=C_{xy}(t,s). Qualification requires directional cross-covariance recovery to improve on the zero-cross-covariance baseline.

One additional case supplies the true correlated measurement-error matrix

$$
R_\epsilon=\begin{bmatrix}0.0009&0.0003\\0.0003&0.0016\end{bmatrix}.
$$

This is a supported-input check for joint PACE, not measurement-error estimation recovery.

## Guarded versus descriptive evidence

The sparse-mfpca-recovery CI job runs the small deterministic qualification matrix with predeclared finite-sample guards. Mean recovery is scaled to the analytic latent finite-sample reference $E\{ISE(\bar X-\mu)\}=\sum_k\lambda_k/n$. For the independent curve-score design used here, the guard requires fitted mean ISE to remain below twice this reference rather than imposing an arbitrary absolute ISE threshold across signal scales.

The first qualification execution used an absolute mean-ISE guard of 0.03 and is retained as failed evidence. For the rho family, $\sum_k\lambda_k/n=2.9/36\approx0.0806$, so that absolute guard was below the scenario's own expected finite-sample latent-mean deviation. The guard definition was therefore corrected to the scale-aware ratio before qualification was accepted; no other recovery guard was relaxed.

The sparse-mfpca-sensitivity job separately records evaluation grids G = 31, 51, 81 and score ridge gamma = 0, 1e-8, 1e-6, 1e-4.

The same analytic process is regenerated directly on each truth grid rather than interpolating truth between grids. Sensitivity tables set selection_performed=false; no tuning value is chosen from them.

## PR D qualification evidence

The seven deterministic native cases passed the current guarded qualification matrix. Across the five rho cases, the minimum whole-subspace principal cosine ranged from 0.953 to 0.994, separated-component median score correlations ranged from 0.844 to 0.992, score-system failure rate was zero, and reconstruction ISE ranged from 0.010 to 0.033. At rho_xy=0, where the two channel modes are tied within each temporal eigenspace, component-specific score metrics were omitted and the maximum tied-eigenspace Procrustes score RMSE was 0.198.

The deliberately asymmetric cross-covariance case recovered Cxy with block ISE 0.0134 versus 0.1406 for the zero-cross-covariance baseline. Its minimum joint-subspace cosine was 0.987 and median separated score correlation was 1.000 to three decimals. This is evidence for directional Cxy recovery, not merely the implementation transpose identity.

The correlated measurement-error case supplied the true fixed matrix rather than estimating it. It completed with zero score failures, minimum subspace cosine 0.996, median separated score correlation 0.934, reconstruction ISE 0.0113, and the assessment records measurement_error_truth_supplied=true.

Grid sensitivity was effectively stable from G=31 through G=81: minimum subspace cosine stayed near 0.957, median score correlation near 0.881, reconstruction ISE near 0.0311, and joint covariance ISE near 0.470. The score-ridge sensitivity likewise changed recovery negligibly over gamma=0 through 1e-4; gamma=1e-4 reduced the median score-system condition number from about 28,954 to 26,059 without a meaningful score-recovery change. These are descriptive observations only; selection_performed remains false and the public default ridge is unchanged.

## Evidence boundary

PR D asks whether the native estimator recovers known joint planar truth under its own supported contracts. It does not test external equivalence. The two-stage benchmark and mGSFPCA comparison remain PR E work; observation-loss stress and performance qualification remain downstream evidence.
