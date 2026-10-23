# RC2 E5 content decision for independent review — 23 October 2026

**Decision requested, not granted. No GitHub tag, GitHub Release or PyPI upload is authorized by this change.**

## Source-specific technical evidence

The literal `1.2.0rc2` candidate was merged via [PR #471](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/471) at commit `9891feee6e5daa638a9de5cada295482a5fa4884`, following 33/33 exact-head checks. The main commit passed 30/30 exact-main workflow runs, zero failures.

Critically, [experimental-workflow-expansion run #40002802440](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/40002802440) finished successfully for **Python 3.11, 3.12 and 3.13**. Each E1–E4 job passed boundary audits, robustness tests, synthetic end-to-end exercise and building/testing an out-of-checkout candidate wheel. Those checks are software/package evidence, **not** statistical coverage, field validity or API stability evidence.

## Decision proposed

Allow the candidate wheel and sdist to include `eyetrajectoriespy.workflows.experimental` and its **12 E1–E4 importable helpers**, on the strict condition that they are presented as unstable **experimental prerelease interfaces**. This does not promote any of them into the ten supported `eyetrajectoriespy.workflows` route contracts or into the package root. Maintain the prior frozen root boundary of 455 stable plus three explicitly experimental exports.

These helpers offer opt-in preprocessing, quality preflight, descriptive sensitivity and evidence-based reporting. None is a validated solution to response-dependent/MNAR gaze loss or provides calibrated 90% functional-inference coverage.

The other permissible choice is to **exclude** the module from the release distribution and redo exact-source qualification of a changed wheel/sdist. A prose-only exclusion is insufficient because the module is importable in the candidate distribution.

## Independent review required

A human reviewer must explicitly approve the proposed experimental classification and the ten-route claims boundary before a separate publication-arming PR. Specifically review:

1. Importability and non-stability of all 12 helper names, with no root or supported-workflow promotion.
2. Accurate scientific exclusions for open [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296); retain all negative results.
3. Provenance of the literal RC2 candidate and three independent Python-version E5 jobs.
4. Explicitly documented version `1.2.0rc2` as a **prerelease**, not final stable 1.2.0.

The machine-readable `E5_RC2_CONTENT_REVIEW.json` and `scripts/validate_e5_rc2_content_review.py` enforce that the evidence is unchanged and **every authorization flag remains false**. These checks cannot impersonate a human reviewer. Once reviewed, the scope decision must be recorded in a *separate* governance transition, with fresh exact-main CI and the required `pypi` environment approval. The actual `release.yml` manual `workflow_dispatch target=production` is outside the connected GitHub tool's capabilities.

**Review status: PENDING. Current public release: 1.1.0.**
