# R41 — physical-gradient KKT refinement of R40 original optimizer exceptions

**Outcome-selected numerical diagnostic only; NOT a fresh-source independent replication.** Draft research stacked on [R40](w3-r40-fresh-source-nuisance-results.md). No new Gaussian source blocks, no post hoc assumption of optimizer qualification, no significance test, no nominal 90% CR2 interval or whole-function band.

## Original evidence and frozen selection

R40 master seed **202610164040** produced **eight independent Gaussian primitive blocks**, with paired ordinary/extreme leverage and genuine zero/positive slope generating conditions. The original **R40 cases.json SHA256 is 7943b6ea869c242ba8b7ee7c00a7025af755f2d9ef7d9e9aaec1e36c4009c349**; the original R40 artifact is [#12011474333](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38819889969/artifacts/12011474333).

The current experiment *selects* **all 18/192** R40 raw linear-variance nuisance optimizer fits where the projected physical nuisance variance-ratio KKT score exceeded the original frozen **0.001** cutoff; these occur across **15** separate block/support/state/fixed-slope profile cells. The **15 controls**, one from each of the same R40 profile cells with a recorded KKT score at or below 0.001, were selected deterministically in R40 nuisance-start order. Both complete frozen lists are version-controlled in the R41 script. Selection depends on the original numerical outcome: the 33 replayed starts **must not be interpreted as randomly sampled experimental data or an independent test sample**.

## Exactly three algorithms / statuses per original start

Regenerate **the same** original R40 participant-level Gaussian primitives with the exact original master seed and block IDs. Reconstruct the same irregular trials and observed-only reference variances. First re-run each original R40 fit from its frozen observed-data-blind source starting triple with the **unchanged raw positive physical linear-nuisance ratios**, original L-BFGS-B settings and original Gaussian restricted-likelihood score. The original KKT-exception versus control label **must reproduce**; if it does not, record an explicit source-refusal instead of silently selecting alternate cases.

For each successful baseline, run **two prespecified restarts from the same baseline endpoint**:

- **Stricter L-BFGS-B** using unchanged raw Gaussian negative restricted loglikelihood, analytic score and positive variance-ratio box limits, with maxiter 450, ftol 0, gtol 1e-10, maxls 80 and maxfun 2200.
- **Independent SLSQP algorithm** using the *same original raw objective and analytic score*, original strictly positive physical ratio bounds, maxiter 450 and ftol 1e-11. A different convergence flag or worse objective counts as a diagnostic failure, not automatic improvement.

No change to the Gaussian likelihood, model data, random slope variance, nuisance box or truth mechanisms. All fitted objectives must be recomputed against the original unshifted analytic Gaussian NLL and analyzed in a single common physical linear-ratio coordinate system, including projected KKT scores, objective reconstruction errors, optimizer status and nuisance bounds.

Prespecified expected records: **18 original exceptions + 15 controls = 33 original source/start evaluations × 3 algorithms = 99 optimizer records**. An unsuccessful baseline can prevent its two restarts: those absent planned runs **must remain visible as missing**, and the integrity gate must refuse. A failed restart remains in the full ledger, even if a different solver succeeded.

## Decision boundaries

Record whether each original KKT-exceeding case becomes KKT-compliant and remains within 0.001 original NLL of its baseline. Also report all worsening NLL outcomes by more than 0.001, nonconvergences and physical KKT failures; the original 18 exceedances remain part of the historical R40 ledger. No redefinition of the prespecified **physical KKT 0.001** or **NLL 0.001** thresholds.

Even if all outcome-selected exceptions pass on restart, this does not constitute external replication or certify global optimization. The **next** numerical gate is *new independent primitive Gaussian sources* evaluated end-to-end under the predeclared complete candidate selection/refusal policy (not success-biased selection), including a separate potential perturbation of missing-observation process and covariance misspecification. Only after that can scientifically separate variance test null calibration and fitted-covariance-aware pointwise functional CR2 inference be contemplated.

Blockers [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain **OPEN**. No protected-main merge, public estimator/API qualification, publication tag or version 1.2 PyPI release.
