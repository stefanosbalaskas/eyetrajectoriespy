"""New F5 oracle/external-dependence comparator: scientific experiments only."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pytest
from scripts.run_f1_f5_scientific_stress import _ordered_fixture
from eyetrajectoriespy.research.functional_changepoints_ar1_reference import (
    estimate_scalar_functional_ar1,
    infer_ordered_functional_changepoint_ar1_reference as ar1_ref,
)


def test_AR1_reference_deterministic_and_does_not_claim_calibration():
    x=_ordered_fixture(1801,"strong_AR1","null")
    a=ar1_ref(x,ar1_coefficient_from_independent_baseline=.8,
              n_bootstrap=99,random_state=17)
    b=ar1_ref(x,ar1_coefficient_from_independent_baseline=.8,
              n_bootstrap=99,random_state=17)
    assert 0<a.p_value_experimental<=1
    assert 6<=a.split_index<=30
    assert len(a.null_statistics)==99
    np.testing.assert_allclose(a.null_statistics,b.null_statistics,rtol=0,atol=0)
    assert not a.evidence["scientific_inference_qualified"]
    assert not a.evidence["release_authorized"]
    assert a.evidence["coefficient_estimated_on_test_series"] is False
    assert a.evidence["ar1_coefficient_from_independent_baseline"]==.8
    assert a.evidence["bootstrap_type"].startswith("whole_curve")


def test_AR1_reference_preserves_common_functional_translation():
    src=_ordered_fixture(1802,"weak_AR1","null")
    from eyetrajectoriespy.types import TrajectorySet
    base=src.values.copy()
    trend=np.sin(np.pi*src.time)[:,None]
    changed=TrajectorySet(
        time=src.time,values=base+trend[None,:,:],
        curve_ids=src.curve_ids,dimension_names=src.dimension_names,
        coordinate_system=src.coordinate_system,time_unit=src.time_unit,
    )
    a=ar1_ref(src,ar1_coefficient_from_independent_baseline=.35,
              n_bootstrap=99,random_state=41)
    b=ar1_ref(changed,ar1_coefficient_from_independent_baseline=.35,
              n_bootstrap=99,random_state=41)
    np.testing.assert_allclose(a.null_statistics,b.null_statistics,rtol=0,atol=1e-12)
    assert abs(a.statistic-b.statistic)<1e-12
    assert a.p_value_experimental==b.p_value_experimental


def test_refuses_invalid_dependence_estimates_and_pseudoreplication():
    src=_ordered_fixture(2201,"strong_AR1","null")
    for phi in [float("nan"),float("inf"),-.99,1.,True]:
        with pytest.raises(ValueError,match="independent baseline"):
            ar1_ref(src,ar1_coefficient_from_independent_baseline=phi,
                    n_bootstrap=99)
    with pytest.raises(ValueError,match="99"):
        ar1_ref(src,ar1_coefficient_from_independent_baseline=.8,
                n_bootstrap=20)
    with pytest.raises(ValueError,match="segment"):
        ar1_ref(src,ar1_coefficient_from_independent_baseline=.8,
                n_bootstrap=99,min_segment=100)
    from eyetrajectoriespy.types import TrajectorySet
    data=TrajectorySet(
        time=src.time,values=src.values,curve_ids=src.curve_ids,
        dimension_names=src.dimension_names,
        coordinate_system=src.coordinate_system,time_unit=src.time_unit,
        metadata=pd.DataFrame({"participant_id":["duplicate"]*len(src.values)}))
    with pytest.raises(ValueError,match="repeated"):
        ar1_ref(data,ar1_coefficient_from_independent_baseline=.8,n_bootstrap=99)


def test_naive_phi_estimation_is_explicitly_not_an_inferential_input():
    x=_ordered_fixture(112233,"strong_AR1","null")
    estimate=estimate_scalar_functional_ar1(x)
    assert -1<estimate["ar1_coefficient_pooled_descriptive"]<1
    assert estimate["independent_baseline_or_oracle_coefficient_required_for_inference"]
    assert estimate["finite_sample_bias_not_qualified"]
    assert not estimate["science_inference_qualified"]
