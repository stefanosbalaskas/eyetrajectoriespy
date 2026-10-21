# W3 R86: original and independent third-stage failure audit evidence ledger

**Research-only numerically source-grounded evidence · 21 October 2026**

!!! danger "Synthetic randomized remeasurement; no real lost-gaze recovery or calibrated 90% bands"
    An audit of secondary validation failures is possible by construction of the complete-data generator, not demonstrated for actual eye-tracker dropout. Audit-fitted recovery relies on a two-parameter logistic source model and an originally visible-only mean pilot. The exact simulator oracle is not field-deployable. No functional uncertainty procedure or nominal-90% simultaneous band is validated. Issues #289/#296 OPEN; stable 1.1.0 unchanged; v1.2/PyPI RELEASE HOLD.

## Original immutable source and independent audit

| Contract | Source-verified evidence |
|---|---|
| Frozen prospective experiment | [Original R86 draft #434](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/434) |
| Original complete science | [R86 workflow #39639148930](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39639148930), **12/12 dedicated jobs PASS** |
| Frozen genuine original SHA256 source archive | [Artifact #12365391336](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39639148930/artifacts/12365391336) |
| Exact original synthetic source PR-merge checkout | 21a3d42045f56d810d273c83f7e2be645a20160c |
| Independently coded numerical audit | [R86-A draft #435](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/435) |
| Mandatory real original source replay | [R86-A workflow #39640120223](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39640120223), **4/4 dedicated independent jobs PASS** |
| Separate independent audit archive | [Artifact #12363264297](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39640120223/artifacts/12363264297) |
| Genuinely new independent primitive source blocks per fixed cell | **32** |
| Original complete full X/Y source-condition datasets | **256**, 2 native designs ×2 signed leverage supports ×2 source variances ×32 blocks |
| Paired first-stage MAR/MNAR source masks | **512** |
| Source/mask/audit/strategy analyses | **4,608**, NOT 4,608 independent generating datasets |
| Nested independently random audits of secondary failures | q=0, .25, .50 |
| Strategy at each audit level | Naïve union, audit-estimated secondary propensity, simulator-only union oracle |
| Original second-stage secondary recovery law | Outcome selective, true generating gamma=1.0 |
| Pilot and weighted likelihood | Original first-stage visible Y only; genuinely recovered Y, never unrecovered responses |
| Audit-estimated model without random audit | gamma=NULL and first-stage delta=NULL; **explicitly refused** |
| Release qualification | **No new public inference API, model or valid confidence band** |

R86 sources use entirely new RNG seed streams: complete source **202610218680**, original MAR/MNAR masks **202610218681**, secondary validator **202610218682**, third-stage independently randomized audit **202610218683**. The original science and independent audit independently reconstruct all source X/Y, mask, recovery/audit uniform and pilot SHA256 provenance. The first implementation uses Newton recovery estimation and bounded-bisection first-stage delta; the independent implementation uses SciPy multidimensional score-root recovery estimation and scalar Newton first-stage solving.

## Figure 1 — two-stage selection and the original MAR/MNAR controls

![R86 original and secondary audit first-stage fitted scalar delta](../assets/research/w3-r86-randomized-audit-first-stage-delta.svg)

*Figure 1.* Mean first-stage fitted original missingness selection delta in the two-signed-extreme predictor heteroskedastic source, n=32 new independent blocks per fixed cell.

| Original source | q | Naïve delta | Audit-estimated delta | Source-oracle delta | Mean secondary failures randomly audited |
|---|---:|---:|---:|---:|---:|
| Curves MAR, truth 0 | 0 | .656814 | Not estimated | −.020679 | 0 |
| Curves MAR, truth 0 | .25 | .290232 | −.001727 | −.003371 | 126.94 |
| Curves MAR, truth 0 | .50 | .138705 | .002581 | .000260 | 257.03 |
| Participants MAR, truth 0 | 0 | .667535 | Not estimated | .029368 | 0 |
| Participants MAR, truth 0 | .25 | .294295 | −.000635 | .007815 | 235.41 |
| Participants MAR, truth 0 | .50 | .135833 | −.003442 | .001171 | 466.47 |
| Curves MNAR, truth 1.1 | 0 | 1.634187 | Not estimated | 1.006621 | 0 |
| Curves MNAR, truth 1.1 | .25 | 1.311984 | 1.017014 | 1.018042 | 128.06 |
| Curves MNAR, truth 1.1 | .50 | 1.153701 | 1.008253 | 1.009885 | 259.78 |
| Participants MNAR, truth 1.1 | 0 | 1.581850 | Not estimated | .988961 | 0 |
| Participants MNAR, truth 1.1 | .25 | 1.268644 | .978588 | .985729 | 237.78 |
| Participants MNAR, truth 1.1 | .50 | 1.116702 | .974066 | .978082 | 473.34 |

Values are source means, not inferential bounds. These are counts of **time×coordinate×trial recovered measurements**, not additional independent participant sample sizes.

## Figure 2 — estimating the second-stage recovery selection coefficient

![R86 secondary recovery gamma from genuinely randomized audit failures](../assets/research/w3-r86-secondary-gamma-from-random-audit.svg)

*Figure 2.* True source gamma=1, 2-anchor heteroskedastic source, independently reproduced original source means.

| Original first-stage mechanism | Native independent design | Mean gamma at q=.25 | Mean gamma at q=.50 | Converged gamma fits at q=.25 |
|---|---|---:|---:|---:|
| MAR | Curves | .908009 | .893646 | 32/32 |
| MAR | Participants | .940566 | .943150 | 32/32 |
| MNAR | Curves | .898309 | .925818 | 32/32 |
| MNAR | Participants | .960633 | .967724 | 32/32 |

At zero audit the audit-estimated method refuses recovery coefficient estimation, so no source mean is presented. At positive q, source means differ from truth due to finite samples and pilot-model dependence. A weighted score solution is not evidence of a valid sampling covariance or interval.

## Figure 3 — all eight source cells, including unfavorable performance

![R86 eight source-cell original MNAR mean absolute selection errors](../assets/research/w3-r86-all-cell-delta-errors.svg)

*Figure 3.* First-stage original MNAR generating truth delta=1.1. Each value is a mean over 32 new independent source blocks; no cell excluded.

| Native design | Signed x=±4 units | Source variance | No audit/naïve mean abs delta error | 25% audit-fitted | 50% audit-fitted | 25% oracle |
|---|---:|---|---:|---:|---:|---:|
| Independent curves | 2 | Constant | 0.629035 | 0.121457 | 0.088877 | 0.105093 |
| Independent curves | 2 | Heteroskedastic | 0.534187 | 0.102905 | 0.114480 | 0.106203 |
| Independent curves | 16 | Constant | 0.595918 | 0.102577 | 0.091568 | 0.087810 |
| Independent curves | 16 | Heteroskedastic | 0.500302 | 0.131657 | 0.123811 | 0.116792 |
| Repeated participants | 2 | Constant | 0.563927 | 0.085897 | 0.073711 | 0.076877 |
| Repeated participants | 2 | Heteroskedastic | 0.481850 | 0.125260 | 0.128455 | 0.118695 |
| Repeated participants | 16 | Constant | 0.539972 | 0.097639 | 0.097752 | 0.092631 |
| Repeated participants | 16 | Heteroskedastic | 0.393785 | 0.189322 | 0.186767 | 0.180777 |

More randomized auditing adds genuinely measured outcomes, yet **source-mean absolute error does not improve monotonically in every cell**. In the adverse two-anchor heteroskedastic source, independent curves show .102905 at q=.25 versus .114480 at q=.50; participants show .125260 versus .128455. These are not confidence-interval coverage comparisons. The zero-audit naïve control also has a different weighting assumption from audit-fitted positive-q strategies.

## Scientific release decision

R86 independently reproduces the specified synthetic data-generating law and the information effect of a third-stage randomized audit among otherwise missing samples. It does not justify a claim that the secondary outcome-selection model, its measured failure set, or a historical lost eye-tracking response can be observed or recovered in practice. It does not identify a general MNAR law, validate first-stage functional slope inference, or resolve the original nominal-90% coverage blocker.

**Protected main estimator/API unchanged; stable eyetrajectoriespy 1.1.0 unchanged, scientific issues #289/#296 OPEN, eyetrajectoriespy 1.2/PyPI RELEASE HOLD.**

[Full R86 article](../articles/w3-random-audit-secondary-missingness-r86.md) · [Methods companion](../articles/random-audit-of-validation-failures.md) · [Prior R85 secondary-selection falsification](w3-r85-selection-validation-evidence-ledger.md)
