# R92-A — mandatory independent real-original selective-return bias audit

This source/audit experiment is distinct from the original R92 implementation and from production eyetrajectoriespy. No original source/estimator routines are imported.

## Frozen actual original archive

Original [draft R92 PR #453](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/453), original science [run #39837488254](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39837488254): **12/12 dedicated science jobs successful**. Exact original 14,336-record SHA256 [archive #12452420323](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39837488254/artifacts/12452420323), archive ZIP `sha256:76bf1ae3aa9a35b9b29ac6b2c0cfb430f2d5567783ddb4d1099f3a58472b8ae3`, original generating GitHub PR merge checkout `2b0c29cbe342919c204c445be4f80639b2261efb`, distinct from source branch head `6cbb4cfc78a7c8f42181f19bab848c19a2c80930`.

## Required independent replay

A separately coded Python implementation reconstructs **64 independent new complete X/Y source conditions** with frozen seeds, **128 paired MAR/MNAR first-stage masks**, selectively completed secondary recovery, eight conditional assignment/recovery repetitions, nested randomized audit inclusion g=25%/50% and all seven actual completion scenarios: fully completed, uniform failure at δ=1%/5%/15%, and outcome-selective return `c_i=1−δ(0.5+Z_i)` at the same levels. Every original X/Y and source/mask/assignment/actual-return SHA256 digest must match.

For all **14,336** matched source-method rows, independent arithmetic checks the assignment-only inverse g mean, the nominal-uniform inverse `g(1−δ)` mean, oracle conditional biases for each scenario, errors against the original finite source truth, bounded finite-group sharp interval width and all source-level summary cells. The two estimators are observed-only: every otherwise unreturned initial missing target observation must be NaN in their inputs. The true completion probabilities and complete simulator targets must *not* be used by the fitted estimators.

Source denominator remains 32 independent complete generating blocks per fixed native design. The within-source eight repeated audit draws and paired missingness, assignment and return laws are not independent primitive source replicates. A successful 3-Python-version fixtures run **does not independently verify the original source** unless the mandatory immutable complete original archive replay also passes. Archive SHA256 identities, exact original checkout and full failure-inclusive 14,336-key factorial must be verified.

## Interpretation and gate

Uniform noncompletion produces exact conditional zero nominal weighting bias when δ is correct; outcome-selective completion yields an oracle conditional bias in a nominal uniformly adjusted estimator. This is not estimation of field missingness parameters, a valid nominal functional band, a point-identified real missing gaze sequence or a release-ready estimator. Analytic simulator-only conditional biases are not usable observed-only return propensity estimates.

The original implementation and separate audit must remain draft research PRs. Only after independent original-source 4/4 successful jobs may the source-derived figures and article enter a separate docs-only 25-workflow CI and protected-main Pages deployment gate. Scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain open. Stable public 1.1.0 unchanged; **v1.2/GitHub/PyPI HOLD**.
