"""Private experimental 3D gaze/hand proximity trajectories.

This is a descriptive geometric transformation, not a validated model of
attentional capture, motor intention, or synchronized multisensor acquisition.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def describe_gaze_hand_attraction(
    aligned: pd.DataFrame,
    *,
    participant_col: str = "participant_id",
    trial_col: str = "trial_id",
    time_col: str = "time_s",
    shared_clock_certified: bool = False,
) -> pd.DataFrame:
    """Compute target-versus-distractor proximity from synchronized 3D coordinates.

    A positive score indicates closer proximity to the declared target than to
    the distractor; negative indicates the reverse. Gaze and hand are separate
    outputs. No interpolation, coordinate transformation, or time alignment.
    """
    if not shared_clock_certified:
        raise ValueError("require independently checked shared clock and coordinate frame")
    if not isinstance(aligned, pd.DataFrame) or aligned.empty:
        raise ValueError("aligned must be a nonempty DataFrame")
    identities = [participant_col, trial_col, time_col]
    prefixes = ("gaze", "hand", "target", "distractor")
    coordinates = [f"{p}_{axis}" for p in prefixes for axis in ("x", "y", "z")]
    if len(set([*identities, *coordinates])) != len([*identities, *coordinates]):
        raise ValueError("column mapping must be unique")
    absent = sorted(set([*identities, *coordinates]) - set(aligned.columns))
    if absent:
        raise ValueError(f"missing required columns: {absent}")
    if aligned[[participant_col, trial_col]].isna().any().any():
        raise ValueError("participant and trial identifiers cannot be missing")
    d = aligned.copy(deep=True)
    t = pd.to_numeric(d[time_col], errors="coerce").to_numpy(dtype=float)
    xyz = d[coordinates].apply(pd.to_numeric, errors="coerce").to_numpy(dtype=float)
    if not np.isfinite(t).all() or not np.isfinite(xyz).all():
        raise ValueError("timestamps and all 3D coordinates must be finite")
    for _, ix in d.groupby([participant_col, trial_col], sort=False).indices.items():
        if np.any(np.diff(t[ix]) <= 0):
            raise ValueError("time must strictly increase in supplied trial order")
    matrices = {
        p: xyz[:, i * 3:(i + 1) * 3] for i, p in enumerate(prefixes)
    }
    if np.any(np.linalg.norm(matrices["target"] - matrices["distractor"], axis=1) == 0):
        raise ValueError("target and distractor centers must differ")
    result = d[identities].copy(deep=True)
    result["target_distractor_distance"] = np.linalg.norm(
        matrices["target"] - matrices["distractor"], axis=1
    )
    for modality in ("gaze", "hand"):
        to_target = np.linalg.norm(matrices[modality] - matrices["target"], axis=1)
        to_distractor = np.linalg.norm(matrices[modality] - matrices["distractor"], axis=1)
        denom = to_target + to_distractor
        # Distinct target and distractor imply strictly positive denominator.
        result[f"{modality}_target_distance"] = to_target
        result[f"{modality}_distractor_distance"] = to_distractor
        result[f"{modality}_relative_target_proximity"] = (to_distractor - to_target) / denom
    result.attrs["status"] = "experimental_descriptive_geometry"
    result.attrs["claim_boundary"] = (
        "Requires aligned clocks and common metric coordinate frame; "
        "proximity is not validated attention or causal attraction."
    )
    return result
