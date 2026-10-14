# W3 R17 — independent 96-block pointwise calibration protocol

**Research-only preregistered computational experiment, not a release qualification.** The preceding [R17 feasibility PR #316](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/316) was 24/24 green and completed 128/128 evaluations, but only had eight independent generating blocks. This stage does not re-use those blocks or the R16 source random seed.

## Fixed source design

New master seed **202610142424**; **96 new independent generating blocks**, generated with mutually distinct seeds of the form master + 23741 × block, and **nested participant samples of 24, 48 and 96** within each block. There are four predictor-support × participant-covariance combinations (ordinary/ extreme × predictor-independent/dependent), two unchanged prespecified time mean bases (Legendre-5 and cubic-spline-13), and two CR2 working covariance specifications (the **simulation-known true within-person covariance**, versus a deliberately diagonal-misspecified target with identical diagonal). There are **4608 paired source/basis/target evaluations but only 96 independent random generating blocks**. Their reuse across conditions must never be counted as independent replication.

Generation preserves native asynchronous trial timestamps, 1–3 original complete trials per participant, participant-level random functional intercept/slope innovation, trial shared disturbances and independent sensor noise. All source observations are unchanged and there is no interpolation or manipulation of failed cases. Previous R16 WLS and source Gaussian covariance checks are required for every case; the blockwise CR2/Satterthwaite code was independently compared with R clubSandwich's covariance/df calculations at PR #314 and with dense Python reference matrices at PR #315.

## Prespecified comparison

At a single midpoint functional-slope contrast and 90% nominal two-sided pointwise confidence interval, compare **CR1 + t(G−1), working CR2 + t(G−1), working CR2 + coefficient-specific Satterthwaite t, centered leave-whole-participant CV3J + t(G−1), and simulation-known Gaussian variance oracle + t(G−1)**. G is actual independent participant count (24, 48 or 96). In every group, report inclusion counts / 96, estimated pointwise inclusion, **95% Wilson Monte Carlo interval**, mean CR2/known-variance SE ratio, mean Satterthwaite df and **paired block-bootstrap 95% interval** for CR2/Satterthwaite minus CR1 and versus conventional CR2 reference. Bootstrap is over whole independent source blocks, never over dependent model-target evaluations.

## Guardrails and prohibited conclusions

Complete original scientific run must record exactly 4608 evaluable cases and all failures/missing records, with an original case ledger, summary, checked source SHA and SHA256 manifest. A green CI run is a computational qualification only. Even nominal 90% observed pointwise inclusion under an *oracle supplied* true covariance cannot establish empirical real-world calibration; covariance estimation uncertainty, more complex misspecifications, cluster data quality, simultaneous functional bands and external datasets remain unresolved. All scientific blocker issues #289/#296 stay open. The source method, sample size, models, critical-value definitions, bootstrap design and fixed seeds must not be changed in reaction to results.

The Python package's production API, protected main, released stable 1.1.0, 1.2 release permissions, GitHub release tags and PyPI are unchanged. Report method results transparently regardless of whether CR2/Satterthwaite wins.
