"""Independent R51 original evidence audit; no R51 estimator dependency."""
import hashlib
import json
from pathlib import Path

import pytest

from scripts.audit_w3_r51_original_mechanism_independent import (
    KKT_TOL,accept_two_start_nuisance,independently_calculated_wilson,
    must_close,sha_checks,audit,
)


def _two_starts(kkt=.00005):
    return [
        {
            "label":"interior","status":"ok","optimizer_success":True,
            "negative_loglik":10.,"physical_projected_KKT":kkt,
            "ratios":[.1,.2,.3,1.],
            "objective_reconstruction_error":0.,
        },
        {
            "label":"spread","status":"ok","optimizer_success":True,
            "negative_loglik":10.,"physical_projected_KKT":.0000001,
            "ratios":[.1,.2,.3,1.],
            "objective_reconstruction_error":0.,
        },
    ]


def test_w3_r51_readonly_numerical_acceptance_preserves_failed_start():
    starts=_two_starts(.0019989)
    failures=accept_two_start_nuisance(
        starts,"accepted","source-numerical-audit",
        selection={"selected_NLL":10.,"physical_projected_KKT":.0000001}
    )
    assert len(failures)==1
    assert failures[0]["label"]=="interior"
    assert failures[0]["physical_projected_KKT"]>KKT_TOL


def test_w3_r51_kkt_refusal_not_confused_with_optimizer_success():
    starts=_two_starts(.02)
    starts[1]["physical_projected_KKT"]=.03
    with pytest.raises(ValueError,match="no KKT/NLL eligible"):
        accept_two_start_nuisance(starts,"accepted","tampered")


def test_w3_r51_wrong_nll_and_selected_physical_record_refused():
    starts=_two_starts()
    starts[1]["negative_loglik"]=9.
    with pytest.raises(ValueError,match="selected NLL"):
        accept_two_start_nuisance(
            starts,"accepted","bad-selected",
            selection={"selected_NLL":10.,"physical_projected_KKT":.00005},
        )
    starts[1]["negative_loglik"]=10.
    with pytest.raises(ValueError,match="selected nuisance"):
        accept_two_start_nuisance(
            starts,"accepted","bad-kkt",
            selection={"selected_NLL":10.,"physical_projected_KKT":.00000007},
        )


def test_w3_r51_nonphysical_ratios_and_reconstruction_errors_refused():
    starts=_two_starts()
    starts[0]["ratios"]=[-.1,.2,.3,1.]
    with pytest.raises(ValueError,match="nonphysical"):
        accept_two_start_nuisance(starts,"accepted","bad-ratios")
    starts=_two_starts()
    starts[0]["objective_reconstruction_error"]=.01
    with pytest.raises(ValueError,match="reconstructed"):
        accept_two_start_nuisance(starts,"accepted","bad-objective")


def test_w3_r51_source_sha256_manifest_tampering_detected(tmp_path):
    blobs={
        "cases.json":"[]\n",
        "summary.json":"{}\n",
        "source-commit.txt":"pr-merge-sha\n",
    }
    for name,value in blobs.items():
        (tmp_path/name).write_text(value)
    (tmp_path/"SHA256SUMS").write_text("".join(
        hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()
        +"  "+name+"\n" for name in blobs
    ))
    assert len(sha_checks(tmp_path))==3
    (tmp_path/"cases.json").write_text("[modified]\n")
    with pytest.raises(ValueError,match="SHA256 mismatch"):
        sha_checks(tmp_path)
    with pytest.raises(ValueError,match="SHA256 mismatch"):
        audit(tmp_path)


def test_w3_r51_wilson_MC_denominator_is_independent_primitives_only():
    lo,hi=independently_calculated_wilson(8,8)
    assert lo==pytest.approx(.6755924351161198,rel=1e-8)
    assert hi==pytest.approx(1.)
    lo2,hi2=independently_calculated_wilson(7,8)
    assert lo2<7/8<hi2
    with pytest.raises(ValueError,match="recomputation mismatch"):
        must_close(.2,.3,"tampered-quantile")
