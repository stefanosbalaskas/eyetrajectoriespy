# W3 R11: paired observation-process decomposition before uncertainty promotion

!!! warning "Research-only counterfactual source comparison"
    R10 showed that resampling 48 people, rather than their individual
    gaze timepoints or trials, did **not** consistently restore 90%
    pointwise true-slope coverage. R11 asks which failures remain
    with the exact **complete simulated source** available and which
    are introduced by **observation loss**. The complete source is
    a simulation counterfactual, **not** a feasible reconstruction
    of real missing gaze. Nothing is released or automatically
    selected by this study.

## Source design and matched contrasts

Exactly **96 independently seeded generating blocks**, from fresh
master seed `202610131107`, each have **48 independent people**
and a declared unequal 1–3 genuinely asynchronous trials per
person. Each trial has different strictly increasing
jittered native observation times, and shared participant
random intercepts/slopes induce repeated-trial dependence.
Two paired known mean-generating truths are prespecified:
the baseline smooth condition-slope and the same original
source with a localized slope bump at nominal time 0.5.

Within each source block and generating truth, the **same
underlying complete sensor values, time vectors, participant
covariates, noise, trial allocation and loss uniforms**
produce four original observation mechanisms:

| Observation case | Rule for a contiguous eight-recording gap |
|---|---|
| **Complete** | No source record missing: known simulation reference |
| **MCAR** | Each original trial loses its middle eight samples with fixed 0.30 probability |
| **Observed-x MAR** | Gap probability `logistic(-0.85 + 1.20 x)`; x is observed |
| **Latent MNAR** | Gap probability `logistic(-0.85 + 1.20 x + 2.0 × hidden midpoint residual / 0.11)` |

Different mechanisms may mask different original
source times; all retained times/values must match
the original complete source **exactly**. No interpolation,
data-derived missingness diagnosis, person deletion, or
trial-as-independent-unit resampling is permitted.

The two fixed, already specified bases are **degree-five
Legendre** and **13-term cubic spline** (nine original
fixed interior knots from R9). Both use equal total
numerical weight per *participant* and pointwise
participant CR1 at the single prespecified slope
contrast, time 0.5 in response dimension x.

There are **96 independent generating blocks × two paired
truths × four paired observation mechanisms = 768 source
scenarios**. Each scenario has two model fits;
the same block is **not** eight independent replicates.
Complete-source fits are numerical counterfactuals
within the matched generating block, not extra
independent data.

## Prespecified decomposition and source-oracle checks

The scientific source ledger includes, *separately*:

1. The **known conditional-mean projection error**:
   fitted fixed basis evaluated at the midpoint minus the
   known generating slope, using source-known conditional
   means at that regime's actually observed timepoints.
2. The **full estimated slope error**: fitted original
   recorded-data midpoint slope minus known generating truth,
   including source noise/participant effects and selection.
3. The **paired observation-loss displacement**:
   estimated recorded-source slope minus the identical block's
   complete-source estimated slope, with the same fixed basis
   and underlying source. This measures *change under the
   observation mechanism* in the generating experiment,
   not an identified empirical causal effect.
4. The **paired projection displacement** versus the
   complete-source projection, separating selection of
   design/time support from the realized response effect.
5. **90% POINTWISE** known-truth inclusion under participant
   CR1, mean width, complete-function slope RMSE,
   95% Wilson Monte Carlo intervals and 3,000-resample
   paired block Monte Carlo intervals.

All 768 planned rows (including failures), the original
Matplotlib SVG, source commit identity and all four SHA256
hashes are retained. Ordinary CI assesses the correctness
of recorded native source subsets, independent numerical
least-squares/participant score oracles, 48-person
hierarchy, cross-version reproducibility and full
evidence completion—not whether statistical coverage
happens to be close to 90%.

The current supported common-grid W3 workflow must
continue to **reject all native irregular inputs**.
Research modelling uses only the existing isolated
source-only numerical reference implementation.

## Scope and decision boundary

The study quantifies **complete-vs-observed source
differences within its chosen synthetic generator**;
it does not identify the true observation mechanism
in real data, establish valid inverse-probability
weighting from observed records or eliminate latent
MNAR bias. It also cannot establish calibrated
whole-trajectory simultaneous intervals, general
Type-I error rates, a correctly specified mixed
functional model or automatic mean-basis selection.

Any finding that the complete-source case itself
under-covers would be evidence of an additional
uncertainty/mean/finite-participant limitation,
not a reason to hide or correct the result after
the fact. No desired method ordering or threshold
is used as a CI success condition.

```bash
python -m pip install -e ".[dev]"
python scripts/run_w3_r11_paired_observation_process.py \
  --out build/w3-r11-original
```

Keep [W3 inferential blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
and [missing/irregular support #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296)
open. Protected main and published stable **1.1.0**
remain unchanged; unpublished development
`1.2.0rc2.dev0`, `production_release_ready=false`.
No new public estimator, RC/tag or PyPI publication.
