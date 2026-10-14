# W3 R20 — original estimated-target feasibility pilot: failure-inclusive results

**Original-source evidence:** [GitHub Actions run #38641167528](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38641167528) for [draft PR #322](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/322), research head `1b4d250be7fc0b08f8c454ea2b9456a1954fa9e6`. The archived source-commit.txt reports GitHub's pull-request **merge-checkout SHA** `a3b1a6aa6551f6566f35383f63b908495f6f04fe`, distinct from the research branch head. Do not conflate them.

This is the first unmodified original-source execution of the **256 prespecified paired model cases**, based on **8 independently seeded source blocks**, with n=24 and n=48. The scientific workflow appropriately returned a **failure** because **41 of 256 cases were not evaluable**. The summary and original case ledger were retained in artifact [`w3-r20-estimated-target-original-pilot`](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38641167528/artifacts/11931450211), which includes the three source files and a SHA256SUMS manifest. Original artifact checksums were independently verified: all 3 files match their recorded SHA256. No source simulation observations were discarded or regenerated.

| Original-source classification | Count |
|---|---:|
| Prespecified model/working-target cases | 256 |
| Successfully evaluated | 215 |
| Failed — `ValueError: nonpositive or ill-conditioned working covariance` | **41** |
| Missing ledger cases | 0 |
| Failed at n=24 | 33 |
| Failed at n=48 | 8 |
| Failed shared-slope working family | 21 |
| Failed predictor-scaled-slope family | 20 |
| Failed Legendre-5 basis | 20 |
| Failed cubic-spline-13 basis | 21 |
| Successful cases requiring recorded sensor floor | 0 |
| Successful cases with full rank four-component moment operator | 215 |

The **frozen failure identity checksum** is SHA256 `a75ffbf14fb632ffa7ce18ad0203e25141c3ff9d83bbb676ecf6ac55dbc0010e` over alphabetically sorted UTF-8 lines `block|n_participants|source_support|mean_basis|working_family\n` from the original 41 failed model cases. Failed original generating blocks were concentrated at block 0 (n=24), block 1 (one case), block 4 (n=24 and n=48), and block 6 (n=24). This concentration demonstrates that missingness of successful inference is **not ignorable by default**.

The identical exception string does not by itself establish whether covariance-component NNLS boundary solutions, small eigenvalues of the estimated covariance, the residual-covariance CR2 adjustment `D_i`, or the absolute numerical eigensolver threshold is causally responsible. The current pilot has **not** recorded those three scales separately for all failures. They must be examined under the **identical original source seed and unchanged reference mathematics** before choosing a defensible remedy. In particular, simply lowering numeric thresholds or discarding cases to obtain 256/256 would be unjustified.

Reported method inclusion fractions from the 215 survivors are **descriptive and selection-conditioned**; they must never be interpreted as nominal 90% coverage. The original scientific failure and failed run should remain visible even if a later separately identified engineering investigation develops a stable equivalent factorization. Only a new independently seeded calibration with prespecified failure accounting can qualify improved inference.

Status: `estimated_target_pointwise_qualified=false`, `conditional_df_includes_covariance_estimation_uncertainty=false`, `simultaneous_bands_qualified=false`, `release_authorized=false`. Scientific blockers #289 and #296 remain open; no public API promotion, main merge, release tag or PyPI upload.
