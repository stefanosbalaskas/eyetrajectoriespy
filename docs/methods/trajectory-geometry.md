# Continuous trajectory geometry

Version 0.31 adds differential-geometric functions for continuous planar gaze trajectories.

The goal is not to replace event-level saccade-curvature metrics. It is to expose continuous functions that can themselves enter the package's FDA pipeline:

\[
G_i(t)
\rightarrow
\theta_i(t),\ \kappa_i(t),\ \omega_i(t)
\rightarrow
\text{FPCA / multilevel FPCA / functional inference}.
\]

## APIs

The core functions are:

- \`heading_function()\`;
- \`signed_curvature_function()\`;
- \`turning_rate_function()\`;
- \`trajectory_tortuosity()\`.

All require a complete planar trajectory. Differential quantities require at least three time samples because the implementation uses second-order edge-aware numerical gradients.

## Heading

For \(G(t)=[x(t),y(t)]^\top\),

\[
\theta(t)=\operatorname{atan2}\{y'(t),x'(t)\}.
\]

The returned angle is wrapped to \([-\pi,\pi]\). The package does **not** unwrap it automatically.

This matters for FDA: two directions near \(+\pi\) and \(-\pi\) are geometrically close but numerically far apart. Do not feed wrapped heading directly into ordinary Euclidean FPCA without an explicit circular or unwrapping strategy.

## Signed curvature

\[
\kappa(t)
=
\frac{x'(t)y''(t)-y'(t)x''(t)}
{\{x'(t)^2+y'(t)^2\}^{3/2}}.
\]

Curvature is positive or negative according to the orientation of the supplied coordinate axes.

The package does not assume that screen \(y\) points upward. If your tracker reports pixel \(y\) increasing downward, the **visual** interpretation of the sign is reversed relative to a conventional Cartesian plot.

## Turning rate

\[
\omega(t)
=
\frac{x'(t)y''(t)-y'(t)x''(t)}
{x'(t)^2+y'(t)^2}
=
\kappa(t)\|G'(t)\|.
\]

The implementation computes this directly from the derivatives. It does not differentiate the wrapped heading function, so artificial jumps at the \(\pm\pi\) branch cut do not create turning-rate spikes.

## Low-speed contract

Heading, curvature, and turning rate are unstable or undefined when speed approaches zero.

The API therefore exposes

\`min_speed\`

and

\`undefined_policy\`.

The default \`min_speed=0.0\` has a narrow meaning: only mathematically stationary samples are masked. It is **not** a package-selected scientific threshold.

If your measurement resolution makes near-zero velocity unreliable, choose a positive threshold explicitly and report it.

With:

\`undefined_policy="nan"\`

samples satisfying

\[
\|G'(t)\|\le v_{\min}
\]

remain missing. They are never converted to zero.

With:

\`undefined_policy="raise"\`

the function aborts and identifies affected curve/sample counts.

## No hidden stabilization

The geometry layer does not introduce:

- smoothing;
- interpolation;
- automatic rescaling;
- angle unwrapping;
- denominator epsilons;
- automatic low-speed thresholds;
- axis inversion.

Derivative noise therefore remains visible. If smoothing is scientifically justified, perform it explicitly upstream and retain it in provenance.

## Coordinate scaling is part of the estimand

Curvature and tortuosity are Euclidean geometric quantities. Their interpretation assumes the two selected axes are in commensurate spatial units.

This is especially important for coordinates normalized separately to screen width and height. A movement of \(0.1\) on normalized \(x\) and \(0.1\) on normalized \(y\) need not represent the same physical or visual-angle displacement on a non-square display.

If geometric interpretation matters, use an isotropic coordinate representation such as calibrated pixels with known geometry or degrees of visual angle.

## Tortuosity

The implemented whole-trajectory tortuosity is

\[
T
=
\frac{\text{observed path length}}
{\text{endpoint displacement}}.
\]

A straight trajectory has \(T=1\); more circuitous open paths have \(T>1\).

A closed path has zero endpoint displacement and therefore undefined tortuosity under this definition. The package does not add an epsilon or return infinity silently. Use \`undefined_policy="nan"\` or \`"raise"\` explicitly.

## Relation to eye-movement literature

Curvature is already established in eye-movement research, especially for saccades. Ludwig and Gilchrist (2002) compared multiple saccade-curvature measures and emphasized that different definitions capture different geometric properties. More recent reviews continue to treat direction and curvature as established oculomotor trajectory features.

Curved smooth-pursuit trajectories have also been studied experimentally; Ross et al. (2017) showed that pursuit responses can track target curvature over time.

The 0.31 contribution is therefore **not** "curvature has never been used in eye tracking." The package contribution is the provenance-aware treatment of heading, signed curvature, and turning rate as continuous functions that remain compatible with the existing functional-analysis architecture.

## Reporting checklist

Report:

- selected planar dimensions;
- coordinate system and whether horizontal/vertical units are commensurate;
- screen \(y\)-axis orientation if sign is interpreted visually;
- preprocessing and any upstream smoothing;
- derivative method;
- \`min_speed\`;
- \`undefined_policy\`;
- number/fraction of undefined samples;
- whether heading remained wrapped;
- curvature and turning-rate units;
- tortuosity definition and zero-displacement policy.

See the [worked example](../examples/trajectory-geometry.md), [mathematical reference](mathematical-reference.md#trajectory-geometry), [assumptions](assumptions.md), and [limitations](limitations.md).
