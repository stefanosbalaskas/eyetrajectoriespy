"""Independent read-only audit of the immutable ORIGINAL R59 null replication.

Does not import R59 generator, R57/R58 source, or Gaussian REML optimizer.
Validates frozen SHA256 checkout, all 128 paired primitive identities,
256 null cases / 512 fit slots / 1536 start slots, physical KKT,
multistart selection, raw nested likelihood differences, 5% candidate
boundary exceedances, Wilson intervals, numerical refusals and paired table.
Raw native Gaussian responses are NOT archived; no source replay, null-law
qualification, or global optimization theorem is claimed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

ORIGINAL_RUN = 39065162776
SOURCE_CHECKOUT = "90eaac1b7b4e1e5f98ef4fa5d4f63e3ff78689cd"
STUDY = "W3_R59_INDEPENDENT_TRUE_NULL_BOUNDARY_REFERENCE_REPLICATION"
SEED = 202610175959
BLOCKS = 128
SUPPORT = ("ordinary_dependent", "extreme_dependent")
EXPECTED = {(b,s) for b in range(BLOCKS) for s in SUPPORT}
NULL_STARTS = ("null_compact", "null_spread")
ALT_STARTS = ("alt_at_exact_zero", "alt_tiny_positive",
              "alt_positive", "alt_wide")
LOW, HIGH = math.exp(-13.8), math.exp(7.)
CRITICAL = 2.70554345409542
KKT_TOL, NLL_TOL, RECON_TOL, NEST_TOL = .001, .001, 1e-6, 1e-5
Z = 1.959963984540054


def assert_close(observed, expected, name, atol=1e-8, rtol=1e-9):
    if (observed is None or expected is None
            or not math.isfinite(float(observed))
            or not math.isfinite(float(expected))
            or not math.isclose(float(observed),float(expected),
                                abs_tol=atol,rel_tol=rtol)):
        raise ValueError("R59 independent original mismatch: " + name)


def verify_original(folder):
    root=Path(folder)
    names={"cases.json", "summary.json", "source-commit.txt"}
    manifest=(root/"SHA256SUMS").read_text().splitlines()
    if len(manifest)!=3:
        raise ValueError("R59 original SHA256 manifest incomplete")
    hashes={}
    for line in manifest:
        digest, sep, name=line.partition("  ")
        if not sep or name not in names or name in hashes or len(digest)!=64:
            raise ValueError("R59 invalid original manifest member")
        try:
            int(digest,16)
        except ValueError as exc:
            raise ValueError("R59 nonhex digest") from exc
        actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
        if actual!=digest:
            raise ValueError("R59 original SHA256 mismatch "+name)
        hashes[name]=actual
    if set(hashes)!=names:
        raise ValueError("R59 original SHA256 entries missing")
    if (root/"source-commit.txt").read_text().strip()!=SOURCE_CHECKOUT:
        raise ValueError("R59 original source checkout differs from frozen PR-merge")
    return hashes


def projected_kkt(ratios, scores, model):
    bounds=[(LOW,HIGH)]*3 + ([(0.,100.)] if model=="nonnegative" else [])
    if not isinstance(ratios,list) or not isinstance(scores,list):
        raise ValueError("R59 original missing physical score vectors")
    if len(ratios)!=len(bounds) or len(scores)!=len(bounds):
        raise ValueError("R59 original physical-score dimension mismatch")
    magnitude=0.
    for ratio,score,(lower,upper) in zip(ratios,scores,bounds):
        ratio=float(ratio);score=float(score)
        if (not math.isfinite(ratio) or not math.isfinite(score)
            or ratio<lower-1e-9 or ratio>upper+1e-9):
            raise ValueError("R59 physical ratio bound or score invalid")
        if ratio<=lower+1e-9:
            score=min(score,0.)
        elif ratio>=upper-1e-9:
            score=max(score,0.)
        magnitude=max(magnitude,abs(score))
    return magnitude


def audit_fit(fit, model, case_id):
    names=NULL_STARTS if model=="exact_zero" else ALT_STARTS
    stages=fit["original_starts"]
    if len(stages)!=len(names) or [s["label"] for s in stages]!=list(names):
        raise ValueError("R59 source optimizer start identities invalid "+case_id)
    if fit["status"]=="not_attempted":
        if any(s["status"]!="not_attempted" for s in stages):
            raise ValueError("R59 false original not-attempted placeholder")
        return {"status":"not_attempted","count":len(names)}
    if fit["model"]!=model or fit["status"] not in ("accepted","refused"):
        raise ValueError("R59 original fit model/status inconsistent "+case_id)
    evaluated,eligible=[],[]
    for start in stages:
        val=start["negative_loglik"]
        if val is None:
            if start["status"]=="ok":
                raise ValueError("R59 optimizer labeled ok without NLL")
            continue
        if not math.isfinite(float(val)):
            raise ValueError("R59 nonfinite original NLL")
        evaluated.append(start)
        assert_close(val,start["reconstructed_loglik"],
                     case_id+"/original reconstructed likelihood",
                     atol=RECON_TOL+1e-8)
        kkt=projected_kkt(start["ratios"],start["physical_score"],model)
        assert_close(kkt,start["physical_projected_KKT"],
                     case_id+"/physical KKT",atol=2e-7,rtol=5e-7)
        if (start["status"]=="ok" and
                start["optimizer_success"] is True and
                float(start["objective_reconstruction_error"])<=RECON_TOL and
                kkt<=KKT_TOL):
            eligible.append(start)
    if not evaluated:
        if fit["status"]!="refused":
            raise ValueError("R59 claimed accepted without numerical start")
        return {"status":"refused","count":len(names)}
    best=min(s["negative_loglik"] for s in evaluated)
    assert_close(best,fit["best_observed_multistart_NLL"],
                 case_id+"/observed best NLL")
    candidates=[s for s in eligible
                if s["negative_loglik"]-best<=NLL_TOL+1e-8]
    if fit["status"]=="refused":
        if candidates:
            raise ValueError("R59 refusal despite eligible multistart fit")
        return {"status":"refused","count":len(names)}
    if not candidates:
        raise ValueError("R59 false accepted model")
    chosen=[s for s in candidates if s["label"]==fit["selected_start"]]
    if len(chosen)!=1:
        raise ValueError("R59 absent original selected start")
    selected=chosen[0]
    assert_close(selected["negative_loglik"],fit["selected_NLL"],
                 case_id+"/selected likelihood")
    assert_close(min(s["negative_loglik"] for s in candidates),
                 fit["selected_NLL"],case_id+"/eligible minimum")
    assert_close(selected["physical_projected_KKT"],
                 fit["selected_physical_KKT"],case_id+"/selected KKT")
    if fit["global_optimum_proven"] is not False:
        raise ValueError("R59 claimed proven REML global optimum")
    free=fit["selected_free_component_variance_ratios"]
    if len(free)!=3:
        raise ValueError("R59 original nuisance dimension")
    for actual,stored in zip(selected["ratios"][:3],free):
        assert_close(actual,stored,case_id+"/selected nuisance ratio")
    if model=="exact_zero":
        if (fit["selected_slope_ratio"]!=0. or
            fit["null_includes_exact_zero_variance"] is not True):
            raise ValueError("R59 exact zero null excluded zero")
    else:
        if fit["alternative_includes_structural_zero"] is not True:
            raise ValueError("R59 alternative does not nest zero")
        assert_close(selected["ratios"][3],fit["selected_slope_ratio"],
                     case_id+"/selected slope variance")
    return {"status":"accepted","count":len(names),
            "NLL":float(fit["selected_NLL"]),
            "slope":float(fit["selected_slope_ratio"]),
            "KKT":float(fit["selected_physical_KKT"])}


def wilson(k,n):
    if type(k) is not int or type(n) is not int or not 0<=k<=n:
        raise ValueError("R59 invalid independent Wilson inputs")
    if n==0:return None
    p=k/n; d=1+Z*Z/n
    c=(p+Z*Z/(2*n))/d
    h=Z*math.sqrt(p*(1-p)/n+Z*Z/(4*n*n))/d
    return [max(0.,c-h),min(1.,c+h)]


def median(values):
    seq=sorted(values)
    if not seq:return None
    n=len(seq)
    return (seq[n//2] if n%2 else (seq[n//2-1]+seq[n//2])/2)


def audit(folder):
    digest=verify_original(folder)
    rows=json.loads((Path(folder)/"cases.json").read_text())
    original=json.loads((Path(folder)/"summary.json").read_text())
    ids=[(x["block"],x["support"]) for x in rows]
    if len(ids)!=256 or set(ids)!=EXPECTED or len(set(ids))!=256:
        raise ValueError("R59 original 128 independent paired sources incomplete")
    frozen={"study":STUDY,"new_Gaussian_independent_primitive_blocks":BLOCKS,
       "source_seed":SEED,"participants_per_block":24,
       "paired_ordinary_extreme_not_independent":True,
       "generating_slope_variance_exact_zero":True,
       "planned_cases":256,"recorded_cases":256,
       "planned_H0_H1_model_slots":512,"recorded_H0_H1_model_slots":512,
       "planned_optimizer_start_slots":1536,"recorded_optimizer_start_slots":1536,
       "classical_half_mixture_reference_is_candidate_not_proven":True,
       "no_positive_source_or_power_simulation":True,
       "no_90pct_CR2_pointwise_or_simultaneous_qualification":True,
       "release_authorized":False}
    for key,val in frozen.items():
        if original.get(key)!=val:
            raise ValueError("R59 original source summary mismatch "+key)
    assert_close(original["candidate_cutoff_strict_greater"],
                 CRITICAL,"frozen classical candidate cutoff",atol=1e-11)
    assert_close(original["candidate_reference_alpha"],.05,
                 "frozen candidate alpha",atol=1e-12)
    records=[]
    starts=0
    max_kkt=0.
    for case in rows:
        block,support=case["block"],case["support"]
        key=f"{block}/{support}"
        if (case["study"]!=STUDY or
            case["generating_state"]!="true_zero" or
            case["new_independent_primitive_block"] is not True or
            case["paired_across_leverage_not_independent"] is not True or
            case["pointwise_or_simultaneous_CR2_qualified"] is not False or
            case["release_authorized"] is not False):
            raise ValueError("R59 source case changed scientific truth")
        assert_close(case["true_slope_variance"],0.,key+"/true slope zero")
        a=audit_fit(case["null_fit"],"exact_zero",key+"/H0")
        b=audit_fit(case["alternative_fit"],"nonnegative",key+"/H1")
        starts+=a["count"]+b["count"]
        for f in (a,b):max_kkt=max(max_kkt,f.get("KKT",0.))
        comp=case["comparison"]
        accepted=a["status"]==b["status"]=="accepted"
        if comp["null_reference_validated"] is not False:
            raise ValueError("R59 claimed validated classical null reference")
        result={"block":block,"support":support,
            "source":case["source_status"],"H0":a["status"],"H1":b["status"],
            "accepted":False,"exceed":None,"at_zero":None,"deviance":None}
        if case["source_status"]!="ok" and accepted:
            raise ValueError("R59 false fit after source refusal")
        if accepted:
            raw=float(2*(a["NLL"]-b["NLL"]))
            assert_close(raw,comp["raw_signed_deviance"],key+"/raw NLL gap",
                         atol=1e-7)
            if not math.isfinite(raw) or raw<-NEST_TOL:
                if comp["status"]!="refused":
                    raise ValueError("R59 improperly accepted invalid nested gap")
            else:
                if comp["status"]!="ok":
                    raise ValueError("R59 refused numerically eligible nested gap")
                dev=max(0.,raw)
                assert_close(dev,comp["nonnegative_deviance"],
                             key+"/nonnegative nested gap")
                p=1. if dev==0. else .5*math.erfc(math.sqrt(dev/2.))
                assert_close(p,comp["candidate_half_chisquare_p"],
                             key+"/candidate half chi-square tail",atol=1e-10)
                exceed=bool(dev>CRITICAL)
                zero=bool(b["slope"]<=1e-10)
                if (comp["candidate_nominal_005_exceedance"] is not exceed or
                    comp["H1_selected_exact_zero"] is not zero):
                    raise ValueError("R59 false candidate null exceedance")
                result.update(accepted=True,exceed=exceed,at_zero=zero,
                              deviance=dev)
        elif comp["status"]=="ok":
            raise ValueError("R59 numerically unaccepted case falsely counted")
        if not result["accepted"] and (
            comp["candidate_nominal_005_exceedance"] is not None or
            comp["candidate_half_chisquare_p"] is not None):
            raise ValueError("R59 refused fit reclassified as a hypothesis test")
        records.append(result)
    if starts!=1536:
        raise ValueError("R59 incomplete original numeric optimizer start ledger")
    strata={}
    for support in SUPPORT:
        subset=[r for r in records if r["support"]==support]
        accepted=[r for r in subset if r["accepted"]]
        n=len(accepted);k=sum(r["exceed"] is True for r in accepted)
        refused=BLOCKS-n
        expected_cell={
            "planned_new_independent_primitive_blocks":BLOCKS,
            "recorded_null_source_cases":len(subset),
            "source_generation_failures":sum(r["source"]!="ok" for r in subset),
            "null_model_numeric_refusals":sum(r["H0"]!="accepted" for r in subset),
            "alternative_model_numeric_refusals":sum(
                r["H1"]!="accepted" for r in subset),
            "nested_reference_numeric_refusals":refused,
            "accepted_candidate_calculations":n,
            "candidate_exceedances":k,
            "candidate_exceedance_fraction_accepted_only":k/n if n else None,
            "candidate_exceedance_Wilson95_accepted_only":wilson(k,n),
            "all_source_lower_assuming_refusals_no_exceedance":k/BLOCKS,
            "all_source_upper_assuming_refusals_all_exceedance":(k+refused)/BLOCKS,
            "selected_exact_zero_count":sum(
                r["at_zero"] is True for r in accepted),
            "median_accepted_nested_deviance":median(
                [r["deviance"] for r in accepted]),
            "reference_distribution_qualified":False,
        }
        observed_cell=original["strata"][support]
        for name,val in expected_cell.items():
            stored=observed_cell[name]
            if isinstance(val,list):
                if not isinstance(stored,list) or len(stored)!=len(val):
                    raise ValueError("R59 original Wilson structure mismatch")
                for x,y in zip(val,stored):
                    assert_close(x,y,support+"/"+name,atol=1e-9)
            elif isinstance(val,(int,float)) and not isinstance(val,bool):
                assert_close(val,stored,support+"/"+name,atol=1e-9)
            elif val!=stored:
                raise ValueError("R59 original summary classification mismatch "+name)
        strata[support]=expected_cell
    pairs={(r["block"],r["support"]):r for r in records}
    paired=[(pairs[(b,SUPPORT[0])],pairs[(b,SUPPORT[1])])
            for b in range(BLOCKS)]
    both=[(a["exceed"],b["exceed"]) for a,b in paired
          if a["accepted"] and b["accepted"]]
    paired_fields={
        "both_leverage_candidate_comparisons_accepted":len(both),
        "paired_ordinary_only_exceedance":sum(a and not b for a,b in both),
        "paired_extreme_only_exceedance":sum(b and not a for a,b in both),
        "paired_both_exceedances":sum(a and b for a,b in both),
        "paired_neither_exceedances":sum(not a and not b for a,b in both),
    }
    for name,val in paired_fields.items():
        if original[name]!=val:
            raise ValueError("R59 source-paired exceedance counts not reproducible")
    return {
        "immutable_R59_original_numerical_evidence_audit_passed":True,
        "source_run":ORIGINAL_RUN,
        "frozen_original_PR_merge_checkout":SOURCE_CHECKOUT,
        "verified_original_SHA256":digest,
        "distinct_independent_Gaussian_primitive_blocks":BLOCKS,
        "paired_support_case_count":len(records),
        "original_selected_H0_H1_model_slots":2*len(records),
        "original_optimizer_start_slots_checked":starts,
        "max_selected_KKT":max_kkt,
        "source_pairing_claim_based_on_archived_metadata":True,
        "native_Gaussian_Y_not_archived":True,
        "raw_native_generating_source_not_independently_replayed":True,
        "candidate_half_chisquare_reference_not_qualified":True,
        "release_authorized":False,
        "paired":paired_fields,
        "strata":strata,
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--original",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    result=audit(args.original)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(args.out.read_text())


if __name__=="__main__":
    main()
