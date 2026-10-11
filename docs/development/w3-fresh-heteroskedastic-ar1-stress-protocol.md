# W3 R2: fresh heteroskedasticity × temporal-AR(1) calibration stress

!!! danger "Prespecified research pilot, not calibrated 90% inference"
    The original fixed-HC1 maximum-statistic wild-bootstrap bands showed
    substantial 90% undercoverage. A refitted-HC1 bootstrap-t diagnostic
    improved some simulation cells, but has **not** been established as a
    calibrated method. This new study must retain all undercoverage.

## Statistical question

How robust is the apparent small-sample studentization improvement to
known departures from independent homoskedastic observation errors?

This is a **fresh independent-block study**, using new source seed
`2026101263` rather than any previous W3 seed namespace. All source
blocks and scientific settings are fixed in code before evaluating results.

The design has 24 independent generating blocks *per scientific source
design* (independent trajectories, participant-aggregated trajectories).
Within each block, the unit counts **36 and 144 are nested**, and the
following **2 × 2 error mechanisms share the same underlying innovations**:

| Marginal variance structure | Temporally independent | Within-curve AR(1), ρ = 0.70 |
|---|---|---|
| Constant error variance | IID reference | AR(1) temporal dependence |
| Condition-dependent heteroskedasticity | Heteroskedastic | Joint heteroskedastic + AR(1) |

Condition-dependent error SD is `0.60 + 1.20 × ((x + .95) / 1.90)` for
generating `x∈[-.95,.95]`. Independent innovations are generated
once per block; under AR(1) they are filtered with stationary initialization,
so marginal error variance remains controlled. The participant design has
three source trials per unit and a smooth participant random intercept,
with participant (not trial) used for inference. The variance scaling is
also applied to participant-specific intercept noise under heteroskedasticity.

**384** source regression fits (24 blocks × 2 designs × 2 nested sample sizes
× 4 related error regimes) form only **24 independent block indices per
source design**, not 384 independent replications. Scenarios and unit sizes
are strongly correlated within block. Mean coefficients are identical
across error structures; only the noise process changes.

## Prespecified uncertainty comparison

Both methods evaluate nominal **90% simultaneous slope truth inclusion**
over the same 31-point × two-dimension observation grid. All cells use
**199 identical Rademacher wild multipliers per independent unit**.

- Existing fixed-HC1 method: divide bootstrap coefficient deviations
  by original-data HC1 pointwise SE; exact matched actual package
  `function_on_scalar_simultaneous_bands` output must agree.
- Investigational bootstrap-t: refit the OLS coefficient and recompute
  HC1 pointwise SE for each exact same wild pseudo-sample; divide the
  bootstrap deviation by its new HC1 SE. The truth statistic retains
  the *original-data* HC1 denominator.

Independent NumPy least-squares and HC1 oracles must agree with the W3
workflow at tolerance 2e-10. The generating source and bootstrap weights
are held fixed across reference methods; regime and n contrasts share
innovations rather than introducing independent-data confounding.

For each cell preserve coefficient/SE oracle differences, original
inference-unit counts, both critical values, paired truth inclusions,
pointwise-cell inclusion, median simultaneous band widths and any error.
The source-run ledger must be **failure inclusive**, and the workflow
must not treat low coverage as an engineering failure. Original JSON,
source commit, SVG plot and SHA256 fingerprints are retained as an
artifact. Summary truth-inclusion rates use 24 *block-level* datasets
per design/regime/unit count and Wilson Monte Carlo intervals, rather
than treating cells inside a block as independent.

## Scientific interpretation limits

This is a modest, controlled finite-sample exploration—not a method
selection study or a nominal calibration certificate. Coverage estimates
from 24 datasets per design and regime have substantial uncertainty.
AR(1) dependence is specified within time for each independent
curve/participant; the participant design remains dependent across
repeated trials due to its shared participant intercept. This does not
cover nonignorable dropout, irregular timing, unequal trials or true
eye-tracking sensor artifacts. A later independent study must examine
larger replication counts and realistic observed-gaze conditions.

Source command:

```bash
python scripts/run_w3_heteroskedastic_ar1_stress.py \
  --out build/w3-heteroskedastic-ar1
```

[Prior W3 bootstrap-t nested-unit evidence](w3-bootstrap-t-nested-unit-count-results.md)
is an input, not a basis for changing inferential APIs. [W3 scientific
blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
remains OPEN; Bayesian #255 and F5 #256 remain separate.
Stable 1.1.0 is published, core source is unreleased
`1.2.0rc2.dev0`, and `production_release_ready=false`.
