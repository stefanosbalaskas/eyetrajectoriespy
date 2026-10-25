---
title: Integration roadmap and release boundaries
description: Prioritized optional Python package interoperability candidates and scientific qualification gates.
---

# Qualifying future integrations

This roadmap is not a commitment to new dependencies or a claim of stable compatibility.

| Priority | Integration | Qualification before adding a supported API |
| --- | --- | --- |
| 1 | pandas / Polars / PyArrow | **Example exists**; qualify null/dtype parity, large-file behavior and version/platform matrix |
| 2 | pymovements sample and event handoff | **Pinned 0.28.0 synthetic-object preview implemented**; still requires real-device fixtures, upstream version compatibility, trial/time mapping and detector provenance to qualify a stable API |
| 3 | Pandera optional schema checks | Explicit nullable rules, strict failure contracts and no silent coercion or missing-row filtering |
| 4 | Eye-Tracking-BIDS reading | **Read-only JSON/TSV.GZ shape preview implemented**; still requires full version-pinned BIDS conformance, sidecar inheritance, recorded-eye and event validations |
| 5 | PyNeon mobile recordings | Native/cloud format fixtures, synchronization and coordinate provenance |
| 6 | eyekit/PupEyes | Real reading/pupil fixtures, separate raw/derived modalities and clock contracts |
| 7 | scikit-fda/FDApy independent references | Matched estimands, support, simulation-law and numerical tolerance audits |

### Optional Python plugin architecture

Later, versioned [Python entry points](https://packaging.python.org/en/latest/specifications/entry-points/) could register independent data adapters. Entry points should declare the external package/version, source format, coordinate and time metadata, and explicit fail-closed rejection. They must not monkey-patch root APIs, silently install heavy dependencies, or imply valid confidence bands. **No plugin registry or new package extra is introduced here.**

A compatibility smoke test or an upstream release is not scientific inference qualification. The 1.2.0 API and open W3 scientific exclusions remain unchanged.

[API stability](../reference/api-stability.md) · [Research evidence](../research/index.md) · [Tabular example](tabular-handoff.md)
