# Sparse-MFPCA bandwidth-selection qualification

This page documents the deterministic known-truth qualification for the 1.1 development capability `select_sparse_mfpca_bandwidths()`.

## What is being qualified?

The selector is an **opt-in audit layer** for the native synchronous sparse planar MFPCA estimator. It tunes only the declared mean and latent-covariance smoothing bandwidths. It does not change `fit_sparse_mfpca()` defaults and does not apply selected values automatically.

For each training fold and candidate bandwidth pair, the selector refits the native planar population mean and full latent covariance blocks from training curves only. A held-out curve with $m_i$ paired native observations is evaluated under

$$
\mathbf\Sigma_i
=\widehat{\mathbf C}_i^{TM}
+I_{m_i}\otimes\mathbf R_\epsilon,
$$

where $\widehat{\mathbf C}_i^{TM}$ is the **full fitted joint covariance** evaluated at the held-out native timestamps in `time_major_interleaved_xy` order and $\mathbf R_\epsilon$ is the analyst-declared 2x2 measurement-error covariance.

The held-out criterion is the Gaussian negative log predictive density per scalar planar observation,

$$
L_i
=\frac{1}{2(2m_i)}
\left[
\log|\mathbf\Sigma_i|
+\mathbf r_i^\top\mathbf\Sigma_i^{-1}\mathbf r_i
+2m_i\log(2\pi)
\right],
$$

where $\mathbf r_i$ is the interleaved held-out residual vector. Fold loss is the equal-weight mean of $L_i$ across held-out curves; candidate loss is the mean across valid folds.

The calculation uses stable linear solves and the full fitted covariance. It does **not** use a rank-K covariance reconstruction, PACE score loss, validation-curve score fitting, or score ridge in the predictive covariance.

## Resampling and leakage contract

The qualified selector supports curve-level or group-level resampling. For group resampling, all curves sharing the declared metadata group remain in the same fold. Training-fold population surfaces are fitted without held-out observations, and the fixed declared measurement-error covariance is not re-estimated or tuned from validation data.

Failed candidate/fold evaluations remain in the audit tables. `min_valid_folds` controls candidate eligibility. If no candidate is eligible, the selector returns the explicit `no_eligible_candidate` state rather than silently falling back to another rule.

## Candidate and selection contract

Candidate grids are sorted and deduplicated before a deterministic Cartesian product is created. The primary rule is the exact minimum eligible mean fold loss. Exact ties are resolved deterministically by preferring the larger mean bandwidth, then the larger covariance bandwidth, then the candidate ID.

No 1-SE rule is implemented because this first two-bandwidth selector has no predeclared scalar simplicity ordering for the bandwidth tuple. The software therefore does not invent one after seeing the data.

## Known-truth qualification design

The dedicated `sparse-mfpca-bandwidth-selection-validation` workflow uses the native functional simulator and two deterministic planar scenarios:

| Scenario | Curves | Resampling | Measurement error |
| --- | ---: | --- | --- |
| `diagonal_curve_cv` | 24 | 3-fold curve CV | diagonal 2x2 covariance |
| `correlated_repeated_trial_group_cv` | 48 (24 participants × 2 trials) | 3-fold `participant_id` group CV | correlated positive-definite 2x2 covariance |

Both scenarios use the same predeclared candidate grid:

- mean bandwidths: `1e-6`, `0.18`, `0.50`;
- covariance bandwidths: `0.25`, `0.60`.

The `1e-6` mean bandwidth is deliberately pathological and is expected to expose insufficient local support rather than be silently discarded. The `(0.50, 0.60)` pair is the predeclared oversmoothing edge. These edges are diagnostic controls; the qualification does not define a population-optimal or "true" smoothing bandwidth.

## Qualification guards

The workflow fails unless all of the following hold:

1. fold/candidate evidence replays deterministically under the fixed simulation and CV seeds;
2. the selected candidate is eligible and is the exact argmin under the declared criterion and tie-break;
3. pathological undersmoothing failures remain visible in the audit evidence;
4. the selected loss does not exceed the eligible predeclared oversmoothing edge;
5. repeated trials from the same participant stay in one group-CV fold;
6. diagonal and correlated measurement-error contracts are both exercised;
7. the full fitted joint covariance is used for validation;
8. PACE score fitting/loss and rank-K covariance reconstruction are absent from the selection criterion;
9. measurement error, rank, score ridge, evaluation grid, PSD policy, and support policy are not tuned; and
10. explicitly passing selected values to a later `fit_sparse_mfpca()` leaves the fitter's `automatic_bandwidth_selection_performed` provenance flag false.

## First qualification evidence

The first complete run on PR #173 head `2400316b0e13fe1728e5a2af89d8f61457435b74` passed all guards. GitHub Actions run `37291648497` produced artifact `11337470067`, digest `sha256:3b7bf6ae4bb32dfc0cfde0071dd463a0901d040cf85ce8d432fd3688d8569880`.

### Diagonal measurement error / curve CV

- 6 declared candidates;
- 4 eligible candidates;
- 6 retained candidate-fold failures, all from the pathological `mean_bandwidth=1e-6` edge;
- selected `candidate_0004`: mean bandwidth `0.50`, covariance bandwidth `0.25`;
- selected mean held-out loss: `2.3666524073`;
- predeclared oversmoothing edge `(0.50, 0.60)` remained eligible with mean loss `5.2494893391`;
- deterministic replay passed;
- the explicit downstream `fit_sparse_mfpca()` remained nonautomatic.

### Correlated measurement error / repeated-trial participant CV

- 48 curves from 24 participants with two trials each;
- 6 declared candidates;
- 4 eligible candidates;
- 6 retained candidate-fold failures, again from the pathological `mean_bandwidth=1e-6` edge;
- selected `candidate_0004`: mean bandwidth `0.50`, covariance bandwidth `0.25`;
- selected mean held-out loss: `0.1890502843`;
- predeclared oversmoothing edge `(0.50, 0.60)` remained eligible with mean loss `5.8467340905`;
- every participant's repeated trials stayed in a single fold;
- deterministic replay passed;
- the explicit downstream `fit_sparse_mfpca()` remained nonautomatic.

In both scenarios the artifact records `measurement_error_tuned=false`, `joint_pace_scoring_performed=false`, `rank_k_covariance_used_for_validation=false`, and `unique_true_bandwidth_recovery_claimed=false`.

## What this evidence supports

The qualification supports the software and scientific-contract claim that `select_sparse_mfpca_bandwidths()` performs auditable, leakage-aware training-fold selection over declared mean/covariance bandwidth grids using the full native planar predictive covariance and fixed measurement-error specification. It also supports deterministic failure retention, group-CV isolation, exact argmin selection, and explicit downstream application of the selected values.

## What it does not support

This evidence does **not** establish that predictive likelihood uniquely identifies a population-optimal smoothing bandwidth. It does not prove recovery of an unknown "true" bandwidth, separate latent from measurement-error covariance without the declared error model, tune component rank or score regularization, qualify asynchronous x/y grids, or propagate bandwidth-selection uncertainty into downstream inference.

Those are separate targets and require separate estimands and validation programmes.

## Reproducible evidence

The workflow runs:

```text
python scripts/run_sparse_mfpca_bandwidth_selection_validation.py \
  --n-participants 24 \
  --output sparse-mfpca-bandwidth-selection-validation.json
```

and uploads the JSON as the `sparse-mfpca-bandwidth-selection-validation` artifact. The artifact retains the candidate grid, selection and loss summaries, failed-fold counts, resampling/error modes, group-leakage status, deterministic replay, full-covariance/no-score-loss flags, and downstream explicit-fit status.
