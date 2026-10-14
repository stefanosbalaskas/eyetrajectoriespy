# W3 R21 — original 41-case estimated-target spectral audit results

**Original scientific evidence:** [draft PR #323](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/323), [GitHub Actions science run #38641949525](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38641949525), fixed original R20 generating seed `202610150821`. Both numerical-contract and original-source spectral jobs passed. The 256-case source ledger was reproduced **exactly**: 215 cases remain original successes, **41 remain original failures**, zero cases discarded or relabeled. The original failure-key SHA256 `a75ffbf14fb632ffa7ce18ad0203e25141c3ff9d83bbb676ecf6ac55dbc0010e` matches the replayed source identifiers.

The [R21 audit artifact](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38641949525/artifacts/11930029213) retains the full 256-case original-source replay, spectral-case ledger, original failure status, run checkout SHA and checksum manifest. All **four** original audit files independently match their SHA256SUMS checksums. The original R20 pilot remains scientifically **failed** at 215/256 successful evaluations, as documented in [its original result page](w3-r20-estimated-target-pilot-original-failures.md).

## Frozen-case mechanism classification

A separate diagnostic calculates the eigen spectra of the **estimated** whitened within-participant covariance `Φ_i`, the Gaussian CR2 residual covariance `D_i` and the symmetric CR2 product `Φ_i^(1/2)D_iΦ_i^(1/2)`. The original estimator and its absolute `1e−11` matrix-inverse-square-root tolerance were not changed.

| Original case classification | Number | Estimated Φ minimum eigenvalue | Residual D minimum eigenvalue | CR2 product minimum eigenvalue | Sensor floor |
|---|---:|---:|---:|---:|---:|
| Reference eigenspectrum above tolerance; original success | **215** | 3.44×10⁻⁶ to 2.45×10⁻⁵ | 2.90×10⁻⁶ to 2.33×10⁻⁵ | 1.16×10⁻¹¹ to 5.50×10⁻¹⁰ | 0 |
| Positive product eigenvalues **below absolute tolerance**; original failures | **9** | 1.51×10⁻⁷ to 3.06×10⁻⁶ | 1.51×10⁻⁷ to 2.58×10⁻⁶ | 2.27×10⁻¹⁴ to 9.20×10⁻¹² | 0 |
| Computed product eigenvalues slightly negative despite positive Φ and D; original failures | **32** | ~2.00×10⁻¹⁰ | ~2.00×10⁻¹⁰ | −2.78×10⁻¹⁹ to −2.05×10⁻²⁰ | 32 |

### Scientific interpretation

All 41 failure cases had **positive minimum eigenvalues of both Φ_i and D_i**. The 32 most severely conditioned cases used the expressly flagged sensor-floor intervention (estimated sensor variance approximately 1.86×10⁻⁸ in affected n=24 examples). The product of two poorly conditioned covariance operators loses numerical relative accuracy at that scale: slightly negative floating-point product eigenvalues here **do not establish negative true covariance**. The remaining nine cases were positive throughout but rejected by the implementation's **absolute** tolerance.

This classification shows that the original 41 failures originate from the *reference numerical inverse-square-root requirement* on the product matrix; it does **not** demonstrate that a simple lower tolerance is adequate. The 32 floor cases have extremely small eigenvalues that may be below reliable double-precision relative resolution once the product is formed. The variance-component estimator also reaches a boundary in some source blocks, which is itself a meaningful statistical nuisance-estimation warning. Neither mathematical positivity of Φ and D nor passing an eigen threshold guarantees stable coefficient-specific Satterthwaite degrees of freedom.

## Required next numerical qualification

If development continues, isolate a **new** numerically stable CR2 adjustment implementation rather than modifying the original reference or source data. It should use documented scaling or higher-precision dense numerical oracle checks, require agreement with the independently implemented **R clubSandwich** under well-conditioned correlated targets, and prespecify how near-boundary solutions are flagged or rejected. The original 41 failures stay failures in the original R20 feasibility ledger. Do **not** call the repaired implementation scientifically calibrated merely because it can compute a number for formerly failed cases.

Next separately seeded inferential studies still need nuisance-estimation uncertainty, component identifiability and coverage with **estimated** working covariance, potentially multiple trial counts and real physiological source structures, and ultimately simultaneous functional bands. Issues #289 and #296 remain open, public API and protected main untouched, no version 1.2 release tag or PyPI upload.

`original_failed_case_count=41`; `failure_reproduced_exactly=true`; `spectral_audit_complete=true`; `estimated_target_coverage_qualified=false`; `numerical_repair_qualified=false`; `simultaneous_bands_qualified=false`; `release_authorized=false`.
