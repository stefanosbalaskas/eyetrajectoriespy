"""W3 R92 prospectively frozen actual-return/nominal-response fragility gates."""
import numpy as np
import pytest
from scripts import run_w3_r92_return_fragility as r


def test_fresh_14336_source_records_and_registered_scenarios():
    assert r.N_SOURCES==64
    assert r.N_RECORDS==14336
    assert len(r.SCENARIOS)==7
    assert r.ASSIGNMENT_FRACTIONS==(.25,.50)
    assert r.NOMINAL_FAILURE_RATES==(.01,.05,.15)
    assert r.ASSIGNMENT_REPLICATES==8
    assert len(r.SHARDS)==8
    assert set(r.SEEDS.values())==set(range(202610229200,202610229205))
    with pytest.raises(ValueError,match="primitive block"):
        r.generate(32,"independent_curves")
    with pytest.raises(ValueError,match="assignment repetition"):
        r.paired_audit_uniforms(0,"independent_curves",8,(4,))


def test_return_failure_laws_are_distinct_and_monotone():
    y=np.array([-.8,0.,.8,9.])
    all_c=r.actual_return_probability(y,"complete",0.)
    np.testing.assert_array_equal(all_c,np.ones_like(y))
    for d in r.NOMINAL_FAILURE_RATES:
        uniform=r.actual_return_probability(y,"uniform",d)
        selective=r.actual_return_probability(y,"outcome_selective",d)
        np.testing.assert_array_equal(uniform,np.full_like(y,1.-d))
        np.testing.assert_allclose(selective,1.-d*(.5+r.bounded_value(y)))
        assert 0 < selective.min() <= selective.max() <=1
        assert selective[0]>selective[-1]
    for law in ("uniform","outcome_selective"):
        rates=[r.actual_return_probability(y,law,d)
               for d in r.NOMINAL_FAILURE_RATES]
        assert all(np.all(a>=b) for a,b in zip(rates[:-1],rates[1:]))


def test_nominal_observed_only_cannot_see_hidden_gaze():
    m=np.array([1,1,1,1],bool)
    secondary=np.array([1,0,0,0],bool)
    recovered=np.array([0,1,0,0],bool)
    y=np.array([.1,-.2,np.nan,np.nan])
    got=r.observed_only_nominal_ht(y,m,secondary,recovered,.5,.05)
    z=r.bounded_value(y[secondary|recovered])
    assert got["assignment_only"]==pytest.approx((z[0]+2*z[1])/4)
    assert got["nominal_uniform_completion"]==pytest.approx((z[0]+z[1]/(.5*.95))/4)
    with pytest.raises(ValueError,match="hidden unreturned outcome leaked"):
        r.observed_only_nominal_ht(np.array([.1,-.2,.4,np.nan]),m,secondary,recovered,.5,.05)
    with pytest.raises(ValueError,match="observed-outcome provenance"):
        r.observed_only_nominal_ht(y,m,secondary,secondary,.5,.05)
    with pytest.raises(ValueError,match="policy probabilities"):
        r.observed_only_nominal_ht(y,m,secondary,recovered,0.,.05)
    with pytest.raises(ValueError,match="scenario"):
        r.actual_return_probability(y,"nonregistered",.05)


def test_analytic_complete_and_uniform_response_does_not_bias_nominal_weighting():
    for config in r.CONFIGS:
        rows=r.evaluate(0,config)
        assert len(rows)==2*8*2*7
        assert len({row["Y_digest"] for row in rows})==1
        for mechanism in r.MECHANISMS:
          target=[v for v in rows if v["mechanism"]==mechanism]
          assert len({v["initial_missing_digest"] for v in target})==1
          for rep in range(8):
           for g in r.ASSIGNMENT_FRACTIONS:
            pairs={(v["return_law"],v["nominal_failure"]):v for v in target
                   if v["rep"]==rep and v["g"]==g}
            assert pairs[("complete",0.)]["failure_n"]==0
            for law,d in r.SCENARIOS:
                v=pairs[(law,d)]
                assert v["return_n"]<=v["assigned_n"]
                assert v["release_authorized"] is False
                assert v["data_fitting_did_not_receive_hidden_return_probability"]
                assert np.isfinite(v["nominal_correction_realized_error"])
                if law in ("complete","uniform"):
                    assert abs(v["oracle_design_nominal_bias_simulator_only"])<1e-10
            for law in ("uniform","outcome_selective"):
                f=[pairs[(law,d)]["failure_n"] for d in r.NOMINAL_FAILURE_RATES]
                assert f==sorted(f)
                q=[pairs[(law,d)]["return_n"] for d in r.NOMINAL_FAILURE_RATES]
                assert q==sorted(q,reverse=True)


def test_fail_closed_source_aggregation(tmp_path):
    with pytest.raises(ValueError,match="four-block"):
        r.shard(tmp_path/"bad",2,6)
    with pytest.raises(ValueError,match="all eight"):
        r.aggregate(tmp_path/"out",tmp_path/"none")
    with pytest.raises(ValueError,match="ledger incomplete"):
        r.summarize([])
