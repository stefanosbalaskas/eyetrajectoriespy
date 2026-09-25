# Worked transfer-entropy sensitivity example

This synthetic example contains a one-sample directed dependence from the
source to the target. It is used to demonstrate the sensitivity contract, not
to justify automatic lag selection in empirical data.

```python
import numpy as np

from eyetrajectoriespy import (
    plot_transfer_entropy_sensitivity,
    transfer_entropy_parameter_sensitivity,
    transfer_entropy_parameter_sensitivity_reporting_text,
)

rng = np.random.default_rng(42)
n = 1400
source = rng.integers(0, 2, size=n)
target = np.zeros(n, dtype=int)
noise = rng.random(n) < 0.08
target[1:] = np.bitwise_xor(source[:-1], noise[1:].astype(int))

sensitivity = transfer_entropy_parameter_sensitivity(
    source,
    target,
    target_histories=(1, 2),
    source_histories=(1, 2),
    source_lags=(1, 2, 3, 4),
    shifts=range(40, 60),
)

print(sensitivity.table)
print(sensitivity.summary_table)
print(
    transfer_entropy_parameter_sensitivity_reporting_text(
        sensitivity
    )
)
```

The result contains \(2\times2\times4=16\) rows. The row with lag one should
recover substantially more directed information in this synthetic mechanism,
but the package does not label that row "best" or automatically select it.

## Inspect one exact slice

```python
ax = plot_transfer_entropy_sensitivity(
    sensitivity,
    parameter="source_lag",
    metric="transfer_entropy_bits",
    filters={
        "target_history": 1,
        "source_history": 1,
    },
)
```

Trying to plot `source_lag` without fixing the other multi-valued dimensions
raises an error instead of silently averaging them.

## Inspect support deterioration

```python
support = sensitivity.table[
    [
        "target_history",
        "source_history",
        "source_lag",
        "n_effective",
        "n_joint_histories",
        "singleton_joint_history_fraction",
        "min_joint_history_count",
    ]
]
print(support)
```

Longer histories may increase the number of observed joint-history states while
reducing the number of observations per state. This is part of the robustness
result, not a reason for silent exclusion.
