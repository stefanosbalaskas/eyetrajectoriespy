---
title: Sparse MFPCA comparator sensitivity
---

# Sparse MFPCA comparator sensitivity

PR E characterizes the native direct sparse MFPCA estimator against two
non-canonical comparator routes. This is sensitivity evidence, not an
equivalence or architecture-selection exercise.

## Internal two-stage marginal-basis benchmark

The benchmark fits native univariate sparse FPCA/PACE separately to x and y
using declared marginal ranks. The marginal score matrices are concatenated,

$$
Z_i =
[\xi^{(x)}_{i1},\ldots,\xi^{(x)}_{ir_x},
 \xi^{(y)}_{i1},\ldots,\xi^{(y)}_{ir_y}],
$$

their empirical covariance is diagonalized, and the resulting loading vectors
combine the marginal eigenfunctions into joint vector-valued functions.

This route is useful because it asks how much of the direct joint result can be
recovered after committing first to separate marginal bases. It is not the
canonical estimator and is never exposed through the public API.

The deterministic sensitivity fixture fixes rho_xy=0.6 and evaluates declared
marginal ranks 1 and 2. No automatic rank selection is performed. Evidence
retains:

- named covariance-block ISE against truth;
- joint functional-subspace principal cosines against truth;
- joint functional-subspace principal cosines against the direct estimator;
- score-subspace principal cosines against truth;
- score-subspace principal cosines against the direct estimator;
- latent reconstruction ISE;
- the fraction of curves with finite marginal-score systems.

Marginal-basis truncation can change the estimand represented by the two-stage
route. A smaller covariance or reconstruction error in one finite sample is not
interpreted as an architecture winner.

## External mGSFPCA sensitivity

The external comparator uses CRAN mGSFPCA version 0.2.2 and
`mGSFPCA::spMultFPCA()` on the same frozen irregular rho_xy=0.6 fixture used
by the native direct fit.

The package is installed only in the validation workflow and is not a runtime
scientific dependency. The frozen eyetrajectoriespy curve IDs remain unchanged;
the existing comparator-boundary adapter maps them to contiguous integer IDs
only for the R call and persists that mapping.

Rank and basis settings are explicit. Automatic model selection is not treated
as equivalent to the package contract.

The evaluator compares three invariant relationships:

1. native direct versus known truth;
2. mGSFPCA versus known truth;
3. mGSFPCA versus native direct.

For each relationship it reports functional-subspace and score-subspace
principal cosines. Raw component signs and implementation-specific
normalizations are not comparison targets.

## Interpretation boundary

The evidence explicitly records

```text
equivalence_claim = false
architecture_winner_selected = false
automatic_rank_selection = false
```

because sparse smoothing, marginal truncation, likelihood, basis construction,
normalization and score contracts are not identical across implementations.

PR E therefore answers:

> Are the main joint functional and score subspaces broadly compatible with
> reasonable internal and external comparator routes under a controlled common
> fixture, and how sensitive is the two-stage route to marginal truncation?

It does not answer whether one implementation is universally superior.

Observation-process stress and dedicated 0.12 performance evidence remain
separate downstream gates before a release-candidate decision.
