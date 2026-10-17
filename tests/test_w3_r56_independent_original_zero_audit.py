"""R56 independent original SHA and zero-vs-positive fitted bound audit."""
import hashlib
from pathlib import Path

import pytest

from scripts.audit_w3_r56_original_zero_positive_independent import (
    LOW,MASTER,verify_archive,close,
)


def test_source_qualified_constants_are_frozen():
    assert MASTER==202610175656
    assert LOW==pytest.approx(1.0156314710024903e-6,rel=1e-10)


def test_original_archive_sha_and_merge_checkout_require_exact_bytes(tmp_path):
    files={
        "cases.json":"[]\n",
        "summary.json":"{}\n",
        "source-commit.txt":"R56-original-source\n",
    }
    for key,contents in files.items():
        (tmp_path/key).write_text(contents)
    (tmp_path/"SHA256SUMS").write_text("".join(
        hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()
        +"  "+name+"\n" for name in files
    ))
    with pytest.raises(ValueError,match="source case/summary hash"):
        verify_archive(tmp_path)
    (tmp_path/"cases.json").write_text("[tampered]")
    with pytest.raises(ValueError,match="checksum mismatch"):
        verify_archive(tmp_path)


def test_numerical_uncertainty_audit_mismatches_fail_closed():
    with pytest.raises(ValueError,match="mismatch"):
        close(.2,.1,"fabricated Gaussian CR2 coverage")
    with pytest.raises(ValueError,match="mismatch"):
        close(float("nan"),1.,"missing original evidence")
