# B7: learned Bayesian planar factor posterior (unpublished research)

**Status:** native implementation and reproducible pilot are experimental.
No 1.2 release, root export, selected architecture, or scientific inferential
qualification is authorized. Stable `1.1.0` is unchanged.

The parent B7 `fit_bayesian_planar_score_baseline()` **conditions on known
population functions**. The follow-on experimental
`eyetrajectoriespy.bayesian.fit_bayesian_planar_factor()` instead uses a
Gaussian shared-factor model to **learn** the population mean and joint
x/y covariance from irregular coordinate observations.

## Generative model

For independent participant `i`, coordinate `d` in `{x,y}` and its own
observed timestamp `t_idj`:

$$
 y_{idj}=B(t_{idj})^\top(\mu_d+L_d z_i)+\epsilon_{idj},
 \qquad z_i\sim N(0,I_K).
$$

Here `B(t)` is a **fixed** cubic B-spline dictionary; each coordinate has
Gaussian priors on mean and loading coefficients, and
`epsilon_idj ~ N(0, sigma_d^2)` with **fixed, supplied** coordinate-specific
noise scales. Exact Gaussian conditional updates alternate mean, loadings
and **shared** participant scores. Posterior x/y cross-covariance follows
from the shared factors, not from interpolation.

## Native asynchronous input

`IrregularTrajectorySet` can encode separate coordinate observation
times as the union of actual timestamps, using `NaN` for the unobserved
coordinate. Only observed likelihood rows are included. Neither coordinate
is silently interpolated or aligned to the other, and all timestamps must
lie within the declared evaluation-grid support. No repeated
`participant_id` is permitted by this model.

```python
import numpy as np
from eyetrajectoriespy.bayesian import fit_bayesian_planar_factor

result = fit_bayesian_planar_factor(
    gaze,  # native IrregularTrajectorySet, unique participant_id metadata
    dimensions=("x", "y"),
    evaluation_grid=np.linspace(0, 1, 27),
    observation_noise_sd=(0.04, 0.06),
    n_components=2,
    n_basis=5,
    n_chains=2,
    n_draws=60,
    warmup=90,
    random_state=2026,
)
summary = result.posterior_population_frame()
```

The `joint_population_covariance_draws` tensor has shape
`(chain, draw, 2G, 2G)` and **channel-major** ordering
`[x(t_1)..x(t_G), y(t_1)..y(t_G)]`. Do not feed this tensor into a
time-major multivariate recovery helper without an explicit permutation.
The `loading_function_draws` shape is
`(chain, draw, component, grid, coordinate)`. Individual loading columns
are nonidentified under sign/rotation; compare only reconstructed
functions, covariance and appropriate subspaces.

The summary displays marginal posterior means and pointwise 5th/95th
quantiles for mean x, mean y, their variances and synchronous-time x/y
cross-covariance. They are **not scientifically calibrated intervals**.

## Prior/likelihood pilot

```bash
python scripts/run_b7_learned_planar_truth_pilot.py --replicates 4 --draws 35 --warmup 60 --out build/b7-truth
```

The pilot generates actual Gaussian parameters, shared scores and noise
from the declared priors/likelihood. It refits the learned x/y model for
rank-1 and rank-2 populations, with paired and separately timestamped
asynchronous observations. It retains exceptions and evaluates pointwise
mean and cross-covariance 90% coverage with exact binomial Monte Carlo
intervals. CI uses only two repetitions per condition, an engineering
smoke pilot and **not** scientific coverage evidence.

## Outstanding scientific requirements

A complete B7 programme still requires posterior convergence and
multivariate SBC rank studies; near-tied subspace calibration;
measurement-noise and prior misspecification; native PACE and independent
external comparison; held-out independent participant prediction;
multi-session/participant hierarchy; and residual serial covariance.
Channel-specific Gaussian observation noise is **fixed**, not inferred.
Identifiable individually ordered eigenfunctions are **not learned**.
The factor rank and basis are **not** selected by posterior inference.

Engineering success must never set scientific or publication flags true.
See [B6/F1/F5 calibration protocol](b6-f1-f5-calibration-protocol.md)
and the scientific issue [B7 #239](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/239).
