"""R55 original R53-source multi-amplitude active-positive-face stress contracts."""
import hashlib
import json

import numpy as np
import pytest

from scripts import run_w3_r53_local_reml_influence as r53
from scripts import run_w3_r54_boundary_active_set_influence as r54
from scripts import run_w3_r55_active_face_switch_profile as r55


def test_predeclared_source_replay_not_new_independent_Gaussian_coverage():
    assert r55.REUSED_SOURCE_SEED==r53.SOURCE_SEED
    assert r55.DIRECTION_SEED not in (r53.DIRECTION_SEED,
                                     r54.DIRECTION_SEED)
    assert r55.BLOCKS==4 and r55.PARTICIPANTS==24
    assert r55.LEVELS==(.0005,.005,.05,.25)
    assert r55.SHARDS==((0,2),(2,4))
    assert r55.N_ORIGINAL==8
    assert r55.N_DIRECTIONS==16
    assert r55.N_NODES==128
    assert r55.N_FITS==136
    assert r55.N_STARTS==272
    previous=r53.problem(0,r55.SUPPORT[0])
    current=r55.data_for(0,r55.SUPPORT[0])
    np.testing.assert_array_equal(previous["y"],current["y"])
    np.testing.assert_array_equal(previous["X"],current["X"])
    with pytest.raises(ValueError,match="unregistered"):
        r55.data_for(4,r55.SUPPORT[0])


def test_direction_innovation_and_weighted_length_are_reproducible():
    a,seed=r55.direction_vector(0,r55.SUPPORT[1],1,139)
    b,other=r55.direction_vector(0,r55.SUPPORT[1],1,139)
    assert seed==other
    np.testing.assert_array_equal(a,b)
    assert np.linalg.norm(a)==pytest.approx(np.sqrt(139))
    assert not np.array_equal(
        a,r55.direction_vector(0,r55.SUPPORT[1],0,139)[0])
    with pytest.raises(ValueError,match="outside"):
        r55.direction_vector(0,r55.SUPPORT[1],2,139)


def _node(level,sign,changed=False,status="ok"):
    n=r55.node_template(level,sign)
    n["status"]=status
    n["face_changed_from_original"]=changed if status=="ok" else None
    return n


def test_first_observed_switch_bracket_not_exact_crossing_time():
    arr=[_node(x,s,(x>=.05 and s==1))
         for x in r55.LEVELS for s in r55.SIGNS]
    x=r55.profile_transition(arr,1)
    assert x["status"]=="first_observed_active_face_change_bracket"
    assert x["previous_no_switch_level"]==.005
    assert x["first_changed_level"]==.05
    assert x["true_crossing_time_identified"] is False
    y=r55.profile_transition(arr,-1)
    assert y["status"]=="no_changed_face_on_frozen_grid"
    assert y["switch_absence_between_grid_nodes_not_proven"]
    arr[4]["status"]="refused"
    x=r55.profile_transition(arr,-1)
    assert x["status"]=="unresolved_after_fit_or_CR2_refusal"
    assert x["first_refused_level"]==.05
    assert x["previous_no_switch_level"]==.005


def _case(block,support):
    rows=[]
    for direction in range(r55.DIRECTIONS):
        nodes=[r55.node_template(l,s)
               for l in r55.LEVELS for s in r55.SIGNS]
        rows.append({
            "direction":direction,"nodes":nodes,
            "transition_by_sign":{
                str(sign):r55.profile_transition(nodes,sign)
                for sign in r55.SIGNS
            },
        })
    return {
        "block":block,"support":support,
        "original_fit":{
            "status":"not_attempted",
            "numerical_starts":[
                {"label":"interior","status":"not_attempted"},
                {"label":"spread","status":"not_attempted"}]},
        "local_face_status":"not_attempted",
        "directions":rows,
    }


def test_full_failure_inclusive_grid_even_when_no_REML_attempt_possible():
    rows=[_case(block,s) for block in range(4) for s in r55.SUPPORT]
    report=r55.summary(rows)
    assert report["full_failure_inclusive_structural_source_grid"]
    assert report["planned_signed_perturbed_fit_slots"]==128
    assert report["recorded_signed_perturbed_fit_slots"]==128
    assert report["executed_perturbed_full_REML_fit_attempts"]==0
    assert report["recorded_executed_two_start_optimizer_outcomes"]==16
    assert report["new_independent_Gaussian_primitive_source_count"]==0
    assert report["no_population_switch_probability_estimated"]
    assert not report["release_authorized"]
    with pytest.raises(ValueError,match="duplicated"):
        r55.summary(rows+[rows[0]])
    rows[0]["directions"][0]["nodes"].pop()
    with pytest.raises(ValueError,match="missing frozen"):
        r55.summary(rows)


def test_sha_frozen_shard_join_rejects_source_replacement(tmp_path,monkeypatch):
    monkeypatch.setenv("GITHUB_SHA","fixed-r55-merge-source")
    part=tmp_path/"parts"
    for start,stop in r55.SHARDS:
        place=part/f"source-{start}"
        place.mkdir(parents=True)
        rows=[_case(b,s) for b in range(start,stop) for s in r55.SUPPORT]
        r55._write(place/"cases.json",rows)
        r55._write(place/"manifest.json",{
            "study":r55.STUDY,"start":start,"stop":stop,
            "source_seed_reused":r55.REUSED_SOURCE_SEED,
            "direction_seed":r55.DIRECTION_SEED,
            "source_checkout":"fixed-r55-merge-source",
            "SHA256_cases":hashlib.sha256(
                (place/"cases.json").read_bytes()).hexdigest(),
            "cases":len(rows),
        })
    r55.aggregate(tmp_path/"result",part)
    result=json.loads((tmp_path/"result"/"summary.json").read_text())
    assert result["full_failure_inclusive_structural_source_grid"]
    assert result["recorded_signed_perturbed_fit_slots"]==128
    (part/"source-0"/"cases.json").write_text("tampered")
    with pytest.raises(ValueError,match="checksum"):
        r55.aggregate(tmp_path/"damaged",part)


def test_json_invalid_float_is_not_evidence(tmp_path):
    with pytest.raises(ValueError):
        r55._write(tmp_path/"bad.json",{"status":"ok","missing":float("nan")})
