# F5 independent-baseline AR(2) null: model-robustness falsification

**Research only. Not a qualified generic serial-dependence change-point test and not a replacement for the stable package API.**

The previous 2,520-test F5 comparison and subsequent 3,600-fit baseline-length ablation showed a useful reduction in false positives after propagating nuisance-AR(1) uncertainty, but marked conservatism under weak dependence and persistent false-positive inflation under true AR(2) dependence. Those results do not justify recalibrating thresholds or selecting an AR order on the test sequence.

This tranche implements a **separately prespecified, independently estimated scalar stationary AR(2) reference**, alongside the existing independently estimated AR(1) prototype. Each learns nuisance parameters and *whole-function innovation vectors* exclusively from an 80-curve stationary training baseline with participant IDs disjoint from the 36 tested whole curves. Coefficients are estimated via pooled lag regression across all time and coordinate dimensions, with original timestamp and channel geometry retained. There is no test-series nuisance fitting, oracle coefficient or automatic lag selection.

For scalar AR(2), the baseline model is

$$
X_i(t)-\mu(t)=\phi_1\{X_{i-1}(t)-\mu(t)\}
+\phi_2\{X_{i-2}(t)-\mu(t)\}+\epsilon_i(t).
$$

Independent-baseline *parametric bootstrap refits* approximate the joint nuisance coefficient sampling variation; stable coefficient draws and resampled whole-function innovations generate independent null sequences. The companion-root stationarity requirement is an explicit model boundary, not a rejection threshold. Unstable nuisance bootstrap coefficients are retained in the diagnostic rejection counts; extensive rejection fails closed. The nuisance distribution remains only an approximation, **not** a justified confidence distribution or posterior.

## Independent falsification design

New seed namespace `F5_INDEPENDENT_BASELINE_AR2_MODEL_STRESS_V1`; five generating processes:

- Independent Gaussian whole-function innovations.
- Strong scalar AR(1), true $\phi=.8$.
- Scalar stationary AR(2), true $(\phi_1,\phi_2)=(.64,.24)$.
- Stationary MA(1), which violates **both** fitted AR(1) and AR(2) dependence families.
- An intentionally nonstationary test with serial dependence changing from .35 to .85 during the tested series, while its independent baseline remains stationary at .35. It is a **true no-change-in-mean** counterexample that violates baseline-to-test transportability.

Each generator has 100 **independent true-null mean-stationary or dependence-shift datasets** and 50 fixed, injected mean-break alternatives, each evaluated under two fully fitted models. The first wave therefore comprises **750 independent test datasets** and **1,500 actual full fits** (1,000 null and 500 alternative method attempts), using 99 nuisance-bootstrap refits and 119 null simulations per test. Report every fitting failure, independent seed, nominal .01/.05/.10 false-positive fractions, exact binomial Monte Carlo intervals and original SHA256 evidence. Unit tests run on Python 3.11–3.13; five scientific shards run separately to avoid treating repeated methods on the same data as independent observations.

## Gates and interpretation

This AR(2) comparator is a focused statistical model-robustness study rather than a method that is robust to arbitrary unknown dependence. A favorable AR(2) true-null rate would be evidence only within the validated stationary AR(2) contract, not proof of nominal size or a reasonable default for eye-tracking data. Failure under MA(1), time-varying dependence, changing sensor variance, or participant hierarchy must be reported rather than tuned away. No automatic choice of AR(1) versus AR(2), alpha adjustment, nonstationary fallback, or user-facing API promotion is authorized.

`scientific_inference_qualified=false`, `unknown_dependence_inference_qualified=false`, `release_authorized=false`. The open [F5 scientific issue #256](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/256) is the scientific decision authority; protected main and 1.1.0 are unaffected.

## Completed first-wave 1,500-fit independent falsification results

The prespecified original [workflow #38000177988](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38000177988) completed **9/9 research jobs**: the full independent stationarity/unit-test matrix, five scientific generator shards, and a combined original SHA256 audit. Across **750 distinct independent test data-generating replicates and 1,500 real hypothesis-test fits**, no model raised a fitting error. The exact-source combined verified artifact is `11648842221`. Individual original-shard evidence is also retained.

The independent-baseline AR(1) and new AR(2) reference each used baseline length 80, test length 36, 99 independent-baseline nuisance refits and 119 whole-function null simulations per method fit. Coefficients were never estimated from the tested series; the two methods share exactly the same test dataset within each replicate. For nominal $\alpha=.05$, the true no-mean-change rejection results were:

| Data-generating truth | Estimated AR(1) | Estimated AR(2) |
|---|---:|---:|
| Iid Gaussian | 0/100 = 0% | 1/100 = 1% |
| Strong stationary AR(1), true phi=.8 | 3/100 = 3% | 3/100 = 3% |
| Stationary AR(2), true (.64, .24) | 15/100 = 15% | **9/100 = 9%** |
| Stationary MA(1), unmodelled | 0/100 = 0% | 11/100 = 11% |
| Nonstationary AR(1) transfer counterexample | **94/100 = 94%** | **94/100 = 94%** |

Every cell includes only 100 independent null datasets. Exact binomial 95% Monte Carlo interval for the AR(2)-fit rejection rate 9% under true AR(2) is 4.20%–16.40%, and for its MA(1) false rejection 11% is 5.62%–18.83%. The deliberately nonstationary mean-null result 94% has 95% exact Monte Carlo interval 87.40%–97.77%, indicating severe failure of baseline-to-test dependence transportability. **Changing autoregressive order does not fix dependence nonstationarity**.

Under the single fixed mean-break alternative, 50 independent datasets per process and method, the new AR(2) method rejected **7/50 (14%)** for the true AR(2) generator versus **19/50 (38%)** for the misspecified AR(1) method. Given the AR(1) true-null rejection of 15%, that higher alternative-rejection fraction cannot be interpreted as calibrated power. For stationary strong AR(1), both methods rejected 3/100 nulls and 40/50 and 41/50 alternatives, respectively. Under MA(1), estimated AR(2) rejected 11/100 true nulls while AR(1) rejected none, demonstrating different—not universally superior—model-conditional behavior.

**Formal research decision:** Neither estimated AR(1) nor estimated AR(2) is qualified as a generally valid unknown-dependence null. Keep the new AR(2) procedure explicitly experimental, without automatically selecting between models, altering p-value thresholds or claiming validity for MA/ARMA, participant hierarchy, changes in covariance over the test interval or nontransferable baseline laws. The next falsification programme requires an independent theoretical dependence-robust null construction with explicit assumptions and stable type-I rates across new datasets, plus sensitivity/power surfaces and baseline transferability assessment. Source negative evidence is retained; issue #256 and all release/inferential gates remain blocked.
