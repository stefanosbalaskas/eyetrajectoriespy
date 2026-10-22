# R89-A independent full-source finite-population sharp-bound numerical audit

**Research only · Independent verification acceptance protocol.** This page records the originally archived experiment and the conditions for a separate numerical/provenance qualification. It is not evidence that the R89-A audit has passed until all independent CI jobs succeed.

Original source [R89 draft PR #444](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/444), [science workflow #39696542346](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39696542346), 12/12 dedicated tests and original simulation/aggregation jobs passed. Frozen original checkout `656df21a042e0e823147e37002580aeba41ac17d`; archive [artifact #12391167529](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39696542346/artifacts/12391167529) with GitHub ZIP digest `sha256:fdab0cd2d1fef878beed95621612dbedec4751abc3749ed16a74673e3a86c24b`. There are 64 complete independent source conditions, 128 paired first-stage MAR/MNAR masks and 512 repeated measurement-method records, 32 primitive blocks per fixed native-design/mechanism/return-law/audit-fraction comparison.

## Independent implementation

The separate `audit_w3_r89_original_finite_bounds_independent.py` does not import original R89 source code, package estimators, or hidden source summary calculators. It generates X/Y and observation masks from independently coded equations and exact prospectively frozen streams; reconstructs secondary validation and nested randomized audits, both complete and outcome-selective returns; independently recomputes algebraic finite-population bounds from observed Y only and contrasts for the positive/negative predictor groups; compares original simulator-only truths and all cell-level summaries. Every one of the 512 original row identities, SHA256/X/Y/observation digests and source-refusal status must agree. The original archive contains three content members, a source-commit field and SHA256 manifest; all are mandatory and protected by fail-closed validation.

The audit requires three independently running Python-version contract jobs and an unconditional original-archive replay. Preflight fixtures alone are **not** an independent source replay.

## Original descriptive negative-identification result (not yet independently audited)

At 25% audit assignment and outcome-selective completion, the source-mean sharp-bound width for the bounded mean is approximately **0.601** for MAR independent curves, **0.594** for MNAR independent curves, **0.596** for MAR repeated-trial participants and **0.585** for MNAR repeated-trial participants. At 50% assignment, the corresponding widths narrow to approximately **0.473**, **0.474**, **0.467** and **0.464**. Across original fixed cells, zero of 32 independent primitive blocks has a positive-versus-negative-predictor *bounded-mean contrast* interval that excludes zero. These are source-level descriptive means without statistical intervals; the no-return-assumptions bounds can be wide and uninformative about contrast sign.

Every original source truth lies inside its interval *by finite-population algebra*, not as evidence of frequentist nominal coverage. No sample-size/cluster uncertainty is supplied for the bound-width means.

## Mandatory interpretation boundary

The constructed target is **clip((Y+1)/2,0,1)** among initially missing records; the required [0,1] support makes finite-population worst-case bounds possible. This is neither an arbitrary raw gaze coordinate nor the function-on-scalar regression slope. Sharpness is conditional on the finite missing-record target population and no auxiliary constraints. It does not identify a nonreturned gaze value, model the latent completion probability, recover R88's outcome-return gamma, or establish the W3 simultaneous 90% band coverage.

Open blockers [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) and [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) remain open. Stable 1.1.0 unchanged. The R89/R89-A code must remain in draft research PRs, separate from protected main. No v1.2 tag/GitHub release/PyPI publication is authorized.
