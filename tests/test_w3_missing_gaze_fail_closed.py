"""W3 fail-closed missing and irregular gaze without modifying source data."""
import numpy as np
import pandas as pd
import pytest

from eyetrajectoriespy import IrregularTrajectorySet, TrajectorySet
from eyetrajectoriespy.workflows import (
    FunctionOnScalarWorkflowConfig,
    run_function_on_scalar_workflow,
    workflow_preflight,
)


def _complete():
    n = 12
    time = np.linspace(0, 1, 9)
    x = np.linspace(-1, 1, n)
    mean = (.2 + .04 * time)[None, :] + x[:, None] * (.3 + .08 * time)[None, :]
    values = mean[:, :, None].copy()
    tr = TrajectorySet(
        time=time, values=values,
        curve_ids=tuple(f"C{i:03d}" for i in range(n)),
        dimension_names=("x",), time_unit="s",
        coordinate_system="normalized"
    )
    design = pd.DataFrame({"curve_id": tr.curve_ids, "condition": x})
    return tr, design


def _fit(tr, design):
    return run_function_on_scalar_workflow(
        tr, design,
        config=FunctionOnScalarWorkflowConfig(
            predictors=("condition",), dimensions=("x",),
            unit="curve"
        )
    )


@pytest.mark.parametrize("invalid", [np.nan, np.inf, -np.inf])
def test_incomplete_common_grid_is_rejected_without_silent_imputation(invalid):
    tr, design = _complete()
    values = tr.values.copy()
    values[2, 4, 0] = invalid
    dirty = TrajectorySet(
        time=tr.time, values=values,
        curve_ids=tr.curve_ids, dimension_names=tr.dimension_names,
        time_unit="s", coordinate_system="normalized",
    )
    before = dirty.values.copy()
    with pytest.raises(ValueError, match=r"found 1 non-finite gaze value\(s\).*No automatic imputation"):
        _fit(dirty, design)
    np.testing.assert_array_equal(
        np.isnan(dirty.values),np.isnan(before)
    )
    # No participant or curve was silently removed or replaced.
    assert dirty.n_curves == tr.n_curves
    np.testing.assert_array_equal(dirty.values, before)


def test_irregular_input_routes_explicitly_without_interpolation():
    tr, design = _complete()
    irregular = IrregularTrajectorySet(
        time=(np.array([0.,.4,1.]), np.array([0.,.3,.8,1.])),
        values=(np.array([[.1],[.3],[.4]]),
                np.array([[.2],[.25],[.4],[.6]])),
        curve_ids=("R0","R1"), dimension_names=("x",),
        time_unit="s", coordinate_system="normalized",
    )
    df = pd.DataFrame({"curve_id":("R0","R1"),"condition":(0.,1.)})
    with pytest.raises(TypeError, match="IrregularTrajectorySet must use.*sparse/irregular workflow"):
        _fit(irregular, df)
    assert len(irregular.time[0])==3 and len(irregular.time[1])==4
    np.testing.assert_array_equal(irregular.time[0],[0.,.4,1.])


def test_preflight_retains_missingness_instead_of_certifying_fos_validity():
    tr, design = _complete()
    values=tr.values.copy()
    values[0,0,0]=np.nan
    dirty=TrajectorySet(
        time=tr.time, values=values, curve_ids=tr.curve_ids,
        dimension_names=tr.dimension_names,
        time_unit="s", coordinate_system="normalized",
    )
    report=workflow_preflight(
        dirty, participant_column=None, trial_column=None,
        require_common_grid=True, required_dimensions=("x",)
    )
    assert report.summary.iloc[0]["missing_values"]==1
    assert report.provenance["input_modified"] is False
    assert report.provenance["automatic_exclusions"] is False
    # Preflight layout compatibility must not be interpreted as statistical
    # support for W3 complete-grid function-on-scalar regression.
    with pytest.raises(ValueError, match="complete finite common-grid"):
        _fit(dirty, design)


def test_valid_complete_grid_workflow_output_remains_unchanged():
    tr, design = _complete()
    fit = _fit(tr, design)
    assert fit.workflow_contract=="function_on_scalar:v1"
    assert fit.fit.design_rank==2
    assert fit.fit.coefficients.shape==(2,9,1)
    assert fit.fit.unit=="curve"
    assert fit.provenance["preprocessing_executed"] is False
    assert fit.provenance["automatic_model_selection_performed"] is False
