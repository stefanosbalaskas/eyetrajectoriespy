# F1–F6 experimental expansion: methods and qualification boundaries

> These implementations are exploratory research modules under `eyetrajectoriespy.research`, **not stable 1.2 or release-candidate APIs**. Published stable remains **1.1.0**; main development remains **1.2.0rc2.dev0**. Neither GitHub nor PyPI publication is authorized.

All six directions requested for the 1.2 programme are represented in the opt-in research namespace. They require **independent scientific qualification**, beyond passing these initial engineering contract tests, before migration to any stable public module. The existing 10 workflow contracts and prior RC1 evidence are not changed.

## F1 — Sparse two-sample functional inference

- `test_sparse_functional_groups()`, `functional_group_contrast_frame()`, `plot_functional_group_contrast()`.
- Current experimental algorithm: fit a **pooled** planar sparse MFPCA/PACE model without labels, aggregate scores at declared independent-unit level, compare joint mean scores and conditionally permute complete independent units. It returns a global provisional Monte Carlo p-value and a descriptive reconstructed contrast. Both x/y coordinates enter the joint fit; no channel-wise multiple testing.
- **Not an implementation of Koner and Luo (2024)**. It does not inherit that paper's finite-sample properties. Exchangeability of whole independent units and a common null score distribution are assumptions, not tested facts. There is no repeated-measures within-unit treatment crossover support, covariate adjustment, heteroscedastic calibration, or inferential component-selection correction. Reject designs that violate supported grouping or have unscorable curves.
- The isolated F1 conditional randomization kernel has a seeded null/alternative Monte Carlo pilot (`scripts/run_research_f1_f5_pilot.py`) that does **not** refit sparse MFPCA per replicate; it cannot validate the full inferential pipeline. CI retains reproducible source-generated evidence and sha256 digest.\n- Required before promotion: systematic null type-I error simulation (multiple alpha levels, imbalanced groups, dependence/heteroscedasticity), power profiles under joint/coordinate effects, support sensitivity, measured-versus-nominal size, uncertainty for group contrasts, independent comparison and performance qualification. Do not claim valid p-values for nonexchangeable groups.

## F2 — Measured gaze quality provenance

- `audit_gaze_measurement_quality()`, `measurement_quality_reporting_frame()`.
- Distinguishes externally measured accuracy/precision and observed missing-coordinate support. Without calibration/validation records, measurement quality is **not available**; it cannot be reverse-engineered from observed gaze alone.
- Participant identifiers and source evidence are mandatory for supplied calibration records. Match calibration session/device/target provenance in subsequent iterations. Not a vendor-specific QC replacement.

## F3 — Eye-Tracking-BIDS subset adapter

- `validate_eyetracking_metadata()`, `from_bids_eyetracking()`.
- A narrow **BEP020-inspired subset**, not complete BIDS compliance: accepts a single continuously sampled physio TSV.GZ and explicit JSON sidecar, with time, x/y column definitions, units, one recorded eye, positive sampling rate and finite origin. It preserves NaNs and rejects nonuniform timestamps.
- Enforces mandatory per-eye `recording-` identity, a matching JSON sidecar filename, explicitly marked `n/a` missing coordinates, and rejects corrupted nonnumeric values; this is checked against the published BEP020 descriptions and MNE-BIDS's single-eye export approach.\n- No asynchronous clock reconciliation, device event inference, binocular fusion, hidden resampling or claim that all BIDS entities are validated. A pinned published standard conformance fixture and validator integration are mandatory before claiming compatibility across datasets.
- Relevant BIDS preprint is a specification discussion, not itself evidence that this limited adapter passes the BIDS validator.

## F4 — Constrained AOI geometry feasibility

- `project_simplex()`, `compare_aoi_functional_geometries()`.
- Comparison: existing qualified ALR-FPCA against a deliberately elementary alternative (raw-coordinate FPCA followed by Euclidean projection onto the simplex). Reports reconstruction error and zero counts, preserving simplex-valid reconstructed values.
- `compare_aoi_functional_geometries_holdout()` fits both candidate bases on training participants only and compares projection-based reconstruction on disjoint held-out participants, with explicit leakage guards. This is **not** prospective trajectory prediction, since the holdout gaze series is observed to obtain component scores.\n- **Not the Kwan et al. constrained eigenfunction estimator.** Production promotion would require implementing and independently qualifying the actual constrained geometry, holdout rather than only in-sample reconstruction, structural/rounded zero scenarios, support and reference-AOI sensitivity, known-truth recovery and interpretability assessment.

## F5 — Change points across ordered whole curves

- `detect_ordered_functional_changepoint()`.
- Implements a whole-function L2 mean CUSUM scan. Analyst explicitly declares independence for curve permutation or weak dependence with a selected circular block length. The p-value is marked **experimental**.
- The seeded F5 pilot separately records observed null rejection and alternative detection in independent and weakly dependent whole-curve processes, without interpreting 100 replications as certification. Repeated-participant trajectories are rejected under the independent-curve resampling option.\n- Not within-trial saccade/blink detection. Not the robust U-statistic of Wegner and Wendler (2024). Block bootstrap validity, stationarity, dependence robustness, multiple changes and effect-region interpretation all remain **unqualified**. Resampling participants across repeated trials without modelling hierarchy must not be treated as valid.

## F6 — Weighted multivariate functional geometry

- `fit_weighted_mfpca()`, `reconstruct_weighted_mfpca()`, `weighted_component_geometry()`.
- Uses a diagonal weighted L2 isometry: multiply each channel by the square root of its **declared positive** weight, fit existing common-grid MFPCA with no auto-scaling and invert on reconstruction. No learned optimal weights, and no sparse route.
- Unit tests now cover weighted quadrature orthogonality and declared inverse-unit transformations. Qualify weighted orthogonality, inverse reconstruction, unit equivalence, sensitivity to weights, original-channel scale, and time-domain quadrature; distinguish weights chosen for scientific importance from inferred measurement reliability.

## Mandatory scientific references

- Koner, S. & Luo, S. (2024). *Biostatistics* 25, 1156–1177. https://doi.org/10.1093/biostatistics/kxae004
- Niehorster, D. C. et al. (2026). *Behavior Research Methods*. https://doi.org/10.3758/s13428-026-03039-4
- Dunn, M. J. et al. (2024). *Behavior Research Methods* 56, 4351–4357. https://doi.org/10.3758/s13428-023-02187-1
- Szinte, M. et al. (2026). Eye-Tracking-BIDS, bioRxiv preprint. https://doi.org/10.64898/2026.02.03.703514
- Kwan, B. et al. (2024). *Statistics in Biosciences* 16, 578–603. https://doi.org/10.1007/s12561-023-09399-1
- Wegner, L. & Wendler, M. (2024). *Statistical Papers* 65, 4767–4810. https://doi.org/10.1007/s00362-024-01577-7
- Happ, C. & Greven, S. (2018). *JASA* 113, 649–659. https://doi.org/10.1080/01621459.2016.1273115

## Release governance

This scientific expansion intentionally reopens the freeze stated in [#225](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/225). **Do not** promote source to literal 1.2.0rc2 before the F1–F6 scope is separately reviewed, each scientifically warranted method qualified, old estimator contracts regressed, and fresh exact-version release evidence generated. Previously qualified literal 1.2.0rc1 ledgers remain immutable. Track the expanded programme under [#226](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/226).
