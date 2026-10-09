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
