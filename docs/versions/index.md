---
title: Documentation versions and frozen source references
description: Current stable 1.2.0 docs, historical release notes and immutable GitHub tag sources.
---

# Documentation versions

**Current online documentation:** published stable 1.2.0, Python 3.11–3.13. The web pages follow the protected main branch, so their **content may receive corrections after a release**. Treat exact tag source as the authoritative historical snapshot.

| Version | Status | Documentation / source provenance |
| --- | --- | --- |
| **1.2.0** | Current stable | [Current docs](../start/index.md) · [1.2.0 release notes](../releases/1.2.0.md) · [Immutable source at v1.2.0](https://github.com/stefanosbalaskas/eyetrajectoriespy/tree/v1.2.0/docs) |
| **1.2.0rc2** | Historical prerelease | [Release notes](../releases/1.2.0rc2.md) · [Tagged source](https://github.com/stefanosbalaskas/eyetrajectoriespy/tree/v1.2.0rc2/docs) |
| **1.1.0** | Previous stable | [Release notes](../releases/1.1.0.md) · [Tagged source](https://github.com/stefanosbalaskas/eyetrajectoriespy/tree/v1.1.0/docs) |
| **1.0.0** | Older stable | [Release notes](../releases/1.0.0.md) · [Tagged source](https://github.com/stefanosbalaskas/eyetrajectoriespy/tree/v1.0.0/docs) |

!!! info "What is, and is not, versioned"
    This index provides **release-indexed documentation and immutable tagged documentation sources**; it does **not** claim that separate full MkDocs sites are hosted at /1.1.0/ or /1.2.0/. Deep links to the current site may reflect later documentation maintenance. For historical behavior, install the exact wheel and consult the corresponding tagged source and release notes.

## Version compatibility

- The frozen 1.0 root API compatibility boundary remains an explicit contract.
- The 1.1 release added qualified module-scoped sparse/irregular methods.
- 1.2.0 made ten W1–W4 module-scoped workflow orchestration routes stable. E1–E4 remain experimental.
- Issues [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) remain scientific limitations, not archived release announcements.

[Stable API](../reference/api-stability.md) · [Release process](../release-process.md) · [Reproducibility guide](../reproducibility/checklist.md)
