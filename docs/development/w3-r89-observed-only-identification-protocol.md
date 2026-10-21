# W3 R89 — observed-only partial identification under selective audit nonreturn

**Prospective research protocol · Frozen before original CI science run.** This is a deliberately narrow *finite-population* nonidentification experiment, not a missing-gaze estimator or functional inference method. It is implemented on a research branch derived from protected main without changing the production API.

## Why R89 differs from R87/R88

R87 established that randomized audit assignment cannot remove outcome-dependent attrition when assigned outcomes do not return. R88 showed that a fitted first-stage selection coefficient depends on the assumed hidden-outcome return coefficient. R89 asks a different, exactly solvable question: **What can the observed returns bound without a return-propensity or missingness model?**

The target is *not* the original unbounded gaze response, conditional regression slope, or first-stage MNAR coefficient. The predeclared scalar is `Z = clip((Y + 1)/2, 0, 1)`, an artificial but fully observed-value-computable bounded transformation of a normalized synthetic coordinate. The finite-population target is the realized mean of Z among records selected as initially missing in a frozen generating block. A second target is the difference in those means between positive- versus negative-predictor groups among initially missing records. Both targets concern the realized selected finite population, not a superpopulation distribution.

## Sharp, assumption-free algebra

Let M mark the initially missing target records, S the subset subsequently measured (secondary recovery or realized audit completion), N the count of M and n the count of S. Assume only that the bounded transformed outcome Z lies in [0,1], that M and S can be counted, and that actually measured Z is valid. Then, without any return model,

`L = sum(Z_i : i in S)/N`

`U = [sum(Z_i : i in S) + (N - n)]/N`.

The endpoints are attained as infimum/supremum by assigning all unmeasured bounded responses to 0/1. Thus [L,U] is sharp **for the finite selected population under exactly the stipulated [0,1] support and no other constraints**. It is *not* a confidence interval or a bound on a regression coefficient. For groups + and -, the positive-minus-negative contrast has the sharp interval `[L_plus - U_minus, U_plus - L_minus]` when the groups are disjoint and nonempty.

Because audit assignments use common underlying random uniforms, the 50% audit group nests the 25% group at fixed source. Similarly, actual returns under outcome-dependent noncompletion are a subset of returns under complete assignment-to-measurement. Therefore the widths under the larger realized measured subset cannot increase. This is an algebraic monotonicity check, not a nominal probabilistic coverage check.

The code that forms bounds receives only explicitly measured outcomes and NaNs at nonreturned target outcomes. A test rejects any hidden unreturned value appearing in the input. The simulator separately reveals latent source truth exclusively to check deterministic bound inclusion.

## Frozen experiment

- **64 new independent complete X/Y source conditions**, 32 generating blocks in each of the two native experimental designs: 72 independent curves or 36 participants with 3 repeated trials, across 31 time points and 2 coordinates. Response generation includes temporal correlation, participant effects, Student-t-like unit scales, heteroskedasticity and occasional asymmetric shocks. Fresh master seeds 202610228900 through 202610228904 have no overlap with earlier R87–R88 streams.
- Pair first-stage MAR and response-dependent MNAR missing masks using shared original source Y and uniforms. Record secondary validation and randomized third-stage audit assignment at q=0.25 or 0.50. Compare **complete** return after assignment with outcome-selective audit nonreturn, using common random streams.
- Record both target strata (X at least zero and X less than zero), first-stage missing-group N, actually recovered n, sharp bound endpoints, widths, positive-minus-negative contrast bounds and simulator-only actual truth. Missing-group strata cannot be empty; refuse a source condition rather than invent or drop records.
- Exactly `32 × 2 native designs × 2 missingness laws × 2 return laws × 2 audit fractions = 512` source-method records, from **64 independent source conditions and 128 paired missingness masks**. The 512 records are not independent experimental replications.
- Eight four-block new-source shards, failure-inclusive original ledgers, fixed-checkout manifests and SHA256 archive checks. Numeric and falsification tests on Python 3.11, 3.12 and 3.13.

## Prespecified scientific outputs

Report the mean source-level width of the finite-population bounded-mean interval, mean source-level width for the group contrast, source blocks whose contrast interval excludes zero, assigned-versus-returned counts, and original complete-source/first-stage denominators. Describe both complete-versus-selective actual return and 25%-versus-50% assignment comparisons using identical source blocks, not as independent designs. Source-level interval widths do **not** have a declared frequentist confidence interpretation.

By construction, simulation-only source truth must belong to these sharp bounds for every source. A 100% containment rate would be a deterministic consistency gate, **not statistical coverage calibration**. Report conditional behavior and any refusals; do not use this to infer the original unbounded outcome, arbitrary function-on-scalar regression slopes, identified MNAR return mechanisms, or nominal 90% simultaneous-band validity.

## Mandatory independent evidence gate

The original R89 programme cannot be described as independently verified until a **separately coded** R89-A implementation retrieves the actual original SHA256 source archive and independently regenerates the primitive X/Y sources, paired observation masks, secondary validation, audit assignments, selectively returned records and algebraic bound endpoints for **all 512 recorded source cases**, including refusal evidence. Passing original source CI or tests is insufficient for independent scientific qualification.

Only after that independent gate and separately green documentation CI may research-only results and figures be published on the website. Research implementations stay as draft PRs, excluded from production.

Open science boundaries: [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) response-dependent gaze loss and [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) simultaneous 90% confidence-band undercoverage. Stable 1.1.0 and its public API remain unchanged. **Version 1.2 / GitHub release / PyPI remain HOLD.**
