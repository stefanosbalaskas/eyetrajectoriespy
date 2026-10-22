# W3 R92 — near-complete audit return and fragility of nominal design weighting

**Prospectively frozen research-only protocol (22 October 2026).** No production estimator, release or website evidence until original and independently implemented actual-source audits pass.

## Scientific question

R91 established an exact **conditional design-unbiasedness identity** for an HT estimator *if an independently Bernoulli-selected subset of previously unrecovered synthetic outcomes actually completes measurement with known probability*. That is an idealized measurement intervention. R92 tests the fragility of that identity to **small actual noncompletion**, distinguishing (i) randomized audit invitations and (ii) a second, potentially outcome-dependent response step.

This is a falsification of **nominal weighting assumptions**, not a study that can empirically identify real-data MNAR response probabilities. A negative outcome does not imply the earlier source mathematics was incorrect.

## Fixed independent source and paired factors

- Fresh, disjoint streams: `202610229200` for 64 complete independent X/Y source conditions (32 independent 72-curve blocks; 32 independent 36-participant × three-trial blocks), `202610229201` for paired first-stage MAR/MNAR loss, `202610229202` for outcome-selective secondary recovery, `202610229203` for third-stage *assignment* and `202610229204` for *actual completion*. Blocks are newly drawn, not recycled R91 sources.
- Per complete source: two paired first-stage masks (MAR versus outcome-dependent MNAR); 8 frozen conditional randomized assignment/retrieval repetitions; assignment probability `g∈{0.25,0.50}` nested via a common uniform field.
- Actual return scenarios (7): exact complete response `c=1` at failure 0; uniform response `c=1−δ` at `δ∈{.01,.05,.15}`; and outcome-dependent response `c_i=1−δ(0.5+Z_i)` at the same three levels. The latter uses simulator-only transformed outcome `Z_i=clip((Y_i+1)/2,0,1)`; **the response probability is not observable or supplied to the estimator**. This is a controlled synthetic completion law, not an empirically identified return process. Conditional completion probabilities lie in `[1−1.5δ,1−0.5δ]`.
- Same assignment U and return V fields are reused for every scenario within a source and repeat. The seven laws are matched, not seven independent original datasets. Original source denominator **64 complete independent conditions; 32 generating blocks per fixed native design**. Total repeated source-method rows `64×2×8×2×7=14,336`, **not 14,336 independent observations**.

## Observed-data estimands and exact simulator-only design expectations

The finite-population estimand is the realized mean of the bounded transformed gaze response **among initially missing synthetic target records**, whose count N is known. Earlier secondary observations S are included as observed census members. Among remaining unobserved U, let `I_i~Bernoulli(g)` be randomized invitations, `R_i~Bernoulli(c_i)` conditional on true Y be actual completions, and `Z_i` their bounded target outcome. The actual measured indicator is `I_i R_i`; invitation by itself does not reveal Z.

Compare two fitted estimates, both computed **strictly from measured responses**, and not supplied with c_i:

1. **Assignment-only HT:** `[sum_{S}Z + sum_{U}I R Z/g]/N`. It wrongly treats all assigned values as if they returned.
2. **Nominal-uniform adjusted HT:** `[sum_{S}Z + sum_{U}I R Z/{g(1−δ)}]/N`. It is design-unbiased only if actual completion probability really equals `1−δ` independently of the still-unobserved outcome. The assumed δ is a hypothetical *policy constant*, not a fitted or identified return rate.

Conditional on each complete synthetic finite source, exact analytic design biases are

$$
\mathrm{Bias}_{assignment}= -\frac{1}{N}\sum_{i\in U}(1-c_i)Z_i,
\qquad
\mathrm{Bias}_{nominal}=\frac{1}{N}\sum_{i\in U}
\left(\frac{c_i}{1-\delta}-1\right)Z_i.
$$

Thus perfect completion gives zero bias for both estimators; uniform noncompletion causes assignment-only negative bias but nominal-uniform adjustment has *exactly zero conditional bias*; outcome-selective completion generally leaves a nonzero bias in the nominally adjusted estimator despite an almost-complete return policy. **Simulator-only full outcomes are used solely for these oracle analytic biases and true-target error checks**, never fitted.

These identities are about expectation over repeated *invitations and completed-response events*, not confidence interval coverage, minimax bias or exact point identification of a particular incomplete realized source. A nominal adjusted estimate can fall outside [0,1].

## Prespecified contrasts and transparency gates

For every fixed native source × MAR/MNAR × g × return law × δ cell, with 32 independent source blocks and 8 conditional repeats per block, report both empirical mean signed error and root-mean-square error, *simulator-only analytic conditional bias* for assignment-only and nominal adjusted weighting, mean actually returned counts, mean failure counts and sharp observed-only finite-population bounded-mean width. These metrics are **descriptive**, not nominal 90/95% coverage intervals or statistical significance tests.

All source X/Y, first-stage, secondary and randomized assignment SHA256 digests must be identical across matched return policies at the same g and repetition. Return counts must decline monotonically as δ grows and as actual completion becomes more selective *within each law* for fixed coupled uniforms; sharp widths rise accordingly. At δ=0, assignments all return; under strictly uniform c=1−δ, oracle nominal-bias must be machine-zero; no field response propensity is identified. All unfavorable source/realization errors and any rejected CI runs are retained. The estimator must reject any hidden unreturned Y not marked NaN in observed inputs.

Three Python-version contracts, eight disjoint four-primitive-block fresh-source shards and the complete SHA256 archival aggregation must pass. **A separate R92-A audit implementation that never imports the original R92 generator/estimator or production package must independently download the exact full original immutable archive, regenerate all 14,336 rows, all source and return digests, oracle and observed-only results and summaries, and pass 4/4 dedicated jobs** before scientific publication. Only then may a separate docs-only website PR with original-data SVG figures run all CI and protected-main Pages deployment.

## Interpretation and release hold

Neither invitation randomization, an assumed nominal completion fraction, nor a fitted response rate from the selectively completed subset is sufficient to justify unbiased recovery in the outcome-selective scenario. Exact identification of MNAR return probabilities, unrecoverable real gaze signals, functional regression slopes or 90% simultaneous-band coverage is **not** established by this synthetic experiment. [Issue #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) and [issue #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) stay **open**. Experimental original/audit code remains **draft, unmerged**, public version 1.1.0 unchanged, v1.2 GitHub/PyPI publication **HOLD**.
