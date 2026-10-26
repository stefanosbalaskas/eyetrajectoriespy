---
title: Parallel documentation-generator evaluation
description: Historical non-deploying Zensical Classic compatibility evaluation preceding the selected Modern migration.
---

# Historical Zensical Classic compatibility experiment

This page preserves the earlier **non-deploying Classic-theme evaluation** from when MkDocs Material was the publication builder. It does **not** describe the selected Modern design or the current deployment state. The subsequent [Zensical Modern release-gated PR #503](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/503) adds native-search and full route/browser qualification while retaining a MkDocs rollback build. Manual assistive-technology review remains [open](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/499).

Zensical's [MkDocs migration guide](https://zensical.org/docs/compatibility/mkdocs/migration/) permits using the same `mkdocs.yml` with a reversible build command. Its [current plugin compatibility](https://zensical.org/docs/compatibility/mkdocs/plugins/) explicitly includes `search` and `mkdocstrings`. We use its **classic theme variant**, which is intended for existing Material-style sites with custom JavaScript and CSS.

## Implemented experiment

1. Use the existing production dependencies and generated scientific SVGs.
2. Run `mkdocs build --strict` unmodified, with output in `site/`.
3. Create an **ephemeral** `.zensical-preview.mkdocs.yml` differing only in isolated `site_dir` and `theme.variant: classic`.
4. Pin `zensical==0.0.72` in the experiment only; this is not a project dependency or published package extra.
5. Run the Zensical build into `build/zensical-preview-site/`; audit homepage, first-analysis tutorial, visual explorer, figures, methods, API and navigation-linked pages against the MkDocs baseline.
6. Save build logs and a machine-readable report as GitHub Actions artifacts. **No GitHub Pages deployment** occurs in this workflow.

The experimental workflow is explicitly non-blocking for the production deployment. An unsuccessful preview is a **real compatibility finding**, not evidence that MkDocs production is broken.

## Extended full-site acceptance checks

The separate CI report now counts **all rendered HTML routes** in each generator, flags missing historical URLs and core copied assets, and inventories the search-related files. At this historical stage, the production decision was on **HOLD** pending live-browser search, mobile/desktop accessibility and API fidelity. See the [site-wide quality programme](sitewide-experience-audit.md).

## Required future acceptance criteria

| Area | Acceptance threshold before any migration |
| --- | --- |
| Release/docs correctness | Both builders complete strictly against the same source and generated figures |
| API reference | `mkdocstrings` Python objects actually render with stable links |
| Figures | All generated SVG figures and legends resolve and have descriptive text |
| JavaScript | Interactive navigator, CSV inspector, filters and selectors survive instant navigation |
| User experience | Desktop/mobile theme, contrast, keyboard focus, and no-JS fallbacks pass visual browser checks |
| URLs | Published root and deep links remain compatible with existing `/eyetrajectoriespy/` routes |
| Governance | This experiment could not switch GitHub Pages; a separately qualified PR was required |

The [MNE documentation organization](https://mne.tools/stable/documentation/index.html) informed the distinction between first-analysis tutorials and example galleries. The [MNE examples gallery](https://mne.tools/stable/auto_examples/) explicitly warns that synthetic and shortcut demonstrations must be interpreted cautiously; the same boundary is retained in our new [visual methods explorer](../tools/figure-storyboard.md).

!!! warning "An exploratory build is not a completed migration"
    The audit compares a representative selection of generated pages and static assets, but does not certify pixel-equivalent rendering, comprehensive accessibility, correct scientific inference, all historical links, or package functionality. Only a verified separate full review could justify switching build systems.

[Visual methods explorer](../tools/figure-storyboard.md) · [First analysis](../start/first-analysis.md) · [Existing documentation versions](../versions/index.md)
