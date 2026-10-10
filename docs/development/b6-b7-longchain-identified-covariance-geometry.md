# B6/B7: longer-chain identified covariance geometry — research pilot

!!! danger "No Bayesian inferential qualification"
    This is an **unpublished draft-branch** scientific diagnostic experiment, not a validation of nominal population-covariance intervals. Stable eyetrajectoriespy 1.1.0 and protected main remain unchanged. [Scientific blocker #255](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/255) remains open.

## Why this experiment is needed

The earlier 36-fit joint-loading score-marginal elliptical-slice study was a negative result: B6 covariance median R-hat/ESS was **1.084/22.5 for the original collapsed-mean Gibbs** and **1.141/15.4 for joint-loading ESS**; B7 paired **1.407/4.3 vs 1.378/4.9**, asynchronous **1.149/11.4 vs 1.418/4.4**. None met the prespecified covariance R-hat ≤1.01 and bulk ESS ≥400 screen. A scientifically sound loading update can nevertheless mix poorly; green CI is not posterior coverage evidence.

## Design frozen before the run

One **new independently prior-generated rank-one dataset** for each of B6 sparse univariate, B7 paired planar and B7 asynchronous planar, retaining original timestamps, common Gaussian priors and known per-channel noise.

On each dataset, fit:

1. Native original partially collapsed mean Gibbs: **four chains, 1,000 warmup + 800 retained draws each**.
2. Native score-marginal loading elliptical-slice comparator under exactly the same priors/noise: **four chains, 1,000 warmup + 800 retained draws each**.
3. Independently constructed analytic-score-marginal **PyMC NUTS: two chains, 1,200 tuning + 800 retained draws each**, using the independent likelihood derivation, rather than native conditionals.

Total: **nine actual posterior fits** (three datasets × three backends) with zero tolerable silent failures. Fit errors and PyMC divergences are retained.

## Identifiable outputs and diagnostics

Compute at the common-grid midpoint: population x mean, B6 x covariance, and B7 joint x/y cross-covariance, all invariant under loading sign changes. Do **not** screen using raw loading R-hat alone.

- Rank-normalized R-hat, bulk/tail and mean ESS, and **genuine ArviZ spectral mean MCSE** rather than marginal SD divided by bulk ESS.
- Per-chain posterior means and chain-mean range relative to posterior SD; first/second-half mean shifts are descriptive only, not formal convergence tests.
- Posterior mean, SD and marginal 90% interval, one known generating truth per dataset, zero-divergence diagnostics and MCSE magnitude. Compare source/posterior differences cautiously when either chain is mixing poorly.
- Report the prespecified rank R-hat ≤1.01 and bulk ESS ≥400 screen as **diagnostic**, never as a coverage or release gate.

This pilot is intentionally limited to rank one. Rank-two independent posterior references, simulation-based calibration of posterior ranks across many fresh prior-generated datasets and nominal interval coverage require separate predeclared larger experiments. They are *not* inferred from three NUTS fits or nine total posterior attempts.

## Reproducibility

Source script: \`scripts/run_b6_b7_longchain_identified_geometry.py\`; dedicated CI \`.github/workflows/science-b6-b7-longchain-covariance-geometry.yml\`. The original source study creates per-design \`cases.json\`, \`evidence.json\`, \`SHA256SUMS\`, independently verifies the complete experiment in a combined job, and preserves failures. Once completed, record the exact-head CI run and retained artifact IDs here. **Do not change the underlying sampler default or promote posterior inferential validity based on these results.**
