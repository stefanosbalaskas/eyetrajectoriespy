"""Executable transfer-entropy specification-sensitivity example."""

import numpy as np

from eyetrajectoriespy import transfer_entropy_parameter_sensitivity

rng = np.random.default_rng(42)
n = 1400
source = rng.integers(0, 2, size=n)
target = np.zeros(n, dtype=int)
noise = rng.random(n) < 0.08
target[1:] = np.bitwise_xor(source[:-1], noise[1:].astype(int))

result = transfer_entropy_parameter_sensitivity(
    source,
    target,
    target_histories=(1, 2),
    source_histories=(1, 2),
    source_lags=(1, 2, 3, 4),
    shifts=range(40, 60),
)

assert result.n_specifications == 16
assert result.has_surrogate_inference
lag_one = result.table.loc[
    (result.table["target_history"] == 1)
    & (result.table["source_history"] == 1)
    & (result.table["source_lag"] == 1),
    "transfer_entropy_bits",
].iloc[0]
lag_two = result.table.loc[
    (result.table["target_history"] == 1)
    & (result.table["source_history"] == 1)
    & (result.table["source_lag"] == 2),
    "transfer_entropy_bits",
].iloc[0]
assert lag_one > lag_two

print(result.table)
print(result.summary_table)
