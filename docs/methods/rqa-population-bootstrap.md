# Population uncertainty for RQA summaries

Version 0.28 adds uncertainty for **population-average curve-level RQA metrics** while preserving the study's independent sampling unit.

This is intentionally narrower than a generic "bootstrap RQA" claim.

## Estimand

For source curve \(i\), selected RQA metric \(q\), and one fixed recurrence specification \(\theta\),

\[
M_{iq}=Q_q\{R_i(\theta)\}.
\]

With independent curves, the target is the equal-weight mean of the curve-level summaries.

With repeated trials nested within participant \(p\), the package first computes

\[
U_{pq}
=
\frac{1}{m_p}
\sum_{j=1}^{m_p}
M_{pjq},
\]

then bootstraps the participant means. Participants therefore receive equal inferential weight even when trial counts differ.

## API

~~~python
from eyetrajectoriespy import bootstrap_rqa_metric_means

fit = bootstrap_rqa_metric_means(
    gaze,
    dimensions=("x", "y"),
    metrics=("determinism", "laminarity", "trapping_time"),
    radius=0.08,
    theiler_window=0.05,
    theiler_window_units="seconds",
    min_diagonal_length=2,
    min_vertical_length=2,
    unit="participant",
    participant_column="participant_id",
    confidence_level=0.95,
    n_bootstrap=2000,
    random_state=42,
)
~~~

The result retains four tables:

- `observed_table`: one RQA row per source curve, including solved radius/RR audit information;
- `unit_table`: the actual independent bootstrap units;
- `bootstrap_table`: one population-mean vector per bootstrap replicate;
- `summary_table`: observed mean, bootstrap mean/bias/SE, and percentile interval for each selected metric.

## Fixed specification means fixed specification

The recurrence/RQA contract is held fixed across the analysis:

- state variables;
- optional delay embedding;
- embedding dimension and delay;
- fixed radius or target recurrence rate;
- distance metric;
- Theiler window;
- minimum diagonal length;
- minimum vertical length.

The bootstrap does not search over those values and does not propagate uncertainty created by choosing them from the same data.

Use `rqa_parameter_sensitivity()` separately when robustness to defensible analysis choices is scientifically important.

## Why curve-level RQA is computed once

For an observed curve and one fixed RQA specification, RR, DET, LAM and related metrics are deterministic summaries.

Repeating the exact same RQA computation every time that curve is drawn in an ordinary nonparametric bootstrap would reproduce the same number. Version 0.28 therefore computes each curve-level RQA summary once, then resamples the **independent units** whose population distribution is the inferential target.

This is not a shortcut around within-series uncertainty; it defines a different estimand.

## What this bootstrap does not estimate

The method does **not** estimate:

- uncertainty of RQA for one single observed trajectory;
- uncertainty from recurrence-line construction inside a trajectory;
- uncertainty from temporal autocorrelation through moving/block resampling;
- tracker/calibration/preprocessing measurement uncertainty;
- uncertainty from choosing embedding, radius, Theiler, or line thresholds;
- uncertainty from post-hoc metric selection;
- participant-by-trial hierarchical resampling.

Schinkel et al. developed recurrence-based bootstrap confidence bounds for time-series recurrence measures. That literature establishes bootstrap precedent for RQA, but its within-series target is distinct from the population-unit bootstrap implemented here.

For repeated experimental gaze designs, resampling the genuinely independent subjects while preserving/aggregating their within-subject structure is the more direct contract for a population mean across participants.

## Participant mode

Use participant-level inference when trials are nested in participants and participant is the independent sampling unit:

~~~python
fit = bootstrap_rqa_metric_means(
    gaze,
    dimensions=("x", "y"),
    metrics=("determinism", "laminarity"),
    radius=0.08,
    unit="participant",
    participant_column="participant_id",
    n_bootstrap=2000,
)
~~~

The package computes each trial's RQA first, then averages the selected trial-level RQA metrics within participant.

It does **not** pool all trials before constructing one participant recurrence plot, because that would change the recurrence object and scientific estimand.

It also does not bootstrap trials within participant. The current interval therefore reflects between-participant sampling uncertainty of participant-average curve-level RQA metrics, conditional on the observed trial set for each participant.

## Target recurrence rate

When `target_recurrence_rate` is used, each curve can require a different solved radius to attain the declared recurrence density.

Those solved radii and achieved recurrence rates are retained in `observed_table`.

Because recurrence density is controlled by design, `recurrence_rate` cannot be selected as a bootstrap outcome in target-RR mode.

## Undefined metrics fail closed

Some RQA metrics are undefined when a curve contains no qualifying line structures.

If a requested metric is undefined for any source curve, the analysis raises and identifies the curve. It does not:

- delete that curve;
- replace missing with zero;
- silently switch line thresholds;
- choose a different radius;
- compute the bootstrap on only the convenient units.

A different scientifically justified specification must be declared explicitly.

## Interval

For bootstrap replicate \(b\), if \(I_1^{(b)},\dots,I_n^{(b)}\) are sampled independent-unit indices,

\[
\bar U_q^{*(b)}
=
\frac{1}{n}
\sum_{r=1}^{n}
U_{I_r^{(b)}q}.
\]

Version 0.28 reports a percentile interval,

\[
\left[
Q_{\alpha/2}(\bar U_q^*),
Q_{1-\alpha/2}(\bar U_q^*)
\right].
\]

The result also retains bootstrap bias and bootstrap standard error.

Percentile intervals are not guaranteed to contain the observed point estimate in every finite sample; the software does not impose such a condition.

## Plotting

~~~python
from eyetrajectoriespy import plot_rqa_metric_mean_bootstrap

ax = plot_rqa_metric_mean_bootstrap(fit)
~~~

The figure shows one point and percentile interval per selected RQA metric.

## Interpretation

A 95% interval for participant-level mean DET should be phrased as uncertainty in the **population mean of participant-average curve-level DET under the declared RQA specification**.

It should not be phrased as:

- "95% certainty that this participant's true DET lies here";
- uncertainty in a latent chaos parameter;
- uncertainty corrected for parameter tuning;
- uncertainty for every time point in a windowed RQA function.

For the last problem, use the separate functional-RQA mean-band workflow.

## Reporting

Report the complete recurrence specification, selected RQA metrics, independent resampling unit, participant column if applicable, number of independent units, trial counts per participant, bootstrap replicate count, seed, confidence level, interval type, observed means, intervals, and the explicit scope boundary excluding within-single-trajectory and parameter-selection uncertainty.

See the [worked example](../examples/rqa-population-bootstrap.md), [limitations](limitations.md), [pre-registration checklist](preregistration.md), and [mathematical reference](mathematical-reference.md#rqa-population-bootstrap).
