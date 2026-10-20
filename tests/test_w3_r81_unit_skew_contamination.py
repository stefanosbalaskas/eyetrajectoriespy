"""R81 frozen new-source original numerical, PSD, falsification and checksum gates."""
from __future__ import annotations

from hashlib import sha256
import json

import numpy as np
import pytest

from scripts import run_w3_r81_unit_skew_contamination as study
from scripts import run_w3_r71_new_known_gaussian_band_oracle as known
from scripts.run_w3_fixed_truth_interval_pilot import independent_hc1_oracle


def _refused(block,config,support,variance):
    n,trials,design=study.config_info(config)
    return {
        "study":study.STUDY,"block":block,"config":config,"design":design,
        "support":support,"variance":variance,
        "source_seed":study.seed(block,config,support,variance,"source"),
        "gaussian_seed":study.seed(block,config,support,variance,"gaussian"),
        "wild_seed":study.seed(block,config,support,variance,"wild"),
        "reg025_seed":study.seed(block,config,support,variance,"reg025"),
        "reg050_seed":study.seed(block,config,support,variance,"reg050"),
        "native_units":n,"observed_curves":n*trials,
        "number_of_extreme_anchor_units":study.ANCHORS[support],
        "completed":False,"refused":True,
        "exception":{"type":"PreservedSourceRefusal","message":"not accepted"},
        "not_90pct_calibrated":True,"release_authorized":False,
        "true_reference_is_simulation_known_AR1":True,
        "true_reference_nonseseparable_spatial_temporal":True,
        "true_reference_independent_unit_student_t5":True,
        "true_reference_skewed_centered_bernoulli_unit_contamination":True,
        "no_MNAR_missingness":True,
    }


def _grid():
    return [_refused(b,c,s,v) for b in range(study.BLOCKS)
            for c in study.CONFIGS for s in study.SUPPORT for v in study.VARIANCES]


def test_prespecified_source_grid_and_per_reference_seed_independence():
    assert study.STUDY.startswith("W3_R81_")
    assert (study.SOURCE_SEED,study.GAUSSIAN_SEED,study.WILD_SEED,
            study.REG025_SEED,study.REG050_SEED)==(
                202610208180,202610208181,202610208182,202610208183,202610208184)
    assert study.BLOCKS==32 and study.SOURCE_CASES==256 and study.B==999
    assert study.ANCHORS=={"two_anchors":2,"sixteen_anchors":16}
    assert study.REGULARIZATION==(("REG025",.25),("REG050",.50))
    assert study.SHARDS==tuple((i,i+4) for i in range(0,32,4))
    assert len(study.MAX_ARRAYS)==5
    assert study.AR_RHO==.72
    assert study.LATENT_CROSS_RHO==.45
    assert study.STUDENT_DF==5
    assert study.CONTAMINATION_P==.08
    assert study.CONTAMINATION_A==.16
    np.testing.assert_allclose(study.trial_cross_correlation()[[0,-1]],[.15,.80])
    np.testing.assert_allclose(study.trial_time_sd()[[0,-1]],[.028,.052])
    for domain in ("gaussian","wild","reg025","reg050"):
        assert len({study.seed(b,c,s,v,domain) for b in range(32)
                    for c in study.CONFIGS for s in study.SUPPORT
                    for v in study.VARIANCES})==256
    with pytest.raises(ValueError,match="frozen NEW"):
        study.seed(32,"curve_standard","two_anchors","constant","source")
    with pytest.raises(ValueError,match="frozen NEW"):
        study.seed(0,"curve_standard","eight_anchors","constant","source")


@pytest.mark.parametrize("config",study.CONFIGS)
def test_paired_source_innovations_and_analytic_true_law(config):
    y=[]
    for support in study.SUPPORT:
        _,_,truth,X,Y,scale=study.simulate(0,config,support,"constant")
        _,_,truth2,XX,Z,s=study.simulate(
            0,config,support,"predictor_heteroskedastic")
        np.testing.assert_array_equal(X,XX)
        np.testing.assert_array_equal(truth,truth2)
        assert np.count_nonzero(np.abs(X[:,1])==4)==study.ANCHORS[support]
        assert np.all(X[:study.ANCHORS[support]//2,1]==-4.)
        assert np.all(X[-study.ANCHORS[support]//2:,1]==4.)
        np.testing.assert_array_equal(scale,np.ones(len(X)))
        np.testing.assert_array_equal(s,1.+.75*np.abs(X[:,1]))
        resid=Y-np.einsum("np,ptd->ntd",X,truth)
        hetero=Z-np.einsum("np,ptd->ntd",X,truth)
        np.testing.assert_allclose(hetero,resid*s[:,None,None],atol=5e-14,rtol=0)
        y.append(resid)
        _,_,design=study.config_info(config)
        a=(np.linalg.inv(X.T@X)@X.T)[1]
        np.testing.assert_allclose(
            study.exact_heterogeneous_slope_se(X,s,design),
            np.sqrt(np.sum((a*s)**2)*study.source_unit_variance(design)),
            atol=1e-14,rtol=0)
    np.testing.assert_allclose(y[0],y[1],atol=5e-14,rtol=0)


@pytest.mark.parametrize("config",study.CONFIGS)
def test_regularized_covariance_exact_matrix_psd_and_gaussian_standardization(config):
    _,_,_,X,Y,_=study.simulate(0,config,"two_anchors","predictor_heteroskedastic")
    beta,_=independent_hc1_oracle(X,Y)
    factor,hc3,hat=study.estimated_HC3_slope_factor(X,Y,beta)
    assert (hat<1).all()
    c=factor.T@factor
    v=np.diag(c).reshape(31,2)
    smooth=np.stack([np.mean(v[max(0,t-3):min(31,t+4)],axis=0)
                     for t in range(31)],axis=0).reshape(-1)
    for lam in (.25,.50):
        candidate,chol,se=study.regularized_covariance(factor,lam)
        expected=(1-lam)*c+lam*np.diag(smooth)
        np.testing.assert_allclose(candidate,expected,atol=1e-14,rtol=0)
        np.testing.assert_allclose(chol@chol.T,expected,atol=1e-13,rtol=0)
        np.testing.assert_allclose(se.reshape(-1),np.sqrt(np.diag(expected)),
                                   atol=1e-14,rtol=0)
        assert np.linalg.eigvalsh(candidate).min()>0
        rng=np.random.default_rng(777)
        raw=study.regularized_gaussian_maxima(chol,se,rng,draws=99)
        assert raw.shape==(99,) and (raw>=0).all() and np.isfinite(raw).all()
    with pytest.raises(ValueError,match="not prespecified"):
        study.regularized_covariance(factor,.99)
    with pytest.raises(ValueError,match="not prespecified"):
        study.regularized_covariance(factor,.25,window=5)
    with pytest.raises(ValueError,match="shape"):
        study.regularized_covariance(factor[:,:-1],.25)


def test_changed_true_scaled_AR1_covariance_and_999_maxima():
    L=study.temporal_chol()
    expected=study.AR_RHO**np.abs(
        np.arange(len(study.TIME))[:,None]-np.arange(len(study.TIME))[None,:])
    np.testing.assert_allclose(L@L.T,expected,atol=1e-14,rtol=0)
    for design in ("curve","participant"):
        variance=study.generating_unit_variance(design)
        assert variance.shape==(len(study.TIME),len(study.DIMS))
        assert np.all(variance>0)
        config="curve_standard" if design=="curve" else "participant_standard"
        _,_,_,X,_,scales=study.simulate(0,config,"two_anchors","constant")
        z=study.true_correlation_maxima(design,np.random.default_rng(202610208181),X=X,unit_sd=scales)
        assert z.shape==(999,) and np.isfinite(z).all() and np.min(z)>=0
    _,_,_,X,Y,_=study.simulate(
        0,"curve_standard","two_anchors","constant")
    expected_Y=Y
    assert expected_Y.shape==(72,31,2)
    # True temporal covariance has AR1 correlation; spatial covariance is nonseparable.
    assert expected[0,1]==pytest.approx(.72)
    rng=np.random.default_rng(90791)
    before=rng.standard_normal((12000,31,2))
    changed=study.mix_trial_coordinates(before)
    for i,expected_rho in [(0,.15),(15,.475),(30,.80)]:
        assert np.corrcoef(changed[:,i,0],changed[:,i,1])[0,1]==pytest.approx(expected_rho,abs=.025)
    latent=study.mix_participant_latent(rng.standard_normal((12000,1,2)))
    assert np.corrcoef(latent[:,0,0],latent[:,0,1])[0,1]==pytest.approx(.45,abs=.025)
    np.testing.assert_allclose(
        np.var(changed[:,[0,30],:],axis=0),np.ones((2,2)),atol=.05,rtol=0)


def test_centered_asymmetric_unit_contamination_and_true_variance():
    h=study.contamination_shape()
    assert h.shape==(31,2)
    np.testing.assert_allclose(h[0],[.75,-.4875])
    np.testing.assert_allclose(h[-1],[1.,-.65])
    g=study.generating_unit_variance("curve")
    expected=(.16**2)*(.08)*(.92)*h*h
    np.testing.assert_allclose(study.source_unit_variance("curve")-g,expected)
    for d in ("curve","participant"):
        assert np.all(study.source_unit_variance(d)>g.min())
    rng=np.random.default_rng(8286)
    z=study.unit_contamination(rng,160000)
    assert z.shape==(160000,) and np.isfinite(z).all()
    assert np.mean(z)==pytest.approx(0,abs=.005)
    assert np.mean(z*z)==pytest.approx(.08*.92,abs=.005)
    assert np.mean(z**3)>0.035
    _,_,_,X,_,scale=study.simulate(0,"curve_standard","two_anchors","constant")
    se=study.exact_heterogeneous_slope_se(X,scale,"curve")
    a=(np.linalg.inv(X.T@X)@X.T)[1]
    np.testing.assert_allclose(se*se, np.sum((a*scale)**2)*study.source_unit_variance("curve"))


def test_student_t_radial_law_and_design_conditional_known_oracle():
    rng=np.random.default_rng(5519)
    q=study.unit_student_radial(rng,(90000,))
    assert np.isfinite(q).all() and np.all(q>0)
    assert np.mean(q*q)==pytest.approx(1.,abs=.018)
    assert np.quantile(q,.99)>1.6
    _,_,_,X,_,scales=study.simulate(
        0,"curve_standard","two_anchors","predictor_heteroskedastic")
    ref=study.true_correlation_maxima(
        "curve",np.random.default_rng(31415),X=X,unit_sd=scales)
    assert ref.shape==(999,) and np.isfinite(ref).all()
    changed=study.true_correlation_maxima(
        "curve",np.random.default_rng(31415),X=X,unit_sd=np.ones_like(scales))
    assert not np.array_equal(ref,changed)
    with pytest.raises(ValueError,match="requires original"):
        study.true_correlation_maxima("curve",np.random.default_rng(31415))


@pytest.mark.parametrize("config",study.CONFIGS)
def test_original_actual_W3_and_five_999_draw_references(config):
    row=study.evaluate(0,config,"two_anchors","predictor_heteroskedastic")
    assert row["completed"],row["exception"]
    assert row["refused"] is False
    assert row["OLS_HC1_package_oracle_error"]<=study.TOL
    assert row["W3_wild_package_critical_error"]<=study.TOL
    assert not row["release_authorized"] and row["not_90pct_calibrated"]
    assert set(row["cell_truth_included"])==set(study.CELLS)
    for name in study.MAX_ARRAYS:
        v=np.asarray(row["raw_reference_maxima"][name])
        assert v.shape==(999,)
        assert np.isfinite(v).all()
        assert row["reference_criticals"][name]==np.quantile(
            v,.90,method="higher")
    for name in study.CELLS:
        assert row["cell_truth_included"][name] is bool(
            row["cell_observed_pivots"][name] <=
            row["reference_criticals"][name.split("/")[1]])
    for key in ("REG025","REG050"):
        ratio=row["regularized_ratio_statistics"][key]
        se=np.asarray(row["regularized_se_grids"][key])
        truth=np.asarray(row["known_SE_grid"])
        np.testing.assert_allclose(ratio["mean"],np.mean(se/truth))
        np.testing.assert_allclose(ratio["p10"],np.quantile(se/truth,.1))
        assert ratio["minimum"]<=ratio["p10"]<=ratio["mean"]


def test_complete_grid_refusal_provenance_and_no_coverage_qualification():
    cases=_grid()
    report=study.summarize(cases)
    assert report["source_cases"]==256
    assert report["regularization_strengths"]==[.25,.50]
    assert report["fixed_time_smoothing_window"]==7
    assert report["true_AR1_rho"]==.72
    np.testing.assert_allclose(report["true_cross_coordinate_trial_rho_endpoints"],[.15,.80])
    assert report["true_latent_cross_coordinate_rho"]==.45
    assert report["independent_unit_student_df"]==5
    assert report["contamination_unit_probability"]==.08
    assert report["contamination_unit_amplitude"]==.16
    np.testing.assert_allclose(
        report["contamination_shape_endpoints"],
        [[.75,-.4875],[1.,-.65]])
    np.testing.assert_allclose(report["true_time_SD_endpoints"],[.028,.052])
    assert sum(report[name] for name in (
        "original_wild_999_multiplier_positions","known_Student_t5_skewed_contamination_maxima",
        "HC3_Gaussian_maxima","REG025_Gaussian_maxima",
        "REG050_Gaussian_maxima"))==256*999*5
    assert report["no_90pct_simultaneous_band_calibration"]
    assert report["release_authorized"] is False
    for c in study.CONFIGS:
        for s in study.SUPPORT:
            for v in study.VARIANCES:
                assert report["results"][c][s][v]["refused"]==32
    cases.pop()
    with pytest.raises(ValueError,match="incomplete or duplicated"):
        study.summarize(cases)
    cases=_grid()
    cases[0]["reg050_seed"]+=1
    with pytest.raises(ValueError,match="provenance"):
        study.summarize(cases)
    cases=_grid()
    cases[0]["release_authorized"]=True
    with pytest.raises(ValueError,match="withheld calibration"):
        study.summarize(cases)


def test_immutable_eight_source_shards_and_tamper_refusal(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","f"*40)
    folder=tmp_path/"parts"
    cases=_grid()
    for lo,hi in study.SHARDS:
        dst=folder/f"source-{lo}"
        dst.mkdir(parents=True)
        rows=[x for x in cases if lo<=x["block"]<hi]
        raw=(json.dumps(rows,sort_keys=True,indent=2)+"\n").encode()
        (dst/"cases.json").write_bytes(raw)
        (dst/"manifest.json").write_text(json.dumps({
            "study":study.STUDY,"start":lo,"stop":hi,
            "source_seed":study.SOURCE_SEED,"gaussian_seed":study.GAUSSIAN_SEED,
            "wild_seed":study.WILD_SEED,"reg025_seed":study.REG025_SEED,
            "reg050_seed":study.REG050_SEED,"number_cases":len(rows),
            "source_checkout":"f"*40,"cases_sha256":sha256(raw).hexdigest(),
        }))
    out=tmp_path/"out"
    study.aggregate(out,folder)
    assert json.loads((out/"summary.json").read_text())["source_cases"]==256
    assert len((out/"SHA256SUMS").read_text().splitlines())==3
    tampered=folder/"source-0"/"cases.json"
    tampered.write_bytes(tampered.read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        study.aggregate(tmp_path/"reject",folder)
