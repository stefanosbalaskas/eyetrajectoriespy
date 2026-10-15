# R33 — independent high-leverage and wrong-working-covariance CR2 falsification

**Research-only prespecified high-risk stress, not a 90% coverage qualification or API release.** [R32 pilot](w3-r32-reml-plugin-cr2-results.md) showed that observed-only Gaussian REML plug-in covariance and the oracle generating covariance produced the same 90%-nominal CR2 interval truth-inclusion decisions for 16 independent Gaussian blocks, but only in favorable ordinary-support, matched-family, complete/time-MAR cases. R32's green engineering CI cannot justify that conditional covariance inference generalizes to high-leverage or incorrectly modeled working covariance.

## New independent source and explicit factorial

New seed **202610153333**, **24 genuinely new independent generating blocks**, each nested n24/n96 participants, original complete irregular native gaze with 1–3 trials/person. Cross the four independently specified original R16 support/covariance designs:
- Ordinary predictor spread (source x ~ U[-.95,.95]) with predictor-independent slope covariance;
- Ordinary spread with predictor-dependent slope covariance;
- **Extreme leverage** (first two original predictor values replaced with +3 and −2.5) with independent covariance;
- Extreme leverage with dependent covariance.

On each exact source trajectory, fit **both** independently specified working covariance families: participant random-slope covariance either shared or predictor-scaled. Therefore each Gaussian generator is analyzed under one correctly specified family and one deliberately **wrong functional covariance**. Exactly 24×2×4×2 = **384 paired model-family evaluations**, NOT 384 independent generating blocks. Native response, participant/trial identifiers, timestamps and weights are held fixed between the two fitted models per source; only the *estimated* working family differs. Legendre-5 fixed mean basis and the focal functional predictor contrast are held constant. No empirical gaze data, non-Gaussian innovations, MNAR or physiological sensor models are added in this stage.

## Independent generator covariance and observed-data REML

For each source, independently compute **known true Gaussian covariance blocks** from original generating variance components and the *true source covariance family*, never the fitted or misspecified nuisance family; verify every covariance block against the established R17 original-source construction, especially in extreme predictor conditions. This oracle arm provides a consistent numerical reference for the same realized trajectories irrespective of what nuisance working family will be fitted.

In the parallel data-only arm, fit independent Gaussian restricted likelihood (REML) using **only observed native responses, WLS mean design and participant/trial/time/predictor labels**, once under the matched covariance form and once under the wrong form. Neither original true random effects, original generator variance coefficients, nor expected covariance blocks can reach the REML estimator. Preserve positive-constrained REML estimated components, flags for near-zero/bounded estimates, optimizer failures, and *separately counted* R22 scaled-Cholesky CR2 numerical refusals.

For this one prespecified single focal contrast, define its Gaussian truth as the known generating functional mean projected onto the **identical observed weighted Legendre-5 design**, not silently the unprojected generating focal slope; separately record the projection difference. Apply original R22 numerically guarded CR2 adjustments to oracle and to REML-fit target. On accepted computations, report experimental two-sided **90%-nominal** inclusion using (a) coefficient-specific *conditional* Satterthwaite df and (b) t(G−1). The fitted covariance has sampling uncertainty **not accounted for** in the current conditional Satterthwaite reference.

## Failure-inclusive scientific reporting

For **each of 16 predeclared source size/support/working-family cells**, denominator is **24 independent generating blocks**. Record source failures; REML nonconvergence; numerical CR2 refusal; fraction numerically accepted, with 95% Wilson intervals; raw truth-inclusion fraction **among accepted computations** with its Wilson interval; **joint acceptance and truth inclusion over all original source cases**; medians of conditional SE and df; paired oracle/plugin half-width ratios and true-interval-inclusion disagreements only when both are accepted. Mismatched-family component estimates are **not** compared with incompatible generator component values. Only *matched* fitted families receive a postfit simulation-specific slope <5%-of-truth boundary flag.

Never discard or reinterpret refused cases to make conditional truth-inclusion appear nominal. The four source designs and n24/n96 conditions are nested across the same 24 independent generating blocks; **do not pool 384 paired computations as 384 independent experiments**. Each cell's independent n is just 24, and resulting Wilson confidence intervals remain wide: R33 is a falsification/feasibility pilot, not evidence of precise nominal calibration. If numerical failures or undercoverage emerge, preserve them, localize them, and design larger independent reference replications before modifying estimation code.

## Inference/release boundaries

Even a green R33 original-source workflow cannot qualify estimated-target CR2/Satterthwaite confidence intervals, because REML nuisance covariance estimation uncertainty is not included in those df. Nor would this evaluate simultaneous confidence bands, non-Gaussian correlated measurement errors, unobserved sample-selection effects, eye-tracker device quality or empirically validated trial covariance. Maintain historical original R20 **41/256 failures**, R22 **32 numerical refusals**, and all R23–R32 negative scientific outcomes as immutable evidence.

Scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain OPEN. Draft research PR stacked on [R32 #334](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/334), no protected-main merge, supported public API promotion, 1.2 release tag or PyPI publication.
