"""R94-A: independent missing-Z1 mass allocation and original SHA256 evidence replay.

Deliberately imports no R94 original proof or public package estimator.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

SOURCE="W3_R94_EXTERNAL_COMPLETION_FLOOR_SHARP_SETS"
AUDIT="W3_R94_A_INDEPENDENT_ORIGINAL_FLOOR_REPLAY"
DELTA=(Q(1,1000),Q(1,100),Q(1,20))
G=(Q(1,4),Q(1,2),Q(1))
CASES=("unrestricted","weak_common","moderate_common","strong_common","asymmetric","overstrong_incompatible")
EXPECTED=54


def rational(z):
    return f"{z.numerator}/{z.denominator}"


def decode(x):
    if not isinstance(x,str) or "/" not in x:
        raise ValueError("R94-A non-rational source number")
    z=Q(x)
    if f"{z.numerator}/{z.denominator}"!=x:
        raise ValueError("R94-A unnormalized or tampered rational")
    return z


def design_floors(d,s):
    if s=="unrestricted":return (Q(0),Q(0))
    if s=="weak_common":return (1-2*d,1-2*d)
    if s=="moderate_common":return (1-Q(3,2)*d,1-Q(3,2)*d)
    if s=="strong_common":return (1-d,1-d)
    if s=="asymmetric":return (1-d,1-2*d)
    if s=="overstrong_incompatible":return (1-d/2,1-d/2)
    raise ValueError("R94-A unrecognized external assumption")


def missing_outcome_allocation(q0,q1,min0,min1):
    """Independent algebra: unobserved Z1 mass t; unobserved Z0 = d-t."""
    if not (0<q0 and 0<q1 and q0+q1<=1 and 0<=min0<=1 and 0<=min1<=1):
        raise ValueError("R94-A invalid source law or external floor")
    d=1-q0-q1
    a=Q(0)
    b=d
    if min0:
        a=max(a,d-q0*(1/min0-1))
    if min1:
        b=min(b,q1*(1/min1-1))
    if a>b:
        return None
    return (q1+a,q1+b)


def witness_for(p,q0,q1):
    if not (0<p<1):
        raise ValueError("R94-A noninterior underlying p")
    c0=q0/(1-p)
    c1=q1/p
    return {"p":rational(p),"c0":rational(c0),"c1":rational(c1)}


def replay_rows(rows):
    if not isinstance(rows,list) or len(rows)!=EXPECTED:
        raise ValueError("R94-A full original 54-record archive required")
    observed={}
    for row in rows:
        key=(decode(row["failure_among_invited"]),decode(row["random_invitation_probability"]),row["external_assumption"])
        if key in observed:
            raise ValueError("R94-A duplicate original design cell")
        observed[key]=row
    if set(observed)!=set(product(DELTA,G,CASES)):
        raise ValueError("R94-A missing original factorial case")
    count_feasible=0
    for d,g,s in product(DELTA,G,CASES):
        row=observed[(d,g,s)]
        q0=q1=(1-d)/2
        f0,f1=design_floors(d,s)
        p_set=missing_outcome_allocation(q0,q1,f0,f1)
        expected={
            "study":SOURCE,
            "failure_among_invited":rational(d),
            "random_invitation_probability":rational(g),
            "external_assumption":s,
            "externally_guaranteed_minimum_c0":rational(f0),
            "externally_guaranteed_minimum_c1":rational(f1),
            "observed_responded_Z0_given_invitation":rational(q0),
            "observed_responded_Z1_given_invitation":rational(q1),
            "baseline_identification_width":rational(d),
            "assumptions_feasible":p_set is not None,
            "sharp_lower":None if p_set is None else rational(p_set[0]),
            "sharp_upper":None if p_set is None else rational(p_set[1]),
            "sharp_width":None if p_set is None else rational(p_set[1]-p_set[0]),
            "lower_endpoint_witness":None if p_set is None else witness_for(p_set[0],q0,q1),
            "upper_endpoint_witness":None if p_set is None else witness_for(p_set[1],q0,q1),
            "external_floors_are_not_inferred_from_observed_data":True,
            "no_finite_sample_confidence_or_coverage_claim":True,
            "does_not_identify_real_gaze_or_functional_bands":True,
            "release_authorized":False
        }
        if row!=expected:
            diff=[k for k in (set(row)|set(expected)) if row.get(k)!=expected.get(k)]
            raise ValueError("R94-A independently calculated original cell mismatch "+str(diff))
        if p_set is not None:
            count_feasible+=1
            for p in p_set:
                model=witness_for(p,q0,q1)
                if not (f0<=decode(model["c0"])<=1 and f1<=decode(model["c1"])<=1):
                    raise ValueError("R94-A purported sharp endpoint cannot be attained")
                if (1-p)*decode(model["c0"])!=q0 or p*decode(model["c1"])!=q1:
                    raise ValueError("R94-A endpoint changes observed event law")
    if count_feasible!=45:
        raise ValueError("R94-A unexpected rejection count")
    return {"source_records_exactly_replayed":EXPECTED,"feasible":count_feasible,"incompatible":EXPECTED-count_feasible,
            "no_identification_claim_without_external_floors":True}


def verify_archive(directory):
    ledger=directory/"r94_exact_evidence.json"
    manifest=directory/"SHA256SUMS"
    if not ledger.is_file() or not manifest.is_file():
        raise ValueError("R94-A complete immutable original archive required")
    lines=manifest.read_text().strip().splitlines()
    if len(lines)!=1 or "  " not in lines[0]:
        raise ValueError("R94-A malformed SHA256 manifest")
    digest,filename=lines[0].split("  ",1)
    if filename!="r94_exact_evidence.json" or sha256(ledger.read_bytes()).hexdigest()!=digest:
        raise ValueError("R94-A actual original SHA256 mismatch")
    record=json.loads(ledger.read_text())
    if record["study"]!=SOURCE or record["record_count"]!=EXPECTED or record["release_authorized"] is not False:
        raise ValueError("R94-A original source identity mismatch")
    for field in ("invitation_randomization_only_scales_observable_event_masses",
                  "external_floors_are_hypothetical_not_estimated",
                  "models_with_empty_identification_region_are_falsified_conditionally_on_observed_law",
                  "independent_original_archive_audit_required_before_publication"):
        if record[field] is not True:
            raise ValueError("R94-A source provenance or guardrail missing")
    result=replay_rows(record["rows"])
    return {"audit":AUDIT,"source":SOURCE,"original_SHA256":digest,
            **result,"no_public_API_change":True,"release_authorized":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--original",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    result=verify_archive(args.original)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"original_records_verified":result["source_records_exactly_replayed"],
                      "incompatible":result["incompatible"],"release_authorized":False}))

if __name__=="__main__":
    main()
