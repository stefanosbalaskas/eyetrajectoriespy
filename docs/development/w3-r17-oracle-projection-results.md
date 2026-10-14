# R17 original Gaussian oracle — truth vs projected mean diagnostic results

**Original diagnostic execution:** [workflow #38615016308](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38615016308), source commit `3ce3485d64f70c84a16affcfd2db1c2c19afa702`, [draft PR #318](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/318). **2304/2304 original-source/model evaluations completed, zero failures and zero missing.** This audit reuses exactly the same 96 independently generated source blocks, seed `202610142424`, nested participant sizes and native observations from [primary R17 PR #317](w3-r17-independent-96block-results.md). It does **not** create fresh data and **does not** redefine R17's original 90% functional-slope target.

The original Gaussian oracle uses the known conditional covariance of the source WLS coefficient estimator. Its interval is examined against both the original continuous-time generating midpoint truth and, *only as a diagnostic*, the known conditional mean's discrete-design WLS projection at that midpoint. The table reports **t(G−1)** inclusion, with G the number of participants; each fraction has 96 independent generating blocks as denominator. Standardized projection displacement and observed standard deviation of oracle-standardized stochastic error are descriptive.

| Participants | Source factor | Basis | Truth oracle /96 | Projected oracle /96 | Mean absolute projection shift / oracle SE | SD((point − projection)/oracle SE) |
|---|---|---|---:|---:|---:|---:|
| 24 | ordinary_independent | legendre5 | 86/96 (89.6%) | 86/96 (89.6%) | 6.75e-7 | 0.996 |
| 24 | ordinary_independent | cubic_spline13 | 85/96 (88.5%) | 85/96 (88.5%) | 1.51e-7 | 0.998 |
| 24 | ordinary_dependent | legendre5 | 89/96 (92.7%) | 89/96 (92.7%) | 7.13e-7 | 0.977 |
| 24 | ordinary_dependent | cubic_spline13 | 88/96 (91.7%) | 88/96 (91.7%) | 1.60e-7 | 0.995 |
| 24 | extreme_independent | legendre5 | 87/96 (90.6%) | 87/96 (90.6%) | 2.14e-6 | 1.010 |
| 24 | extreme_independent | cubic_spline13 | 87/96 (90.6%) | 87/96 (90.6%) | 5.20e-7 | 1.027 |
| 24 | extreme_dependent | legendre5 | 88/96 (91.7%) | 88/96 (91.7%) | 1.50e-6 | 1.041 |
| 24 | extreme_dependent | cubic_spline13 | 87/96 (90.6%) | 87/96 (90.6%) | 3.69e-7 | 1.034 |
| 48 | ordinary_independent | legendre5 | 87/96 (90.6%) | 87/96 (90.6%) | 6.36e-7 | 1.024 |
| 48 | ordinary_independent | cubic_spline13 | 87/96 (90.6%) | 87/96 (90.6%) | 1.53e-7 | 1.021 |
| 48 | ordinary_dependent | legendre5 | 85/96 (88.5%) | 85/96 (88.5%) | 6.71e-7 | 1.063 |
| 48 | ordinary_dependent | cubic_spline13 | 86/96 (89.6%) | 86/96 (89.6%) | 1.61e-7 | 1.066 |
| 48 | extreme_independent | legendre5 | 89/96 (92.7%) | 89/96 (92.7%) | 1.89e-6 | 0.929 |
| 48 | extreme_independent | cubic_spline13 | 89/96 (92.7%) | 89/96 (92.7%) | 4.56e-7 | 0.943 |
| 48 | extreme_dependent | legendre5 | 86/96 (89.6%) | 86/96 (89.6%) | 1.43e-6 | 1.020 |
| 48 | extreme_dependent | cubic_spline13 | 87/96 (90.6%) | 87/96 (90.6%) | 3.48e-7 | 1.031 |
| 96 | ordinary_independent | legendre5 | 83/96 (86.5%) | 83/96 (86.5%) | 6.69e-7 | 1.081 |
| 96 | ordinary_independent | cubic_spline13 | 84/96 (87.5%) | 84/96 (87.5%) | 1.83e-7 | 1.072 |
| 96 | ordinary_dependent | legendre5 | 81/96 (84.4%) | 81/96 (84.4%) | 7.06e-7 | 1.072 |
| 96 | ordinary_dependent | cubic_spline13 | 83/96 (86.5%) | 83/96 (86.5%) | 1.93e-7 | 1.077 |
| 96 | extreme_independent | legendre5 | 89/96 (92.7%) | 89/96 (92.7%) | 1.64e-6 | 1.010 |
| 96 | extreme_independent | cubic_spline13 | 89/96 (92.7%) | 89/96 (92.7%) | 3.95e-7 | 1.040 |
| 96 | extreme_dependent | legendre5 | 86/96 (89.6%) | 86/96 (89.6%) | 1.35e-6 | 1.045 |
| 96 | extreme_dependent | cubic_spline13 | 84/96 (87.5%) | 84/96 (87.5%) | 3.29e-7 | 1.077 |

## Results and qualification

**Paired oracle truth versus projected target:** 0 of 24 source/sample-size/basis cells changed their observed t(G−1) inclusion count between targets. Maximum group mean absolute projection displacement: 2.139e-6 times the simulation-known Gaussian oracle SE. This is far too small to explain the n=96 ordinary-support undercoverage. No original R17 truth-inclusion status was changed.

At n=96 ordinary-support the observed SD of the Gaussian-standardized error about the projection was roughly **1.07–1.08**, rather than exactly 1. This is consistent with somewhat greater observed dispersion in this set of 96 simulation blocks, but those values have sampling uncertainty and four models share the same generating blocks. It is **not sufficient to infer that the known covariance formula is incorrect**; a newly seeded Gaussian-source replication and an analytical conditional-variance contract are justified.

An additional frozen original-source reference file at `docs/development/w3-r17-original-oracle-coverage-contract.json` records all 24 known-Gaussian original R17 truth-inclusion counts from run #38609764263, with original source SHA. The latest diagnostic implementation requires exact equality of all 24 primary truth counts to this original record and fails on any difference; this subsequent exact-head contract CI must be verified separately before engineering completion is claimed.

This is a **post hoc diagnostic**, not a new inferential endpoint. `pointwise_coverage_qualified=false`, `simultaneous_inference_qualified=false`, `empirically_estimated_covariance_qualified=false`, `production_release_ready=false`. Scientific blockers #289 and #296 remain open. No protected-main merge, public API, release tag or PyPI publication.
