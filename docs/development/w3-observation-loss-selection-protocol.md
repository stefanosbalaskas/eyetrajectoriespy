# W3 R4: observation loss, complete-unit selection and native irregular timing

!!! danger "Missing-data research protocol — not a missingness correction"
    The completed W3 inference studies concern finite complete common-grid
    trajectories, not the validity of deleting or interpolating incomplete
    gaze. This new R4 study investigates what happens if an analyst
    **explicitly excludes incomplete source units**, rather than silently
    manipulating data inside a workflow. It does not identify an MNAR
    mechanism from observations or validate a correction.

## Prespecified science and source

There are **96 fresh independently seeded generating blocks per source
design**, independent curves (72 units) and independent participants
(48 participants × three repeated trials). Both source designs have
31 time locations, two gaze dimensions, known intercept/condition
slope functions and source-level smooth participant heterogeneity.
Seed family `202610124217` is distinct from previous W3 datasets.

Each block generates the **complete source once** and compares two
*paired* recording-loss scenarios using the **same original complete
trajectories, conditions and uniform loss draws**:

| Scenario | Recording-loss assignment | Interpretive limit |
|---|---|---|
| MCAR | Each independent unit has loss probability 0.35, independent of latent responses and predictors | Known simulation-only MCAR mechanism |
| Latent response-dependent | Unit recording loss depends on its condition and the latent midpoint residual, which is not available after the gap | Explicit generative MNAR-style mechanism, **not** inferred from data |

The outcome-dependent missingness log-odds equal
`-0.65 + 1.35*x + 2.9*(latent_midpoint_residual/0.10)`.
This generating specification is prespecified and not tuned in
response to observed results. It may generate varying loss rates,
selection bias or both; scientific findings will be reported without
a desired-significance or target-effect gate.

A selected unit receives a contiguous **8-location mid-trial
recording gap**, across two dimensions. In the participant design
the gap is imposed on **one** of the three source trials. The
original complete data remain immutable.

## Three separate representations/analyses

1. **Original complete-data known-truth fit:** W3 observes all source
   trajectories. This is a numerical reference only, not what real
   researchers have when recording was lost.
2. **Gapped common-grid `TrajectorySet` and native irregular
   `IrregularTrajectorySet`:** the W3 complete-grid workflow must
   fail closed and retain all source curves. Advisory experimental
   `workflow_preflight` should report the missing-value count and
   curve hierarchy without performing interpolation or exclusions.
   Native irregular recordings retain their original observed
   timestamps—no synthetic common-grid conversion.
3. **Explicit complete-unit sensitivity fit:** the analyst's deliberate
   complete-case decision excludes *entire independent participants*
   (all three source curves) if one source trial has a gap; for
   independent-curve data it excludes the affected curve. The
   resulting finite `TrajectorySet` is fitted with the unchanged
   complete-grid W3 method and checked against an independent
   NumPy least-squares calculation. This is **not** presented as a
   statistically valid or generally recommended solution.

## Prespecified scientific outcomes and failure accounting

96 independently generated block indices **per design** yield
2 paired missingness mechanisms × 2 source designs = **384 attempted
mechanism-fit cases**, not 384 independent datasets. The participant
units, curves and time cells are not independent Monte Carlo replications.

Every source case records the original/retained inference units,
source curves, lost units, fraction of masked values, source and
explicit-complete-case slope RMSE, signed x-dimension midpoint slope
error, complete-case minus full-fit slope difference, independent
OLS-reference discrepancies and both fail-closed guard observations.

Source-level summaries retain all attempted and completed denominators
and use **2000 independent-block bootstrap resamples** for Monte Carlo
uncertainty of mean errors/selection changes. They do not calculate
a p-value from source trajectories or from 31 correlated time cells.

The source run must preserve original `case-ledger.json`,
`evidence.json`, original scientific `source-selection-errors.svg`,
workflow-recorded source SHA and SHA256 checksums, including failures.
All 384 planned case evaluations and oracle checks must be present
before interpreting aggregate results; success of engineering CI
does not require any favored bias or recovery direction.

## Scope boundaries

The contrast is about **measurement loss and naive selection
sensitivity**, not calibrated inference for sparse/irregular
functional regression, missingness weighting, multiple imputation,
latent state modelling or propensity identification. In real data,
the missing midpoint signal is not available to fit a missingness
model; its availability here derives solely from prespecified
simulation known truth. Participants with a missing trial do not
inherently need to be excluded; that deletion is an *explicit
sensitivity scenario* used to understand a common but potentially
problematic analytical choice.

The W3 workflow's new fail-closed data-integrity behavior was
introduced separately in [core development PR #294](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/294).
The [original fixed-HC1 simultaneous coverage limitation #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
also remains open. Neither scientific issue is fixed by
selecting complete cases.

## Exact reproducibility

```bash
python -m pip install -e ".[dev]"
python scripts/run_w3_observation_loss_selection.py \
  --out build/w3-observation-loss-selection
```

Stable release **1.1.0** stays published; core development source
remains **`1.2.0rc2.dev0`** and
`production_release_ready=false`. No release tag,
PyPI upload, or W3 inferential-method promotion is authorized.
