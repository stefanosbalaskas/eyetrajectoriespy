# Experimental E1–E4 workflow expansion (bundled, not stable)

!!! warning "Bundled with stable 1.2.0, but not stable APIs"
    Twelve E1–E4 helpers can be imported from `eyetrajectoriespy.workflows.experimental` in published `1.2.0`. Their interfaces and scientific interpretation remain **experimental and unstable**, separate from the ten supported W1–W4 module-scoped workflow routes. Development [PR #223](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/223) and the historical RC2 [PR #471](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/471) document qualification provenance, not stable helper promotion.

## E1 — Executable preprocessing and retained phase information

The analyst explicitly specifies an ordered `PreprocessingPlan`. The experimental `run_preprocessing_plan()` invokes existing package functions for smoothing, limited gap interpolation, normalization, centering, resampling and landmark-based registration. It records sample support, scientific effects, changes in units and warnings at every step. Full warp functions survive registration, and sparse inputs are **never converted to dense by default**.

## E2 — Preflight without exclusion

`workflow_preflight()` reports per-curve missingness, minimum channel support, recorded time/coordinate units and participant/trial hierarchy. An incompatible requested dimension or common-grid requirement is blocking; low support and absent hierarchy labels are descriptive warnings. This is not a power calculation, a QC exclusion rule or estimator qualification. The optional `plot_workflow_preflight()` presents the rank-ordered missingness fractions without identifying an exclusion threshold.

## E3 — Declared sensitivity rather than hidden model choice

`run_workflow_sensitivity()` requires multiple named typed configurations, a common declared estimand, an explicit baseline and analyst-provided scalar extraction functions. Different estimands fail before execution; incompatible workflow contracts cannot be compared. Fits that fail remain visible in the specification ledger. Optional analyst-defined boolean/string conclusion extractors can show which *declared* interpretation labels change relative to the baseline, without synthesizing statistical tests. Valid uncertainty endpoints may be included only as explicitly extracted comparable model metrics. The companion plot shows descriptive stability, not p-values or confidence intervals.

## E4 — Auditable manuscript reports

`render_workflow_report()` creates Markdown or HTML with only actual fitted outputs: model specification, steps/decisions, existing reporting text, tables, figures, analyst-provided captions and inferential limitations. Each evidence file has a SHA256 digest; generated results do not imply causality or fabricated significance tests.

## Worked local demonstration

Run `python examples/experimental_workflow_e1_e4.py` after installing **`eyetrajectoriespy==1.2.0`** in a disposable research environment. The experimental helper interface can change in future releases. The example uses a synthetic, explicitly seeded trajectory dataset; it saves a preflight CSV, preprocessing audit, descriptive sensitivity CSV and a checksummed Markdown scientific report. It does not publish, promote or select a model.

## Qualification boundary

The stable and RC1 frozen estimator layers are unchanged. The experimental namespace remains outside the ten supported contracts in `WORKFLOW_API_AUDIT.json`. The exact-RC2 [E5 experimental workflow](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/40002802440) passed all three Python 3.11–3.13 source/wheel and synthetic tests on commit `9891feee`. This is **historical engineering qualification only**; it is not statistical inferential calibration or a stable E1–E4 helper contract. The twelve importable helpers remain experimental in 1.2.0. Native Bayesian FPCA and effect-region localization remain out of scope.
