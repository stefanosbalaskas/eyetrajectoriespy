---
title: Cite eyetrajectoriespy and reproduce an analysis
description: Cite the published 1.2.0 Python software accurately, distinguish method citations, and record a reproducible eye-tracking analysis.
---

# Cite the software, preserve the analysis

The published **eyetrajectoriespy 1.2.0** package is software for continuous and functional eye-tracking trajectories. A software citation is **not** evidence that a particular scientific estimator is qualified for a new research design. Cite the software version you actually used and, separately, the statistical method or validation evidence relevant to your analysis.

[Published 1.2.0 release](../releases/1.2.0.md){ .md-button .md-button--primary }
[Public API and version boundaries](../reference/api-stability.md){ .md-button }
[Research reporting checklist](../methods/reporting.md){ .md-button }

## Software citation

The following fields come from the repository's [CITATION.cff](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/main/CITATION.cff) and [published release](https://github.com/stefanosbalaskas/eyetrajectoriespy/releases/tag/v1.2.0):

> Balaskas, S. (2026). *eyetrajectoriespy: Functional and Continuous Trajectory Analysis for Eye-Tracking Data in Python* (Version 1.2.0) [Computer software]. https://github.com/stefanosbalaskas/eyetrajectoriespy

For a BibTeX-compatible software entry, use:

~~~bibtex
@software{balaskas_eyetrajectoriespy_2026,
  author  = {Balaskas, Stefanos},
  title   = {eyetrajectoriespy: Functional and Continuous Trajectory Analysis for Eye-Tracking Data in Python},
  year    = {2026},
  version = {1.2.0},
  url     = {https://github.com/stefanosbalaskas/eyetrajectoriespy}
}
~~~

The release's CFF metadata currently **does not declare a DOI**. Do not manufacture one. If your software environment differs from the published 1.2.0 distribution (e.g. an unreleased development commit or repository-only adapter example), cite the **exact commit** and explicitly name it as development software.

## Which evidence should accompany a citation?

| What you use | Additional source to report | What not to claim |
| --- | --- | --- |
| Published 1.2.0 stable API | [Release notes](../releases/1.2.0.md), actual public function and its documented method | That the package version alone validates hardware or study design |
| One of ten module-scoped W1–W4 routes | [Workflow contracts](../workflows/workflow-orchestration.md) and report bundle | That the orchestration wrapper automatically validates all estimates |
| Sparse/irregular or coordinate-specific observations | [Native irregular guide](../guides/irregular-trajectories.md) and [sparse FPCA](../guides/sparse-irregular-fpca.md) | That gaps were observed or imputed without declaring a method |
| Functional confidence bands | [Inference assumptions](../methods/assumptions.md) and [validation ledger](../validation/reference-validation-ledger.md) | That W3 whole-function bands are generally calibrated |
| Repository SyeLink, pymovements or BIDS examples | [Integration status](../integrations/index.md), exact upstream version and commit | That these previews are released, qualified vendor/device adapters |
| Experimental E1–E4 helpers | [Experimental development boundary](../workflows/experimental-expansion.md) | That an unreleased helper is stable or publishable inference |

## Minimum reproducibility record

Keep the following together with any figure or research table:

1. **Source and consent:** acquisition system, original-export provenance, eligibility, and whether the files are recorded or simulated.
2. **Software provenance:** Python version, exact \`eyetrajectoriespy\` distribution version or commit, optional libraries and acquisition parser versions.
3. **Measurement contract:** gaze eye, timestamp origin and unit, x/y coordinate system and screen geometry, sample masks, transformations and any gap handling.
4. **Independent units:** participants, nested trials, experiment conditions, exclusion counts and the unit used for validation or resampling.
5. **Scientific analysis:** predeclared question, estimand, method, hyperparameters, diagnostics, sensitivity checks, and inferential scope.
6. **Outputs:** executable script, random seeds, environment record, figures and a retained [reproducibility bundle](../articles/reproducible-workflow-bundles.md).

The [downloadable seeded teaching example](../tutorials/reproducible-starter.md) illustrates a reproducible path but contains fabricated values—not empirical eye-tracking records.

!!! warning "Scientific uncertainty remains conditional"
    Whole-function inference under the open [W3 qualification issue #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and field identification under [missing-gaze issue #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) must not be described as generally validated. See [limitations and failure modes](../methods/limitations.md).

## Prefer a persistent research record

For replication, save a frozen repository commit or tagged release, the CFF citation, a dependency lock/environment manifest, scripts, data-permission terms and clearly labelled intermediate outputs. A GitHub repository link is the available source identifier here; **no archival identifier or DOI is asserted**.

[Begin a first analysis](first-analysis.md) · [Visual methods explorer](../tools/figure-storyboard.md) · [Stable versus experimental status](../news/release-status.md)
