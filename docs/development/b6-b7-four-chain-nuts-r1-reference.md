# B6/B7 R1: six four-chain independent NUTS references — experimental evidence

!!! danger "Diagnostic success is not posterior-interval qualification"
    **Published stable: eyetrajectoriespy 1.1.0.** This page documents six **synthetic, prior-generated** datasets fit by a separately implemented, **unpublished experimental** Bayesian reference. The original research code remains on draft [PR #271](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/271). A green source workflow, well-mixed chains, and isolated truth-inclusion checks do **not** establish nominal credible-interval coverage, rank-two validity, production readiness or a 1.2 release.

## Original completed source experiment

The exact-head [scientific run #38047872726](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38047872726), on research commit `ca20b142dc5f3e28bd314cd5a65b74fee27567bd`, completed **10/10 scientific jobs**, **six out of six actual PyMC/NUTS posterior fits**, **zero fitting failures**, and a checksum-verified cross-shard evidence audit. The full PR head also passed **26/26 engineering workflow groups**. These are **six independent datasets**, not a six-draw posterior-calibration study or a human-participant sample.

Each design—B6 sparse univariate, B7 paired planar, and B7 asynchronous planar—has two new independently prior-generated rank-one datasets (18 synthetic participants each). Every reference fit uses **four chains, 1,200 tuning iterations, 800 retained iterations per chain**, the matched score-marginalized Gaussian likelihood and priors, and no native Gibbs posterior transitions.

The prespecified population diagnostics cover **six B6 functionals** or **fifteen B7 functionals** per dataset at the evaluation grid quarter, midpoint, and three-quarter: population means, variances, and where applicable x/y cross-covariances. Raw factor-loading sign diagnostics are not the inferential target.

## Identifiable population convergence

![Six actual independent NUTS four-chain sample diagnostics, minimum population bulk ESS and maximum rank R-hat](../assets/research/b6-b7-four-chain-nuts-r1-20261010.svg)

| Generating design | Dataset replicate | Worst rank R-hat | Minimum bulk ESS | Minimum tail ESS | Divergences | Exploratory screen |
|---|---:|---:|---:|---:|---:|---|
| B6 univariate rank 1 | 0 | 1.0016 | 1,316 | 1,470 | 0 | Pass |
| B6 univariate rank 1 | 1 | 1.0022 | 1,892 | 1,510 | 0 | Pass |
| B7 paired rank 1 | 0 | 1.0050 | 1,174 | 1,265 | 0 | Pass |
| B7 paired rank 1 | 1 | 1.0058 | 707 | 923 | 0 | Pass |
| B7 asynchronous rank 1 | 0 | 1.0041 | 1,149 | 1,125 | 0 | Pass |
| B7 asynchronous rank 1 | 1 | 1.0021 | 983 | 1,430 | 0 | Pass |

*Rounded results are recalculated from the individual original `ACTUAL FOUR CHAIN CASE` JSON records printed by the six scientific jobs. The worst R-hat is the maximum, and minimum ESS the minimum, **across the prespecified identified functionals within each dataset**. An exploratory screen requires rank R-hat ≤ 1.01, bulk and tail ESS ≥ 400, BFMI ≥ 0.3 and zero divergences. All six fits passed; minimum observed chain-energy BFMI was approximately **0.770**. The sampler also recorded actual ArviZ spectral MCSE, chain-mean comparisons and within-chain half shifts. There is no qualification flag promoted by these diagnostics.*

## Truth inclusion is not nominal coverage

The original case evidence reports whether each function-specific *marginal* 90% posterior interval includes one generating truth. Two B6 datasets each had 5 of 6 functionals include truth; the B7 paired datasets had 14/15 and 15/15; both asynchronous B7 datasets had 15/15. Those **72 dependent function-specific intervals arise from only six independent datasets**, so their pooled inclusion frequency is **not** a 90% coverage estimate. Their correlation across time, outputs and participants prevents treating them as independent Bernoulli trials. A few missed true values are entirely compatible with valid intervals and also insufficient to prove validity.

This four-chain evidence supports **a more credible rank-one reference computation for the studied functionals**, not a final posterior or scientific uncertainty contract. It differs from the earlier [nine-fit native Gibbs / elliptical-slice / two-chain NUTS pilot](b6-b7-longchain-identified-covariance-geometry.md), which showed poor covariance mixing in both native samplers. R1 does **not** directly compare computational efficiency with native Gibbs and does not establish that their posterior targets differ.

## Execution cost and audit boundaries

The retained source records include full fit wall-clock time **including compilation, tuning and sampling**, from approximately **13–45 minutes per fit**, and identifiable ESS per full-fit second. They do **not** provide a native-versus-NUTS compute-matched benchmark or measured peak process memory; the reference used two compute cores per job with four chains. Do not interpret this as a performance superiority claim over the native implementations.

| Dataset | Original GitHub Actions evidence artifact |
|---|---|
| B6, replicate 0 | `11668966823` (`four-chain-B6_rank1-0`) |
| B6, replicate 1 | `11668806792` (`four-chain-B6_rank1-1`) |
| B7 paired, replicate 0 | `11669205610` (`four-chain-B7_rank1_paired-0`) |
| B7 paired, replicate 1 | `11669865251` (`four-chain-B7_rank1_paired-1`) |
| B7 asynchronous, replicate 0 | `11669408373` (`four-chain-B7_rank1_asynchronous-0`) |
| B7 asynchronous, replicate 1 | `11669423841` (`four-chain-B7_rank1_asynchronous-1`) |

Artifacts are available through [the original source-run page](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38047872726) while GitHub retains them. The figure is constructed only from the six exact-source diagnostic summaries and is **not** a new fitting experiment.

## Scientific decision: keep the gates closed

The next independent scientific gates remain **rank-two posterior likelihood and diagnostic checks; prior-generating rank-based simulation calibration across many fresh datasets; repeated-simulation 90% interval coverage at controlled Monte Carlo error; posterior predictive calibration; matched-compute runtime and memory comparison; and independent real-data studies**. These should be prespecified and retain failed fits and nonconverged draws. There is no justification yet for silently selecting a production NUTS backend, retiring native Gibbs, or exposing experimental covariance uncertainty as validated inference.

[Scientific blocker #255](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/255) remains open; [F5 dependence blocker #256](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/256) is unaffected. Research source [PR #271](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/271) remains separate from protected `main`. **Release and scientific-promotion flags remain false.**
