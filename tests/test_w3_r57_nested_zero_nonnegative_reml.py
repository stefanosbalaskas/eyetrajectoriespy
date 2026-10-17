"""R57 genuine nested theta_slope=0 Gaussian REML and refusal contracts."""
import hashlib
import json

import numpy as np
import pytest

from scripts import run_w3_r16_leverage_covariance_factorial as r16
from scripts import run_w3_r53_local_reml_influence as r53
from scripts import run_w3_r56_true_zero_slope_diagnostic as r56
from scripts import run_w3_r57_nested_zero_nonnegative_reml as r57
from scripts.w3_r25_gaussian_reml_components import prepare_reml_design


def test_new_source_seed_and_full_predeclared_start_denominators():
    assert r57.MASTER_SEED!=r53.SOURCE_SEED
    assert r57.MASTER_SEED!=r56.MASTER_SEED
    assert r57.BLOCKS==8 and r57.PARTICIPANTS==24
    assert r57.N_SOURCE_CASES==32
    assert r57.N_MODEL_FITS==64
    assert r57.N_SOLVER_STARTS==192
    assert r57.SHARDS==((0,2),(2,4),(4,6),(6,8))
    assert any(s[-1]==0. for _,s in r57.ALT_STARTS)
    assert r57.NESTED_MONOTONIC_TOL==1e-5
    zero=r57.independent_source(0,r57.SUPPORT[0])
    extreme=r57.independent_source(0,r57.SUPPORT[1])
    newer=r57.independent_source(1,r57.SUPPORT[0])
    old=r56.independent_primitive_source(0,r57.SUPPORT[0])
    np.testing.assert_array_equal(
        zero[0]["participant_slope"],extreme[0]["participant_slope"])
    assert not np.array_equal(
        zero[0]["participant_slope"],newer[0]["participant_slope"])
    assert not np.array_equal(
        zero[0]["participant_slope"],old[0]["participant_slope"])
    with pytest.raises(ValueError,match="outside"):
        r57.independent_source(8,r57.SUPPORT[0])


def test_exact_zero_source_counterfactual_subtracts_only_gaussian_slope():
    parts,info=r57.pair_data(0,r57.SUPPORT[0])
    z=parts["true_zero"];p=parts["true_positive"]
    src=r57.independent_source(0,r57.SUPPORT[0])
    ui=src[0]["participant_slope"][z["group"].astype(int),0,0,0]
    expected=r16.SIGMA_RANDOM_SLOPE*ui*z["x"]*(1+.25*z["time"])
    np.testing.assert_allclose(p["y"]-z["y"],expected,
                               rtol=2e-13,atol=2e-13)
    for name in ("X","w","group","time","trial","x","contrast"):
        np.testing.assert_array_equal(p[name],z[name])
    assert p["truth"]==z["truth"]
    assert info["same_native_design_mean_and_non_slope_innovations"]


def test_nested_objectives_agree_at_true_zero_exactly():
    inputs,_=r57.pair_data(0,r57.SUPPORT[0])
    data=inputs["true_zero"]
    observed=[data[k] for k in ("X","y","w","group","time","trial","x")]
    prepared=prepare_reml_design(*observed,slope="predictor_scaled_slope")
    reference=r57._reference(data)
    free=np.log(np.array([.10,.15,.9]))
    null_value,null_grad=r57.objective(
        free,prepared,reference,"exact_zero")
    alternative=np.r_[free,0.]
    alt_value,alt_grad=r57.objective(
        alternative,prepared,reference,"nonnegative")
    assert null_value==pytest.approx(alt_value,rel=2e-11,abs=2e-9)
    np.testing.assert_allclose(
        null_grad,alt_grad[:3],rtol=2e-8,atol=2e-7)
    # A genuinely nonnegative alternative has a meaningful *one-sided*
    # analytic slope score at the structural zero boundary.
    epsilon=1e-5
    alt_upper=alternative.copy();alt_upper[3]+=epsilon
    fupper,_=r57.objective(alt_upper,prepared,reference,"nonnegative")
    assert (fupper-alt_value)/epsilon==pytest.approx(
        alt_grad[3],rel=3e-3,abs=2e-3)


def test_one_sided_structural_zero_KKT_does_not_hide_negative_score():
    params=np.r_[np.log([.1,.2,1.]),0.]
    # A negative slope score at zero points toward increasing slope variance,
    # violating the lower-bound KKT for the alternative.
    violation,_,_=r57.physical_projected_kkt(
        params,np.array([0.,0.,0.,-2.]),"nonnegative")
    assert violation==pytest.approx(2.)
    valid,ratios,_=r57.physical_projected_kkt(
        params,np.array([0.,0.,0.,2.]),"nonnegative")
    assert valid==pytest.approx(0.)
    assert ratios[3]==0.
    assert r57.physical_projected_kkt(
        np.log([.1,.2,1.]),np.zeros(3),"exact_zero")[0]==pytest.approx(0.)


def test_numerical_candidate_frozen_start_counts_and_nested_null():
    inputs,_=r57.pair_data(0,r57.SUPPORT[1])
    data=inputs["true_zero"]
    prepared=prepare_reml_design(
        *(data[k] for k in ("X","y","w","group","time","trial","x")),
        slope="predictor_scaled_slope")
    ref=r57._reference(data)
    # The two objectives represent the same restricted Gaussian law.
    null=r57.fit_model(prepared,ref,"exact_zero")
    alt=r57.fit_model(prepared,ref,"nonnegative")
    assert len(null["original_starts"])==2
    assert len(alt["original_starts"])==4
    assert null["null_includes_exact_zero_variance"]
    assert alt["alternative_includes_structural_zero"]
    assert null["global_optimum_proven"] is False
    assert alt["global_optimum_proven"] is False
    if null["status"]=="accepted":
        assert null["selected_slope_ratio"]==0.
        assert null["selected_physical_KKT"]<=r57.KKT_TOL
    if alt["status"]=="accepted":
        assert alt["selected_slope_ratio"]>=0.
        assert alt["selected_physical_KKT"]<=r57.KKT_TOL
    # Genuine numerical refusals remain permitted and must not be
    # recategorized as a zero test rejection.


def test_full_denominator_and_sha256_shard_replacement_refused(tmp_path,monkeypatch):
    cases=[r57.empty_case(b,s,state) for b in range(r57.BLOCKS)
           for s in r57.SUPPORT for state in r57.STATES]
    for c in cases:
        c["null_fit"]=r57._not_attempted_model("exact_zero")
        c["alternative_fit"]=r57._not_attempted_model("nonnegative")
    report=r57.summarize(cases)
    assert report["complete_failure_inclusive_source_and_start_ledger"]
    assert report["recorded_numerical_optimizer_start_slots"]==192
    assert not report["release_authorized"]
    with pytest.raises(ValueError,match="duplicate"):
        r57.summarize(cases+[cases[0]])
    monkeypatch.setenv("GITHUB_SHA","frozen-original-R57-checkout")
    parts=tmp_path/"source_parts"
    for start,stop in r57.SHARDS:
        path=parts/f"blocks-{start}"
        path.mkdir(parents=True)
        group=[c for c in cases if start<=c["block"]<stop]
        r57._write(path/"cases.json",group)
        r57._write(path/"manifest.json",{
            "study":r57.STUDY,"start":start,"stop":stop,
            "new_source_seed":r57.MASTER_SEED,
            "original_checkout":"frozen-original-R57-checkout",
            "records":len(group),
            "SHA256_cases":hashlib.sha256(
                (path/"cases.json").read_bytes()).hexdigest(),
        })
    r57.aggregate(tmp_path/"full",parts)
    (parts/"blocks-0"/"cases.json").write_text("tampered")
    with pytest.raises(ValueError,match="SHA256"):
        r57.aggregate(tmp_path/"corrupt",parts)


def test_nonfinite_evidence_refused(tmp_path):
    with pytest.raises(ValueError):
        r57._write(tmp_path/"invalid.json",{"nonfinite":float("nan")})
