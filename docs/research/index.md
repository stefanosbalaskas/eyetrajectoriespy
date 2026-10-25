---
title: Research & evidence
description: Independently audited functional gaze simulation, missing-data identification and Bayesian feasibility evidence, separated from released package features.
---

# Research & evidence

[Find evidence by research question](../start/find-a-topic.md) · [Search and filter the W3 evidence map](../tools/evidence-explorer.md){ .md-button .md-button--primary } · [Full R76–R95 study chronology](studies.md)

**Open science with its failure cases intact.** This area explains what the development programme *tested*, what original archives and independent auditors reproduced, and which conclusions remain unsupported. It is separate from the [stable 1.2.0 product](../releases/1.2.0.md).

!!! warning "Research ≠ a release qualification"
    **1.2.0 is published, but these research claims remain unqualified.** Simulation and source audits do not establish general nominal-90% simultaneous functional-band calibration or identify outcome-dependent gaze loss. Ten W1–W4 module-scoped workflows are stable engineering APIs; E1–E4 helpers remain experimental. [Blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain open.

<div class="grid cards" markdown>

- **Functional inference under stress — W3**

  Leverage, cluster dependence, temporal and cross-coordinate covariance, heavy tails, contamination and observation support.

  [Read the W3 study map](studies.md) · [Why calibration fails](../articles/when-w3-simultaneous-bands-undercover.md)

- **Missing gaze and audit return**

  R82–R95: MCAR/MAR/MNAR loss, selective secondary validation, known invitation, sharp bounds and externally assumed completion direction.

  [Identification explainer](../articles/how-to-read-identification-bounds.md) · [Original/independent evidence](../development/research-development-hub.md)

- **Synthetic scientific visualizations**

  Inspect original figures with provenance and interpretation limits—not decorative performance claims.

  [Figure atlas](../figures/index.md) · [Research source figures](../development/research-original-figures.md)

- **Methods, numerical replication and provenance**

  Find simulation protocols, immutable source archives, independent replay and negative results.

  [Evidence dashboard](../development/research-scientific-dashboard.md) · [Reproduction guide](../development/research-reproducibility.md)

</div>

[**New synthesis: which external information actually sharpens a missing-gaze identified set?**](../articles/what-sharpens-missing-gaze-bounds.md) compares R93, R94 and R95 on the same observed return law without treating assumptions as observed facts.

## Interpretation rules

A successfully executed experiment proves **that its algorithm ran under its specified data-generating law**. An independently reproduced source archive provides reproducibility evidence; it does **not** convert a failed or underpowered inference procedure into a valid one. The [qualification boundaries](../articles/evidence-vs-qualification.md) distinguish numerical reproducibility, statistical calibration, identifiability and software-release readiness.

## Recent W3 results

| Study | What it identifies | What it does **not** identify |
| --- | --- | --- |
| [R93](../articles/w3-r93-exact-observed-law-nonidentification.md) | Sharp binary outcome sets for an observed return law | Unreturned outcomes from invitation alone |
| [R94](../articles/w3-r94-external-audit-completion-bounds.md) | Conditional sharp sets under externally assumed completion floors | Whether those floors hold in field gaze |
| [R95](../articles/w3-r95-monotone-audit-return-identification.md) | Conditional bounds if outcome-specific return direction is externally known | Direction of return from observed return data alone |

[View all W3 studies](studies.md) · [What changed](../news/index.md)
