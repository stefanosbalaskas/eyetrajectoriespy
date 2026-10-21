---
title: Why an independent audit of validation failures changes the information available
description: R86 methods companion on third-stage double sampling, otherwise missing outcomes and restricted selection models
---

# Why an independent audit of validation failures changes the information available

**Methods companion · 21 October 2026 · independently audited R86**

The original incomplete gaze recording and the external validation sample have **two different observation processes**. The [R85 falsification study](w3-biased-validation-mnar-r85.md) showed that even an originally MAR gaze-loss mechanism can appear MNAR if the external validator preferentially recovers some otherwise missing outcomes and the analyst assumes that validation is random.

R86 evaluates an additional **third-stage randomized audit of the secondary validator's failures**. This is not retrospective imputation; the complete-data simulator newly reveals a random subset of outcomes unavailable to both preceding measurement stages. It allows a conditional parametric secondary selection model to be estimated from observed successes and independently audited failures. The scientific question is what extra information is required, not whether the real sensor can furnish it.

!!! warning "A synthetic measurement intervention is not an existing eye-tracker capability"
    No currently demonstrated technology for recovering historical genuinely missing gaze outcomes is established. The randomized failure audit exists only inside complete-source simulation. Its usefulness for a restricted logistic model does not establish general MNAR identification, valid uncertainty intervals or nominal-90% continuous-function bands. Issues #289/#296 remain open; version 1.2 stays unreleased.

## What the three audit strategies actually assume

Under a frozen secondary selection law, an originally missing gaze outcome is first recovered by an outcome-selective validator. The remaining secondary failures are independently audited with probability q=0, .25 or .50. Only secondary successes and genuine third-stage recovered failures have Y available.

**Naïve union** assumes the secondary validator had constant recovery probability .25. **Audit-estimated union** fits an intercept and residual-dependent parameter from the now observed secondary successes and audited secondary failures, weighting the latter by the known inverse randomized audit probability. It uses a conditional-mean pilot derived strictly from originally observed first-stage outcomes, never the simulator's true source conditional mean. **Simulator-only union oracle** computes recovery weights using a source-known true mean and outcome-dependent probability that an actual analyst would not possess.

The combined propensity for an originally missing response to become observed is

$$
\pi_q(Y)=q+(1-q)r(Y).
$$

The first-stage outcome-selection score uses the original visible outcomes and only genuinely recovered originally missing outcomes. At q=0, the **audit-estimated** method explicitly refuses gamma and first-stage delta: it does not manufacture evidence about secondary failures from successes alone.

## Why the MAR negative control is essential

![R86 true MAR and MNAR first-stage model coefficients under no audit and genuine synthetic random audits](../assets/research/w3-r86-randomized-audit-first-stage-delta.svg)

*Figure 1.* Original MAR means true first-stage delta=0. With an outcome-selective secondary validator and no randomized audit, the naïve fitted coefficient was approximately +.657 for curves and +.668 for repeated participants in the adverse source design. Audit-estimated weights produced means close to zero with either 25% or 50% randomized auditing.

That apparent correction is **conditional on the third-stage audit actually measuring the otherwise missing outcomes**, the audit randomization being correct, and the two-parameter recovery law providing a useful approximation. It is not equivalent to deriving the originally missing Y from existing incomplete gaze.

## The secondary model can be fitted, but not without assumptions

![R86 fitted second-stage outcome selection parameter gamma after the randomized audit supplies additional outcomes](../assets/research/w3-r86-secondary-gamma-from-random-audit.svg)

*Figure 2.* The simulator uses secondary gamma=1.0. In the two-anchor heteroskedastic source, fitted gamma with positive audit probabilities averaged roughly .89–.97 depending on first-stage design and recovery fraction. The visible-only residual pilot is distinct from the true conditional mean, so source means need not equal generating truth.

The 256 complete X/Y source conditions comprise **32 new genuinely independent generating blocks per fixed design/support/variance cell**, with 512 original paired MAR/MNAR masks and 4,608 downstream strategy evaluations. The repeated-trial participants are independent **participants**, not three independent participants per trial. Multiple audit fractions on the same source do not create independent biological replications.

## A finite-source correction is not a calibrated confidence procedure

![R86 full eight original MNAR source cells, mean absolute first-stage delta error](../assets/research/w3-r86-all-cell-delta-errors.svg)

*Figure 3.* Source-average absolute error is often smaller after the third-stage model is fitted, but can be slightly larger at 50% than 25% audit. The naïve zero-audit and positive-audit fitted methods also differ in both the data actually measured and modeling assumptions. No covariance estimator, participant-cluster standard error or inferential coverage calculation is performed here.

A practical next research advance would require demonstrating an **actual auxiliary recording or validation source**, documenting how and when it can measure responses absent from the original gaze stream, and validating its selection behavior independently. Additional synthetic weighting variants cannot establish that physical missing measurements can be recovered.

Original [R86 scientific source #39639148930](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39639148930) passed 12/12 jobs and separately coded [R86-A actual archive #39640120223](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39640120223) passed 4/4, reconstructing all 256 X/Y, 512 first-stage masks and 4,608 audit-strategy rows. Numerical reproducibility is established for **this synthetic design**, not real-world measurement or confidence validity.

[Full R86 scientific article](w3-random-audit-secondary-missingness-r86.md) · [Source and original figure evidence](../development/w3-r86-third-stage-audit-evidence-ledger.md)
