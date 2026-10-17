"""R61-A independent archive, native kernel and whitening contracts."""
import hashlib
import math

import numpy as np
import pytest

from scripts import audit_w3_r61_original_native_gaussian_independent as a


def test_original_primitive_block_and_provenance_contract():
    assert a.ORIGINAL_RUN == 39068871584
    assert a.BLOCKS == 4
    assert len(a.EXPECTED) == 8
    assert a.FROZEN_CHECKOUT == "92af2f707a6e9c608e405b84693165b507900143"
    assert a.WITNESS_DRAWS == 1024
    assert a.WITNESS_PARTICIPANTS == (0, 23)
    assert a.STUDY == "W3_R61_GAUSSIAN_FITTED_H0_DRAW_COVARIANCE_FIDELITY"


def test_closed_form_weighted_H0_covariance_independently_rebuilt():
    t = np.array([0.0, 0.6, 0.9])
    tr = np.array([0, 0, 1])
    w = np.array([.25, .25, .125])
    theta = np.array([1.2, 0.0, 0.7, .3])
    V = a.independent_fitted_null_covariance(t, tr, 1.2, w, theta)
    r = np.sqrt(w)
    u = r * (1 + .30*t)
    expected = 1.2*np.outer(u,u)
    expected += .7 * np.outer(r,r) * (
        tr[:,None] == tr[None,:])
    expected += .3 * np.diag(w)
    np.testing.assert_allclose(V, expected, rtol=0, atol=1e-14)
    assert np.linalg.eigvalsh(V).min() > 0


def test_archive_original_SHA256_and_checkout_fail_closed(tmp_path, monkeypatch):
    content={"cases.json":"[]\n","summary.json":"{}\n",
             "source-commit.txt":"test-original-merge\n"}
    for name,value in content.items():
        (tmp_path/name).write_text(value)
    hashes={name:hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()
            for name in content}
    (tmp_path/"SHA256SUMS").write_text("".join(
        digest+"  "+name+"\n" for name,digest in hashes.items()))
    monkeypatch.setattr(a,"FROZEN_CHECKOUT","test-original-merge")
    assert a.verify_archive(tmp_path)==hashes
    (tmp_path/"cases.json").write_text("tampered")
    with pytest.raises(ValueError,match="SHA256"):
        a.verify_archive(tmp_path)


def test_raw_native_source_rejects_corrupt_weights_predictors_and_participants():
    d = {"X":np.column_stack((np.ones(48), np.arange(48))),
         "y":np.ones(48),"w":np.ones(48),"group":np.repeat(np.arange(24),2),
         "time":np.tile([0.1,0.3],24),"trial":np.zeros(48),
         "x":np.repeat(np.arange(24)/24.,2)}
    native={k:np.asarray(v).tolist() for k,v in d.items()}
    X,y,w,g,t,tr,x,labels=a.read_native({"native_synthetic_source":native})
    assert len(labels)==24
    native["w"][0]=-1
    with pytest.raises(ValueError,match="design"):
        a.read_native({"native_synthetic_source":native})
    native["w"][0]=1
    native["x"][0]=999
    with pytest.raises(ValueError,match="predictor"):
        a.read_native({"native_synthetic_source":native})


def test_frozen_gaussian_identity_failures_are_not_inference():
    V=a.independent_fitted_null_covariance(
        np.array([0.,.5]),np.array([0.,0.]),.5,
        np.array([.3,.3]),np.array([.6,0.,.4,.1]))
    assert np.all(np.isfinite(V))
    with pytest.raises(ValueError,match="mismatch"):
        a.close(.25,.35,"faked covariance")
    with pytest.raises(ValueError,match="nonfinite"):
        a.close(float("nan"),.5,"corrupt raw numerical value")
