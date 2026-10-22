# Design unbiasedness when randomly selected missing gaze outcomes are actually recovered

*Methods companion for [R91](w3-r91-guaranteed-recovery-design-ht.md) · Research-only finite-population demonstration*

## Source target versus randomization distribution

The original target population is the **realized set M of initially missing records**. Their predeclared bounded synthetic outcome is $Z=\operatorname{clip}((Y+1)/2,0,1)$. The finite target mean is the *fixed quantity* $\mu_M=N^{-1}\sum_{i\in M}Z_i$. Some of its values have been separately observed in an earlier response-selective validation phase, and the other values remain unknown.

Unlike the original missingness mechanism, the final validation step is explicitly assumed to sample previously unknown outcomes independently with a **known positive Bernoulli probability $g$** and to **actually complete measurement for all selected records**. This is a stronger requirement than assigning a randomized follow-up invitation. It cannot be assumed merely because investigators intended to remeasure gaze.

## Exact conditional design expectation and variance

Conditional on the fixed outcomes and earlier observation mask, define $S$ as the previously observed subset and $U=M\setminus S$ the still-missing subset. A completed randomized retrieval indicator $G_i$ is independent Bernoulli($g$) for each $i\in U$. Then

$$
\hat\mu=\frac{1}{N}\left[\sum_{i\in S}Z_i+\sum_{i\in U}\frac{G_iZ_i}{g}\right].
$$

The conditional expectation is $\mu_M$ because each unknown finite-source outcome contributes $Z_i$ in expectation. Conditional independence of the sampling indicators—not independence of the repeated gaze observations—gives

$$
\operatorname{Var}_G(\hat\mu)
=\frac{1-g}{gN^2}\sum_{i\in U} Z_i^2.
$$

The observed-data unbiased design-variance estimator is

$$
\hat V_G
=\frac{1-g}{g^2N^2}\sum_{i\in U}G_iZ_i^2.
$$

These expressions do not require knowing the hidden $Z_i$ values in the estimator. The separate simulation-only variance oracle evaluates the unknown sum using the known generating truth to test arithmetic. The public package does not expose any of these experimental methods. The HT point estimate is not necessarily constrained to [0,1] despite the bounded source values; clipping the estimate would alter the unbiasedness property.

The test suite independently **enumerates all four Bernoulli completion patterns** for two otherwise unknown outcomes at $g=.5$, proving exact conditional expectation, variance and unbiased variance-estimation identities. This is stronger arithmetic evidence than a 16-realization Monte Carlo mean close to zero, though it remains only evidence of the stated design formulas.

## The 16 randomized retrieval repetitions

R91 uses a fresh, frozen source generator to create 32 independent curve blocks and 32 independent repeated-participant blocks. MAR and MNAR missingness are paired on the same complete source. Sixteen new Bernoulli assignment masks are created *conditional on that original complete source and missingness state*, and the three inclusion probabilities 0.10, 0.25, 0.50 use common uniforms within each repetition.

The 6,144 analysis records therefore include only 64 independently generated complete sources. Within each fixed configuration and inclusion fraction there are 32 independent generating blocks and 16 **dependent conditional resamplings** of each; treating all 512 records in a fixed cell as independent datasets would exaggerate precision.

## Why observed RMSE can favor a naive estimate

An estimator may be unbiased with respect to the randomized recovery assignment and nevertheless have higher finite-sample variance than a biased estimator. In the frozen synthetic law, the naive measured-only estimate has relatively modest bias, while inverse-probability weighting amplifies the contribution of a small number of recovered values, particularly for $g=.10$.

For the selected MAR independent-curve fixed cell, the original simulation reports HT RMSE approximately .0413 at 10% recovery and .0149 at 50%; the corresponding naive values are .0112 and .0043. It would be incorrect to claim general dominance for either method. The comparison is conditional on a bounded transformed estimand, a specific source law, an assumed completed-retrieval mechanism and only 16 recovery replicates per independent source.

## What is not proven

Design unbiasedness means an expectation over the **hypothetical recovery randomization**, not exact point identification of the particular target with only partial observed records, not small mean squared error, and not validity of a nominal confidence interval. No confidence interval or variance correction for source-level superpopulation effects is supplied. The exact conditional randomization variance does not resolve W3's independent-curve/participant simultaneous-functional-band undercoverage.

If the recovery *completion* depends on hidden outcomes after assignment, the known Bernoulli inclusion probability no longer describes the actual observed outcome sampling law, and the HT argument ceases to apply without stronger verified information. R91 does not recover sensor values that cannot be remeasured.

Source and independent-audit evidence, archived checkout/digests and any failure-inclusive replay are tracked in the [evidence ledger](../development/w3-r91-independent-recovery-evidence-ledger.md). Issues [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) and [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) remain open. Research code stays draft, stable 1.1.0 unchanged, **v1.2 GitHub/PyPI HOLD**.
