# W3 R54 — prospective active-face REML nuisance response influence, preserving the R53 source

**Research-only mathematical/numerical diagnostic, not a population coverage simulation or software release.** This study deliberately reuses the exact R53 Gaussian primitive innovations because it is designed to investigate the **four original R53 covariance fits that were refused for smooth-interior differentiation**. R54 does **not** count them as new independent simulation replications, erase their earlier refusals, or relax R53's mathematical inclusion criteria.

## Scientific problem and predeclared contrast

R53 found **8/8** numerically accepted four-component Gaussian REML variance fits but only **4/8** regular positive-interior REML response Jacobians; the other four fitted **participant-slope covariance ratios at the original positive lower box bound** `LOW=exp(-13.8)`, despite positive source generating slope variance. The old full inverse-Hessian derivative is not valid at a bound.

The R49 Gaussian optimizer does not constrain the physical variances `theta` to fixed absolute bounds. Instead, its **ratio** parameters satisfy `LOW <= theta_k / reference(y) <= HIGH`, where `reference(y)=max(mean((y-X beta_WLS)^2),1e-8)` is itself estimated from the observed source responses. Hence at a lower active constraint, the physical component `theta_a(y)=LOW × reference(y)` **moves when the responses are perturbed**. An analysis fixing `theta_a` to zero or to an unchanging constant would be an incorrect derivative of the actual original R49 estimator.

## Derivation on a locally stable active face

Let `y_w=sqrt(w)y`, `Z=sqrt(w)X`, `R=I-Z(Z'Z)^-1 Z'`, and `n` denote observed native rows. Away from the separate absolute reference floor, `reference(y)=n^-1 y_w' R diag(1/w) R y_w`, so the **exact response gradient** is

`D_y reference = (2/n) R diag(1/w) R y_w`.

For the original absolute four-component Gaussian REML negative restricted-likelihood score and Hessian `s(theta,y_w)` and `H=d_theta s` derived and independently verified in R53, split the components into a fixed active set `A` and unconstrained free set `F`. On an active lower or upper variance-ratio face,

`D_y theta_A = diag(bound_ratio_A) D_y reference`,

and from the free-component restricted stationarity conditions `s_F=0`,

`H_FF D_y theta_F = B_F - H_FA D_y theta_A`, where `B_k=P K_k P y_w`.

When and only when `H_FF` is strictly positive definite, invertible and well conditioned, the resulting full four-component response Jacobian is used in the unchanged R53/R22 identity

`D_y (CR2_SE²) = partial_y(CR2_SE²)|theta + partial_theta(CR2_SE²) × D_y theta`,

then propagated to the studentized focal CR2 statistic using the exact WLS numerator derivative. These local constrained-face equations are not a global characterization of estimator-root switching, variance-component zero-null distributions or a general coverage correction.

### Frozen refusal and strict-complementarity gates

Every original Gaussian covariance fit must still pass **the same two-start R49 physical ratio optimization**, with original projected KKT **<=0.001** and near-best original NLL **<=0.001**. Active lower/upper states are recognized only within a preregistered relative ratio tolerance **1e-5** of the exact positive box bound. Any other free ratio must remain at least **20×** the lower bound and below the upper bound divided by 20. Require a dimensionless signed Gaussian REML gradient **>=0.001** at every lower active face (or **<=−0.001** at every upper active face), excluding weak strict-complementarity cases; do not silently declare a zero-sign-gradient or loosely clipped estimate a valid nonsmooth derivative. The **free-block observed Hessian** must be SPD with spectral condition <= **1e9**; otherwise refuse. Do not regularize Hessians, alter the original physical ratio box, permit zero-variance components by fiat, or fall back to the R53 full inverse Hessian for an active case.

The active-set derivative holds only while the exact optimizer remains on the same face. If an original response perturbation makes either plus or minus REML refit choose a **different active-set signature**, record a refused directional comparison with all numerical fits and original source identities intact. Such switching is evidence of a nonsmooth issue, not a bug to hide.

## Exact R53 source replay and prospective perturbation design

Use **the original R53 source seed 202610175353 and same four independent Gaussian primitive source blocks**, n24, true positive predictor-scaled slope, paired ordinary/extreme leverage. This produces eight source/support cases but **does not add any new independent Gaussian source evidence or coverage trials**. Use a new independent perturbation direction seed **202610175454** and **two** frozen deterministic native weighted-response directions per source, instead of R53's three. Use amplitude `h=0.0005 × max(original weighted-response RMS, 0.01)`, smaller than R53's perturbation amplitude to interrogate the *same local face*. Preserve the fixed source innovations, original estimated covariance family, R49 solver starts, full-patient cluster IDs and true focal projected slope.

For every accepted active-face or free-interior local Jacobian, fit full original two-start Gaussian REML separately on `y_w±h d` and recompute CR2. Compare the observed centered four-component nuisance derivative and studentized focal derivative against the constrained implicit prediction **only if the original and both perturbed fits pass all original numerical gates and retain identical active-set signatures**. Preserve signs and derivative values; do not reselect directions based on agreement. Cases whose original strict complementarity, reference floor, box or Hessian conditions refuse retain both original direction slots as not attempted.

The frozen failure-inclusive ledger contains **8 original source records, 16 directional comparison records, 32 planned plus/minus covariance refit slots, 40 planned original/perturbed REML fit slots and 80 planned two-start optimizer outcome slots**. These are *planned* denominators; not-attempted stages must be distinguished from executed accepted stages, and attempted but active-set-switched directions are refused, not treated as valid comparisons. The original JSON archive preserves each plus/minus fit, signed KKT checks, chosen active-face components and strict rejection reasons; also records `cases.json`, `summary.json`, `source-commit.txt` and all three SHA256 digests. A complete structural ledger can pass CI with genuine source-level scientific refusals, which are to be reported.

The mathematical test suite independently verifies the derivative of R49's moving WLS variance-reference bound against centered response finite differences, source equality to R53, original lower-bound detection, positive slope covariance, correct reduced/free Jacobian dimensions, active-bound derivative `LOW × D_y reference`, serialization of arrays and NaN refusal, and complete failure-denominator accounting.

## Scientific boundaries

This study can determine whether **a stable strictly complementary active-face local derivative exists** for the originally refused R53 boundary cases and whether that local prediction matches the actual R49 refitting algorithm. It does **not** derive a directional projection limit distribution at weak complementarity, prove the optimizer selects the same local optimum, characterize the finite-sample distribution of the fitted covariance across faces, or establish calibrated nominal 90% pointwise CR2 confidence intervals. It does not produce 90% simultaneous whole-function bands, a valid slope-variance boundary null test, causal missingness identification, MAR/MNAR correction, or latent complete-participant selection inference.

Keep original adverse R20/R22/R33–R53 results—including the four R53 smooth-interior refusals—intact. Scientific issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain **OPEN**. No protected-main merge, supported inference API, version 1.2 tag or PyPI publication.
