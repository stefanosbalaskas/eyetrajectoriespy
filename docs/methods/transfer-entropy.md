# Discrete transfer entropy

Transfer entropy (TE) is an **experimental directed-dependence diagnostic** in
`eyetrajectoriespy` 0.41. It asks whether a declared source history improves
prediction of the next target state beyond the information already present in
the target's own history.

For discrete source states \(X_t\) and target states \(Y_t\), the package
estimates

\[
T_{X\rightarrow Y}(k,l,d)
= I\!\left(X_{t-d}^{(l)};Y_t\mid Y_{t-1}^{(k)}\right),
\]

where \(k\) is the target-history length, \(l\) is the source-history length,
and \(d\ge1\) is the source lag in sample-index units. The empirical plug-in
estimate is reported in bits.

## Explicit state representation

`discrete_transfer_entropy()` accepts only one-dimensional **integer-coded
discrete states**. It never bins, rounds, quantizes, smooths, interpolates,
rescales, or otherwise converts continuous gaze coordinates into states. For
continuous gaze, pupil, head-motion, or physiological signals, state
construction is an upstream scientific decision and must be documented
separately.

This matters because TE can change materially with discretization, history
length, sampling interval, and source lag. The package therefore has no
automatic history/lag optimizer and no default binning rule. Finite-sample
support is exposed instead of hidden.

## Histories and lag

With `target_history=k`, the target history at index \(t\) is

\[
(Y_{t-1},\ldots,Y_{t-k}),
\]

and with `source_history=l` and `source_lag=d`, the source history is

\[
(X_{t-d},\ldots,X_{t-d-l+1}).
\]

All three settings are required. The result retains the effective number of
transitions, source/target state counts, numbers of target and joint histories,
minimum/maximum joint-history support, and the fraction of joint histories
observed only once. These are diagnostics for sparse empirical support, not
automatic validity thresholds.

## Local transfer entropy

`transfer_entropy_local_frame()` exposes each local log-ratio contribution
with the exact target/source histories used at that sample index. Local
contributions can be negative even when mean TE is positive; they are not
silently truncated or converted to zero.

## Circular-shift surrogate test

`transfer_entropy_circular_shift_test()` compares observed TE with TE obtained
after **analyst-declared circular shifts of the complete source series**. The
shift set is mandatory and is never generated, optimized, filtered, or selected
automatically.

The procedure reports the plus-one upper-tail Monte Carlo value

\[
p_{+}=\frac{1+\sum_b I(T_b^*\ge T_{obs})}{B+1},
\]

plus the surrogate mean and the surrogate-centered difference
\(T_{obs}-\bar T^*\).

Circular shifts preserve the source marginal exactly and retain its circular
ordering while changing source-target alignment. They are appropriate only
when wrap-around/stationarity assumptions are scientifically defensible. For
strongly nonstationary trials or meaningful trial boundaries, use a null model
designed for that structure rather than treating circular shifts as universal.

## Interpretation boundary

A positive TE estimate means that, under the declared state representation,
history lengths, lag, and sampling design, the empirical source history
contains predictive information about the target beyond the declared target
history. It is **not by itself evidence of causal influence**. Common drivers,
unobserved history, state construction, temporal aggregation, finite-sample
bias, and nonstationarity can all affect the result.

The 0.41 API intentionally does not expose automatic discretization,
conditional/multivariate TE, continuous estimators, network inference, lag
scanning, multiple-testing correction, or a causal-graph interpretation.

## Evidence and direct eye/head precedent

Schreiber introduced transfer entropy as a conditional information-transfer
measure in 2000 (Phys. Rev. Lett. 85, 461–464,
DOI `10.1103/PhysRevLett.85.461`). A direct eye/head application is Zhang et
al. (2024), *Entropy* 26(1), 3, DOI `10.3390/e26010003`, which used
bidirectional TE for head-eye coordination in driving. These precedents support
the method family, not automatic causal interpretation or the package's
specific surrogate contract.

## Reporting minimum

Report at least the source/target state definitions, sampling unit, \(k\),
\(l\), \(d\), effective transitions, empirical TE in bits, joint-history
support diagnostics, and—if surrogate testing is used—the complete shift
rule/set, number of shifts, surrogate mean, plus-one p-value, and attainable
resolution.

See the [mathematical reference](mathematical-reference.md#discrete-transfer-entropy)
and [worked example](../examples/transfer-entropy.md).
