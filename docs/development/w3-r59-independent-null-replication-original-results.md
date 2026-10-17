# W3 R59 — original 128-independent-block Gaussian true-null replication

**Frozen original numerical results, not a qualified boundary hypothesis test.** [Original R59 scientific workflow #39065162776](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39065162776) completed **10/10 dedicated jobs successfully**, eight disjoint source shards, source tests and complete SHA256 aggregation. Original [complete immutable-source archive #12112524426](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39065162776/artifacts/12112524426) is pinned to original scientific PR-merge checkout `90eaac1b7b4e1e5f98ef4fa5d4f63e3ff78689cd`. The first independent R59-A audit tried to download the archive *before publication* and correctly failed; the rerun is separately tracked and must not be counted as passed until its results are independently verified.

## Prespecified design and full numerical denominator

**128 genuinely new independent Gaussian primitive blocks**, seed `202610175959`, n24 participants, two paired support levels (ordinary and extreme leverage) per block, true structural participant random-slope variance exactly zero in both cases. These are **256 paired source cases, not 256 independent Monte Carlo replications**, with 512 H0/H1 model slots and 1,536 original optimizer starts. Every original case and fit was accepted: **256/256** accepted nested comparisons, **0** source-generation failures, **0** H0/H1 numerical refusals, **0** invalid nested comparisons. All original starts were recorded, not all starts independently identified global maxima. No positive-source power was tested.

The deliberately unmodified *candidate* 50:50 point-zero/chi-square-one classical asymptotic reference flags a case when T=2(negative REML log likelihood H0 minus H1) **>2.70554345409542**, the nominal 5% cutoff. The model fits a structurally **exact-zero** random-slope null against a nested **nonnegative** random-slope alternative; no post-R58 cutoff tuning was permitted.

| Predictor support | Independent true-zero blocks | Exceedances of candidate 5% reference | Observed rate | 95% Wilson interval | Exact-zero alternative selected | Median nested deviance |
|---|---:|---:|---:|---:|---:|---:|
| Ordinary dependent | 128 | **11** | **8.59%** | **4.87–14.73%** | 71/128 | ~0 |
| Extreme dependent | 128 | **7** | **5.47%** | **2.67–10.86%** | 73/128 | ~0 |

All-source refusal assignment bounds are identical to the observed fraction (ordinary 11/128, extreme 7/128) because no numerical refusals occurred.

**Paired 128-block decomposition:** both reject 2; ordinary-only reject 9; extreme-only reject 5; neither rejects 112. Leverage comparisons are not independent samples, and no preregistered formal paired superiority test is asserted.

## Scientific interpretation compared with R58

R58's original 24 independent blocks yielded ordinary true-null **5/24 = 20.83%**, Wilson **9.24–40.47%**, and extreme true-null **2/24 = 8.33%**, Wilson **2.32–25.85%**. Those results were internally numerically audited in [R58-A independent workflow #39064795085](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39064795085) with all 96 cases and 576 original starts checked.

The distinct R59 source yields a much less extreme ordinary true-null estimate of **8.59%**. Its 95% Wilson interval **includes** the candidate nominal 5% rate, whereas R58's ordinary pilot interval did not. This is not a successful independent confirmation of R58's 20.8% frequency or proof that the 5% reference is valid. It leaves a plausible finite-sample excess rejection rate, with uncertainty. The extreme design is similarly inconclusive. Together these results warrant design-specific finite-sample null-reference research, not rejection of all variance-component methodology nor declarations of nominal type-I control.

**Practical response:** independently develop a design-specific finite-sample null reference; for example conditional Gaussian parametric H0 bootstrapping with nuisance covariance re-estimated in each bootstrap and calibration separate from evaluation blocks. Calibration should not be tuned on an evaluation sample, and failures must remain recorded in the original source and bootstrap denominators. Before computational scale-up, prove or test simulation fidelity, restrictions imposed by the fixed mean, and the role of covariance nuisance estimation. Raw native Gaussian responses were **not saved** in original case archive, so the read-only R59-A audit can verify archived numerical and source metadata, not replicate native source `y` from first principles.

No calibrated p-values, statistical power, fitted-covariance 90% CR2 pointwise intervals, or simultaneous function-wide bands have been established. Issues #289 and #296 remain open. Protected main, public APIs, version 1.2 releases and PyPI remain unchanged.
