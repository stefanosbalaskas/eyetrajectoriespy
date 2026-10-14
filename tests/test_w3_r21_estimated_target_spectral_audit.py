"""R21 original-source spectral diagnostic contracts; never conceal failures."""
import hashlib
import numpy as np
import pytest
from scripts import run_w3_r20_estimated_target_pilot as pilot
from scripts import run_w3_r21_estimated_target_spectral_audit as spec


@pytest.mark.parametrize("block,n,support,model,family",[
    (0,24,"ordinary_independent","legendre5","shared_slope"),
    (0,24,"extreme_independent","legendre5","predictor_scaled_slope"),
    (1,24,"ordinary_dependent","legendre5","shared_slope"),
    (4,48,"ordinary_dependent","cubic_spline13","shared_slope"),
])
def test_observed_source_eigen_decomposition_preserves_failures(block,n,support,model,family):
    original=pilot.evaluate(block,n,support,model,family)
    d=spec.diagnose(block,n,support,model,family)
    assert d["status"]=="ok",d["exception"]
    assert d["observed_only_estimation"]
    assert d["source_covariance_oracle_not_used"]
    assert d["min_fitted_phi_eigenvalue"]>0
    assert np.isfinite(d["min_residual_D_eigenvalue"])
    assert not d["release_authorized"]
    if original["status"]=="failed":
        assert original["error"]["message"]=="nonpositive or ill-conditioned working covariance"


def test_original_failure_hash_requires_no_case_omission():
    a=[{"block":0,"n_participants":24,"source_support":"ordinary_independent",
        "mean_basis":"legendre5","working_family":"shared_slope","status":"failed"}]
    s=spec.summarize([spec.diagnose(0,24,"ordinary_independent","legendre5","shared_slope")],a)
    assert s["original_source_failed_cases"]==1
    assert s["recorded_original_cases"]==1
    assert s["missing_diagnostics"]==255
    assert not s["matches_frozen_original_failure_set"]
    assert not s["inference_qualified"]
