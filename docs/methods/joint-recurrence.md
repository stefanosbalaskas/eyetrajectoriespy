# Joint recurrence analysis

Version 0.39 adds synchronized **joint recurrence plots (JRPs)** and joint RQA
for cases where several simultaneously observed systems should each recur at
the same time pair.

This is not cross-recurrence.

- **Cross-recurrence** asks whether a state in system A resembles a state in
  system B.
- **Joint recurrence** asks whether system A recurs within its own state space
  **and** system B recurs within its own state space at the same pair of time
  indices.

## Definition

For subsystem auto-recurrence matrices \(R^{(s)}\),

$$
JR_{ij}
=
\prod_{s=1}^{S}R_{ij}^{(s)}.
$$

Because the component matrices are binary, the product is an elementwise
logical AND.

Each subsystem may use a different:

- state dimension;
- coordinate/state variables;
- distance metric;
- fixed radius or target-recurrence-rate policy.

Those contracts remain visible rather than being forced into one pooled state
space.

## Build the component recurrences first

~~~python
from eyetrajectoriespy import recurrence_matrix

gaze_rec = recurrence_matrix(
    gaze,
    curve="trial_01",
    dimensions=("x", "y"),
    target_recurrence_rate=0.08,
    metric="euclidean",
    theiler_window=10,
)

pupil_rec = recurrence_matrix(
    pupil,
    curve="trial_01",
    dimensions=("pupil",),
    target_recurrence_rate=0.10,
    metric="cityblock",
    theiler_window=10,
)
~~~

The same Theiler window is required for every component because it defines the
joint eligible-pair denominator.

## Construct the joint recurrence plot

~~~python
from eyetrajectoriespy import joint_recurrence_matrix

joint = joint_recurrence_matrix(
    (gaze_rec, pupil_rec),
    labels=("gaze_state", "pupil_state"),
)
~~~

The function requires:

- at least two component recurrences;
- auto-recurrence inputs only;
- identical square matrix shapes;
- the exact same time grid;
- the same Theiler window.

It does not silently:

- interpolate or resample;
- shift one system in time;
- align lags;
- choose a shared radius;
- force a common recurrence rate;
- rebuild the component recurrences.

## Joint recurrence rate

With one shared set of eligible unordered time pairs,

$$
\mathrm{JRR}
=
\frac{\sum_{i<j}JR_{ij}}{N_{\mathrm{eligible}}}.
$$

Because joint recurrence is an intersection, JRR cannot exceed the recurrence
rate of any component when all components share the same eligible-pair
denominator.

## Inspect component contracts

~~~python
from eyetrajectoriespy import joint_recurrence_component_frame

components = joint_recurrence_component_frame(joint)
print(components)
~~~

The table retains each component's metric, radius, target recurrence rate,
achieved recurrence rate, state dimension, and Theiler window.

## Joint RQA

~~~python
from eyetrajectoriespy import joint_rqa_metrics

jrqa = joint_rqa_metrics(
    joint,
    min_diagonal_length=2,
    min_vertical_length=2,
)
~~~

The package applies the same line-counting conventions used by ordinary
auto-RQA to the joint matrix. Thus JDET, JLAM, line lengths, entropy, trapping
time, and CORM are summaries of **coincident recurrence structure**.

Line-based JRQA inherits the existing approximately regular-grid requirement.
The spatial joint recurrence matrix can be constructed independently of that
line-metric assumption.

## Plot

~~~python
from eyetrajectoriespy import plot_joint_recurrence

ax = plot_joint_recurrence(joint)
~~~

The plot remains sparse and refuses silent point subsampling when
`max_points` is exceeded.

## Interpretation

Appropriate wording is:

> Gaze and pupil state spaces showed recurrent configurations at the same time
> pairs under their separately declared recurrence thresholds.

Do not translate JRR or JDET directly into:

- causal influence;
- direction of information flow;
- transfer entropy;
- synchronization strength without a separately justified synchronization
  model;
- evidence that the two systems occupy similar states.

The component systems need not even have the same state dimension. Joint
recurrence concerns simultaneity of their *own* recurrence events.

## Threshold choice

Joint recurrence does not eliminate threshold sensitivity. If each component
uses a target recurrence rate, the joint analysis is conditioned on those
component-level density constraints. If fixed radii are used, JRR remains
conditional on those radii.

Use the existing recurrence-threshold and RQA-sensitivity tools where needed.
Version 0.39 does not optimize thresholds to maximize joint recurrence.

## Reporting

Report:

- every component state representation;
- metric and radius policy for every component;
- achieved component recurrence rates;
- common time grid and sampling interval;
- shared Theiler window;
- number of eligible unordered pairs;
- JRR;
- JRQA line thresholds and line metrics if used;
- that the JRP was the logical intersection of component auto-recurrence
  matrices;
- whether thresholds were fixed or target-rate based;
- that no lag alignment or threshold harmonization was performed.

## Evidence basis

Romano et al. (2004) introduced multivariate recurrence plots based on joint
recurrences of the individual systems. Marwan et al. (2007) review recurrence
plot methodology and distinguish recurrence-based constructions used for
interrelated systems. Later multidimensional RQA work has continued to treat
joint recurrence as the intersection of subsystem recurrence matrices rather
than as cross-recurrence.

eyetrajectoriespy 0.39 does not claim methodological novelty for JRPs. The
package contribution is a fail-closed, provenance-preserving implementation
that keeps each component recurrence contract explicit and reuses the package's
already documented RQA line conventions.
