---
title: eyetrajectoriespy — Functional gaze analysis
description: Stable Python 1.1.0 functional gaze trajectory methods, reproducible guides and independently audited research evidence.
hide:
  - navigation
  - toc
---

<div class="et-home-intro" markdown>

<div class="et-home-label">Functional eye-tracking analysis · Python 3.11–3.13</div>

# Analyze the trajectory, not just the fixation count.

**eyetrajectoriespy** models gaze as a time-indexed two-coordinate functional process. Work with dense, sparse, irregular and repeated-trial trajectories while keeping the assumptions behind analysis and uncertainty visible.

[Install stable 1.1.0](start/index.md){ .md-button .md-button--primary }
[Explore methods](methods/index.md){ .md-button }
[Research evidence](research/index.md){ .md-button }

<div class="et-micro-status">**Published:** 1.1.0 · **Literal RC2 candidate:** 1.2.0rc2 (unpublished; qualification in progress) · **Open scientific blockers:** #289 / #296</div>

</div>

<div class="et-landing-visual" markdown>

![Conceptual illustration of planar gaze samples, time-indexed functional representation and inference](assets/site/hero-trajectories.svg)

<small>Conceptual synthetic schematic, not measured human gaze or a performance claim.</small>

</div>

## Begin with your scientific question

<div class="grid cards" markdown>

- **Explore variation in continuous gaze paths**

  Use FPCA and planar MFPCA to inspect structured temporal variation.

  [FPCA workflow](workflows/fpca-exploration.md)

- **Analyze sparse or asynchronous recordings**

  Respect irregular sampling and coordinate-specific recorded times.

  [Sparse planar methods](guides/sparse-multivariate-fpca.md) · [Irregular data](guides/irregular-trajectories.md)

- **Examine changing experimental effects**

  Fit interpretable functional regression with explicitly declared support and units.

  [Regression guide](workflows/experimental-functional-regression.md)

- **Model participants and repeated trials**

  Keep cluster structure and repeated observations visible.

  [Mixed-effects workflow](workflows/repeated-trial-mixed-effects.md)

- **Study recurrence and temporal dynamics**

  Report embedding, threshold and time-delay decisions.

  [Recurrence workflow](workflows/nonlinear-recurrence.md)

- **Report auditable decisions**

  Surface preprocessing, model assumptions, scientific contracts and failures.

  [Scientific contracts](concepts/contracts.md) · [Reporting](methods/reporting.md)

</div>

## Released software is not the same as ongoing research

<div class="et-release-grid" markdown>

<div class="et-release-panel" markdown>
<span class="et-eyebrow">Available via pip</span>

### Stable version 1.1.0

The published package contains qualified stable methods, including documented module-scoped sparse/irregular 1.1 additions.

```bash
pip install eyetrajectoriespy==1.1.0
```

[Quick start](quickstart.md) · [Stable API](reference/api.md)
</div>

<div class="et-release-panel et-release-panel--research" markdown>
<span class="et-eyebrow">Unpublished development</span>

### 1.2 experimental source

The ten orchestrated workflow routes and W3 inference investigations are research/candidate material. A new literal RC2 has **not** been qualified or published. GitHub Release/PyPI promotion of 1.2 remains **on hold**.

[Research library](research/index.md) · [Release status](news/release-status.md)
</div>

</div>

## Explore scientific evidence

<div class="et-figure-pair" markdown>

![R82 original selective-missing-gaze support and refusal evidence](assets/research/w3-r82-missingness-retention-and-grid-refusal.svg)

![R95 conditional sharp binary mean sets under different return-direction assumptions](assets/w3-r95-monotone-direction-sharp-sets.svg)

</div>

**Read each figure in the context of its source.** R82 shows that apparently high gaze retention can coexist with inadequate independent-unit support. R95 proves conditional sharp *population* bounds given externally justified return assumptions; it does **not** establish the true missing-gaze mechanism or calibrate nominal-90% confidence bands.

[Study map R76–R95](research/studies.md){ .md-button }
[Scientific figure atlas](figures/index.md){ .md-button }

## Latest news

<div class="et-news-strip" markdown>

<div markdown>

**23 October 2026 · R93–R95 original and independent evidence**

Exact observational equivalence, completion-floor assumptions, and monotone-return sensitivity—with sources and scientific limits.

[Research update](news/2026-10-23.md) · [News archive](news/index.md)
</div>

<div markdown>

**Product status remains unchanged**

Published 1.1.0. Experimental 1.2 and whole-function inference / field-MNAR qualification remain on hold.

[Release status](news/release-status.md) · [Roadmap](roadmap.md)
</div>

</div>

## Transparent research software

The package starts after gaze has a scientifically interpretable time and coordinate representation. It **complements**, rather than replaces, fixation/saccade detection, instrument-level QC, AOI/scanpath methods and upstream recording workflows.

[Representations](concepts/representations.md) · [Mathematical reference](methods/mathematical-reference.md) · [Workflow guide](workflows/index.md) · [Contribute](contributing.md) · [GitHub](https://github.com/stefanosbalaskas/eyetrajectoriespy)
