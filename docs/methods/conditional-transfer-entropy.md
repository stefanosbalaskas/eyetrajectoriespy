# Conditional transfer entropy

Version 0.43 adds **discrete conditional transfer entropy (CTE)** as a narrow
extension of the package's explicit 0.41 transfer-entropy contract.

For source process (X), target process (Y), and an explicitly supplied
conditioning process (Z), the estimand is

[
T_{X\rightarrow Y\mid Z}(k,l,m,d,c)
=
I\!\left(
X_{t-d}^{(l)};
Y_t
\mid
Y_{t-1}^{(k)},
Z_{t-c}^{(m)}
\right).
]

It asks how much predictive information the declared source history contributes
about the next target state **beyond both the target's own past and the
declared conditioning-process past**.

This is a conditional predictive-information measure. It is not labelled
"causal conditional TE."

## API

```python
from eyetrajectoriespy import conditional_transfer_entropy

result = conditional_transfer_entropy(
    source,
    target,
    condition,
    target_history=1,
    source_history=1,
    condition_history=1,
    source_lag=1,
    condition_lag=1,
)
```

All three input sequences must be one-dimensional, equal-length,
integer-coded discrete states. The package does not bin, round, interpolate,
smooth, scale, or otherwise create the state representation.

History lengths and lags are mandatory positive integers in sample-index units.

## Empirical estimator

For observed histories

[
\mathbf y=Y_{t-1}^{(k)},\qquad
\mathbf x=X_{t-d}^{(l)},\qquad
\mathbf z=Z_{t-c}^{(m)},
]

the empirical plug-in local contribution is

[
t_{X\rightarrow Y\mid Z}
=
\log_2
\frac{
\widehat p(y_t\mid\mathbf y,\mathbf x,\mathbf z)
}{
\widehat p(y_t\mid\mathbf y,\mathbf z)
}.
]

The reported CTE is the mean local contribution across the exact effective
transitions retained by the declared history/lag contract.

## Support accountability

`ConditionalTransferEntropyResult` retains substantially more than the scalar
estimate:

- every local CTE contribution and effective sample index;
- the complete source, target, and conditioning state arrays;
- exact target-, source-, and conditioning-history arrays for every effective
  transition;
- numbers of source, target, and conditioning states;
- observed target-history and conditioning-history counts;
- observed target+conditioning, source+conditioning, and complete
  target+source+conditioning history-state counts;
- singleton complete-joint-history fraction;
- minimum, maximum, and mean complete-joint-history cell counts;
- all histories, lags, estimator conventions, and provenance.

No empirical-support threshold is imposed automatically. A sparse support table
is therefore visible rather than silently filtered or converted into a
trustworthy-looking estimate.

## Constant-conditioning identity

When the conditioning process is constant and does not alter the effective
sample window, the conditional estimator reduces exactly to the ordinary
pairwise TE estimator. This identity is included as a regression test.

## Common-driver interpretation

Conditioning can be useful when a specified process offers an alternative
common-driver explanation for pairwise information transfer. In the package's
constructed validation system,

```text
Z_t -> X_t
Z_(t-1) -> Y_t
```

pairwise (T_{X\rightarrow Y}) is large because (X_{t-1}) reveals the same
driver that determines (Y_t). Conditioning on (Z_{t-1}) removes that
redundant predictive contribution.

This behavior must not be generalized into the rule that conditional TE is
always smaller than pairwise TE. Conditional mutual information can also
increase when the conditioning process exposes synergistic information.

## Source-only circular-shift test

```python
from eyetrajectoriespy import (
    conditional_transfer_entropy_circular_shift_test,
)

test = conditional_transfer_entropy_circular_shift_test(
    source,
    target,
    condition,
    target_history=1,
    source_history=1,
    condition_history=1,
    source_lag=1,
    condition_lag=1,
    shifts=range(40, 80),
)
```

Only the source is circularly shifted. Target and conditioning process remain
fixed. For the declared shift set, the package computes

[
p_+
=
\frac{
1 + \sum_{b=1}^{B}
\mathbb I(T_b^{*,cond}\ge T_{obs}^{cond})
}{
B+1
}.
]

The result retains the full surrogate CTE distribution, surrogate mean,
surrogate-centered CTE, plus-one upper-tail p-value, attainable resolution,
exact shifts, and which processes were shifted or fixed.

The circular-shift null requires a defensible wrap-around/stationarity
assumption. The package never generates, optimizes, or filters shifts.

## Interpretation boundary

> Conditional transfer entropy measures incremental directed predictive
> information after conditioning on the explicitly supplied process. It does
> not establish causal influence or guarantee adjustment for unmeasured common
> drivers.

That distinction follows the information-dynamics literature, which separates
information transfer from causal effect and treats conditional TE as a
conditional information-transfer measure rather than automatic causal
identification.

## Deliberate 0.43 exclusions

Version 0.43 does **not** add:

- conditional-TE history/lag sensitivity grids;
- multiple simultaneous conditioning processes;
- continuous/KSG conditional TE;
- automatic state discretization;
- TE networks or edge-search procedures;
- automatic causal discovery;
- time-varying/windowed TE;
- automatic support thresholds or adequacy rules.

The TE mini-series ends here. The next package-level inferential priority
returns to simultaneous inference for functional mixed-effects coefficient
functions.

## Reporting

Report the discrete state definitions, all five history/lag settings
((k,l,m,d,c)), number of effective transitions, CTE in bits, complete
joint-history support diagnostics, and the scientific role of the supplied
conditioning process.

For surrogate testing, report the exact shift rule/set, number of shifts,
surrogate mean, surrogate-centered CTE, plus-one p-value and attainable
resolution. State explicitly that only the source was shifted and that target
and conditioning processes were held fixed.

See the
[worked example](../examples/conditional-transfer-entropy.md),
[base TE guide](transfer-entropy.md),
and
[mathematical reference](mathematical-reference.md#conditional-transfer-entropy).
