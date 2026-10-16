"""R52 fixed-covariance Gaussian CR2 reference-law algebra and refusals."""
import numpy as np
import pytest

from scripts import run_w3_r51_bootstrap_narrowing_mechanism as r51
from scripts import run_w3_r52_gaussian_cr2_joint_law as r52
from scripts.w3_r22_scaled_cholesky_cr2 import stable_cr2_blockwise_wls


def test_new_source_primitive_independence_and_freeze():
    assert r52.MASTER_SEED!=r51.SOURCE_SEED
    assert r52.MC_SEED!=r51.DRAW_SEED
    assert r52.BLOCKS==4 and r52.PARTICIPANTS==24
    assert r52.EXPECTED_SOURCE==8
    assert r52.EXPECTED_TARGET==16
    assert r52.EXPECTED_CRITICAL==32
    assert r52.N_MC==16384
    a=r52.source(0,r52.SUPPORT[0])
    paired=r52.source(0,r52.SUPPORT[1])
    b=r52.source(1,r52.SUPPORT[0])
    old=r51.source(0,r51.SUPPORT[0])
    np.testing.assert_array_equal(
        a[0]["participant_intercept"],paired[0]["participant_intercept"])
    assert not np.array_equal(
        a[0]["participant_intercept"],b[0]["participant_intercept"])
    assert not np.array_equal(
        a[0]["participant_intercept"],old[0]["participant_intercept"])
    with pytest.raises(ValueError,match="unregistered"):
        r52.source(4,r52.SUPPORT[0])


def test_joint_geometry_directly_reconstructs_original_CR2_score_and_estimator():
    data=r52.native_problem(0,r52.SUPPORT[0])
    Omega,m,algebra=r52.joint_geometry(
        data["X"],data["w"],data["group"],data["contrast"],
        data["true_covariance"],data["true_covariance"])
    n=len(data["y"])
    assert Omega.shape==(25,25)
    assert m["number_of_clusters"]==24
    assert 0<=m["max_absolute_numerator_score_correlation"]<=1+1e-8
    assert np.linalg.eigvalsh(Omega).min()>-1e-8
    assert m["max_adjustment_identity_error"]<=3e-7
    rng=np.random.default_rng(1234)
    beta0=rng.normal(size=data["X"].shape[1])
    e=rng.standard_normal(n)*.025
    y_star=data["X"]@beta0+e/np.sqrt(data["w"])
    recomputed=stable_cr2_blockwise_wls(
        data["X"],y_star,data["w"],data["group"],
        data["contrast"],data["true_covariance"])
    point_error=recomputed["point"]-float(data["contrast"]@beta0)
    assert point_error==pytest.approx(algebra["u"]@e,rel=1e-7,abs=1e-9)
    assert recomputed["cr2_se"]**2==pytest.approx(
        float(np.sum((algebra["score_rows"]@e)**2)),rel=1e-7,abs=1e-10)
    assert recomputed["satterthwaite_df"]==pytest.approx(
        m["score_effective_df_from_true_covariance"],rel=3e-7)
    assert recomputed["conditional_expectation"]==pytest.approx(
        m["expected_CR2_squared_SE"],rel=3e-7)


def test_independent_numerator_counterfactual_changes_only_cross_covariance():
    data=r52.native_problem(0,r52.SUPPORT[1])
    O,m,_=r52.joint_geometry(
        data["X"],data["w"],data["group"],data["contrast"],
        data["true_covariance"],data["true_covariance"])
    independently_forced=r52._sym(np.block([
        [O[:1,:1],np.zeros_like(O[:1,1:])],
        [np.zeros_like(O[1:,:1]),O[1:,1:]],
    ]))
    np.testing.assert_array_equal(
        independently_forced[1:,1:],O[1:,1:])
    assert independently_forced[0,0]==O[0,0]
    np.testing.assert_array_equal(independently_forced[0,1:],
                                  np.zeros(O.shape[0]-1))
    q=r52._mc_quantiles(O,seed=314159,n=512)
    assert len(q)==2
    assert all(v["status"]=="ok" for v in q)
    assert all(v["absolute_studentized_critical_q90"]>0 for v in q)
    assert all(v["MC_order_statistic_95pct_limits"][0] <=
               v["absolute_studentized_critical_q90"] <=
               v["MC_order_statistic_95pct_limits"][1] for v in q)


def test_wrong_true_covariance_shape_and_non_SPD_refused():
    data=r52.native_problem(0,r52.SUPPORT[0])
    wrong=list(data["true_covariance"])
    wrong[0]=np.eye(2)
    with pytest.raises(ValueError,match="dimension mismatch"):
        r52.joint_geometry(
            data["X"],data["w"],data["group"],data["contrast"],
            wrong,data["true_covariance"])
    wrong=list(data["true_covariance"])
    wrong[0]=-np.eye(wrong[0].shape[0])
    with pytest.raises(np.linalg.LinAlgError):
        r52.joint_geometry(
            data["X"],data["w"],data["group"],data["contrast"],
            wrong,data["true_covariance"])


def test_report_refusals_preserve_full_target_denominator_and_no_coverage_claim():
    row={
        "block":0,"support":r52.SUPPORT[0],
        "targets":[r52.refuse(t,"forced-source-failure") for t in r52.TARGETS],
    }
    report=r52.summarize([row])
    assert report["planned_covariance_targets"]==16
    assert report["recorded_covariance_targets"]==2
    assert report["recorded_critical_records"]==4
    assert not report["complete_failure_inclusive_evidence"]
    assert report["no_90pct_pointwise_coverage_qualification"]
    assert report[
        "estimated_target_held_fixed_is_counterfactual_not_true_conditional_distribution"]
    assert not report["release_authorized"]
    with pytest.raises(ValueError,match="duplicated"):
        r52.summarize([row,row])
