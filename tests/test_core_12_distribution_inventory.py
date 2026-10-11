"""Reject unexpected wheel content without claiming API qualification."""
from pathlib import Path
import json
import sys
from zipfile import ZipFile, ZIP_DEFLATED

import pytest

# The documentation gallery invokes pytest from a subprocess without this root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.audit_core_12_distribution_inventory import (
    PACKAGE, _ast_inventory, _classify, _module_path,
    inventory_wheel,
)


def test_ast_extracts_true_static_exports_and_named_definitions():
    obj=_ast_inventory(b'from .foo import Widget\nclass Thing: pass\ndef fit(): pass\n__all__=["Thing","fit","Widget"]\n')
    assert obj["static_all_export_names"] == ["Thing", "Widget", "fit"]
    assert obj["defined_public_classes"] == ["Thing"]
    assert obj["defined_public_functions"] == ["fit"]
    assert obj["imported_nonprivate_names"] == ["Widget"]


def test_module_path_and_support_classification():
    assert _module_path("eyetrajectoriespy/__init__.py")==PACKAGE
    assert _module_path("eyetrajectoriespy/workflows/__init__.py")==PACKAGE+".workflows"
    assert _classify(PACKAGE+".research.experimental")=="blocked_experimental_namespace"
    assert _classify(PACKAGE+".bayesian")=="blocked_experimental_namespace"
    assert _classify(PACKAGE+"._internal")=="private_implementation_unreviewed"
    assert _classify(PACKAGE+".fpca")=="importable_submodule_support_review_required"


def _fixture(tmp_path, *, extra=None, omit=False):
    source=tmp_path/"src"/PACKAGE
    source.mkdir(parents=True)
    (source/"__init__.py").write_text('__all__=["fit"]\n')
    (source/"fpca.py").write_text("def fit(): return 1\n")
    baseline=tmp_path/"validation/core_12/stable_1_1_0_root_exports.json"
    baseline.parent.mkdir(parents=True)
    baseline.write_text(json.dumps({"tag":"v1.1.0", "declared_exports":["fit"]}))
    (tmp_path/"pyproject.toml").write_text(
        '[project]\nname="eyetrajectoriespy"\nversion="1.2.0rc2.dev0"\n')
    entries={
        f"{PACKAGE}/__init__.py":(source/"__init__.py").read_bytes(),
        f"{PACKAGE}/fpca.py":(source/"fpca.py").read_bytes(),
        "eyetrajectoriespy-1.2.0rc2.dev0.dist-info/METADATA":b"Name: eyetrajectoriespy\n",
    }
    if omit:
        del entries[f"{PACKAGE}/fpca.py"]
    if extra:
        entries.update(extra)
    p=tmp_path/"example.whl"
    with ZipFile(p,"w",ZIP_DEFLATED) as z:
        for name,data in entries.items():
            z.writestr(name,data)
    return p


def test_complete_inventory_preserves_hashes_and_explicitly_unqualified(tmp_path):
    w=_fixture(tmp_path)
    v=inventory_wheel(w,tmp_path)
    assert v["summary"]["python_modules"]==2
    assert v["all_source_python_modules_verified_against_wheel"]
    assert v["root_explicit_all_exports"]==["fit"]
    assert v["root_export_names_match_stable_1_1_0"]
    assert not v["release_authorized"]
    assert not v["full_public_api_independently_approved"]
    assert len(v["all_archive_contents"])==3


def test_rejects_missing_source_module(tmp_path):
    w=_fixture(tmp_path,omit=True)
    with pytest.raises(ValueError,match="module difference"):
        inventory_wheel(w,tmp_path)


def test_rejects_experimental_package_content(tmp_path):
    w=_fixture(tmp_path,extra={f"{PACKAGE}/research/__init__.py":b""})
    (tmp_path/"src"/PACKAGE/"research").mkdir()
    (tmp_path/"src"/PACKAGE/"research/__init__.py").write_bytes(b"")
    with pytest.raises(ValueError,match="unqualified Bayesian/research"):
        inventory_wheel(w,tmp_path)


def test_rejects_unaccounted_distribution_tools(tmp_path):
    w=_fixture(tmp_path,extra={"scripts/unsafe.py":b"print(42)"})
    with pytest.raises(ValueError,match="source tooling"):
        inventory_wheel(w,tmp_path)


def test_detects_source_wheel_byte_difference(tmp_path):
    w=_fixture(tmp_path)
    (tmp_path/"src"/PACKAGE/"fpca.py").write_text("def fit(): return 3\n")
    with pytest.raises(ValueError,match="bytes differ"):
        inventory_wheel(w,tmp_path)


def test_rejects_public_root_exports_drifting_from_published_stable_names(tmp_path):
    w=_fixture(tmp_path)
    p=tmp_path/"validation/core_12/stable_1_1_0_root_exports.json"
    p.write_text(json.dumps({"tag":"v1.1.0","declared_exports":["other"]}))
    with pytest.raises(ValueError, match="stable v1.1.0"):
        inventory_wheel(w,tmp_path)
