# W3 R3: independent 192-block confirmation under selected error regimes

!!! danger "Research-only confirmation, not a stable inference approval"
    Prior W3 studies reveal serious undercoverage of nominal 90%
    simultaneous slope-function bands, particularly in small samples.
    This independent replication tests whether an experimental
    refitted-HC1 wild-bootstrap reference improves truth inclusion
    reproducibly. It does **not** qualify nominal coverage or replace
    an existing supported estimator.

## Independently prespecified design

Previous [R2 stress study](w3-fresh-heteroskedastic-ar1-stress-results.md)
evaluated 24 independently seeded source blocks per design across
four regimes and two nested sample sizes. Its strongest negative
case was n=36 independent curves with joint condition-dependent
heteroskedasticity and stationary AR(1): original fixed-HC1
simultaneous bands covered the generating slope over the full grid
in **5/24** datasets, while the exploratory refitted-HC1 reference
covered in **20/24**, with wider intervals.

The new R3 study uses a **fresh seed family `202610122177`** and
**192 independent source datasets per scientific design**, not
recycled original R2 data. It deliberately concentrates on four
prespecified design × noise settings (no selection after seeing R3
outcomes):

| Independent-unit design | IID reference | Joint heteroskedastic+AR(1) stress |
|---|---|---|
| 36 independent curves | 192 datasets | 192 datasets |
| 36 independent participants, three trials each | 192 datasets | 192 datasets |

There are **384 independently generated design-specific block sources**
(192 independent blocks *per source design*), while the two error regimes
reuse condition assignments and innovations within each block.
The **768 fitted dataset/scenario rows are not 768 independent
replications**. All models share the same known generating intercept
and slope coefficient functions over 31 observed times and two
dimensions.

Joint stress multiplies error SD by `0.60 + 1.20 × ((x+.95)/1.90)`
and applies stationary within-trial AR(1) filtering with `ρ=0.70`.
Participants retain a smooth participant random intercept and three
repeated trials, averaged to one independent inference unit before
OLS fitting. This is a between-participant estimand, not a functional
mixed model for trial-varying predictors.

## Fixed, paired statistical comparison

Every source dataset is evaluated using its existing OLS fit and
independently calculated HC1 pointwise SE. The two simultaneous
slope-function references share **199 identical Rademacher unit-level
wild pseudo-responses**, fixed known coefficient truth and original
sample. The only difference is the denominator in the bootstrap
maximum-t statistic:

- **Supported fixed-HC1 reference:** bootstrap OLS coefficient
  deviations divided by the original-data HC1 SE at each observed
  time/dimension. Independent NumPy algebra and the actual package
  `function_on_scalar_simultaneous_bands` output must agree.
- **Experimental refitted-HC1 bootstrap-t:** identical bootstrap
  coefficient deviations divided by the HC1 SE recomputed on each
  bootstrap pseudo-dataset. The observed truth statistic retains
  the original-data HC1 denominator.

The nominal target is **90% full-grid slope-function truth inclusion**
at all 31 times and both dimensions, not average pointwise-cell
coverage. Report both outcomes separately alongside mean
time/dimension pointwise-cell inclusion.

## Source-audited outcomes and Monte Carlo precision

Prespecified outputs are the *entire* 768-case ledger, independent
OLS/HC1 and band-max numerical checks, all failures and missing
cases, truth-inclusion counts, band widths and critical values.

For each of the four design×regime settings:

1. Report the observed full-curve inclusion count/192 separately
   for fixed-HC1 and refitted-HC1, with **Wilson 95% Monte Carlo
   intervals** calculated over independent generating blocks.
2. Report each *paired* refitted-minus-fixed inclusion difference,
   including rescue/loss/nonchange counts, with a **2000-resample
   block-level bootstrap 95% interval** over paired outcomes.
3. Report both methods' mean critical values and mean of dataset
   median simultaneous-band widths. Better coverage through
   unnecessarily wider bands must not be concealed.
4. Count every failed/missing case in the attempted denominator,
   preserve the source exception and show completed-only intervals
   separately where necessary. Preserve original source commit,
   JSON files, original SVG and SHA256 checksums.

**Important:** the same block's two regimes are *not* independent;
bootstrap resampling is by block, never time cell, repeated trial,
or wild-bootstrap draw. This R3 study was specified before outcomes
were viewed. The prior 24-block study is exploratory and should not
be pooled naively with this fresh study when interpreting evidence.

No coverage rate or improvement is an automatic CI pass criterion.
The scientific evidence can falsify nominal calibration, even if
all engineering tests pass. Even nominal-looking results at n=36
do not establish broad validity for nonignorable missingness,
irregular gaze sampling, device dropout, participant recruitment,
nonlinear mean misspecification or more extreme heterogeneity.
These remain future, separately specified studies.

## Reproduce original source evidence

```bash
python -m pip install -e ".[dev]"
python scripts/run_w3_192_block_independent_confirmation.py \
  --out build/w3-192-block-confirmation
```

See [open W3 scientific blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
and [development roadmap #286](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/286).
Bayesian B6/B7 #255 and dependent-data F5 #256 remain distinct.

Version governance: published stable **1.1.0** remains unchanged;
core source remains **`1.2.0rc2.dev0`** with
`production_release_ready=false`. No literal release candidate,
release tag or PyPI upload is authorized.
