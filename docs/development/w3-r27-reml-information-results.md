# R27 — restricted Gaussian information explains weak random-slope covariance recovery

**Original research evidence:** [draft PR #329](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/329), [scientific run #38727413069](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38727413069), source head `ad9b8a92c15c2b692090cd7f343e5ffb011c692c`. Both independent mathematical score-contract tests and original fixed-source diagnostics **passed**. Original design rows are frozen from **R26 generating blocks 0 and 15** (seed `202610153626`), sample sizes n24/n96, ordinary-support predictor-independent/predictor-dependent covariance, matched working family only: **8 fixed designs, 2 original independent blocks**. Additional seed `202610153727` supplied 128 new conditional Gaussian innovation vectors/design (1,024 conditional vectors, **zero new independent generating designs**). All original R26 paired recovery data remain unchanged.

The [original source artifact](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38727413069/artifacts/11968354528) includes complete eight-design score/information ledger and SHA256SUMS. The archive was downloaded and its **three** original source entries each independently verified by SHA256.

## Restricted Gaussian variance-component information

With `Z=sqrt(W)X`, `V(theta)=sum_k theta_k K_k` and the GLS residual projection `P=V^-1−V^-1 Z (ZᵀV^-1Z)^-1 ZᵀV^-1`, analytically compute the restricted Fisher information `I_jk=1/2 tr(PK_jPK_k)` via participant-specific covariance blocks. This implementation never constructs the global dense N×N `P`. For log-component variance coefficients, information is `I_log,jk=theta_j theta_k I_jk`; its inverse diagonal yields **local asymptotic** component log-standard errors under the specified, correctly parameterized Gaussian source.

All eight original design information matrices were **positive definite**: formal information rank is not the problem. Nevertheless, random slope information was weak, and several components were strongly correlated in information space. The entire matrix can be well defined while one variance parameter remains practically uncertain.

## All eight original frozen-source information cells

| Original block | n | Source covariance | Log slope variance local SE | Log intercept variance local SE | Log trial variance local SE | Log sensor variance local SE | Log-information condition | Largest off-diagonal information correlation | Conditional slope score variance / Fisher information |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 24 | independent | 4.535 | 1.382 | 0.306 | 0.037 | 16606 | 0.956 | 1.136 |
| 0 | 24 | dependent | 4.501 | 0.526 | 0.305 | 0.037 | 15188 | 0.758 | 1.059 |
| 0 | 96 | independent | 2.199 | 0.670 | 0.156 | 0.018 | 15378 | 0.956 | 1.072 |
| 0 | 96 | dependent | 2.072 | 0.231 | 0.156 | 0.018 | 12662 | 0.702 | 0.976 |
| 15 | 24 | independent | 4.527 | 1.379 | 0.306 | 0.037 | 16551 | 0.956 | 1.054 |
| 15 | 24 | dependent | 4.646 | 0.446 | 0.305 | 0.037 | 16126 | 0.661 | 0.901 |
| 15 | 96 | independent | 2.193 | 0.668 | 0.155 | 0.018 | 15374 | 0.956 | 1.038 |
| 15 | 96 | dependent | 1.900 | 0.229 | 0.155 | 0.018 | 10707 | 0.695 | 0.901 |

## Conditional Gaussian score validation

A separate 128-draw Gaussian score experiment within every frozen design recomputed GLS fixed-effect residualization from each simulated innovation vector. The resulting analytic log-variance score was independently compared to the **negative** of the separately finite-difference-validated R25 restricted negative-loglikelihood gradient, and the scientific tests passed. The empirical component score variances were broadly consistent with the exact Gaussian Fisher information: across the eight designs the slope score-variance/reference ratios ranged from **0.901 to 1.136**.

The conditional score experiment is only a numerical/statistical contract for the Gaussian working model, **not eight independently new source studies** and not estimated nuisance covariance interval inference.

## Research interpretation

For the tested source designs, the random-slope variance has dramatically less local information than the trial and sensor variances. At n=24, its local asymptotic log-variance SE is approximately **4.50–4.65**; at n=96, approximately **1.90–2.20**. Trial variance log-SE is approximately **0.305–0.306** at n24 and **0.155–0.156** at n96; sensor variance log-SE approximately **0.0367** and **0.0184–0.0185**, respectively.

These values help explain why R26's independent 16-block study found positive slope variance estimates below 5% of truth in **52/192 matched REML cases**, even as trial and sensor variances were recovered much more reliably. More participants improved *expected* information but did not make the slope component locally precise at n96. The local Gaussian Fisher inverse is not an exact finite-sample confidence interval, especially at zero/boundary variance components; extrapolating a guaranteed target sample size from eight frozen configurations would overstate the evidence.

A future design-specific study should test whether greater between-participant predictor range, longer within-participant observation windows, more repeated trials, or external measurement of random-slope variation improves information while preserving realistic irregular gaze and sensor dependence. This is a scientific **study-design qualification** problem, not simply a numerical matrix-root problem.

Neither R26 nor R27 qualifies estimated-target CR2/Satterthwaite uncertainty, pointwise 90% inference or whole-function simultaneous bands. R27 uses known true variance components solely to compute the *oracle information* benchmark and has not developed a new production covariance estimator.

`source_information_operator_verified=true`, `random_slope_practical_identifiability_limited=true`, `nuisance_estimation_inference_qualified=false`, `simultaneous_functional_bands_qualified=false`, `release_authorized=false`. Scientific issues #289 and #296 remain OPEN. Original R20 41/256 failures and R22 32 numerically refused cases remain unchanged; no public API promotion, protected-main merge, tag or PyPI publication.
