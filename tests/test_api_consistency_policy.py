import inspect

import eyetrajectoriespy as et


def test_public_export_list_has_no_duplicates():
    assert len(et.__all__) == len(set(et.__all__))


def test_reporting_helper_suffix_is_consistent():
    reporting = [
        name
        for name in et.__all__
        if "reporting" in name.lower()
    ]
    assert reporting
    assert all(name.endswith("_reporting_text") for name in reporting)


def test_canonical_bootstrap_randomness_uses_random_state():
    for name in (
        "bootstrap_function_on_scalar_coefficients",
        "bootstrap_functional_mixed_effects_coefficients",
        "bootstrap_generalized_function_on_scalar_coefficients",
    ):
        signature = inspect.signature(getattr(et, name))
        assert "random_state" in signature.parameters


def test_canonical_simultaneous_inference_uses_confidence_level():
    for name in (
        "function_on_scalar_simultaneous_bands",
        "functional_mixed_effects_simultaneous_bands",
        "generalized_function_on_scalar_simultaneous_bands",
    ):
        signature = inspect.signature(getattr(et, name))
        assert "confidence_level" in signature.parameters
