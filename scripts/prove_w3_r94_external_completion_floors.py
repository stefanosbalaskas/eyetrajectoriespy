"""R94: exact sharp binary mean sets under externally justified response floors.

Research-only mathematical sensitivity analysis. No fitted response law, raw gaze
recovery, confidence/coverage claims, or production API changes.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path

STUDY = "W3_R94_EXTERNAL_COMPLETION_FLOOR_SHARP_SETS"
DELTA = (Q(1,1000), Q(1,100), Q(1,20))
INVITATIONS = (Q(1,4), Q(1,2), Q(1))
SCENARIOS = ("unrestricted", "weak_common", "moderate_common", "strong_common", "asymmetric", "overstrong_incompatible")
EXPECTED_ROWS = len(DELTA)*len(INVITATIONS)*len(SCENARIOS)
RELEASE_AUTHORIZED = False


def rational(x):
    return str(x.numerator) + "/" + str(x.denominator)


def response_floors(delta, case):
    if delta not in DELTA or case not in SCENARIOS:
        raise ValueError("R94 unregistered design")
    options = {
        "unrestricted": (Q(0), Q(0)),
        "weak_common": (1-2*delta, 1-2*delta),
        "moderate_common": (1-Q(3,2)*delta, 1-Q(3,2)*delta),
        "strong_common": (1-delta, 1-delta),
        "asymmetric": (1-delta, 1-2*delta),
        "overstrong_incompatible": (1-delta/2, 1-delta/2),
    }
    return options[case]


def sharp_set(q0, q1, floor0=Q(0), floor1=Q(0)):
    """P(Z=1) sharp interval, or None if assumed floors contradict observed law.

    q0=(1-p)c0, q1=p*c1; floors c0>=floor0 and c1>=floor1.
    Lower=max(q1,1-q0/floor0) if floor0>0.
    Upper=min(1-q0,q1/floor1) if floor1>0.
    Endpoint source models explicitly attain all nonempty bounds.
    """
    args=(q0,q1,floor0,floor1)
    if any(not isinstance(z,Q) for z in args):
        raise TypeError("R94 probabilities must be exact rational Fractions")
    if not (0<q0 and 0<q1 and q0+q1<=1 and 0<=floor0<=1 and 0<=floor1<=1):
        raise ValueError("R94 invalid observed masses or completion floors")
    lower=q1
    upper=1-q0
    if floor0:
        lower=max(lower,1-q0/floor0)
    if floor1:
        upper=min(upper,q1/floor1)
    return None if lower>upper else (lower,upper)


def witnessed_model(p,q0,q1,floor0,floor1):
    if not (0<p<1):
        raise ValueError("R94 endpoint mean outside interior")
    c0=q0/(1-p)
    c1=q1/p
    if not (floor0<=c0<=1 and floor1<=c1<=1):
        raise ValueError("R94 endpoint response violates externally assumed floor")
    if ((1-p)*c0,p*c1)!=(q0,q1):
        raise ValueError("R94 inconsistent endpoint observed law")
    return {"p":rational(p),"c0":rational(c0),"c1":rational(c1)}


def construct_rows():
    rows=[]
    for delta in DELTA:
        q0=q1=(1-delta)/2
        base=sharp_set(q0,q1)
        for g in INVITATIONS:
            for case in SCENARIOS:
                f0,f1=response_floors(delta,case)
                bounds=sharp_set(q0,q1,f0,f1)
                lower_model=None if bounds is None else witnessed_model(bounds[0],q0,q1,f0,f1)
                upper_model=None if bounds is None else witnessed_model(bounds[1],q0,q1,f0,f1)
                rows.append({
                    "study":STUDY,
                    "failure_among_invited":rational(delta),
                    "random_invitation_probability":rational(g),
                    "external_assumption":case,
                    "externally_guaranteed_minimum_c0":rational(f0),
                    "externally_guaranteed_minimum_c1":rational(f1),
                    "observed_responded_Z0_given_invitation":rational(q0),
                    "observed_responded_Z1_given_invitation":rational(q1),
                    "baseline_identification_width":rational(base[1]-base[0]),
                    "assumptions_feasible":bounds is not None,
                    "sharp_lower":None if bounds is None else rational(bounds[0]),
                    "sharp_upper":None if bounds is None else rational(bounds[1]),
                    "sharp_width":None if bounds is None else rational(bounds[1]-bounds[0]),
                    "lower_endpoint_witness":lower_model,
                    "upper_endpoint_witness":upper_model,
                    "external_floors_are_not_inferred_from_observed_data":True,
                    "no_finite_sample_confidence_or_coverage_claim":True,
                    "does_not_identify_real_gaze_or_functional_bands":True,
                    "release_authorized":False,
                })
    if len(rows)!=EXPECTED_ROWS:
        raise ValueError("R94 incomplete frozen factorial")
    return rows


def verify(rows):
    expected={(rational(d),rational(g),s) for d in DELTA for g in INVITATIONS for s in SCENARIOS}
    if len(rows)!=EXPECTED_ROWS:
        raise ValueError("R94 full evidence ledger required")
    actual=[(r["failure_among_invited"],r["random_invitation_probability"],r["external_assumption"]) for r in rows]
    if len(set(actual))!=len(actual) or set(actual)!=expected:
        raise ValueError("R94 duplicated or missing cells")
    if rows!=construct_rows():
        raise ValueError("R94 exact archived proof altered")
    for d in DELTA:
        for g in INVITATIONS:
            cells={r["external_assumption"]:r for r in rows if r["failure_among_invited"]==rational(d) and r["random_invitation_probability"]==rational(g)}
            if Q(cells["unrestricted"]["sharp_width"])!=d or Q(cells["weak_common"]["sharp_width"])!=d:
                raise ValueError("R94 negative control incorrectly shrank bound")
            if not (Q(0)<Q(cells["moderate_common"]["sharp_width"])<d):
                raise ValueError("R94 moderate floor invalid")
            if Q(cells["strong_common"]["sharp_width"])!=0:
                raise ValueError("R94 strong bound must point-identify within frozen model")
            if Q(cells["asymmetric"]["sharp_width"])!=d/2:
                raise ValueError("R94 asymmetric bound should halve width")
            if cells["overstrong_incompatible"]["assumptions_feasible"]:
                raise ValueError("R94 impossible external lower floors not flagged")
    return True


def evidence():
    rows=construct_rows()
    verify(rows)
    return {"study":STUDY, "record_count":len(rows),
            "interpretation":"exact sharp population identification conditional on unverifiable-from-observed-data external response floors, binary originally missing stratum only",
            "invitation_randomization_only_scales_observable_event_masses":True,
            "external_floors_are_hypothetical_not_estimated":True,
            "models_with_empty_identification_region_are_falsified_conditionally_on_observed_law":True,
            "independent_original_archive_audit_required_before_publication":True,
            "release_authorized":False, "rows":rows}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    a=parser.parse_args()
    obj=evidence()
    a.out.mkdir(parents=True,exist_ok=True)
    blob=(json.dumps(obj,sort_keys=True,indent=2)+"\n").encode("utf-8")
    (a.out/"r94_exact_evidence.json").write_bytes(blob)
    (a.out/"SHA256SUMS").write_text(sha256(blob).hexdigest()+"  r94_exact_evidence.json\n")
    print(json.dumps({"rows":len(obj["rows"]),"sha256":sha256(blob).hexdigest(),"release_authorized":False}))


if __name__=="__main__":
    main()
