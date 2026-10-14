# R19 — original Gaussian primitive-innovation audit results

**Original science:** [run #38620150284](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38620150284), research commit `2538502d62c0e306ea875b522a96adc2b6155cfb`, [draft PR #320](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/320). Both original-source and primitive-contract jobs passed. **768/768 source/model cases completed; zero failures or missing.** All 16 original normal/t × continuous-truth/projection inclusion counts in the four R18 source-model cells matched the frozen original [R18 source](w3-r18-independent-gaussian-oracle-results.md) **exactly**.

The 192 source blocks are **not new in R19**: all observation sets and primitive Gaussian draws are reproduced with the original R18 seed `202610142621`. The twelve additional conditional Monte Carlo experiments are at three prespecified frozen source designs (blocks 0, 37, 191) crossed with the two covariance mechanisms and two bases, each with 1,024 *newly drawn conditional innovations*, not independent full-source blocks.

## 768 original-source primitive reconstruction checks

Each participant-specific intercept, slope, trial and sensor random innovation contributes with an independently reconstructed linear coefficient to the fitted WLS midpoint contrast. The realized sum must match the **original** fitted error about the design-weighted mean projection; its sum of squared coefficients must match the **original** known-Gaussian oracle variance.

| Original source mode | Mean basis | Original source blocks | Maximum error reconstruction delta | Maximum native residual delta | Maximum variance delta |
|---|---|---:|---:|---:|---:|
| ordinary_independent | legendre5 | 192 | 1.072e-15 | 1.069e-15 | 5.746e-18 |
| ordinary_independent | cubic_spline13 | 192 | 2.108e-15 | 2.121e-15 | 3.957e-18 |
| ordinary_dependent | legendre5 | 192 | 1.107e-15 | 1.107e-15 | 5.313e-18 |
| ordinary_dependent | cubic_spline13 | 192 | 1.873e-15 | 1.874e-15 | 3.415e-18 |

## Prespecified fixed-design conditional Gaussian checks

Each row is a *conditional* simulation at one frozen original n=96 design, comprising **1,024 new independent primitive Gaussian draws**. It cannot be pooled with the original 192 independent source blocks or across correlated bases/conditions to manufacture independent-source Monte Carlo confidence.

| Source mode | Basis | Frozen block | Std. error Z mean | Std. error Z SD | 90% normal inclusion /1024 |
|---|---|---:|---:|---:|---:|
| ordinary_independent | legendre5 | 0 | -0.016 | 0.997 | 927/1024 (90.5%) |
| ordinary_independent | legendre5 | 37 | 0.038 | 1.000 | 918/1024 (89.6%) |
| ordinary_independent | legendre5 | 191 | -0.006 | 0.975 | 923/1024 (90.1%) |
| ordinary_independent | cubic_spline13 | 0 | 0.023 | 1.031 | 907/1024 (88.6%) |
| ordinary_independent | cubic_spline13 | 37 | -0.002 | 0.973 | 937/1024 (91.5%) |
| ordinary_independent | cubic_spline13 | 191 | 0.003 | 1.011 | 918/1024 (89.6%) |
| ordinary_dependent | legendre5 | 0 | -0.049 | 1.000 | 925/1024 (90.3%) |
| ordinary_dependent | legendre5 | 37 | 0.069 | 0.994 | 922/1024 (90.0%) |
| ordinary_dependent | legendre5 | 191 | 0.023 | 0.977 | 930/1024 (90.8%) |
| ordinary_dependent | cubic_spline13 | 0 | 0.017 | 0.986 | 931/1024 (90.9%) |
| ordinary_dependent | cubic_spline13 | 37 | -0.029 | 0.996 | 923/1024 (90.1%) |
| ordinary_dependent | cubic_spline13 | 191 | -0.020 | 0.983 | 931/1024 (90.9%) |

## Interpretation and inferential boundary

Every original R18 fitted contrast error was reconstructed from *primitive* independent Gaussian innovations, with maximum realized contrast discrepancy below **2.2×10⁻¹⁵**. Every original known Gaussian covariance variance was reproduced as the sum of squared primitive innovation weights with maximum discrepancy below **5.8×10⁻¹⁸**. Across the 12 prespecified conditional simulations, standardized errors had SD in the range **0.973–1.031**. These observations independently corroborate the source implementation's algebra and the stipulated conditional Gaussian variance.

This finding **does not retroactively change** original R18 normal-oracle inclusion of 163/192 to 170/192 under the various cells, nor R17's original n=96 oracle results. The original standardized errors had higher empirical SD (roughly 1.075–1.090), which is now more plausibly a realized between-block Monte Carlo fluctuation or a feature of the deterministic between-seed sampling arrangement than a demonstrated primitive Gaussian covariance error. The limited fixed-design checks do not establish that these are the only possible explanations, and they do not test arbitrary source designs.

A further independent-source replication using an explicitly different seed-stream architecture, with predeclared n=96 ordinary cells, would be scientifically informative if the programme needs to characterize potential random-stream effects. It should not be designed or interpreted to retrospectively select which original source runs count. More important for production use, CR2 Satterthwaite with **estimated** (not simulation-known) working covariance and simultaneous functional intervals remain unqualified.

`original_R18_coverage_contract_all_four_cells_exact=true`, `inference_qualified=false`, `simultaneous_bands_qualified=false`, `production_release_ready=false`. Scientific blockers #289 and #296 stay open; no protected-main merge, public API promotion, release tag or PyPI publication.
