---
title: Sparse MFPCA observation stress and performance
---

# Sparse MFPCA observation stress and performance

This page closes the final pre-release-candidate evidence gate for the public
native sparse MFPCA estimator. It keeps **observation-process sensitivity** and
**runtime/memory characterization** separate from native known-truth
qualification.

## Observation-process stress

The stress runner reuses the frozen pre-0.12 row-loss mechanisms and applies
them to paired planar observations before fitting the public
`fit_sparse_mfpca()` estimator.

The supported contract remains unchanged: x and y are jointly observed at the
same retained native timestamps. Row deletion can depend on x, y,
eccentricity, velocity, or phase, but it does not create coordinate-specific
missingness.

The deterministic matrix uses rho_xy=0.6, three seeded replicates, and:

```text
none
mcar
signal_dependent_x_loss
signal_dependent_y_loss
eccentricity_dependent_loss
velocity_dependent_loss
phase_dependent_loss
```

Each fit retains the same declared grid, bandwidths, component count,
measurement-error variances, PSD action, and joint-PACE contract used by the
native recovery qualification.

The evidence records actual loss, mean/covariance/Cxy ISE, joint-subspace
cosines, score correlation, reconstruction ISE, score-system failures and
conditioning, and PSD correction.

This is **descriptive stress evidence**:

```text
threshold_gate_applied = false
parameter_selection_performed = false
```

Signal-dependent observation loss can change finite-sample recovery and is not
silently reclassified as an estimator defect. The stress table does not select
bandwidths, ridge, grid size, component count, or public defaults.

## Dedicated sparse-MFPCA performance envelope

A separate runner measures only the public native sparse MFPCA/joint-PACE
pipeline. Synthetic data generation occurs before the timed fit, and every
timing repetition is executed in a fresh Python process with BLAS/OpenMP thread
counts fixed to one.

Three planar workloads are declared:

```text
very_sparse_planar
moderate_planar
irregular_rich_planar
```

For each workload the evidence retains:

- number of curves;
- median native samples per curve;
- ordered off-diagonal covariance-pair count per block;
- total xx/xy/yy latent pair products;
- evaluation-grid size;
- returned component count;
- runtime median, IQR and range over at least three repetitions;
- process peak RSS median/max when available;
- score-failure rate;
- relative joint-PSD correction;
- Python/package/platform/CPU/commit/run provenance.

The envelope is non-comparative and threshold-free:

```text
comparative_benchmark = false
speed_threshold_applied = false
```

It does not claim that eyetrajectoriespy is faster than another package, does
not define a universal workstation runtime, and does not weaken scientific
computation to satisfy a speed target.


## Observed PR evidence

All 21 public-estimator fits in the three-replicate stress matrix completed
successfully, with score-failure rate 0 for every mechanism.

The no-loss baseline had mean ISE about 0.055, joint covariance ISE 0.239,
minimum joint-subspace cosine 0.982, median separated score correlation 0.951,
and reconstruction ISE 0.0216. MCAR at about 20.4% loss remained close to that
baseline: joint covariance ISE 0.272, minimum subspace cosine 0.980, median
score correlation 0.941, and reconstruction ISE 0.0254.

The informative mechanisms were visibly more sensitive in different ways.
Signal-dependent x/y loss increased mean ISE to about 0.328/0.378 and
reconstruction ISE to about 0.070/0.054 while retaining minimum joint-subspace
cosines around 0.975. Eccentricity-dependent loss produced the largest
covariance/reconstruction change in this matrix: joint covariance ISE about
1.45, Cxy ISE about 0.255, and reconstruction ISE about 0.144, while the
minimum joint-subspace cosine remained about 0.964. Velocity- and
phase-dependent loss were closer to the baseline on the principal recovery
metrics. These differences are retained as sensitivity evidence, not
reclassified as estimator defects or used to select tuning parameters.

The dedicated performance run used GitHub-hosted Linux/CPython 3.12 on an
AMD EPYC 9V74 runner with numerical-library thread counts fixed to one. Median
public-fit runtimes over three fresh-process repetitions were approximately
0.51 s for 80 curves with median 8 native samples and a 21-point grid, 1.35 s
for 60 curves with median 14 samples and a 31-point grid, and 2.98 s for 36
curves with median 23.5 samples and a 41-point grid. Peak process RSS medians
were approximately 226, 227 and 229 MiB, respectively. All three workloads had
score-failure rate 0. These values define a recorded environment-specific
performance envelope only; no speed threshold or cross-package claim follows
from them.

## RC interpretation

After this tranche, the 0.12 methodological evidence sequence contains:

1. analytical/operator checks;
2. native known-truth recovery;
3. grid/ridge sensitivity;
4. internal two-stage marginal-basis sensitivity;
5. external mGSFPCA 0.2.2 sensitivity;
6. public-estimator observation-process stress;
7. dedicated sparse-MFPCA runtime/peak-memory characterization;
8. existing documentation, portability, release-readiness, examples and
   cross-platform package CI.

An RC decision should still be made explicitly after reviewing the complete
evidence. This page does not itself change the package version or publish
0.12.
