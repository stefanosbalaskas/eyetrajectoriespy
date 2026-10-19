"""R71 prospectively known Gaussian-law benchmark and refusal-inclusive source tests."""
from __future__ import annotations

from hashlib import sha256
import json

import numpy as np
import pytest

from scripts import run_w3_r71_new_known_gaussian_band_oracle as r71


def _case(b,design,support,complete=False):
    n=72 if design=="curve" else 36
    row={
        "study":r71.STUDY,"block":b,"design":design,"support":support,
        "source_seed":r71.SOURCE_SEED+10007*b+r71.DESIGNS.index(design),
        "wild_seed":r71.wild_seed(b,design,support),
        "independent_units":n,"observed_curves":n if design=="curve" else n*3,
        "completed":complete,"exception":None if complete else {"type":"SyntheticSourceRefusal","message":"kept"},
        "OLS_oracle_max_error":0. if complete else None,
        "HC1_oracle_max_error":0. if complete else None,
        "package_wild_max_reference_error":0. if complete else None,
        "no_nominal_90pct_wild_band_qualification":True,
        "known_covariance_not_observed_data_estimator":True,
        "release_authorized":False,
    }
    if complete:
        ref=r71.known_law_reference(design)
        row.update({
            "known_law_slope_truth_included":True,
            "original_wild_HC1_slope_truth_included":False,
            "min_HC1_over_known_SE":.8,"mean_HC1_over_known_SE":.85,
            "max_HC1_over_known_SE":.95,
            "wild_critical_over_known_law_critical":.8,
            "known_law_critical":ref["critical"],
            "original_wild_critical":ref["critical"]*.8,
            "wild_999_raw_slope_maxima":[1.]*r71.WILD_B,
        })
    else:
        row.update({
            "known_law_slope_truth_included":None,
            "original_wild_HC1_slope_truth_included":None,
            "wild_999_raw_slope_maxima":None,
        })
    return row


def _all(complete=False):
    return [_case(b,d,s,complete) for b in range(r71.BLOCKS)
            for d in r71.DESIGNS for s in r71.SUPPORT]


def test_exact_frozen_gaussian_covariance_and_counts():
    assert r71.BLOCKS==32 and r71.SOURCE_CASES==128
    assert r71.ORACLE_K==32767
    assert r71.ORACLE_TOTAL==65534
    assert r71.WILD_DRAW_POSITIONS==127872
    assert r71.SHARDS==((0,8),(8,16),(16,24),(24,32))
    assert r71.SOURCE_SEED==202610197171
    assert r71.ORACLE_SEED==202610197172
    assert r71.WILD_SEED==202610197173
    np.testing.assert_allclose(
        r71.unit_covariance_variance("curve"),
        np.full((len(r71.TIME),2),.04**2),atol=1e-15,rtol=0)
    expected=(.065**2*(1+.35*r71.TIME)**2+.04**2/3)
    np.testing.assert_allclose(r71.unit_covariance_variance("participant"),
                               np.repeat(expected[:,None],2,axis=1))
    assert np.all(np.diff(expected)>0)
    with pytest.raises(ValueError,match="unknown oracle"):
        r71.known_law_reference("other")


@pytest.mark.parametrize("design",r71.DESIGNS)
def test_new_Gaussian_source_extreme_and_ordinary_share_noise_and_condition(design):
    _,_,truth,X,Y=r71.simulate(0,design,"ordinary")
    _,_,truth2,Z,W=r71.simulate(0,design,"extreme")
    np.testing.assert_array_equal(truth,truth2)
    np.testing.assert_array_equal(X[1:-1],Z[1:-1])
    assert Z[0,1]==-4 and Z[-1,1]==4
    a=Y-np.einsum("np,ptd->ntd",X,truth,optimize=True)
    b=W-np.einsum("np,ptd->ntd",Z,truth,optimize=True)
    np.testing.assert_allclose(a,b,atol=3e-14,rtol=0)
    analytic=r71.true_slope_standard_errors(Z,design)
    direct=np.sqrt(np.linalg.inv(Z.T@Z)[1,1]*r71.unit_covariance_variance(design))
    np.testing.assert_allclose(analytic,direct,atol=1e-13)
    assert analytic.shape==(31,2)
    with pytest.raises(ValueError,match="outside"):
        r71.simulate(32,design,"ordinary")


def test_exact_law_oracle_known_correlation_has_plausible_90pct_critical():
    curve=r71.known_law_reference("curve")
    participant=r71.known_law_reference("participant")
    for ref in (curve,participant):
        assert len(ref["raw_standardized_maxima"])==32767
        assert ref["critical"]==np.quantile(
            ref["raw_standardized_maxima"],.90,method="higher")
        assert 2.<ref["critical"]<5.
    # Correlated repeated participant time grid has a lower effective rank
    assert participant["critical"]<curve["critical"]


def test_full_source_actual_999_original_W3_wild_and_known_gaussian_oracle():
    observed=r71.case(0,"curve","ordinary")
    assert observed["completed"],observed["exception"]
    assert observed["OLS_oracle_max_error"]<=r71.ORACLE_TOL
    assert observed["HC1_oracle_max_error"]<=r71.ORACLE_TOL
    assert observed["package_wild_max_reference_error"]<=r71.ORACLE_TOL
    assert len(observed["wild_999_raw_slope_maxima"])==r71.WILD_B
    assert observed["original_wild_critical"]==np.quantile(
        observed["wild_999_raw_slope_maxima"],.90,method="higher")
    ratio=np.asarray(observed["observed_HC1_slope_SE_grid"])/np.asarray(
        observed["known_law_true_slope_SE_grid"])
    assert np.min(ratio)==pytest.approx(observed["min_HC1_over_known_SE"])
    assert np.mean(ratio)==pytest.approx(observed["mean_HC1_over_known_SE"])
    assert np.max(ratio)==pytest.approx(observed["max_HC1_over_known_SE"])
    assert not observed["release_authorized"]


def test_failure_inclusive_128_cases_only_32_primitive_units_per_cell():
    refused=r71.summarize(_all())
    assert refused["new_independent_primitive_generating_blocks"]==32
    assert refused["source_cases"]==128
    assert refused["original_Rademacher_wild_multiplier_draw_positions"]==127872
    assert refused["original_known_gaussian_reference_draws"]==65534
    assert refused["per_design_and_support"]["curve"]["ordinary"]["failed"]==32
    assert refused["release_authorized"] is False

    ok=r71.summarize(_all(True))
    assert ok["per_design_and_support"]["curve"]["ordinary"][
        "known_law_true_inclusions"]==32
    assert ok["per_design_and_support"]["curve"]["ordinary"][
        "original_wild_HC1_inclusions"]==0
    pair=ok["paired_truth_inclusion_diagnostics"]["curve/ordinary/known_minus_original_wild"]
    assert pair["known_only_truth_included"]==32
    assert pair["complete_matched_primitive_blocks"]==32
    assert pair["not_test_of_method_superiority"]


def test_duplicate_source_missing_999_maxima_or_fake_release_fails_closed():
    x=_all(True)
    x[0]["block"]=31
    with pytest.raises(ValueError,match="identities"):
        r71.summarize(x)
    x=_all(True)
    x[0]["wild_999_raw_slope_maxima"].pop()
    with pytest.raises(ValueError,match="999 maxima"):
        r71.summarize(x)
    x=_all(True)
    x[0]["no_nominal_90pct_wild_band_qualification"]=False
    with pytest.raises(ValueError,match="qualification flag"):
        r71.summarize(x)


def test_four_SHA256_original_shards_aggregate_and_synthetic_tamper(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","d"*40)
    parts=tmp_path/"parts"
    for lo,hi in r71.SHARDS:
        folder=parts/f"part{lo}"
        folder.mkdir(parents=True)
        rows=[_case(b,d,s) for b in range(lo,hi)
              for d in r71.DESIGNS for s in r71.SUPPORT]
        raw=(json.dumps(rows,sort_keys=True,indent=2)+"\n").encode()
        (folder/"cases.json").write_bytes(raw)
        (folder/"manifest.json").write_text(json.dumps({
            "study":r71.STUDY,"start":lo,"stop":hi,
            "source_seed":r71.SOURCE_SEED,"oracle_seed":r71.ORACLE_SEED,
            "wild_seed":r71.WILD_SEED,
            "source_checkout":"d"*40,"original_source_cases":len(rows),
            "cases_sha256":sha256(raw).hexdigest()}))
    dest=tmp_path/"complete"
    r71.aggregate(dest,parts)
    assert len((dest/"SHA256SUMS").read_text().splitlines())==4
    report=json.loads((dest/"summary.json").read_text())
    assert report["source_cases"]==128
    assert "known_gaussian_reference.json" in (dest/"SHA256SUMS").read_text()
    source=parts/"part0"/"cases.json"
    source.write_bytes(source.read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        r71.aggregate(tmp_path/"reject",parts)
