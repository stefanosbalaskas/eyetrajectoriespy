# R88-A — independent numerical reconstruction of conditional audit-return sensitivity

**Scientific audit protocol, not a production feature or a new estimator.** This document describes the independently implemented verification gate for the original R88 experiment, rather than independently established findings. The independently replayed results may be reported only after all four dedicated audit jobs actually pass.

## Original source archive

Original prospectively frozen [R88 research PR #441](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/441), [science workflow #39672709750](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39672709750) and immutable [archive #12381046538](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39672709750/artifacts/12381046538) passed all **12/12** dedicated science jobs. The original checkout recorded by the GitHub PR scientific merge is `194d00a14ac35b85cf25864ed5e099d0c7ffb02c`. The archive contains the complete 64 independent source conditions, 128 MAR/MNAR masks and 1,024 repeated method records; none is discarded to secure numeric agreement.

Original-source 25% audit-fraction mean fitted first-stage coefficients at assumed return γ=0 versus γ=1.35: MAR independent curves +0.2859 versus +0.0066 (true δ=0), MAR repeated participants +0.3207 versus +0.0225 (true δ=0); MNAR independent curves +1.2174 versus +1.0147 (true δ=1.1), MNAR participants +1.2117 versus +0.9892 (true δ=1.1). Each cell comprises 32 independent source blocks. These original results **are not independently audited conclusions** until the mandatory original replay passes.

## Implementation independence

The R88-A audit script does **not** import either original R87 or R88 generators/estimators or the production package. It independently regenerates exact complete source X/Y, trial covariance, paired first-stage MAR/MNAR masks, secondary-recovery uniforms, third-stage randomized assignment and outcome-selective audit return using the archived, prospectively frozen seeds. It verifies complete-source, mask, pilot and selection SHA digests and every original assigned/returned count.

The independent numerical implementation uses SciPy score roots rather than source bounded Newton iteration for the secondary-selection model, and an independent Newton scoring routine rather than source bisection for the first-stage δ. It replays **every** archived combination of native independent-unit design, observation law, assignment rate, source block and four stipulated γ values; checks convergence/refusal statuses, delta estimates, and cell summaries with explicit tolerances; validates original three-member SHA256 manifest and original-source checkout; and uploads a distinct audit artifact. Changing hidden Y after fixing observed selection cannot change the original fitted score.

The four-gamma sensitivity family depends on a **simulator-calibrated recorded-input baseline** and an analyst-assumed outcome coefficient, which is not identified from returned outcomes alone. Inclusion of generating γ=1.35 is an oracle-alignment comparator, not evidence of empirical return-parameter recovery. Source rows are repeated method evaluations, not 1,024 independent datasets. These point-estimation diagnostics establish neither general MNAR identification nor confidence-band calibration.

## Acceptance conditions

The mandatory independent workflow consists of Python 3.11/3.12/3.13 numerical/tamper tests and an unskippable archived-R88 replay job. The original 12/12 passes and independent synthetic fixture tests do **not** substitute for passing the actual original-artifact replay. Treat discrepancies as real failures, preserve provenance, and resolve visibly in this research PR. Do not publish figures or website prose as independently verified before that gate.

Protected main/public 1.1.0 is unchanged; no production inference API, version 1.2 release, TestPyPI/PyPI publication or nominal-90% simultaneous band claim is authorized. Scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain OPEN.
