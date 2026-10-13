# R16 CR2 exploratory factorial pilot — original results

Original simulation [GitHub Actions run #38467599297](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38467599297), source head `4ef5500c18800105e68bd3844c30d08d397db4dc`. The two dedicated original scientific jobs passed, **192/192 completed, zero failed**. The results use **24 paired source blocks already used within R16**, not 192 independent datasets nor an independent replication. Numerical cross-check compares an explicitly specified working-identity CR2 adjustment with an independent dense block computation. Note the broader full test matrix failed on Windows because the optional R fixture ran in an environment without installed `clubSandwich`; this was corrected in a subsequent commit by making the cross-language test opt-in in its dedicated R workflow. Latest-head CI must pass before engineering completion is claimed.

## Nominal 90% *pointwise* truth inclusion, counts / 24

| Leverage | Participant covariance | Basis | CR1 | Working-identity CR2 | Centered CV3J | Simulation-known Gaussian oracle | Mean CR2/oracle SE ratio |
|---|---|---|---:|---:|---:|---:|---:|
| Ordinary | Independent | Legendre-5 | 22 | 22 | 22 | 22 | 0.990 |
| Ordinary | Independent | Cubic spline | 23 | 23 | 23 | 23 | 1.003 |
| Ordinary | Dependent | Legendre-5 | 20 | 20 | 20 | 21 | 0.976 |
| Ordinary | Dependent | Cubic spline | 22 | 22 | 22 | 21 | 0.980 |
| Extreme | Independent | Legendre-5 | 18 | 19 | 20 | 21 | 0.844 |
| Extreme | Independent | Cubic spline | 17 | 21 | 21 | 22 | 0.855 |
| Extreme | Dependent | Legendre-5 | 16 | 18 | 19 | 23 | 0.870 |
| Extreme | Dependent | Cubic spline | 16 | 19 | 19 | 24 | 0.850 |

CR2 improves the observed extreme-leverage inclusion relative to CR1 under these generating cases, but the pattern is not evidence of nominal finite-sample calibration. The original 24 blocks are too few for precise individual coverage comparisons; CR2 uses an identity working target after WLS whitening, **not the generator's within-person correlation**, and a descriptive t(23) reference with unvalidated CR2-specific degrees of freedom. All estimates are pointwise, not simultaneous; the truth covariance oracle remains unavailable in empirical data. No estimator is selected or promoted.

Scientific blocker issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain open. Release authorization is false; version 1.2 remains unreleased.
