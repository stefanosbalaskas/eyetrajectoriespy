# RQA software conventions and frozen package contracts

Recurrence-analysis software does not use one universal set of conventions. This page records the external conventions audited for eyetrajectoriespy and freezes the package choices that affect reproducibility.

## Why this matters

Two implementations can analyze the same binary recurrence geometry and still disagree numerically because of choices about the line of identity (LOI), Theiler exclusion, recurrence-rate denominator, ratio scaling, border handling, threshold comparison, normalization, and fixed-recurrence-rate thresholding.

The goal here is not to declare one library "correct." It is to make eyetrajectoriespy's behavior explicit, testable, and stable.

## Audited software

| Software | Relevant observed conventions | Consequence for eyetrajectoriespy |
| --- | --- | --- |
| **pyRQA** | Exposes an explicit `theiler_corrector`, minimum line lengths, fixed-radius neighborhoods, several distance metrics, and OpenCL-oriented large-scale computation. | We retain an explicit Theiler contract and minimum line thresholds, but do not copy backend-specific defaults. |
| **pyunicorn** | Supports fixed threshold, threshold scaled by the signal SD, global fixed recurrence rate, local recurrence rate, optional normalization, and an experimental sparse-RQA path. Its documented RR is the fraction of recurrent cells in the full matrix. The comparison documentation reports no Theiler-window support in the classic RQA path. | We do not normalize internally, we require the analyst to choose fixed radius versus target RR, and we keep Theiler exclusion explicit. |
| **crqa** | Does not exclude the LOI by default; `tw` controls Theiler removal; RR is reported on a 0-100 percentage scale; recurrence points are divided by the full matrix size; normalization/rescaling options are available; the recurrence plot is sparse. | We use 0-1 ratios, exclude the auto-recurrence LOI by construction, adjust the auto RR denominator to eligible off-diagonal pairs outside the Theiler window, and do no hidden normalization/rescaling. |
| **RecurrenceAnalysis.jl** | Defines recurrence with an inclusive `distance <= epsilon` rule and sparse Boolean matrices. For ordinary recurrence matrices the LOI is excluded by default, and RR can be adjusted to the number of potential recurrent points outside the Theiler window; cross-recurrence uses the full matrix denominator. Ratios are reported on 0-1 scale. | This is closest to our chosen RR/LOI convention, but eyetrajectoriespy still records its own denominator, threshold, and alignment rules explicitly. |
| **nolds** | Its Rosenstein `lyap_r` API can estimate lag/minimum temporal separation automatically and offers fit choices such as RANSAC or polynomial fitting plus a fit offset. | eyetrajectoriespy deliberately does not auto-select the embedding lag, temporal separation, or linear fit interval. The divergence curve and declared fit interval remain separate public steps. |

These observations are compatibility notes, not validation by numerical identity. Cross-library comparisons must match all conventions before values are expected to agree.

## Frozen eyetrajectoriespy recurrence contract

### Radius comparison

A pair is recurrent when

```text
distance <= radius
```

not only when `distance < radius`. This is inherited from the exact-radius SciPy KD-tree queries used by the implementation and is protected by regression tests.

### Auto-recurrence LOI and Theiler policy

For `recurrence_matrix()`:

- the LOI is never counted;
- `theiler_window = 0` means only the LOI is excluded;
- a positive Theiler window excludes pairs satisfying `abs(i - j) <= w`;
- the sparse matrix stores both symmetric off-diagonal directions for retained unordered pairs.

The auto-recurrence rate is

```text
number of retained unordered recurrent pairs
------------------------------------------------
number of eligible unordered off-diagonal pairs
outside the declared Theiler window
```

and is returned as a ratio in `[0, 1]`.

### Cross-recurrence policy

`cross_recurrence_matrix()` is the rectangular all-pairs object

```text
CR[i, j] = 1{ d(A[i], B[j]) <= radius }.
```

It does not align, synchronize, lag-shift, resample, or warp either trajectory. Cross-recurrence rate uses the full `n_A * n_B` denominator and is returned on the 0-1 scale.

If clock alignment or a lag-restricted scientific question is required, that operation must be explicit upstream or implemented as a separate, separately named analysis.

### Target recurrence rate

Target-RR mode solves for an inclusive radius. Because empirical distance distributions contain ties, an exact requested RR may be unattainable. The solved radius and achieved RR are therefore always retained; the achieved value, not the requested target, is the realized recurrence density.

No random tie-breaking is used.

### Line metrics and entropy

For `rqa_metrics()` and `cross_rqa_metrics()`:

- `DET` and `LAM` are ratios in `[0, 1]`;
- minimum diagonal and vertical line lengths are explicit parameters;
- diagonal-line entropy is the Shannon entropy of the frequency distribution of **qualifying line lengths**, normalized by the number of qualifying lines;
- finite-matrix border lines are counted at their observed length;
- no border-effect correction or tangential-motion correction is silently applied.

Border truncation can bias line-length distributions and entropy. If a correction is scientifically required, it must be a future explicit method/option with its own tests and provenance rather than a hidden change to the base estimator.

### Sampling-grid policy

Spatial recurrence can be constructed for irregular observations. Classical line-based RQA is only computed on an approximately regular grid, and cross-RQA additionally requires matching sampling steps. No interpolation is performed inside recurrence analysis.

## Multivariate surrogate contract: deferred, not approximated

Version 0.24 supports **scalar IAAFT only**.

Classical IAAFT is a univariate surrogate construction preserving the marginal amplitude distribution exactly and approximating the original Fourier-amplitude spectrum. It must not be described as automatically multivariate.

A future MIAAFT/multivariate-Fourier surrogate implementation for planar gaze must satisfy a stronger contract:

1. operate on the jointly sampled multichannel trajectory, not independently surrogate `x` and `y`;
2. preserve each channel's marginal distribution to the declared tolerance;
3. preserve the declared linear auto- and cross-channel structure (for example cross-spectrum/cross-correlation) to reported tolerances;
4. require a regular common grid unless a distinct irregular-time surrogate method is implemented;
5. state the exact multivariate null hypothesis;
6. return convergence diagnostics for both marginal/spectral and cross-channel constraints;
7. fail if the requested constraints do not converge;
8. be validated against a primary-method/reference implementation before public release.

Until those conditions are met, independently applying scalar IAAFT to gaze axes is intentionally unsupported because it can destroy the cross-channel structure that defines the planar trajectory.

## Performance contract

Recurrence construction is potentially quadratic in the number of samples. Dense allocation is therefore not an implementation detail.

For `N = 18,000` samples, `N^2 = 324,000,000` cells. A dense one-byte Boolean array alone is about 324 MB (309 MiB), while a float64 distance matrix is about 2.59 GB (2.41 GiB). For `N = 36,000`, the corresponding figures are about 1.30 GB (1.21 GiB) and 10.37 GB (9.66 GiB).

eyetrajectoriespy therefore:

- constructs recurrence through KD-tree neighbor search;
- stores recurrence as SciPy CSR;
- never materializes a dense pairwise-distance matrix in the public recurrence path;
- reports achieved recurrence density;
- treats target-RR search as potentially expensive because it repeatedly counts neighbors.

No wall-clock claim belongs in the documentation unless it comes from a retained benchmark record. The repository benchmark harness is `benchmarks/benchmark_recurrence.py`; its output includes sample count, state dimension, radius policy, achieved RR, elapsed time, sparse nonzero count, and CSR array bytes.

## Primary references for the frozen choices

- Marwan, N., Romano, M. C., Thiel, M., & Kurths, J. (2007). *Recurrence plots for the analysis of complex systems*. Physics Reports, 438, 237-329. https://doi.org/10.1016/j.physrep.2006.11.001
- Kraemer, K.-H., & Marwan, N. (2019). *Border effect corrections for diagonal line based recurrence quantification analysis measures*. Physics Letters A, 383, 125977. https://doi.org/10.1016/j.physleta.2019.125977
- Prichard, D., & Theiler, J. (1994). *Generating surrogate data for time series with several simultaneously measured variables*. Physical Review Letters, 73, 951. https://doi.org/10.1103/PhysRevLett.73.951
- Schreiber, T., & Schmitz, A. (1996). *Improved surrogate data for nonlinearity tests*. Physical Review Letters, 77, 635-638. https://doi.org/10.1103/PhysRevLett.77.635
- Schreiber, T., & Schmitz, A. (2000). *Surrogate time series*. Physica D, 142, 346-382. https://doi.org/10.1016/S0167-2789(00)00043-9
