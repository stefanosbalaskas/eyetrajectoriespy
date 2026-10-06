from pathlib import Path
import json

OLD = "1.1.0rc1"
NEW = "1.1.0"


def replace(path, old, new, *, count=None):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if old not in text:
        raise SystemExit(f"expected token not found in {path}: {old!r}")
    if count is not None and text.count(old) != count:
        raise SystemExit(f"unexpected token count in {path}: {text.count(old)} != {count}")
    p.write_text(text.replace(old, new), encoding="utf-8")


replace("pyproject.toml", 'version = "1.1.0rc1"', 'version = "1.1.0"', count=1)
replace("src/eyetrajectoriespy/__init__.py", '__version__ = "1.1.0rc1"', '__version__ = "1.1.0"', count=1)
replace("CITATION.cff", "version: 1.1.0rc1", "version: 1.1.0", count=1)

for name in ("CANONICAL_WORKFLOWS.json", "REFERENCE_VALIDATION.json", "VALIDATION_TOLERANCES.json"):
    p = Path(name)
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("package_version") != OLD:
        raise SystemExit(f"{name} package_version was not {OLD}")
    data["package_version"] = NEW
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

readiness_path = Path("RELEASE_READINESS.json")
readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
if readiness.get("current_development_version") != OLD:
    raise SystemExit("unexpected current_development_version")
readiness["current_development_version"] = NEW
readiness["production_release_ready"] = False
readiness["github_release_ready"] = False
additions = [
    "Installed 1.1.0rc1 observation PR #200 merged as exact protected-main commit 3a8f8a47647ed2c4cee5121713e0c67afc65ae72. The complete post-merge exact-main observation matrix finished 24/24 workflow groups successfully with zero failures, including the exact external mGSFPCA comparator.",
    "Exact-main installed-RC workflow run 37526057779 reinstalled production-PyPI 1.1.0rc1 on Python 3.11-3.13 and passed installed-distribution separation, recovery, threshold-free stress, external-consumer observation, sparse-MFPCA observation, the complete installed 1.1 end-to-end product analyses, evidence-contract verification, and checksum capture.",
    "Canonical exact-main installed observation artifact 11442785076 has digest sha256:aba9dc71c2e2bc5d5f198f2b6c4709e1b21acc4e880435b081c678e1f7ae917e.",
    "Final 1.1.0 is a version-only promotion of the frozen, production-observed 1.1.0rc1 scientific/API surface. No estimator, numerical method, scientific default, dependency, deprecation, removal, threshold, or public API expansion is introduced during final qualification.",
    "The immutable 1.1.0rc1 package-wide performance envelope remains archived under validation/performance/PERFORMANCE_ENVELOPE-1.1.0rc1.json and must not be relabelled as final-version evidence.",
    "Final 1.1.0 qualification requires fresh exact-version package-wide and sparse-MFPCA performance evidence, the complete pull-request matrix, protected-main merge, and the complete exact-main matrix before publication may be armed.",
    "Publication remains jointly disarmed during final 1.1.0 qualification. Arming GitHub/PyPI publication is reserved for a later governance-only reviewed change after exact-main final-version qualification passes.",
]
for note in additions:
    if note not in readiness["notes"]:
        readiness["notes"].append(note)
readiness_path.write_text(json.dumps(readiness, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

replace("tests/test_public_api.py", 'assert et.__version__=="1.1.0rc1"', 'assert et.__version__=="1.1.0"', count=1)
replace("tests/test_qualification_ledgers.py", 'QUALIFIED_EVIDENCE_VERSION = "1.1.0rc1"', 'QUALIFIED_EVIDENCE_VERSION = "1.1.0"', count=1)
replace("tests/test_release_hardening.py", 'CURRENT_DEVELOPMENT_VERSION = "1.1.0rc1"', 'CURRENT_DEVELOPMENT_VERSION = "1.1.0"', count=1)

roadmap = Path("docs/methods/status-roadmap.md")
text = roadmap.read_text(encoding="utf-8")
old_line = "The current release-candidate line is **1.1.0rc1**. It is a non-published source identity under exact-version qualification and does not alter the immutable `1.0.0` production artifacts or frozen 1.0 qualification records."
new_line = "The current development line is **1.1.0**. It is a version-only final-promotion candidate over the frozen, production-observed `1.1.0rc1` scientific/API surface. `1.0.0` remains the stable production release until final publication succeeds."
if old_line not in text:
    raise SystemExit("status-roadmap current-line contract not found")
text = text.replace(old_line, new_line)
old_r5 = "5. **R5 — RC decision and literal-version qualification:** RC entry approved; exact-`1.1.0rc1` qualification is in progress. Publication remains a separate later governance step."
new_r5 = "5. **R5 — RC/final decision and literal-version qualification:** RC qualification, publication, and production-installed observation are complete; exact-`1.1.0` final qualification is now in progress. Publication remains a separate later governance step."
if old_r5 not in text:
    raise SystemExit("status-roadmap R5 line not found")
roadmap.write_text(text.replace(old_r5, new_r5), encoding="utf-8")

release_page = Path("docs/releases/1.1.0.md")
if release_page.exists():
    raise SystemExit("docs/releases/1.1.0.md already exists")
release_page.write_text("""# eyetrajectoriespy 1.1.0

**Final 1.1 release — under exact-version qualification**

`1.1.0` is a version-only promotion candidate over the frozen, production-observed `1.1.0rc1` scientific/API surface. This tranche does **not** add or change an estimator, numerical method, scientific default, dependency, deprecation, removal, threshold, public export, or root-namespace contract.

## Promotion basis

The published `1.1.0rc1` candidate completed exact-version qualification, production publication, and production-installed observation before this final-version transition.

Observation PR #200 merged as exact protected-main commit `3a8f8a47647ed2c4cee5121713e0c67afc65ae72`. Its complete post-merge matrix finished **24/24 workflow groups successfully with zero failures**.

Exact-main installed-RC workflow `37526057779` installed production-PyPI `1.1.0rc1` on Python 3.11, 3.12, and 3.13. The deep observation passed installed-distribution separation, recovery, threshold-free stress, external-consumer portability, sparse-MFPCA observation, and the complete installed 1.1 end-to-end product analyses. Retained artifact `11442785076` has digest `sha256:aba9dc71c2e2bc5d5f198f2b6c4709e1b21acc4e880435b081c678e1f7ae917e`.

The final external sparse-MFPCA sensitivity run `37526057512` also passed on that exact main commit; both the native two-stage job and exact external `mGSFPCA` job completed successfully, including comparator installation, external execution, invariant sensitivity evaluation, contract verification, and evidence upload.

No release-blocking scientific, API, numerical, or installed-artifact defect is currently detected by the qualification evidence.

## Exact-final qualification contract

Final qualification creates **new literal-`1.1.0` evidence**. It does not relabel prerelease measurements.

The immutable RC performance envelope remains archived as `validation/performance/PERFORMANCE_ENVELOPE-1.1.0rc1.json`. The canonical performance envelope must be replaced only by fresh exact-`1.1.0` evidence generated on the final-version PR head.

Before final publication may be armed, the literal final version must pass:

- fresh package-wide exact-version performance qualification;
- fresh sparse-MFPCA performance/observation qualification;
- the frozen 1.0 root-API boundary and module-scoped 1.1 contracts;
- the complete cross-platform/package, documentation, examples, optional-backend, sparse/irregular, product-analysis, reproducibility, recovery/stress, and external-comparator matrix;
- protected-main merge; and
- the complete matrix again on the exact protected-main final-qualified commit.

Only then may a **separate governance-only PR** arm GitHub and production-PyPI publication.

## Immutable prerelease history

`v1.1.0rc1`, its production-PyPI distributions, checksums, attestations, release artifact, exact-version qualification evidence, installed-artifact observation, and archived RC performance records remain immutable historical evidence.

## Publication status

This page records **qualification state**, not publication. `1.0.0` remains the stable/default production release and `1.1.0rc1` remains the published 1.1 prerelease until final `1.1.0` is independently qualified, armed through a separate reviewed governance change, and successfully published.
""", encoding="utf-8")

mkdocs = Path("mkdocs.yml")
nav = mkdocs.read_text(encoding="utf-8")
anchor = "  - Releases:\n      - 1.1.0rc1: releases/1.1.0rc1.md\n"
if anchor not in nav:
    raise SystemExit("mkdocs release-nav anchor not found")
nav = nav.replace(anchor, "  - Releases:\n      - 1.1.0: releases/1.1.0.md\n      - 1.1.0rc1: releases/1.1.0rc1.md\n", 1)
mkdocs.write_text(nav, encoding="utf-8")
