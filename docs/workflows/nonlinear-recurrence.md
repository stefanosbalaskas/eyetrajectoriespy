# Nonlinear and recurrence trajectory analysis

Use this route when the scientific target is recurrence, state-space structure
or nonlinear temporal organization rather than a mean trajectory or predictor
coefficient function.

## 1. Define the state representation first

Choose the observed/derived state and, when reconstruction is required, declare
embedding dimension $m$, delay $\tau$, Theiler exclusion and any scaling
before computing recurrence quantities.

## 2. Start with a declared recurrence specification

~~~python
recurrence = recurrence_matrix(
    trajectory,
    embedding_dimension=3,
    delay=2,
    radius=0.5,
    theiler=1,
)

metrics = rqa_metrics(recurrence)
~~~

The package does not optimize the radius, embedding or line-length parameters
to obtain a preferred result.

## 3. Inspect specification sensitivity

Use recurrence-radius diagnostics and
`rqa_parameter_sensitivity()` when multiple defensible specifications are
scientifically relevant. Sensitivity results are descriptive robustness
evidence, not an automatic selector.

## 4. Preserve the resampling unit

Population RQA uncertainty resamples complete independent curves or
equal-weight participant summaries; overlapping window rows must not be treated
as independent observations.

## 5. Report interpretation boundaries

Use `rqa_reporting_text()`. Report state construction, embedding, threshold,
Theiler window, line-length definitions, windowing/dependence where applicable,
and the resampling unit.

### Experimental branches

Transfer entropy, conditional transfer entropy, surrogate nonlinearity tests,
largest-Lyapunov estimation and empirical return-map stability have stronger
method-specific interpretation restrictions. They are available, but are not
the default starting point for nonlinear analysis. In particular, positive LLE
is not proof of chaos and transfer entropy is not causal identification.
