---
title: Release status
description: Published eyetrajectoriespy 1.1.0 versus unreleased 1.2 development source and research qualification blockers.
---

# Release status

!!! success "Current published version: 1.1.0"
    Install with `pip install eyetrajectoriespy==1.1.0`. Supported Python range: 3.11–3.13. [Release notes](../releases/1.1.0.md) · [PyPI](https://pypi.org/project/eyetrajectoriespy/) · [Stable API](../reference/api.md).

!!! warning "1.2 is not released"
    The 1.2 research and workflow source does **not** represent a published GitHub Release or PyPI version. The previous 1.2.0rc1 qualification record and the new literal 1.2.0rc2 candidate are separate. RC2 exact-version qualification is in progress, and neither candidate has been published.

| Area | Status | Source |
| --- | --- | --- |
| Public stable installation | **1.1.0** | [Stable release notes](../releases/1.1.0.md) |
| 1.1 sparse/irregular additions | Qualified stable module-scoped APIs | [Module API](../reference/one-dot-one-module-api.md) |
| Ten orchestrated `run_*_workflow()` routes | Unpublished candidate | [Workflow boundary](../workflows/workflow-orchestration.md) |
| W3 nominal-90% whole-functional inference | **Not generally calibrated** | [Interpretation](../articles/interpreting-w3-coverage-and-source-audits.md) · [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) |
| Response-dependent missing gaze | **Not field-identified** | [R93](../articles/w3-r93-exact-observed-law-nonidentification.md) · [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) |
| Experimental GitHub Release / PyPI promotion | **Disarmed / HOLD** | [Development evidence](../development/research-development-hub.md) |

A passing documentation deployment checks that the *website builds and publishes*, not that inference claims have gained scientific qualification. Review [evidence versus release qualification](../articles/evidence-vs-qualification.md) before citing research stages.
