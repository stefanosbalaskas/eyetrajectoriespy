# Targeted pre-0.12 recovery audit

Stable `0.11.0` provides the known-truth laboratory used here. This audit is
intentionally **short and decision-oriented**: it asks whether an existing
supported contract needs corrective work before a new methodological tranche.
It does not implement the planned 0.12 estimator.

## Four questions

### 1. Sparse FPCA/PACE under signal-dependent observation loss

The validation runner adds observation-process stress in which sample loss
depends on generated signal characteristics. Named mechanisms are:

- `signal_dependent_x_loss`;
- `signal_dependent_y_loss`;
- `eccentricity_dependent_loss`;
- `velocity_dependent_loss`;
- `phase_dependent_loss`;
- an MCAR comparator with the same target loss fraction.

These are **stress mechanisms, not estimator corrections**. The audit records
mean, covariance, marginal subspace, reconstruction, and score-failure
sensitivity. Masked curves remain on native irregular grids; they are not
silently interpolated before sparse FPCA/PACE fitting.

### 2. Joint versus separate planar structure

The audit varies `rho_xy` over `0, 0.3, 0.6, 0.9` using a separable
temporal/channel covariance construction. The crucial control is that the
marginal covariance of `x` and `y` is identical across all four conditions
while only the cross-channel covariance changes.

The current native sparse estimator is fitted separately to `x` and `y`.
Separate marginal recovery is therefore distinguished from first-class
representation of the cross-channel covariance block. The audit records the
fraction of true block-covariance energy contained in the cross-channel blocks.

### 3. Sparse repeated-trial hierarchy

The current functional mixed-effects API is a complete common-grid
`TrajectorySet` model. The audit generates participant/trial hierarchy under
increasingly sparse and unequal native schedules and tests that boundary
directly. Rejection of `IrregularTrajectorySet` input is retained as a
capability boundary; the audit does not interpolate sparse trials to
manufacture compatibility.

### 4. External sensitivity comparison

The audit exports a controlled `rho_xy=0.6` irregular planar fixture in long
form (`ID`, `time`, `value`) for independent implementations.

The primary comparator is [mGSFPCA](https://CRAN.R-project.org/package=mGSFPCA)
version 0.2.2 using `spMultFPCA()`. It is a cross-language sensitivity
reference, not a runtime dependency and not an exact-equivalence oracle.
Rank and basis candidates are fixed explicitly instead of using automatic
AIC/elbow selection.

[MFPCA](https://CRAN.R-project.org/package=MFPCA) and
[bayesFPCA](https://github.com/hruffieux/bayesFPCA) remain secondary
sensitivity references. Bayesian sparse MFPCA is not being introduced as a
core subsystem in this tranche.

Comparator configuration is machine-readable in
`validation/pre012/EXTERNAL_COMPARATORS.json`; the explicit mGSFPCA runner is
`validation/pre012/run_mgsfpca.R`.

## Reproducible outputs

Run:

```bash
python scripts/run_pre012_recovery_audit.py --output-dir pre012-audit
```

The output directory contains:

- `signal_dependent_missingness.csv`;
- `cross_channel_truth.csv`;
- `sparse_hierarchy_boundary.csv`;
- `external_fixture_x.csv` and `external_fixture_y.csv`;
- `external_fixture_truth.json`;
- `pre012_audit_summary.json`.

Then, in an R environment with exactly mGSFPCA 0.2.2 installed:

```bash
Rscript validation/pre012/run_mgsfpca.R pre012-audit
```

## Decision contract

The audit can block new methodology if it uncovers a result-changing or
public-API defect inside an already supported 0.11 contract.

The following findings do not, by themselves, constitute an 0.11 defect:

- sensitivity when observation loss is explicitly informative;
- non-zero cross-channel covariance omitted by separate univariate result objects;
- fail-closed rejection of irregular trials by the complete-grid mixed-effects API.

If no supported-contract defect emerges, the next design study is native sparse
multivariate functional analysis for planar gaze. That study must compare the
two-stage univariate-bases/joint-score-covariance route with a direct block-
covariance operator route before an estimator architecture is frozen.
