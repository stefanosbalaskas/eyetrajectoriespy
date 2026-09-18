# Failure cases you should see

A scientific package should fail visibly when assumptions are unresolved.

## Long missing interval

If a long gap remains after explicit resampling, `fit_fpca()` raises an error rather than imputing it.

## Duplicate timestamps

`from_long_dataframe()` refuses duplicate times within a curve. Decide upstream whether they are duplicates, simultaneous binocular samples, or another data structure.

## Mismatched layouts

The package cannot know that `(0.8, 0.2)` means “source card” in one stimulus and “decorative image” in another. Coordinate harmonization requires substantive design knowledge.

## Constant channel + variance scaling

A constant functional dimension cannot be standardized to unit integrated variance and triggers an error.

## Automatic registration

There is no automatic registration step. Define landmarks or explicitly call an elastic workflow.
