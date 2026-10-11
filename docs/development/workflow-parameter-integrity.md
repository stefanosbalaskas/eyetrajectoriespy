# Development 1.2: preserving analyst-declared integer parameters

!!! warning "Development contract, not a release qualification"
    This is an unpublished `1.2.0rc2.dev0` workflow validation improvement.
    Published 1.1.0 estimator implementations and production readiness remain unchanged.

## Scientifically material defect

The W2 sparse workflow constructors previously allowed `n_components=1.9`
and silently converted it to 1. Similar implicit truncation affected
participant/trial component counts and W4 recurrence minimum line lengths.
The recorded specification consequently differed from what an analyst supplied.

## Contract after hardening

The affected seven W2/W4 fields now require positive **Python or NumPy
integer types**, rejecting fractional floats, integral-valued floats,
strings, booleans and nonfinite values rather than coercing them.
The accepted NumPy integers are converted to ordinary Python integers only
*after* validation, which preserves JSON/audit representation.

```python
from eyetrajectoriespy.workflows import RecurrenceWorkflowConfig
valid = RecurrenceWorkflowConfig(
    curve=0, dimensions=("x",), embedding_dimension=2,
    delay=2, radius=0.15, min_diagonal_length=3,
)
```

An attempted `min_diagonal_length=2.9` now raises a clear `ValueError`
instead of silently becoming 2. The positive regression suite must continue
to pass on all supported Python and operating-system combinations.

This change does not introduce a new estimator, select parameters automatically,
assert known-truth recovery, validate uncertainty, or change Bayesian/F5
research gates. Next development stages should improve workflow-level
known-truth tests, real eye-tracking examples, interpretive visualizations
and end-to-end reporting.

**Stable 1.1.0 remains published; 1.2 remains in development.**
