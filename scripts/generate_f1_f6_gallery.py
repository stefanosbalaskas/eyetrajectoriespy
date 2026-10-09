"""Create six deterministic F1-F6 synthetic *illustrative* research SVGs.

These plots are visual method aids, not estimated population-level evidence.
No measured human/animal gaze is represented and no p-value calibration
is implied. Every image uses a fixed seed and deterministic SVG settings.
"""
from __future__ import annotations
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from eyetrajectoriespy.research import project_simplex

ROOT = Path("docs/assets/research")
FILES = (
    "f1-sparse-group-contrast.svg",
    "f2-target-validation-errors.svg",
    "f3-bids-time-provenance.svg",
    "f4-aoi-simplex-reconstruction.svg",
    "f5-ordered-functional-changepoint.svg",
    "f6-weighted-functional-geometry.svg",
)


def _save(fig, filename: str) -> None:
    fig.suptitle("Synthetic illustration — no calibrated inference",
                 fontsize=9, y=1.02, color="#505766")
    fig.savefig(
        ROOT / filename, format="svg",
        bbox_inches="tight",
        metadata={"Date": None, "Creator": "eyetrajectoriespy D5 synthetic"},
    )
    plt.close(fig)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    matplotlib.rcParams["svg.hashsalt"] = "eyetrajectoriespy-f1-f6-v1"
    matplotlib.rcParams["font.family"] = "DejaVu Sans"
    rng = np.random.default_rng(916)
    t = np.linspace(0.0, 1.0, 81)

    # F1: group effect shape is KNOWN synthetic truth, not fitted/PACE CI.
    fig, axes = plt.subplots(1, 2, figsize=(8, 2.8))
    for channel, ax in enumerate(axes):
        baseline = .45 + (.06*np.sin(np.pi*t) if channel == 0
                          else .06*np.cos(np.pi*t))
        effect = .09*np.sin(np.pi*t) if channel == 0 else -.06*np.cos(np.pi*t)
        ax.plot(t, baseline, label="Group A: truth", lw=2)
        ax.plot(t, baseline+effect, label="Group B: truth", lw=2)
        ax.set(xlabel="Trial phase", ylabel=("x" if channel==0 else "y"),
               title=f"Known group effect — {'x' if channel==0 else 'y'}")
    axes[0].legend(fontsize=7)
    _save(fig, FILES[0])

    # F2: observed calibration points around known target locations.
    fig, ax = plt.subplots(figsize=(5.5, 3.5))
    targets = np.array([[0., 0.], [3., 1.8], [6., .5], [7., 3.]])
    for i, target in enumerate(targets):
        points = target + rng.normal(scale=.24, size=(8, 2))
        ax.plot(target[0], target[1], marker="x", markersize=8,
                color="#ae353b", markeredgewidth=2)
        ax.scatter(points[:,0], points[:,1], s=13, alpha=.6, color="#1f668e")
        ax.annotate("", xy=points[0], xytext=target,
                    arrowprops={"arrowstyle":"->", "color":"0.45", "lw":.8})
    ax.set(xlabel="Horizontal position (degrees)",
           ylabel="Vertical position (degrees)",
           title="Targets (crosses) and validation samples (dots)")
    _save(fig, FILES[1])

    # F3: raw ms timestamps, seconds conversion, no offset alignment.
    fig, ax = plt.subplots(figsize=(6.4, 2.8))
    millis = np.arange(7186799, 7186824, dtype=float)
    seconds = millis / 1000.0
    ax.plot(seconds, .45+np.sin(np.linspace(0,2*np.pi,len(seconds)))*.04,
            marker=".", label="x gaze — native device sample")
    ax.set(xlabel="Device timestamp (seconds; raw milliseconds / 1000)",
           ylabel="Normalized gaze x",
           title="BIDS unit conversion — clock NOT synchronized")
    ax.legend(fontsize=8)
    _save(fig, FILES[2])

    # F4: softmax truth and projection feasibility, not a constrained FPCA fit.
    fig, axes = plt.subplots(1, 2, figsize=(8, 2.8))
    logits = np.column_stack((.4+np.sin(np.pi*t),
                              .2+np.cos(np.pi*t),
                              .6+np.sin(2*np.pi*t)))
    prob = np.exp(logits-logits.max(axis=1,keepdims=True))
    prob /= prob.sum(axis=1, keepdims=True)
    proposed = project_simplex(prob + rng.normal(scale=.05, size=prob.shape))
    for idx, ax in enumerate(axes):
        curves = prob if idx==0 else proposed
        for j,label in enumerate(("AOI 1", "AOI 2", "AOI 3")):
            ax.plot(t, curves[:,j], label=label)
        ax.set(xlabel="Trial phase", ylabel="AOI share",
               title=("Known simplex truth" if idx==0
                      else "Post-hoc Euclidean projection"))
        ax.set_ylim(0, 1)
    axes[0].legend(fontsize=7)
    _save(fig, FILES[3])

    # F5: intentionally schematic split scan with *known* location, no p-values.
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    splits = np.arange(5, 36)
    scan = .3+1.6*np.exp(-.5*((splits-20)/4)**2)
    scan += .04*np.sin(splits)
    ax.plot(splits, scan, marker="o", markersize=3, label="Illustrative CUSUM norm")
    ax.axvline(20, ls="--", color="#ae353b", label="Known injected split")
    ax.set(xlabel="Candidate split between ordered whole trials",
           ylabel="Synthetic scan norm", title="Single functional change illustration")
    ax.legend(fontsize=7)
    _save(fig, FILES[4])

    # F6: declared geometry changes axes, not an automatically learned optimum.
    fig, axes = plt.subplots(1, 2, figsize=(8, 2.8))
    raw = np.vstack((.1*np.sin(2*np.pi*t), .18*np.cos(2*np.pi*t)))
    weights = np.array([4., .25])
    for i, ax in enumerate(axes):
        values = raw if i == 0 else np.sqrt(weights)[:,None]*raw
        for j, label in enumerate(("x", "y")):
            ax.plot(t, values[j], label=label)
        ax.set(xlabel="Trial phase",
               ylabel=("Original coordinate" if i==0 else "Weighted coordinate"),
               title=("Raw functional axes" if i==0 else "Declared sqrt(weights) map"))
    axes[0].legend(fontsize=7)
    _save(fig, FILES[5])
    for file in FILES:
        target = ROOT / file
        assert target.is_file() and target.stat().st_size > 1000, target
    print(f"Generated {len(FILES)} synthetic F1-F6 SVGs; no inference claimed")


if __name__ == "__main__":
    main()
