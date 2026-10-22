# R90-A — independent original-source replay of audit saturation

**Independent numerical verification protocol; does not upgrade point-identification or confidence-band claims.** Original R90 [draft PR #447](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/447) created its new-source simulation before this independent audit was implemented.

## Original immutable source

- Original scientific [run #39746751227](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39746751227) passed **12/12 dedicated jobs**: three Python-version contracts, eight four-block independent new-source shards and an audited SHA256 source aggregate.
- Complete original source [artifact #12411243517](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39746751227/artifacts/12411243517), ZIP digest `sha256:664220aa6f100950678a0ca4af1a89a6d1b42614be2a0761f910f11b86465a30`.
- Actual GitHub PR original source checkout archived by GitHub Actions: `2f713c36cdb9977e8277e5a0412e4b162f2aedf2`; original branch source head at first study `46fc947aba820da682371e6e8f91786710fc237e`. The source commit and member SHA256SUMS must match exactly.
- 64 new complete independent source conditions, 128 first-stage MAR/MNAR source masks, **1,280 repeated source-method rows**, 32 independent generating blocks per fixed cell, q in {0, .25, .5, .75, 1}. No conditional source exclusions.

## Independent source and scoring implementation

R90-A does **not import the original R90 generator or package estimators**. An independent script reconstructs the original X/Y law, trial covariance, original response source, first-stage observation masks, secondary validation, common nested randomized audit assignment and selective/complete actual return. It independently calculates finite-population interval endpoints **using only measured Y** with NaNs for all unreturned Y; hidden complete data are used only by a distinct privileged simulator-truth audit. Original X/Y, mask, secondary, assignment, actual-return SHA256 digests and counts, per-source bounds, contrast bounds and truth inclusion are independently checked across all 1,280 rows. The audit independently reproduces the five-step source-level widths and the earliest audited assignment fraction meeting width thresholds 0.10 and 0.05. False claims or omitted rows are fail-closed.

Python 3.11/3.12/3.13 independent fixtures are required, followed by an unconditional read-only **original source-artifact replay**, and distinct evidence artifact upload. Passing fixture tests alone is insufficient. Original-source 12/12 jobs are not themselves independent agreement.

## Original, unaudited source contrasts

When all initially unrecovered records are assigned q=100%, the **ideal complete-return** source mean of the sharp bounded-outcome width reaches precisely zero. Under selective return, source-mean widths remain approximately 0.216 (MAR curves), 0.226 (MNAR curves), 0.210 (MAR participants) and 0.223 (MNAR participants), using 32 independent source blocks per fixed design. **0/32 selective-return source blocks in each fixed q=100% cell** attained bounded-mean width 0.10 or 0.05, while **32/32 complete-return blocks** did. These are original, unaudited simulation point summaries until mandatory R90-A replay passes. This is evidence of an *assignment-versus-actual-return floor in the frozen synthetic law*, not a universally estimated MNAR floor.

## Interpretation/release gate

The bound is sharp for the **finite realized initially missing target population** after the predeclared bounded `clip((Y+1)/2,0,1)` transformation. This is not a bound on arbitrary raw gaze or functional slopes, not the original R88 return γ, not a confidence interval, and not a statistical 90% simultaneous-band coverage validation. The deterministic truth containment is merely an algebraic source consistency check.

Only after independent original-source replay passes may scientific documentation/plots proceed on a separate docs-only branch with strict all-workflows CI and protected-main GitHub Pages validation. Original and independent source PRs remain open draft/unmerged. #289/#296 remain OPEN, stable 1.1.0 unchanged, v1.2/GitHub release/PyPI HOLD.
