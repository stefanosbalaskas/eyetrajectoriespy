---
title: Mathematical reference
---

--8<-- "docs/methods/mathematical-reference-base.md:5:179"

**Scope:** univariate sparse/irregular FPCA with explicit numeric bandwidths,
support/noise contracts, PSD policy, retained component count, score ridge,
and fail-closed score diagnostics. Separate x/y fits do not model
cross-channel covariance; the stable joint planar estimator is documented in
the separate 0.12 contract below.

## Native sparse multivariate FPCA / joint PACE { #sparse-mfpca-joint-pace }

For paired planar curve $i$ observed at native times $t_{ij}$,

$$
\mathbf X_i(t)
=
\begin{bmatrix}
X_i(t)\\
Y_i(t)
\end{bmatrix},
\qquad
\mathbf Y_{ij}
=
\mathbf X_i(t_{ij})
+
\boldsymbol\epsilon_{ij}.
$$

The vector mean is

$$
\boldsymbol\mu(t)
=
E\{\mathbf X(t)\}.
$$

The joint covariance surface is

$$
\mathbf C(s,t)
=
\begin{bmatrix}
C_{xx}(s,t) & C_{xy}(s,t)\\
C_{yx}(s,t) & C_{yy}(s,t)
\end{bmatrix}.
$$

Its directional transpose contract is

$$
C_{yx}(s,t)=C_{xy}(t,s),
$$

while generally

$$
C_{xy}(s,t)\neq C_{xy}(t,s).
$$

Latent covariance smoothing uses temporally off-diagonal within-curve products,

$$
r_{ixj}r_{ix\ell},
\qquad
r_{iyj}r_{iy\ell},
\qquad
r_{ixj}r_{iy\ell},
\qquad
j\neq\ell.
$$

Temporally same-index products are excluded from latent covariance smoothing so that contemporaneous measurement-error covariance is not absorbed into the latent cross-channel surface under the declared error model.

The vector eigenfunctions

$$
\boldsymbol\phi_k(t)
=
\begin{bmatrix}
\phi_{kx}(t)\\
\phi_{ky}(t)
\end{bmatrix}
$$

solve

$$
\int
\mathbf C(s,t)\boldsymbol\phi_k(s)\,ds
=
\lambda_k\boldsymbol\phi_k(t),
$$

under the planar functional inner product

$$
\langle\mathbf f,\mathbf g\rangle
=
\int
\left\{
f_x(t)g_x(t)+f_y(t)g_y(t)
\right\}\,dt.
$$

On the evaluation grid, with quadrature matrix $W$,

$$
\mathbf W_2
=
I_2\otimes W,
\qquad
\mathbf K
=
\mathbf W_2^{1/2}
\widehat{\mathbf C}
\mathbf W_2^{1/2}.
$$

PSD inspection/projection is performed on the **joint weighted operator** $\mathbf K$, not independently on $C_{xx}$ and $C_{yy}$.

The declared contemporaneous measurement-error covariance is

$$
\mathbf R_\epsilon
=
\begin{bmatrix}
\sigma_x^2 & \sigma_{xy}\\
\sigma_{xy} & \sigma_y^2
\end{bmatrix}.
$$

For curve $i$ with $m_i$ paired native observations, the joint conditional covariance is

$$
\widehat{\boldsymbol\Sigma}_i
=
\widehat{\mathbf C}_i^{TM}
+
I_{m_i}\otimes\mathbf R_\epsilon
+
\gamma I_{2m_i}.
$$

Joint PACE scoring is

$$
\widehat\xi_{ik}
=
\widehat\lambda_k
\widehat{\boldsymbol\phi}_{ik}^{\top}
\widehat{\boldsymbol\Sigma}_i^{-1}
\left(
\mathbf y_i-
\widehat{\boldsymbol\mu}_i
\right).
$$

$\widehat{\boldsymbol\Sigma}_i$ uses the **full fitted joint covariance**, not a rank-$K$ covariance reconstruction. `n_components` controls the returned eigensystem and scores only.

Evaluating the fitted population mean, covariance, or eigenfunctions at native observation times is fitted-model evaluation; it is not interpolation of a raw sparse trajectory.

**API:** `fit_sparse_mfpca()`.

**Documentation helpers:** `sparse_mfpca_score_frame()` and `sparse_mfpca_reporting_text()` expose retained outputs and reporting text but do not define separate mathematical estimators.

**Scope:** two jointly observed sparse planar coordinates with matched retained timestamps, direct directional cross-covariance estimation, explicit numeric mean and covariance bandwidths, full joint PSD handling, declared measurement-error covariance, and full-covariance joint PACE. Raw sparse curves are not pre-interpolated to a common grid; automatic bandwidth selection or arbitrary cross-channel noise estimation is not implied.

--8<-- "docs/methods/mathematical-reference-base.md:188"
