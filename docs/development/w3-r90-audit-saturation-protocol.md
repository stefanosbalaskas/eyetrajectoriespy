# W3 R90 — does 100% randomized audit assignment eliminate partial identification?

**Prospectively frozen before original scientific CI. Research-only simulation, not a package estimator.** Source experiments are on a draft branch based on protected `main`, with fresh and disjoint source, first-stage mask, secondary validation, assignment and audit-return random streams.

## Motivation and falsifiable contrast

R89 computed sharp finite-population worst-case bounds for a transformed bounded gaze outcome among records initially missing. R90 evaluates the distinction between **100% of records assigned an audit** and **100% of outcomes actually returned**, with five nested assignment levels. This is a finite-population information accounting result, not a new frequentist interval procedure or a generally identified MNAR correction.

Under the **ideal complete-return** audit law, all previously unmeasured outcomes become known when assignment reaches 100%, hence the bound widths are exactly zero. Under **outcome-selective actual return**, assignment of 100% may still leave unmeasured outcomes, so an irreducible *policy-specific nonreturn floor* remains unless every assigned outcome actually completes. The floor is relative to the simulated actual return law and chosen bounded estimand; it is not a universal population bound or the same as a statistical variance limit.

## Frozen sources, target, factorial and source pairing

- Two native source designs: 72 independent curves or 36 participants with three repeated trials, 31 time positions × two synthetic gaze coordinates; Student-t-like radial scaling, temporally correlated disturbances, heteroskedasticity and asymmetric rare shocks. `32` independent primitive generating blocks per design: **64 complete independent synthetic source conditions**.
- MAR and response-dependent MNAR first-stage masks on paired sources, using shared missingness random uniforms: **128 paired mask conditions**.
- Outcome-selective secondary validation, followed by five *nested* assignment fractions **q = 0%, 25%, 50%, 75%, 100%** and two actual return laws: (i) complete response among the assigned and (ii) outcome-selective completion. Same masks, assignments and returned-outcome random uniforms within all paired comparisons.
- **1,280 repeated source × missingness × return policy × assignment analysis rows**, not independent replications. Five disjoint master seeds `202610229000`–`202610229004`, independent of all R89 and earlier R87/R88 streams.
- Target is the fixed bounded transformed outcome `Z = clip((Y+1)/2, 0, 1)` among initially missing realized records. Also its positive-minus-negative predictor-group mean contrast. It does not bound general raw gaze, historical missing sensor signals, first-stage MNAR δ or functional regression slopes.

For N initially missing outcomes and n actually measured, the sharp bounded-mean interval width is **(N−n)/N**, evaluated solely from observed outcomes and original target/recovery masks. It is a worst-case finite-population interval, **not a confidence interval**. The simulation-only hidden outcomes supply deterministic truth inclusion checks, never fitting data. The source API rejects any numerically filled nonreturn outcome in the observed-only bounds routine.

## Prespecified primary outcomes

1. Across all five assignment fractions, for both laws and each native-design × missingness cell, report the **mean per-source width** of the sharp bounded-mean interval, mean group-contrast width, and actual assigned-versus-returned counts.
2. Under q=100% report the remaining *selective-return* mean width (policy-specific saturation floor) versus exactly zero under ideal complete return. Keep the source-level denominator **32 independent primitive blocks** for each fixed cell.
3. For each source and policy compute whether the bounded-mean width reaches the two **descriptive, prespecified thresholds 0.10 and 0.05** at any member of the five-level assignment grid. Report counts reaching/not reaching and first qualifying assignment fraction. These thresholds are **not** significance levels, nominal coverage probabilities, valid CI widths or a justification for a scientific quality claim.
4. Report 0% assignment as a negative/control baseline. It must be identical under both return laws because no follow-up audits occur. Assignment masks must be identical under competing completion policies, measured counts nested in q, and width monotone nonincreasing across nested q.
5. Report source-block counts whose positive-minus-negative contrast bound excludes zero, without any claim that such an exclusion proves general MNAR identification.

## Source provenance, independent audit and publication gate

Three Python-version contracts (3.11–3.13) plus eight four-block original science shards are required. All original source cases and failures are retained. Final aggregate must check exact 1,280-row identity, per-source nested return invariants, checkout equality and every SHA256 member; no rerun/exclusion conditional on a study result.

Only a **separately coded R90-A independent numerical implementation** that downloads the immutable original full archive, regenerates all original fresh X/Y source conditions, first-stage masks, secondary validations, all five nested audit fractions under both return laws, observed-only bounds, source-level thresholds and complete failure denominators can qualify this as independently reproduced. Publication of articles and SVG figures requires the independent real-archive replay PASS and separate strict docs CI plus protected-main GitHub Pages deployment. This research source remains unmerged and draft.

No claim of response-parameter identification, real historical gaze recovery, validated 90% functional bands or readiness for release 1.2 is authorized. [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) and [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) remain open. Stable 1.1.0 remains unchanged, no release tag/GitHub Release/PyPI.
