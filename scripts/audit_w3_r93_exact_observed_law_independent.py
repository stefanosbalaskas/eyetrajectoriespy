"""R93-A: independent algebraic replay of immutable original near-complete observed law.

No import of R93 original proof script, simulation or production estimators.
Verifies all 27 exact rational parameterizations with independent probability
factorization and observed-likelihood identity.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path

STUDY="W3_R93_EXACT_OBSERVED_LAW_EQUIVALENCE"
PROOF_STUDY="W3_R93_A_INDEPENDENT_EXACT_OBSERVABILITY"
DELTA=(Fraction("1/1000"),Fraction("1/100"),Fraction("1/20"))
G=(Fraction("1/4"),Fraction("1/2"),Fraction("1"))
CASES=("low_mean","uniform_return","high_mean")
EXPECTED=27
EVENTS=("not_invited","invited_responded_Z0","invited_responded_Z1","invited_nonresponse")


def frac(x):
    """Reject floating-point artifacts and invalid rational text."""
    if not isinstance(x,str) or "/" not in x:
        raise ValueError("R93-A exact rational value missing")
    a,b=x.split("/")
    if not a.lstrip("-").isdigit() or not b.isdigit() or int(b)==0:
        raise ValueError("R93-A bad rational numerator/denominator")
    value=Fraction(int(a),int(b))
    if str(value)!=x:
        raise ValueError("R93-A noncanonical exact fraction")
    return value


def expected_row(d,g,case):
    """Construct latent mechanism from observed success subprobabilities."""
    successes={0:(1-d)/2,1:(1-d)/2}
    total_unreturned=1-sum(successes.values())
    if total_unreturned!=d:
        raise AssertionError("R93-A observed response mass inconsistent")
    if case=="low_mean":
        unknown_Z1=Fraction(0)
    elif case=="uniform_return":
        unknown_Z1=d/2
    elif case=="high_mean":
        unknown_Z1=d
    else:
        raise ValueError("R93-A invalid model")
    p1=successes[1]+unknown_Z1
    p0=1-p1
    c0=successes[0]/p0
    c1=successes[1]/p1
    assert 0<c0<=1 and 0<c1<=1
    observed={
        "not_invited":1-g,
        "invited_responded_Z0":g*p0*c0,
        "invited_responded_Z1":g*p1*c1,
        "invited_nonresponse":g*(p0*(1-c0)+p1*(1-c1))
    }
    return {"p0":p0,"p1":p1,"c0":c0,"c1":c1,"q0":successes[0],
            "q1":successes[1],"width":total_unreturned,"observed":observed}


def validate_archived_records(rows):
    if len(rows)!=EXPECTED:
        raise ValueError("R93-A original 27-world ledger incomplete")
    index={}
    for row in rows:
        key=(frac(row["failure_probability"]),frac(row["invitation_probability"]),row["world"])
        if key in index:
            raise ValueError("R93-A duplicate original latent parameterization")
        index[key]=row
    if set(index)!=set(product(DELTA,G,CASES)):
        raise ValueError("R93-A exact original factorial absent")
    evidence=[]
    for d,g in product(DELTA,G):
        likelihoods=[]
        means=[]
        for case in CASES:
            row=index[(d,g,case)]
            model=expected_row(d,g,case)
            if row["study"]!=STUDY or row["release_authorized"] is not False:
                raise ValueError("R93-A original science/release identity invalid")
            comparisons={
                "latent_mean_binary_Z":model["p1"],
                "unobserved_return_c0":model["c0"],
                "unobserved_return_c1":model["c1"],
                "sharp_mean_lower":model["q1"],
                "sharp_mean_upper":1-model["q0"],
                "sharp_mean_width":model["width"],
                "completion_probability_given_invitation":1-d
            }
            for field,value in comparisons.items():
                if frac(row[field])!=value:
                    raise ValueError("R93-A independent latent/source proof disagreement "+field)
            if set(row["observed_joint_law"])!=set(EVENTS):
                raise ValueError("R93-A observable event support incomplete")
            observed={k:frac(v) for k,v in row["observed_joint_law"].items()}
            if observed!=model["observed"] or sum(observed.values())!=1:
                raise ValueError("R93-A original observable law not reproduced")
            for field in ("observed_law_exactly_identical_across_three_worlds",
                          "return_propensities_are_latent_not_fitted",
                          "iid_binary_submodel_only","general_functional_identification_not_claimed",
                          "no_empirical_coverage_or_interval_claim"):
                if row[field] is not True:
                    raise ValueError("R93-A original claim boundary missing "+field)
            if set(row)!={"study","failure_probability","invitation_probability",
                         "world","latent_mean_binary_Z","unobserved_return_c0",
                         "unobserved_return_c1","observed_joint_law","sharp_mean_lower",
                         "sharp_mean_upper","sharp_mean_width",
                         "completion_probability_given_invitation",
                         "observed_law_exactly_identical_across_three_worlds",
                         "return_propensities_are_latent_not_fitted",
                         "iid_binary_submodel_only",
                         "general_functional_identification_not_claimed",
                         "no_empirical_coverage_or_interval_claim","release_authorized"}:
                raise ValueError("R93-A original row has unidentified extra fields")
            likelihoods.append(observed)
            means.append(model["p1"])
        if not likelihoods[0]==likelihoods[1]==likelihoods[2]:
            raise ValueError("R93-A original worlds statistically distinguishable")
        if means[0]>=means[1] or means[1]>=means[2] or means[2]-means[0]!=d:
            raise ValueError("R93-A sharp identification gap incorrect")
        # Independently check equality for every ordered length-three sample:
        for events in product(EVENTS,repeat=3):
            if len({__product_probability(L,events) for L in likelihoods})!=1:
                raise ValueError("R93-A three-record observed likelihood not identical")
        evidence.append({"response_failure":str(d),"known_invitation":str(g),
                         "sharp_underlying_mean_width":str(d),
                         "uniform_world_has_c0_eq_c1":True,
                         "all_observed_likelihoods_identical":True})
    return evidence


def __product_probability(law,events):
    result=Fraction(1)
    for e in events:
        result*=law[e]
    return result


def verify_archive(directory):
    content=directory/"exact_rational_evidence.json"
    checkfile=directory/"SHA256SUMS"
    if not content.is_file() or not checkfile.is_file():
        raise ValueError("R93-A complete original SHA256 archive required")
    manifest=checkfile.read_text().strip().splitlines()
    if len(manifest)!=1 or "  " not in manifest[0]:
        raise ValueError("R93-A original proof manifest malformed")
    checksum,filename=manifest[0].split("  ",1)
    if filename!="exact_rational_evidence.json" or checksum!=sha256(content.read_bytes()).hexdigest():
        raise ValueError("R93-A original rational proof SHA256 does not match")
    original=json.loads(content.read_text())
    if original["study"]!=STUDY or original["exact_rational_laws"]!=EXPECTED:
        raise ValueError("R93-A original study metadata mismatch")
    if original["release_authorized"] is not False:
        raise ValueError("R93-A original release incorrectly authorized")
    for field in ("nonidentification_even_at_99p9pct_return",
                  "finite_pop_point_recovery_not_claimed",
                  "real_sensor_validation_not_claimed",
                  "simultaneous_confidence_band_calibration_not_claimed"):
        if original[field] is not True:
            raise ValueError("R93-A original source boundary false")
    groups=validate_archived_records(original["records"])
    return {"study":PROOF_STUDY,"independently_replayed_original_exact_worlds":EXPECTED,
            "observational_equivalence_groups":len(groups),
            "original_sha256":checksum,"groups":groups,
            "exact_probability_likelihood_indistinguishability":True,
            "unknown_real_response_mechanism_not_identified":True,
            "public_package_changed":False,"release_authorized":False}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--original",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    result=verify_archive(args.original)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"study":PROOF_STUDY,"verified":EXPECTED,
                      "identified":False,"release_authorized":False}))


if __name__=="__main__":
    main()
