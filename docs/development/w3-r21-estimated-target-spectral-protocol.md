# W3 R21 — original 41 failed estimated-target cases: spectral diagnosis

Research-only, stacked on [R20 original feasibility draft PR #322](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/322). **The original 256-case scientific pilot failed** with **41 / 256** cases raising `ValueError: nonpositive or ill-conditioned working covariance`; all case records survive in the original [failure-inclusive artifact](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38641167528/artifacts/11931450211), and all three internal artifact SHA256 checks passed independently. Thirty-three failures occurred at 24 participants; eight at 48. This is an *original scientific result*, not CI noise.

## Predeclared same-source audit

Recreate all 256 native original study source cases using R20 pilot's original seed `202610150821`, the same independent source blocks, n, leverage and covariance modes, mean bases and candidate covariance nuisance families. Execute the **unchanged** R20 pilot inference evaluator to reproduce precisely the original 41 failing identities. The alphabetically sorted original failure-key checksum `a75ffbf14fb632ffa7ce18ad0203e25141c3ff9d83bbb676ecf6ac55dbc0010e` is a strict requirement; the source audit fails if any case is dropped or reclassified.

Using the same *observed-only* estimated covariance target, distinguish independently for every original participant block:

- minimum eigenvalue and scale of the estimated whitened within-person covariance `Φ_i`;
- minimum eigenvalue and scale of the CR2 residual covariance `D_i = [(I−H)Φ(I−H)ᵀ]ᵢᵢ`, calculated blockwise;
- minimum eigenvalue and scale of `Φ_i^(1/2) D_i Φ_i^(1/2)`, whose inverse square root enters the previously externally validated **symmetric** correlated-target CR2 adjustment.

Classify whether the failure is genuinely nonpositive, below the R16 reference's **absolute** `1e−11` eigenvalue threshold despite theoretical positivity, or remains unexplained. The audit records the original estimated variance components, nuisance moment condition number and sensor floor status. It does not alter the original estimator, original source, CR2 algebra, numerical threshold or simulation success/failed record.

**Scientific decision is not predetermined.** If numerically small but positive product eigenvalues explain all failures, an independently verified scale-invariant inverse square root might be investigated later with a new numerical qualification gate and unchanged original failed results. A genuinely nonpositive working target instead requires revisiting covariance model parameterization and estimator feasibility. Neither case justifies deleting 41 source cases, selecting a favorable covariance family after the pilot, reporting 90% coverage from successful cases alone, or releasing 1.2.

No public API, main merge, simultaneous inference claim, release tags or PyPI. Scientific issues #289/#296 remain open.
