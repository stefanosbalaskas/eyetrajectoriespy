# One participant random functional slope

Version 0.45 adds one explicitly declared participant random functional slope to
the existing Gaussian functional mixed-effects regression.

## Model

For participant $i$, trial $j$, and observed time $t$,

$$
Y_{ij}(t)
=
\mathbf x_{ij}^{\top}\boldsymbol\beta(t)
+
b_{0i}(t)
+
X_{ij,q}b_{1i}(t)
+
\varepsilon_{ij}(t).
$$

The participant random intercept and random slope are

$$
b_{0i}(t)=\mathbf B_r(t)^{\top}\mathbf u_{0i},
\qquad
b_{1i}(t)=\mathbf B_r(t)^{\top}\mathbf u_{1i}.
$$

Version 0.45 supports **exactly one** random-slope predictor:

~~~python
fit = fit_functional_mixed_effects_regression(
    trajectories,
    design,
    predictors=("condition",),
    participant_column="participant_id",
    dimension="x",
    fixed_basis_size=6,
    random_basis_size=4,
    random_slope_predictor="condition",
)
~~~

Setting `random_slope_predictor=None` retains the existing random-functional-
intercept model.

## Why the covariance guard matters

With random basis size $q$, the intercept-only random vector has dimension
$q$. Adding one random functional slope gives dimension $2q$. A fully
unstructured covariance therefore has

$$
p_{\Psi}=\frac{(2q)(2q+1)}{2}
$$

free parameters.

For the default $q=4$, this is 36 covariance parameters.

Version 0.45 therefore refuses the random-slope model unless the participant
count is **strictly greater** than the number of free covariance parameters.
Thus the default $q=4$ random-slope specification requires at least 37
participants.

This is a conservative **minimum complexity guard** against an obviously
fragile covariance fit. It is not an adequacy guarantee, a universal
statistical theorem, or an automatic basis-selection rule. Passing the guard
does not make the covariance well estimated; eigenvalues, condition number,
boundary and singularity diagnostics must still be inspected.

## Identifiability guard

The named random-slope predictor must:

- be one of the declared fixed predictors;
- contain finite numeric values;
- vary within every participant.

The last requirement is intentionally stricter than mathematical identification
requires in every possible unbalanced mixed-model design. It is the guarded
0.45 contract: if any participant lacks within-participant variation, the
package refuses the model rather than relying on cross-cluster information to
rescue that participant's slope. A future unbalanced-design tranche could relax
this only with dedicated validation.

## Retained covariance diagnostics

The result retains:

- the complete random-effect design matrix;
- full random-effect covariance;
- intercept covariance block;
- slope covariance block;
- intercept/slope cross-covariance block;
- covariance eigenvalues;
- covariance condition number;
- random-effect dimension;
- free covariance parameter count;
- boundary and singularity diagnostics;
- a dedicated near-zero random-slope boundary flag;
- participant count and curves-per-participant counts;
- backend convergence warnings;
- the exact random-slope predictor name.

No random-effect covariance block is reconstructed from rounded summaries.

## Participant BLUP functions

The participant-specific functions are available directly:

~~~python
from eyetrajectoriespy import (
    functional_random_effect_frame,
    plot_functional_random_effects,
)

slope_frame = functional_random_effect_frame(
    fit,
    effect="slope",
)

ax = plot_functional_random_effects(
    fit,
    effect="slope",
)
~~~

The slope function $\widehat b_{1i}(t)$ describes how participant $i
response to the declared predictor deviates from the population fixed
coefficient function over trial time.

It is a model-based BLUP, not an independently observed participant trajectory.

## Covariance interpretation

The intercept/slope cross-covariance block describes association between the
random-basis coefficients underlying $b_{0i}(t)$ and $b_{1i}(t)$. It should
not be reduced automatically to one scalar correlation unless that reduction is
scientifically justified.

If the slope covariance approaches zero, the dedicated slope-boundary
diagnostic is retained rather than silently converting the model to an
intercept-only fit.

At an exact zero-variance boundary, the backend may instead fail to converge.
That is also treated as an informative fail-closed outcome: the package raises
the non-convergence error and does not return a nominal heterogeneous-slope fit
or silently switch optimizers.

## Simultaneous fixed-effect inference

The 0.44 participant-cluster bootstrap remains available:

~~~python
boot = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)
~~~

For a random-slope fit, the full fitted intercept/slope covariance and residual
variance remain fixed during the bootstrap GLS refits. Therefore these bands
remain **conditional fixed-effect inference under the fitted covariance
structure**.

Version 0.45 does not claim that the 0.44 bootstrap incorporates random-slope
variance-component estimation uncertainty.

## What 0.45 deliberately does not add

Version 0.45 does not add:

- more than one random functional slope;
- automatic random-slope selection;
- automatic covariance simplification;
- separate slope/intercept basis sizes;
- residual serial correlation;
- trial-level functional random effects;
- generalized/non-Gaussian responses;
- full-refit participant bootstrap uncertainty.

The planned next inference tranche is a full-refit participant bootstrap
sensitivity layer so covariance parameters are re-estimated inside bootstrap
samples.

## Evidence basis

Functional additive/mixed models support correlated functional responses with
functional random effects and scalar covariates whose effects vary over the
functional index. See Scheipl, Staicu, and Greven (2015), DOI
`10.1080/10618600.2014.901914`.

The underlying `statsmodels.MixedLM` backend represents correlated random
coefficients through the supplied random-effects design matrix. Version 0.45
uses that native contract while adding stricter functional-design,
within-participant-variation, covariance-complexity, and provenance safeguards.
s
response to the declared predictor deviates from the population fixed
coefficient function over trial time.

It is a model-based BLUP, not an independently observed participant trajectory.

## Covariance interpretation

The intercept/slope cross-covariance block describes association between the
random-basis coefficients underlying (b_{0i}(t)) and (b_{1i}(t)). It should
not be reduced automatically to one scalar correlation unless that reduction is
scientifically justified.

If the slope covariance approaches zero, the dedicated slope-boundary
diagnostic is retained rather than silently converting the model to an
intercept-only fit.

## Simultaneous fixed-effect inference

The 0.44 participant-cluster bootstrap remains available:

~~~python
boot = bootstrap_functional_mixed_effects_coefficients(
    fit,
    n_bootstrap=1000,
    random_state=2026,
)
~~~

For a random-slope fit, the full fitted intercept/slope covariance and residual
variance remain fixed during the bootstrap GLS refits. Therefore these bands
remain **conditional fixed-effect inference under the fitted covariance
structure**.

Version 0.45 does not claim that the 0.44 bootstrap incorporates random-slope
variance-component estimation uncertainty.

## What 0.45 deliberately does not add

Version 0.45 does not add:

- more than one random functional slope;
- automatic random-slope selection;
- automatic covariance simplification;
- separate slope/intercept basis sizes;
- residual serial correlation;
- trial-level functional random effects;
- generalized/non-Gaussian responses;
- full-refit participant bootstrap uncertainty.

The planned next inference tranche is a full-refit participant bootstrap
sensitivity layer so covariance parameters are re-estimated inside bootstrap
samples.

## Evidence basis

Functional additive/mixed models support correlated functional responses with
functional random effects and scalar covariates whose effects vary over the
functional index. See Scheipl, Staicu, and Greven (2015), DOI
`10.1080/10618600.2014.901914`.

The underlying `statsmodels.MixedLM` backend represents correlated random
coefficients through the supplied random-effects design matrix. Version 0.45
uses that native contract while adding stricter functional-design,
within-participant-variation, covariance-complexity, and provenance safeguards.
