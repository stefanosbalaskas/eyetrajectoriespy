# Rank-two R5: independent controlled generating blocks

!!! danger "Research replication, not rank-two posterior qualification"
    The first new R5 block is one *independent* generating draw relative to R4.
    Its four cells are linked within the block and must **never** be counted
    as four independent calibration datasets. No Bayesian implementation,
    production API, 1.2 release or publication flag changes.

## Original evidence and question

[R4 scientific workflow #38126832171](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38126832171)
fitted all four rank-two four-chain NUTS cells with 3/4 successful exploratory
screens, zero fitting exceptions, and a completed SHA256 audit. The paired
n=4 cell failed its predeclared screen; asynchronous n=4, asynchronous n=12,
and paired n=12 passed. This **single generating realization** establishes
neither a schedule effect nor sample-size reliability.

R5 tests whether that computational pattern recurs under new matched-prior
generating populations, not whether one scheduler has categorically better
mixing. Replication seeds are generated in a new distinct namespace using
`calibration_replicate_seed`; all eight potential seeds are declared before
sampling and excluded from R4 seed reuse. Each block holds the population
coefficients, latent participant effects, x data, y noise and observation counts
fixed across both schedules. Its n=4 sample is nested inside its n=12 sample.

## Study and staged computation

The 2 × 2 within-block design is observation schedule (paired/asynchronous)
× participant count (4/12). Each fit retains four chains, 700 tuning and 400
draws per chain and the same target acceptance (.94) as R4, enabling a direct
computational pilot comparison without post hoc budget adaptation.

Stage 0: one genuinely new block (**replicate 0**) runs all four cells from
the PR workflow. Stage 1: after reviewing cost, mixing and diagnostic outputs,
each successive workflow_dispatch may execute **one** additional *prespecified*
block from replicate 1–7; running eight blocks is not automatic. This limits
initial CI expenses and prevents prematurely extrapolating from small samples.

For each of 15 identified population functionals, preserve generating truth,
posterior mean, signed single-dataset error (**not systematic bias**), 90%
interval width/inclusion, spectral MCSE, rank R-hat, bulk/tail ESS and the
functional screening result. Preserve BFMI, divergences, elapsed time, fitting
exceptions and computational-screen failures as independent outcomes.

Report schedule contrasts paired **within each n and block**. Replication blocks,
not four constituent cells, form the eventual independent units for estimating
reproducibility, schedule differences and uncertainty intervals. n=4/12 remain
nested and require paired/block-aware analysis.

Passing convergence or observing truth inclusion in one block cannot estimate
rank-SBC uniformity or frequentist 90% coverage. Such studies must be designed
independently and sufficiently powered. Maintain blocker #255 OPEN.
