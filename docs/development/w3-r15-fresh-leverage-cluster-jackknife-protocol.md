# W3 R15 — fresh finite-participant and leverage stress

!!! danger "Prespecified research simulation, not a qualified pointwise or simultaneous method"
    R14 showed that source covariance choice, rather than switching
    between t(47) and normal critical values, accounted for most observed
    90% *pointwise* inclusion-count differences on the original R13 data.
    R15 conducts an **entirely NEW independently seeded source study**,
    without reusing R13/R14 Monte Carlo blocks, to evaluate participant
    count and extreme observed-covariate leverage. No estimator will be
    selected by a favorable outcome.

## Independent simulation design

**96 new generating blocks**, master seed `202610131515`, each
containing up to 96 independent participants. Samples of
**24, 48, and 96 participants are nested** within source block,
with the same source random components, complete original
1–3 asynchronous trials and unchanged native timestamps.
The stable original smooth condition-slope generator uses
Gaussian participant random intercept (SD 0.08),
participant random functional slope (SD 0.045),
trial intercept (SD 0.025) and sensor noise (SD 0.045).
The true conditional mean is represented by both **fixed,
prespecified** Legendre-5 and cubic-spline-13 functions.

Within every block and participant-size cell, the same
source latent effects/noise/timestamps are used for two
predeclared observed-predictor conditions: an ordinary
`Uniform(-.95, .95)` participant covariate and a **two-person
high-leverage stress** resetting independent participants
0 and 1 to x=3.0 and x=−2.5, respectively, with all other
participant covariates unchanged. The complete observed
responses are generated from the same true slope *at
the substituted observed x*. Thus this is a deliberate
**predictor-distribution intervention within simulation**,
not post-hoc deletion or selective loss of outcomes.
Every recorded native timepoint and trial is retained;
no interpolation or imputation occurs.

Crossed comparison: **96 blocks × 3 participant sizes × 2
prespecified covariate regimes × 2 fixed mean bases = 1,152
source/model evaluations**. These are **96 independent
generating blocks**, NOT 1,152 independent datasets.
The two bases, sample sizes and predictor supports
share generating innovations within block.

## Predeclared covariance and critical-value comparisons

All five intervals use the **identical** weighted least-squares
estimate of the first-dimensional condition slope at
the one fixed midpoint time `t=.5`. Each source
participant receives total original numerical regression
weight one, distributed among original trial samples.
No trial or gaze point is counted as an independent
cluster.

| Method | SE construction | 90% pointwise reference |
|---|---|---|
| **CR1/t** | Native participant-aggregated WLS residual-score sandwich with original finite corrections | Student t(n−1) |
| CR1/normal | Exactly same CR1 SE, unchanged point estimate | Standard normal |
| **Delete-one-person jackknife/t** | Exactly refit original complete WLS after leaving each entire person (and all their trials) out, with `(n−1)/n` delete-one variance | Student t(n−1) |
| **Known Gaussian oracle/t** | Analytic original known-source conditional variance incorporating shared person intercept/slope, independent trial intercept and sensor noise | Student t(n−1) |
| Known Gaussian oracle/normal | Exactly same simulation-only oracle SE | Standard normal |

The **oracle requires the true generating variances** and is not
available from real observed gaze without modelling
assumptions. The delete-one-person jackknife is
*experimentally computed*, not yet a public package
estimator. No CR2 leverage-adjustment correction is
claimed; measured participant block leverage and
the genuine cluster jackknife are the prespecified
finite-cluster diagnostics. A separate CR2
implementation would require additional independent
leverage transformation/reference validation.

## Original source and numerical contracts

The original research workflow must verify:
- All 1–3 source trials per participant have exactly
  the generating native timestamps and fully observed
  data; current public complete-grid W3 **rejects**
  genuinely asynchronous trial input.
- Original regression weighted normal equations match
  independent weighted QR regression on the same actual
  source values, and grouped residual participant scores
  match independently summed original observations.
- Analytical source-known Gaussian midpoint-slope
  variance matches an independently assembled latent-
  component variance sum for the original 24-person
  source; full repeated-trial participant covariance
  is preserved, not pseudo-replicated.
- Source predictor leverage is measured as the
  maximum eigenvalue of the participant
  information-block hat operator and the mean of
  the first two independent person's block
  leverages. The high-leverage manipulation
  must demonstrably increase the first-two-person
  leverage in source contract tests.
- True mean projection bias, signed point error,
  90% *pointwise* inclusion, widths, SE/oracle
  ratios, 96-block Wilson 95% intervals and
  3,000-resample paired source-block inclusion
  contrasts are retained for each cell.
- Original source block is the Monte Carlo
  independent unit; no success or noncoverage
  is omitted, and no desired inferential
  performance is an engineering CI gate.
- Full **1,152-case original failure-inclusive JSON
  ledger**, source-audited scientific summary,
  original Matplotlib SVG, source checkout SHA
  and four SHA256 checksums are retained.

Scientific comparisons are descriptive finite-simulation
effects of original sample size, predictor leverage
and covariance method. The ordinary and extreme-x
generating regimes do not have identical
*conditional responses* because their x values
differ; they share innovations and original
timing, as required by the design.

## Scientific and release boundaries

Even a method that attains 90% pointwise truth inclusion
under this complete Gaussian generator has not
qualified full-trajectory **simultaneous** bands,
non-Gaussian observation models, latent-MNAR
correction, model-selection inference, real
device time synchronization or a fitted
functional random-effects covariance likelihood.
The 96 outer blocks yield finite Monte Carlo
uncertainty; multiple stress comparisons
are exploratory and not model-selection gates.

```bash
python -m pip install -e ".[dev]"
python scripts/run_w3_r15_fresh_cluster_leverage.py \
  --out build/w3-r15-original
```

Keep [W3 simultaneous coverage #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
and [missing native support #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
open. Stable 1.1.0 and unpublished dev `1.2.0rc2.dev0`
remain unchanged, with `production_release_ready=false`.
No public estimator, protected-main merge, RC,
release tag or PyPI publication is authorized.
