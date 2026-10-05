# Sparse joint-PACE score-uncertainty qualification

This page documents the deterministic known-population qualification for the 1.1 development capability `sparse_mfpca_score_uncertainty()`.

## What is being qualified?

For a retained joint score vector $\boldsymbol\xi_i$ and paired native planar observations, the capability reports

$$
\operatorname{Var}(\boldsymbol\xi_i\mid\mathbf Y_i,\text{ fitted population})
=\mathbf\Lambda
-\mathbf\Lambda\mathbf\Phi_i^\top
\mathbf\Sigma_i^{-1}
\mathbf\Phi_i\mathbf\Lambda.
$$

The claim is deliberately narrow: this is **conditional-on-fitted-population uncertainty** for native sparse planar joint-PACE scores. It is not full uncertainty for sparse-MFPCA estimation.

The qualification therefore supplies the true Gaussian population mean, joint covariance operator, eigensystem, and measurement-error covariance to the score system. This isolates the conditional covariance calculation from sparse mean/covariance estimation, smoothing-bandwidth choice, PSD repair, and measurement-error estimation.

## Exact score system

The validation uses the same primitives as native `joint_pace_scores()`:

$$
\mathbf\Sigma_i
=\mathbf C_i^{TM}
+I_{m_i}\otimes\mathbf R_\epsilon
+\gamma I_{2m_i},
$$

where the fitted joint covariance is evaluated at the curve's retained native times in `time_major_interleaved_xy` order. The operator itself is retained in channel-major form. The posterior calculation uses a linear solve; it never constructs an explicit matrix inverse.

The evidence contract requires:

- the full fitted joint covariance rather than a rank-truncated reconstruction;
- paired synchronous x/y native observations;
- the declared 2x2 measurement-error covariance, including correlated-error cases;
- the same score ridge and condition policy as the fitted joint-PACE system;
- no raw sparse-trajectory interpolation;
- exact curve/order/support alignment with the fit.

## Oracle scenarios

The dedicated `sparse-mfpca-score-uncertainty-validation` workflow runs four deterministic scenarios with 500 curves each:

| Scenario | Native samples per curve | Measurement error |
| --- | --- | --- |
| `diagonal_sparse` | 5-7 | diagonal 2x2 covariance |
| `diagonal_dense` | 14-18 | same diagonal covariance |
| `correlated_sparse` | 5-7 | positive correlated 2x2 covariance |
| `correlated_dense` | 14-18 | same correlated covariance |

The latent process has two known orthonormal planar modes and fixed eigenvalues. The simulator generates the latent scores and irregular native observations; the oracle scorer then receives the same known population functions and covariance used to generate those data.

## Qualification guards

The workflow fails if any declared guard is violated. It checks that:

1. every joint conditional score system is solved successfully;
2. each posterior covariance is symmetric and positive semidefinite within numerical tolerance;
3. marginal score-error MSE is broadly consistent with mean reported conditional variance;
4. standardized score errors have approximately zero mean and unit scale;
5. nominal 68% and 95% marginal conditional intervals have broadly compatible empirical coverage;
6. denser native observation reduces mean total conditional variance within each fixed measurement-error regime;
7. both diagonal and correlated measurement-error contracts are exercised;
8. deterministic replay under the same seed is exact;
9. the uncertainty provenance declares that a rank-K covariance reconstruction was not used; and
10. population-estimation, bandwidth-selection, and measurement-error-estimation uncertainty are explicitly excluded.

The numerical acceptance windows are intentionally broad Monte Carlo qualification guards, not inferential confidence intervals or universal performance guarantees.

## First exact-head qualification evidence

The first complete qualification run on PR #170 head `06c0f61dd94a3b008fc223c94ca0bf6fe4a45ce0` passed all guards. GitHub Actions run `37288035380` produced artifact `11334658246`, digest `sha256:2799a46491c43ec702df55b247b39187fb59d066727a53a60d7c32d697c0ae1d`.

Across the eight component-by-scenario calibration cells:

- MSE / mean reported conditional variance ranged from **0.966 to 1.089**;
- standardized-error means ranged from **-0.093 to 0.056**;
- standardized-error standard deviations ranged from **0.975 to 1.045**;
- empirical 68% marginal conditional coverage ranged from **0.660 to 0.704**; and
- empirical 95% marginal conditional coverage ranged from **0.932 to 0.956**.

No joint score system failed in any scenario. Posterior covariance symmetry error was exactly `0.0` throughout, and the smallest retained posterior eigenvalue across all scenarios was approximately `9.58e-05`, so every retained posterior covariance was positive definite in this qualification run.

The information comparison behaved in the expected direction. Mean total conditional variance fell from `0.002157` to `0.000488` when the diagonal-error design moved from 5-7 to 14-18 native observations per curve, and from `0.002352` to `0.000474` under the correlated-error design. Deterministic replay passed for all four scenarios. The artifact also records `rank_k_covariance_used_for_uncertainty=false`, `population_estimation_uncertainty_included=false`, and `bandwidth_uncertainty_included=false` for every scenario.

These are qualification observations for the declared oracle designs, not distribution-free guarantees for arbitrary fitted sparse-MFPCA analyses.

## What this evidence supports

A passing run supports the implementation claim that, when the fitted joint Gaussian population objects are treated as fixed and correctly specified, `sparse_mfpca_score_uncertainty()` reproduces the expected conditional score-covariance behavior for the qualified planar designs.

It also supports the software contracts for joint observation ordering, correlated measurement error, native-time evaluation, deterministic replay, failure retention, and posterior covariance diagnostics.

## What it does not support

This qualification does **not** establish:

- full frequentist coverage after estimating sparse mean/covariance surfaces;
- uncertainty from smoothing-bandwidth selection;
- uncertainty from joint PSD repair;
- uncertainty from estimating or misspecifying the 2x2 measurement-error covariance;
- asynchronous x/y observation grids;
- validity after silently interpolating raw sparse trajectories;
- automatic propagation of score uncertainty into downstream regression or prediction; or
- equivalence to dense-grid projection scores.

Those are separate statistical targets and require separate estimands and qualification programmes.

## Reproducible evidence

The workflow runs:

```text
python scripts/run_sparse_mfpca_score_uncertainty_validation.py \
  --n-curves 500 \
  --output sparse-mfpca-score-uncertainty-validation.json
```

and uploads `sparse-mfpca-score-uncertainty-validation.json` as the `sparse-mfpca-score-uncertainty-validation` artifact. The JSON retains scenario-level calibration summaries, posterior PSD/symmetry diagnostics, information comparisons, measurement-error mode, deterministic-replay status, and the explicit uncertainty-scope flags.
