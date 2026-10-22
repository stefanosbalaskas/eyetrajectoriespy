# Reading sharp observed-only bounds under selectively missing gaze

*Methods companion for [R89/R89-A](w3-r89-sharp-observed-only-bounds.md) · Research-only algebra*

## Precisely which quantity is bounded?

The realized original missing-record population is established by the first-stage missingness mask. The estimand is the finite mean of a *known bounded transform* of each of those originally missing synthetic gaze responses. It is not the mean of available gaze, the mean over all originally observed and missing measurements combined, an unbounded source response or a regression slope.

The fixed transform is

$$
Z_i=\min\left(1,\max\left(0,\frac{Y_i+1}{2}\right)\right).
$$

This transform ensures $0\le Z_i\le1$ for every possible raw $Y_i$. It deliberately changes the target to permit algebraic worst-case reasoning. In an applied experiment, selecting a range or transform must be justified before seeing outcomes; the instrument's normalized-coordinate convention alone need not guarantee every raw observation lies in a valid [0,1] interval.

## Finite-population sharpness

Condition on the realized list of $N$ initially missing records, on which of these were eventually returned, and on their $n$ measured transformed values. The remaining $N-n$ are entirely unknown aside from $0\le Z\le1$. Their sum can be as small as zero or as large as $N-n$, so the infimum and supremum of the realized population mean are exactly the observed sum divided by $N$ and that same sum plus $N-n$ divided by $N$.

The endpoints are worst-case consequences of the stated support, not sampling distributions. If separate positive- and negative-predictor groups are disjoint and nonempty, lower bound for the *difference* equals positive-group lower bound minus negative-group upper bound, and upper bound reverses the endpoints. Both underlying means may vary independently within their stipulated support, making these contrast limits sharp under the same absence of additional restrictions.

A measured record in the selected population is only one returned by the secondary validation or by actual completion of a third-stage audit. Random assignment without actual return does not make the outcome measured.

## Observed-only computation

The original R89 bounds routine requires a population-membership mask, an actual-measurement mask, and a value array that explicitly contains **NaN for every unreturned target outcome**. It fails if an unreturned target outcome appears as a number. Grouping and count calculations use source predictors known before observation loss. It does not receive or fit a latent-Y return propensity.

The *simulation* independently retains the full generating outcome to compute the otherwise inaccessible realized truth, used only after the endpoints are calculated. Thus simulator truth inclusion is an algebraic correctness test, not an externally estimated probability of coverage.

## Nested assignment is not monotone response identification

Audits of 25% and 50% are coupled through shared assignment uniforms. Under the same actual response law and source, an outcome measured at 25% remains measured at 50%. Consequently the unmeasured fraction and sharp-bound width cannot increase. Similarly, complete actual return measures at least all outcomes returned by the selective law for a given assignment and source.

That monotonicity holds for the specified finite target population even when the missingness and return mechanisms are MNAR. It does **not** identify the latent response mechanism or establish that random assignment resolves hidden-Y selection bias in a regression estimator.

## Replication and independence

There are 32 independent primitive generating blocks in each of two native-unit designs, for 64 complete sources. Each complete source receives paired MAR/MNAR observation masks and four return/assignment design combinations. The resulting 512 analysis records are correlated repeated measurements on the source conditions. Multiple gaze coordinates, time positions and three trials from one participant are not new independent generating blocks.

Source means shown in plots are descriptive averages across 32 independent block-level bound widths within the stated fixed cell, without advertised confidence intervals. Bound widths for the contrast may exceed one because a difference of two separately bounded means lies within [-1,1] and its full possible width can be two.

## Independent numerical gate and unresolved problems

R89 original source CI [#39696542346](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39696542346) passed 12/12 dedicated jobs. Separately coded R89-A [#39697384391](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39697384391) passed 4/4, including mandatory actual original-archive replay. The replay reconstructed all 512 original rows, outcome and observation-process streams, finite-population bounds, refusals and source-summary denominators.

For precise artifacts, archived checkout, repaired provenance check and immutability contracts, see the [evidence ledger](../development/w3-r89-original-independent-evidence-ledger.md).

These results do not bound the functional regression coefficient, identify a field-data MNAR return parameter or validate 90% simultaneous functional bands. Issues [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) and [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) remain OPEN; release 1.2/PyPI HOLD.
