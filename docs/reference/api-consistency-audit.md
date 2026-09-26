# 0.55 public API consistency audit

This audit is deliberately conservative. Its purpose is to identify naming and
navigation pressure without using stabilization as a reason for a breaking
namespace redesign.

## Current public surface

At the 0.55 stabilization branch, `eyetrajectoriespy.__all__` contains **407**
public exports with no duplicate names.

Convention-shaped groups currently include:

| Convention | Public exports |
|---|---:|
| `fit_*` estimator entry points | 12 |
| `bootstrap_*` resampling entry points | 13 |
| `plot_*` plotting helpers | 66 |
| `*_frame` tabular extractors | 41 |
| `*_reporting_text` manuscript/reporting helpers | 57 |
| `*Result` analysis result classes | 82 |

All public names containing the reporting-helper convention use the
`*_reporting_text` suffix. The 0.55 canonical manifest is checked in CI for
duplicate workflow IDs, missing documentation and references to non-public
entry points.

## Consistencies to preserve

The mature inferential layers already show a useful pattern:

~~~text
fit_* -> bootstrap_* -> *_bands / inference -> *_frame -> plot_* -> *_reporting_text
~~~

The generalized and mixed-effects routes also use explicit
`participant_column`, preserve whole-participant resampling and expose
scientific choices as keyword arguments rather than selecting them silently.

New stochastic APIs should continue to use `random_state`; interval-producing
APIs should continue to use `confidence_level`.

## Historical patterns retained in 0.55

Not every scientific operation should be forced into a `fit_*` name.
Established domain operations such as `recurrence_matrix()`, `rqa_metrics()`,
`dynamic_time_warping_distance()`, `register_to_landmarks()` and
`summarise_fpca()` remain descriptive and are not renamed merely to satisfy a
prefix convention.

Likewise, 0.55 does not reorder historical positional arguments globally.
Doing so would create churn in examples and user scripts without changing the
scientific contract.

## Actions taken in 0.55

- define five canonical workflows instead of adding wrapper aliases;
- test that every canonical/advanced/diagnostic/experimental function named by
  the workflow manifest is an existing public API;
- document forward naming conventions;
- establish a deprecation window before future removals;
- separate the exhaustive capability inventory from the recommended entry path;
- use documentation hierarchy before considering namespace surgery.

## Deferred cleanup

Any future inconsistency selected for correction should receive an individual
migration record containing:

1. current public name/signature;
2. canonical replacement;
3. compatibility alias/warning behavior;
4. first deprecated version;
5. earliest eligible removal version;
6. affected docs/examples/tests.

No such removal is authorized by 0.55.
