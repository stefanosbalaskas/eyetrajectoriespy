import pandas as pd
import pytest

import eyetrajectoriespy as et


def test_registry_is_stable_unique_and_public():
    contracts = et.list_mathematical_contracts()

    assert isinstance(contracts, tuple)
    assert len(contracts) >= 10

    keys = [contract.key for contract in contracts]
    anchors = [contract.site_anchor for contract in contracts]
    assert len(keys) == len(set(keys))
    assert len(anchors) == len(set(anchors))

    registered = []
    for contract in contracts:
        assert isinstance(contract, et.MathematicalContract)
        assert contract.title
        assert contract.scope
        assert contract.public_api
        assert contract.equations
        assert all(equation.strip() for equation in contract.equations)
        assert all("$$" not in equation for equation in contract.equations)
        registered.extend(contract.public_api)

    assert len(registered) == len(set(registered))
    for function_name in registered:
        assert function_name in et.__all__
        assert hasattr(et, function_name)
        assert callable(getattr(et, function_name))


def test_lookup_by_key_and_function_returns_same_contract():
    by_key = et.get_mathematical_contract("fpca")
    by_function = et.get_mathematical_contract("fit_mfpca")

    assert by_key is by_function
    assert "fit_fpca" in by_key.public_api
    assert by_key.site_anchor == "fpca"


@pytest.mark.parametrize("bad", [None, 1, True, ["fpca"]])
def test_lookup_rejects_non_string_names(bad):
    with pytest.raises(TypeError, match="name must be a string"):
        et.get_mathematical_contract(bad)


def test_lookup_rejects_unknown_name():
    with pytest.raises(KeyError, match="No mathematical contract"):
        et.get_mathematical_contract("not-a-contract")


def test_contract_frame_is_long_form_and_deterministic():
    frame = et.mathematical_contract_frame()

    assert isinstance(frame, pd.DataFrame)
    assert list(frame.columns) == [
        "contract_key",
        "title",
        "function",
        "latex",
        "site_anchor",
        "scope",
    ]
    assert not frame.empty
    assert frame["function"].is_unique
    assert frame["latex"].str.len().gt(0).all()
    assert frame["site_anchor"].str.len().gt(0).all()
    assert frame.equals(et.mathematical_contract_frame())


def test_registry_lookup_covers_every_frame_row():
    frame = et.mathematical_contract_frame()
    for row in frame.itertuples(index=False):
        contract = et.get_mathematical_contract(row.function)
        assert contract.key == row.contract_key
        assert contract.site_anchor == row.site_anchor
        assert row.latex == "\n\n".join(contract.equations)
