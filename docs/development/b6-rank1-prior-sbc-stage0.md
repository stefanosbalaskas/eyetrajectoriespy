# B6 rank-one: first staged independent-NUTS prior-SBC and coverage pilot

!!! danger "Not enough independent datasets for calibration claims"
    Four fresh matched-prior datasets **cannot** establish SBC rank
    uniformity or 90% credible-interval coverage. All scientific and release
    gates remain closed. The stable package is still 1.1.0.

The source code predeclares four **new independent prior-generated** B6
rank-one sparse univariate datasets, using a separate seed namespace from
four-chain reference study R1. Each receives the independent score-marginal
PyMC/NUTS model with 4 chains, 700 warmup and 400 retained draws per chain.
These are deliberately shorter pilot fits to assess cost and failure modes,
*not* retrospectively selected well-mixed chains.

The two primary invariant targets are the population x mean and x variance
at the grid midpoint. For each: preserve the full four-chain ArviZ diagnostic,
a discrete truth-versus-posterior SBC rank with reproducible tie handling and
one truth-in-90%-interval flag. All six time-indexed functionals remain in the
diagnostic evidence, but **only one rank per primary quantity per independent
dataset** enters preliminary rank and coverage summaries. A 10-bin rank
histogram with only four ranks is merely bookkeeping, not an interpretable
uniformity test.

Dataset-level denominator, fit errors, sampling-screen failures and individual
source hash checks are retained. Preliminary binomial intervals are exact
Clopper-Pearson intervals among successful fits and explicitly report total
attempts, so failures are not silently removed.

Next prespecified calibration stage should set a *simulation-precision*
target, e.g. approximate 95% Monte Carlo half-width ≤.06 for a nominal 90%
event needs roughly 100 independent successfully assessed datasets, while
failed/nonconverged runs need explicit handling. No fixed-parameter
frequentist coverage is studied here: that requires fixing a generating
functional truth across repeated observation datasets, distinct from
generating truth itself from the prior every replication.

B7 prior calibration, a rank-two posterior reference, posterior predictive
checking, implementation model audits and power/cost scaling remain separate
workstreams under scientific issue #255. Public release flags remain false.
