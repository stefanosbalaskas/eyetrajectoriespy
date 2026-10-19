# W3 R71-A — independently re-simulated exact Gaussian law and archived 999 wild-maxima

**Research-only original-source numerical audit; not 90% data-estimated coverage validation.** Separate branch stacked on prospectively predeclared [R71 original Gaussian-law benchmark](w3-r71-prospective-known-law-oracle-protocol.md), independent of source generator/fit/aggregation. Scientific [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) remains open.

## Original source results and original archive

Original prospective [R71 draft PR #390](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/390), [complete science workflow #39227237532](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39227237532) **8/8 dedicated jobs PASS** (3 numerical Python-version contracts, four new eight-block source shards and SHA256 complete aggregate). Original full [archive artifact #12175485571](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39227237532/artifacts/12175485571), frozen GitHub Actions original scientific PR merge checkout **`1102b57fe9605e46303921989842ee3f7a0e1f84`**.

New source seed 202610197171, **32 independent primitive generating Gaussian blocks**, paired independent-unit designs (72 curves or 36 participant means each with 3 trials) × ordinary/extreme leverage, **128 original source cases**, all 128 completed, zero numerical refusals. Exactly 999 frozen original W3 independent-unit Rademacher multiplier vectors per case (**127,872 total**), original raw **999 source wild-slope maximum statistics** per case, and separate Gaussian exact-known-covariance reference seed 202610197172 with **32,767 standardized maximum-pivot draws per design, 65,534 total**. These reference draws are *conditional Monte Carlo*, not independent generating source blocks. The Gaussian law comes from the simulation's exact known covariance, not estimated from observed data.

Original empirical 90% simultaneous slope-band truth inclusion on the complete 31×2 time×dimension grid:

| Source design; denominator 32 independent blocks | Original W3 wild-HC1 | Known-Gaussian-law reference |
|---|---:|---:|
| Independent curves ordinary | 22/32 = 68.75% | 28/32 = 87.50% |
| Independent curves extreme | **2/32 = 6.25%** | **26/32 = 81.25%** |
| Repeated participants ordinary | 25/32 = 78.125% | 27/32 = 84.375% |
| Repeated participants extreme | **13/32 = 40.625%** | **27/32 = 84.375%** |

Known Gaussian original reference criticals: curves **3.1316628143877114**, participant means **2.484611913363955**. Mean observed HC1-to-exact true SE ratios: curves ordinary **0.9878**, extreme **0.8770**; participants ordinary **0.9655**, extreme **0.7859**. Mean wild-critical/known-law-critical ratios: curves ordinary **0.9443**, extreme **0.8981**; participants ordinary **0.9465**, extreme **0.9072**. Two sources in ordinary curves and participants had a known-vs-wild discordance in the opposite direction (one wild-only each); original paired comparison retains them.

## Independently implemented original numerical reconstruction

The separate auditor `scripts/audit_w3_r71_independent_known_gaussian_archive.py` **imports none** of R71's original source generator, package W3 OLS, wild-bootstrap implementation or original aggregation. Required genuine-original-source workflow must independently:

- verify all **four original SHA256 bytes/checksum members** including the **complete 65,534-draw known-law archive**, original full exact science PR checkout and all 128 new source identities;
- separately re-simulate **all 65,534 standardized Gaussian exact-known-law maximum draws** using independent formulae for curve-i.i.d. normal noise and participant correlated-in-time latent effect + averaged three-trial noise, with archived true variance-grid verification; sort/recompute two 90% `higher` Gaussian critical values;
- sort/recompute every original **999 wild-slope raw maximum-statistic reference** for every completed new fitted source (127,872 original wild draw maxima) and original source criticals;
- check the original 31×2 archived slope beta-error, HC1 sample SE and exact-known true SE grids, known Gaussian covariance *shape*, source true and HC1 maximum-stat pivots, mean/min/max HC1/known true SE and wild/known critical ratios, all original truth inclusion classifications and all original 32-independent-block Wilson Monte Carlo intervals and paired differences, with failure-inclusive bounds;
- reject tampered/checksum-mismatched originals, missing/duplicated generating-source identities, altered original frozen seeds, forged release/nominal 90% claims and falsely substituted source fit evidence.

**Important original-source limitation:** original R71 did **not** archive the full individual unit design matrix `X` or raw Gaussian response innovations. The independently audited exact-known SE grid can be checked for correct conditional-Gaussian **variance shape** and internal consistency, but its source-specific scalar `[(X'X)^{−1}]_{slope,slope}` cannot be independently derived from unarchived X. The original R71 Python regression-contract jobs separately check original package OLS/HC1 and source law against the generator. An audit passing archived numerical evidence **does not independently prove the unarchived source data-generation law**.

Even when the independent original archive audit is green, the scientifically justified conclusion is that the *artificially known-law* Gaussian benchmark has much higher observed truth inclusion than the existing wild-HC1 band under this fully observed fixed-grid Gaussian mechanism. This does **not** provide an implementable known-covariance reference for real eye tracking, nor certify nominal 90% inference of estimated-covariance 1.2 methods.

Blockers **#289 and #296 OPEN**; protected main, stable v1.1.0, unreleased 1.2, tags and PyPI unchanged.
