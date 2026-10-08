"""Short 1.2 candidate route: paired native sparse planar MFPCA."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from eyetrajectoriespy import IrregularTrajectorySet
from eyetrajectoriespy.workflows import (
    SparseMFPCAWorkflowConfig, run_sparse_mfpca_workflow,
    workflow_summary_frame, workflow_reporting_text,
)

def main():
    rng=np.random.default_rng(1202)
    times=[];values=[];ids=[]
    for i in range(20):
        t=np.r_[0.,np.sort(rng.uniform(.06,.94,12)),1.]
        a,b=rng.normal(size=2)
        v=np.column_stack((.46+.10*a*np.sin(np.pi*t),.52+.10*b*np.cos(np.pi*t)))
        v+=rng.normal(0,.015,v.shape)
        times.append(t);values.append(v);ids.append(f"P{i:02d}")
    sparse=IrregularTrajectorySet(time=tuple(times),values=tuple(values),curve_ids=tuple(ids),
        dimension_names=("x","y"),metadata=pd.DataFrame({"participant_id":ids}),
        coordinate_system="normalized",time_unit="s",provenance={"synthetic":True,"paired_native_samples":True})
    fit=run_sparse_mfpca_workflow(sparse,config=SparseMFPCAWorkflowConfig(
        n_components=2,evaluation_grid=tuple(np.linspace(0,1,21)),
        mean_bandwidth=.28,covariance_bandwidth=.40,measurement_error="diagonal",
        measurement_error_variance=(.0004,.0004),psd_action="project",score_failure_action="retain_nan"))
    root=Path("build/quickstarts/sparse-planar");root.mkdir(parents=True,exist_ok=True)
    workflow_summary_frame(fit).to_csv(root/"summary.csv",index=False)
    (root/"interpretation.txt").write_text(workflow_reporting_text(fit)+"\nThe raw samples were not interpolated onto a manufactured gaze grid.\n",encoding="utf-8")
    fig,ax=plt.subplots(figsize=(7,3.5))
    for t,v in zip(sparse.time[:5],sparse.values[:5]): ax.plot(t,v[:,0],"o-",alpha=.65,markersize=3)
    ax.set(xlabel="Observed time (s)",ylabel="Horizontal gaze (normalized)",title="Native sparse observation support")
    fig.savefig(root/"observed-support.svg",format="svg",bbox_inches="tight");plt.close(fig)
    print("PASS paired sparse planar tutorial")
if __name__=="__main__": main()
