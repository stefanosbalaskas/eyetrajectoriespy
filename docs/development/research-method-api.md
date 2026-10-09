# Research method contracts — experimental, opt-in

!!! warning "Do not confuse research functions with production inference"
    These APIs exist only in the development **eyetrajectoriespy.research** namespace; stable 1.1.0 cannot import them. A passing CI job does not establish type-I calibration.

## Existing F1–F6 methods

**F1: test_sparse_functional_groups()** estimates joint pooled PACE scores and performs conditional whole-unit label permutation. Repeated curves from the same participant cannot be split across independent units. It does not implement Koner and Luo's test; null size, power and heteroscedasticity remain unqualified.

**F2: summarize_gaze_validation_targets()** calculates descriptive Euclidean planar error against independently documented targets, within-target RMS precision and validation sample loss, in declared degrees. **link_gaze_validation_sessions()** links explicit participant, device and session identifiers; it never asserts calibration recency or drift absence.

**F3: from_bids_eyetracking()** imports a single eye recording under a narrow BIDS 1.11.2 convention, preserving device timestamps (s or ms), missingness and data provenance without resampling or clock synchronization. **audit_bids_eyetracking_dataset()** checks multi-file eye labels, sidecars and required screen-presentation fields; neither is the official bids-validator.

**F4: compare_aoi_functional_geometries_holdout()** contrasts ALR-FPCA against post-hoc simplex projection with disjoint participants; not the constrained AOI eigenfunction estimator.

**F5: detect_ordered_functional_changepoint()** scans whole-function mean differences across trial order. Independent and weak-block bootstrap p-values are experimental and require validation under serial dependence.

**F6: fit_weighted_mfpca()** explicitly transforms channels by their declared square-root weights. It does not learn optimal weights or support incomplete sparse observations.

## New D4 design methods

**simulate_functional_study_power(units_per_group, n_replicates, ...)** uses fresh native irregular x/y observations and actually refits experimental F1 under both null and alternative. All failed fits are retained, rejected rates are conditional on success and the result explicitly sets **scientifically_qualified=False** and **recommended_sample_size=None**. It is **not fPASS theory**.

**fit_functional_reliability(trajectories, participant_column, condition_column)** requires balanced repeated trials, matched common time grids, finite values and at least three independent participants. Between variance is max(0, (MS_between−MS_within)/m); within is MS_within. The reliability for mean of m trials is between/(between+within/m); truncation and zero-denominator NaNs are disclosed.

**compare_repeated_functional_groups(trajectories, participants, conditions, sign_symmetry_assumed=True, ...)** averages within each participant-condition then runs sign flips of independent participant-paired difference curves using an integrated L2 norm statistic. Requires complete paired conditions, balanced replicates and symmetric subject differences under the null. Period/order and carryover are not modelled, so p-values remain experimental.

[Evidence matrix](research-evidence-matrix.md) · [Case studies](research-case-studies.md)
