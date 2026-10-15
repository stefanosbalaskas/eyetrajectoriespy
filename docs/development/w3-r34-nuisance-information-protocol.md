# R34 — fitted Gaussian covariance nuisance-information and interval-width sensitivity

**Research-only independent numerical diagnostic, not a new functional confidence interval method.** [R33 original high-leverage results](w3-r33-leverage-misspecified-cr2-results.md) identified changes in conditional Satterthwaite degrees of freedom and 90%-nominal CR2 interval half-widths under fitted covariance working-family misspecification, even when pointwise CR2 standard errors looked similar. That finding motivates quantifying the *local sensitivity* of the conditional interval width to each nuisance covariance variance component.

## Prespecified independent source and evaluation

Fresh Gaussian seed **202610163434**, **4 genuinely new independently generated source blocks**, **24 participants**, native original irregular repeated-trial trajectories, original n24 Gaussian predictor-dependent random-slope source with either ordinary bounded predictor or extreme-leverage source (participant x0=3, x1=−2.5). Cross two **independently specified working families**: predictor-scaled (correct) and shared slope (deliberately incorrect). This yields **16 model/source cases, only 4 independent source blocks**; it is a targeted mathematical and engineering pilot, **not** nominal Monte Carlo coverage.

For each case, fit the R25 observation-only four-component Gaussian REML estimator using the complete native WLS design, participant/trial/time/predictor labels and original gaze response values; simulator-generating variance parameters and latent innovations are never supplied to fitting. Retain optimizer status, covariance-boundary flags, source failures and every CR2 refusal in an original case ledger.

The fitted vector of **log component variances** is perturbed one component at a time by ±0.02 and ±0.01, holding the other components fixed. Build each participant covariance target from the four prespecified Gaussian covariance kernels and recompute the original R22 scaled-Cholesky CR2 SE, conditional Satterthwaite df and two-sided 90%-nominal interval half-width. The central finite-difference gradient of **log half-width** and of df is reported, with a separate half-step numerical sensitivity check; a CR2 numerical refusal must be counted, never replaced by a threshold relaxation.

## Curvature diagnostic and explicit refusal policy

Independently evaluate the original analytic Gaussian REML negative-loglikelihood gradient around the same fitted log covariance components using centered ±0.02 and ±0.01 perturbations. This produces the **observed REML log-variance information / Hessian**, not the R27 simulation-true *expected* Fisher information. Check approximate Hessian symmetry, numerical derivative-step agreement, strictly positive eigenvalues, and an eigencondition ratio below 1e9.

Only for a stable positive-definite **interior** REML fit (no active numerical lower bound or near-zero variance), compute the exploratory delta diagnostic

`local_sd(log CI_halfwidth) = sqrt(g' H^{-1} g)`,

where `g` is the conditional CR2 log half-width gradient with respect to four log-component variances and `H` is observed restricted-likelihood curvature. Record the derivative, curvature eigenvalues, number of refusals and the local SD. A boundary variance component, nonpositive curvature, strongly asymmetric/unstable Hessian, unstable width derivative or R22 numerical refusal leads to a **documented refusal**, not a positive semidefinite clip, floor or unqualified inverse.

**This formula is NOT an uncertainty-corrected confidence interval for the functional regression coefficient.** It describes sensitivity in the *reported interval half-width* to a local Gaussian nuisance-covariance asymptotic approximation, not coverage or an adjustment to Satterthwaite df. No new critical-value correction or method winner is selected.

## Scientific and release boundaries

Four independent source blocks and 16 paired nuisance models cannot establish population performance or general inferential validity. The correctly specified Gaussian source omits physiological sensor contamination, non-Gaussian joint errors, realistic selection, missing gaze samples and unknown true covariance structure. The curvature inverse itself relies on regular finite-sample Gaussian assumptions, which are particularly questionable near the exact component boundaries motivating R20–R33.

R34 must not produce 90% pointwise truth-inclusion coverage, simultaneous confidence bands, a release verdict or public API. A separate independently seeded, substantially larger **inference procedure** study (such as genuine participant-level bootstrap with full REML re-estimation or a theoretically derived joint nuisance adjustment) is needed to qualify functional effect uncertainty. Keep scientific blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) OPEN, preserve R20 41/256 failures and R22 32 numerical refusals, and keep all development in a draft PR stacked on R33 with protected main, stable API, release tags and PyPI unchanged.
