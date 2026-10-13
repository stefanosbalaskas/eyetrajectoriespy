# W3 R14 — verified crossed variance and reference-quantile findings

!!! danger "Original numerical evidence, not calibrated interval inference"
    All **384/384** original R13 source/model cases recomputed successfully.
    The original R11 historical source counts reproduced exactly
    (**80/96** for Legendre-5; **77/96** for cubic spline-13).
    No simultaneous band or publicly supported new method has qualified.

## Original scientific source and provenance

The [R14 original workflow #38377157176](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38377157176)
completed all four research jobs, including numerical contracts for
Python 3.11, 3.12 and 3.13. Its
[original artifact 11802105183](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38377157176/artifacts/11802105183)
retains the original R13 source ledger and summary, R14 crossed
case ledger, scientific evidence JSON, Matplotlib SVG and source
commit identity. All **six SHA256 digests were independently verified**
against the downloaded artifact ZIP.

There are **192 independent generating blocks**: 96 original historical
R11 blocks and 96 independently generated fresh blocks of the identical
R11 data-generating process. Each block has 48 independent people and
two *paired*, fixed mean-basis analyses with genuinely asynchronous,
complete repeated trials. R14 did not create any new independent
source datasets. The four intervals within a fitted source/model case
all use the *same* slope estimate, participant records, timestamps
and numerical weights.

## Nominal 90% pointwise known-truth inclusion

Numbers are source blocks out of **96** containing the known midpoint
condition slope, first response dimension.

| Cohort / fixed basis | CR1 / normal | CR1 / t(47) | Known Gaussian / normal | Known Gaussian / t(47) |
|---|---:|---:|---:|---:|
| Historical R11 · Legendre-5 | 79/96 (82.3%) | **80/96 (83.3%)** | **85/96 (88.5%)** | 86/96 (89.6%) |
| Historical R11 · cubic spline-13 | 77/96 (80.2%) | **77/96 (80.2%)** | **81/96 (84.4%)** | 82/96 (85.4%) |
| Fresh R11-DGP · Legendre-5 | 81/96 (84.4%) | **81/96 (84.4%)** | **85/96 (88.5%)** | 85/96 (88.5%) |
| Fresh R11-DGP · cubic spline-13 | 82/96 (85.4%) | **82/96 (85.4%)** | **86/96 (89.6%)** | 86/96 (89.6%) |

The bold original R13 diagonal methods (CR1/t and
known-Gaussian/normal) exactly reproduce earlier reported interval
widths and truth inclusion for each original model/source case.

## Controlled decomposition

Holding the **variance source constant**, switching from normal to
t(47) reference moved the true-point inclusion count by just
**zero or one of 96** in each cohort and mean-basis comparison.
This is not mathematical equivalence: t(47) gives wider
intervals than normal for a fixed standard error.

Holding the **critical-value source constant**, switching from
participant CR1 to simulation-known Gaussian covariance increased
the inclusion count by **six of 96** for historical Legendre-5,
**four or five of 96** for historical spline, and **four of 96**
for each fresh cohort mean basis. Within the normal-reference
comparison, the paired 95% independent-block bootstrap interval
for the oracle-minus-CR1 inclusion difference was approximately
**+1.0 to +12.5 percentage points** for historical Legendre-5,
**0 to +9.4 points** for historical spline, and
**+1.0 to +8.3 points** for each fresh mean model.

The variance-by-critical inclusion interaction was zero in three
cohort/basis comparisons and **one of 96** in historical spline.
The original evidence JSON contains all per-block indicators,
mean interval widths, Wilson intervals and paired uncertainty
intervals. These results are descriptive finite-simulation
comparisons, not a general hypothesis test.

**Interpretation:** In this matched R13 generating study, the
variance-source change accounted for most of the *observed*
inclusion-count differences, rather than the changed t/normal
reference quantile. Since the known Gaussian source variance
requires unobservable generating parameters, this is
**not an available empirical correction** and establishes
no calibrated interval architecture or universal method winner.

## Remaining scientific boundaries

The results concern one **pointwise** midpoint condition-slope
contrast in simulated normalized gaze coordinates. R14 does not
establish nominal simultaneous whole-function bands, participant
random-effect fitting, latent-MNAR correction, family-wise
error control, inference under heteroscedasticity or real-device
sensor validity. A separately designed independent replication
and finite-cluster/leverage study remains useful.

[Protocol](w3-r14-variance-reference-factorial-protocol.md)
· [Original R13 findings](w3-r13-exact-r11-conditional-variance-results.md)
· [W3 inferential blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
· [Missingness blocker #296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296).

All code remains in a draft research branch. Stable 1.1.0 and
unreleased development 1.2.0rc2.dev0 are unchanged;
production release authorization remains false.
No root API promotion, tag, release candidate or PyPI publication.
