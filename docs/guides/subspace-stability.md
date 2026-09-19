# Near-tied eigenvalues and FPCA subspace stability

Individual FPC labels can become unstable when adjacent eigenvalues are close.

That instability is not always evidence that the underlying low-dimensional functional structure has disappeared. Two nearby eigenfunctions can swap order, flip sign, or rotate within essentially the same eigenspace.

## Why individual matching can be misleading

Suppose FPC1 and FPC2 have similar eigenvalues. A bootstrap sample may return a rotated pair:

\[
\tilde\phi_1 = \cos(\theta)\phi_1 + \sin(\theta)\phi_2,
\qquad
\tilde\phi_2 = -\sin(\theta)\phi_1 + \cos(\theta)\phi_2.
\]

Each individual component can have only moderate similarity to its reference counterpart even though the span of the two functions is unchanged.

Use subspace diagnostics when the scientific interpretation concerns a block of nearly tied components.

## Step 1: inspect adjacent eigengaps

`fpca_eigenvalue_gap_table()` reports:

- adjacent retained eigenvalues;
- absolute gap;
- relative gap;
- next/current eigenvalue ratio.

```python
gaps = fpca_eigenvalue_gap_table(fit)
print(gaps)
```

The function does **not** label any pair as near-tied by default.

If your protocol pre-specifies a relative-gap threshold:

```python
gaps = fpca_eigenvalue_gap_table(
    fit,
    relative_gap_threshold=0.10,
)
```

The resulting `near_tie_flag` is a descriptive review flag under that explicit rule.

!!! important
    To inspect the gap at a proposed retention boundary, fit at least one component beyond that boundary. A fit containing only three FPCs cannot report the FPC3–FPC4 gap.

## Step 2: compare subspaces with principal angles

`compare_fpca_subspaces()` compares corresponding contiguous component blocks.

```python
comparison = compare_fpca_subspaces(
    reference_fit,
    candidate_fit,
    start_component=0,
    n_components=2,
)
```

The result includes:

- principal cosines;
- principal angles in degrees;
- Frobenius distance between projection operators;
- normalized projector distance in [0, 1].

A normalized projector distance of zero means the selected subspaces are identical, even if the individual basis functions inside that subspace have rotated.

## Step 3: bootstrap the eigenspace

```python
stability = bootstrap_fpca_subspace_stability(
    gaze,
    start_component=0,
    n_components=2,
    n_bootstrap=500,
    scaling="dimension_sd",
    resample_unit="participant",
    participant_column="participant_id",
    random_state=2026,
)
```

For repeated-trial designs, participant-level resampling usually matches the population sampling unit better than treating every trial as independent.

```python
summary = summarise_fpca_subspace_stability(stability)
print(summary)
plot_fpca_subspace_stability(stability)
```

Useful summaries include:

- median minimum principal cosine;
- distribution of the maximum principal angle;
- normalized projector distance.

## Individual stability versus subspace stability

Use both when needed.

| Pattern | Interpretation |
|---|---|
| high individual similarity + high subspace stability | component labels and span are both reproducible |
| low individual similarity + high subspace stability | labels may rotate/swap inside a stable eigenspace |
| low individual similarity + low subspace stability | the fitted functional structure itself is unstable |
| high individual similarity + low block stability | unusual; inspect the chosen block and implementation assumptions |

Do not rename rotated components across bootstrap samples merely to manufacture apparent label stability.

## Interpretation

High subspace stability supports the statement that the selected **functional span** is reproducible under the stated resampling scheme.

It does not prove:

- that each individual FPC is identifiable;
- that a psychological label belongs to a particular axis inside the subspace;
- that a chosen relative eigengap threshold has inferential meaning;
- that the same eigenspace generalizes to another stimulus population;
- equality of population eigenspaces.

## Reporting example

> The first two FPCs had closely spaced retained eigenvalues, so stability was evaluated both at the individual-component and two-dimensional subspace levels. Participant-level bootstrap refits were compared with the full-sample FPC1–FPC2 span using principal angles. The median minimum principal cosine was 0.97 and the median normalized projector distance was 0.08. These diagnostics were interpreted as descriptive evidence that the two-dimensional functional span was more stable than the orientation of the individual FPC axes.

## API links

- `fpca_eigenvalue_gap_table()`
- `compare_fpca_subspaces()`
- `bootstrap_fpca_subspace_stability()`
- `summarise_fpca_subspace_stability()`
- `plot_fpca_subspace_stability()`
- `fpca_eigengap_reporting_text()`
- `fpca_subspace_stability_reporting_text()`

## Methodological context

Eigenvalue spacing has a first-order effect on eigenfunction estimation uncertainty in FPCA. When eigenvalues are close, inference and interpretation of individual eigenfunctions require particular caution.

Principal angles provide a basis-invariant way to compare finite-dimensional subspaces, so rotations within the selected span do not create artificial instability.

- Hall P, Hosseini-Nasab M. *On Properties of Functional Principal Components Analysis*. JRSS B. 2006;68(1):109–126. doi:10.1111/j.1467-9868.2005.00535.x.
- Stewart GW, Sun J-G. *Matrix Perturbation Theory*. Academic Press; 1990.
