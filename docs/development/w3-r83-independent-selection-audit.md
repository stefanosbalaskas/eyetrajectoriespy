# W3 R83-A — mandatory independent source/visible-only sensitivity numerical replay

**Research only, not missing-data inference.** This audit is separately coded against the source-immutable frozen [original R83 science run #39575847765](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39575847765), whose exact PR science checkout is `4aaf792457c789b3fafd218e3dd94ae46af47e86`. Original source artifact: [#12333573581](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39575847765/artifacts/12333573581).

The R83 research question is **assumption sensitivity of pointwise selection-weighted descriptions**, not identification of MNAR or calibrated 90% confidence bands. 32 new primitive independent source blocks per design/support/variance condition produce 256 true complete X/Y source conditions, four paired observation masks per source, and 13 different analysis configurations per source, totaling **1,024 unique masks and 3,328 descriptive pointwise sensitivity/oracle records**. The five frozen MNAR assumptions are δ=-1.1, -.55, 0, +.55, +1.1.

## Audit acceptance contract

Three independent Python 3.11–3.13 tests compare source X/Y generated with independent matrix-factor code, actual four source masks and hashes, visible-only pilot intercept/slope, inverse-assumed-observation probability calculation, full 31×2 grid refusals and suff-statistic weighted regression slopes against R83. A fourth mandatory CI job independently **downloads and reads the original immutable archive**, verifies SHA256, source science exact checkout, all 256 distinct primitive source identities, 1024 paired observation masks, all 3328 pointwise estimates, refusal and observed-independent-unit/cluster effective-n diagnostics, all source truth/complete comparisons, and 13-method/five-delta source aggregates. No fixture substitution, no favorable grid selection.

The only oracle is **simulator-only** true MNAR δ=+1.1 plus true generating outcome mean, unavailable in observed data. It must be reported separately from the five observed-outcome-pilot assumption cases. This is pointwise *descriptive* WLS, not valid covariance or missingness-adjusted inference; even the correctly specified simulator oracle does not validate finite-sample 90% bands.

**No estimator promotion; inference blocker #289 and missingness blocker #296 OPEN. Stable 1.1.0 unchanged, v1.2/PyPI RELEASE HOLD.**

**Status: mandatory actual original-source replay pending.**
