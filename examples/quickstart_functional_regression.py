"""Short 1.2 candidate route: function-on-scalar regression on independent curves."""
from pathlib import Path
import numpy as np
import pandas as pd
from eyetrajectoriespy import TrajectorySet
from eyetrajectoriespy.workflows import (
    FunctionOnScalarWorkflowConfig, run_function_on_scalar_workflow,
    save_workflow_figure, workflow_summary_frame, workflow_reporting_text,
)

def main():
    rng=np.random.default_rng(1203)
    t=np.linspace(0,1,31)
    condition=np.tile([0.,1.],15)
    ids=tuple(f"independent-{i:02d}" for i in range(len(condition)))
    values=np.stack([np.column_stack((
        .43+.06*np.sin(np.pi*t)+.035*c*np.sin(2*np.pi*t)+rng.normal(0,.012,len(t)),
        .49+.05*np.cos(np.pi*t)+rng.normal(0,.012,len(t)))) for c in condition])
    gaze=TrajectorySet(time=t,values=values,curve_ids=ids,dimension_names=("x","y"),
        metadata=pd.DataFrame({"participant_id":ids}),coordinate_system="normalized",
        time_unit="s",provenance={"synthetic":True,"independent_curves":True})
    design=pd.DataFrame({"curve_id":ids,"condition":condition})
    fit=run_function_on_scalar_workflow(gaze,design,
        config=FunctionOnScalarWorkflowConfig(predictors=("condition",),dimensions=("x",)))
    root=Path("build/quickstarts/functional-regression");root.mkdir(parents=True,exist_ok=True)
    workflow_summary_frame(fit).to_csv(root/"summary.csv",index=False)
    (root/"interpretation.txt").write_text(workflow_reporting_text(fit)+"\nObserved-grid coefficients describe a seeded design; no significance inference is claimed.\n",encoding="utf-8")
    save_workflow_figure(fit,root/"condition-x.svg",plot="function_on_scalar_coefficient",
        coefficient="condition",dimension="x")
    print("PASS functional regression tutorial")
if __name__=="__main__": main()
