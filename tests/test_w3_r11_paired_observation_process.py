"""W3 R11 paired generating support versus observed-data selection contracts."""
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pytest

from scripts.run_w3_r11_paired_observation_process import (
    BLOCKS,N_PARTICIPANTS,TRUTHS,OBSERVATION,MODELS,TIME,
    original_full_source,recorded_case,enforce_observed_source,
    block_evidence,audit,wilson,interval_of_mean_paired
)


def test_original_complete_source_is_identical_across_truths_except_known_mean_shift():
    a=original_full_source(0,"baseline")
    b=original_full_source(0,"localized_bump")
    for name in ("x","n_trials","time","dropout_uniforms"):
        np.testing.assert_array_equal(a[name],b[name])
    np.testing.assert_allclose(
        a["values"]-a["conditional_mean"],
        b["values"]-b["conditional_mean"],atol=1e-14
    )
    assert not np.array_equal(a["values"],b["values"])
    assert len(a["x"])==N_PARTICIPANTS


def test_complete_and_all_missingness_regimes_are_exact_same_native_source_subsets():
    src=original_full_source(1,"baseline")
    all_cases={m:recorded_case(src,m) for m in OBSERVATION}
    for rec in all_cases.values():
        enforce_observed_source(src,rec)
        assert len(np.unique(rec["units"]))==N_PARTICIPANTS
        assert len(rec["gaze"].time)==int(src["n_trials"].sum())
        assert all(np.all(np.diff(t)>0) for t in rec["gaze"].time)
    full=all_cases["complete"]
    assert full["n_gapped_trials"]==0
    for mechanism in OBSERVATION[1:]:
        missing=all_cases[mechanism]
        assert missing["n_observed_samples"]<full["n_observed_samples"]
        for (original_t,original_y),(native_t,native_y) in zip(
            zip(full["gaze"].time,full["gaze"].values),
            zip(missing["gaze"].time,missing["gaze"].values)
        ):
            _,full_idx,observed_idx=np.intersect1d(
                original_t,native_t,return_indices=True
            )
            assert len(full_idx)==len(native_t)
            np.testing.assert_array_equal(original_y[full_idx],
                                          native_y[observed_idx])


@pytest.mark.parametrize("truth_mode",TRUTHS)
def test_full_block_models_preserve_original_regression_and_reference_contracts(truth_mode):
    cases=block_evidence(0,truth_mode)
    assert len(cases)==len(OBSERVATION)
    assert set(x["observation"] for x in cases)==set(OBSERVATION)
    full=next(x for x in cases if x["observation"]=="complete")
    assert full["status"]=="ok",full["exception"]
    assert full["n_gapped_trials"]==0
    for row in cases:
        assert row["status"]=="ok",row["exception"]
        assert row["source_unchanged"]
        assert row["supported_dense_w3_rejected"]
        assert row["n_independent_participants"]==N_PARTICIPANTS
        assert len(row["models"])==len(MODELS)
        for model in MODELS:
            m=row["models"][model]
            assert m["qr_oracle"]<=4e-7
            assert m["score_oracle"]<=4e-7
            assert m["width"]>0
            assert isinstance(m["pointwise_90pct_true_included"],bool)
            if row["observation"]=="complete":
                assert abs(m["paired_loss_point_shift_vs_complete"])<4e-7
                assert abs(m["paired_loss_projection_shift_vs_complete"])<4e-7
    assert not any(x["uncertainty_qualified"] for x in cases)


def test_source_ledger_failure_is_retained_as_failure_not_silently_excluded():
    full=block_evidence(0,"baseline")[0]
    bad=dict(full,observation="mcar",status="failed",
             exception={"type":"ControlledSourceFailure"})
    summary=audit([full,bad])
    assert summary["planned_cases"]==BLOCKS*len(TRUTHS)*len(OBSERVATION)
    assert summary["recorded_cases"]==2
    assert summary["completed_cases"]==1
    assert summary["failed_cases"]==1
    assert len(summary["missing_cases"])==summary["planned_cases"]-2
    assert not summary["simultaneous_band_qualified"]
    with pytest.raises(ValueError,match="duplicate"):
        audit([full,full])


def test_independent_generating_block_mc_unit_and_guardrails():
    a=original_full_source(0,"baseline")
    b=original_full_source(1,"baseline")
    assert not np.array_equal(a["values"],b["values"])
    with pytest.raises(ValueError,match="outside"):
        original_full_source(BLOCKS,"baseline")
    with pytest.raises(ValueError,match="unplanned"):
        original_full_source(0,"unapproved_truth")
    with pytest.raises(ValueError,match="unplanned"):
        recorded_case(a,"secret_analysis")
    assert interval_of_mean_paired([],seed=3) is None
    sample=[-1.,.1,.5,.2]
    assert interval_of_mean_paired(sample,seed=2)==interval_of_mean_paired(sample,seed=2)
    assert wilson(0,0) is None
    assert abs(wilson(0,96)[0])<1e-12
    assert wilson(96,96)[1]==1
