"""R67 archived R66 refusal provenance tests; all fake records are fixtures."""
from __future__ import annotations

from copy import deepcopy

import pytest

from scripts import audit_w3_r67_original_r66_refusal_provenance as r67


def _fit(status: str, model: str) -> dict:
    return {
        "status":status,
        "model":model,
        "best_observed_multistart_NLL":1.25,
        "selected_start":None if status!="accepted" else "candidate",
        "selected_physical_KKT":None if status!="accepted" else .0003,
        "original_starts":[{
            "label":"candidate",
            "status":"ok" if status=="accepted" else "refused",
            "optimizer_success":status=="accepted",
            "physical_projected_KKT":.0003 if status=="accepted" else .02,
            "objective_reconstruction_error":0.,
            "negative_loglik":1.25,
        }],
    }


def _draw(idx: int, *, failed: bool=False, exception: bool=False):
    return {
        "draw":idx,
        "status":"refused" if failed else "accepted",
        "seed":5+idx,
        "nested":{
            "status":"refused" if failed else "accepted",
            "raw_deviance":None if failed else .2,
            "nonnegative_deviance":None if failed else .2,
            "null_fit":_fit("accepted","exact_zero"),
            "alternative_fit":_fit("refused" if failed else "accepted","nonnegative"),
        },
        "error":"test synthetic optimizer failure" if failed and exception else None,
    }


def _records():
    cases=[]
    for b in range(r67.BLOCKS):
        for s in r67.SUPPORT:
            for level in r67.LEVELS:
                failed=(b==7 and s=="extreme_dependent" and level=="half") or (
                    b==66 and s=="extreme_dependent" and level=="full")
                row={
                    "block":b,"support":s,"level":level,"source_status":"ok",
                    "source_error":None,"observed":{"status":"accepted"},
                    "fitted_null_theta":[1,0,1,1],
                    "bootstrap_5pct_exceedance":None if failed else False,
                    "conditional_bootstrap_p":None if failed else .125,
                    "bootstrap":[_draw(j,failed=(failed and j==9)) for j in range(r67.B)],
                }
                cases.append(row)
    return cases


def _independent_evidence():
    return {
        "R66_independent_original_numerical_archive_reproduced":True,
        "original_source_checkout":r67.ORIGINAL_SHA,
        "original_sha256_entries_verified":3,
        "prospective_paired_primitive_block_audit":{
            "complete_matched_blocks":126,
            "refused_incomplete_blocks":2,
            "paired_diagnostics":{
                "extreme_minus_ordinary_zero_to_full":{
                    "prospective_95pct_primitive_block_bootstrap_percentile":None,
                },
            },
        },
    }


def test_immutable_source_denominators_and_two_separate_original_refusals():
    x=r67.summarize_refusals(_records(),_independent_evidence())
    assert x["source_cases"]==768
    assert x["original_gaussian_bootstrap_draw_slots"]==48384
    assert x["accepted_original_conditional_draws"]==48382
    assert x["refused_original_conditional_draws"]==2
    assert x["affected_primitive_blocks"]==[7,66]
    assert x["failure_category_counts"]=={"alternative_model_not_accepted":2}
    assert x["prospective_primary_paired_complete_blocks"]==126
    assert x["prospective_primary_paired_incomplete_blocks"]==2
    assert x["prospective_primary_pct95_interval_correctly_withheld"]
    assert x["new_original_source_generating_blocks"]==0
    assert x["new_covariance_fits"]==0
    assert not x["release_authorized"]


def test_nested_refusal_record_does_not_recover_or_change_original_status():
    original=_draw(9,failed=True)
    before=deepcopy(original)
    record=r67.refusal_reason(original)
    assert record["draw"]==9
    assert record["mechanism"]=="alternative_model_not_accepted"
    assert record["null_fit"]["status"]=="accepted"
    assert record["alternative_fit"]["status"]=="refused"
    assert record["null_fit"]["optimizer_start_status_counts"]=={"ok":1}
    assert original==before
    exception=r67.refusal_reason(_draw(9,failed=True,exception=True))
    assert exception["mechanism"]=="source_or_draw_exception"
    with pytest.raises(ValueError,match="accepted original Gaussian"):
        r67.refusal_reason(_draw(9))


def test_any_forged_repair_duplicate_source_or_empty_draw_slot_fails_closed():
    cases=_records()
    cases[0]["block"]=7
    with pytest.raises(ValueError,match="grid"):
        r67.summarize_refusals(cases,_independent_evidence())
    cases=_records()
    cases[-1]["bootstrap"]=cases[-1]["bootstrap"][:-1]
    with pytest.raises(ValueError,match="order/denominator"):
        r67.summarize_refusals(cases,_independent_evidence())
    cases=_records()
    last=next(row for row in cases if row["block"]==7 and row["support"]=="extreme_dependent" and row["level"]=="half")
    last["bootstrap"][9]=_draw(9)
    with pytest.raises(ValueError,match="two numerical refusal slots"):
        r67.summarize_refusals(cases,_independent_evidence())


def test_independent_immutable_audit_gate_and_withheld_primary_ci_enforced():
    cases=_records()
    evidence=_independent_evidence()
    evidence["R66_independent_original_numerical_archive_reproduced"]=False
    with pytest.raises(ValueError,match="before immutable"):
        r67.summarize_refusals(cases,evidence)
    evidence=_independent_evidence()
    evidence["original_source_checkout"]="a"*40
    with pytest.raises(ValueError,match="before immutable"):
        r67.summarize_refusals(cases,evidence)
    evidence=_independent_evidence()
    evidence["prospective_paired_primitive_block_audit"]["paired_diagnostics"][
        "extreme_minus_ordinary_zero_to_full"
    ]["prospective_95pct_primitive_block_bootstrap_percentile"]=[0,.1]
    with pytest.raises(ValueError,match="withheld"):
        r67.summarize_refusals(cases,evidence)
