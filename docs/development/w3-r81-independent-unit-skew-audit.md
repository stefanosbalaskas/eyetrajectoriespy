# W3 R81-A — mandatory original skewed Student-t5 source audit

**Independently coded, read-only source replay; research only, no method calibration.** Original [prospectively frozen R81 PR #417](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/417) tests Student-t5 independent-unit shared radial noise plus centered, rare **one-sided Bernoulli contamination** `p=.08`, `A=.16`, signed time-varying profile `(.75+.25t)[1,-.65]`, superimposed on R80's correlated Gaussian component. Both skew and heavy tails are present in the same study; it is not a controlled isolation of either mechanism.

The replay pins original scientific checkout `698bf1eb80a9e856bfc2e0b5bdc362f425a75dc1` and original [workflow #39490888383](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39490888383), distinct from R80 source blocks. Frozen streams source 202610208180, true simulation-only reference 202610208181, wild 202610208182, two unchanged data-estimated Gaussian regularization references 202610208183/184.

## Independent numeric gates
1. Recompute original 32 independent primitive blocks ×2 designs ×2 support ×2 noise regimes = 256 source cases with exact RNG ordering for X, time-dependent Gaussian trial/participant components, independently drawn unit-specific Student-t5 radial χ² scales and **centered Bernoulli shocks**, one unit shock shared across all times/dimensions/participant trials.
2. Verify additional known marginal variance term `A² p(1-p) H(t,d)²` and correctly model source-specific true slope SE, not merely the preceding R80 Gaussian-conditional variance.
3. Independently compute original package W3 wild-HC1, baseline HC3 Gaussian, λ=.25 and λ=.50 positive-definite HC3 Gaussian maxima and true-source **non-Gaussian Student-t5 plus asymmetric Bernoulli** maxima: each of 999 known-law reference replicates must draw independent per-unit t radial *and Bernoulli* shocks, combine them using actual source design/s_i slope weights, and standardize by the correct enlarged true SE.
4. Reconstruct all five arrays of 999 raw maximum statistics, source-level 31×2 truth pivots and inclusion, critical values, paired discordances and error/refusal counts. Expect exactly **1,278,720** maxima if all original 256 cases are accepted. All checks use original read-only SHA256 manifest and exact source checkout; no source cases may be filtered or substituted.
5. Three separate Python version numerical contracts must pass before fourth original-archive artifact replay. Independent agreement verifies numerical reproducibility of the specified synthetic law only.

## Interpretation
Rare centered Bernoulli shocks induce genuine skewness, additional rank-one temporal and spatial covariance and source-level contamination, while t5 radial shocks retain finite fourth moment. No genuine eye-tracking recording, irregular observation process, MAR/MNAR loss, or broad family of contaminations is established. **W3 #289/#296 OPEN, stable 1.1.0 unchanged, 1.2 RELEASE HOLD, no public inference API or PyPI upload**.

**Status:** Original source outcomes and mandatory independent original-artifact audit must both complete before numerical coverage claims or website plots are published.
