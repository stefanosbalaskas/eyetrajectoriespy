# W3 R65 — immutable R64 primitive-block paired detection uncertainty

**Research-only read-only post-hoc diagnostic. Zero NEW independent original source blocks, zero NEW nuisance REML optimizations, no R64 source regeneration, no reference recalibration, and no public inference API.**

## Purpose and evidence

The [R64 original source workflow #39121431222](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39121431222) passed 12/12 science jobs and original exact-head CI 25/25. The separately required immutable [R64-A independent source audit #39151655810](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39151655810) passed **4/4** numerical and original-data jobs, revalidating 3 SHA256 source members, 192 paired source identities, 12,096 conditional H0 Gaussian pseudodraw fit records, 24,576 nested models, 73,728 original optimizer starts and maximum selected physical projected KKT **0.00069147** below 0.001.

The original six-cell R64 candidate rejection fractions, with only **32 independent primitive generating blocks**, were ordinary zero/half/full **3/32, 3/32, 4/32** and extreme **2/32, 4/32, 8/32**. Because *every* block supplies both leverage conditions at all slope levels, comparing six independent Wilson confidence intervals does not exploit the experiment's matched source structure.

R65 performs a focused descriptive post-hoc analysis: quantify the **paired within-source candidate detection change** from zero to half, half to full and zero to full for both leverage conditions, plus the matched cross-leverage difference in full-minus-zero change. Original source IDs and original conditional-bootstrap candidate rejection flags are read only from the frozen archive.

## Frozen analysis plan and independent-unit definition

- Input: exactly original immutable R64 [source archive #12136512850](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39121431222/artifacts/12136512850) at pinned scientific PR merge SHA `ebe731c3db6a491f1d6b494d91d05143ecc9ee35`. The independent R64-A standard-library verifier is **required to pass first** on this archive, checking SHA256, all original likelihood/KKT decisions and original p-rank provenance. A new R65 output is **not original R64 empirical evidence**.
- Original source sampling unit: **32 independent primitive Gaussian generating blocks**, each with exactly six repeated support×slope observations. **Never** treat 192 matched cases or 12,096 conditional H0 pseudodraws as independent resampling units.
- For each leverage support, each within-block contrast `Δ_b = I(reject at later slope)-I(reject at earlier slope)`, taking values -1, 0 or 1, is recorded. Preserve concordant rejections and discordant earlier-only/later-only, and all 32 matched block identifiers.
- For the cross-leverage full-minus-zero comparison, compute `D_b=[I_extreme(full)-I_extreme(zero)]-[I_ordinary(full)-I_ordinary(zero)]`, range -2 to +2. This preserves participant/source pairing when summarizing the apparent leverage interaction.
- If any original conditional p or numerical status is missing, retain the **fixed 32-block denominator**, report fully conservative missing-contrast lower/upper bounds, and **withhold** paired bootstrap CI instead of silently dropping refused blocks.
- Exploratory paired-block nonparametric resampling: `20,000` entire-source-block bootstrap replicates, pseudorandom seed `202610186565`, all six rows of each sampled primitive block transferred together to every contrast and the interaction. Compute deterministic empirical 2.5th and 97.5th percentile boundaries with linear rank interpolation. These are **post-hoc block-bootstrap descriptive uncertainty ranges**, not validation of original candidate test calibration, and certainly not the original 63 fitted-null Gaussian pseudodraws.
- **No new hypothesis-test p-value or confirmatory superiority claim.** These contrasts were chosen after seeing the R64 marginal estimates. Finite-sample bootstrap percentile intervals can be inaccurate near sparse Bernoulli boundaries and with 32 matched primitive source units; interpret conservatively.

## Evidence available before this analysis

The independently verified original archive's zero-versus-full discordance is ordinary **1 full-only / 0 zero-only**, hence a **+1/32 = +3.125 percentage-point** within-block candidate rejection change, and extreme **7 full-only / 1 zero-only**, hence a **+6/32 = +18.75 percentage-point** change. Their matched difference is **+5/32 = +15.625 percentage points**. This comparison is descriptive; original archived source pairs, not separate Bernoulli denominators, determine the uncertainty. Confidence range outputs are **not asserted until the required exact-original analysis workflow completes**.

## Release and science boundaries

R65's numerical outputs are wholly derived from existing R64 data, **not independent new external replication evidence**. No source is discarded for numerical failure, and R64/R63 original scientific archives and thresholds remain frozen. The 5% null and positive alternatives are based on a narrow specified Gaussian mechanism; the candidate test is **not qualified to control 5% Type I error or to have calibrated statistical power**. Fitted-working-covariance CR2 90% pointwise intervals and simultaneous function-wide confidence bands, non-Gaussian robustness, original latent-source audit and MAR/MNAR observation mechanisms remain unqualified. Research issues #289 and #296 stay open. Protected main, stable 1.1.0, release 1.2, API, tags and PyPI stay untouched.
