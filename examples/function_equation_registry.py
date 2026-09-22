"""Inspect implementation-matched mathematical contracts programmatically."""

from eyetrajectoriespy import (
    get_mathematical_contract,
    list_mathematical_contracts,
    mathematical_contract_frame,
)


contracts = list_mathematical_contracts()
print(f"registered contracts: {len(contracts)}")

fpca = get_mathematical_contract("fit_mfpca")
print(fpca.title)
print("functions:", ", ".join(fpca.public_api))
print("site anchor:", fpca.site_anchor)
for equation in fpca.equations:
    print(equation)

frame = mathematical_contract_frame()
print(frame[["contract_key", "function", "site_anchor"]].to_string(index=False))

assert not frame.empty
assert frame["function"].is_unique
assert get_mathematical_contract("fpca") is fpca
