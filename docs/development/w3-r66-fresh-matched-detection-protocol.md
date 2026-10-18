# W3 R66 — prospective 128-independent-block matched positive-slope detection replication

**Research only. This experiment is not certification of a 5% variance-component hypothesis test, statistical power, pointwise 90% CR2 inference, simultaneous confidence bands, or a public API. No release authorization.**

## Why an independent R66 experiment

The [R64 original 32-block study](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/378) and independent [R64-A source audit](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/379) showed exploratory Gaussian null-bootstrap rejection counts under zero/half/full random-slope standard-deviation multipliers:

| Source leverage | Zero | Half | Full |
|---|---:|---:|---:|
| Ordinary | 3/32 | 3/32 | 4/32 |
| Extreme | 2/32 | 4/32 | 8/32 |

The [R65 matched-block analysis](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/380) rechecked the immutable R64 source archive and resampled **intact original source blocks**, rather than mistakenly regarding 192 six-cell cases as independent. For the matched zero→full changes, ordinary was +1/32 (+3.125 pp), extreme +6/32 (+18.75 pp), and their difference **+5/32 (+15.625 pp)**. Its post-hoc 95% whole-block percentile interval **−3.125 to +34.375 pp crosses zero**. These source-derived estimates suggested a possible leverage difference but could not establish it.

R66 prospectively freezes the SAME source model and matched zero/half/full contrasts on **128 newly generated, independently seeded primitive Gaussian source blocks**, with all design choices frozen before inspecting original R66 outcomes. R66 is not a resampling extension of the old 32 R64 blocks.

## Frozen design and scientific decision rule

- New independent generating-source master seed **202610186666**, new Gaussian fitted-null pseudodraw seed **202610186667**, and separate primitive-block resampling seed **202610186668**, all disjoint from R64/R65.
- **128 independent primitive Gaussian generating blocks**, each with **24 participants** and native irregular repeated trials; each primitive is observed in six paired conditions (ordinary/extreme predictor leverage × zero/half/full random-slope standard-deviation multiplier).
- Exact original random-slope SD **0.045** with frozen multipliers **0, 0.5, 1**: structural variance **0**, **0.00050625**, **0.002025**. Within primitive block and leverage condition, the original intercept, sensor noise, trial innovations, design/timestamps and Gaussian slope draw are identical across the three levels; **only the slope-innovation amplitude is modified**. The two leverage supports remain paired within primitive block.
- Preserve the original R57/R63 exact-zero (H_0) versus nonnegative (H_1) Gaussian REML, its fixed two H0 / four H1 starting solutions, physical projected KKT ≤ **0.001**, likelihood/objective restrictions, and the same Gaussian fitted-H0 covariance nuisance-refitting bootstrap. Every conditional H0 pseudodraw fully refits both nested nuisance covariance models.
- Per original case, freeze **63** independent fitted-H0 Gaussian pseudoresponses and the add-one conditional p-value `p = (1 + number of bootstrap LR statistics >= observed LR statistic) / 64`, only if the original and all 63 bootstrap nested fits are accepted; nominal 5% rejection means `p <= 3/64 = 0.046875`. The unchanged classical mixture cutoff (T>2.70554345409542) is retained descriptively. No source filtering, redraw, threshold tuning or post-data method selection.

## Prospective primary matched estimand

For each truly independent source block (b) and leverage (s), define the observed binary **candidate-test** decision (I_{b,s,l}) at slope level (l), after complete 63-draw computation. The primary planned comparative diagnostic is:


`D_b = [I_extreme(full) - I_extreme(zero)] - [I_ordinary(full) - I_ordinary(zero)]`

Its primitive-block mean can range from −2 to +2. The ordinary/full-minus-zero and extreme/full-minus-zero changes and the zero→half / half→full changes are secondary descriptive contrasts. The method compares **candidate rejection behavior under the stipulated Gaussian source**, not power of an independently qualified 5%-size test, and does not establish a causal benefit from manipulating observational leverage.

Prespecify **20,000** percentile bootstrap replicates of **128 whole primitive source blocks**, seed **202610186668**, resampling all six condition outcomes together in every replicate. Record a deterministic 2.5–97.5% percentile range for each matched contrast and the primary difference-in-differences. These ranges describe Monte Carlo uncertainty in this specific simulation design; they are not general hypothesis-test calibration guarantees or confidence intervals for real gaze trajectories.

If any of the six paired cases is numerically refused, retain the original **128-block denominator**, report conservative complete-versus-missing contrast bounds using each contrast's attainable range, and **withhold** its paired-block percentile interval rather than conditioning on a favorable survivor population. Always report per-cell all-source inclusion/rejection counts, Wilson source-level uncertainty, accepted/refused fits and complete draw counts separately.

## Frozen computational workload and provenance

| Item | Count |
|---|---:|
| New independent primitive blocks | **128** |
| Paired source cases: 128 × 2 leverage × 3 slope levels | **768** |
| Null-Gaussian pseudoresponse/refit attempts: 768 × 63 | **48,384** |
| Nested H0/H1 fits, original + pseudodraw: 2 × (768 + 48,384) | **98,304** |
| Original individual nuisance optimizer-start positions: 6 × (768 + 48,384) | **294,912** |
| Source shards | **32** nonoverlapping shards of four primitive blocks |
| Frozen intact-primitive resamples | **20,000** |

Each original shard retains complete source-case, numerical fit, draw and start positions, checkout SHA and SHA256 hash of exact UTF-8 response ledger bytes. Only an **exactly complete** original 32-shard, same-checkout, same-seed and collision-free aggregate is accepted. Failed or missing source positions remain refusals; checksum mismatch, duplicate cases and missing shards must fail closed. The complete original aggregate must be archived with a final SHA256 manifest.

The three-version (Python 3.11–3.13) contract workflow gates all original science shards. No empirical R66 detection result or calibrated interaction claim should be reported until **all** original science shards and original complete evidence aggregation pass. Independent original-archive re-audit is a separate downstream requirement before describing the full study as independently verified.

## Boundaries and release hold

R66 evaluates one family of fully observed, Gaussian irregular-repeated-trial designs with 24 participants per independent source. It neither resolves fitted working-covariance CR2 90% pointwise undercoverage nor simultaneously calibrated whole-function confidence bands, random-effect variance-component robustness to wrong covariance families, complete-participant missingness or response-dependent MNAR gaze loss.

Keep open scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296). Preserve original unfavorable R64/R65 results. Do **not** merge into protected main, promote a supported inference API, publish version 1.2, create a release tag, or upload to PyPI/TestPyPI.

**Prospective design freeze: before the first original R66 outcome.**
