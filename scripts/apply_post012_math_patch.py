"""Insert the stable sparse-MFPCA mathematical contract into docs/registry."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MATH = r'''## Native sparse multivariate FPCA / joint PACE { #sparse-mfpca-joint-pace }

For paired planar curve $i$ observed at native times $t_{ij}$,

$$
\mathbf X_i(t)=
\begin{bmatrix}X_i(t)\\Y_i(t)\end{bmatrix},
\qquad
\mathbf Y_{ij}=\mathbf X_i(t_{ij})+\boldsymbol\epsilon_{ij}.
$$

The vector mean is $\boldsymbol\mu(t)=E\{\mathbf X(t)\}$ and the joint covariance surface is

$$
\mathbf C(s,t)=
\begin{bmatrix}
C_{xx}(s,t) & C_{xy}(s,t)\\
C_{yx}(s,t) & C_{yy}(s,t)
\end{bmatrix}.
$$

The directional transpose relation is

$$
C_{yx}(s,t)=C_{xy}(t,s),
$$

while generally $C_{xy}(s,t)\neq C_{xy}(t,s)$.

Latent covariance smoothing uses temporally off-diagonal products

$$
r_{ixj}r_{ix\ell},\qquad r_{iyj}r_{iy\ell},\qquad r_{ixj}r_{iy\ell},\qquad j\neq\ell.
$$

Temporally same-index products are excluded so contemporaneous measurement-error covariance is not absorbed into the latent cross-channel surface under the declared error model.

The vector eigenfunctions

$$
\boldsymbol\phi_k(t)=
\begin{bmatrix}\phi_{kx}(t)\\\phi_{ky}(t)\end{bmatrix}
$$

solve

$$
\int \mathbf C(s,t)\boldsymbol\phi_k(s)\,ds
=\lambda_k\boldsymbol\phi_k(t),
$$

under

$$
\langle\mathbf f,\mathbf g\rangle
=\int\{f_x(t)g_x(t)+f_y(t)g_y(t)\}\,dt.
$$

On the evaluation grid,

$$
\mathbf W_2=I_2\otimes W,
\qquad
\mathbf K=\mathbf W_2^{1/2}\widehat{\mathbf C}\mathbf W_2^{1/2}.
$$

PSD inspection/projection is performed on the **joint** weighted operator $\mathbf K$, not independently on marginal blocks.

The declared contemporaneous measurement-error covariance is

$$
\mathbf R_\epsilon=
\begin{bmatrix}
\sigma_x^2 & \sigma_{xy}\\
\sigma_{xy} & \sigma_y^2
\end{bmatrix}.
$$

For curve $i$ with $m_i$ paired observations,

$$
\widehat{\boldsymbol\Sigma}_i
=\widehat{\mathbf C}^{TM}_i
+I_{m_i}\otimes\mathbf R_\epsilon
+\gamma I_{2m_i},
$$

and joint PACE scoring is

$$
\widehat\xi_{ik}
=\widehat\lambda_k
\widehat{\boldsymbol\phi}_{ik}^{\top}
\widehat{\boldsymbol\Sigma}_i^{-1}
(\mathbf y_i-\widehat{\boldsymbol\mu}_i).
$$

$\widehat{\boldsymbol\Sigma}_i$ uses the **full fitted joint covariance**, not a rank-$K$ reconstruction. `n_components` controls only the returned eigensystem/scores.

Evaluating fitted population objects at native observation times is fitted-model evaluation, not interpolation of raw sparse trajectories.

**API:** `fit_sparse_mfpca()`.

**Documentation helpers:** `sparse_mfpca_score_frame()`, `sparse_mfpca_reporting_text()` summarize retained outputs but do not define separate estimators.

**Scope:** two jointly observed sparse planar coordinates with matched retained timestamps, direct directional cross-covariance estimation, explicit numeric mean/covariance bandwidths, full joint PSD handling, declared measurement-error covariance, and full-covariance joint PACE. Raw curves are not pre-interpolated to a common grid; automatic bandwidth or arbitrary cross-channel noise estimation is not implied.

'''

CONTRACT = r'''    MathematicalContract(
        key="sparse-mfpca-joint-pace",
        title="Native sparse multivariate FPCA / joint PACE",
        public_api=("fit_sparse_mfpca",),
        equations=(
            r"\mathbf X_i(t)=\begin{bmatrix}X_i(t)\\Y_i(t)\end{bmatrix}",
            r"\mathbf C(s,t)=\begin{bmatrix}C_{xx}(s,t)&C_{xy}(s,t)\\C_{yx}(s,t)&C_{yy}(s,t)\end{bmatrix}",
            r"C_{yx}(s,t)=C_{xy}(t,s)",
            r"\int \mathbf C(s,t)\boldsymbol\phi_k(s)\,ds=\lambda_k\boldsymbol\phi_k(t)",
            r"\widehat{\boldsymbol\Sigma}_i=\widehat{\mathbf C}_i^{TM}+I_{m_i}\otimes\mathbf R_\epsilon+\gamma I",
            r"\widehat\xi_{ik}=\widehat\lambda_k\widehat{\boldsymbol\phi}_{ik}^{\top}\widehat{\boldsymbol\Sigma}_i^{-1}\{\mathbf y_i-\widehat{\boldsymbol\mu}_i\}",
        ),
        site_anchor="sparse-mfpca-joint-pace",
        scope=(
            "Two jointly observed planar sparse functional coordinates with "
            "direct directional cross-covariance estimation, explicit mean and "
            "covariance bandwidths, full joint PSD handling, declared "
            "measurement-error covariance, and full-covariance joint PACE. "
            "Raw sparse curves are not interpolated to a common grid; automatic "
            "bandwidth or arbitrary cross-channel noise estimation is not implied."
        ),
    ),
'''


def main():
    path = ROOT / "docs/methods/mathematical-reference.md"
    text = path.read_text(encoding="utf-8")
    marker = "## Integrated functional $L^2$ distance { #functional-l2 }"
    if "{ #sparse-mfpca-joint-pace }" not in text:
        if text.count(marker) != 1:
            raise RuntimeError("mathematical reference marker mismatch")
        path.write_text(text.replace(marker, MATH + marker, 1), encoding="utf-8")

    path = ROOT / "src/eyetrajectoriespy/mathematical_contracts.py"
    text = path.read_text(encoding="utf-8")
    marker = '    MathematicalContract(\n        key="functional-l2",'
    if 'key="sparse-mfpca-joint-pace"' not in text:
        if text.count(marker) != 1:
            raise RuntimeError("registry marker mismatch")
        path.write_text(text.replace(marker, CONTRACT + marker, 1), encoding="utf-8")


if __name__ == "__main__":
    main()
