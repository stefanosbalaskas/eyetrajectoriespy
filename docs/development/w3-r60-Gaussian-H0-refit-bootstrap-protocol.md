# W3 R60 — prospectively frozen conditional Gaussian H0 nuisance-refit bootstrap feasibility

**Research-only numerical feasibility experiment**, not a qualified 5% variance-component test, a confirmed bootstrap null reference, a power analysis or a 90% fitted-CR2 confidence interval / simultaneous functional band.

## Motivating independent evidence

R58 original 24-block true-zero Gaussian candidate 50:50 point-zero/chi-square-one 5% benchmark exceeded its cutoff in **5/24 = 20.8%** ordinary and **2/24 = 8.3%** extreme support. R59 used **128 new independent blocks** and found **ordinary 11/128 = 8.6%** (95% Wilson 4.9–14.7%) and **extreme 7/128 = 5.5%** (95% Wilson 2.7–10.9%). [R59 original #39065162776](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39065162776) passed 10/10 source jobs with 256/256 accepted nested Gaussian fits and complete 1,536 optimizer-start slots. R59-A's first independent audit failed because it attempted to download the archive before its publication. Audit rerun is separately required; do not conflate original science with independent audit.

The modest R59 excess relative to 5% is uncertain. Rather than tune a cutoff using R59's evaluation blocks, R60 probes whether a **fitted-null, nuisance-refitted, finite-design Gaussian parametric bootstrap** is computationally and numerically viable.

## Frozen R60 feasibility design

**4 entirely NEW independent Gaussian primitive source blocks**, seed `202610176060` (not R58 or R59), with 24 participants, native irregular trial observations and fixed observed predictor/timestamp geometry. For each primitive block evaluate ordinary and extreme dependent support as **paired** variants: 8 source cases, not 8 independent primitive blocks. The generating random-slope contribution is subtracted to yield a **true exact structural zero variance** data-generating condition.

For every source case:
1. Fit the original R57 *nested* Gaussian REML hypotheses: H0 fixes random-slope variance to exactly 0 and profiles intercept/trial/sensor covariance; H1 permits variance >=0. Keep R57's original 2 H0 and 4 H1 starts, optimizer success, physical-coordinate KKT≤.001, reconstruction≤1e−6, near-best-NLL≤.001, and signed nested monotonicity threshold. A failed source or numerical fit remains in the source and subsequent bootstrap original draw ledgers.
2. Build H0 **weighted participant covariance blocks** exclusively from that source's numerically accepted H0 variance ratios and `prepare_reml_design` kernels. Require zero slope component, SPD Cholesky, and exact original observed design/block alignment. Compute H0 GLS fitted mean coefficients using its weighted block covariance.
3. Simulate **31 new Gaussian H0 pseudoresponses** per source (draw seed `202610176061` with frozen disjoint block/support/draw indexing). Each simulation retains that observed source's fixed X, w, group, time, trial and predictor values. Draw independent participant-block Gaussian residuals under H0 from weighted block Cholesky and backtransform by sqrt(weight). This is a **conditional plug-in Gaussian null hypothesis** and the finite-nuisance estimation uncertainty of the original source fit is not magically removed.
4. **Independently re-estimate all nuisance components on EVERY bootstrap pseudoresponse** by fitting the exact original Gaussian H0 and H1 nested REML objectives (6 original optimizer start records per new response). The original source has another six starts. Thus total planned **248 bootstrap responses**, **512 nested model slots**, **1,536 optimizer-start records**. Every failed draw keeps all six start placeholders; **do not silently resample or substitute another draw**.
5. Only when the source and **all 31** bootstrap numerical nested fits are accepted, compute the conditional add-one right-tail p-value `(1 + count(T_boot >= T_obs)) / 32`. Its minimum is **1/32 = .03125**, and its next rank is **2/32 = .0625**; a 5% rejection is therefore possible for just the most extreme original statistic. This discreteness and B=31 make this only a coarse diagnostic. Do not compare a partially completed bootstrap fraction to the 5% threshold or treat missing draws as zeros. Report candidate classical cutoff exceedances separately with original frozen T>2.705543454.
6. Record original exact-checkout SHA256 source provenance, null fitted physical covariance, original signed deviance, 31 original draw seeds/statistics and both fitted-null and fitted-alternative numerical start results; enumerate all source/refit refusals and conditional bootstrap p-values by leverage, not just successful claims.

Four one-block independent shards must aggregate only after exact unique case identities, same-checkout SHA256 manifests and exact planned 248 draw and 1,536 solver-start positions are checked.

## Interpretation and boundaries

This **cannot** validate null size with four independent primitive blocks. Conditional simulation from a *plug-in* fitted H0 covariance is not analytically exact; calibrating the null model within each observed source does not prove a uniform p-value distribution across fresh independent generating blocks or identify the correct covariance family. Even perfect solver success and nominal-looking p-values will not qualify 5% null behavior, power, component recovery, **90% fitted-CR2 pointwise intervals**, **simultaneous functional bands**, or MAR/MNAR extensions.

Next gate after numerical feasibility: independently reproduce original bootstrap evidence; audit Gaussian draw covariance against the fitted null (analytic matrix identities, empirical generated-moment checks with separate draws); enlarge B and evaluate error frequency across **disjoint NEW independent truth-null source blocks**, prespecifying error/refusal handling. Compare to the unfitted-nuisance reference and alternatives only after a complete source denominator.

Keep blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) open. Do not merge into protected main, tag version 1.2, publish PyPI or promote to public API.
