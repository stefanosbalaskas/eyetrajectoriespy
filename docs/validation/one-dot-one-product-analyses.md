# 1.1 canonical end-to-end product analyses

R3 is an **integration and usability** tranche for the completed 1.1 sparse/irregular surface. It is not another estimator benchmark and it does not reuse the known-truth qualification simulators as its product-use evidence.

The canonical harness is:

```text
python scripts/run_one_dot_one_product_analyses.py \
  --output-dir build/one-dot-one-product-analyses
```

The harness generates deterministic realistic synthetic eye-tracking fixtures inside the script. They are explicitly **not empirical human observations**. The generated data are designed around typical sparse/irregular gaze structure, repeated trials, candidate-sample retention, paired planar samples, and coordinate-specific asynchronous sampling rather than around method-qualification thresholds.

## What R3 tests

R3 asks a product question: can a scientist conduct coherent analyses from supported user-facing imports to interpretable tables and manuscript-ready reporting without private helpers or repository-specific knowledge?

Three routes are exercised.

### Univariate sparse/irregular route

The route retains an explicit candidate-sample denominator and runs:

1. `observation_process_data()` and `diagnose_observation_process()` with participant grouping, design predictors, time dependence, and past-observed-gaze history diagnostics;
2. group-aware `select_sparse_fpca_bandwidths()` over declared mean/covariance candidates;
3. stable `fit_sparse_fpca()` / native PACE with the selected numeric bandwidths passed explicitly;
4. `sparse_fpca_score_uncertainty()` conditional on the fitted sparse population objects;
5. `sparse_fpca_partial_trajectory_prediction()` for a new partially observed target trajectory; and
6. participant-aware split-conformal calibration with `calibrate_sparse_fpca_partial_prediction_conformal()` and `sparse_fpca_conformal_prediction_band()`.

Proper-training, calibration and target participants are disjoint. The conformal future grid uses three declared acquisition-anchor timestamps with actual retained responses. No response interpolation is used to satisfy the calibration contract.

### Paired and asynchronous planar route

The paired route uses native sparse x/y observations at common timestamps, performs audited `select_sparse_mfpca_bandwidths()`, fits `fit_sparse_mfpca()` / joint PACE and then computes conditional joint-score uncertainty.

A second fixture uses the asynchronous representation expected by `fit_sparse_mfpca_async()`: each curve is stored on the **exact union of native x and y timestamps**, with `NaN` only in the coordinate that was not observed at that timestamp. This route performs no nearest-neighbour synchronization, interpolation or time binning.

R3 intentionally does **not** treat the paired bandwidth selector as validation for the asynchronous observation contract. The asynchronous fit therefore uses explicitly declared manual bandwidths; the absence of a separately qualified asynchronous selector is retained in the friction ledger.

### Repeated-trial sparse route

The multilevel fixture contains 16 participants and 34 irregular trials with unequal trial counts. Twelve participants contribute repeated trials and four contribute one trial each. The route fits `fit_sparse_multilevel_fpca()` and retains:

- participant and trial score tables;
- participant-level BLUP diagnostics;
- separate between/within PSD diagnostics;
- support/pair-count diagnostics; and
- `sparse_multilevel_fpca_reporting_text()`.

The synthetic fixture contains no task/visit fixed functional effect, matching the current model boundary. Applied users must still stratify or remove such effects upstream when scientifically required.

## First successful branch execution

The first complete branch execution used source commit
`5b2939b76f4c2112acbed415c7b40f0c37a72b15` with package identity
`1.1.0.dev0` on Ubuntu 24.04 / Python 3.12.14.

- workflow run: `37437196381`;
- workflow job: `112181805264`;
- artifact: `one-dot-one-product-analyses`, ID `11399602744`;
- artifact files: 51;
- artifact size: 102,535 bytes;
- artifact digest: `sha256:c44b69dc79fbce575ce4c325543afae0cccac9576f781dd753016374fe80c9a1`;
- harness wall-clock time: 30.53 s;
- process max RSS on the Linux runner: 242,672 KiB;
- release-blocking friction items: 0.

The machine-readable frozen snapshot is `ONE_DOT_ONE_PRODUCT_ANALYSES.json`. CI also uploads the complete generated tables, reporting text, input fixtures, environment record and friction ledger on each R3 workflow run.

## Observed product results

### Univariate route

The candidate denominator had a 14.36% missing fraction. Twenty participants formed the proper-training set, ten formed the participant-level conformal calibration set, and a disjoint participant supplied the target curve.

The audited selector chose mean bandwidth `0.36` and covariance bandwidth `0.42`. Native PACE returned zero retained score-system failures, and conditional score uncertainty returned zero failures. Participant-aware conformal calibration used ten independent participant units. Raw sparse observations were never interpolated.

### Planar route

The paired selector chose mean bandwidth `0.36` and covariance bandwidth `0.44`; paired joint PACE returned zero score-system failures and the conditional joint-score uncertainty route completed without retained failures.

The asynchronous fixture contained 259 x-only timestamp rows and 270 y-only timestamp rows in addition to simultaneous rows. Asynchronous joint PACE returned zero score-system failures. The retained provenance records no raw interpolation, nearest-neighbour synchronization or time binning.

### Repeated-trial route

All 16 participants and all 34 trials were retained. Four single-trial participants remained in the analysis after population identifiability was established by the repeated participants. The joint hierarchical BLUP stage returned zero failed participant systems.

## Product-friction ledger

R3 found no release-blocking usability defect. The retained lower-severity observations are still useful for documentation and future design:

| Route | Severity | Observation |
| --- | --- | --- |
| Univariate | low | Bandwidth selection and fitting are intentionally separate, so the selected numeric values must be transferred explicitly. |
| Univariate | low | Conformal calibration requires actual retained observations at every declared future-grid timestamp; R3 uses declared acquisition anchors rather than interpolation. |
| Univariate | low | Score-uncertainty estimation and reporting are split across companion supported modules. |
| Planar | low | Paired bandwidth selection and fitting remain explicitly separate. |
| Planar | moderate | No separately qualified asynchronous bandwidth selector exists; asynchronous bandwidths remain analyst-declared. |
| Planar | low | Users must choose paired versus asynchronous observation contracts explicitly. |
| Multilevel | moderate | The sparse multilevel route has no dedicated bandwidth selector; mean/total/between bandwidths remain analyst inputs. |
| Multilevel | low | Score tables are tidy, while covariance/support diagnostics are mappings that R3 exports directly to JSON. |
| Multilevel | low | Fixed functional effects remain outside the first sparse multilevel model and must be handled upstream. |

These are product observations, not reasons to silently change scientific defaults. R3 therefore adds no estimator and no automatic convenience behavior.

## Interpretation boundary

Passing R3 supports the claim that the completed 1.1 module-scoped sparse/irregular capabilities can be composed coherently from supported APIs into reportable analyses. It does **not** establish empirical generalizability, estimator optimality, real-data validity for a particular device or task, or release-candidate eligibility by itself.

Release-candidate eligibility is decided only after the separate R4 full prerelease qualification/audit tranche.
