# Generalized binary and count functional responses

Use this route for repeated non-Gaussian functional responses when the target is
a **marginal / population-averaged** effect of scalar predictors.

## 1. Declare the observation contract

Choose exactly one of the supported representations:

- Bernoulli: (Y_{ij}(t)in{0,1});
- grouped binomial: integer successes (S_{ij}(t)) plus explicit positive
  integer denominators (N_{ij}(t));
- Poisson expected count: non-negative integer counts;
- Poisson rate: non-negative integer counts plus explicit positive exposure
  (E_{ij}(t)).

Do not supply an arbitrary proportion for grouped binomial data and do not use
exposure merely to normalize a count trajectory.

## 2. Fit the marginal GEE

~~~python
fit = fit_generalized_function_on_scalar_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="response",
    family="binomial",
    basis_size=4,
    spline_degree=2,
)
~~~

Participants are independent clusters. Working independence is fixed and
coefficient uncertainty uses the robust cluster sandwich covariance.

## 3. Preserve denominator/exposure information

For grouped binomial observations, denominators travel with successes in every
participant bootstrap. For Poisson rate models, exposure travels with counts.
Neither is inferred or perturbed independently.

## 4. Use fixed-profile prediction only for declared scientific targets

Bernoulli/grouped-binomial fits predict marginal success probability.
Exposure-adjusted Poisson fits distinguish rate from expected count; expected
count requires explicit target exposure.

## 5. Report the marginal estimand

Use `generalized_function_on_scalar_reporting_text()`. State family/link,
response coding, participant cluster, grouped denominator or exposure
definition, basis, robust covariance, bootstrap contract and whether prediction
targets were extrapolative.

### Scope boundary

This is not a generalized functional random-effects model. Negative binomial,
zero-inflated, hurdle and Tweedie families are intentionally outside the
0.51-0.54 canonical observation contract.
