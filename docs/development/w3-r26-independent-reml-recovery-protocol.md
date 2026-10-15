# R26 — independently seeded reliability replication of covariance-component estimators

**Research-only, no confidence-interval coverage or method winner.** R25 [draft PR #327](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/327) tested four independent blocks, where REML's median matched-family trial relative error was ~0.221 vs original NNLS's ~1.0, and REML frequently improved sensor-variance recovery. Those 64 paired fits had only **4 source blocks** and an important constraint: original NNLS can return literal zero while REML uses strictly positive bounded log variances. A larger independent source experiment is needed before even a conditional reliability decision.

## Prespecified distinct source

Master seed **202610153626**, **16 genuinely new independent generating blocks**. Each uses native irregular sample times and 1–3 trials/participant with nested n24, n48 and n96, four fixed leverage × source covariance structures, one Legendre-5 functional mean basis and both **separately fitted** predeclared shared/predictor-scaled covariance working families. This yields **384 paired model-family evaluations, but only 16 independent generating blocks**. Generating source is entirely independent of R25, and its finite sample outcomes cannot retrospectively change R20–R25.

Both methods see exactly the same observed participant/trial/time/predictor/response rows. The original leverage-corrected covariance moment NNLS retains its exact nonnegative constraints and sensor-floor diagnostic. The alternate REML retains the independent analytically tested restricted Gaussian likelihood, bounded positive log-component parameterization, and observed-data NNLS initialization. **No source covariance components, true random effects, Gaussian innovations or generating mean are passed into fitting.**

## Common boundary and paired recovery comparison

To prevent the trivial difference of literal zeros (allowed by NNLS and excluded by log-REML) from determining a false winner, separately report a **common simulation diagnostic: estimates below 5% of the positive true generating component variance**, applied only **after** fitting and only for structurally matched source/working covariance families. Record all native method-specific zeros, sensor floors, lower-bound REML fits and nonconverged optimizer statuses. A model whose covariance family is structurally wrong is analyzed for reliability but not assigned component recovery error against incompatible source truth.

For each participant size, source mechanism and candidate family (24 strata), record **16 generating blocks per stratum** and all estimator failures or nonconvergence, the common truth-relative near-zero frequency and component-level median absolute relative recovery errors for matched structures only.

For *paired* method comparison of component error in matched-family cases, first average REML–NNLS absolute relative recovery-error differences over the prespecified n × source conditions **within each independent source block**; then use 2,500 whole-generating-block bootstrap resamples (seed `202610153628`) for descriptive 95% Monte Carlo intervals. Report source block count and whether pairing is complete. These are uncertainty intervals for **method error differences**, not confidence intervals for gaze-function parameters. An inferred preference must not ignore estimator failures and must not choose the method after seeing results.

## Limits

The data generator and covariance candidates are deliberately aligned, and REML's conditional Gaussian assumption is not stress-tested against heavy tails, missingness or misidentified trial effects here. Nuisance parameter estimation uncertainty is unaccounted for in the currently conditional CR2 Satterthwaite reference; **no CR2 SE, df, nominal pointwise or simultaneous confidence-interval coverage is calculated in R26**. No public API support, protected-main merge, version 1.2 release tag or PyPI upload. Scientific blocker issues #289/#296 remain open, and the original R20 41/256 scientific failure cases remain permanently recorded.
