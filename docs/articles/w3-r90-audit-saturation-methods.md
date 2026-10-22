# Interpreting audit saturation without mistaking assignment for observation

*Methods companion to [W3 R90](w3-r90-audit-saturation-selective-return.md) · 22 October 2026*

## Estimand and what the word “sharp” means

The analysis conditions on the **realized set of originally missing records**, whose membership is represented by the first-stage missingness mask. The target is the finite-population mean of the prespecified bounded response $Z=\operatorname{clip}((Y+1)/2,0,1)$ among those records, not the original unbounded gaze response or a functional regression coefficient.

If there are $N$ originally missing records, and outcomes for $n$ are actually measured by secondary validation or completed follow-up audits, the unknown bounded outcomes may collectively contribute anywhere from 0 to $N-n$. With no restrictions beyond $0\le Z\le1$, both endpoints are attainable. Consequently the finite-population mean has sharp interval

$$
\left[\frac{\sum_{i\in S}Z_i}{N},\frac{\sum_{i\in S}Z_i+N-n}{N}\right],
$$

where $S$ contains actually measured records, **not simply assigned records**. Its width $(N-n)/N$ is a deterministic fraction of unavailable data. It has no guaranteed 90% or 95% confidence interpretation.

For a positive-minus-negative predictor-group contrast, subtract opposite bound endpoints in the two disjoint observed groups. This contrast bound can be wider than one; it is sharp under no additional constraints on unreturned data.

## Saturation identities and their limits

The five nested randomized assignments are q=0, 0.25, 0.50, 0.75 and 1. Assignment uses common uniforms; therefore a record assigned at q=0.25 is also assigned at higher q, with actual-return uniforms held fixed. With identical underlying masks, the number of truly observed outcomes cannot decrease, so the bound width is nonincreasing.

Under the **ideal complete-return policy**, q=1 forces every initially missing record either to be recovered in secondary validation or returned in its assigned audit, making $n=N$. Bound width zero and point identification of the realized finite mean are then tautological. They do not establish a universal method for field-data MNAR identification.

Under the **outcome-selective return policy**, even q=1 need not make $n=N$. The nonzero remaining interval width is the realized fraction of unreturned records, specific to the synthetic return law, sources and target definition—not a general or irreducible law of missing data.

At q=0, no third-stage audit is assigned; both return policies must coincide exactly. This provides a negative control against accidental policy-driven changes before assignment.

## Thresholds are descriptive decisions, not significance tests

For each independent generating block and policy, the original study computes the earliest of the five assignment levels whose bounded-mean width is at most 0.10 or 0.05, or records that the threshold is never reached. These cutoffs are **descriptive information-width criteria**. They are not hypothesis-test thresholds, confidence levels or a quality standard validated for actual eye-tracking data.

At q=1, all 32 sources per fixed cell cross both thresholds under complete return, while none cross under the frozen selective-return law. This is observed conditional on the source generator, not an uncertainty claim about a population of users.

The number of independent source conditions is 64: 32 primitive blocks in each native design. MAR/MNAR, return law and five assignment levels are paired reanalyses of those sources. The **1,280 resulting records must not be counted as 1,280 independent experimental replications**. Repeated trials and within-trajectory time points are also not independent source blocks.

## Original and independently reconstructed scientific evidence

The [original R90 run #39746751227](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39746751227) completed 12/12 dedicated scientific jobs, including eight fresh-source shards and a SHA256-checked original ledger. The [independent R90-A run #39747852468](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39747852468) completed 4/4, including mandatory replay of all 1,280 original source records with separately coded generation and bounded estimands.

The first independent real-archive run failed because the replay checked an inherited R89 summary field instead of R90's frozen field name. The audit was corrected **without changing the source generating process, archived outcomes or interval computations**, and the subsequently rerun immutable original replay passed. Preserve both the failed and corrected runs in the evidence ledger.

Agreement between original and independent implementations is evidence of software/numerical reproducibility only. It does not show that selectively missing real-world outcomes are identified, that a return propensity is estimable, or that W3 simultaneously covers true functional slopes with nominal 90% frequency.

## Release boundary

The experimental R90 and R90-A implementations remain unmerged draft PRs. Only articles and source-derived SVG plots may enter protected main after their own strict CI and Pages deployment. Issues [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) (response-dependent gaze loss) and [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) (simultaneous-band coverage) are still open. Stable 1.1.0 remains unchanged, and **v1.2 GitHub/PyPI publication is on hold**.
