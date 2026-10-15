"""R31 native data retention, explicit MAR/MCAR and paired covariance contracts."""
import numpy as np
import pytest
from scripts import run_w3_r17_fresh_feasibility as fresh
from scripts import run_w3_r31_observation_process_recovery as study


def original(n=24,support="ordinary_dependent"):
    return fresh.fresh_source(
        0,support,n=n,master_seed=study.MASTER_SEED,
        n_blocks=study.BLOCKS,max_n=max(study.SIZES))


@pytest.mark.parametrize("mode",study.OBSERVATION)
def test_native_time_and_values_always_subset_without_imputation(mode):
    raw=original()
    before=[(t.copy(),v.copy()) for t,v in zip(raw[1].time,raw[1].values)]
    transformed,meta=study._native_observation_transform(
        raw,mode,block=0,support="ordinary_dependent")
    assert transformed[1].provenance["interpolation_performed"] is False
    assert meta["missing_observed_outcomes_used_to_select_samples"] is False
    assert len(set(transformed[3]))==24
    assert len(transformed[1].values)==meta["retained_native_trials"]
    assert len(meta["retained_curve_indices"])==len(transformed[1].time)
    for kept_curve,kept_ix,times,values in zip(
        meta["retained_curve_indices"],meta["retained_native_index_maps"],
        transformed[1].time,transformed[1].values):
        np.testing.assert_array_equal(times,raw[1].time[kept_curve][kept_ix])
        np.testing.assert_array_equal(values,raw[1].values[kept_curve][kept_ix])
        assert np.all(np.diff(times)>0)
    for (time,value),ref_t,ref_v in zip(before,raw[1].time,raw[1].values):
        np.testing.assert_array_equal(time,ref_t)
        np.testing.assert_array_equal(value,ref_v)
    if mode=="complete":
        assert meta["retained_native_points"]==meta["original_native_points"]
        assert meta["retained_native_trials"]==meta["original_native_trials"]
    else:
        assert meta["retained_native_points"]<meta["original_native_points"]
    if mode=="predictor_mar_trial_dropout":
        assert meta["retained_native_trials"]<meta["original_native_trials"]
    else:
        assert meta["retained_native_trials"]==meta["original_native_trials"]


@pytest.mark.parametrize("mode",study.OBSERVATION)
def test_mask_of_first_24_is_stable_in_nested_96_person_source(mode):
    a=original(24)
    b=original(96)
    first,ma=study._native_observation_transform(
        a,mode,block=0,support="ordinary_dependent")
    all_obs,mb=study._native_observation_transform(
        b,mode,block=0,support="ordinary_dependent")
    nb=len(first[1].values)
    assert len(all_obs[1].values)>=nb
    assert ma["retained_curve_indices"]==[
        j for j in mb["retained_curve_indices"] if j<len(a[1].time)]
    for ta,tb,ya,yb in zip(
        first[1].time,all_obs[1].time[:nb],
        first[1].values,all_obs[1].values[:nb]):
        np.testing.assert_array_equal(ta,tb)
        np.testing.assert_array_equal(ya,yb)


def test_prespecified_nonresponse_mechanisms_are_not_outcome_selected():
    assert study.OBSERVATION==(
        "complete","mcar_20","time_mar_20","predictor_mar_trial_dropout")
    assert study.PLANNED==192
    assert study.BLOCKS==12
    assert study.MASTER_SEED not in (202610153030,202610152929)
    with pytest.raises(ValueError,match="unregistered"):
        study._native_observation_transform(
            original(),"outcome_mnar",block=0,support="ordinary_dependent")


@pytest.mark.parametrize("mode",study.OBSERVATION)
def test_observed_only_fits_and_failure_inclusive_ledger(mode):
    x=study.evaluate(0,24,"ordinary_independent",mode)
    assert x["source_generated"],x["source_failure"]
    assert x["postfit_generator_oracle_only"]
    assert x["native_source_unmodified"]
    assert not x["no_pointwise_coverage_calculated"] is False
    assert not x["release_authorized"]
    for method in study.METHODS:
        f=x["methods"][method]
        assert f["status"] in ("ok","failed","nonconverged")
        if f["status"]=="ok":
            assert len(f["postfit_component_absolute_relative_errors"])==4
            assert len(f["postfit_below_5pct_positive_truth"])==4
    result=study.summarize([x])
    assert result["recorded_evaluations"]==1
    assert result["missing_evaluations"]==191
    assert result["no_nominal_pointwise_coverage"]
    assert result["within_block_masks_not_independent_sources"]
    assert not result["release_authorized"]


def test_paired_block_bootstrap_never_uses_unpaired_missing_sources():
    row=study.evaluate(0,24,"ordinary_independent","complete")
    compare=study.block_paired_change(
        [row],24,"ordinary_independent","mcar_20",
        "gaussian_reml","participant_slope")
    assert compare["paired_independent_blocks"]==0
    assert compare["whole_block_bootstrap_95pct"] is None
