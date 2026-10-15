"""Original R20 failure identity must survive the R22 numerical audit."""
import numpy as np
import pytest
from scripts import run_w3_r22_original_256case_audit as audit
from scripts import run_w3_r20_estimated_target_pilot as old
from scripts import run_w3_r21_estimated_target_spectral_audit as frozen


@pytest.mark.parametrize("block,n,support,model,family",[
    (0,24,"ordinary_independent","legendre5","shared_slope"),
    (0,24,"ordinary_dependent","legendre5","predictor_scaled_slope"),
    (4,48,"extreme_dependent","cubic_spline13","shared_slope"),
])
def test_unmodified_original_source_with_explicit_numerical_refusal(block,n,support,model,family):
    historic=old.evaluate(block,n,support,model,family)
    candidate=audit.evaluate(block,n,support,model,family)
    assert historic["status"] in ("ok","failed")
    assert candidate["new_status"] in ("ok","refused")
    assert candidate["original_status_unmodified"]
    assert not candidate["pointwise_coverage_qualified"]
    assert not candidate["release_authorized"]
    if candidate["new_status"]=="ok":
        assert candidate["relative_identity_error"]<=3e-7
        assert candidate["stable_cr2_se"]>0
        assert candidate["stable_satterthwaite_df"]>0
    else:
        assert candidate["new_error"] is not None


def test_full_original_case_set_mandatory_for_claims():
    h=old.evaluate(0,24,"ordinary_independent","legendre5","shared_slope")
    n=audit.evaluate(0,24,"ordinary_independent","legendre5","shared_slope")
    with pytest.raises(ValueError,match="incomplete"):
        audit.summarize([n],[h])
    assert frozen.ORIGINAL_FAILED_CASES==41
    assert len(frozen.ORIGINAL_FAILURE_KEY_SHA256)==64
