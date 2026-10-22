"""R95-A independent immutable-original replay by assigning missing binary Z1 mass.

Does not import original R95 script or any public package estimator.
"""
from __future__ import annotations
import argparse
from fractions import Fraction as Q
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

SOURCE="W3_R95_MONOTONE_AUDIT_RETURN_IDENTIFICATION"
AUDIT="W3_R95_A_INDEPENDENT_MONOTONICITY_REPLAY"
D=(Q(1,1000),Q(1,100),Q(1,20))
G=(Q(1,4),Q(1,2),Q(1))
CASES=("unrestricted","c1_at_least_c0","c0_at_least_c1",
       "equal_completion","c1_ge_c0_ratio_le_1_plus_delta","direction_unknown_union")
EXPECTED=54


def frac(v):
    if not isinstance(v,str) or "/" not in v:
        raise ValueError("R95-A source must supply canonical fraction")
    f=Q(v)
    if f"{f.numerator}/{f.denominator}"!=v:
        raise ValueError("R95-A noncanonical rational evidence")
    return f


def s(v):
    return f"{v.numerator}/{v.denominator}"


def missing_mass_region(q0,q1,d,shape):
    """Independent derivation: t = latent unseen Z1 mass, 0 <= t <= d."""
    if q0<=0 or q1<=0 or q0+q1+d!=1 or d<=0:
        raise ValueError("R95-A invalid observed source model")
    if shape not in CASES:
        raise ValueError("R95-A unspecified monotonic condition")
    a,b=Q(0),d
    equal_t=q1*d/(q0+q1)
    if shape in ("c1_at_least_c0","c1_ge_c0_ratio_le_1_plus_delta"):
        b=min(b,equal_t)
    elif shape=="c0_at_least_c1":
        a=max(a,equal_t)
    elif shape=="equal_completion":
        a=b=equal_t
    if shape=="c1_ge_c0_ratio_le_1_plus_delta":
        # c1 / c0 <= (1+d), substitute p=q1+t in conditional return law
        # t >= q1 * (d-d*q0) / (q1+(1+d)*q0)
        a=max(a,q1*(d-d*q0)/(q1+(1+d)*q0))
    if a>b:raise ValueError("R95-A empty exact monotone region")
    return (q1+a,q1+b)


def endpoint(p,q0,q1):
    c0=q0/(1-p);c1=q1/p
    if not (0<c0<=1 and 0<c1<=1):
        raise ValueError("R95-A invalid endpoint completion")
    return {"p":s(p),"c0":s(c0),"c1":s(c1),"response_ratio_c1_over_c0":s(c1/c0)}


def replay(rows):
    if not isinstance(rows,list) or len(rows)!=EXPECTED:
        raise ValueError("R95-A actual full 54-case source ledger required")
    found={}
    for r in rows:
        key=(frac(r["invited_nonreturn"]),frac(r["known_random_invitation"]),r["external_direction_assumption"])
        if key in found:raise ValueError("R95-A duplicate frozen assumption cell")
        found[key]=r
    if set(found)!=set(product(D,G,CASES)):
        raise ValueError("R95-A missing original experiment cell")
    for d,g,shape in product(D,G,CASES):
        q0=q1=(1-d)/2
        low,high=missing_mass_region(q0,q1,d,shape)
        actual=found[(d,g,shape)]
        law={"not_invited":s(1-g),
             "invited_return_Z0":s(g*q0),
             "invited_return_Z1":s(g*q1),
             "invited_nonreturn":s(g*d)}
        expected={
            "study":SOURCE,"invited_nonreturn":s(d),"known_random_invitation":s(g),
            "external_direction_assumption":shape,
            "observed_conditional_q0":s(q0),"observed_conditional_q1":s(q1),
            "observed_joint_law":law,
            "sharp_lower":s(low),"sharp_upper":s(high),"sharp_width":s(high-low),
            "lower_endpoint_witness":endpoint(low,q0,q1),
            "upper_endpoint_witness":endpoint(high,q0,q1),
            "response_direction_is_not_observed_or_estimated":True,
            "simulator_sources_or_monte_carlo_claimed":False,
            "real_missing_gaze_identification_claimed":False,
            "functional_confidence_coverage_claimed":False,
            "release_authorized":False,
        }
        if actual!=expected:
            fields=sorted(k for k in set(actual)|set(expected) if actual.get(k)!=expected.get(k))
            raise ValueError("R95-A full original source replay mismatch "+str(fields))
        for p in (low,high):
            c0=q0/(1-p);c1=q1/p
            if shape=="c1_at_least_c0" and c1<c0:raise ValueError("R95-A direction failure")
            if shape=="c0_at_least_c1" and c0<c1:raise ValueError("R95-A reverse failure")
            if shape=="equal_completion" and c0!=c1:raise ValueError("R95-A equality failure")
            if shape=="c1_ge_c0_ratio_le_1_plus_delta" and not c0<=c1<=(1+d)*c0:
                raise ValueError("R95-A ratio-cap failure")
    return {"source_records_independently_replayed":EXPECTED,"distinct_known_invitation_laws":9,
            "all_exact_witnesses_verified":True,"no_coverage_claim":True}


def verify_archive(directory):
    data=directory/"r95_exact_source.json"
    manifest=directory/"SHA256SUMS"
    if not data.is_file() or not manifest.is_file():
        raise ValueError("R95-A mandatory original archive members missing")
    lines=manifest.read_text().strip().splitlines()
    if len(lines)!=1 or "  " not in lines[0]:
        raise ValueError("R95-A malformed original SHA256SUMS")
    digest,filename=lines[0].split("  ",1)
    if filename!="r95_exact_source.json" or digest!=sha256(data.read_bytes()).hexdigest():
        raise ValueError("R95-A original SHA256 integrity failure")
    obj=json.loads(data.read_text())
    if obj["study"]!=SOURCE or obj["source_rows"]!=EXPECTED or obj["release_authorized"] is not False:
        raise ValueError("R95-A original study/release identity mismatch")
    if any(obj[f] is not True for f in ("no_observed_data_identification_of_direction",
                                       "mandatory_independent_immutable_original_artifact_replay",
                                       "no_empirical_coverage_or_functional_band_claim")):
        raise ValueError("R95-A original scientific boundaries absent")
    return {"audit":AUDIT,"original_source_sha256":digest,**replay(obj["records"]),
            "research_only":True,"release_authorized":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--original",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    report=verify_archive(a.original)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"replayed":EXPECTED,"release_authorized":False}))

if __name__=="__main__":main()
