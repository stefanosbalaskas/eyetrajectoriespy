# Portable scientific results and environment capture

Version 0.57 defines a **portable scientific result** as an explicit snapshot of
scientifically consequential state rather than a promise that arbitrary Python
backend objects can be unpickled forever.

## Portable scope

\`export_portable_result()\` writes a directory containing:

- \`manifest.json\`: schema version, result type, package version, units,
  provenance structure, environment capture and explicit nonportable fields;
- \`arrays.npz\`: numerical/string array payload with a SHA-256 checksum.

The portable scope includes scientific arrays, identifiers, specifications,
units, diagnostics and provenance. Backend-native fitted objects such as
statsmodels/sklearn/scikit-fda model instances are **not** promised portable.
When encountered, they are represented by an explicit nonportable marker and
their field paths are retained in \`nonportable_fields\`; they are never silently
discarded.

~~~python
from eyetrajectoriespy import export_portable_result, load_portable_result

export_portable_result(fit, "analysis-result")
snapshot = load_portable_result("analysis-result")

print(snapshot.result_type)
print(snapshot.nonportable_fields)
~~~

Loading verifies the array checksum and schema version. It returns a
\`PortableScientificResultSnapshot\`, not a reconstructed fitted estimator.
That distinction prevents a JSON/NPZ archive from pretending to preserve
backend optimizer internals that may change across dependency versions.

## Environment capture

\`capture_environment()\` records:

- eyetrajectoriespy version;
- Git commit when available;
- Python version, implementation and executable;
- OS/platform/machine/processor information;
- core dependency versions;
- presence/version of scikit-fda, FDApy and fdasrsf;
- numerical thread environment variables.

~~~python
from eyetrajectoriespy import capture_environment

environment = capture_environment()
~~~

Environment capture is descriptive provenance. It is not a lockfile and does
not claim that every environment difference changes the scientific result.

## Compatibility policy

Portable schema version 1 is explicit and fail-closed:

- the loader accepts schema version 1;
- unknown future schema versions raise rather than being guessed;
- source and current package versions are retained separately;
- cross-version loading is allowed as a scientific snapshot but
  \`package_version_match\` makes the mismatch visible;
- exact reconstruction of opaque backend objects is outside the schema.

If a future release changes the portable schema, it must either preserve a
reader for schema 1 or provide a documented migration utility before removing
that reader.

## Integrity boundary

The NPZ payload checksum detects accidental or intentional modification of the
scientific arrays after export. The manifest itself should be retained with the
analysis/reproducibility bundle and version-controlled or archived through the
research workflow where appropriate.

The format is designed for scientific audit and transport, not as a security
container or digital signature.
