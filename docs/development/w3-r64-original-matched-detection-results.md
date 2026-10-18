# W3 R64 — original matched zero/half/full random-slope detection results

**Completed original Gaussian simulation. Exploratory candidate rejection sensitivity, NOT qualified 5% test power.** Source [PR #378](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/378), [original workflow #39121431222](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39121431222), [immutable original source archive #12136512850](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39121431222/artifacts/12136512850); original source GitHub Actions PR-merge checkout `ebe731c3db6a491f1d6b494d91d05143ecc9ee35`.

## Prespecified complete original-source denominator

The original study ran 32 NEW independent Gaussian primitive blocks with n24 participants each, paired ordinary/extreme dependent predictor support and three matched slope-level multipliers `m = 0, 0.5, 1`. Each block's nuisance noise and latent slope innovations are retained across the matched levels; the simulated source response deliberately removes a known fraction of the random-slope component. The **structural generating slope variances** are, respectively, `0`, `0.00050625` and `0.002025` (coefficient variance units).

There are **192 matched source cases but only 32 independent generating blocks for each of six support×slope conditions**. Every source receives 63 conditional fitted-null Gaussian pseudoresponses, with the originally unchanged exact-zero H0 versus nonnegative H1 REML nuisance covariance completely refitted on every pseudoresponse. The original aggregate has **192/192 accepted original source fits, 12,096/12,096 accepted bootstrap draw fits** (2,016 per condition), 24,576 nested H0/H1 model fit positions and 73,728 optimization start records, with **zero numerical refusals**. Full original workflow **12/12 science jobs passed** and source exact-head CI **25/25 workflows passed**. The original R64 branch preserves all recorded source/draw/start failure positions and has 3 SHA256 aggregate members.

## Complete six-cell empirical candidate rejection fractions

Candidate fixed rule is `p=(1+#(T_boot≥T_observed))/64 ≤ 0.05`, requiring 63/63 bootstrap nested fits accepted, with no threshold tuning after R59–R63. The classical comparison is the unchanged **candidate**, not validated, half-zero/half-χ²(1) likelihood-ratio critical value `T>2.70554345409542`.

| Predictor leverage | True slope SD multiplier | True slope variance | Fitted-null bootstrap | Bootstrap Wilson 95% MC interval | Classical candidate |
|---|---:|---:|---:|---:|---:|
| Ordinary | 0 | 0 | **3/32 = 9.38%** | 3.24–24.22% | 3/32 = 9.38% |
| Ordinary | 0.5 | 0.00050625 | **3/32 = 9.38%** | 3.24–24.22% | 3/32 = 9.38% |
| Ordinary | 1 | 0.002025 | **4/32 = 12.50%** | 4.97–28.07% | 3/32 = 9.38% |
| Extreme | 0 | 0 | **2/32 = 6.25%** | 1.73–20.15% | 1/32 = 3.13% |
| Extreme | 0.5 | 0.00050625 | **4/32 = 12.50%** | 4.97–28.07% | 3/32 = 9.38% |
| Extreme | 1 | 0.002025 | **8/32 = 25.00%** | 13.25–42.11% | 9/32 = 28.13% |

All Wilson intervals measure the uncertainty across **32 independent primitive source blocks within a cell**. They do not establish valid statistical power or calibrated 5% error control across covariance laws.

## Interpretation and research priorities

Original source outcomes indicate **weak detection sensitivity in the ordinary-leverage design**: 9.38% at structural slope zero and half, and only 12.50% at full variance. Under extreme leverage, detection grows from 6.25% at zero to 12.50% at half and 25.00% at full, consistent with signal being more detectable at larger participant predictor scale, but with only 32 independent blocks/cell and wide confidence limits. The matched block design supports a within-block comparison, **not** six independent datasets of size 32 nor an unconditional claim that all alternative effects are monotonically detected within every matched source. A nonzero slope can still produce no rejection, and false rejection under exact zero is an error, not detection.

The R64 source archive contains original numerical fit/status, nested deviance, Gaussian pseudodraw seed and structural slope metadata but **not original complete native latent participant Gaussian innovations**, so its independent archive audit can validate recorded algebra/decisions/provenance but cannot re-generate or prove the original source law. [Independent R64-A draft PR #379](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/379) is separately required to reconstruct the original immutable numerical archive; its original-data result must not be assumed merely because the first three contract/fixture jobs passed.

R64 remains a **narrow Gaussian detection sensitivity result**. It does not establish statistical test power at a calibrated 5% level, control under non-Gaussian/heteroskedastic covariance or MAR/MNAR gaze loss, or 90% estimated-working-covariance CR2 pointwise or simultaneous functional coverage. No valid general pointwise/simultaneous 90% inference API, release or PyPI promotion follows.

Scientific issues #289 and #296 stay open; protected `main` remains unchanged and version 1.2 remains unpublished.
