# Targeted pre-0.12 recovery audit

Stable `0.11.0` provides the known-truth laboratory used here. This audit is
intentionally **short and decision-oriented**: it asks whether an existing
supported contract needs corrective work before a new methodological tranche.
It does not implement the planned 0.12 estimator.

## Four questions

### 1. Sparse FPCA/PACE under signal-dependent observation loss

The validation runner adds observation-process stress in which sample loss
depends on generated signal characteristics. Named mechanisms are:

- `signal_dependent_x_loss`;
- `signal_dependent_y_loss`;
- `eccentricity_dependent_loss`;
- `velocity_dependent_loss`;
- `phase_dependent_loss`;
- an MCAR comparator with the same target loss fraction.

These are **stress mechanisms, not estimator corrections**. The audit records
mean, covariance, marginal subspace, reconstruction, and score-failure
sensitivity. Masked curves remain on native irregular grids; they are not
silently interpolated before sparse FPCA/PACE fitting.

### 2. Joint versus separate planar structure

The audit varies `rho_xy` over `0, 0.3, 0.6, 0.9` using a separable
temporal/channel covariance construction. The crucial control is that the
marginal covariance of `x` and `y` is identical across all four conditions
while only the cross-channel covariance changes.

The current native sparse estimator is fitted separately to `x` and `y`.
Separate marginal recovery is therefore distinguished from first-class
representation of the cross-channel covariance block. The audit records the
fraction of true block-covariance energy contained in the cross-channel blocks.

### 3. Sparse repeated-trial hierarchy

The current functional mixed-effects API is a complete common-grid
`TrajectorySet` model. The audit generates participant/trial hierarchy under
increasingly sparse and unequal native schedules and tests that boundary
directly. Rejection of `IrregularTrajectorySet` input is retained as a
capability boundary; the audit does not interpolate sparse trials to
manufacture compatibility.

### 4. External sensitivity comparison

The audit exports a controlled `rho_xy=0.6` irregular planar fixture in long
form (`ID`, `time`, `value`) for independent implementations.

The primary comparator is [mGSFPCA](https://CRAN.R-project.org/package=mGSFPCA)
version 0.2.2 using `spMultFPCA()`. It is a cross-language sensitivity
reference, not a runtime dependency and not an exact-equivalence oracle.
Rank and basis candidates are fixed explicitly instead of using automatic
AIC/elbow selection.

mGSFPCA 0.2.2 expects numeric subject identifiers. The frozen
eyetrajectoriespy fixture therefore remains unchanged; the R comparator applies
a boundary-only mapping from original curve IDs to contiguous integer IDs,
persists that mapping as `mgsfpca_id_mapping.csv`, and exports scores back
under the original identifiers.

[MFPCA](https://CRAN.R-project.org/package=MFPCA) and
[bayesFPCA](https://github.com/hruffieux/bayesFPCA) remain secondary
sensitivity references. Bayesian sparse MFPCA is not being introduced as a
core subsystem in this tranche.

Comparator configuration is machine-readable in
`validation/pre012/EXTERNAL_COMPARATORS.json`; the explicit mGSFPCA runner is
`validation/pre012/run_mgsfpca.R`.

## Observed audit evidence

The final audit ran against stable `eyetrajectoriespy==0.11.0`. It did not
expose a result-changing or public-API defect inside an already supported 0.11
contract.

At an approximately 20% target loss fraction, every tested missingness
mechanism retained a zero PACE score-failure rate in this controlled audit.
Marginal functional subspace recovery remained high: the mean minimum principal
cosine ranged from about 0.976 to 0.995 across mechanisms and dimensions.
Sensitivity was nevertheless visible in other targets. In particular,
eccentricity-dependent loss increased covariance and reconstruction error
relative to the matched MCAR case. This is evidence that the observation
process belongs in sparse-functional sensitivity analysis; it is not evidence
that informative missingness should be silently reclassified as an 0.11
estimator defect.

The controlled planar experiment shows why separate sparse `x` and `y`
fits are not an adequate endpoint for planar gaze. While marginal covariance is
held fixed, the fraction of total block-covariance energy carried by the
cross-channel blocks rises from effectively zero at `rho_xy=0` to about
0.083, 0.265, and 0.448 at `rho_xy=0.3, 0.6, 0.9`, respectively. The
corresponding mean absolute same-time correlation is approximately
0, 0.294, 0.588, and 0.882. Those changes are genuine joint structure that
cannot appear in two independent univariate result objects.

The sparse repeated-trial audit also confirms the current boundary rather than
revealing a regression: very sparse (8-12 observations/curve), moderately
sparse (14-20), and less sparse (24-32) unequal trial schedules are all rejected
by the complete-grid functional mixed-effects API without silent interpolation.

The independent mGSFPCA 0.2.2 run on the `rho_xy=0.6` fixture completed
successfully. Its four joint functional-subspace principal cosines were
approximately `0.9982, 0.9965, 0.9891, 0.8914`; its score-subspace cosines
were approximately `0.99986, 0.99946, 0.99590, 0.98372`. Estimated
eigenvalues differ from the frozen truth because the implementations use
different smoothing, basis, normalization, likelihood, truncation, and score
contracts, so this remains sensitivity evidence rather than an
exact-equivalence claim.

## 0.12 architecture decision

The audit clears the way for the next methodological tranche. The canonical
0.12 target is **native sparse multivariate FPCA for planar gaze**, not another
pair of univariate sparse fits.

The primary architecture should estimate a genuine joint block covariance
operator,

```text
C(s,t) = [[C_xx(s,t), C_xy(s,t)],
          [C_yx(s,t), C_yy(s,t)]]
```

on sparse/irregular observations and derive one joint eigensystem and one
conditional score system from that operator. Cross-channel measurement-error
assumptions must be explicit, and the implementation must retain the
observation-process and recovery provenance introduced in 0.11.

A two-stage construction based on univariate sparse bases followed by a joint
score covariance remains useful as an internal benchmark and sensitivity
implementation. It should not become the canonical estimator merely because it
is easier to compose: the audit was designed precisely to show that
cross-channel covariance is a first-class estimand.

Sparse participant/trial functional decomposition remains subsequent work. It
should not be folded into 0.12 until the sparse joint planar estimator has its
own recovery and external-sensitivity evidence.

## Reproducible outputs

Run:

```bash
python scripts/run_pre012_recovery_audit.py --output-dir pre012-audit
```

The output directory contains:

- `signal_dependent_missingness.csv`;
- `cross_channel_truth.csv`;
- `sparse_hierarchy_boundary.csv`;
- `external_fixture_x.csv` and `external_fixture_y.csv`;
- `external_fixture_truth.json`;
- `pre012_audit_summary.json`.

Then, in an R environment with exactly mGSFPCA 0.2.2 installed:

```bash
Rscript validation/pre012/run_mgsfpca.R pre012-audit
```

The external comparator additionally writes the persisted ID mapping,
eigenvalues, joint scores, per-dimension eigenfunction representations, run
metadata, and `mgsfpca_sensitivity.json`.

## Decision contract

The audit can block new methodology if it uncovers a result-changing or
public-API defect inside an already supported 0.11 contract.

The following findings do not, by themselves, constitute an 0.11 defect:

- sensitivity when observation loss is explicitly informative;
- non-zero cross-channel covariance omitted by separate univariate result objects;
- fail-closed rejection of irregular trials by the complete-grid mixed-effects API.

No such supported-contract blocker emerged here. The next development tranche
may therefore open the native sparse multivariate planar estimator, using the
direct block-covariance route as the canonical design and retaining the
two-stage route as a benchmark/sensitivity comparator.
