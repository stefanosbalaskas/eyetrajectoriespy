"""R16 four-cell source, numerical and no-promotion contracts."""
import numpy as np
import pytest
from scripts.run_w3_r16_leverage_covariance_factorial import (
    source,fit,evaluate,SIZES,MODELS,SUPPORT,BLOCKS,audit
)

def test_paired_four_cells_preserve_original_timestamps_and_innovations():
    cases={s:source(0,24,s) for s in SUPPORT}
    originals=[c[0] for c in cases.values()]
    for key in ("time","n_trials","participant_intercept","participant_slope",
                "trial_noise","sensor_noise"):
        for r in originals[1:]:
            np.testing.assert_array_equal(r[key],originals[0][key])
    for mode in ("independent","dependent"):
        a=cases["ordinary_"+mode]
        b=cases["extreme_"+mode]
        assert a[0]["covariance_mode"]==b[0]["covariance_mode"]==mode
        for t,u in zip(a[1].time,b[1].time):
            np.testing.assert_array_equal(t,u)
    for leverage in ("ordinary","extreme"):
        a=cases[leverage+"_independent"]
        b=cases[leverage+"_dependent"]
        np.testing.assert_array_equal(a[2],b[2])
        assert any(not np.array_equal(t,u) for t,u in zip(a[1].values,b[1].values))

@pytest.mark.parametrize("model",MODELS)
@pytest.mark.parametrize("support",SUPPORT)
def test_four_cell_numerical_and_oracle_contract(model,support):
    d=fit(source(0,24,support),model)
    assert d["qr_delta"]<4e-7 and d["score_delta"]<4e-7
    assert d["cr1_se"]>0 and d["oracle_se"]>0 and d["jack_se"]>0
    assert abs(d["contrast_leverage_sum"]-1)<1e-10
    assert 1<=d["contrast_effective_clusters"]<=24+1e-8
    assert 0<d["contrast_max_partial_leverage"]<1
    assert d["contrast_top_two_partial_leverage"]>=d["contrast_max_partial_leverage"]
    assert np.isfinite(d["contrast_max_standardized_influence"])
    r=evaluate(0,24,support,model)
    assert r["status"]=="ok",r["exception"]
    assert not r["release_authorized"]
    assert not r["method_winner_selected"]
    assert not r["simultaneous_bands_qualified"]
    assert r["public_dense_W3_rejects_async"]

@pytest.mark.parametrize("model",MODELS)
def test_leverage_is_crossed_with_covariance(model):
    for mode in ("independent","dependent"):
        a=fit(source(0,24,"ordinary_"+mode),model)
        b=fit(source(0,24,"extreme_"+mode),model)
        assert b["first_two_mean_block_leverage"]>a["first_two_mean_block_leverage"]
        assert b["max_block_leverage"]>a["max_block_leverage"]

def test_ledger_denominators_and_failure_inclusion():
    ok=evaluate(0,24,"ordinary_independent","legendre5")
    bad=dict(ok,support="ordinary_dependent",status="failed",
             exception={"type":"ScientificFailure","message":"retained"})
    report=audit([ok,bad])
    assert report["planned_cases"]==BLOCKS*len(SIZES)*len(SUPPORT)*len(MODELS)==2304
    assert report["recorded_cases"]==2
    assert report["completed_cases"]==1 and report["failed_cases"]==1
    assert len(report["missing_cases"])==2302
    assert report["no_method_winner"] and not report["release_authorized"]


@pytest.mark.parametrize("model",MODELS)
def test_focal_contrast_diagnostics_respond_to_extreme_x(model):
    for covariance in ("independent","dependent"):
        base=fit(source(0,24,"ordinary_"+covariance),model)
        extreme=fit(source(0,24,"extreme_"+covariance),model)
        assert extreme["contrast_max_partial_leverage"]>base["contrast_max_partial_leverage"]
        assert extreme["contrast_effective_clusters"]<base["contrast_effective_clusters"]
