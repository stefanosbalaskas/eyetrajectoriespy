"""Synthetic discrete transfer-entropy example for the 0.41 development line."""

import numpy as np

from eyetrajectoriespy import (
    discrete_transfer_entropy,
    transfer_entropy_circular_shift_test,
)

rng = np.random.default_rng(7)
n = 1500
source = rng.integers(0, 2, size=n)
target = np.zeros(n, dtype=int)
noise = rng.random(n) < 0.08
target[1:] = np.bitwise_xor(source[:-1], noise[1:].astype(int))

forward = discrete_transfer_entropy(
    source, target, target_history=1, source_history=1, source_lag=1
)
reverse = discrete_transfer_entropy(
    target, source, target_history=1, source_history=1, source_lag=1
)
assert forward.transfer_entropy_bits > 0.5
assert reverse.transfer_entropy_bits < 0.01

shift_test = transfer_entropy_circular_shift_test(
    source,
    target,
    target_history=1,
    source_history=1,
    source_lag=1,
    shifts=range(50, 100),
)
assert shift_test.observed.transfer_entropy_bits > shift_test.surrogate_mean_bits
assert shift_test.upper_tail_p_value == 1 / 51

print(f"forward_TE_bits={forward.transfer_entropy_bits:.6f}")
print(f"reverse_TE_bits={reverse.transfer_entropy_bits:.6f}")
print(f"shift_mean_bits={shift_test.surrogate_mean_bits:.6f}")
print(f"plus_one_p={shift_test.upper_tail_p_value:.6f}")
