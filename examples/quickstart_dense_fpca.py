"""Short 1.2 candidate route: common-grid FPCA; synthetic learning data."""
from pathlib import Path
from eyetrajectoriespy import simulate_planar_trajectories
from eyetrajectoriespy.workflows import (
    FPCAWorkflowConfig, run_fpca_workflow, save_workflow_figure,
    workflow_summary_frame, workflow_reporting_text,
)

def main():
    root=Path("build/quickstarts/dense");root.mkdir(parents=True,exist_ok=True)
    gaze=simulate_planar_trajectories(n_participants=16,trials_per_participant=2,n_time=41,random_state=1201)
    result=run_fpca_workflow(gaze,config=FPCAWorkflowConfig(n_components=2,scaling="dimension_sd"))
    workflow_summary_frame(result).to_csv(root/"summary.csv",index=False)
    (root/"interpretation.txt").write_text(workflow_reporting_text(result)+"\nFPCs are modes of variability, not inferred psychological states.\n",encoding="utf-8")
    save_workflow_figure(result,root/"component-x.svg",plot="fpca_component",component=0,dimension="x")
    print("PASS dense FPCA tutorial")
if __name__=="__main__": main()
