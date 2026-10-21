# W3 R88 — prospective sensitivity to outcome-selective audit nonreturn

**Frozen research protocol — no empirical R88 results or scientific qualification until original source and independent numerical audit pass.** This work is stacked on the R87-A draft research branch. It does not change the public package, API, protected main, release metadata, or PyPI.

## Motivation and estimand

R87 demonstrates in synthetic data that a randomly assigned audit can fail to recover selectively unreturned outcomes. R88 asks a **conditional sensitivity** question: given a stipulated, simulator-calibrated return-propensity baseline and an assumed range for hidden-outcome dependence, how do the **fitted first-stage selection coefficients** change when every assumption uses precisely the same observed returns?

Random assignment probability is known by design. **Return-completion propensity conditional on the unavailable response is not identified from the audit-return subset alone.** In particular, the generating outcome coefficient does not become estimable merely because randomized assignment occurred. R88 **does not** claim a field-identifiable correction or sharp partial-identification bounds.

## Prospective design and source isolation

- 32 NEW independent primitive generating blocks for each native-unit design (independent curves versus 36 participants with three repeated trials), totalling 64 independent complete synthetic source conditions; never treat the repeated method rows as independent sources.
- New, separate random streams for complete X/Y, first-stage MAR/MNAR masks, secondary validation, third-stage randomized assignment and actual return. Master seeds 202610218880–202610218884. These are distinct from R86/R87 streams.
- Source family matches the existing heavy-tailed, skew-contaminated two-anchor, predictor-heteroskedastic gaze simulation; 31 time positions and 2 coordinates. Missing public input **must** still be rejected by the stable API.
- Paired first-stage MAR (true δ=0) and MNAR (true δ=1.1), audit assignment fractions q=0.25 and 0.50, and actual outcome-selective return with **simulator-known** coefficient γ=1.35.
- Four **assumed** return-sensitivity scenarios: γ∈{0, 0.675, 1.35, 2.025}. The recorded-input baseline is treated as *known by simulation assumption*, not fitted from real-world return records. Including true γ is an oracle-alignment comparator, **not** an identifiable or implementable data-derived estimate.
- Exactly 32×2×2×2×4=**1,024** analysis records, from 64 independent X/Y conditions and 128 paired MAR/MNAR masks. Same audit assignment, actual return records, and original observed Y under all four γ assumptions. A changed γ does **not** reselect or impute any outcomes.

The conditional return family is logit p(return|assigned,X,time,Y)=logit p0(X,time)+γ tanh((Y−μ_pilot(X,time))/0.08), where μ_pilot is estimated solely from originally observed outcomes. The design-known baseline p0 depends on recorded predictors, trial and time. The true generating γ is visible to simulation code, **not** the fitted sensitivity procedure.

## Frozen primary comparisons

For each native-unit × first-stage mechanism × randomized assignment-fraction cell, aggregate the fitted first-stage δ, signed error versus generating δ, and complete/refused counts separately at the four assumed γ values. Describe paired within-source shifts from γ=0 to γ=1.35 and assess qualitative sensitivity across the other predeclared assumptions. **Do not** label the observed γ-spread a formal confidence interval, identified set, confidence band, or probability coverage.

The score functions use originally observed or actually recovered Y only; simulated hidden outcomes are used solely to generate the missingness/return process and to compute *privileged source truth*. Tests explicitly corrupt never-recovered Y after fixing original selection and require exact invariance of all fitted outcomes.

## Acceptance gates and disclosure

1. All Python 3.11–3.13 score/identity/hidden-Y nonuse contracts pass.
2. Eight four-block source shards complete with no deleted/refitted generating conditions.
3. The fail-closed aggregate verifies exact 1,024-row factorial identity, 32 unique original blocks per fixed cell, paired measured-return digests, original source checkout and every shard SHA256; archive includes complete cases, summary, source-commit and aggregate SHA256SUMS.
4. A **separately coded** independent R88-A replay against the immutable original artifact must reconstruct X/Y sources, masks, assignments, return subsets, coefficients and refusals. Passing the original CI alone is insufficient.
5. Only after R88-A should a **documentation-only** article and original-data SVG proceed through strict docs CI and independent Pages deployment.

If any numerical or provenance gate fails, preserve the failure and revise in a traceable research PR. No unqualified MNAR point identification, real-world gaze recovery, uncertainty calibration, or nominal-90% simultaneous-band claims are authorized.

Research blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain OPEN. Stable 1.1.0 and production inference API remain untouched; **v1.2/PyPI release HOLD**.
