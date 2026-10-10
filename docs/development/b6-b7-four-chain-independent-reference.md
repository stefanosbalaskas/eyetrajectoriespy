# B6/B7 four-chain independent PyMC/NUTS — rank-one reference replication

!!! danger "Experimental posterior reference, NOT qualified posterior uncertainty"
    The study is restricted to an **unmerged research branch** and cannot
    promote a Bayesian posterior method, posterior interval, inference gate or
    eyetrajectoriespy 1.2 release. Scientific blocker #255 remains open.

## Source-grounded motivation

The nine-fit B6/B7 longer-chain experiment in [research documentation](b6-b7-longchain-identified-covariance-geometry.md)
found persistent native identified population-covariance mixing failures. Two-chain
independent PyMC/NUTS showed substantially better rank R-hat, ESS and spectral
MCSE in all three studied datasets, but rank-one NUTS with two chains and a
single prior-generated dataset per design is not a qualified posterior
reference and does not establish nominal coverage or efficiency.

## Frozen R1 pilot protocol

- Generate **two new independent prior draws per design**, six datasets in
  total, with a new independent calibration seed namespace. Reuse the
  **exact original Gaussian prior, known-noise model, rank-one basis** and
  untouched native B6 sparse univariate, B7 paired and B7 asynchronous
  observation geometry.
- Sample the **same independent Gaussian score-integrated PyMC likelihood**
  with **four chains**, each **1,200 warmup + 800 retained iterations**,
  using at most two CPU cores; fixed target acceptance 0.94.
- Analyze **6 identified functionals** in B6 (x population mean and variance
  at three positions), and **15** in each B7 design (x/y means and variances
  plus within-time x/y cross-covariance, each at 25%, 50% and 75% of grid).
- Record for *each* identified quantity: rank R-hat, bulk/tail/mean ESS,
  genuine spectral MCSE, chain-mean dispersion, half-chain drift,
  posterior mean/SD, 90% interval and one generating truth.
- Record NUTS divergences, energy BFMI by chain, tree-depth diagnostics,
  full fitting elapsed seconds (includes model graph compilation and
  tuning), and identified ESS/full-fitting-second. This is only a reference
  throughput measure, **not** a compute-matched native-versus-NUTS
  efficiency benchmark. Memory peaks are not measured in this tranche.

The predeclared **exploratory** screen is all quantity-specific rank R-hat
≤1.01, bulk AND tail ESS ≥400, zero divergences and BFMI ≥0.3 for each
chain. A screen failure remains a scientifically useful result, not an excuse
to remove replicates. A screen pass is *not* proof of calibrated intervals,
general posterior correctness, or rank-two validity.

All **six actual fits** must be present with **original SHA256 evidence**,
including explicit numerical failure records. The workflow checks
attempt counts, seeds, chain counts and artifact validity without tuning
convergence thresholds based on outcomes.

## Future gates not authorized by this pilot

1. Independently validated score-integrated rank-two log-likelihood with
   near-tied component cases and identified covariance diagnostics.
2. Rank-based SBC on substantially more independent prior-generated
   datasets; predeclared error bars, non-convergence handling and failures.
3. 90% interval *repeated-simulation* calibration after adequate posterior
   computation. A single prior-truth-in-interval flag is not coverage.
4. Compute-matched Gibbs/NUTS/other reference comparisons, resource-use
   audits and independent sparse asynchronous real-data applications.

Stable 1.1.0 remains unchanged and 1.2 remains unpublished.
