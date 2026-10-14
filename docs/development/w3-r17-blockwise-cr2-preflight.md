# W3 R17 — blockwise CR2 and conditional Satterthwaite preflight

**Research-only preflight**, stacked on the corrected R16 external-reference PR #314, without any public API modification, merge to protected main, publication or release candidate promotion.

The old dense R16 CR2/Satterthwaite code assembles the whole N×N residual-maker matrix, making it unsuitable for larger asynchronous source recordings. The new R17 reference instead uses within-cluster matrices and participant-level Gram terms only. With whitened Zᵢ, G=ΣZᵢᵀZᵢ, B=G⁻¹ and specified within-cluster Φᵢ, define M=ΣZᵢᵀΦᵢZᵢ. Then

Dᵢ=Φᵢ−HᵢᵢΦᵢ−ΦᵢHᵢᵢ+Zᵢ B M B Zᵢᵀ, Hᵢᵢ=ZᵢBZᵢᵀ.

Aᵢ=Φᵢ^(1/2)(Φᵢ^(1/2)DᵢΦᵢ^(1/2))^(−1/2)Φᵢ^(1/2) is the symmetric CR2 adjustment. For the focal contrast c, let gᵢ=AᵢZᵢBc, aᵢ=Zᵢᵀgᵢ, bᵢ=ZᵢᵀΦᵢgᵢ and dᵢ=gᵢᵀΦᵢgᵢ. Form participant-level C=diag(d)−aBbᵀ−bBaᵀ+aBMBaᵀ. The conditional Gaussian moment-matched Satterthwaite df is tr(C)²/tr(C²). No full N×N matrix is needed.

The prespecified tests require agreement with the **existing dense, externally compared** R16 estimators across identity and correlated targets, balanced and unbalanced cluster sizes, arbitrary positive WLS weights and two fixed contrasts. They require small covariance-identity and symmetry errors and an internal expected-variance equality. A failed case is a failed preflight, never dropped or declared qualified. This is only numerical computation; the specified covariance target is not estimated from empirical data.

The **next independent R17 scientific stage** must use freshly seeded independent generating blocks and prespecified sample sizes, leverage and predictor-dependent covariance cells; paired comparison of CR1/t(G−1), CR2/t(G−1), CR2/Satterthwaite, delete-participant CV3J and the simulation-known oracle; and correctly specified vs deliberately misspecified working targets. Results must include missing/failure counts and independent-block uncertainty intervals. There is no basis to qualify simultaneous bands from a pointwise pilot.

Science issues #289 and #296 remain open and stable 1.1.0 remains the released package.
