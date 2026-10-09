# Empirical calibration: first predeclared scientific wave

**Research only. No release authorization, automatic estimator promotion or inference
certification.** This is an actual Monte Carlo study, not a smoke-test proposal.
Its GitHub Actions workflow uses two nonoverlapping deterministic shards with
master seed `20261009` and retains independent case-level files, failures,
SHA256 manifests, audited aggregates and full GitHub run provenance.

## Executed designs and predeclared numerical settings

| Track | Per-shard design | Across two shards | Likelihood/model |
|---|---|---|---|
| B6 learned sparse population | 200 refits × 6 distinct scenarios | 2,400 fitted attempts, 400/scenario | Native participant-level learned Gaussian Gibbs posterior |
| B7 learned x/y planar population | 200 refits × paired/asynchronous × ranks 1/2 | 1,600 fitted attempts, 400/scenario | Actual learned joint cross-covariance Gaussian Gibbs |
| F1 full sparse group model | 150 null + 150 alternatives × 4 designs | 2,400 attempted tests | Native full sparse-PACE group-test path |
| F5 ordered functional changes | 150 × {null, one break, two breaks} × 8 null/dependence/block specifications | 7,200 attempted tests | Native whole-curve change-point bootstrap |

Total expected **13,600 independent fit/test attempts**. The F5
block-length settings share the same underlying scenario type but use
independently keyed replicate seeds. Every attempt has a persistent
scenario, shard, replicate and generated seed.

The Gibbs initial run intentionally uses `warmup=160`,
`draws_per_chain=70` and the models' two-chain defaults. These lengths
are sufficient for an *exploratory coverage diagnostic*, **not** proof
that posterior quantiles, chain convergence, effective sample sizes or
Bayesian calibration are satisfactory. No rank-based SBC is run.

F1 uses 199 permutations and F5 uses 199 bootstrap draws. Consequently
a seemingly exact 0.05 rejection boundary is quantized and adds Monte
Carlo randomization error to the operating-characteristic estimates.
The 300 attempted null fits per F1/F5 scenario are intentionally
**below** the long-term initial target of 1,000 per critical null;
these runs identify failures, pathological regimes and computational
feasibility for a subsequent preregistered larger campaign. The
300 attempted alternatives per scenario are also below 500.

## Evidence and interpretation controls

1. Each native model must be fitted from scratch on every generated
   participant-level dataset. Never substitute a cached score-kernel
   approximation.
2. Failed fits must remain in the CSV denominator and reported
   separately. Conditional intervals and rejection rates among
   successful fits are **not unconditional operating characteristics**.
3. Treat the two B6/B7 400-refit matched-prior samples as **empirical
   marginal coverage explorations**. Misspecified and near-tied
   scenarios are sensitivity analyses, not prior-based SBC.
4. B7's eight coordinate-time observations per new participant are
   dependent. Report average pointwise inclusion at the **participant
   replicate level**; an all-eight-points event is *not* an explicitly
   calibrated simultaneous 90% trajectory band.
5. F1's deliberately heteroscedastic unbalanced null intentionally
   violates exchangeability; a different false-positive rate there is
   not necessarily a defect in nominally valid exchangeable tests.
6. F5's two-break truth is a detection stress, not demonstration that
   the current estimator reliably localizes multiple change points.
7. Hashes, common master seed, scenario-specific replicate IDs and
   observed 63-bit seed collisions are audited before aggregation.

## How to inspect the GitHub evidence

The workflow is `research-empirical-calibration-wave1.yml` and starts
on the draft research PR only. Six model-fitting shard jobs create
`wave1-{b6,b7,f1-f5}-shard-{0,1}` artifacts. Three subsequent audit
jobs aggregate the verified shards and retain
`wave1-{b6,b7,f1-f5}-aggregate` artifacts. The aggregate logs expose
exact attempted/failed counts, binomial Monte Carlo intervals for
estimable quantities, and conditional alpha=.01/.05/.10 F1/F5
rejection. Failure of an aggregate must not be overlooked as a
successful study even if an earlier individual shard completed.

**No statistical finding is asserted until the actual complete
retained evidence has been independently inspected.** In particular,
a green workflow is engineering evidence that computations completed,
not an inferential decision. Final scientific qualification requires
long-chain Rhat/ESS/MCSE and rank-based SBC where appropriate, prior
and observation-noise sensitivity, independent comparator benchmarks,
and adequate replication under both null and alternative hypotheses.

The validation flags in
`BAYESIAN_B7_PREDICTION_QUALIFICATION.json` and
`SCIENTIFIC_CALIBRATION_BATCH_QUALIFICATION.json` are reconciled for
their **historical #248/#249 exact-head engineering checks only**.
They retain `scientific_inference_qualified=false`, and the
descendant research branch requires its own engineering CI.


**Results are now available.** Read the [actual first-wave B6/B7/F1/F5 scientific findings](first-empirical-calibration-findings.md) before interpreting any experimental 1.2 inference. The 400-refit matched Bayesian credible intervals undercovered severely and the F5 weak-block bootstrap failed nominal size under strong AR(1), depending on block length. All scientific and publication gates remain false.
