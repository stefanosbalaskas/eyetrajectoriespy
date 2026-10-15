"""R38 dual-seed, exact-zero profile geometry numerical contracts."""
import numpy as np
from scripts import run_w3_r38_dualseed_profile_geometry as r38
from scripts import run_w3_r37_continuous_boundary_reml as r37
from scripts.w3_r20_estimated_working_target import observed_weighted_rows
from scripts.w3_r25_gaussian_reml_components import prepare_reml_design


def test_same_original_source_and_frozen_discrepancy_targets():
    assert r38.BLOCK == 2
    assert r38.REUSED_SEED == r37.MASTER_SEED
    assert r38.PLANNED_CASES == 4
    assert r38.PLANNED_FITS == 160
    assert r38.PROFILE_RATIOS[0] == 0.
    assert r38.PROFILE_RATIOS[-1] == 10.
    assert 1.75 in r38.PROFILE_RATIOS
    assert 3.5 in r38.PROFILE_RATIOS


def test_projected_KKT_residual_handles_exact_boundary_correctly():
    b = [(0., 2.),(-1., 1.),(0., 10.)]
    # At x=0, positive score points into feasible increasing objective:
    # it satisfies first-order lower-bound optimality.
    x = np.array([0., 1., 3.])
    g = np.array([5., -4., -2.])
    np.testing.assert_allclose(
        r38.projected_gradient(g,x,b), [0., 0., -2.]
    )
    np.testing.assert_allclose(
        r38.projected_gradient([-3.,4.,0.],x,b), [-3.,4.,0.]
    )


def test_R37_continuous_and_R35_fixed_slope_objective_consistency_at_zero():
    case = r37.source(2,"ordinary_dependent","zero_slope")
    X,y,w,g,t,tr,x = observed_weighted_rows(
        (None,case[1],case[2],case[3],case[4],None),"legendre5"
    )
    prepared = prepare_reml_design(
        X,y,w,g,t,tr,x,slope="predictor_scaled_slope"
    )
    ref = 1.
    pars = np.array([0.,0.,0.,0.])
    o,gradient = r37.continuous_reml_objective(pars,prepared,ref)
    from scripts import run_w3_r35_slope_boundary_profiles as r35
    of,gradf = r35.fixed_slope_reml_objective(pars[:3],prepared,ref,0.)
    np.testing.assert_allclose(o,of,atol=1e-9,rtol=1e-11)
    np.testing.assert_allclose(gradient[:3],gradf,atol=1e-7,rtol=1e-8)
    assert np.isfinite(gradient[3])


def test_summary_refuses_incomplete_without_renaming_as_replication():
    rows = [{"source_block":2,"support":"ordinary_dependent",
             "true_state":"zero_slope","base_status":"failed",
             "profile_points":[],"candidate_diagnostics":[]}]
    summary = r38.summarize(rows)
    assert summary["missing_cases"] == 3
    assert summary["base_failure_count"] == 1
    assert summary["independent_generating_blocks_in_R38"] == 0
    assert summary["recorded_profile_fits"] == 0
    assert summary["no_type_I_or_power_inference"]
    assert not summary["release_authorized"]
