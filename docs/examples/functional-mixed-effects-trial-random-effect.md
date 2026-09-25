# Trial-level functional random effects

This example adds a nested smooth trial-specific deviation to the existing
functional mixed-effects model.

## Fit the hierarchy

Assume `trajectories.metadata` contains `participant_id` and `trial_id`,
with one trajectory per participant/trial pair.

~~~python
from eyetrajectoriespy import fit_functional_mixed_effects_regression

fit = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    trial_column="trial_id",
    trial_random_effect="functional_intercept",
    dimension="metric",
    fixed_basis_size=4,
    random_basis_size=3,
    trial_random_basis_size=3,
    spline_degree=2,
    reml=True,
    method="lbfgs",
)
~~~

The fitted model is

[
Y_{ij}(t)
=
mathbf x_{ij}^{	op}oldsymboleta(t)
+
b_i(t)
+
u_{ij}(t)
+
epsilon_{ij}(t).
]

The participant and trial covariance matrices are estimated separately.

## Inspect covariance diagnostics

~~~python
fit.trial_random_effect_covariance
fit.trial_random_effect_covariance_eigenvalues
fit.trial_random_effect_covariance_condition_number
fit.trial_random_effect_boundary_fit
fit.trial_random_effect_singular
~~~

Do not remove the trial effect automatically merely because a covariance
eigenvalue is close to a numerical boundary. Report and investigate the
diagnostic.

## Inspect trial BLUPs

~~~python
from eyetrajectoriespy import (
    functional_trial_random_effect_frame,
    plot_functional_trial_random_effects,
)

trial_frame = functional_trial_random_effect_frame(fit)

plot_functional_trial_random_effects(
    fit,
    participant_id=fit.participant_ids[0],
    max_trials=6,
)
~~~

Each source trial remains identifiable through its curve ID, participant ID,
source trial label, and composite nested trial ID.

## Compare residual structure before and after

~~~python
from eyetrajectoriespy import (
    functional_mixed_effects_residual_diagnostics,
)

before = functional_mixed_effects_residual_diagnostics(
    participant_only_fit,
    max_lag=6,
)

after = functional_mixed_effects_residual_diagnostics(
    fit,
    max_lag=6,
)
~~~

A reduction in broad, smooth residual dependence supports the interpretation
that some dependence belonged to trial-specific smooth heterogeneity. It is not
a model-selection test and does not prove that no serial residual covariance
remains.

## Fixed-covariance participant bootstrap

~~~python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_coefficients,
    functional_mixed_effects_simultaneous_bands,
)

conditional_bootstrap = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=1000,
    random_state=48,
)

conditional_band = functional_mixed_effects_simultaneous_bands(
    conditional_bootstrap,
)
~~~

The fitted participant covariance, trial covariance, and residual variance are
held fixed.

## Full-refit participant bootstrap

~~~python
from eyetrajectoriespy import (
    bootstrap_functional_mixed_effects_full_refit,
    functional_mixed_effects_full_refit_trial_audit_frame,
)

full = bootstrap_functional_mixed_effects_full_refit(
    fit,
    n_bootstrap=1000,
    random_state=48,
)

trial_audit = functional_mixed_effects_full_refit_trial_audit_frame(full)
~~~

Whole participants are resampled. Their complete trial bundles travel with
them. A duplicated participant draw receives a distinct bootstrap participant
identity and its trials receive distinct nested bootstrap trial identities.
