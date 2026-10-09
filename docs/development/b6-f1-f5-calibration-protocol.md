# Scientific calibration extension: B6, F1 and F5 (unpublished)

This validation tranche builds on [B6 draft PR #243](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/243).
It is **not** a scientific qualification decision, a version qualification, or permission
to publish 1.2. The 1.1.0 stable implementation and frozen root API are unchanged.

## Evidence lineage

| Source | Exact pre-extension GitHub head | Verified engineering outcome |
|---|---|---|
| F1–F6 #227 | `d48c939b01fbfa19f0e060902b6a61ebddbe7aa6` | 27/27 success |
| D1–D5 #235 | `013cd05d93a5edeb8515d4f3afce22e44d67c9a9` | 27/27 success |
| Bayesian B5–B10 #237 | `2a7a3c03211cf4e4754b96406563e4d8b0a1acd2` | 32/32 success |
| Native learned B6 #243 | `e7a972ae4f09c30d2ac56429e77da54b38ab3661` | 27/27 success |

These are **different** workflow matrices. The source-head success records do not
transfer to the new follow-on branch or to inferential qualification.

## B6: prior-generated calibration and stress

`python scripts/run_b6_population_calibration_grid.py --replicates 8 --draws 60 --warmup 120 --out build/scientific-b6`

Three **matched-prior/likelihood** scenarios are: rank-1, rank-2 and
rank-2 with heterogeneous irregular observation densities. Here the
mean/loadings are drawn from precisely the Gaussian priors assumed by the
sampler, the participant scores are standard Gaussian, and observation
errors are sampled under the assumed iid Gaussian likelihood. Every
replicate refits the full learned-population Gibbs procedure.

Three additional scenarios are **model stress, not SBC**: an exactly
near-tied rank-2 population eigenspace on the declared evaluation grid,
a true noise SD twice the fitted SD, and a true loading-prior SD twice the
fitted SD. They must not be pooled with matched calibration.

Assess the 90% *pointwise marginal* posterior intervals for the population
mean and population covariance diagonal at a preregistered time location.
Report coverage conditional on successful fits **and** the number of
attempted/failed fits. Retain a Monte Carlo interval across independent
simulation repetitions; a point estimate from 2 or 8 runs is not evidence
for acceptable nominal coverage.

A rotation-invariant subspace projector error is calculated from the
population covariance eigenspaces. An exactly tied rank-2 eigenspace does
**not** identify two individually ordered eigenfunctions; report the
subspace rather than arbitrary loading signs/rotations.

One wholly new, untrained participant is generated per replicate. Posterior
predictive **marginal** 90% intervals incorporate population covariance and
observation error, evaluated at irregularly selected grid nodes. The five
observations from that one participant are correlated; the pooled
observation-level coverage tally has **no binomial Monte Carlo CI** and
cannot be called joint trajectory coverage.

Current B6 limitations remain: fixed rank, fixed spline basis, fixed noise,
fixed prior scales; no participant/trial hierarchy, no learnt eigenfunction
identity, no registration, and no definitive chain mixing or SBC-rank study.
An executable two-chain fit is not convergence evidence. A separate
long-chain, repeated-seed Rhat/ESS/rank-SBC programme is still required.

## F1: repeated full sparse refits

`python scripts/run_f1_f5_scientific_stress.py --f1-replicates 8 --f1-permutations 199 --f5-replicates 25 --f5-bootstrap 199 --out build/scientific-f1-f5`

All F1 trials invoke the **actual sparse-MFPCA pooled-score permutation
pipeline**, not the isolated score-only permutation kernel. The scenarios
include balanced groups, unequal allocation with heteroscedasticity,
repeated participant curves with intact unit resampling, and low sampling
density. Each scenario has a null and a known effect. Fit failures remain
in `f1-cases.csv`; rejection fractions conditional on fitting are not
unconditional false-positive rates when missing fits are selective.

The unequal-heteroscedastic null deliberately violates the strict
permutation-exchangeability assumptions and must be treated as a failure
stress, not as a null under which exact randomization inference is expected.

## F5: weak dependence and block-length sensitivity

For independent curves and heavy-tailed iid curves, run independent-mode
ordered whole-function CUSUM. For stationary AR(1) Gaussian ordered
curves, run weak-block resampling at block lengths 2, 4 and 8 under
moderate and strong dependence. The generated AR process has stationary
marginal variance matched to the independent innovation scale. Assess
no-break, single-break and two-break data-generating scenarios.

The current estimator reports a **single best split**. Two-break
simulation is an adversarial case, not implementation or verification of
multiple-break estimation. Repeated-patient/trial dependence, evolving
variance and genuinely nonstationary nulls still need dedicated modelling.

## Replication plan and interpretation

A first engineering CI run uses only two replicates per design to check
execution, output shape and failed-case retention. It provides no size,
coverage or power qualification. Before a scientific decision, preregister
a fixed full grid, effect magnitudes, seeds, tolerances, long-chain
diagnostic criteria and a computational budget. As an initial *planning
target*, use at least 1,000 independent null replications per critical F1
and F5 null scenario, 500 alternative replications for power, and at least
400 model refits per matched B6 scenario, then expand as required by
Monte Carlo uncertainty. These are suggested study sizes, **not**
completed experiments or automatic passing criteria.

Model comparison must use independent truth-based baselines, including
native PACE and appropriately isolated external methods, not merely
compare plots from the same sampler. Quantify Monte Carlo uncertainty,
multiple prespecified alpha thresholds, convergence failure and fit
failure. Use a versioned analysis decision record before setting any
`scientific_inference_qualified` flag to true.

The follow-on workflows archive `cases.csv`, `evidence.json` and
`sha256.txt`. All publication interlocks remain false. Passing CI is a
necessary engineering checkpoint, not a statistical qualification gate.

## Pending B7 modelling

A genuine Bayesian planar MFPCA model must learn shared x/y loadings,
cross-covariance and channel-specific observation error from separately
observed irregular timestamps. Do not relabel the currently available
fixed-population paired/asynchronous score benchmark as full B7.
A separate implementation and qualification programme is required.
