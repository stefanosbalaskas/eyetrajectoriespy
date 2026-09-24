# Transfer-entropy specification sensitivity

Version 0.42 adds a **descriptive specification-sensitivity layer** around the
0.41 discrete transfer-entropy estimator. The purpose is to show how strongly
the reported directed predictive information depends on defensible choices of
target history, source history, and source lag.

The package evaluates the full declared Cartesian multiverse

[
Theta=mathcal K	imesmathcal L	imesmathcal D,
]

and, for every (	heta=(k,l,d)inTheta), computes

[
T_{	heta}
=
I!left(X_{t-d}^{(l)};Y_tmid Y_{t-1}^{(k)}ight).
]

This is **not** an automatic history/lag selector.

## Why sensitivity analysis belongs in the API

Practical TE estimation is conditional on temporal-history and delay choices.
Vicente et al. (2011, DOI `10.1007/s10827-010-0262-3`) explicitly show that
embedding dimension and delay can materially affect TE estimates and that
larger state reconstructions can reduce estimator accuracy at fixed data
length. The direct eye/head TE application by Zhang et al. (2024, DOI
`10.3390/e26010003`) fixed both history lengths to one and explicitly noted
that alternative history lengths were outside that study's scope.

Accordingly, `transfer_entropy_parameter_sensitivity()` treats plausible
analysis choices as a declared robustness multiverse rather than searching for
the combination that maximizes TE.

## API

```python
from eyetrajectoriespy import transfer_entropy_parameter_sensitivity

result = transfer_entropy_parameter_sensitivity(
    source,
    target,
    target_histories=(1, 2, 3),
    source_histories=(1, 2),
    source_lags=(1, 2, 3, 4),
)
```

Every Cartesian-product combination is evaluated. Invalid combinations abort
the complete analysis with the offending `k`, `l`, and `d` identified.
Failed specifications are never omitted from a summary table.

## Retained support diagnostics

Each row retains:

- empirical TE in bits;
- effective transition count and fraction;
- observed target-history count;
- observed joint target/source-history count;
- singleton joint-history fraction;
- minimum, maximum, and mean joint-history cell count.

These diagnostics matter because increasing history depth expands the empirical
state space while reducing the number of transitions available to populate it.
The package records that deterioration; it does not silently impose a
minimum-count threshold or delete sparse rows.

## Optional common surrogate null

A fixed set of analyst-declared circular source shifts can be passed once:

```python
result = transfer_entropy_parameter_sensitivity(
    source,
    target,
    target_histories=(1, 2),
    source_histories=(1, 2),
    source_lags=(1, 2, 3),
    shifts=range(40, 80),
)
```

The **identical shift set** is used for every specification. Each row then also
retains the surrogate mean, surrogate-centered TE,

[
Delta T_{	heta}
=
T_{	heta,mathrm{obs}}
-
rac{1}{B}sum_{b=1}^{B}T_{	heta,b}^{*},
]

the plus-one upper-tail p-value, its attainable resolution, and the number of
shifts.

The p-values are not adjusted merely because they appear in one sensitivity
table. If the scientific analysis turns multiple specifications into formal
hypothesis tests, the multiplicity plan must be declared separately.

## Plotting without hidden averaging

`plot_transfer_entropy_sensitivity()` plots one declared parameter at a time.
If any non-plotted sensitivity dimension still contains multiple values, the
function refuses to average across them. Supply explicit filters instead:

```python
from eyetrajectoriespy import plot_transfer_entropy_sensitivity

ax = plot_transfer_entropy_sensitivity(
    result,
    parameter="source_lag",
    filters={
        "target_history": 1,
        "source_history": 1,
    },
)
```

This makes every plotted line correspond to one exact sensitivity slice.

## Interpretation

A robust result is one whose substantive interpretation remains similar across
the **predeclared scientifically defensible** specifications. A sensitive
result should be reported as specification-dependent.

Do not:

- choose the largest TE and call it the primary estimate;
- choose the smallest p-value after scanning histories/lags;
- remove combinations because their support diagnostics look inconvenient;
- describe the fraction of positive/significant specifications as a posterior
  probability;
- interpret pairwise TE robustness as causal identification.

The multiverse is descriptive robustness evidence. It is not a sampling
distribution, posterior distribution, or model-selection algorithm.

## Reporting minimum

Report the complete history/lag grids, number of evaluated specifications,
whether the grid was preregistered or exploratory, TE range/median, support
diagnostics, and any restricted plotting slice. With surrogate inference,
report the common shift rule/set, number of shifts, surrogate-centered TE
variation, unadjusted p-value range, and any separate multiplicity procedure.

See the
[worked example](../examples/transfer-entropy-sensitivity.md),
[mathematical reference](mathematical-reference.md#transfer-entropy-sensitivity),
and [base transfer-entropy guide](transfer-entropy.md).
