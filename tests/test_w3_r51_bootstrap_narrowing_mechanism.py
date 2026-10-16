"""W3 R51 prospective paired Gaussian nuisance/bootstrap mechanism contracts."""
import hashlib
import json

import numpy as np
import pytest

from scripts import run_w3_r49_nuisance_refit_bootstrap_t as r49
from scripts import run_w3_r50_independent_bootstrap_calibration as r50
from scripts import run_w3_r51_bootstrap_narrowing_mechanism as r51


def test_independence_and_frozen_failure_denominators():
    assert r51.SOURCE_SEED not in (r49.SOURCE_SEED,r50.SOURCE_SEED)
    assert r51.DRAW_SEED!=r50.DRAW_SEED
    assert r51.BLOCKS==8 and r51.PARTICIPANTS==24
    assert r51.N_BOOT==63
    assert r51.N_SOURCE_CASES==16
    assert r51.N_INTERVALS==80
    assert r51.N_DRAW_RECORDS==2016
    assert r51.N_OPT_STARTS==4064
    assert r51.PARTITIONS==((0,4),(4,8))
    assert len(r51.METHODS)==5


def test_new_primitives_independent_and_leverage_paired():
    a=r51.source(0,r51.SUPPORT[0])
    paired=r51.source(0,r51.SUPPORT[1])
    separate=r51.source(1,r51.SUPPORT[0])
    previous=r50.original_source(0,r50.SUPPORT[0])
    np.testing.assert_array_equal(a[0]["participant_intercept"],
                                  paired[0]["participant_intercept"])
    assert not np.array_equal(a[0]["participant_intercept"],
                              separate[0]["participant_intercept"])
    assert not np.array_equal(a[0]["participant_intercept"],
                              previous[0]["participant_intercept"])
    assert paired[2][np.flatnonzero(paired[3]==0)[0]]==pytest.approx(3.)
    assert paired[2][np.flatnonzero(paired[3]==1)[0]]==pytest.approx(-2.5)
    with pytest.raises(ValueError,match="outside"):
        r51.source(8,r51.SUPPORT[0])


def test_common_gaussian_draws_and_oracle_never_enter_fitted_remL():
    data=r51.problem(0,r51.SUPPORT[0])
    fit=r51.observed_fit(data)
    assert fit["status"]=="accepted",fit.get("reason")
    stripped={k:v for k,v in data.items() if k!="oracle_covariance"}
    other=r51.observed_fit(stripped)
    assert other["status"]==fit["status"]
    assert other["selected_start"]==fit["selected_start"]
    x1,seed1=r51.paired_draw(stripped,fit["working_blocks"],0,
                             r51.SUPPORT[0],0)
    x2,seed2=r51.paired_draw(stripped,fit["working_blocks"],0,
                             r51.SUPPORT[0],0)
    np.testing.assert_array_equal(x1,x2)
    assert seed1==seed2 and np.isfinite(x1).all()
    # Identical standard-normal draws enter fitted and oracle matrices;
    # check reconstructed innovations participant by participant.
    y_oracle,seed3=r51.paired_draw(
        data,data["oracle_covariance"],0,r51.SUPPORT[0],0)
    assert seed1==seed3
    Z=data["X"]*np.sqrt(data["w"])[:,None]
    beta=np.linalg.lstsq(Z,data["y"]*np.sqrt(data["w"]),rcond=None)[0]
    original_mean=data["X"]@beta
    for i,who in enumerate(np.unique(data["group"])):
        indices=np.flatnonzero(data["group"]==who)
        a=np.linalg.solve(np.linalg.cholesky(fit["working_blocks"][i]),
                          (x1-original_mean)[indices]*np.sqrt(data["w"][indices]))
        b=np.linalg.solve(np.linalg.cholesky(data["oracle_covariance"][i]),
                          (y_oracle-original_mean)[indices]*np.sqrt(data["w"][indices]))
        np.testing.assert_allclose(a,b,rtol=1e-8,atol=1e-8)


def test_original_physical_remL_gate_retained():
    data=r51.problem(0,r51.SUPPORT[0])
    fit=r51.observed_fit(data)
    assert fit["status"]=="accepted"
    assert len(fit["numerical_starts"])==2
    assert fit["physical_projected_KKT"]<=r49.KKT_TOL
    assert fit["global_optimum_proven"] is False


def _refused(block,support):
    starts=[{"label":n,"status":"not_attempted"} for n,_ in r49.START_RATIOS]
    return {
        "block":block,"support":support,"source_status":"failed",
        "original_fitted_nuisance":{"status":"not_attempted",
                                    "numerical_starts":starts},
        "intervals":[r51.refused(name,"source refused")
                     for name in r51.METHODS],
        "draws":[{
            **r51.diagnostic_record(i,k),
        } for i in range(r51.N_BOOT) for k in r51.DRAW_TYPES],
    }


def test_independent_numerical_refusal_preserves_all_required_slots():
    bad=_refused(0,r51.SUPPORT[0])
    r=r51.summary([bad])
    assert r["planned_source_cases"]==16
    assert r["planned_interval_records"]==80
    assert r["planned_Gaussian_draw_and_refit_records"]==2016
    assert r["planned_nuisance_two_start_outcomes"]==4064
    assert r["recorded_nuisance_two_start_outcomes"]==254
    assert not r["full_original_failure_inclusive_ledger"]
    assert not r["release_authorized"]
    assert r["oracle_generated_pseudodata_only_diagnostic_NOT_feasible_estimator"]
    with pytest.raises(ValueError,match="duplicate"):
        r51.summary([bad,bad])


def test_shard_sha_and_identity_fail_closed(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","r51-contract-source")
    parts=tmp_path/"parts"
    for start,stop in r51.PARTITIONS:
        folder=parts/f"source-{start}"
        folder.mkdir(parents=True)
        fake=[_refused(i,s) for i in range(start,stop)
              for s in r51.SUPPORT]
        r51._write(folder/"cases.json",fake)
        r51._write(folder/"manifest.json",{
            "study":r51.STUDY,"start":start,"stop":stop,
            "cases":len(fake),"seed":r51.SOURCE_SEED,
            "source_checkout":"r51-contract-source",
            "sha256_cases":hashlib.sha256(
                (folder/"cases.json").read_bytes()).hexdigest(),
        })
    r51.aggregate(tmp_path/"out",parts)
    summary=json.loads((tmp_path/"out"/"summary.json").read_text())
    assert summary["full_original_failure_inclusive_ledger"]
    assert summary["recorded_Gaussian_draw_and_refit_records"]==2016
    (parts/"source-4"/"cases.json").write_text("damaged")
    with pytest.raises(ValueError,match="checksum"):
        r51.aggregate(tmp_path/"no",parts)
    with pytest.raises(ValueError,match="refused"):
        r51.shard(tmp_path/"invalid",1,5)
