# Experimental E1–E4 workflow expansion (not an RC1 public API)

!!! warning "Research development; do not treat as a published feature"
    These APIs are currently on branch `feature/e1-e4-workflow-expansion-rc2` only. Published stable **1.1.0** and frozen qualified candidate source **1.2.0rc1** do **not** promise these interfaces. A new candidate release, compatibility audit and installed-wheel qualification must precede any promotion.

## E1 — Executable preprocessing and retained phase information

The analyst explicitly specifies an ordered `PreprocessingPlan`. The experimental `run_preprocessing_plan()` invokes existing package functions for smoothing, limited gap interpolation, normalization, centering, resampling and landmark-based registration. It records sample support, scientific effects, changes in units and warnings at every step. Full warp functions survive registration, and sparse inputs are **never converted to dense by default**.

## E2 — Preflight without exclusion

`workflow_preflight()` reports per-curve missingness, minimum channel support, recorded time/coordinate units and participant/trial hierarchy. An incompatible requested dimension or common-grid requirement is blocking; low support and absent hierarchy labels are descriptive warnings. This is not a power calculation, a QC exclusion rule or estimator qualification.

## E3 — Declared sensitivity rather than hidden model choice

`run_workflow_sensitivity()` requires multiple named typed configurations, a common declared estimand, an explicit baseline and analyst-provided scalar extraction functions. Different estimands fail before execution; incompatible workflow contracts cannot be compared. Fits that fail remain visible in the specification ledger. The companion plot shows descriptive stability, not p-values or confidence intervals.

## E4 — Auditable manuscript reports

`render_workflow_report()` creates Markdown or HTML with only actual fitted outputs: model specification, steps/decisions, existing reporting text, tables, figures, analyst-provided captions and inferential limitations. Each evidence file has a SHA256 digest; generated results do not imply causality or fabricated significance tests.

## Worked local demonstration

Run `python examples/experimental_workflow_e1_e4.py` after installing **the exact experimental branch** in a disposable research environment. The example uses a synthetic, explicitly seeded trajectory dataset; it saves a preflight CSV, preprocessing audit, descriptive sensitivity CSV and a checksummed Markdown scientific report. It does not publish, promote or select a model.

## Qualification boundary

The stable and RC1 frozen estimator layers are unchanged. The experimental namespace remains outside `WORKFLOW_API_AUDIT.json`; E5 will require a new release identity, an independently reviewed public API freeze, full regression checks and installed-package evidence. Native Bayesian FPCA and effect-region localization remain out of scope.
