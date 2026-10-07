---
title: Bayesian FPCA B2 replication
---

# Bayesian FPCA B2 replication and tuning sensitivity

B2 follows the single-realization B1 external-comparator study with a
predeclared replicated recovery programme. It remains **evidence only**:
no estimator, public API, dependency, scientific default, release version,
or publication-readiness state is changed.

## Why B2 exists

B1 showed a large recovery contrast on five known-truth fixtures, but those
fixtures used one realization per condition, smooth rank-2 Gaussian truth,
fixed native bandwidths, and a fixed external spline-basis size. B2 asks
whether that contrast persists across repeated datasets, separated stress
factors, a non-harmonic truth family, and predeclared tuning sensitivity.

B2 does not test or assert intrinsic architectural superiority. The B4
decision in issue #205 remains deferred.

## Frozen primary design

The design was recorded on issue #205 before any B2 run.

- 16 deterministic replicates per scenario;
- rank 2 throughout;
- Gaussian measurement-noise SD 0.05 per observed coordinate;
- fixed native bandwidths retained as the primary B1-compatible baseline;
- external `bayesFPCA` pinned to exact upstream commit
  `f05b0615632cffe5c63838858d9a956af6588a73`;
- no truth quantity enters estimator tuning.

| Scenario | Purpose | N | Samples | Spectrum | Native mean/cov BW |
|---|---|---:|---:|---|---|
| `univariate_moderate` | ordinary sparse irregular recovery | 32 | 12-18 | (1.00, 0.40) | (0.20, 0.30) |
| `univariate_extreme_sparse` | extreme within-curve sparsity | 32 | 6-9 | (1.00, 0.40) | (0.28, 0.38) |
| `univariate_low_n` | low participant count only | 14 | 12-18 | (1.00, 0.40) | (0.22, 0.32) |
| `univariate_near_tied` | near-tied retained spectrum only | 32 | 12-18 | (1.00, 0.90) | (0.20, 0.30) |
| `univariate_localized` | non-sinusoidal localized triangular truth | 32 | 12-18 | (1.00, 0.40) | (0.18, 0.28) |
| `univariate_informative_time` | logistic candidate-time retention sensitivity | 32 | 31 candidates | (1.00, 0.40) | (0.20, 0.30) |
| `planar_paired` | paired sparse x/y recovery | 28 | 12-18 | (1.10, 0.55) | (0.22, 0.32) |
| `planar_async` | coordinate-specific asynchronous x/y recovery | 28 | 8-12 per coordinate | (1.10, 0.55) | (0.25, 0.36) |

The low-N and near-tied conditions are intentionally separated. The localized
truth uses two disjoint triangular modes rather than a Fourier/sinusoidal
basis, reducing dependence of the conclusion on the B1 truth family.

## Informative observation-time sensitivity

`univariate_informative_time` starts from a fixed 31-point candidate grid and
retains candidate times stochastically under a predeclared logistic function
of time. It is explicitly a **sensitivity scenario**, not an estimator-defect
test and not a formal MAR/MNAR classification.

No inverse-probability or inverse-intensity correction is introduced in B2.

## Asynchronous planar contract

The planar asynchronous scenario preserves coordinate-specific native x and y
time grids. The neutral external fixture exports those grids separately.
There is no raw interpolation, nearest-neighbour synchronization, or time
binning.

## Secondary fairness/tuning analysis

The first four replicates of five predeclared stress scenarios receive a
secondary tuning sensitivity:

- `univariate_extreme_sparse`;
- `univariate_low_n`;
- `univariate_near_tied`;
- `univariate_localized`; and
- `planar_paired`.

For the native estimator, the candidate grid is the Cartesian product of the
frozen mean and covariance bandwidths multiplied by `{0.75, 1.00, 1.25}`.
The existing audited held-out Gaussian predictive criterion is used with
three-fold curve-level cross-validation. Measurement-error variance remains
fixed at its known simulation value and is not tuned.

For `bayesFPCA`, K is restricted to `{5, 6, 7, 8, 9}`. Successful fits are
ranked by final ELBO and the largest final ELBO is selected, with lower K as
the deterministic tie-break. Truth recovery metrics are not used for K
selection.

The fixed B1-compatible routes remain the primary comparison. The selected
routes are secondary sensitivity evidence only.

## Replicated outcomes

Each successful fit is evaluated against known truth using the same invariant
B1 targets:

- integrated mean error;
- latent-trajectory reconstruction ISE;
- minimum functional-subspace principal cosine;
- minimum score-subspace principal cosine;
- retained-spectrum/PVE L1 error; and
- score failure rate.

Estimator/fit failures are retained as outcomes rather than causing the entire
Monte Carlo programme to abort. Across replicates, B2 reports mean/SD,
median/IQR, paired method differences, and descriptive favorable-direction
fractions.

No p-values, superiority labels, post-hoc qualification thresholds, automatic
architecture winners, or automatic API-promotion decisions are produced.

## B3 handoff

Native conditional PACE/joint-PACE score-covariance objects and external
variational score-covariance objects are retained where available, but B2
does not compare their magnitudes or treat them as equivalent estimands.
They are retained solely to support the subsequent B3 calibration tranche.

B3 will evaluate uncertainty against the quantity each object actually claims
to cover over repeated known-truth datasets. B4 remains deferred until those
coverage results are retained and reviewed.

## Reproducibility

The dedicated `bayesian-fpca-replication` workflow retains the complete B2
evidence directory for 90 days. The external comparator remains isolated from
the MIT Python package and is installed from the exact pinned upstream Git
commit. The artifact also retains exact R package versions, `sessionInfo()`,
`R.version.string`, `extSoftVersion()`, system/runtime details, and SHA256
checksums for every retained evidence file.
