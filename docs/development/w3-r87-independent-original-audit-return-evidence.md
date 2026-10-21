# W3 R87-A — independent replay of missing returns from randomized gaze audits

**Research only · Independent numerical/provenance audit, not a new estimator.** This page documents the original R87 source design and separate audit acceptance gate. It is not a statement that the original archive was independently verified until the R87-A real-archive workflow completes.

## Original prospective study completed

[R87 draft #438](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/438), [original science workflow #39646565487](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39646565487) finished all 3 Python-version numerical contract jobs, 8 new-source shards and the checksummed complete aggregate **12/12 successful**. Source artifact [#12367807523](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39646565487/artifacts/12367807523) includes **32 independent generating blocks per cell, 64 independent complete synthetic X/Y source conditions, 128 first-stage MAR/MNAR masks and 2,304 repeated-method evaluation records**. The original science checkout was **2716a79ceec03ef8cf1cd0a8be3546e638c98884**, and all three original aggregate SHA256 digests were checked.

The experiment prospectively compared complete audit return, selectively returned audits according to recorded predictor/time, and audit returns additionally selected on hidden outcome Y. Random audit assignments (q=.25,.50) were paired within source, as were outcome-specific return uniforms. The three model assumptions fitted to identical observed returns were assignment-only, recorded-input return probability, and a simulator-only true return oracle. The latter is not available from real gaze data.

## Original source contrasts — not yet independent R87-A outcomes

| First-stage mechanism | Native unit | Recorded-input return weighting, q=.25, outcome-selective actual return | Simulator oracle | True source delta |
|---|---|---:|---:|---:|
| MAR | Independent curves | +0.2356 | −0.0102 | 0 |
| MAR | Three-trial participants | +0.2889 | +0.0296 | 0 |
| MNAR | Independent curves | +1.1740 | +0.9915 | 1.1 |
| MNAR | Three-trial participants | +1.1716 | +0.9817 | 1.1 |

Each original cell contains 32 independent generating blocks and no numerical first-stage refusals in these displayed comparisons. The 50% audit assignment showed qualitatively similar direction in the original archive. These estimates demonstrate simulated sensitivity to selective third-stage audit return; they are **not** identified MNAR parameters or validated uncertainty intervals.

## What the independent R87-A implementation checks

The separate pure-research [R87-A draft](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/439) does not import the R87 source simulator, estimator or package. Its independent implementation reconstructs the original synthetic X/Y and native Gaussian/trial laws, original MAR/MNAR uniforms/masks, second-stage validation successes, randomized third-stage assignments, hidden-outcome-selective return probabilities and independent completion uniforms. It checks the original source and audit-return digests and enforces assignment/returned subset relations.

For every one of the 2,304 original rows, it independently estimates secondary recovery logistic coefficients using SciPy score-root equations rather than the original code's bounded Newton iterations. It separately estimates the first-stage MNAR logistic selection coefficient from the measured observations and the stated union recovery propensity, independently verifying refusal statuses, fitted parameters, weight selection and original true-MAR/MNAR labels. It recomputes the cell-level fitted means and numerical completion/refusal counts across all 32 source blocks. The actual original source checkout and exact three-member SHA256 manifest are frozen and required.

The dedicated GitHub Actions workflow tests numerical agreement on synthetic fixtures in Python 3.11, 3.12 and 3.13, then requires downloading **the actual immutable R87 original source archive**, running the separate audit code, and uploading its own evidence. **Passing preflight tests or R87 original aggregate does not imply independent original numerical verification.** Claim that status only after all four independent audit jobs pass.

## Scientific limits

Randomized audit assignment does not imply randomized *return* of assigned missing outcomes. The outcome-dependent audit completion oracle uses simulation-known Y and cannot be assumed observed for ordinary missing gaze. Recorded-input weights may remain biased when return depends on latent Y. The original R87 source produces point-estimation diagnostics only; it does not estimate general MNAR identification bounds, recover historical gaze, provide cluster-valid uncertainty or justify nominal-90% simultaneous slope bands.

Issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain OPEN. No change to stable 1.1.0, production inference API, protected main, v1.2 release tag or PyPI/TestPyPI is authorized.
