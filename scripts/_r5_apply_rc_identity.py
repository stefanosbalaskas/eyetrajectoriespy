from pathlib import Path
import re


def replace(path: str, old: str, new: str, *, required: bool = True) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if old not in text:
        if required and new not in text:
            raise SystemExit(f"expected token not found in {path}: {old!r}")
        return
    target.write_text(text.replace(old, new), encoding="utf-8")


replace("pyproject.toml", 'version = "1.1.0.dev0"', 'version = "1.1.0rc1"')
replace("src/eyetrajectoriespy/__init__.py", '__version__ = "1.1.0.dev0"', '__version__ = "1.1.0rc1"')
replace("CANONICAL_WORKFLOWS.json", '"package_version": "1.1.0.dev0"', '"package_version": "1.1.0rc1"')
replace("RELEASE_READINESS.json", '"current_development_version": "1.1.0.dev0"', '"current_development_version": "1.1.0rc1"')

cff = Path("CITATION.cff")
text = cff.read_text(encoding="utf-8").replace("version: 1.1.0.dev0", "version: 1.1.0rc1")
if "date-released:" in text:
    text = re.sub(r"^date-released:.*$", "date-released: 2026-10-06", text, flags=re.MULTILINE)
else:
    text = text.replace("version: 1.1.0rc1\n", "version: 1.1.0rc1\ndate-released: 2026-10-06\n", 1)
cff.write_text(text, encoding="utf-8")

readme = Path("README.md")
text = readme.read_text(encoding="utf-8")
text = text.replace("**Stable:** `1.0.0` · **Development source:** `1.1.0.dev0` · **Python:** 3.11–3.13", "**Stable:** `1.0.0` · **1.1 release candidate under qualification:** `1.1.0rc1` · **Python:** 3.11–3.13")
text = text.replace("**Development source: `1.1.0.dev0`**", "**1.1 release candidate under qualification: `1.1.0rc1`**")
text = text.replace("`1.1.0.dev0`", "`1.1.0rc1`")
readme.write_text(text, encoding="utf-8")

roadmap = Path("docs/methods/status-roadmap.md")
text = roadmap.read_text(encoding="utf-8").replace("The current development line is **1.1.0.dev0**.", "The current release-candidate line is **1.1.0rc1**.")
roadmap.write_text(text, encoding="utf-8")

changelog = Path("CHANGELOG.md")
text = changelog.read_text(encoding="utf-8").replace("## Unreleased — 1.1.0.dev0", "## 1.1.0rc1 (under exact-version qualification)", 1)
marker = "## 1.1.0rc1 (under exact-version qualification)\n"
qualification = "\n- Promote the completed R1-R4 development surface to the literal `1.1.0rc1` identity for qualification only; no estimator, analytical default, dependency, root-API expansion, or publication arming is introduced by this version change.\n- Require fresh literal-`1.1.0rc1` qualification/performance evidence plus complete pull-request and protected-main matrices before any publication decision.\n"
if qualification.strip() not in text:
    text = text.replace(marker, marker + qualification, 1)
changelog.write_text(text, encoding="utf-8")

readiness = Path("docs/release-readiness.md")
text = readiness.read_text(encoding="utf-8")
section = "## 1.1.0rc1 exact-version qualification\n\nR4 records `eligible_for_rc_decision=true` on the completed `1.1.0.dev0` surface. R5 therefore qualifies the same scientific/product surface under the literal `1.1.0rc1` identity. This tranche is version/evidence only: no estimator, analytical default, dependency, supported module-scoped API, or frozen 1.0 root boundary changes. GitHub and production-PyPI publication readiness remain jointly disarmed until a later governance-only decision.\n\n"
if "## 1.1.0rc1 exact-version qualification" not in text:
    text = text.replace("# Pre-1.0 release-readiness checklist\n\n", "# Pre-1.0 release-readiness checklist\n\n" + section, 1)
readiness.write_text(text, encoding="utf-8")

process = Path("docs/release-process.md")
text = process.read_text(encoding="utf-8")
section = "## 1.1.0rc1 exact-version qualification\n\n`1.1.0rc1` may be qualified only because R4 recorded `eligible_for_rc_decision=true`. The RC transition is version-only and must generate fresh literal-version evidence. Historical `1.1.0.dev0` R4 evidence and frozen 1.0 evidence remain attributed to their original identities. Publication remains disarmed throughout RC qualification; arming and production publication require later, separate governance.\n\n"
if "## 1.1.0rc1 exact-version qualification" not in text:
    text = text.replace("# Coordinated GitHub Release and PyPI publication\n\n", "# Coordinated GitHub Release and PyPI publication\n\n" + section, 1)
process.write_text(text, encoding="utf-8")

validation = Path("VALIDATION.md")
text = validation.read_text(encoding="utf-8")
start = text.find("## Current development target")
if start >= 0:
    next_heading = text.find("\n## ", start + 4)
    if next_heading < 0:
        next_heading = len(text)
    replacement = "## Current development target\n\n`1.1.0rc1` is the literal release-candidate identity under qualification; published stable `1.0.0` remains immutable.\n\n- R4 qualified the integrated `1.1.0.dev0` surface and recorded `eligible_for_rc_decision=true`.\n- The RC transition changes identity/evidence only; no estimator, scientific default, dependency, or supported API is added here.\n- Active reference/tolerance/performance evidence must be regenerated or promoted only as fresh literal-`1.1.0rc1` qualification evidence; historical 1.0 and R4 development ledgers remain immutable.\n- The complete RC pull-request matrix and complete post-merge exact-main matrix must pass before publication may be considered.\n- GitHub/PyPI publication readiness remains jointly false throughout qualification.\n"
    text = text[:start] + replacement + text[next_heading:]
validation.write_text(text, encoding="utf-8")

release_page = Path("docs/releases/1.1.0rc1.md")
if not release_page.exists():
    release_page.write_text("""# eyetrajectoriespy 1.1.0rc1

**Release candidate — under exact-version qualification**

`1.1.0rc1` is the release-candidate identity for the integrated post-1.0 sparse/irregular surface qualified through R1-R4. It introduces no new estimator, scientific default, dependency, deprecation, removal, or root-namespace expansion relative to the completed `1.1.0.dev0` surface.

## Qualification rule

The RC must generate fresh literal-version validation and performance evidence, pass the complete pull-request matrix, merge through protected `main`, and pass the complete exact-main matrix. The R4 development-readiness ledger and frozen 1.0 evidence remain immutable historical inputs and are not relabelled as RC evidence.

## Publication governance

GitHub and production-PyPI publication remain disarmed during qualification. A green RC is not publication approval; arming requires a later governance-only change and production remains an explicit manual release workflow dispatch.
""", encoding="utf-8")

mkdocs = Path("mkdocs.yml")
text = mkdocs.read_text(encoding="utf-8")
marker = "  - Releases:\n"
entry = "      - 1.1.0rc1: releases/1.1.0rc1.md\n"
if entry not in text:
    text = text.replace(marker, marker + entry, 1)
mkdocs.write_text(text, encoding="utf-8")
