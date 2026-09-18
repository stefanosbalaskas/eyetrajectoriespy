---
title: Functional gaze trajectories, without hidden analytical decisions
---

<div class="et-hero" markdown>
<div class="et-kicker">eyetrajectoriespy · continuous eye-tracking FDA</div>

# Model gaze as a function, not only a summary

`eyetrajectoriespy` provides a vendor-neutral scientific layer for continuous gaze paths, multivariate FPCA, repeated-trial functional decomposition, compositional AOI trajectories, and explicit phase–amplitude analysis.

<span class="et-pill">2-D x(t), y(t)</span><span class="et-pill">FPCA / MFPCA</span><span class="et-pill">multilevel</span><span class="et-pill">registration</span><span class="et-pill">compositional</span><span class="et-pill">elastic SRVF</span>
</div>

<div class="grid cards" markdown>

-   **Start with the scientific object**

    Decide whether the object is a planar path, a derived function, repeated-trial process, AOI composition, or phase/amplitude problem before choosing an estimator.

    [:octicons-arrow-right-24: Choose a representation](concepts/representations.md)

-   **Keep timing decisions visible**

    Time normalization and registration can remove scientifically meaningful latency. They are explicit operations and their provenance is retained.

    [:octicons-arrow-right-24: Registration guide](guides/registration.md)

-   **Separate stable people from variable trials**

    Repeated trials are not independent replicas. The multilevel workflow separates participant-level and within-participant functional variation.

    [:octicons-arrow-right-24: Multilevel FPCA](guides/multilevel.md)

-   **Respect constrained outcomes**

    AOI probability functions live on a simplex. Compositional FPCA works in log-ratio coordinates and reconstructs valid probabilities.

    [:octicons-arrow-right-24: AOI probability functions](guides/compositional.md)

</div>

## The core pipeline

[
	ext{raw/clean gaze} ightarrow 	ext{functional representation} ightarrow
	ext{explicit preprocessing} ightarrow 	ext{FPCA / registration} ightarrow
	ext{scores, functions, or phase} ightarrow 	ext{scientific interpretation}
]

!!! important "This is not a fixation detector"
    `eyetrajectoriespy` starts once gaze has a scientifically interpretable time and coordinate system. Event detection, general gaze QC, and AOI robustness belong upstream rather than being duplicated here.

## What problem does it solve?

Conventional summaries such as fixation count or total dwell deliberately discard temporal structure. Functional analysis asks a complementary question: **how does the entire viewing trajectory vary over time?** A retained functional component can encode an early evidence excursion, a left–right spatial bias, a direct versus exploratory path, or another whole-trajectory pattern.

## A minimal analysis

```python
from eyetrajectoriespy import fit_mfpca, simulate_planar_trajectories

gaze = simulate_planar_trajectories(
    n_participants=20,
    trials_per_participant=6,
    random_state=7,
)

fit = fit_mfpca(
    gaze,
    n_components=0.95,
    scaling="dimension_sd",
)

print(fit.explained_variance_ratio)
print(fit.scores.shape)
```

## The package is deliberately conservative

<div class="grid cards" markdown>

- **Missingness stays missing** until an explicit interpolation or exclusion decision is made.
- **Smoothing is opt-in** because abrupt gaze transitions can be real.
- **Registration is opt-in** because latency can be theoretically meaningful.
- **Coordinate conversion is explicit** because screen position and stimulus geometry matter.
- **Channel scaling is explicit** because equalizing x/y or heterogeneous channels changes the estimand.
- **Provenance travels with every transformation** so a result can be traced to analytical choices.

</div>

Use the [analysis decision map](concepts/decision-map.md) if you know the research question but not the representation. For manuscripts, start with the [reporting checklist](methods/reporting.md) and [limitations](methods/limitations.md).
