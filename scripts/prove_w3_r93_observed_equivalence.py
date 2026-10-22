"""R93: exact observed-law equivalence at 99.9%, 99%, or 95% audit return.

Research-only binary bounded-outcome submodel counterexample, not a package API,
a fitted MNAR model, functional slope inference or nominal confidence interval.
All probabilities are exact rationals, not Monte Carlo point estimates.
"""
from __future__ import annotations

import argparse
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path

STUDY="W3_R93_EXACT_OBSERVED_LAW_EQUIVALENCE"
FAILURE_FRACTIONS=(Q(1,1000),Q(1,100),Q(1,20))
INVITATION_FRACTIONS=(Q(1,4),Q(1,2),Q(1))
OUTCOME_STRATA=("binary_bounded_originally_missing",)
WORLDS=("low_mean","uniform_return","high_mean")
EXPECTED_ROWS=len(FAILURE_FRACTIONS)*len(INVITATION_FRACTIONS)*len(WORLDS)
RELEASE_AUTHORIZED=False


def rational(x):
    return str(x.numerator)+"/"+str(x.denominator)


def probability_world(failure,case):
    """Underlying binary outcome P(Z=1) and response c(z), conditional on invitation.

    The three mechanisms have the same observed success masses q0=q1=(1-d)/2.
    Success count and labels alone cannot determine unreturned mass assignment.
    """
    if failure not in FAILURE_FRACTIONS or case not in WORLDS:
        raise ValueError("R93 unregistered failure/world")
    q=(1-failure)/2
    if case=="low_mean":
        p1=q
    elif case=="uniform_return":
        p1=Q(1,2)
    else:
        p1=q+failure
    p0=1-p1
    if not (0<p1<1 and 0<p0<1):
        raise ValueError("R93 invalid source distribution")
    c0=q/p0
    c1=q/p1
    if not (0<c0<=1 and 0<c1<=1):
        raise ValueError("R93 true return propensity invalid")
    return {"p0":p0,"p1":p1,"c0":c0,"c1":c1}


def observed_law(failure,invitation,case):
    """Exact distribution for *all* observables: invitation, completion, seen Y."""
    if invitation not in INVITATION_FRACTIONS:
        raise ValueError("R93 unregistered random invitation rate")
    w=probability_world(failure,case)
    return {
        "not_invited":1-invitation,
        "invited_responded_Z0":invitation*w["p0"]*w["c0"],
        "invited_responded_Z1":invitation*w["p1"]*w["c1"],
        "invited_nonresponse":invitation*(w["p0"]*(1-w["c0"])+w["p1"]*(1-w["c1"]))
    }


def exact_identified_set(q0,q1):
    """Sharp binary source-mean region with unknown outcome-specific c0,c1."""
    if not (0<q0 and 0<q1 and q0+q1<=1):
        raise ValueError("R93 invalid observed masses")
    return (q1,1-q0)


def construct_rows():
    records=[]
    for failure in FAILURE_FRACTIONS:
      for invitation in INVITATION_FRACTIONS:
        q=(1-failure)/2
        reference=observed_law(failure,invitation,WORLDS[0])
        endpoints=exact_identified_set(q,q)
        for case in WORLDS:
            world=probability_world(failure,case)
            law=observed_law(failure,invitation,case)
            if law!=reference or sum(law.values())!=1:
                raise ValueError("R93 exact observational equivalence failed")
            if not endpoints[0]<=world["p1"]<=endpoints[1]:
                raise ValueError("R93 source mean outside exact sharp set")
            records.append({
                "study":STUDY,"failure_probability":rational(failure),
                "invitation_probability":rational(invitation),"world":case,
                "latent_mean_binary_Z":rational(world["p1"]),
                "unobserved_return_c0":rational(world["c0"]),
                "unobserved_return_c1":rational(world["c1"]),
                "observed_joint_law":{k:rational(v) for k,v in law.items()},
                "sharp_mean_lower":rational(endpoints[0]),
                "sharp_mean_upper":rational(endpoints[1]),
                "sharp_mean_width":rational(endpoints[1]-endpoints[0]),
                "completion_probability_given_invitation":rational(1-failure),
                "observed_law_exactly_identical_across_three_worlds":True,
                "return_propensities_are_latent_not_fitted":True,
                "iid_binary_submodel_only":True,
                "general_functional_identification_not_claimed":True,
                "no_empirical_coverage_or_interval_claim":True,
                "release_authorized":False
            })
    if len(records)!=EXPECTED_ROWS:
        raise ValueError("R93 missing exact-law factorial records")
    return records


def verify(rows):
    if len(rows)!=EXPECTED_ROWS:
        raise ValueError("R93 full source ledger required")
    expected={(rational(d),rational(g),case) for d in FAILURE_FRACTIONS
              for g in INVITATION_FRACTIONS for case in WORLDS}
    keyed={(r["failure_probability"],r["invitation_probability"],r["world"]):r
           for r in rows}
    if len(keyed)!=len(rows) or set(keyed)!=expected:
        raise ValueError("R93 duplicated or incomplete exact-law evidence")
    if rows!=construct_rows():
        raise ValueError("R93 exact source-rational evidence altered")
    for d in FAILURE_FRACTIONS:
      for g in INVITATION_FRACTIONS:
        cell=[keyed[(rational(d),rational(g),case)] for case in WORLDS]
        if len({json.dumps(z["observed_joint_law"],sort_keys=True) for z in cell})!=1:
            raise ValueError("R93 empirically distinguishable observed likelihood")
        if (Q(cell[-1]["latent_mean_binary_Z"])-Q(cell[0]["latent_mean_binary_Z"])!=d
            or Q(cell[0]["sharp_mean_width"])!=d):
            raise ValueError("R93 incorrect sharp identification gap")
        if (cell[1]["unobserved_return_c0"]!=rational(1-d)
            or cell[1]["unobserved_return_c1"]!=rational(1-d)):
            raise ValueError("R93 supposedly uniform world not uniform")
    return True


def evidence():
    rows=construct_rows()
    verify(rows)
    return {
       "study":STUDY,
       "observation_model":"iid binary Z conditional on originally missing stratum; Bernoulli randomized known invitations; latent outcome-dependent completion",
       "exact_rational_laws":len(rows),
       "distinct_latent_worlds_per_fixed_observed_distribution":3,
       "prespecified_failure_rates":[rational(d) for d in FAILURE_FRACTIONS],
       "prespecified_invitation_rates":[rational(g) for g in INVITATION_FRACTIONS],
       "identified_set_derivation":"given observed masses q0=P(R=1,Z=0|I=1),q1=P(R=1,Z=1|I=1), sharp p1 in [q1,1-q0]",
       "nonidentification_even_at_99p9pct_return":True,
       "finite_pop_point_recovery_not_claimed":True,
       "real_sensor_validation_not_claimed":True,
       "simultaneous_confidence_band_calibration_not_claimed":True,
       "release_authorized":False,
       "records":rows
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    obj=evidence()
    args.out.mkdir(parents=True,exist_ok=True)
    blob=(json.dumps(obj,indent=2,sort_keys=True)+"\n").encode()
    (args.out/"exact_rational_evidence.json").write_bytes(blob)
    (args.out/"SHA256SUMS").write_text(sha256(blob).hexdigest()+"  exact_rational_evidence.json\n")
    print(json.dumps({"study":STUDY,"records":EXPECTED_ROWS,
                      "sha256":sha256(blob).hexdigest(),"release_authorized":False}))


if __name__=="__main__":
    main()
