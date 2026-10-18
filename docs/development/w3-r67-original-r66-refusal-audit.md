# W3 R67 — read-only numerical refusal provenance for completed R66

**Research-only diagnostic of the immutable ORIGINAL R66 archive. No new sources, Gaussian draws, covariance fits, acceptance-rule changes, confidence interval recovery or public API.**

## Original evidence and scientific motivation

R66 [original science workflow #39162296955](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39162296955) passed all **36/36 dedicated jobs** and general original CI 25/25, producing [the complete original archive #12153256485](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39162296955/artifacts/12153256485). The original merged research checkout was `6e462b2b59609327f15c76b838c1743c20f20f9a`. The separate required [independent R66-A numerical archive audit #39176110530](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39176110530) passed **4/4**, publishing [independent original evidence #12153768854](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39176110530/artifacts/12153768854).

The original experiment used **128 NEW independent primitive Gaussian blocks**, each contributing six matched leverage×true structural slope rows: **768 source cases**, 48,384 planned/recorded fully nuisance-refitted H0 pseudodraw nested-fit slots and 294,912 original optimizer starts. **All 768 original nested source models were accepted, but two conditional bootstrap pseudodraw nested fits refused**, across two independent primitive generating blocks in distinct extreme-leverage half/full structural slope cells. This left **126/128 six-cell blocks fully complete**.

The prospectively chosen extreme-minus-ordinary zero→full change in candidate rejection among 126 complete blocks was +14/126 = +11.111 percentage points, with conservative refusal-inclusive bounds +7.8125 to +14.0625 points across 128 blocks. The prospectively required 20,000 whole-block percentile confidence interval was **withheld**. Positive partial-identification bounds are **not a confidence interval**.

## R67 objective and frozen source

Rather than quietly dropping/refitting those two failures or selecting a new inference rule after the fact, this follow-up extracts **their original numerical provenance**:

- exact source block, support, structural slope level and conditional H0 pseudodraw index/seed;
- original nested H0/H1 status, original optimizer-start labels/status/success, physical-coordinate KKT and objective reconstruction errors;
- archived source/draw exception messages if any, and whether refusal occurred in H0, H1, both, nested likelihood comparison or source exception;
- independent full 768-case grid, 48,384-draw and 48,382-accepted-draw count, 3/3 archive SHA256 checks and exact frozen original source commit; 
- confirmation that original incomplete block statuses and the prospective null bootstrap interval remain **unchanged**.

This is a *post-hoc diagnostic classification*, not a predeclared inferential test. Archive classifications are limited to recorded optimizer provenance and **cannot establish the unarchived participant-level Gaussian innovations or cause of optimizer failure beyond the stored evidence**.

Implementation `scripts/audit_w3_r67_original_r66_refusal_provenance.py` imports **only the separately implemented R66-A numerical auditor**, not original R66 generator, REML optimizer or simulation aggregate. A dedicated workflow requires independent R66-A to re-pass on the immutable original artifact before analyzing the two recorded refusals. Three cross-Python contract jobs ensure tampering, source omission, duplicate cases, improperly accepted draws, absent original source verification or fabricated recovered primary CI cannot silently pass.

## Executed immutable original-data provenance findings — PASS

The complete original archive was independently re-audited and the two numerically refused conditional draws classified in [R67 exact-head scientific workflow #39176779324](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39176779324), **4/4 dedicated jobs PASSED** (three Python 3.11/3.12/3.13 refusal integrity contracts plus required read-only original-data job). The [separately archived R67 diagnostic artifact #12154667932](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39176779324/artifacts/12154667932) stores the exact original H0/H1 multistart negative likelihoods, physical KKT diagnostics, draw seeds and original failure statuses. Original SHA256/checkout and 48,384/48,382 planned/accepted draw positions were reverified. Neither was a caught Python exception.

| Immutable primitive generating block | Predictor support | True structural slope | Conditional draw index (0-based) | Independent classification |
|---|---|---|---:|---|
| **7** | extreme dependent | half (variance 0.00050625) | **47** | **H0 accepted; H1 refused because the best raw-objective optimizer start was not KKT eligible, while eligible alternatives were too far above that minimum** |
| **66** | extreme dependent | full (variance 0.002025) | **61** | **H0/H1 individual fits accepted; raw nested likelihood deviance was negative beyond the frozen admissibility tolerance** |

### Block 7 — optimizer multistart disagreement, not a Python crash

All four original H1 multistart attempts reported optimizer success and had reconstructed objective errors zero, but one `alt_tiny_positive` start produced the lowest observed H1 negative log likelihood **−6724.8863645173105** and physical projected KKT **8.961450901186097**, very far above the frozen **0.001** admissibility threshold. Other H1 starts had small KKT residuals, e.g. `alt_at_exact_zero` KKT **3.7945e−6** and objective **−6724.8804114785735**. The raw-objective gap between the KKT-eligible solution and best nonstationary observed start was **0.0059530387**, exceeding the frozen **0.001** multistart objective proximity requirement. Therefore the original H1 was **correctly refused under its frozen numerical acceptance contract**, despite all four starts individually reporting optimizer success. H0 was accepted (selected KKT ~**1.4483e−5**). No alternative start was substituted retrospectively.

### Block 66 — negative nested likelihood contrast, despite individually accepted models

The original H0 and H1 optimizations were both individually accepted, with selected physical projected KKT residuals **1.0942e−7** (H0) and **8.0100e−6** (H1). However, their recorded selected negative log likelihoods were H0 **−5848.97655716093** and H1 **−5848.974463772949**. The H1 objective was **worse** than the nested exact-zero H0 by ~**0.00209339**, yielding a raw likelihood-ratio deviance of **−0.004186775960988598**, which is less than the frozen lower admissible nested-deviance tolerance **−0.00001**. The original nested comparison was correctly **refused**, rather than clipping away that material nesting discrepancy. No numerical result was silently changed.

These two patterns are **different**: one is multistart objective-versus-KKT incongruity, and the other is violated numerical nestedness. They do not license a higher tolerance, unilateral refit, dropping a source, relaxing failure-inclusive bounds or retrospectively recovering the withheld prospective matched-block percentile interval. The original 128 blocks and their 768 matched cases are preserved without substitution.

**R67 is diagnosis only.** The independent source data record supports these numerical classifications, not a guarantee about why the algorithms encountered the landscapes, true optimizer global optimality, calibrated hypothesis-test power, or fitted-CR2 confidence coverage.

## Reporting and science qualification

Until R67's actual original-data job succeeds, **do not claim a particular failed pseudodraw index, optimizer family or numerical mechanism**. Engineering-green synthetic fixture tests cannot substitute for inspecting the real original artifact.

The purpose is to select an explicit prospective numerical sensitivity experiment only **after identifying** the original failure types, without retrospective reinterpretation or repair of R66 itself. Do not turn the R67 diagnostic into a change in the preregistered primary R66 inference, or use it to certify 5% Type I calibration / correct-size power or fitted 90% CR2 pointwise/simultaneous confidence coverage.

Scientific blockers #289 (undercovering function-wide bands) and #296 (response-dependent gaze loss) remain OPEN; protected main, stable 1.1.0, unreleased 1.2, tags and PyPI remain untouched.
