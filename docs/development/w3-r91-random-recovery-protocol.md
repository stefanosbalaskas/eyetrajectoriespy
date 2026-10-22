# W3 R91 — what guaranteed randomized *completed* recovery can identify

**Prospectively frozen research protocol, 22 October 2026.** This is an exploration of design-based finite-population mean estimation under a strong *real outcome-retrieval* assumption, and is not a missing-data estimator added to the public package.

## Scientific question

R90 demonstrated, in a specified synthetic law, that assigning 100% of otherwise missing gaze records to an audit does not eliminate partial-identification uncertainty when some assigned outcomes still fail to return. R91 investigates a stronger prospective intervention: a Bernoulli **randomly selected subset of the remaining unobserved records is actually measured without selective noncompletion**. Assignment and completed retrieval coincide **by experimental assumption**. That may be impossible for historical gaze loss or genuine sensor failure. It must not be confused with random follow-up *invitations*.

Under known, positive, outcome-independent inclusion probability $g$, a design-based Horvitz–Thompson (HT) estimator is conditionally unbiased for the realized finite target mean, even if earlier validation was selective and initial missingness was MAR or MNAR. This analytic property identifies the **design expectation** of the estimator, not the realized missing full-population mean exactly for one incomplete sample, and says nothing about identifying the underlying MNAR observation process.

## Frozen design and independent units

- Two native generating designs: 72 independent curves, or 36 independent participants with three repeated trials. Each source is a 31-position × two-coordinate synthetic field with temporal correlation, participant heterogeneity, heavy-tailed radial scales, predictor heteroskedasticity and occasional asymmetric shocks. 32 independently generated complete source blocks per native design: **64 new independent X/Y source conditions**.
- The same source receives paired MAR and response-dependent MNAR first-stage masks, followed by a response-selective secondary validation that leaves an unrecovered portion. This creates **128 paired missingness masks**.
- From the still-unobserved records, a third-party validator independently Bernoulli-selects each record with known inclusion probability **g = .10, .25 or .50** and **actually returns every selected outcome**. The three probabilities are nested using shared random uniforms. This is an idealized *completed random retrieval*, not outcome-selective nonreturn.
- The independent retrieval stream is repeated **16 times for each fixed complete source and first-stage mechanism**. These are conditional randomization repetitions, not fresh independent generating X/Y sources. Exactly **32 × 2 × 2 × 16 × 3 = 6,144 paired method records**; there are only 64 independent complete-source conditions.
- Fresh master streams: 202610229100 (complete source), 202610229101 (first-stage observation masks), 202610229102 (secondary response-selective validation) and 202610229103 (randomized guaranteed actual retrieval), with a frozen distinct per-replicate offset. These streams are separate from all R89 and R90 streams.

## Bounded target and estimator

Use the already defined synthetic bounded transform `Z = clip((Y+1)/2, 0, 1)`; the target $μ_M$ is the realized mean of Z in the entire originally missing finite-record target population of size N. Suppose outcomes for a subset S are already actually observed via selective secondary validation. All remaining outcomes form U. Every $i\in U$ is retrieved independently with completed Bernoulli indicator $G_i\sim\mathrm{Bernoulli}(g)$.

$$
\hat{\mu}_{HT}=\frac{1}{N}\left[
\sum_{i\in S}Z_i+\frac{1}{g}\sum_{i\in U}G_i Z_i
\right].
$$

Conditional on the entire fixed source's outcomes and the previous selected subsets, random retrieval gives

$$
\mathrm{E}_{G}(\hat{\mu}_{HT})=\mu_M,
\qquad
\mathrm{Var}_{G}(\hat{\mu}_{HT})=
\frac{1-g}{g N^2}\sum_{i\in U}Z_i^2.
$$

The second expression is a **privileged simulator oracle**, not used as an observed-data estimator. The observable design-variance estimator is

$$
\hat{V}_{G}=\frac{1-g}{g^2N^2}\sum_{i\in U} G_iZ_i^2,
$$

which is itself unbiased conditional on the fixed complete source. These identities hold for independent *record-level retrieval indicators* conditional on the outcomes and previous observation process. They do not require the original gaze records to be independently distributed. Independence is in the designed sampling indicators, not in trial/time-trajectory outcomes.

**Crucial restrictions:** the HT point estimate may fall outside [0,1], even though individual Z_i are bounded. It is a design-unbiased estimate **over randomization**, not a sharp identified interval for a particular observed realization or a valid confidence band. No truncation of the estimator, no hidden-Y imputation and no plug-in nominal confidence statement are authorized.

## Prespecified evidence and falsification gates

For each fixed native design × MAR/MNAR × g cell report the **descriptive mean signed HT error**, root mean-squared HT error, mean naive-only-observed error, mean *estimated* design variance versus mean simulator-only *oracle* conditional variance, actual number of guaranteed completed records and sharp worst-case finite-population bounded interval width. Report 32 independent primitive source blocks per cell and 16 *within-source* randomized retrieval draws; the 512 source-replicate rows per fixed g cell are dependent.

The source-level 16-draw average is **not expected to equal the full target mean exactly**. Its finite Monte Carlo difference from zero is not a failure of analytic design-unbiasedness, nor is the squared-error comparison a calibrated confidence interval. An exact analytical enumeration of two Bernoulli draws in the test suite verifies conditional expectation and variance without Monte Carlo approximation; independently generated source-ledger results must include the signed estimation errors, including unfavorable cases.

Fail-closed protections: every complete-source X/Y and first-stage mask digest must remain unchanged across retrieval replicate and g; retrieval sets nested for fixed replicate; all selected guaranteed recoveries are actually measured; the HT estimator receives **NaN for every unreturned target outcome**, refusing any hidden observation leak; observed-only estimated variance must be computed from measured values only. Preserve all source-mismatches, failed trials, original SHA256 shards, generating checkout and source-denominator identity.

## Mandatory independent and website gates

Three Python-version contract checks, eight independent four-block source shards, and one complete original source-artifact aggregate with SHA256 must pass. Before any independently validated findings or scientific website plots are published, a separately coded **R91-A numerical/provenance audit** must download and reproduce the original immutable complete 6,144-row source archive, source/mask/guaranteed-recovery digests, analytic expectation/variance calculations and all fixed-cell summaries. The audit must not import original source/estimator implementations. Only then may documentation-only materials enter a separately gated CI/Pages PR.

The resulting work can show that true known-probability random **completed** retrieval permits design-unbiased estimation of this finite bounded mean under the stated intervention. It does *not* show such retrieval is available in real eye-tracking data, that ordinary audit invitations have random actual completion, that a missingness propensity is identified from observed data, that raw functional slopes are identified, or that 90% simultaneous confidence-band coverage is fixed.

Research blockers [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) and [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) remain **OPEN**. Original/audit code must remain on draft research PRs, not protected main. Stable public 1.1.0 remains unchanged, **v1.2 GitHub/PyPI release HOLD**.
