# W3 R87 — prospectively specified failures to return randomized audit outcomes

**Research-only falsification study, 21 October 2026.** This is not an MNAR-identifying method, calibrated interval, or public package feature. No release authorization.

## Why R87 follows the independently verified R86 experiment

R86 original PR #434 and independent numerical audit PR #435 verified 256 synthetic source conditions, 512 MAR/MNAR masks and 4,608 strategy records, with 12/12 original and 4/4 independent audit science jobs passed. Under its two-influential-unit heteroskedastic source, an independently randomized audit of 25–50% of second-stage validation failures supplied otherwise unobserved synthetic outcomes. This reduced large source-only apparent-selection distortions: for complete curves under original MAR truth delta=0, the naïve no-audit estimate was +0.657, while the audit-weighted 25% estimate was −0.002; for participant means, +0.668 versus −0.001. For original MNAR truth delta=1.1, 25% fitted estimates were approximately +1.017 (curves) and +0.979 (participants). These are modeled point estimates, not identification in actual incomplete gaze, estimator uncertainty or calibrated simultaneous bands.

A hidden vulnerability remains: *random assignment to an audit does not ensure the assigned gaze outcomes are successfully returned*. If return/completion itself depends on hidden Y, ignorability of the audit-assignment coin does not imply ignorability of realized audit data.

## Frozen generating structure

R87 uses **32 new independent source-generating blocks**, disjoint new RNG seeds, two native units-of-analysis (72 independent curves or 36 participants × three trials), the prespecified two-influential-predictor-unit heteroskedastic source, and original MAR/MNAR loss. Within a source, missingness stages and candidate audit fractions reuse the same original X/Y, first-stage mask, secondary-validation success draws, third-stage audit-assignment uniforms and *new independent audit-return uniforms*.

New source RNG seed **202610218780**, first-stage mask **202610218781**, secondary recovery **202610218782**, audit assignment **202610218783**, and return-completion **202610218784**. Original missing response values remain unavailable to fitted strategies unless successfully recovered; the original stable package should still refuse incomplete native function-on-scalar trajectories.

For each second-stage validator failure, independently assign a third-stage audit with probability q in **0.25 or 0.50**. Conditional on assignment, compare three frozen **audit return** laws:

- **Complete return:** every assigned outcome is successfully measured.
- **Recorded-input selective return:** return probability depends on the observed predictor magnitude, trial and time, without dependence on hidden outcome.
- **Outcome-selective return:** the same recorded-input propensity plus logistic dependence on the original latent residual, with source generating coefficient 1.35. This truth is simulator-only and is *not* available to empirical analysts.

All three return laws use exactly the same new independent return-uniform realization for paired comparisons. Assigned-but-not-returned outcomes remain unobserved; they are not imputed and are not used by the fitted pilot.

## Fixed estimation comparisons and falsification outcomes

For every law, apply three prospectively specified second-stage selection assumptions to the **same returned observations**:

1. **assignment_only:** assume every assigned audit returns data; use the intended assignment probability q.
2. **recorded_propensity:** use the stipulated recorded predictor/time return model; this is correct only under that law and is deliberately misspecified under outcome-dependent return.
3. **outcome_oracle:** use the full true third-stage completion law, unavailable without privileged simulator knowledge.

Estimate the two-parameter secondary recovery-selection model by scores weighted inversely by assumed *audit-assignment × audit-return* probability, with primary secondary successes retained at weight one. Use only original first-stage observed Y plus genuinely remeasured secondary and third-stage returns. Given an accepted secondary model, compute the original R86 first-stage logistic selection coefficient using the modeled total recovery propensity p_secondary + (1 − p_secondary) × q × p_return, with the frozen prespecified first-stage offset and score gates. Refuse an estimate rather than silently using an incomplete score. No thresholds are tuned to coverage outcomes.

The predeclared primary descriptive endpoint is the original MNAR true delta=1.1 difference between recorded_propensity and outcome_oracle under outcome-selective audit failure, evaluated separately for each native design and both q values. Secondary descriptors include estimated secondary gamma (truth 1), first-stage MAR false-positive delta (truth 0), audit-assigned and audit-returned counts, failed audit-response counts, and numerical refusal rates.

This factorial yields **64 new independent complete-data source conditions**, **128 original MAR/MNAR masks**, and **2,304 strategy/source records**, with **32 genuinely independent generating blocks** per fixed design×mechanism×audit fraction×return law×strategy cell. The 2,304 records are repeated within-source comparisons, *not* independent subjects or independent Gaussian generating samples.

## Source integrity and release boundaries

Run **eight immutable four-block shards**, preceded by source/score and refusal tests on Python 3.11/3.12/3.13. Archive each source record including source seeds, shared X/Y digests, realized first-stage mask, secondary-validation successes, audit assignments, realized returned outcomes, and total observation unions. The aggregate checks the original source-checkout, all eight source case manifests, each SHA256 digest, all 32 primitive identities and 2,304 strategy records. A dedicated independent original-source audit must be performed after source aggregation; passing fixture tests alone is not evidence of scientific validity.

The outcome_oracle is a deliberate simulator-only control; its inclusion is not an assertion that outcome-dependent audit completion is identifiable from incomplete real observations. R87 tests a specified parametric source and records point-estimation distortions; it does not provide uncertainty intervals, observational identifiability, realistic recovery of lost eye-tracking observations, valid estimated-covariance CR2 function-on-scalar inference, or nominal-90% simultaneous confidence-band calibration.

Scientific issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain OPEN. Do not change the supported package inference API, merge experimental research into protected main, release v1.2, create tags, or publish PyPI/TestPyPI.

**Frozen before any original R87 scientific source outcomes.**
