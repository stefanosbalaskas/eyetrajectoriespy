---
title: Observation-process diagnostic validation
---

# Observation-process diagnostic validation

This page records the qualification contract for the 1.1 A3 **informative observation-process diagnostics**. The scope is intentionally narrower than a missing-data model: qualification concerns denominator accounting and descriptive diagnostics only.

## Qualified claim

The A3 surface is designed to preserve and describe an explicit candidate-sample retention process. Qualification asks whether it can

- keep candidate/observed/missing accounting exact;
- remain approximately null under known MCAR retention;
- expose contiguous block loss through the supplied schedule/run structure;
- recover the direction and time profile of one known informative candidate-time retention mechanism;
- retain participant grouping without presenting candidate rows as iid inferential units;
- replay deterministically under a fixed seed; and
- preserve the explicit no-imputation/no-correction boundary.

It does **not** qualify a formal MAR/MNAR test, inverse-probability weighting, inverse-intensity weighting, a joint outcome/missingness model, or any modified sparse-FPCA/MFPCA estimator.

## Evidence workflow

The repository workflow is

```text
.github/workflows/observation-process-validation.yml
```

and its deterministic runner is

```text
scripts/run_observation_process_validation.py
```

The workflow uses Python 3.12, installs the development package with its test dependencies, runs three known-truth scenarios, and uploads

```text
observation-process-validation.json
```

as the `observation-process-validation` artifact.

## Simulation truth

Existing functional-simulation truth is reused for the candidate schedule, pre-missing observed values, group/trial metadata, and realized MCAR/block masks. The A3 private simulation layer converts those retained truth objects to the explicit `ObservationProcessData` denominator.

The known informative mechanism is deliberately simulation-only. Starting from a complete functional simulation, candidate time is mapped from the global truth support to

\[
z(t)\in[-1,1],
\]

and retention is generated as

\[
P(R=1\mid t)=\operatorname{logit}^{-1}\{0.8-2.4z(t)\}.
\]

The exact probability for every candidate row is retained in simulation truth. It is used for qualification only and is not passed to the public diagnostic as a measured gaze predictor.

## Scenario 1: MCAR/null behavior

Each candidate sample is independently missing with probability 0.25. Qualification requires

- exact candidate/observed/missing identities;
- realized overall retention close to 0.75;
- candidate-time rank association within a declared near-null tolerance;
- previous-observed-position rank association within a declared near-null tolerance; and
- limited variation in declared time-bin observation fractions.

The purpose is not to prove non-informativeness from a finite null sample. It is to verify that the diagnostic does not manufacture a strong systematic association when the simulator supplies an MCAR process.

## Scenario 2: contiguous block loss

Each curve receives one contiguous missing block covering 30% of its candidate schedule. Qualification compares the supplied truth mask to the per-curve diagnostic run summaries and requires the known missing-run length and contiguity to be recovered exactly.

This checks localization in the schedule/run sense. It does not assume that independently positioned blocks across curves must produce a large global linear-time association.

## Scenario 3: known informative candidate-time retention

The simulation-only logistic mechanism above produces a strong, known decline in retention over candidate time. Qualification requires

- a negative descriptive candidate-time association with the declared minimum magnitude;
- a substantial decline from the first to last declared time bin;
- empirical time-bin retention fractions that remain close to the bin-averaged exact retention probabilities;
- exact participant grouping count; and
- identical masks/probabilities under deterministic replay with the same seed.

This qualifies recovery of **direction/ranking and coarse calibration for this known mechanism**. It does not establish universal power for all informative observation processes.

## Governance assertions

Every scenario additionally asserts that

- the denominator is explicit and exact;
- `p_value` is absent from the association table;
- `iid_sample_level_inference_performed=False`;
- `inverse_probability_weighting_performed=False`;
- `inverse_intensity_correction_performed=False`;
- `current_missing_gaze_imputed=False`; and
- `sparse_estimator_modified=False`.

These assertions are part of the scientific qualification, not merely documentation language.

## Interpreting a pass

A passing workflow supports the claim that A3 provides audited descriptive evidence about the supplied observation process under the qualified scenarios. It does not license statements such as “missingness is MAR,” “missingness is MNAR,” or “the sparse estimator has been corrected for informative sampling.”

Use the [observation-process diagnostics guide](../guides/observation-process-diagnostics.md) for the data contract, history-variable rules, failure semantics, and reporting workflow.
