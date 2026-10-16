"""R41 outcome-selected original R40 exceptional-case identity and refusal tests."""
import numpy as np
import pytest

from scripts import run_w3_r41_targeted_kkt_refinement as r41


def test_freeze_parent_original_sha_and_target_denominators():
    assert len(r41.PARENT_CASES_SHA256)==64
    assert r41.PARENT_CASES_SHA256=="7943b6ea869c242ba8b7ee7c00a7025af755f2d9ef7d9e9aaec1e36c4009c349"
    assert len(r41.EXCEPTIONS)==18
    assert len(r41.CONTROLS)==15
    assert r41.PLANNED_EVALUATIONS==33
    assert r41.PLANNED_FITS==99
    assert r41.METHODS==(
        "original_R40_raw_linear",
        "stricter_LBFGSB_restart",
        "independent_SLSQP_restart",
    )
    assert not set(r41.EXCEPTIONS)&set(r41.CONTROLS)
    for c in r41.CONTROLS:
        assert c[:4] in {t[:4] for t in r41.EXCEPTIONS}


def test_physical_kkt_sign_at_original_strictly_positive_box():
    lo,hi=r41.r39.LOW,r41.r39.HIGH
    grad=np.array([5.,-2.,4.])
    good=r41.r39.projected_residual(
        grad,np.array([lo,hi,2.])
    )
    np.testing.assert_array_equal(good,[0.,0.,4.])
    bad=r41.r39.projected_residual(
        np.array([-1.,1.,0.]),np.array([lo,hi,1.])
    )
    np.testing.assert_array_equal(bad,[-1.,1.,0.])


def test_original_source_is_reused_not_new_random_generator():
    block,support,state,slope,start=r41.EXCEPTIONS[0]
    prepared,ref,n=r41.r40.prepare_case(block,support,state)
    assert block==0 and slope==.75 and n>0 and ref>0
    assert len(prepared)==24
    x=np.asarray(r41.r40.SEED_RATIOS[start],dtype=float)
    value,gradient=r41.objective(x,prepared,ref,slope)
    assert np.isfinite(value)
    assert gradient.shape==(3,) and np.isfinite(gradient).all()


def test_original_exception_is_reproduced_and_is_not_relabelled():
    # This is the first of the 18 frozen R40 failures; selected post hoc.
    original=r41.evaluate_case(r41.EXCEPTIONS[0],True,{})
    assert original["source_status"]=="ok",original["error"]
    assert len(original["fits"])==len(r41.METHODS)
    assert original["fits"][0]["status"]=="ok"
    assert original["fits"][0]["fit"]["passes_frozen_physical_KKT"] is False
    assert original["was_selected_after_original_R40_outcomes"] is True
    assert original["independent_R41_generator_block"] is False
    assert original["release_authorized"] is False


def test_refusal_and_negative_outcomes_retained_in_summary():
    test_rows=[
        {"block":0,"support":"ordinary_dependent","state":"zero_slope",
         "fixed_random_slope_ratio":.75,"initialization":"interior",
         "source_status":"failed","error":"source failed",
         "original_R40_KKT_exception":True,"fits":[]}
    ]
    stats=r41.summarize(test_rows)
    assert stats["planned_optimizer_fits"]==99
    assert stats["recorded_optimizer_fits"]==0
    assert stats["source_errors_or_drift"]==1
    assert not stats["all_cases_replayed_and_refinements_attempted"]
    assert stats["NEW_independent_primitive_blocks"]==0
    assert not stats["type_I_power_calibration"]
    assert not stats["release_authorized"]


def test_duplicate_source_identity_refused():
    record={"block":0,"support":"ordinary_dependent","state":"zero_slope",
            "fixed_random_slope_ratio":.75,"initialization":"interior",
            "source_status":"failed","error":None,
            "original_R40_KKT_exception":True,"fits":[]}
    with pytest.raises(ValueError,match="Duplicate"):
        r41.summarize([record,record])
