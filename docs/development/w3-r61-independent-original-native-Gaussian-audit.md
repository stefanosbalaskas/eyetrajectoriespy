# W3 R61-A — genuinely separate reconstruction of ORIGINAL raw-native Gaussian covariance evidence

**Read-only source-evidence and mathematical-reconstruction audit. Not an inferential-calibration study.**

The original [R61 scientific run #39068871584](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39068871584) completed **6/6** dedicated jobs: four new independent Gaussian primitive blocks, ordinary/extreme leverage paired within block (eight cases), **8/8 accepted**, **192/192 H0 participant covariance/Cholesky checks**, **16/16 1,024-draw Gaussian whitening witnesses**, no source refusal. The original [complete synthetic native archive #12114213307](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39068871584/artifacts/12114213307) was produced at the immutable original scientific PR merge checkout `92af2f707a6e9c608e405b84693165b507900143`. Original source maximum absolute covariance identity discrepancy **3.2526065174565133e−19**; maximum weighted-to-native-to-whitened residual discrepancy **1.2656542480726785e−14**.

Unlike R60, the original R61 archive retains **raw artificial X, y, w, group, time, trial, x**, original fitted H0 physical covariance `theta`, H0 GLS `beta`, source numerical fit and each 1,024-draw witness's original random seed and summary. Therefore a separate implementation can reconstruct the target covariance from those native arrays, rather than inspecting only the previous algorithm's summary claims.

## Independent audit requirements

The R61-A auditor **does not import R61, R60, R57, R20, the source generator, the REML objective or their covariance helpers**. It accesses only the previously completed original archived data and numerical libraries (NumPy, SciPy). It validates three SHA256 source digests and original PR merge checkout before reading 8 complete distinct paired source cases and full source metadata.

For all **24 clusters per case**, reconstruct the fitted exact-zero slope H0 participant covariance in weighted coordinates by direct elementary algebra, independently of R20's kernel builder:

`V_i = theta_intercept [sqrt(w_i)(1+0.30t_i)][sqrt(w_i)(1+0.30t_i)]' + theta_trial [sqrt(w_i)sqrt(w_i)'] ⊙ I(trial_i = trial_j) + theta_sensor diag(w_i)`.

The participant random-slope H0 variance is **exactly 0**. Verify covariance SPD via independent Cholesky; the Cholesky/covariance error across all 192 blocks; and independently refit H0 *generalized least squares fixed mean beta conditional on the frozen original H0 theta* (this is **not** independently rerunning the nuisance REML optimizer), comparing to the original archived beta.

For first/last cluster within each of eight original support cases (16 witnesses), use the archived **frozen independent RNG seeds** to reconstruct all **1,024 Gaussian standard-normal draws per witness**, then apply participant Cholesky, remove native weights and restore them to whiten again. Reconstruct each archived witness mean RMS, empirical covariance-to-identity Frobenius RMS, approximate sampling-noise scale and maximum original weighted residual/whitening deviation. Enforce full source/participant/draw denominator and fail-closed provenance, seed, SHA256 and scientific non-release flags.

## Scientific qualification boundary

Successful R61-A would establish **independently reproduced covariance algebra, GLS mean and seed-based Gaussian draw back-transformation** for previously archived artificial data. It cannot independently regenerate the original unarchived **latent source innovations** or prove that the R17 source Gaussian model is the real generating law in eye-tracking datasets. It also cannot prove finite-sample calibration of the R57/R58 likelihood ratio reference or R60 bootstrap p-values, Type-I error, power, fitted-covariance 90% CR2 pointwise/simultaneous bands, or MAR/MNAR robustness.

The original R61 SHA256 evidence is fixed; do not silently change, regenerate or overwrite it following a discovered audit failure. Preserve any failed independent audit workflow and correct only the new auditor in its own draft research branch. This is a new independent numerical-evidence gate, and passing unit tests alone is not sufficient: the actual complete original-source artifact must be checked by a separately passing job.

Scientific issues #289 and #296 remain open. No public API, protected main merge, version 1.2 release or PyPI publication.
