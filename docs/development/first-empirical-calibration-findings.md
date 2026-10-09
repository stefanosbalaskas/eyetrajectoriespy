# First empirical scientific calibration findings (unpublished, 9 October 2026)

**Source:** [research empirical calibration workflow #37965949039](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37965949039), run at [draft #250](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/250), SHA `5038b7c5c35ee189e516189dee110d8aeb9b0d4d`.
These are **actual fitted-model Monte Carlo outcomes**, not forecast values.
**All Bayesian inferential scientific-validation flags remain false.**

The source study completed **13,600 attempted models/tests with zero execution
exceptions**, and all six independent computation shards succeeded. The
two Bayesian aggregate jobs passed. F1/F5 aggregate failed only because its
historical F1 CSV field was called `iteration`, not `replicate`;
the raw SHA256-identified original shards remain available. This branch
recovers their genuine records without regenerating observations or refitting
models. Results for F1/F5 must be read from that recovery workflow, not
inferred from the failed original aggregation.

## B6: 90% marginal population posterior coverage (400 refits/scenario)

| Generating scenario | Population mean (count/400) | Latent covariance at centre (count/400) | Model match |
|---|---:|---:|---|
| Matched prior, rank 1 | 283/400 = 70.75% | 308/400 = 77.00% | Yes |
| Matched prior, rank 2 | 248/400 = 62.00% | 268/400 = 67.00% | Yes |
| Unequal sparse, rank 2 | 248/400 = 62.00% | 293/400 = 73.25% | Yes |
| Near-tied rank 2 | 284/400 = 71.00% | 306/400 = 76.50% | Stress |
| Noise misspecified, rank 2 | 224/400 = 56.00% | 249/400 = 62.25% | No |
| Loading prior misspecified, rank 2 | 194/400 = 48.50% | 98/400 = 24.50% | No |

The **matched** cases fall far below 90%. The rank-1 population-mean exact
95% Monte Carlo interval is **66.02%–75.17%** and the matched rank-2
population-mean interval is **57.04%–66.78%**: both exclude 90% by a large margin.
Zero fit exceptions is not evidence of convergence or calibrated inference.

## B7: 90% marginal joint planar posterior coverage (400 refits/scenario)

| Rank/layout | X mean | Y mean | X/Y cross-covariance | Held-out subject mean pointwise inclusion |
|---|---:|---:|---:|---:|
| Rank 1, paired | 61.50% | 67.00% | 74.00% | 87.59% |
| Rank 1, asynchronous | 65.00% | 67.75% | 71.25% | 86.41% |
| Rank 2, paired | 57.25% | 62.75% | 70.00% | 86.75% |
| Rank 2, asynchronous | 57.50% | 59.50% | 67.75% | 87.19% |

The average held-out pointwise fraction uses **400 independently generated
held-out participants per scenario**, not 3,200 independent within-subject
timepoints. The probability that all eight *marginal pointwise* intervals
contain the one subject's outcomes is between 54.0% and 61.0%; this is
not, and must not be represented as, a 90% simultaneous prediction region.

## Scientific decision

**Do not promote B6/B7 Bayesian inference.** Undercoverage is severe even
when observations and priors are generated from the declared fitted model.
The precise causal explanation is not established. The first wave uses
two chains, 160 warmup sweeps and only 70 retained draws/chain, so
convergence/mixing must be evaluated before diagnosing a posterior
implementation error. Do not attribute the entire failure to short chains
without evidence. Required tests include longer warmup/draw comparisons
**on the same seeded datasets**, split R-hat/ESS/MCSE for mean/variance/
cross-covariance, rank-based SBC under exact matched priors, and careful
verification of conditional precision matrices and Gaussian sampling.

The original source data hashes and aggregate JSON are retained in workflow
artifacts `11634318292` (B6 aggregate) and `11634745632`
(B7 aggregate). This source is synthetic prior-likelihood evidence;
it says nothing yet about real-device acquisition validity or external
transportability. It also does not justify changing observation-noise
or prior hyperparameters solely to make intervals reach 90%.

## F1/F5 evidence recovery

The original **2,400 F1** and **7,200 F5** attempted tests had zero fitting
exceptions, but combined empirical rejection rates remain to be read from the
archived original files using the historical-schema compatibility repair in
draft #251. The `research-wave1-recover-f1-f5-evidence.yml` workflow reads
GitHub Actions **run #37965949039** artifacts, verifies SHA256, rejects
duplicate seeds/shards, reconstructs the 32 scenario-level alpha=0.01/0.05/0.10
rates and retains a complete 9,600-row aggregate without refitting models.

Passing source CI is not a claim of calibrated null size, alternative power
or correctly localized multiple-change inference. In particular, F1's
heteroscedastic-unbalanced design violates pooled-label exchangeability and
is a sensitivity scenario rather than a validity-guaranteed null.

**No release, stable API or protected-main promotion.**
