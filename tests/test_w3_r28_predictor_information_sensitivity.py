"""R28 predeclared hypothetical predictor-spread information contracts."""
import numpy as np
import pytest

from scripts import run_w3_r27_reml_information_audit as original
from scripts import run_w3_r28_predictor_information_sensitivity as r28


@pytest.mark.parametrize("block,n",[(0,24),(15,96)])
def test_predictor_independent_source_is_negative_control(block,n):
    # Scaling x only reparameterizes fixed effect columns and leaves the
    # matched independent-source covariance K unchanged; P is invariant.
    baseline=original.information_for_original_design(block,n,"ordinary_independent")
    base=baseline["info_log"]
    for multiplier in r28.PREDICTOR_MULTIPLIERS:
        changed=original.information_for_original_design(
            block,n,"ordinary_independent",predictor_multiplier=multiplier)
        np.testing.assert_allclose(changed["info_log"],base,rtol=1e-7,atol=3e-8)
        np.testing.assert_allclose(changed["relative_local_component_SE"],
                                   baseline["relative_local_component_SE"],
                                   rtol=1e-7,atol=1e-8)


def test_scaled_predictor_dependent_working_covariance_is_not_metadata_only():
    base=original.information_for_original_design(0,24,"ordinary_dependent")
    other=original.information_for_original_design(0,24,"ordinary_dependent",
                                                   predictor_multiplier=2.)
    assert np.linalg.norm(other["info_log"]-base["info_log"])>1e-4
    assert np.linalg.eigvalsh(other["info_log"])[0]>0
    assert other["hypothetical_predictor_multiplier"]==2.
    assert not other["original_source_design_only"]
    assert base["original_source_design_only"]


def test_unregistered_hypothetical_multipliers_refused():
    for m in (0,-1,float("nan")):
        with pytest.raises(ValueError,match="multiplier"):
            original.information_for_original_design(
                0,24,"ordinary_dependent",predictor_multiplier=m)


def test_prespecified_reproduction_of_original_r27_slope_information():
    assert r28.ORIGINAL_BLOCKS==(0,15)
    assert r28.ORIGINAL_N==(24,96)
    assert r28.PLANNED==32
    a=r28.evaluate(0,24,"ordinary_independent",1.)
    assert a["status"]=="ok",a["exception"]
    np.testing.assert_allclose(
        a["slope_log_variance_local_SE"],4.534792824732694,
        rtol=3e-8,atol=1e-8)
    assert a["is_exact_original_predictor_design"]
    summary=r28.summarize([a])
    assert summary["recorded_cases"]==1
    assert summary["missing_cases"]==31
    assert summary["new_independent_generating_blocks"]==0
    assert not summary["study_design_inference_qualified"]
    assert not summary["release_authorized"]
