---
title: Find a topic — eyetrajectoriespy documentation
description: Reader-intent index to functional gaze workflows, sparse FPCA, source integration, research uncertainty, equations, reproducibility and release provenance.
search:
  boost: 1.3
---

# Find the right documentation

Not every reader needs the full API reference. Choose the question you are
trying to answer, then follow the **stable method**, its **worked example**,
and the **scientific limitations**. This topic guide is a directory of
existing material, not an additional estimator or a new research qualification.

[Start a first analysis](first-analysis.md){ .md-button .md-button--primary }
[Search the methods](../methods/index.md){ .md-button }
[Explore research evidence](../research/index.md){ .md-button }

## Find a scientific method

| You want to… | Start with | Continue with |
|---|---|---|
| Install the published package and fit a first model | [Five-minute first analysis](first-analysis.md) | [Quick start](../quickstart.md) |
| Decide what raw data shape is admissible | [Data-to-method guide](data-to-method.md) | [Input schemas](../guides/input-schemas.md) |
| Analyze sparse or irregular single-coordinate gaze | [Native sparse FPCA / PACE](../guides/sparse-irregular-fpca.md) | [Bandwidth choice](../guides/sparse-bandwidth-selection.md) |
| Jointly model sparse **x/y** trajectories | [Sparse planar MFPCA](../guides/sparse-multivariate-fpca.md) | [Asynchronous x/y sampling](../guides/sparse-multivariate-async.md) |
| Analyze repeated participant/trial observations | [Repeated-trial mixed effects workflow](../workflows/repeated-trial-mixed-effects.md) | [Covariance sensitivity](../methods/functional-mixed-effects-covariance-sensitivity.md) |
| Model binary/count functional outcomes | [Generalized responses workflow](../workflows/generalized-responses.md) | [Generalized functional response methods](../methods/generalized-function-on-scalar.md) |
| Analyze scanpath recurrence / nonlinear trajectories | [Nonlinear and recurrence workflow](../workflows/nonlinear-recurrence.md) | [RQA conventions](../methods/rqa-software-conventions.md) |

## Find evidence, not just a method name

| You are asking about… | Best page | What not to infer |
|---|---|---|
| Simultaneous inference or coverage under leverage | [Research evidence](../research/index.md) · [Failure cases](../articles/when-w3-simultaneous-bands-undercover.md) | Executable simulation code does not guarantee nominal coverage |
| Missing gaze, MCAR, MAR or MNAR | [Observation-process guide](../guides/observation-process-diagnostics.md) · [Identification bounds](../articles/how-to-read-identification-bounds.md) | A source or return pattern alone does not identify unobserved outcomes |
| Reproducibility and independent checks | [Evidence dashboard](../development/research-scientific-dashboard.md) · [Reproduction guide](../development/research-reproducibility.md) | A reproduced negative result is still a negative result |
| Equations and software contracts | [Mathematical reference](../methods/mathematical-reference.md) · [Function-to-equation index](../reference/function-equation-index.md) | Mathematical documentation does not certify every use case |

## Find tools, integrations, and reporting guidance

- **I have a device export:** [integration navigator](../integrations/navigator.md)
  and [Eye-Tracking-BIDS acquisition context](../integrations/acquisition-and-bids.md).
  Example-level handoffs are not qualified device importers.
- **I have a CSV:** [local data-readiness inspector](../tools/data-readiness.md);
  it checks structure without uploading your file.
- **I want a figure:** [illustrated methods](../tools/figure-storyboard.md),
  [visual gallery](../methods/visual-gallery.md) and
  [research figure evidence](../figures/index.md).
- **I need to choose a supported workflow:** [canonical workflows](../workflows/index.md)
  and [ten-route comparison](../tools/workflow-comparison.md).
- **I need a citation, version or release record:** [cite and reproduce](cite-and-reproduce.md),
  [stable 1.2.0 release](../releases/1.2.0.md), and
  [historical decision archive](../development/unpublished-candidate-history.md).

## Using site search

The header search is **local to the documentation index**; it does not submit
the user's query to a third-party search service. Material's built-in shortcuts
include **/** or **S** to focus search, **Up/Down** to move between results,
**Enter** to follow a result, and **Escape** to close. The built-in search
highlight can preserve a search term in a result URL. The
[documentation quality audit](../development/sitewide-experience-audit.md)
explains what automated index and browser tests can—and cannot—establish.

!!! info "Published product versus active research"
    The published stable package is **1.2.0**. W1–W4 orchestration routes are
    supported as module-scoped APIs; E1–E4 helpers remain experimental.
    Unqualified whole-function inference and missing-gaze identification
    are tracked separately under
    [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
    and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296).
