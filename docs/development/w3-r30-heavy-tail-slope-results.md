# R30 — original-source Gaussian versus standardized Student-t(5) random-slope recovery

**Research-only controlled distributional stress:** [draft PR #332](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/332), [scientific workflow #38784206074](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38784206074), source head `d450f970bba188ce23ad79555144bbee6b84ef10`. Both primitive-Gaussian/t5 source contracts and the original 192-case robustness scientific job **passed**. Distinct master seed `202610153030`; **12 independent generating source blocks**, nested n24/n96, ordinary-support predictor-independent/dependent covariance, 1×/2× predictor spread, paired Gaussian versus standardized Student-t(5) participant random-slope innovations only. **192/192 paired source/law cases recorded, zero missing or source failures, zero NNLS/REML nonconvergences**. The 192 model cases are NOT 192 independent source experiments.

The [original scientific artifact #11998005632](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38784206074/artifacts/11998005632) contains complete 192-case records, source SHA and SHA256SUMS; all **three files were independently SHA256 verified** from the downloaded original artifact.

## Matched Gaussian second moments and a single non-Gaussian departure

Every new t5 random-slope innovation is a deterministic quantile transform of the same original standard normal primitive, `F_t5^{-1}(Phi(z))/sqrt(5/3)`, giving theoretical mean zero and variance one under the standardized t5 law. Original participant intercept, trial and sensor innovation families remain Gaussian. Native irregular timestamps, participant IDs, 1–3 trial structure and original independent source blocks are identical across the two innovation laws, and the expected covariance second-moment family is identical. The mean and predictor-dependent slope contribution are reconstructed from their original primitive innovations; no old Gaussian response is relabeled as t5.

Under t5, the original observed-only NNLS covariance moment estimator and Gaussian REML are evaluated on outcomes whose **variance-component second moments are correctly specified but random-slope distribution is not Gaussian**. This is a narrowly defined model-misspecification stress, not real gaze sensor artifacts, selection/missingness or a general t-distributed residual model.

## Prespecified paired 2×–1× benefit under Gaussian versus t5 slopes

For every matched generating block, define *spread benefit* as absolute relative slope-variance recovery error at 2× minus that at 1×. Negative values favor doubling predictor spread. The primary robustness contrast is the **heavy-tailed minus Gaussian spread benefit** on the same primitive source block, with 2,000 whole-block bootstrap draws, no pooling of trial rows as independent experiments.

| Participants | Covariance source | Method | Gaussian spread benefit | Standardized t5 spread benefit | t5 − Gaussian benefit | 95% whole-block interval on difference |
|---|---|---|---:|---:|---:|---|
| 24 | independent | Original NNLS | 0.000 | -0.000 | -0.000 | -0.000 to 0.000 |
| 24 | independent | Gaussian REML | 0.000 | -0.000 | -0.000 | -0.000 to 0.000 |
| 24 | dependent | Original NNLS | -1.331 | -1.279 | 0.051 | -0.029 to 0.128 |
| 24 | dependent | Gaussian REML | -1.339 | -1.306 | 0.033 | -0.111 to 0.137 |
| 96 | independent | Original NNLS | -0.000 | -0.000 | 0.000 | -0.000 to 0.000 |
| 96 | independent | Gaussian REML | 0.000 | -0.000 | -0.000 | -0.001 to 0.000 |
| 96 | dependent | Original NNLS | -0.703 | -0.705 | -0.002 | -0.065 to 0.053 |
| 96 | dependent | Gaussian REML | -0.756 | -0.773 | -0.017 | -0.095 to 0.046 |

For predictor-dependent Gaussian source, 2× spread improved mean slope recovery in both sample sizes and both estimators; the **same directional mean pattern** appeared when its slope primitive was standardized t5. The t5−Gaussian difference was small, and all four relevant **12-block bootstrap intervals include zero**. Therefore the present study **does not detect** a change in spread benefit due to this particular t5 innovation stress. It does NOT prove equality, noninferiority, robustness to arbitrary tails, or a general method advantage.

The predictor-independent negative controls again exhibited essentially zero change in error when only the participant predictor was multiplied, as expected from fixed-effect reparameterization invariance. Small nonzero REML differences reflect finite numerical optimizer precision.

## All 16 source/n/law/spread original cases

Each row below has **12 generating blocks** as denominator. Near-zero slope estimates use exactly the same simulation-only postfit criterion, *estimated variance below 5% of the positive generating slope variance*, for NNLS and REML.

| n | Source covariance | Slope law | Predictor spread | NNLS median slope error | REML median slope error | NNLS near-zero /12 | REML near-zero /12 |
|---|---|---|---:|---:|---:|---:|---:|
| 24 | independent | Gaussian | 1.0× | 1.000 | 1.000 | 6 | 5 |
| 24 | independent | Gaussian | 2.0× | 1.000 | 1.000 | 6 | 5 |
| 24 | independent | Standardized t5 | 1.0× | 1.000 | 1.000 | 5 | 5 |
| 24 | independent | Standardized t5 | 2.0× | 1.000 | 1.000 | 5 | 5 |
| 24 | dependent | Gaussian | 1.0× | 1.000 | 1.292 | 5 | 3 |
| 24 | dependent | Gaussian | 2.0× | 0.780 | 0.959 | 2 | 1 |
| 24 | dependent | Standardized t5 | 1.0× | 1.000 | 1.177 | 5 | 2 |
| 24 | dependent | Standardized t5 | 2.0× | 0.736 | 0.959 | 2 | 2 |
| 96 | independent | Gaussian | 1.0× | 1.000 | 1.000 | 6 | 3 |
| 96 | independent | Gaussian | 2.0× | 1.000 | 1.000 | 6 | 3 |
| 96 | independent | Standardized t5 | 1.0× | 1.000 | 1.000 | 6 | 3 |
| 96 | independent | Standardized t5 | 2.0× | 1.000 | 1.000 | 6 | 3 |
| 96 | dependent | Gaussian | 1.0× | 0.991 | 0.974 | 3 | 1 |
| 96 | dependent | Gaussian | 2.0× | 0.404 | 0.339 | 0 | 0 |
| 96 | dependent | Standardized t5 | 1.0× | 1.000 | 0.974 | 4 | 1 |
| 96 | dependent | Standardized t5 | 2.0× | 0.485 | 0.427 | 0 | 0 |

## Scientific interpretation and future gates

The original prospective R29 Gaussian result used a *different seed* from this new R30 Gaussian/t5 stress. R30 should not be numerically pooled with or substituted for R29. Results from only **12 independently seeded generating blocks** can be influenced by relatively rare participant-slope outliers, despite the matched within-block transformations. The t5 stress keeps finite second moments and is far less adversarial than a distribution with undefined second moments or participant/trial-dependent nonrandom missingness. It does not establish REML's validity under substantive covariance misspecification or real eye-tracking recordings.

No confidence intervals were estimated for the functional slope in these R29–R30 studies; the whole-block bootstrap intervals in this report are for **differences in covariance-component recovery error only**, not nominal functional effect coverage. A fitted working covariance also makes the current CR2/Satterthwaite df conditional and leaves nuisance covariance estimation uncertainty unresolved. A real inferential qualification stage would need independent source sets, finite-cluster failures/refusals, scientifically justified fitted covariance models, and a separate simultaneous function-wide bands programme.

`primitive_t5_source_contract_passed=true`; `same_second_moments_assumption=true`; `general_non_gaussian_robustness_qualified=false`; `functional_pointwise_or_simultaneous_coverage_qualified=false`; `release_authorized=false`. Scientific blockers #289/#296 OPEN. Historical R20 41/256 numerical failures and R22 32 explicit refusals remain original, all PRs draft, no public API, protected main merge, 1.2 tag or PyPI publication.
