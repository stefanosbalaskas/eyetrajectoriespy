"""Inventory *all* wheel files, import modules and Python-defined symbols.

This is a structural inventory for release review, NOT a claim that every
discoverable submodule or symbol is supported, calibrated or stable.
The wheel, not importable source files, is the package-content authority.
"""
from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import sys
import tomllib
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = "eyetrajectoriespy"
BLOCKED = ("bayesian", "research")
SCHEMA = "CORE_12_WHEEL_COMPLETE_STRUCTURE_INVENTORY_V1"


def _hash(data: bytes) -> str:
    return sha256(data).hexdigest()


def _ast_inventory(data: bytes) -> dict:
    tree = ast.parse(data.decode("utf-8"))
    functions, classes, imported_public = [], [], []
    all_names = None
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                functions.append(node.name)
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                classes.append(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            imported_public.extend(
                (alias.asname or alias.name.split(".")[0])
                for alias in node.names
                if alias.name != "*" and not (alias.asname or alias.name).startswith("_")
            )
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets):
                try:
                    candidate = ast.literal_eval(node.value)
                    if isinstance(candidate, (list, tuple)) and all(
                        isinstance(n, str) for n in candidate
                    ):
                        all_names = list(candidate)
                except (ValueError, TypeError):
                    pass
    return {
        "defined_public_functions": sorted(set(functions)),
        "defined_public_classes": sorted(set(classes)),
        "imported_nonprivate_names": sorted(set(imported_public)),
        "static_all_export_names": sorted(set(all_names)) if all_names is not None else None,
        "has_static_all": all_names is not None,
    }


def _module_path(member: str) -> str:
    rel = member.removeprefix(PACKAGE + "/").removesuffix(".py")
    parts = rel.split("/")
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join([PACKAGE, *parts])


def _classify(module: str) -> str:
    # Discovery/packaging classification, NOT independent science approval.
    suffix = module.removeprefix(PACKAGE).removeprefix(".")
    if not suffix:
        return "public_root_candidate_unreviewed"
    if suffix.split(".")[0] in BLOCKED:
        return "blocked_experimental_namespace"
    if any(p.startswith("_") for p in suffix.split(".")):
        return "private_implementation_unreviewed"
    if suffix.startswith("workflows"):
        return "workflow_submodule_review_required"
    return "importable_submodule_support_review_required"


def inventory_wheel(wheel: Path, source_root: Path = ROOT) -> dict:
    wheel = Path(wheel)
    if wheel.suffix != ".whl":
        raise ValueError("expected .whl artifact")
    with (source_root / "pyproject.toml").open("rb") as f:
        version = tomllib.load(f)["project"]["version"]
    source = source_root / "src" / PACKAGE
    if not source.is_dir():
        raise ValueError("source package directory missing")
    source_members = sorted(
        f"{PACKAGE}/{p.relative_to(source).as_posix()}" for p in source.rglob("*.py")
    )
    source_file_set = set(source_members)
    rows, package_paths, contents = [], [], []
    with ZipFile(wheel) as archive:
        names = archive.namelist()
        if len(set(names)) != len(names):
            raise ValueError("duplicate archive members")
        if any(Path(n).is_absolute() or ".." in Path(n).parts or "\\" in n
               for n in names):
            raise ValueError("unsafe wheel member path")
        for entry in sorted(archive.infolist(), key=lambda e: e.filename):
            if entry.is_dir():
                continue
            name = entry.filename
            raw = archive.read(entry)
            contents.append({"path": name, "bytes": entry.file_size, "sha256": _hash(raw)})
            if not name.startswith(PACKAGE + "/"):
                if name.startswith(("scripts/", "tests/")):
                    raise ValueError("source tooling included at archive root")
                continue
            package_paths.append(name)
            if not name.endswith(".py"):
                continue
            module = _module_path(name)
            row = {
                "module": module, "wheel_path": name,
                "sha256": _hash(raw), "bytes": len(raw),
                "support_classification": _classify(module),
            }
            row.update(_ast_inventory(raw))
            rows.append(row)
    wheel_py = {row["wheel_path"] for row in rows}
    if wheel_py != source_file_set:
        raise ValueError("wheel/source module difference: " + json.dumps({
            "missing_in_wheel": sorted(source_file_set-wheel_py),
            "unexpected_in_wheel": sorted(wheel_py-source_file_set),
        }))
    blocked = sorted(row["module"] for row in rows
                     if row["support_classification"]=="blocked_experimental_namespace")
    if blocked:
        raise ValueError("unqualified Bayesian/research modules packaged: " + ", ".join(blocked))
    roots = [x for x in rows if x["module"] == PACKAGE]
    if len(roots) != 1 or not roots[0]["has_static_all"]:
        raise ValueError("static public root __all__ contract required")
    root_symbols = roots[0]["static_all_export_names"]
    if not root_symbols or len(root_symbols) != len(set(root_symbols)):
        raise ValueError("root public API must be nonempty and unique")
    baseline = json.loads((source_root/"validation/core_12/stable_1_1_0_root_exports.json").read_text())
    if baseline["tag"] != "v1.1.0" or baseline["declared_exports"] != root_symbols:
        raise ValueError("public root __all__ differs from stable v1.1.0 names baseline")
    # Compare actual wheel bytes against source Python files: not merely filenames.
    by_path = {r["wheel_path"]: r for r in rows}
    mismatch = [p for p in source_members
                if _hash((source_root/"src"/p).read_bytes()) != by_path[p]["sha256"]]
    if mismatch:
        raise ValueError("source and wheel Python bytes differ: "+str(mismatch[:8]))
    if not any(x.endswith(".dist-info/METADATA") for x in
               (c["path"] for c in contents)):
        raise ValueError("wheel metadata absent")
    return {
        "schema": SCHEMA, "development_version": version,
        "wheel_filename": wheel.name, "wheel_sha256": _hash(wheel.read_bytes()),
        "all_archive_contents": contents,
        "all_package_contents": sorted(package_paths),
        "all_python_module_symbol_inventories": rows,
        "root_explicit_all_exports": root_symbols,
        "root_all_sha256": _hash(("\n".join(root_symbols)+"\n").encode()),
        "root_export_names_match_stable_1_1_0": True,
        "stable_root_names_baseline_sha256": _hash((source_root/"validation/core_12/stable_1_1_0_root_exports.json").read_bytes()),
        "full_public_api_independently_approved": False,
        "modules_individually_scientifically_qualified": False,
        "literal_rc2_qualified": False, "release_authorized": False,
        "exposed_submodules_are_not_automatically_supported": True,
        "all_source_python_modules_verified_against_wheel": True,
        "blocked_experimental_namespaces_absent": True,
        "summary": {
            "archive_entries": len(contents), "package_entries": len(package_paths),
            "root_export_names_match_stable_1_1_0": True,
            "python_modules": len(rows), "root_explicit_exports": len(root_symbols),
            "submodules_needing_review": sum(x["support_classification"].endswith(
                "review_required") for x in rows),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wheel", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = inventory_wheel(args.wheel)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    print("CORE WHEEL COMPLETE STRUCTURE INVENTORY:",
          json.dumps({**result["summary"], "wheel_sha256": result["wheel_sha256"],
                      "full_public_api_independently_approved": False}, sort_keys=True))


if __name__ == "__main__":
    main()
