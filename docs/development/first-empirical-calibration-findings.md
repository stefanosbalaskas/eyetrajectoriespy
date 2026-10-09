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


## Recovered F1/F5 complete scenario-level operating characteristics

**Recovery source:** [workflow #37969068128](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37969068128)
on draft #252, which fetched and verified the original 9,600 case-level
samples from workflow #37965949039, and refitted **zero** models.
Every scenario below has **300** independently seeded attempted fits,
no fitting exceptions, and is a *separate* operating-characteristic
estimate. Monte Carlo exact 95% intervals are provided in the retained
`evidence-combined.json` artifact, not silently collapsed to this table.
Rates are rejection proportions, **not effect estimates**.

### F1 native sparse-group PACE test (2,400 model fits)

| F1 design | Truth | α=.01 | α=.05 | α=.10 | Failed |
|---|---|---|---|---|---|
| balanced_equal_covariance | alternative | 87.67% | 99.33% | 99.67% | 0 |
| balanced_equal_covariance | null | 2.33% | 7.67% | 12.00% | 0 |
| clustered_two_trials | alternative | 90.33% | 99.33% | 99.67% | 0 |
| clustered_two_trials | null | 0.67% | 6.67% | 11.33% | 0 |
| unequal_heteroscedastic_null | alternative | 95.33% | 99.33% | 99.67% | 0 |
| unequal_heteroscedastic_null | null | 0.00% | 4.33% | 8.67% | 0 |
| very_sparse | alternative | 87.33% | 98.00% | 99.67% | 0 |
| very_sparse | null | 1.33% | 4.33% | 9.67% | 0 |


The balanced independent null is 23/300 = 7.67% at α=.05 (exact
95% Monte Carlo interval 4.92–11.28%), and the clustered two-trial
null 20/300 = 6.67% (4.12–10.11%). The sparse and heterogeneous-unbalanced
null scenarios are both 13/300 = 4.33% (2.33–7.30%). These scenarios
do not yet establish a universal valid type-I error rate, and the
heterogeneous-unbalanced labels are not exchangeable under pooled
permutation. The strong synthetic alternative has 98%–99.33%
rejection, **not** representative power across realistic effect sizes.

### F5 functional ordered-change CUSUM bootstrap (7,200 tests)

| F5 generating errors | Block | Truth | α=.01 | α=.05 | α=.10 |
|---|---|---|---|---|---|
| iid_gaussian | independent | one_break | 100.00% | 100.00% | 100.00% |
| iid_gaussian | independent | two_breaks | 22.33% | 95.67% | 100.00% |
| iid_gaussian | independent | null | 0.33% | 3.33% | 7.67% |
| iid_heavy_tail | independent | one_break | 100.00% | 100.00% | 100.00% |
| iid_heavy_tail | independent | two_breaks | 16.33% | 92.33% | 100.00% |
| iid_heavy_tail | independent | null | 1.33% | 5.00% | 7.00% |
| strong_AR1 | block 2 | one_break | 100.00% | 100.00% | 100.00% |
| strong_AR1 | block 2 | two_breaks | 36.33% | 90.67% | 99.67% |
| strong_AR1 | block 2 | null | 84.33% | 100.00% | 100.00% |
| strong_AR1 | block 4 | one_break | 72.33% | 100.00% | 100.00% |
| strong_AR1 | block 4 | two_breaks | 0.00% | 6.00% | 30.33% |
| strong_AR1 | block 4 | null | 1.33% | 42.67% | 77.33% |
| strong_AR1 | block 8 | one_break | 7.00% | 95.00% | 100.00% |
| strong_AR1 | block 8 | two_breaks | 0.00% | 0.00% | 1.00% |
| strong_AR1 | block 8 | null | 0.00% | 2.33% | 26.00% |
| weak_AR1 | block 2 | one_break | 100.00% | 100.00% | 100.00% |
| weak_AR1 | block 2 | two_breaks | 0.00% | 9.00% | 44.00% |
| weak_AR1 | block 2 | null | 0.33% | 12.00% | 32.00% |
| weak_AR1 | block 4 | one_break | 81.67% | 100.00% | 100.00% |
| weak_AR1 | block 4 | two_breaks | 0.00% | 0.00% | 0.33% |
| weak_AR1 | block 4 | null | 0.00% | 0.33% | 3.67% |
| weak_AR1 | block 8 | one_break | 17.67% | 99.00% | 100.00% |
| weak_AR1 | block 8 | two_breaks | 0.00% | 0.00% | 0.00% |
| weak_AR1 | block 8 | null | 0.00% | 0.00% | 1.33% |


The scientifically consequential result is the strong-AR(1) null:
with block length **2**, 300/300 false rejections at 5%;
with block length **4**, 128/300 (42.67%);
and with block length **8**, 7/300 (2.33%).
The weak-AR(1) null ranges from 12.00% (block 2) to 0%
(block 8). At the tested sample length (36 ordered curves),
the declared block-resampling choice can convert a severely liberal
test into a strongly conservative one. Neither green CI nor successful
bootstrap execution rescues nominal inference. Other effect/null
generating conditions may behave differently; do not promote an
automatic universally optimal block length based on these examples.

### Data-representation issue discovered in the recovered report

The original SHA256-verified data has the **literal text**
`scenario="null"` (F1) and `change="null"` (F5). The historical
aggregator used default `pandas.read_csv` missing-value vocabulary,
which silently mapped the literal string `"null"` to missing data.
This **did not change rejection counts or fitting outcomes**, because
grouping explicitly retained missing-group keys, but it did alter
the reported scenario names. The follow-on fix reads CSV with
`keep_default_na=False, na_values=[""]`, preserving the categorical
`"null"` truth while retaining truly empty numeric cells as NA.
New regression tests reject loss of the `"null"` truth label. The
source-simulation CSVs are never modified.

**Methods decision:** F5 dependence-adjusted p-values are not
qualified; F1 remains restricted to scientifically predeclared,
design-specific null simulations. B6/B7 remain scientifically
unqualified after the substantial matched-prior posterior undercoverage.
No root API or production release promotion is authorized.
