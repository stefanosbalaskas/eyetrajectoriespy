# W3 R80 Student-t5 functional inference — independently audited figure ledger

**Scientific evidence and SVG provenance · 20 October 2026 · research only**

!!! danger "No general 90% calibration"
    Source arrays and reference maxima have been independently numerically reconstructed under a **known synthetic Student-t5 unit-level scale-mixture law**. No observed-data estimator has earned nominal-90% simultaneous calibration, no authentic eye tracking, irregular sampling, dropout or MNAR study is claimed. W3 issues #289 and #296 remain open and eyetrajectoriespy 1.2 remains on release HOLD.

## Figure 1: full 31 × 2 functional slope truth inclusion

![Original R80 whole-function Student-t5 source coverage across five references and two levels of influential unit support](../assets/research/w3-r80-student-t5-whole-band-coverage.svg)

Each plotted cell evaluates **32 independent newly generated primitive source datasets**. The 256 total factorial source-condition cases include repeated experimental configurations from the same generating blocks; **999 reference draws per source and candidate do not add independent source replications**.

| Predictor-dependent source variance | Curves: 2 extremes | Curves: 16 extremes | Participants: 2 extremes | Participants: 16 extremes |
|---|---:|---:|---:|---:|
| Unchanged wild-HC1 | 3/32 | 20/32 | 7/32 | 26/32 |
| Source-observed HC3 Gaussian | 5/32 | 28/32 | 17/32 | 29/32 |
| Fixed HC3 λ=.25 Gaussian | 19/32 | 31/32 | 22/32 | 29/32 |
| Fixed HC3 λ=.50 Gaussian | 23/32 | 32/32 | 24/32 | 32/32 |
| **Source-known independent-unit Student-t5 mixture** | 29/32 | 30/32 | 28/32 | 30/32 |

A whole-slope truth inclusion means **all 62 coordinates** fall within the source-specific simultaneous band. Nominal .90 is the *reference quantile used*, not a validated general coverage frequency. In the primary two-anchor heteroskedastic condition, fixed λ=.50 yields only **23/32 (71.9%) independent curve** and **24/32 (75%) repeated-participant** whole-band truth inclusions.

The prespecified **constant-unit-variance** two-extreme controls gave baseline HC3 / λ=.25 / λ=.50 / source-known t5 oracle **17/32,26/32,28/32,27/32** for independent curves and **26/32,28/32,28/32,28/32** for repeated participants. All remaining source cases are preserved in the immutable archive.

## Figure 2: R79 Gaussian vs R80 Student-t5 sources

![R79 Gaussian and R80 heavy-tailed Student-t5 unpaired source experiment comparison](../assets/research/w3-r79-r80-separate-source-heavy-tail-comparison.svg)

This chart draws **unpaired separate-source** contrasts: R79 and R80 used different newly generated original datasets, so the counts are *not* source-paired treatment changes. Under two extreme high-noise predictor units, curves R79→R80 estimated HC3 3→5, λ=.25 19→19, λ=.50 24→23, simulator-known law 26→29; participants HC3 11→17, λ=.25 17→22, λ=.50 20→24, source-known law 27→28. The source-known reference also **changes law** from Gaussian to independent-unit Student-t5.

## Figure 3: estimated marginal scale and Gaussian reference criticals

![R80 original source-specific HC3 and regularized marginal standard-error lower tails and Gaussian maximum criticals](../assets/research/w3-r80-student-t5-se-tail-and-criticals.svg)

For the primary two-anchor predictor-dependent noise case, source means across each source-specific 10th percentile of estimated-to-*simulation-known true* slope marginal standard error and source-averaged estimated Gaussian maximum-statistic reference criticals:

| Source-averaged diagnostic | HC3 Gaussian | Frozen λ=.25 | Frozen λ=.50 |
|---|---:|---:|---:|
| Curves: lower-tail estimated/true SE | 0.425916 | 0.557491 | 0.626236 |
| Participants: lower-tail estimated/true SE | 0.492913 | 0.526406 | 0.547119 |
| Curves: estimated Gaussian 90% critical | 2.711679 | 2.950893 | 3.055342 |
| Participants: estimated Gaussian 90% critical | 2.248108 | 2.818882 | 2.999366 |

The **simulator-known Student-t5** maximum-statistic critical averages **3.322299** for independent curves and **2.456110** for repeated participants in the adverse condition. Directly comparing criticals without their different marginal SE scales or reference distributions is insufficient to assess coverage. The true SE ratio denominator and generating-tail parameters are **not available in actual sensor recordings**.

## Original immutable source and independently implemented audit

| Evidence contract | R80 verification |
|---|---|
| Prospective source protocol | [Draft R80 PR #414](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/414), frozen source seeds and methods before outcomes |
| Original source workflow | [R80 run #39487449656](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39487449656), **12/12 scientific jobs passed** |
| Immutable original source archive | [Artifact #12293409344](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39487449656/artifacts/12293409344) |
| Original source scientific checkout | c3c590788a8d126c73e59d7e0e799d6f39f0d655 |
| Independently implemented original-source audit | [Draft R80-A PR #415](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/415) |
| Independent original-archive audit | [R80-A run #39487811433](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39487811433), **4/4 dedicated audit jobs passed** |
| Separately retained independent audit report | [Artifact #12294940973](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39487811433/artifacts/12294940973) |
| Completed/attempted source cases | **256/256 complete, 0 refusals** |
| Independently generated primitive source blocks | **32 per design/support/variance condition**, paired across source conditions |
| Original conditional reference maximum values | **256 × 5 × 999 = 1,278,720**, all independently replayed |
| Generating innovation | **Independent-unit radial Student-t5**, one scaled chi-square factor shared across times, coordinates and participant trials |
| Conditional spatial-temporal Gaussian law | Trial AR1 rho .72, time-varying trial SD .04(.70+.60t), coordinate correlation q(t)=.15+.65t, participant shared latent coordinate correlation .45 |
| Known reference construction | **Unit-specific Student-t5 mixture conditional on original X and true unit scales**; not the earlier known-Gaussian reference |
| Candidate references | Original package wild-HC1, residual HC3 Gaussian and two frozen positive-definite covariance candidates λ=.25/.50 |
| Product release qualification | **None**. W3 #289/#296 open; stable release 1.1.0, protected-main inference code, unreleased 1.2 and PyPI unchanged |

Independent numerical agreement on source arrays, raw maxima, criticals, full-grid inclusion and SHA256 establishes reproducibility **for the specified synthetic data-generating design**. It does not establish general nominal-90% inference under other heavy-tailed families, skewed contamination, irregular or response-dependent missing data.

[Read the R80 research article](../articles/w3-student-t5-heavy-tail-inference-r80.md) · [Methods companion](../articles/independent-unit-student-t-functional-uncertainty.md) · [Previous R79 evidence ledger](w3-r79-nonseparable-covariance-evidence-ledger.md)
