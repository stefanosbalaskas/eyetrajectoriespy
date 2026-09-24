"""Executable conditional transfer-entropy example."""

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

assert pairwise.transfer_entropy_bits > 0.95
assert abs(conditioned.conditional_transfer_entropy_bits) < 1e-12

rng = np.random.default_rng(12)
n = 5000
condition = rng.integers(0, 2, size=n)
innovation = rng.integers(0, 2, size=n)
source = 2 * condition + innovation
target = np.zeros(n, dtype=int)
target[1:] = source[:-1]

direct = conditional_transfer_entropy(
    source,
    target,
    condition,
    target_history=1,
    source_history=1,
    condition_history=1,
    source_lag=1,
    condition_lag=1,
)
assert 0.95 < direct.conditional_transfer_entropy_bits < 1.05

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
assert shift_test.surrogate_centered_conditional_transfer_entropy_bits > 0.9

print(pairwise.transfer_entropy_bits)
print(conditioned.conditional_transfer_entropy_bits)
print(direct.conditional_transfer_entropy_bits)
print(shift_test.upper_tail_p_value)
