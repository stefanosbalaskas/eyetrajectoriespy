# Worked conditional transfer-entropy example

This example contrasts pairwise TE with conditional TE in a deliberately simple
common-driver system.

```python
import numpy as np

from eyetrajectoriespy import (
    conditional_transfer_entropy,
    conditional_transfer_entropy_circular_shift_test,
    discrete_transfer_entropy,
)

rng = np.random.default_rng(11)
n = 4000

condition = rng.integers(0, 2, size=n)
source = condition.copy()
target = np.zeros(n, dtype=int)
target[1:] = condition[:-1]

pairwise = discrete_transfer_entropy(
    source,
    target,
    target_history=1,
    source_history=1,
    source_lag=1,
)

conditioned = conditional_transfer_entropy(
    source,
    target,
    condition,
    target_history=1,
    source_history=1,
    condition_history=1,
    source_lag=1,
    condition_lag=1,
)

print(pairwise.transfer_entropy_bits)
print(conditioned.conditional_transfer_entropy_bits)
```

Here \(X_{t-1}\) predicts \(Y_t\), but it does so because both expose the same
declared \(Z_{t-1}\) driver. Pairwise TE is therefore large, whereas
conditional TE collapses in this constructed truth.

That is a validation example, not a universal expectation: conditioning may
also reveal synergistic information.

## Direct contribution plus a common driver

Now let the source state contain both the common-driver bit and an independent
innovation:

```python
rng = np.random.default_rng(12)
n = 5000
condition = rng.integers(0, 2, size=n)
innovation = rng.integers(0, 2, size=n)

source = 2 * condition + innovation
target = np.zeros(n, dtype=int)
target[1:] = source[:-1]

conditioned_direct = conditional_transfer_entropy(
    source,
    target,
    condition,
    target_history=1,
    source_history=1,
    condition_history=1,
    source_lag=1,
    condition_lag=1,
)

print(conditioned_direct.conditional_transfer_entropy_bits)
```

After conditioning on the common-driver bit, the source still contributes the
independent innovation. The synthetic truth therefore retains about one bit of
conditional TE.

## Source-only surrogate null

```python
shift_test = conditional_transfer_entropy_circular_shift_test(
    source,
    target,
    condition,
    target_history=1,
    source_history=1,
    condition_history=1,
    source_lag=1,
    condition_lag=1,
    shifts=range(80, 120),
)

print(shift_test.upper_tail_p_value)
print(
    shift_test.surrogate_centered_conditional_transfer_entropy_bits
)
```

Only `source` is shifted. `target` and `condition` remain fixed.

## Inspect finite support

```python
print(conditioned_direct.n_effective)
print(conditioned_direct.n_joint_histories)
print(conditioned_direct.singleton_joint_history_fraction)
print(conditioned_direct.min_joint_history_count)
print(conditioned_direct.mean_joint_history_count)
print(conditioned_direct.max_joint_history_count)
```

These diagnostics should be inspected especially when \(k\), \(l\), or \(m\)
are large relative to the available series length.
