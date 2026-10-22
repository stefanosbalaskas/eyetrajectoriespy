"""R95: exact binary sharp-set sensitivity to an EXTERNALLY known return direction.

Research-only population identification theorem. No sampled gaze, fitted missingness,
confidence intervals, coverage qualification, public API or release.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as F
from hashlib import sha256
import json
from pathlib import Path

STUDY="W3_R95_MONOTONE_AUDIT_RETURN_IDENTIFICATION"
FAILURES=(F(1,1000),F(1,100),F(1,20))
INVITATIONS=(F(1,4),F(1,2),F(1))
ASSUMPTIONS=("unrestricted","c1_at_least_c0","c0_at_least_c1",
             "equal_completion","c1_ge_c0_ratio_le_1_plus_delta","direction_unknown_union")
EXPECTED=54
RELEASE_AUTHORIZED=False


def canonical(v):
    return f"{v.numerator}/{v.denominator}"


def sharp_interval(q0,q1,assumption,delta=None):
    """Sharp population P(Z=1) interval under externally stipulated c1/c0 sign/cap.

    q0=(1-p)c0 and q1=p*c1. None of these shape assumptions can be learned
    solely from observed audit returns; delta is an exact sensitivity cap.
    """
    if not all(isinstance(x,F) for x in (q0,q1)):
        raise TypeError("R95 probabilities must be exact rational")
    if not (0<q0 and 0<q1 and q0+q1<=1):
        raise ValueError("R95 invalid observed subprobabilities")
    if assumption not in ASSUMPTIONS:
        raise ValueError("R95 unregistered shape assumption")
    lower=q1
    upper=1-q0
    pivot=q1/(q0+q1)
    if assumption in ("c1_at_least_c0","c1_ge_c0_ratio_le_1_plus_delta"):
        upper=min(upper,pivot)
    if assumption=="c0_at_least_c1":
        lower=max(lower,pivot)
    if assumption=="equal_completion":
        lower=upper=pivot
    if assumption=="c1_ge_c0_ratio_le_1_plus_delta":
        if not isinstance(delta,F) or not 0<delta<1:
            raise ValueError("R95 exact cap delta required")
        lower=max(lower,q1/(q1+(1+delta)*q0))
    return lower,upper


def point_witness(p,q0,q1,assumption,delta=None):
    if not (F(0)<p<F(1)):
        raise ValueError("R95 noninterior latent mean")
    c0=q0/(1-p)
    c1=q1/p
    if not (0<c0<=1 and 0<c1<=1):
        raise ValueError("R95 latent completion probability invalid")
    if assumption=="c1_at_least_c0" and c1<c0:
        raise ValueError("R95 increasing direction violated")
    if assumption=="c0_at_least_c1" and c0<c1:
        raise ValueError("R95 decreasing direction violated")
    if assumption=="equal_completion" and c0!=c1:
        raise ValueError("R95 equality violated")
    if assumption=="c1_ge_c0_ratio_le_1_plus_delta" and not (c0<=c1<=(1+delta)*c0):
        raise ValueError("R95 capped ratio violated")
    return {"p":canonical(p),"c0":canonical(c0),"c1":canonical(c1),
            "response_ratio_c1_over_c0":canonical(c1/c0)}


def rows():
    result=[]
    for delta in FAILURES:
        q=(1-delta)/2
        for g in INVITATIONS:
            for a in ASSUMPTIONS:
                low,high=sharp_interval(q,q,a,delta)
                if not (low<=high):
                    raise AssertionError("R95 impossible research cell")
                left=point_witness(low,q,q,a,delta)
                right=point_witness(high,q,q,a,delta)
                event_law={
                    "not_invited":canonical(1-g),
                    "invited_return_Z0":canonical(g*q),
                    "invited_return_Z1":canonical(g*q),
                    "invited_nonreturn":canonical(g*delta),
                }
                result.append({
                    "study":STUDY,
                    "invited_nonreturn":canonical(delta),
                    "known_random_invitation":canonical(g),
                    "external_direction_assumption":a,
                    "observed_conditional_q0":canonical(q),
                    "observed_conditional_q1":canonical(q),
                    "observed_joint_law":event_law,
                    "sharp_lower":canonical(low),
                    "sharp_upper":canonical(high),
                    "sharp_width":canonical(high-low),
                    "lower_endpoint_witness":left,
                    "upper_endpoint_witness":right,
                    "response_direction_is_not_observed_or_estimated":True,
                    "simulator_sources_or_monte_carlo_claimed":False,
                    "real_missing_gaze_identification_claimed":False,
                    "functional_confidence_coverage_claimed":False,
                    "release_authorized":False,
                })
    if len(result)!=EXPECTED:
        raise ValueError("R95 missing planned mathematical cells")
    return result


def verify(records):
    if len(records)!=EXPECTED:
        raise ValueError("R95 complete evidence ledger required")
    index={(r["invited_nonreturn"],r["known_random_invitation"],
             r["external_direction_assumption"]):r for r in records}
    expected={(canonical(d),canonical(g),a) for d in FAILURES for g in INVITATIONS for a in ASSUMPTIONS}
    if len(index)!=len(records) or set(index)!=expected:
        raise ValueError("R95 missing or duplicated assumption scenarios")
    if records!=rows():
        raise ValueError("R95 source evidence altered")
    for d in FAILURES:
        for g in INVITATIONS:
            cell={a:index[(canonical(d),canonical(g),a)] for a in ASSUMPTIONS}
            if F(cell["unrestricted"]["sharp_width"])!=d:
                raise ValueError("R95 unrestricted incorrect")
            for s in ("c1_at_least_c0","c0_at_least_c1"):
                if F(cell[s]["sharp_width"])!=d/2:
                    raise ValueError("R95 direction only should halve symmetric width")
            if F(cell["equal_completion"]["sharp_width"])!=0:
                raise ValueError("R95 equal response should point-identify")
            if not F(0)<F(cell["c1_ge_c0_ratio_le_1_plus_delta"]["sharp_width"])<d/2:
                raise ValueError("R95 capped direction not strictly tighter")
            if cell["unrestricted"]["sharp_lower"]!=cell["direction_unknown_union"]["sharp_lower"] or cell["unrestricted"]["sharp_upper"]!=cell["direction_unknown_union"]["sharp_upper"]:
                raise ValueError("R95 unspecified monotone sign cannot narrow set")
            obs=[json.dumps(cell[a]["observed_joint_law"],sort_keys=True) for a in ASSUMPTIONS]
            if len(set(obs))!=1:
                raise ValueError("R95 latent assumptions changed observable likelihood")
    return True


def evidence():
    original=rows()
    verify(original)
    return {"study":STUDY,"source_rows":EXPECTED,
            "interpretation":"external monotonic direction can one-side-restrict binary population identified set; unknown direction alone cannot",
            "no_observed_data_identification_of_direction":True,
            "mandatory_independent_immutable_original_artifact_replay":True,
            "no_empirical_coverage_or_functional_band_claim":True,
            "release_authorized":False,"records":original}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,required=True)
    opts=parser.parse_args()
    a=evidence()
    opts.out.mkdir(parents=True,exist_ok=True)
    blob=(json.dumps(a,sort_keys=True,indent=2)+"\n").encode()
    (opts.out/"r95_exact_source.json").write_bytes(blob)
    (opts.out/"SHA256SUMS").write_text(sha256(blob).hexdigest()+"  r95_exact_source.json\n")
    print(json.dumps({"source_rows":EXPECTED,"sha256":sha256(blob).hexdigest(),"release_authorized":False}))


if __name__=="__main__":
    main()
