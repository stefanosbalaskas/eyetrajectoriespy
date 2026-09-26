# Experimental functional regression

Use this route when the response is a continuous functional outcome and the
scientific question is how **declared scalar experimental predictors** change
that response over time.

## 1. Define the response and predictor design

Construct a complete common-grid functional response and an aligned scalar
design table. Encode interactions explicitly. The package does not choose
categorical coding, interactions, centering or scaling automatically.

## 2. Choose the correct repeated-measures route

For independent curves, fit

~~~python
fit = fit_function_on_scalar_regression(
    trajectories,
    design,
    predictors=("condition",),
    dimension="response",
)
~~~

If repeated participant trials exist, participant averaging is only defensible
when the predictor is participant-constant and that aggregation matches the
scientific estimand. Trial-varying predictors should move to the
[repeated-trial mixed-effects workflow](repeated-trial-mixed-effects.md).

## 3. Use whole-function inference

For simultaneous coefficient inference, use the fixed-design wild bootstrap
provided for function-on-scalar regression rather than reading pointwise
intervals as whole-function evidence.

~~~python
bootstrap = bootstrap_function_on_scalar_coefficients(
    fit,
    n_bootstrap=1000,
    random_state=55,
)
~~~

## 4. Interpret coefficients as functions

A coefficient $\\beta_k(t)$ is the expected change in the functional response
at time (t) for a one-unit change in the declared predictor, conditional on
the fitted scalar design. Report the time domain over which simultaneous
coverage is claimed.

## 5. Report the complete contract

Use `function_on_scalar_reporting_text()`. Report predictor coding, basis or
grid contract, uncertainty method, bootstrap seed/size, simultaneous scope and
any aggregation performed upstream.

### Advanced branches

Scalar-on-function FPCR and heteroscedastic fixed-target wild-bootstrap
inference answer different questions. They are not interchangeable with this
canonical function-on-scalar route.
