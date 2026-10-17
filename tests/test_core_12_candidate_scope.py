"""Core 1.2 release-track isolation without arming candidate/publication."""
from copy import deepcopy
from pathlib import Path
import json
import shutil
import sys

import pytest

# Docs gallery invokes pytest in a subprocess without the repository root on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.audit_core_12_candidate_scope import analyze_scope, ROOT


def test_development_scope_audit_has_no_release_promotion():
    result=analyze_scope()
    assert result["source_version"]=="1.2.0rc2.dev0"
    assert result["experimental_namespace_exclusions_verified"]
    assert not result["core_api_full_inventory_independently_frozen"]
    assert not result["literal_candidate_qualified"]
    assert not result["release_authorized"]


@pytest.fixture
def mirrored_root(tmp_path):
    for f in ("pyproject.toml", "RELEASE_READINESS.json"):
        shutil.copy2(ROOT/f,tmp_path/f)
    for path in ("src/eyetrajectoriespy/__init__.py",
                 "validation/core_12/core_rc_scope_policy.json"):
        destination=tmp_path/path
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(ROOT/path,destination)
    return tmp_path


def test_fail_closed_when_unqualified_root_symbol_added(mirrored_root):
    p=mirrored_root/"src/eyetrajectoriespy/__init__.py"
    p.write_text(p.read_text()+"\nfrom .bayesian import fit_bayesian_sparse_fpca\n")
    with pytest.raises(ValueError,match="experimental"):
        analyze_scope(mirrored_root)


def test_fail_closed_when_publication_armed(mirrored_root):
    p=mirrored_root/"RELEASE_READINESS.json"
    value=json.loads(p.read_text())
    value["production_release_ready"]=True
    p.write_text(json.dumps(value))
    with pytest.raises(ValueError,match="publication gate"):
        analyze_scope(mirrored_root)


def test_fail_closed_when_source_promoted_without_exact_evidence(mirrored_root):
    p=mirrored_root/"pyproject.toml"
    p.write_text(p.read_text().replace(
        'version = "1.2.0rc2.dev0"','version = "1.2.0rc2"',1))
    with pytest.raises(ValueError,match="development"):
        analyze_scope(mirrored_root)
