# 1.1 development readiness audit

This page records the R4 development-line readiness audit for `eyetrajectoriespy` 1.1. It is a **pre-RC evidence consolidation**, not an RC release record and not publication authorization.

## Decision snapshot

| Item | R4 result |
|---|---|
| Exact qualified protected-main commit | `1f9b80701ba4d10c97836277e18d8a16abe0038a` |
| Active source identity | `1.1.0.dev0` |
| Stable compatibility baseline | immutable `1.0.0` |
| Exact-main workflow groups | **24/24 successful** |
| R3 release-blocking friction | **0** |
| Publication readiness | disarmed |
| R4 recommendation | **`eligible_for_rc_decision=true`** |

The recommendation means that the integrated 1.1 development surface is sufficiently qualified to enter the separate R5 RC decision gate. It does **not** change the source version, create `1.1.0rc1`, arm GitHub/PyPI publication, or publish any artifact.

## Compatibility boundary

The frozen 1.0 compatibility manifest remains unchanged. `ONE_DOT_ZERO_API_STABILITY.json` still records 458 public exports, including 455 stable exports, three explicitly experimental exports and one compatibility export, with no authorized deprecations or removals. R1 deliberately kept the post-1.0 additions as supported module-scoped 1.1 APIs instead of mechanically expanding the frozen package-root namespace.

R4 does not mutate or relabel any frozen 1.0 validation or performance record. In particular, `PERFORMANCE_ENVELOPE.json` remains historical 1.0 evidence rather than being rewritten as 1.1 evidence.

## Integration tranches

### R1 — public-surface/API integration

R1 (#184 / PR #187) audited the combined A1-C1 public surface. The supported 1.1 additions remain module-scoped, result-object and reporting conventions are documented, and tests pin their deliberate absence from the frozen 1.0 root namespace. No estimator/default/version/publication change was introduced.

### R2 — documentation and release narrative

R2 (#188 / PR #194) reconciled README, roadmap, changelog and release/readiness documentation with the completed A1-C1 programme. Historical releases remain historical records, `1.1.0.dev0` remains the active source identity, and no RC decision was made.

### R3 — canonical product analyses

R3 (#189 / PR #195) exercised three coherent analysis routes using public supported APIs and deterministic realistic synthetic gaze rather than private qualification simulators:

- univariate sparse/irregular diagnostics → grouped bandwidth selection → sparse FPCA/PACE → conditional score uncertainty → future prediction → participant-aware split conformal calibration;
- paired planar bandwidth selection → sparse MFPCA/joint PACE → conditional joint-score uncertainty, plus a separate asynchronous coordinate-specific native-grid fit;
- sparse participant/trial multilevel FPCA with unequal trial counts and single-trial participants.

The first retained R3 run (`37437196381`) completed in 30.53 s with process max RSS 242,672 KiB, retained 51 evidence files, and recorded zero release-blocking friction. There were zero univariate PACE/uncertainty failures, zero paired or asynchronous joint-PACE failures and zero multilevel BLUP failures. The asynchronous fixture retained 259 x-only and 270 y-only timestamps without interpolation, nearest-neighbour synchronization or time binning.

## A1-C1 exact-main evidence

All method-specific validations were rerun successfully on exact protected main `1f9b80701ba4d10c97836277e18d8a16abe0038a`. R4 retains exact-main artifact identities rather than relying only on earlier feature-PR evidence.

| Tranche | Workflow | Exact-main run | Artifact | Digest |
|---|---|---:|---:|---|
| A1 conditional sparse-PACE score uncertainty | `sparse-score-uncertainty-validation` | `37439404000` | `11400607280` | `sha256:6e2ddfdf...deed1d` |
| A2 audited sparse-FPCA bandwidth selection | `sparse-bandwidth-selection-validation` | `37439403877` | `11400891283` | `sha256:1b461b47...84bf09` |
| A3 observation-process diagnostics | `observation-process-validation` | `37439404153` | `11400572196` | `sha256:ff2610c9...8b6e7` |
| A4 conditional joint-PACE uncertainty | `sparse-mfpca-score-uncertainty-validation` | `37439403814` | `11400981227` | `sha256:58c0780e...263331` |
| A5 audited sparse-MFPCA bandwidth selection | `sparse-mfpca-bandwidth-selection-validation` | `37439404011` | `11399819377` | `sha256:bd76e514...6c80f9` |
| B1 sparse participant/trial multilevel FPCA | `sparse-multilevel-validation` | `37439403996` | `11400961213` | `sha256:0434797b...a95aec` |
| B2 asynchronous coordinate-specific sparse MFPCA | `sparse-mfpca-async-validation` | `37439403973` | `11400966100` | `sha256:3c723d29...247031d` |
| C1 sparse partial prediction + conformal bands | `sparse-partial-prediction-validation` | `37439403942` | `11400661649` | `sha256:ad10e508...ef4bab` |

The complete digests and historical qualification identities are retained in `ONE_DOT_ONE_DEVELOPMENT_READINESS.json`.

## Exact-main repository matrix

The post-R3 protected-main commit ran the complete repository qualification matrix and finished **24/24 workflow groups successfully with zero failures**. The matrix included package build and the Ubuntu/macOS/Windows × Python 3.11-3.13 test/compile/Ruff lanes, strict docs and examples, release-readiness, package-wide performance, pre-0.12 recovery, sparse-native validation, A1-A5, B1, B2, C1, optional backends, functional-simulation validation/stress, product/reproducibility workflows, two-stage comparator sensitivity and the exact external `mGSFPCA` comparator.

Selected exact-main run identities retained for the RC decision are:

- tests: `37439404053`;
- examples: `37439403759`;
- docs: `37439403972`;
- release-readiness: `37439403832`;
- package-wide performance: `37439403915`;
- pre-0.12 recovery: `37439403977`;
- external comparator: `37439403893` (job `112189116488`).

The external comparator installed the exact `mGSFPCA` dependency, ran the comparator, evaluated invariant sensitivity, verified its evidence contract and uploaded the evidence successfully.

## Performance and product audit

No pathological runtime or peak-RSS growth was identified in the integrated 1.1 workflows at the qualified workloads. The exact-main package-wide performance gate passed, while the R3 canonical three-route product harness completed in about 30.5 s at about 237 MiB max RSS on its retained Ubuntu/Python 3.12 run.

Bandwidth cross-validation necessarily refits population models across declared candidates/folds, but this cost is **explicit and opt-in**: it is not hidden inside `fit_sparse_fpca()` or `fit_sparse_mfpca()`. R4 found no accidental repeated-refit path that silently changes the runtime contract of the canonical fitters.

R4 does not invent a new threshold merely to justify an RC and does not relabel the historical 1.0 performance envelope. A separate pre-RC 1.1 performance artifact is not required to make the R5 decision because current exact-main package/per-product evidence is non-pathological. If R5 approves `1.1.0rc1`, however, that literal RC identity must generate **fresh exact-version performance and qualification evidence** before it can be considered qualified.

## Retained non-blocking scope limits

The audit retains the following limitations rather than hiding them behind convenience behavior:

- asynchronous sparse-MFPCA bandwidths remain analyst-declared; there is no separately qualified asynchronous selector;
- sparse multilevel FPCA bandwidths remain analyst-declared; there is no dedicated multilevel selector;
- the first sparse multilevel tranche does not estimate fixed functional effects, which must be absent, stratified or handled upstream;
- sparse score/prediction uncertainty remains conditional on fitted population objects where documented rather than full population-estimation uncertainty;
- R3 is product/integration evidence from deterministic realistic synthetic gaze, not empirical human-data validation.

None of these limits contradicts the documented 1.1 estimands or creates a hidden compatibility failure. They therefore remain declared scope boundaries rather than R4 release blockers.

## R4 recommendation

**`eligible_for_rc_decision=true`**.

The reason is joint rather than checklist-only: A1-C1 remain qualified together on one exact protected-main snapshot; the 1.0 compatibility boundary is preserved; R1-R3 close the API, documentation and end-to-end product-integration gaps; the complete exact-main matrix is green; R3 found no release-blocking product friction; and the current performance evidence does not reveal a pathological integrated workload.

R5 remains a separate decision. If R5 approves an RC, the next tranche must be version-only, move active identity to `1.1.0rc1`, generate fresh literal-RC qualification/performance evidence, pass both PR and post-merge exact-main matrices, and keep publication readiness disarmed. Publication arming, if later approved, remains a separate governance-only change.
