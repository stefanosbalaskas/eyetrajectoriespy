# W3 R58 — first original independent-source Gaussian boundary-reference results

**Original numerical experiment passed, null-reference calibration not qualified.** This is a frozen 24-independent-primitive-block Gaussian diagnostic, not a supported variance-component test. Original scientific run: [#39027935413](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39027935413) (**8/8** dedicated jobs successful). Original source archive: [#12098994180](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39027935413/artifacts/12098994180); original PR **merge checkout**: `c1d4c0f5f7805d1f2dd746e6208f0087c68395d6`. An independent SHA256/numerical read-only audit is **separate**, not automatically established by this science job.

## Preregistered design and complete denominator

R58 generated **24 NEW independent Gaussian primitive blocks** from seed `202610175858`, each with 24 participants and native irregular trial support. Each block supplies paired ordinary/extreme leverage and true-zero/positive generating slope states. Thus **96 source variants are 24 primitive independent blocks, not 96 independent draws**. All **96/96** nested comparisons were numerically accepted: 192/192 H0/H1 selected model slots, 576/576 original solver-start slots recorded, **zero source/model/likelihood comparison refusals**. Six original source shards plus the original complete aggregate and source manifests were successfully created. This is numerical execution and original provenance, not inferential validation or global optimizer proof.

## Candidate 50:50 boundary-reference diagnostic

The planned benchmark is **50% point mass at zero + 50% chi-square(1)**, with candidate alpha .05 strict rejection at twice-profiled NLL gap **>2.70554345409542**. It is *not* assumed to be a valid finite-sample RLRT distribution in an irregular repeated-trial model with fitted nuisance components.

| Paired leverage support / generating slope | Candidate exceedances (24 independent blocks per cell) | Raw exceedance frequency | 95% Wilson interval | H1 selected fitted slope at exact zero | Median accepted nested gap |
|---|---:|---:|---:|---:|---:|
| Ordinary / **true zero** | **5/24** | **0.2083** | **[0.0924, 0.4047]** | 6/24 | 0.38164 |
| Extreme / **true zero** | **2/24** | **0.0833** | [0.0232, 0.2585] | 7/24 | 0.18715 |
| Ordinary / true positive | 8/24 | 0.3333 | [0.1797, 0.5329] | 6/24 | 0.40705 |
| Extreme / true positive | 11/24 | 0.4583 | [0.2789, 0.6493] | 8/24 | 1.92034 |

**Scientific interpretation.** The ordinary true-null cell has a Wilson interval entirely above the candidate nominal 0.05 rejection rate. On this specific design, the classic asymptotic boundary benchmark displays evidence of anti-conservative behavior, rather than demonstrated calibration. For extreme leverage 2/24 remains too imprecise to reject a 0.05 true rate; no general robustness conclusion follows. Positive-generating-state exceedances are **not qualified statistical power**, because the candidate reference has failed to establish its own null size. Within-block leverage and state pairs may be compared descriptively, not pooled as independent replication counts. No numerical-refusal sensitivity interval is needed in this original run because every case was accepted, but the failure-inclusive source denominator remains a prospective invariant.

The fitted alternative selected an *exact zero* slope parameter in 6/24 ordinary true-null and 7/24 extreme true-null cases; positive-source corresponding counts 6/24 and 8/24. This does not identify the generating variance accurately and cannot serve as a surrogate test.

## Research decision and limits

R58 **does not validate** an asymptotic chi-bar-square reference, finite-sample nominal type-I control, statistical power, simultaneous function-wide bands, 90% pointwise fitted-covariance CR2 intervals, random-slope identification or whole-participant MNAR selection. The independent Gaussian simulation unit is still only 24 blocks per stratum and evidence applies only to the frozen nuisance and source family. The original `cases.json` archive has optimizer scores and likelihood summaries, but **not full native raw responses**; a separate read-only audit can verify archived numbers and source ids, not independently reproduce raw generative Gaussian outcomes.

**Next priority:** independent immutable-source numeric re-audit of all 96 cases and 576 starts; then larger independent-source *null-calibration* with either justified design-specific restricted-likelihood reference or null-parametric-bootstrap calibration with full nuisance refits, and standalone validation of calibration cutoffs on disjoint generating blocks. Do not reuse the same null blocks both to learn and evaluate an empirical critical value without acknowledging adaptive bias. Record failures even if a bootstrap or optimizer cannot qualify. The fitted-covariance CR2 inferential programme remains separate.

Maintain research blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) OPEN. No protected-main merge, release version 1.2, public inference API or PyPI distribution.
