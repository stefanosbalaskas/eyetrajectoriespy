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

## Reporting and science qualification

Until R67's actual original-data job succeeds, **do not claim a particular failed pseudodraw index, optimizer family or numerical mechanism**. Engineering-green synthetic fixture tests cannot substitute for inspecting the real original artifact.

The purpose is to select an explicit prospective numerical sensitivity experiment only **after identifying** the original failure types, without retrospective reinterpretation or repair of R66 itself. Do not turn the R67 diagnostic into a change in the preregistered primary R66 inference, or use it to certify 5% Type I calibration / correct-size power or fitted 90% CR2 pointwise/simultaneous confidence coverage.

Scientific blockers #289 (undercovering function-wide bands) and #296 (response-dependent gaze loss) remain OPEN; protected main, stable 1.1.0, unreleased 1.2, tags and PyPI remain untouched.
