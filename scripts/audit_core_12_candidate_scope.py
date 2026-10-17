"""Fail-closed scope and publication governance for proposed *core-only* 1.2.

Scope audit != scientific qualification of every estimator or release approval.
Run on development source only; literal candidate requires a separate exact-version
qualification PR and independent publication authorization.
"""
from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys
import tomllib

from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "validation/core_12/core_rc_scope_policy.json"
ROOT_MODULE = ROOT / "src/eyetrajectoriespy/__init__.py"


def analyze_scope(root: Path = ROOT) -> dict:
    policy = json.loads((root / "validation/core_12/core_rc_scope_policy.json").read_text())
    package_source = root / "src/eyetrajectoriespy/__init__.py"
    text = package_source.read_text()
    tree = ast.parse(text)
    pyproject = tomllib.loads((root / "pyproject.toml").read_text())
    source_version = pyproject["project"]["version"]
    readiness = json.loads((root / "RELEASE_READINESS.json").read_text())
    init_assignments = {}
    root_import_modules = []
    imported_symbols = []
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    try:
                        init_assignments[target.id] = ast.literal_eval(node.value)
                    except (ValueError, TypeError):
                        pass
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            root_import_modules.append(module)
            imported_symbols.extend(a.asname or a.name for a in node.names)
        elif isinstance(node, ast.Import):
            root_import_modules.extend(a.name for a in node.names)
    errors = []
    if source_version != policy["current_source_version"] or not Version(source_version).is_devrelease:
        errors.append("active source is no longer the declared .dev release identity")
    if str(readiness.get("current_development_version")) != source_version:
        errors.append("release-readiness development version differs")
    if readiness.get("production_release_ready") is not False:
        errors.append("release publication gate must remain false")
    if init_assignments.get("__version__") != source_version:
        errors.append("root __version__ differs from source")
    if policy["release_authorized"] is not False or policy["literal_candidate_qualified"] is not False:
        errors.append("core stage-0 policy must not arm candidate or publication")
    if policy["target_candidate_not_yet_created"] is not True:
        errors.append("stage-0 cannot represent a literal release candidate")
    if not policy["no_pypi_or_github_release_from_this_branch"]:
        errors.append("stage-0 must prohibit distribution publication")
    for name in policy["experimental_namespaces_excluded_from_qualification"]:
        if any(module == name or module.startswith(name + ".")
               for module in root_import_modules):
            errors.append(f"experimental {name} module imported into public root")
    exported_set = set(imported_symbols)
    declared_all = init_assignments.get("__all__")
    if isinstance(declared_all, (tuple, list)):
        exported_set.update(declared_all)
    for name in policy["experimental_public_root_symbols_forbidden"]:
        if name in exported_set:
            errors.append(f"unqualified experimental symbol exported: {name}")
    for name in policy["core_supported_example_exports"]:
        if name not in exported_set:
            errors.append(f"reviewed core smoke symbol is missing: {name}")
    # Manifest is NOT treated as qualified evidence for the full export surface.
    # Retain hash and full export count to allow a separate explicit freeze review.
    if errors:
        raise ValueError("; ".join(errors))
    return {
        "stage":"core_12_independent_release_scoping_not_literal_rc",
        "source_version":source_version,
        "published_stable_version_declared":policy["published_stable_version"],
        "source_development_identity":True,
        "source_root_sha256":sha256(text.encode()).hexdigest(),
        "policy_sha256":sha256(
            (root/"validation/core_12/core_rc_scope_policy.json").read_bytes()).hexdigest(),
        "top_level_imported_export_name_count":len(exported_set),
        "reviewed_smoke_export_names":policy["core_supported_example_exports"],
        "experimental_namespace_exclusions_verified":True,
        "production_release_ready":False,
        "literal_candidate_qualified":False,
        "release_authorized":False,
        "platform":platform.platform(),
        "python":sys.version.split()[0],
        "core_api_full_inventory_independently_frozen":False,
        "core_scientific_qualification_completed":False,
    }


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    result=analyze_scope()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print("CORE 1.2 RELEASE SCOPE PREQUALIFICATION:",json.dumps(result,sort_keys=True))


if __name__=="__main__":
    main()
