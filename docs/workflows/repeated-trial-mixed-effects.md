# Repeated-trial functional mixed effects

Use this route when participants contribute repeated trials and the response is
continuous/approximately Gaussian, especially when predictors vary by trial or
participant/trial covariance is scientifically consequential.

## 1. Preserve the hierarchy

Keep participant, trial and time identities explicit:

~~~text
participant -> trial -> time
~~~

Do not flatten trial-time rows into independent observations.

## 2. Fit the smallest scientifically justified mixed model

~~~python
fit = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="response",
    fixed_basis_size=4,
)
~~~

The canonical starting point is the documented participant functional random
effect. Random functional slopes, trial functional effects and residual
correlation are **advanced extensions** that should be declared because the
scientific design requires them, not added automatically.

## 3. Diagnose covariance attribution

Inspect random-effect covariance diagnostics and residual dependence. If a
serial covariance model is fitted, whitened residuals—not raw residuals—are the
relevant check for remaining serial structure.

## 4. Separate coefficient inference from covariance sensitivity

Use `bootstrap_functional_mixed_effects_coefficients()` for whole-function
coefficient bands. Use full-refit bootstrap or covariance-structure sensitivity
only when variance-component uncertainty or defensible competing covariance
structures are part of the scientific question.

## 5. Report estimand and hierarchy

Use `functional_mixed_effects_reporting_text()`. Report participant/trial
mapping, fixed and random bases, residual covariance specification, ML/REML
contract, resampling unit, convergence/boundary diagnostics and simultaneous
coverage scope.

### Do not use this route when

The response is genuinely Bernoulli, grouped binomial or Poisson. The current
mixed-effects subsystem is Gaussian; use the generalized marginal GEE workflow
for those observation families.
