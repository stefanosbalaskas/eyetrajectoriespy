# Sparse planar MFPCA / joint-PACE reproducibility case study

This is the canonical post-0.12 reproducibility case study for
`eyetrajectoriespy`. It exercises the public native sparse planar workflow from
long-format gaze samples to manuscript-oriented reporting, deterministic
figures and a portable scientific result.

The dataset is a **deterministic synthetic gaze surrogate**, not empirical human
data. It preserves a realistic sparse/irregular observation pattern, normalized
screen coordinates, seconds, participant IDs and paired x/y observations while
remaining unambiguously redistributable.

## Scientific question

Can jointly observed sparse planar gaze be represented without interpolating
raw trajectories to a common grid, while estimating the full x/y covariance
structure and obtaining joint PACE scores that remain reportable and portable?

The case study follows:

```text
long-format paired sparse x/y samples
    -> from_irregular_long_dataframe_native()
    -> fit_sparse_mfpca()
    -> joint-PACE score diagnostics
    -> score frame + reporting text
    -> deterministic public plots
    -> portable JSON + NPZ scientific snapshot
```

No private estimator, recovery or simulation API is used in the analysis.

## Reproduce from a fresh checkout

From the repository root:

```bash
python -m pip install -e .
python case_studies/sparse_mfpca_0_12/generate_data.py
python case_studies/sparse_mfpca_0_12/run.py \
  --output-dir build/case-study-sparse-mfpca-0.12
```

The data generator must produce:

```text
sha256:9f1305c91c03aa188ad5535c901eb8140ae4553e92a63eb10569ccbcbaf30bf7
```

for `data/input_long.csv`. Any change is treated as a changed case-study input,
not silently accepted.

## Expected evidence

`run.py` verifies the scientific invariants in `expected.json` and writes:

```text
build/case-study-sparse-mfpca-0.12/
├── component-1.svg
├── covariance-blocks.svg
├── score-diagnostics.svg
├── scores.csv
├── reporting.txt
├── summary.json
├── environment.json
└── portable-result/
    ├── arrays.npz
    └── manifest.json
```

The frozen observation contract expects 409 rows from 36 curves, 9–14 native
observations per curve, two retained joint components, 36/36 successful joint
PACE score systems, finite scores, no raw interpolation and no nonportable
fields in the `SparseMFPCAResult` snapshot.

The reference eigenvalues are checked with declared numerical tolerances rather
than byte equality. The figures are generated through the public
`plot_sparse_mfpca_*` APIs; their existence is part of the case-study contract,
but their SVG bytes are not used as a numerical estimator oracle.

## What the case study does not claim

- The surrogate is not evidence about a particular empirical population.
- The fitted bandwidths are declared analysis settings, not automatically
  selected optimal bandwidths.
- Successful execution is not a claim that every future dataset will satisfy
  the sparse-MFPCA observation contract.
- The case study does not manufacture a new plotting API or estimator merely
  for symmetry.

## Provenance

`provenance.json` records the exact successful product-observation workflow,
retained artifact digest and branch head from which this case study was frozen.
`reference_environment.json` records the Python, dependency and platform state
of that successful observation. Every rerun also captures its own environment
in the output directory.

## Citation

Use the metadata in `CITATION.cff`, cite `eyetrajectoriespy`, and include the
immutable release/tag or repository commit used for the analysis. When the
case study is discussed as evidence, identify it as the **sparse planar MFPCA /
joint-PACE reproducibility case study** and state that the bundled gaze data are
synthetic.
