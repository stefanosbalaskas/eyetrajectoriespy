import builtins
import pytest

from eyetrajectoriespy import fit_elastic_fpca, simulate_planar_trajectories, to_skfda_grid

def test_optional_skfda_conversion_or_clear_error():
    x=simulate_planar_trajectories(n_participants=2,trials_per_participant=1,n_time=21)
    try:
        fd=to_skfda_grid(x)
    except ImportError as exc:
        assert "scikit-fda" in str(exc)
    else:
        assert fd.data_matrix.shape[0]==x.n_curves

def test_elastic_requires_optional_backend_if_missing(monkeypatch):
    x=simulate_planar_trajectories(n_participants=2,trials_per_participant=1,n_time=21)
    original_import=builtins.__import__
    def fake_import(name,*args,**kwargs):
        if name=="fdasrsf":
            raise ImportError("missing")
        return original_import(name,*args,**kwargs)
    monkeypatch.setattr(builtins,"__import__",fake_import)
    with pytest.raises(ImportError,match="fdasrsf"):
        fit_elastic_fpca(x,n_components=2)
