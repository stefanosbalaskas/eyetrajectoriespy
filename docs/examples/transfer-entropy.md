# Worked discrete transfer-entropy example

This example uses already-discrete binary states. No continuous gaze variable is
silently converted into categories.

```python
import numpy as np
from eyetrajectoriespy import (
    discrete_transfer_entropy,
    transfer_entropy_circular_shift_test,
    transfer_entropy_local_frame,
)

rng = np.random.default_rng(7)
n = 1500
source = rng.integers(0, 2, size=n)
target = np.zeros(n, dtype=int)
noise = rng.random(n) < 0.08
target[1:] = np.bitwise_xor(source[:-1], noise[1:].astype(int))

forward = discrete_transfer_entropy(
    source,
    target,
    target_history=1,
    source_history=1,
    source_lag=1,
)
reverse = discrete_transfer_entropy(
    target,
    source,
    target_history=1,
    source_history=1,
    source_lag=1,
)

print(forward.transfer_entropy_bits)
print(reverse.transfer_entropy_bits)
print(transfer_entropy_local_frame(forward).head())
```

The synthetic mechanism makes the target depend on the previous source state,
so the forward estimate should be substantially larger than the reverse
estimate. That is a numerical recovery check for this synthetic mechanism, not
a general causal-inference rule.

## Explicit circular-shift comparison

```python
shift_test = transfer_entropy_circular_shift_test(
    source,
    target,
    target_history=1,
    source_history=1,
    source_lag=1,
    shifts=range(50, 100),
)

print(shift_test.observed.transfer_entropy_bits)
print(shift_test.surrogate_mean_bits)
print(shift_test.surrogate_centered_transfer_entropy_bits)
print(shift_test.upper_tail_p_value)
```

The smallest possible plus-one p-value with 50 supplied shifts is \(1/51\).
Increasing the number of shifts increases Monte Carlo resolution; it does not
repair an inappropriate surrogate null.

## Continuous gaze requires an upstream representation decision

Do not pass raw `x(t)` or `y(t)` values to this API and expect automatic
binning. If a research question requires TE between continuous gaze-derived
signals, preregister and justify the state/estimator construction first. The
package fails rather than silently choosing that scientific decision for you.
