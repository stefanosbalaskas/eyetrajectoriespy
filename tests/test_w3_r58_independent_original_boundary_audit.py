"""Independent R58 original Gaussian boundary-null immutable-evidence contracts."""
import hashlib

import pytest

from scripts import audit_w3_r58_original_boundary_independent as audit


def test_candidate_null_reference_has_atom_and_one_sided_KKT():
    assert audit.CRITICAL == pytest.approx(2.705543454095404, rel=1e-10)
    assert audit.projected_kkt([.1,.2,1.,0.],
                                [0.,0.,0.,-2.], "nonnegative") == pytest.approx(2.)
    assert audit.projected_kkt([.1,.2,1.,0.],
                                [0.,0.,0.,2.], "nonnegative") == 0.
    with pytest.raises(ValueError, match="variance ratio"):
        audit.projected_kkt([.1,.2,1.,-.001],
                            [0.,0.,0.,0.], "nonnegative")


def test_binomial_wilson_recomputed_without_source_script():
    assert audit.wilson(0, 0) is None
    assert audit.wilson(0, 24)[1] == pytest.approx(.1379762, abs=.0001)
    assert audit.wilson(5, 24) == pytest.approx(
        [.09244825352851854, .40470453253188665], abs=1e-12)
    assert audit.wilson(2, 24) == pytest.approx(
        [.023158815297043348, .2584880219321069], abs=1e-12)
    with pytest.raises(ValueError):
        audit.wilson(25, 24)


def _fake_model():
    starts = [
        {
            "label": label, "status": "ok", "negative_loglik": 100.,
            "reconstructed_loglik": 100., "objective_reconstruction_error": 0.,
            "physical_projected_KKT": 0., "physical_score": [0.,0.,0.],
            "ratios": [.1,.2,1.], "optimizer_success": True,
        } for label in audit.NULL_STARTS
    ]
    return {
        "model": "exact_zero", "status": "accepted",
        "original_starts": starts, "best_observed_multistart_NLL": 100.,
        "selected_NLL": 100., "selected_start": audit.NULL_STARTS[0],
        "selected_physical_KKT": 0.,
        "selected_free_component_variance_ratios": [.1,.2,1.],
        "selected_slope_ratio": 0.,
        "null_includes_exact_zero_variance": True,
        "global_optimum_proven": False,
    }


def test_fake_selected_likelihood_or_KKT_refused():
    fit = _fake_model()
    assert audit.audit_fit(fit, "exact_zero", "mock")["status"] == "accepted"
    fit["selected_NLL"] = 99.
    with pytest.raises(ValueError, match="mismatch"):
        audit.audit_fit(fit, "exact_zero", "fake best")
    fit = _fake_model()
    fit["selected_physical_KKT"] = .01
    with pytest.raises(ValueError, match="mismatch"):
        audit.audit_fit(fit, "exact_zero", "fake KKT")
    fit = _fake_model()
    fit["selected_slope_ratio"] = .01
    with pytest.raises(ValueError, match="fix exact zero"):
        audit.audit_fit(fit, "exact_zero", "fake null")


def test_original_source_archive_sha256_and_commit_fail_closed(tmp_path, monkeypatch):
    data = {
        "cases.json": "[]\n",
        "summary.json": "{}\n",
        "source-commit.txt": "frozen-original-R58-merge\n",
    }
    for name, content in data.items():
        (tmp_path/name).write_text(content)
    sums = {name: hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()
            for name in data}
    (tmp_path/"SHA256SUMS").write_text("".join(
        h + "  " + name + "\n" for name,h in sums.items()))
    monkeypatch.setattr(audit, "SOURCE_CHECKOUT",
                        "frozen-original-R58-merge")
    assert audit.verify_source(tmp_path) == sums
    (tmp_path/"summary.json").write_text("tampered")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        audit.verify_source(tmp_path)


def test_infinite_invalid_source_facts_refused():
    with pytest.raises(ValueError, match="mismatch"):
        audit.close(float("inf"), 1., "infinite")
    with pytest.raises(ValueError, match="mismatch"):
        audit.close(1., 2., "wrong numerical statistic")
    with pytest.raises(ValueError, match="score dimension"):
        audit.projected_kkt([.1,.2,1.,0.], [0.], "nonnegative")
