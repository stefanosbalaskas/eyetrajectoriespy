# B6/B7 rank-two four-chain PyMC/NUTS R3 — exploratory computational pilot

!!! danger "Not a validated statistical-inference method"
    This research-only pilot tests whether the **already numerically verified** rank-two score-marginal PyMC model can produce usable four-chain posterior draws on two independently prior-generated sparse planar gaze datasets. **No outcome has been presupposed.** The correct result can include fitting exceptions, divergences, poor mixing or low ESS. Passing an exploratory screen would not establish SBC, 90% population interval coverage, fixed-truth coverage, posterior prediction or release readiness.

## Prerequisites and experiment

The [rank-two dense Gaussian versus Woodbury contract](b6-b7-rank2-marginal-mathematics.md) and [actual PyMC log-posterior/gradient verification (R2)](b6-b7-rank2-pymc-r2-research-protocol.md) are separate mathematical prerequisites. Their original four-case graph study is [workflow #38095088126](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38095088126).

R3 is intentionally a **small stage-zero pilot**, not an SBC sample. It prespecifies one freshly prior-generated **rank-two** dataset under each of two observation designs: paired x/y gaze and genuinely asynchronous x/y timestamps. Each dataset has four simulated participants, a known two-channel noise level, two score components and matched isotropic Gaussian loading priors. The experiment uses the verified, actual PyMC rank-two graph with participant scores analytically integrated out.

Each dataset receives **four NUTS chains, 700 warmup and 400 retained draws per chain**, with target acceptance 0.94 and two CPU cores per fitting job. The data-generation seed namespace is isolated from all prior rank-one experiments, and no out-of-prior near-tied design is silently represented as prior-SBC.

## Predeclared diagnostic targets

All posterior summaries refer to **identifiable, factor-rotation-invariant** population mean, variance and cross-covariance functionals on the grid quarter, midpoint and three-quarter positions (15 in each planar dataset). Do not assess convergence of individually signed or rotated loadings as scientific population-functionals.

The original numerical source records include rank-normalized R-hat, bulk/tail ESS, ArviZ spectral MCSE, chain-mean spread, split-half drift, NUTS divergences, BFMI, tree depth, observed single-truth 90% interval inclusion, full fit elapsed time and identified ESS per elapsed second. The *exploratory* screen is R-hat ≤1.01, bulk/tail ESS ≥400, BFMI ≥0.3 and zero divergences **for all prespecified identified functionals**; scientific fits should not be silently discarded or rerun in response to screen failures.

The source workflow runs two actual PyMC posterior jobs, numerical contract tests on Python 3.11–3.13, source SHA256 verification and a two-dataset failure-inclusive aggregate. Each attempted dataset writes a case and evidence ledger even on sampling exceptions. The audit reports separate counts for fit exceptions and computational-screen failures and retains negative outcomes.

## Qualification limits and next decision

This experiment is **not** the formal rank-two SBC or coverage study. Two datasets cannot establish repeatability of convergence, and neither one-of-one interval inclusion nor ESS/second can establish statistical calibration or an architecture-level runtime winner. If the posterior fits mix inadequately, investigate identified mean/covariance chain geometry, rotational degeneracy and parameterization before expanding simulation counts. If the small fits pass, prespecify independent rank-two R4 replicates, rank-based SBC and coverage Monte Carlo precision targets.

Experimental methods remain on draft research branches. [Scientific blocker #255](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/255) and the independent [F5 dependence issue #256](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/256) remain open; published stable **1.1.0** and unreleased **1.2** are unaffected. This page is only available in the research draft unless separately integrated into the public research website after original evidence exists.
