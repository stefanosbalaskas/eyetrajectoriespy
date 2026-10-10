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

## Completed original-source results — 10 October 2026

The **original scientific fitting workflow [#38039822342](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38039822342)** completed **7/7 jobs**, **9/9 actual posterior fits**, zero fit exceptions and a successful cross-design SHA256 evidence audit. Retained original study artifacts:

- B6 univariate: [artifact `11665746776`](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38039822342) (`b6-b7-longchain-B6_rank1`)
- B7 paired: [artifact `11665707552`](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38039822342) (`b6-b7-longchain-B7_rank1_paired`)
- B7 asynchronous: [artifact `11665607799`](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38039822342) (`b6-b7-longchain-B7_rank1_asynchronous`)

**Source provenance:** original fitting was executed at PR #269 parent-study head `b0e64de579d72a40ace71c1ef3fe3dfe84db6a55`; the subsequent tests/doc-only corrections at `024779aaaa516681f34855577d65c54e7280b561` did not change the posterior algorithm. The corrected-head general CI finished **24/24 green**. Results below are the originally emitted JSON scientific rows, not refits on the doc-update commit.

### Identifiable covariance diagnostics

| Study | Sampling architecture | Rank R-hat | Bulk ESS | Tail ESS | Spectral mean MCSE | Exploratory R-hat ≤1.01 and ESS ≥400? |
|---|---|---:|---:|---:|---:|---|
| B6 rank 1 | Original partially collapsed Gibbs | 1.0901 | 45.6 | 32.6 | 0.001677 | **No** |
| B6 rank 1 | Score-marginal elliptical slice | 1.2049 | 13.4 | 41.2 | 0.003107 | **No** |
| B6 rank 1 | Independent PyMC NUTS | 1.0060 | 399.6 | 340.6 | 0.000702 | Borderline threshold, formally no |
| B7 rank-1 paired | Original partially collapsed Gibbs | 1.2928 | 11.7 | 74.6 | 0.002090 | **No** |
| B7 rank-1 paired | Score-marginal elliptical slice | 1.4250 | 8.5 | 24.3 | 0.001355 | **No** |
| B7 rank-1 paired | Independent PyMC NUTS | 1.0005 | 705.7 | 838.3 | 0.000224 | **Yes, screen only** |
| B7 rank-1 asynchronous | Original partially collapsed Gibbs | 1.1594 | 19.9 | 108.4 | 0.001514 | **No** |
| B7 rank-1 asynchronous | Score-marginal elliptical slice | 1.6015 | 6.8 | 32.7 | 0.001909 | **No** |
| B7 rank-1 asynchronous | Independent PyMC NUTS | 0.9997 | 699.2 | 959.7 | 0.000205 | **Yes, screen only** |

Original source diagnostic functionals are the **B6 midpoint x variance** and the **B7 midpoint x/y cross-covariance**. The independent NUTS runs reported **zero divergences in each study**. All three samplers' single-dataset marginal 90% intervals contained their respective generating covariance truth. This one-of-one observation per design **does not estimate** nominal repeated-sampling posterior coverage.

### Posterior agreement and its limits

| Study | Original Gibbs posterior mean | Elliptical slice posterior mean | Independent NUTS posterior mean |
|---|---:|---:|---:|
| B6 variance | 0.03154 | 0.03337 | 0.03514 |
| B7 paired x/y covariance | −0.01757 | −0.01500 | −0.01762 |
| B7 asynchronous x/y covariance | 0.02066 | 0.01848 | 0.01897 |

Native posterior means lie in the vicinity of the independent reference, but *apparent numerical agreement is not reliable agreement* when native bulk ESS is only 6.8–45.6 and between-chain differences are substantial. On the covariance functional, chain-mean ranges as fractions of pooled posterior SD reached **0.97/1.48/0.018** for B6 original/ESS/NUTS, **0.93/1.27/0.038** for B7 paired, and **0.76/1.54/0.041** for B7 asynchronous. NUTS population mean itself is generally better mixed than native covariance, but reference quality must be assessed across more functionals/datasets.

**Computational efficiency not established:** native Gibbs retained 4 × 800 draws versus NUTS 2 × 800. The source study did **not** measure per-method wall time; therefore absolute ESS ratios and mean MCSE differences are *not* speed or ESS-per-second comparisons.

**Scientific decision:** evidence across three newly prior-generated rank-one datasets disfavors further unmotivated native Gibbs transition variants as the first priority. A separate validated four-chain independent NUTS reference, rank-2 diagnostic study, many-dataset rank-based SBC, known-truth nominal coverage and compute-budget-matched timing remain required before selecting a production posterior backend or promoting any uncertainty interface. [Blocker #255](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/255) and all release/inferential flags remain unchanged.

## Reproducibility

Source script: `scripts/run_b6_b7_longchain_identified_geometry.py`; dedicated CI `.github/workflows/science-b6-b7-longchain-covariance-geometry.yml`. The original source study creates per-design `cases.json`, `evidence.json`, `SHA256SUMS`, independently verifies the complete experiment in a combined job, and preserves failures. The preceding original workflow and retained artifacts document completion; do not attribute the fitting run to a later docs-only head. **Do not change the underlying sampler default or promote posterior inferential validity based on these results.**
