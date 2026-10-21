"""R89 nonidentification and reproducibility contracts."""
import numpy as np
import pytest

from scripts import run_w3_r89_bounded_missing_gaze as r89


def test_freeze_independent_sources_and_factorial():
    assert r89.BLOCKS == 32
    assert r89.N_SOURCES == 64
    assert r89.N_RECORDS == 512
    assert len(r89.SHARDS) == 8
    assert len(set(r89.SEEDS.values())) == 5
    assert set(r89.CONFIGS) == {"independent_curves","repeated_trial_participants"}
    assert r89.RETURN_LAWS == ("complete","outcome_selective")
    assert r89.AUDIT_FRACTIONS == (.25,.50)
    with pytest.raises(ValueError,match="invalid original"):
        r89.generate(32,"independent_curves")
    with pytest.raises(ValueError,match="invalid original stream"):
        r89.stream_seed(0,"independent_curves","unknown")


def test_true_finite_population_sharpness_and_observed_only_nonleakage():
    eligible=np.array([True,True,True,True,False])
    seen=np.array([True,False,True,False,False])
    y=np.array([0.,np.nan,.5,np.nan,777.])
    b=r89.sharp_bounds(y,eligible,seen)
    assert b["total_n"]==4
    assert b["returned_n"]==2
    assert b["unreturned_n"]==2
    assert b["lower"]==pytest.approx((.5+.75)/4)
    assert b["upper"]==pytest.approx((.5+.75+2)/4)
    assert b["width"]==pytest.approx(.5)
    corrupt=y.copy()
    corrupt[4]=-1.e8
    assert r89.sharp_bounds(corrupt,eligible,seen)==b
    with pytest.raises(ValueError,match="leaked"):
        r89.sharp_bounds(np.array([0.,123.,.5,np.nan,5.]),eligible,seen)
    with pytest.raises(ValueError,match="outside target"):
        r89.sharp_bounds(y,eligible,np.array([True,False,True,False,True]))
    with pytest.raises(ValueError,match="empty"):
        r89.sharp_bounds(np.full(5,np.nan),np.zeros(5,bool),np.zeros(5,bool))


def test_repeated_trial_and_curve_primitive_generator():
    for config,n,trials in (("independent_curves",72,1),
                            ("repeated_trial_participants",36,3)):
        x,y,mu=r89.generate(0,config)
        xx,yy,mm=r89.generate(0,config)
        assert x.shape==(n,) and y.shape==(n,trials,31,2) and mu.shape==(n,1,31,2)
        np.testing.assert_array_equal(x,xx)
        np.testing.assert_array_equal(y,yy)
        np.testing.assert_array_equal(mu,mm)
        assert np.isfinite(y).all()
        s=r89.random_streams(0,config,y.shape)
        mar=r89.first_stage_missing(x,y,mu,s["mask"],"MAR")
        mnar=r89.first_stage_missing(x,y,mu,s["mask"],"MNAR")
        assert mar.shape==y.shape and mnar.shape==y.shape
        assert mar.any() and mnar.any()
        assert not np.array_equal(mar,mnar)
        with pytest.raises(ValueError,match="first-stage"):
            r89.first_stage_missing(x,y,mu,s["mask"],"unsupported")


def test_one_actual_primitive_block_no_hidden_y_in_bounds():
    rows=r89.evaluate(0,"independent_curves")
    assert len(rows)==8
    assert len({r["original_Y_digest"] for r in rows})==1
    for row in rows:
        assert row["mean_bounds"]["lower"]<=row["simulation_true_mean_only"]
        assert row["simulation_true_mean_only"]<=row["mean_bounds"]["upper"]
        assert row["contrast_lower"]<=row["simulation_true_contrast_only"]
        assert row["simulation_true_contrast_only"]<=row["contrast_upper"]
        assert row["audit_returned_n"]<=row["audit_assigned_n"]
        assert row["release_authorized"] is False
        assert row["response_mechanism_identified"] is False
    for mechanism in r89.MECHANISMS:
        for law in r89.RETURN_LAWS:
            sub={r["audit_fraction"]:r for r in rows
                 if r["mechanism"]==mechanism and r["return_law"]==law}
            assert sub[.5]["mean_bounds"]["width"]<=sub[.25]["mean_bounds"]["width"]+1e-12
            assert sub[.5]["contrast_width"]<=sub[.25]["contrast_width"]+1e-12


def test_failed_archives_fail_closed(tmp_path):
    with pytest.raises(ValueError,match="four-block"):
        r89.shard(tmp_path/"invalid",2,9)
    with pytest.raises(ValueError,match="all eight"):
        r89.aggregate(tmp_path/"out",tmp_path/"missing")
    with pytest.raises(ValueError,match="ledger incomplete"):
        r89.summarize([])
