# Workflow reproducibility bundles

`export_workflow_bundle()` packages an **already computed** typed workflow result into an inspectable reproducibility directory. The exporter does not fit a model, run a diagnostic, create an inference target, choose a plot, or select a preferred analysis.

The intended direction is:

```text
analysis workflow
        -> typed result
        -> explicit optional tables/reports/figures
        -> workflow bundle
```

not:

```text
bundle export
        -> discover and execute more analysis
```

## Bundle layout

A bundle may contain:

```text
workflow.json
config.json
provenance.json
steps.json
environment.json

results/
    workflow-result/
        manifest.json
        arrays.npz

tables/
reports/
figures/
SHA256SUMS
```

The complete typed workflow result is delegated to the existing `export_portable_result()` JSON + NPZ format. W1 does not invent a second scientific-result serialization mechanism.

## Integrity boundary

The bundle writer generates SHA-256 checksums for every retained payload file. `load_workflow_bundle()` verifies those hashes before loading the scientific result. Checksum paths are constrained to the bundle directory; absolute paths and parent-directory traversal fail closed.

The checksum mechanism is for scientific integrity and audit. It is not a digital signature or a security container.

## Environment provenance

By default the bundle captures the same software/platform provenance as `capture_environment()`. Set `include_environment=False` only when the caller deliberately wants to omit it.

Environment capture is descriptive. It is not a lockfile and does not claim that every dependency difference changes a scientific result.

## Optional exported surfaces

Tables, reports, and figures are explicit mappings supplied by the caller:

```python
from eyetrajectoriespy.workflows import export_workflow_bundle

export_workflow_bundle(
    result,
    "analysis-bundle",
    tables={"scores": score_frame},
    reports={"methods": methods_text},
    figures={"components": components_ax},
)
```

Those objects must already exist. W1 never calls plotting, reporting, diagnostic, inference, preprocessing, or model-selection functions implicitly.

Names are restricted to safe file components and are validated before any optional output is written.

## Schema policy

The current identities are:

```text
WORKFLOW_SCHEMA_VERSION = 1
WORKFLOW_BUNDLE_SCHEMA_VERSION = 1
```

Unknown future bundle or workflow schema versions fail closed. Each concrete workflow also has a stable semantic contract identifier such as `sparse_fpca:v1`.

This separates three reproducibility identities: package version, workflow semantic contract, and workflow-bundle storage schema. They may evolve on different schedules and must not be conflated.
