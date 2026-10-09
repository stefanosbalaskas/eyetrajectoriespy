"""F1 independent null and moderate power calibration audit contracts."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pytest
from scripts.run_f1_larger_operating_characteristics import run
from scripts.run_f1_f5_scientific_stress import F1_DESIGNS


def test_full_native_F1_both_truth_states_with_distinct_attempt_seeds():
    records,evidence=run("balanced_equal_covariance",
                         null_replicates=2,alternative_replicates=2,
                         permutations=99,master_seed=20261125)
    assert len(records)==4 and evidence["total_attempts"]==4
    assert set(records.condition)=={"null","alternative"}
    assert records.groupby("condition").size().to_dict()=={
        "null":2,"alternative":2}
    assert records.seed.nunique()==4
    assert (records.loc[records.condition=="null","effect_amplitude"]==0).all()
    assert (records.loc[records.condition=="alternative","effect_amplitude"]==.04).all()
    assert len(evidence["summary"])==2
    assert not evidence["statistical_null_size_qualified"]
    assert not evidence["statistical_power_qualified"]
    assert not evidence["release_authorized"]
    assert not evidence["group_label_permutation_may_violate_exchangeability"]


def test_null_conditions_distinct_from_heteroscedastic_violation():
    assert set(F1_DESIGNS)=={
        "balanced_equal_covariance","clustered_two_trials",
        "unequal_heteroscedastic_null","very_sparse"}
    assert F1_DESIGNS["unequal_heteroscedastic_null"]["group_noise_multiplier"]>1
    with pytest.raises(ValueError,match="unknown"):
        run("unlisted_design",null_replicates=2,alternative_replicates=2)
    with pytest.raises(ValueError,match="adequate"):
        run("balanced_equal_covariance",null_replicates=1,
            alternative_replicates=2)


def test_exact_attempt_and_failure_accounting():
    records,evidence=run("very_sparse",null_replicates=2,
                         alternative_replicates=2,permutations=99,
                         master_seed=117)
    assert evidence["fit_failures"]==records.status.eq("failed").sum()
    for case in evidence["summary"]:
        assert case["attempted"]==2
        assert case["completed"]+case["failed"]==case["attempted"]
        for alpha in ("0.01","0.05","0.1"):
            result=case[f"alpha_{alpha}"]
            assert result["attempts_including_failures"]==2
            assert 0<=result["rejections"]<=result["conditional_n"]<=2
