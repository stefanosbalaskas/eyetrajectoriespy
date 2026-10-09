# Independent computational checks and F5 dependence reference — research only

**Unpublished 1.2 methods. Not part of stable 1.1.0; scientific qualification
and release authorization remain false.**

## B6/B7 computational correctness

The full [B6/B7 long-chain comparison run #37969903148](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37969903148)
completed 96/96 actual Gibbs fits (48 independent prior-generated datasets
paired across 160/70 and 1200/600 warmup/draw schedules). Exact PR #253
CI passed 30/30. Even the longer fits had R-hat substantially above 1.01
and bulk effective sample sizes in the single digits for many identifiable
population parameters. Therefore **convergence is not qualified**.

This tranche adds **independent conditional algebra checks** using
directly stacked observation-row Gaussian regression to validate, without
reuse of the sampler's sufficient statistics:

- population-mean posterior precision and mean in B6;
- rank-2 loading posterior precision including row-major Kronecker ordering;
- B7 asynchronous x/y score posterior with different channel observation
  counts and distinct channel noise;
- B7 loading precision across sparse participant observations;
- Gaussian precision-Cholesky draw moments against analytic covariance.

Passing these checks would establish *conditional algebra correctness
only*, not joint posterior convergence. It neither demonstrates adequate
mixing in the mean/loading/latent-score funnel nor proves frequentist
coverage. After this check, the next Bayesian work remains reparameterized/
collapsed models, independent NUTS reference, chain-wise scalar SBC ranks
and independent held-out recovery. No analytic conditional test alone
qualifies Bayesian inference.

## F5 experimental AR1 innovation-permutation comparator

The first wave's dependent F5 weak-block bootstrap showed nominal 5%
null rejection **100% / 42.67% / 2.33%** at block lengths 2/4/8,
respectively, under stationary AR(1) phi=0.8, 300 independent nulls each.
See [blocker #256](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/256).

A distinct comparator at
`eyetrajectoriespy.research.functional_changepoints_ar1_reference`
now generates a stationary scalar-AR(1) null by permuting entire fitted
innovation vectors **without replacement**, and then reconstructing
ordered whole curves using an **externally specified scalar phi**.
This keeps gaze function-time coordinates and correlated 3D/2D channels
together, and performs no timestamp interpolation. The original
`detect_ordered_functional_changepoint(...dependence="weak_block")`
remains unchanged.

**Critical identification limitation:** test-series-only estimation
of phi is often downward biased for 36 curves and can be anti-conservative.
The new inferential comparator therefore requires a prespecified/independent
baseline phi or the actual known phi in a simulated experiment. It is
**not an operational calibrated test for unknown dependence**. The
separate `estimate_scalar_functional_ar1()` returns only a descriptive
coefficient and explicitly rejects inferential qualification.

Scientific comparison protocol: entirely **fresh master seed 20261120**
(not the empirical validation data from 20261009), 200 independently
generated true null and 100 one-break alternative datasets for each
true phi 0, .35, .8; the old weak-block (block 4, independent mode
for phi=0) and the new *oracle-known-phi* comparator are run on
the same 900 generated trajectories for a total of 1,800 tests,
199 bootstraps each. All failed fits, case-level seeds, exact Monte
Carlo binomial intervals at alpha=.01,.05,.10, and SHA256 evidence
are retained.

This experiment is an **oracle validity check** for a stronger conditional
model, not a comparison that can justify routine use with unknown real-world
dependence. Even satisfactory oracle null rejection must be followed by
independently estimated phi uncertainty, non-AR1 dependence, sample-size
and innovation-sensitivity tests before **any** inference qualification.

## Engineering and release boundaries

The 13,600-attempt `research-empirical-calibration-wave1.yml` workflow has
been changed from pull-request/docs-triggered execution to **manual
workflow_dispatch only**. This avoids rerunning the immutable original
study for a documentation or ledger update. A new scientific study
requires a separate declared protocol and source head, not a silent replay.

The exact source-ledger in
`EMPIRICAL_SCIENTIFIC_QUALIFICATION_20261009.json` records the
96-fit long-chain convergence failure and the limits of these changes.
Stable/root exports are unchanged. Protected `main` stays unchanged
and the 1.2 research candidate is not authorized for publication.


## Newly recovered F5 empirical comparison — actual independent data

Exact source [run #37975560959](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37975560959)
fit **1,800 F5 tests**, with zero model exceptions. The source final
post-fit audit failed because `pd.read_csv` converted the scientific
`"null"` truth label to missing; the source artifact
`11639020647` remained immutable. The descendant
[recovery workflow #37976469318](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37976469318)
passed, retained result artifact `11638977236`, verified all source
SHA256 checksums, all 900 matched datasets and all 12 scenario summaries,
and refitted **zero** models.

**At alpha 0.05, 200 independent fresh no-change datasets per regime:**

| Generator | Prior experimental method | New reference with known oracle phi | Exact 95% MC interval for reference |
|---|---:|---:|---:|
| iid Gaussian phi=0 | 7/200 (3.5%) | 6/200 (3.0%) | 1.11–6.42% |
| weak Gaussian AR1 phi=0.35 | 0/200 (0%) | 8/200 (4.0%) | 1.74–7.73% |
| strong Gaussian AR1 phi=0.80 | 99/200 (49.5%) | 16/200 (8.0%) | 4.64–12.67% |

Under the deliberately strong one-break synthetic alternative,
**both** comparator methods rejected 100/100 per regime. No modest
effect sizes or multi-break localization qualification follows.

**Scientific interpretation:** the independent conditional-AR1
comparator improves false-positive behavior over the legacy block-4
bootstrap on these specific regimes. **It does not achieve demonstrated
nominal calibration**: strong-AR1 8% has substantial MC uncertainty
and the procedure used the **actual known generating phi**, which
cannot generally be supplied for observed human gaze data. Its
model assumes a single shared stationary scalar AR1 coefficient and
iid whole-function innovation vectors, not arbitrary residual
nonstationarity, device artifacts or hierarchical trials. The
original dependent F5 test therefore remains scientifically blocked
under [issue #256](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/256).

Next scientific evidence must include independently baseline-estimated
phi uncertainty (with no leakage from the test sequence),
non-AR1 dependence stress and adequately replicated true nulls.
Do **not** choose coefficients or bootstrap schemes merely to make
the same simulated null rejection match 5%.
