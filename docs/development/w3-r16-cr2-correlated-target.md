# R16 correlated-working-target CR2 — numerical research only

The working-identity CR2 implementation previously matched R `clubSandwich` numerically, but that target is not the true within-person covariance of R16. This tranche implements a general block-diagonal **specified** working covariance in whitened weighted-observation space, without estimating source covariance from data.

For a fixed WLS estimator, with `Z = sqrt(W) X`, `H=Z(ZᵀZ)⁻¹Zᵀ` and block diagonal specified target `Φ`, participant i's residual target is `Dᵢ=[(I−H)Φ(I−H)ᵀ]ᵢᵢ`. The adjustment `Aᵢ=Φᵢ^(1/2) [Φᵢ^(1/2)DᵢΦᵢ^(1/2)]^(-1/2)Φᵢ^(1/2)` satisfies the covariance identity `AᵢDᵢAᵢᵀ=Φᵢ`. Covariance is the sum of adjusted participant scores through the WLS bread.

Numerical tests require (a) agreement with the separately tested identity CR2 when all covariance blocks equal identity, (b) covariance adjustment identity under compound-symmetry correlation, (c) heterogeneous positive-definite target matrices and WLS weights and (d) rejection of singular/malformed targets.

This is **not** yet independent external `clubSandwich` validation for a correlated working target. Neither a fitted/random-effects target estimator nor coefficient-specific reference df has been implemented, and no coverage result or public production estimator is claimed. Dense per-cluster matrices are a numerical research reference, not a memory-scalable native asynchronous gaze method. Research PR stacked only; version 1.2 unreleased, no tag, main merge or PyPI publication.


## R16 external validation corrections (PR #314)

The first expanded R comparison failed on three correlated-target fixtures while two identity-target fixtures agreed. Two distinct methodological differences were identified:

1. The originally implemented Python factor satisfied `Aᵢ Dᵢ Aᵢᵀ = Φᵢ` but was nonsymmetric for a correlated `Φᵢ`. The implementation now uses the canonical symmetric positive-definite CR2 factor, and symmetry is regression-tested.
2. The original R comparison supplied `inverse_var=TRUE` with unweighted `lm()` and a **non-identity** within-person target. This setting activates R's inverse-variance-specific shortcut, although the fitted weights do not equal the inverse specified target covariance. The independent comparison has been changed to `inverse_var=FALSE`, so the R adjustment uses the full residual covariance under the declared target. The original shortcut is appropriate for an actual inverse-variance fit, not this unweighted correlated-target fixture.

The individual contribution of these differences to the prior numerical discrepancy is not established until a fresh exact-head external validation completes. All frozen data designs, coefficient contrasts and numeric tolerances are unchanged, and the historical failed run remains available. No pointwise or simultaneous calibration has been established.
