# Independent-reference validation ledger

Version 0.56 distinguishes three evidence strengths. They are not interchangeable
and are never collapsed into a generic statement that a method is simply
"validated".

The machine-readable ledger is `REFERENCE_VALIDATION.json`.

## Evidence types

**Analytical truth**  
A small declared problem with an exact or hand-computable scientific answer.

**Independent implementation equivalence**  
The same estimand/specification is fitted or represented independently from the
package code path. Agreement is assessed only after parameterization and
normalization are matched.

**Simulation recovery**  
Data are generated from known parameters and recovery is assessed under a
finite stochastic sample. This is useful scientific evidence but weaker than an
exact truth or independent-equivalence case.

**Cross-implementation sensitivity**  
Two implementations address closely related scientific quantities, but their
smoothing, discretization, covariance, scoring, or other contracts cannot be
made identical. Comparisons use invariant quantities and broad predeclared
guards, and must not be described as equivalence.

## Qualified 0.56 reference cases

| Method | Scientific quantity | Reference type | Reference | CI gate |
|---|---|---|---|---|
| FPCA | leading eigenvalue, functional subspace, rank-one reconstruction | analytical truth | hand-derived unit-norm rank-one process | `test_reference_fpca_rank_one_analytical_truth` |
| Gaussian functional mixed effects | fixed basis coefficients, random covariance, residual scale, log likelihood | independent implementation equivalence | independently assembled stacked `statsmodels.MixedLM` | `test_reference_mixed_effects_matches_independent_stacked_mixedlm` |
| Poisson exposure GEE | coefficients, robust covariance, rate, expected count | independent implementation equivalence | independently assembled direct `statsmodels.GEE` | `test_reference_poisson_exposure_matches_direct_stacked_gee` |
| Grouped-binomial GEE | coefficients and robust covariance | independent implementation equivalence | row-expanded Bernoulli GEE | `test_grouped_binomial_matches_row_expanded_bernoulli_reference` |
| Discrete Fréchet | bottleneck distance/coupling | analytical truth | hand-computable 3-point vs 2-point path | `test_reference_frechet_and_dtw_have_hand_computable_optima` |
| DTW | symmetric1/symmetric2 raw and normalized cost | analytical truth | hand-computable 3-point vs 2-point path | `test_reference_frechet_and_dtw_have_hand_computable_optima` |
| RQA | RR, DET, line lengths, entropy, LAM, line counts | analytical truth | hand-constructed recurrence matrix | `test_reference_rqa_matches_hand_counted_cross_recurrence` |
| Discrete TE | plug-in TE and local contributions | analytical truth | independently enumerated contingency counts | `test_reference_transfer_entropy_matches_exact_contingency_calculation` |

The ledger also records selected existing **simulation-recovery** evidence for
mixed effects and Poisson generalized FoSR. Those rows remain labeled as
simulation recovery rather than being promoted to stronger evidence.


## Native sparse FPCA/PACE evidence

The 0.10 development branch adds four deliberately distinct rows:

| Method | Scientific quantity | Reference type | Reference |
|---|---|---|---|
| Native sparse weighted eigensolver | eigenvalues, weighted subspace, orthonormality | analytical truth | constructed rank-two weighted covariance operator |
| Native sparse FPCA + PACE | subspace and conditional scores | simulation recovery | known-truth irregular two-component generator |
| Pooled local-linear mean smoother | fitted mean values | independent implementation equivalence | FDApy 1.0.x `LocalPolynomial` with matched degree/kernel/bandwidth |
| Whole sparse estimator | eigenstructure and score association | cross-implementation sensitivity | FDApy 1.0.x UFPCA/PACE |

The FDApy whole-estimator row is explicitly not equivalence. FDApy and the
native implementation differ in 2-D kernel geometry, noise handling, irregular
PACE interpolation, and the covariance object used in conditional scoring.
See [native sparse FPCA/PACE validation](sparse-fpca-validation.md).

## Native sparse multivariate FPCA/PACE evidence

PR D adds one simulation-recovery row for the direct planar estimator:

| Method | Scientific quantity | Reference type | Reference |
|---|---|---|---|
| Native sparse MFPCA + joint PACE | vector mean, named covariance blocks, joint eigenspace, separated and tied score recovery, reconstruction | simulation recovery | deterministic irregular planar truth over five rho values plus asymmetric-Cxy and correlated-noise cases |

The tied rho=0 truth is assessed as an eigenspace rather than by arbitrary
component identity. Covariance recovery is assessed through named Cxx/Cxy/Cyx/Cyy
blocks, avoiding storage-order ambiguity. The true measurement-error matrix is
supplied to the estimator and is therefore an input-contract check rather than
an estimated-noise recovery result.

This row does not replace the still-separate two-stage and mGSFPCA
cross-implementation sensitivity evidence. See
[native sparse MFPCA recovery validation](sparse-mfpca-recovery.md).

## Interpretation boundaries

The mixed-effects reference deliberately uses the same established statsmodels
backend but an independently assembled stacked design. It therefore validates
the package's functional-to-stacked model construction and returned covariance
semantics; it is not evidence that statsmodels itself is independently correct.

Likewise, the Poisson exposure comparison validates the package's construction
of the exposure-adjusted marginal GEE against a direct backend formulation.

For FPCA, sign is not a scientific invariant. The analytical test checks the
absolute weighted alignment to the known rank-one subspace and exact
reconstruction instead of requiring an arbitrary component sign.

For RQA and TE, small exact constructions are preferred over matching a
black-box package because software conventions can differ materially.

## Required fields for future rows

Every future ledger entry must include:

`method`, `scientific_quantity`, `reference_source`, `reference_type`,
`dataset_problem`, `expected_result`, `comparison_metric`, `tolerance`,
`platforms`, `status`, `limitations`, and the enforcing `ci_test`.

The numerical policy is documented separately in
[numerical tolerance policy](numerical-tolerance-policy.md).
