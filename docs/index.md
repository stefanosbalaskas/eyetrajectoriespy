---
title: Functional gaze trajectories, without hidden analytical decisions
---

!!! info "Development documentation"
    This website follows the active `main` development line (**0.9.1.dev0**).
    The stable PyPI release is **0.9.0**. See the
    [0.9.0 release notes](releases/0.9.0.md) or the
    [frozen 0.9.0 documentation source](https://github.com/stefanosbalaskas/eyetrajectoriespy/tree/v0.9.0/docs)
    when you need documentation tied to the published release.

<div class="et-hero" markdown>
<div class="et-kicker">eyetrajectoriespy · functional gaze analysis in Python</div>

# Model the viewing process, not only its summaries

A vendor-neutral scientific layer for continuous gaze trajectories, functional
data analysis, repeated-trial inference, and nonlinear trajectory methods —
with consequential analytical choices kept explicit.

<div class="et-install" markdown>

```bash
pip install eyetrajectoriespy
```

</div>

[Get started](quickstart.md){ .md-button .md-button--primary }
[Choose a workflow](workflows/index.md){ .md-button }
[View on GitHub](https://github.com/stefanosbalaskas/eyetrajectoriespy){ .md-button }

<span class="et-pill">Continuous trajectories</span><span class="et-pill">FPCA / MFPCA</span><span class="et-pill">Functional regression</span><span class="et-pill">Repeated-trial models</span><span class="et-pill">Nonlinear dynamics</span><span class="et-pill">Explicit provenance</span>
</div>

## Which analysis do you need?

Start from the scientific question, sampling hierarchy, and outcome type. The
five canonical routes are the recommended entry points; specialist methods
remain available through the guides, methods, examples, and API.

<div class="grid cards" markdown>

-   **Continuous gaze exploration + FPCA**

    Represent the trajectory explicitly, inspect dominant variation, and
    evaluate component stability without hiding preprocessing decisions.

    [:octicons-arrow-right-24: Start FPCA workflow](workflows/fpca-exploration.md)

-   **Experimental functional regression**

    Estimate how declared scalar predictors change a continuous functional
    response, with explicit design and whole-function inference.

    [:octicons-arrow-right-24: Start experimental workflow](workflows/experimental-functional-regression.md)

-   **Repeated-trial functional mixed effects**

    Preserve participant → trial → time hierarchy and separate fixed-effect
    inference from covariance diagnostics and sensitivity.

    [:octicons-arrow-right-24: Start mixed-effects workflow](workflows/repeated-trial-mixed-effects.md)

-   **Generalized binary/count responses**

    Keep Bernoulli, grouped-binomial, Poisson-count, and exposure-adjusted rate
    observation contracts explicit.

    [:octicons-arrow-right-24: Start generalized workflow](workflows/generalized-responses.md)

-   **Nonlinear / recurrence analysis**

    Begin from a declared state representation and recurrence specification;
    treat sensitivity analysis as robustness evidence rather than tuning.

    [:octicons-arrow-right-24: Start nonlinear workflow](workflows/nonlinear-recurrence.md)

</div>

[Browse the five canonical routes](workflows/index.md){ .md-button .md-button--primary }
[Full capability inventory](reference/capability-inventory.md){ .md-button }

## See the scientific object

<figure class="et-home-figure">
  <a href="methods/visual-gallery.md">
    <img src="assets/gallery/planar-trajectories.svg" alt="Synthetic continuous planar gaze trajectories generated for the eyetrajectoriespy visual gallery">
  </a>
  <figcaption>
    Synthetic continuous planar gaze trajectories. Documentation CI regenerates
    the gallery deterministically from package code; the gallery links figures
    to their methods, public APIs, and mathematical contracts.
  </figcaption>
</figure>

<div class="et-flow" markdown>
<span>native gaze</span><b>→</b><span>functional representation</span><b>→</b><span>declared preprocessing</span><b>→</b><span>model / decomposition</span><b>→</b><span>diagnostics & uncertainty</span><b>→</b><span>scientific interpretation</span>
</div>

The package treats the path to a result as part of the scientific specification.
Missingness, time support, scaling, registration, basis projection, model family,
and resampling unit therefore remain visible choices.

[Open the visual gallery](methods/visual-gallery.md){ .md-button }
[Read the mathematical contracts](methods/mathematical-reference.md){ .md-button }

## A 60-second 2-D analysis

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
```

This minimal example is intentionally small. Real analyses should start from the
[quick start](quickstart.md), then follow the canonical workflow that matches the
sampling unit and scientific question.

## What eyetrajectoriespy refuses to hide

<div class="grid cards" markdown>

- **Missingness stays missing** until interpolation or exclusion is explicitly requested.
- **Smoothing is opt-in** because abrupt gaze transitions can be genuine.
- **Registration is opt-in** because latency can carry theory.
- **Irregular-to-grid projection is explicit** because overlap, union, and gap rules change the observed process.
- **Resampling units are explicit** because repeated trials are not independent participants.
- **Provenance travels with transformations** so results remain traceable to analytical choices.

</div>

!!! important "Not a replacement for event analysis"
    Whole-trajectory FDA answers different questions from fixation, saccade,
    AOI-transition, and latency analyses. eyetrajectoriespy complements those
    methods rather than replacing them.

## Scientific qualification

<div class="grid cards" markdown>

-   **Cross-platform qualification**

    Core qualification covers Python 3.11–3.13 across Linux, Windows, and
    macOS, with optional-backend qualification tracked separately.

    [:material-check-decagram: Release readiness](release-readiness.md)

-   **Independent-reference validation**

    Analytical truth, independent implementation equivalence, and
    simulation-recovery evidence are recorded separately from ordinary unit
    tests.

    [:material-flask-outline: Validation ledger](validation/reference-validation-ledger.md)

-   **Reproducible scientific figures**

    The documentation workflow regenerates the deterministic SVG gallery and
    validates its references during the strict documentation build.

    [:material-chart-line: Visual gallery](methods/visual-gallery.md)

-   **Implementation-matched equations**

    Public methods are linked to mathematical contracts and explicit scope
    boundaries rather than relying on names alone.

    [:material-function-variant: Mathematical reference](methods/mathematical-reference.md)

</div>

## Explore deeper

<div class="grid cards" markdown>

-   **Choose a representation**

    Planar path, irregular process, repeated-trial process, AOI composition,
    registered amplitude, or phase function.

    [:octicons-arrow-right-24: Representation guide](concepts/representations.md)

-   **Audit assumptions and failure modes**

    Check observation units, hierarchy, estimands, diagnostics, and conditions
    under which a result should fail or remain under review.

    [:octicons-arrow-right-24: Assumptions & diagnostics](methods/assumptions.md)

-   **Inspect specialist methods**

    Sparse PACE FPCA, phase analysis, trajectory geometry and distances,
    recurrence, Lyapunov analysis, transfer entropy, surrogate testing, and
    sensitivity workflows.

    [:octicons-arrow-right-24: Capability inventory](reference/capability-inventory.md)

-   **Follow worked examples**

    Move from executable examples to the method page, mathematical contract,
    and plotting output.

    [:octicons-arrow-right-24: Worked examples](tutorials/index.md)

-   **Find a public function**

    Browse the public API or map a function directly to its equation and scope
    boundary.

    [:octicons-arrow-right-24: Public API](reference/api.md)

-   **Plan a reproducible analysis**

    Use the reporting, pre-registration, portability, and reproducibility
    checklists before treating a pipeline as final.

    [:octicons-arrow-right-24: Pre-registration checklist](methods/preregistration.md)

</div>

## Release, citation, and source

**Stable release:** `0.9.0` · **development line:** `0.9.1.dev0`

[Install from PyPI](https://pypi.org/project/eyetrajectoriespy/){ .md-button .md-button--primary }
[0.9.0 release notes](releases/0.9.0.md){ .md-button }
[Citation metadata](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/main/CITATION.cff){ .md-button }
[API stability policy](reference/api-stability.md){ .md-button }
