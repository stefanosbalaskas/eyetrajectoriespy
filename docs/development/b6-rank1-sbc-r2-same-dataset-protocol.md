# B6 rank-one SBC R2: targeted stage-0 replicate-one refit

**Research draft; not independent calibration evidence.** This study reuses exactly
the original prior-generated dataset from the corrected stage-0 run
[#38087405506](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38087405506),
replicate 1, original artifact `11683660208`. The generating seed comes from the
unchanged stage-0 seed function. The NUTS initialization seed offset is
unchanged. The sampling budget increases from four chains × 700 tuning + 400
retained draws to four chains × **1,200 tuning + 800 retained draws**.

The purpose is **diagnostic**: investigate the original worst identified
R-hat of **1.0158**, minimum bulk ESS approximately **543**, and zero divergences,
not to select or reweight SBC replicates. Keep both original and longer-budget
diagnostics visible, including whether the prespecified R-hat ≤1.01, bulk and
tail ESS ≥400, BFMI ≥0.3 and zero-divergence checks are satisfied on all
identified population functionals.

Three outcomes are reported **separately**: (1) fitting exceptions and
all-attempt computational-screen success; (2) conditional interval inclusion
among adequately mixed fits; (3) end-to-end screen-and-interval inclusion
among *all attempts*. A rechecked dataset is not a new independent replication,
and its ranks must not be appended to an SBC histogram as if independent.

The code persists `case.json`, `reliability.json`, `evidence.json` and
`SHA256SUMS` even if an exception occurs. All mathematical and statistical
qualification flags remain false. Larger genuinely independent-data SBC studies
require a separately prespecified design and compute budget. Protected main,
stable 1.1.0 and 1.2 release authorization remain untouched.
