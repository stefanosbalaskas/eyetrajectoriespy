---
title: Scientific article library
description: Thematic scientific library for functional gaze analysis, W3 simulation evidence, missing-gaze sensitivity and exact identification studies.
---

# Scientific article library

An organized route through **method tutorials, interpretation guidance, independently auditable research and negative results**. Articles explain a specific question, the assumptions behind it and its evidence boundary; they do not turn experimental methods into stable product APIs.

!!! info "Published software versus research"
    **Stable 1.2.0** is now the current PyPI release, including ten transparent module-scoped workflows. E1–E4 helpers remain experimental. W3 studies and their original/independent archives **do not** establish general 90% simultaneous confidence-band calibration or field identification of observation-dependent missing gaze.

## Start with the scientific method

<div class="grid cards" markdown>

- **Which trajectory analysis should I choose?**

  Functional PCA, paired sparse MFPCA, repeated-trial regression, generalized responses and recurrence.

  [Choose among ten workflow families](choosing-the-ten-workflows.md) · [Input representations](../concepts/representations.md)

- **How should I read a figure?**

  Component alignment, effect functions, covariance diagnostics and explicit recurrence parameters.

  [Interpret synthetic workflow figures](interpreting-workflow-figures.md) · [Scientific figure atlas](../figures/index.md)

- **How should a study be reproduced?**

  Model contracts, input audit, declared choices and portable reproducibility bundles.

  [Reproducible bundles](reproducible-workflow-bundles.md) · [Research source reproduction](../development/research-reproducibility.md)

- **Which evidence actually qualifies a claim?**

  Distinguish a passing execution, an independently replayed archive, identifiability, interval coverage and released product readiness.

  [Evidence versus qualification](evidence-vs-qualification.md)

</div>

## Functional inference under stress (R76–R81)

| Question | Read |
| --- | --- |
| Why can nominal whole-function bands under-cover? | [Whole-band coverage interpretation](when-w3-simultaneous-bands-undercover.md) |
| What if predictor leverage is concentrated? | [R76 independent leverage support](how-independent-leverage-support-affects-coverage.md) |
| Does fixed covariance regularization help? | [R77 regularization](covariance-regularization-and-w3-coverage.md) |
| What if errors are temporally dependent? | [R78 time-varying AR(1)](w3-temporal-covariance-robustness-r78.md) |
| What if coordinate covariance is nonseparable? | [R79 bivariate covariance](w3-nonseparable-coordinate-covariance-r79.md) |
| What if independent units are heavy-tailed or asymmetrically contaminated? | [R80 Student-t5](w3-student-t5-heavy-tail-inference-r80.md) · [R81 skewed shocks](w3-skew-unit-contamination-r81.md) |

These synthetic inclusion proportions are tied to **registered data-generating laws** and are not universal estimates of nominal coverage.

## Observation-dependent missing gaze and external validation (R82–R88)

| Question | Read |
| --- | --- |
| Can high gaze retention conceal insufficient functional support? | [R82 observation process](w3-response-dependent-gaze-loss-r82.md) |
| Are signed MNAR sensitivity parameters empirically identified? | [R83 selection sensitivity](w3-mnar-selection-sensitivity-r83.md) |
| When can genuinely new missing-outcome measurements identify a *restricted* model? | [R84 external validation](w3-external-validation-mnar-identification-r84.md) |
| What if secondary validation is itself selective? | [R85 secondary return](w3-biased-validation-mnar-r85.md) |
| Can randomized audits of validation failures help? | [R86](w3-random-audit-secondary-missingness-r86.md) |
| What if randomized audit returns still depend on the missing outcome? | [R87](w3-selective-audit-return-r87.md) · [R88](w3-r88-return-audit-sensitivity.md) |

## Sharp bounds and identification (R89–R95)

These studies increasingly separate *new observed information* from *assumptions about unreturned values*.

| Stage | Central finding | Method detail |
| --- | --- | --- |
| [R89](w3-r89-sharp-observed-only-bounds.md) | Observed-only finite-population bounds | [Sharp-bound methods](w3-r89-sharp-bound-methods.md) |
| [R90](w3-r90-audit-saturation-selective-return.md) | Assignment saturation does not ensure actual response | [Saturation analysis](w3-r90-audit-saturation-methods.md) |
| [R91](w3-r91-guaranteed-recovery-design-ht.md) | Completed randomized recovery as a distinct design | [Design-based methods](w3-r91-guaranteed-recovery-methods.md) |
| [R92](w3-r92-near-complete-return-fragility.md) | Selective return can bias nominal weighting | [Conditional-bias methods](w3-r92-selective-return-methods.md) |
| [R93](w3-r93-exact-observed-law-nonidentification.md) | Exact same observed law permits different latent means | [Exact proof](w3-r93-exact-observability-methods.md) |
| [R94](w3-r94-external-audit-completion-bounds.md) | Sharp mean sets under **externally justified** completion floors | [Fraction methods](w3-r94-sharp-completion-floor-methods.md) |
| [R95](w3-r95-monotone-audit-return-identification.md) | Known return direction narrows; unknown sign does not | [Exact independent derivation](w3-r95-monotone-return-sharp-set-methods.md) |

[**Interpret identification bounds**](how-to-read-identification-bounds.md) · [**Compare the R93–R95 assumption ladder and widths**](what-sharpens-missing-gaze-bounds.md) · [Research study map](../research/studies.md)

![Exact normalized sharp-set widths, each conditional on a different external return assumption](../assets/site/r93-r95-assumption-widths.svg)

## More research and validation context

The independent [source and figure ledgers](../development/research-original-figures.md) document original artifacts and numerical audit denominators. Read [Bayesian feasibility boundaries](bayesian-feasibility-boundary.md), [authentic gaze usability](real-gaze-usability.md) and [interpreting W3 source audits](interpreting-w3-coverage-and-source-audits.md) for adjacent research questions.

**Research blockers remain open:** [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) (simultaneous inference) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) (observation-dependent missing gaze). [Release status](../news/release-status.md) · [News](../news/index.md)
