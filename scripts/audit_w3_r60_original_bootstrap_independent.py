"""Independent read-only audit of the immutable ORIGINAL R60 null replication.

Does not import R60 generator, R57/R58 source, or Gaussian REML optimizer.
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

ORIGINAL_RUN = 39067797968
SOURCE_CHECKOUT = "9424d2507a9ba38132bec1feee9af4c40263f52a"
STUDY = "W3_R60_NUISANCE_REFITTED_GAUSSIAN_H0_BOOTSTRAP_FEASIBILITY"
SEED = 202610176060
DRAW_SEED = 202610176061
B = 31
BLOCKS = 4
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
        raise ValueError("R60 independent original mismatch: " + name)


def verify_original(folder):
    root=Path(folder)
    names={"cases.json", "summary.json", "source-commit.txt"}
    manifest=(root/"SHA256SUMS").read_text().splitlines()
    if len(manifest)!=3:
        raise ValueError("R60 original SHA256 manifest incomplete")
    hashes={}
    for line in manifest:
        digest, sep, name=line.partition("  ")
        if not sep or name not in names or name in hashes or len(digest)!=64:
            raise ValueError("R60 invalid original manifest member")
        try:
            int(digest,16)
        except ValueError as exc:
            raise ValueError("R60 nonhex digest") from exc
        actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
        if actual!=digest:
            raise ValueError("R60 original SHA256 mismatch "+name)
        hashes[name]=actual
    if set(hashes)!=names:
        raise ValueError("R60 original SHA256 entries missing")
    if (root/"source-commit.txt").read_text().strip()!=SOURCE_CHECKOUT:
        raise ValueError("R60 original source checkout differs from frozen PR-merge")
    return hashes


def projected_kkt(ratios, scores, model):
    bounds=[(LOW,HIGH)]*3 + ([(0.,100.)] if model=="nonnegative" else [])
    if not isinstance(ratios,list) or not isinstance(scores,list):
        raise ValueError("R60 original missing physical score vectors")
    if len(ratios)!=len(bounds) or len(scores)!=len(bounds):
        raise ValueError("R60 original physical-score dimension mismatch")
    magnitude=0.
    for ratio,score,(lower,upper) in zip(ratios,scores,bounds):
        ratio=float(ratio);score=float(score)
        if (not math.isfinite(ratio) or not math.isfinite(score)
            or ratio<lower-1e-9 or ratio>upper+1e-9):
            raise ValueError("R60 physical ratio bound or score invalid")
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
        raise ValueError("R60 source optimizer start identities invalid "+case_id)
    if fit["status"]=="not_attempted":
        if any(s["status"]!="not_attempted" for s in stages):
            raise ValueError("R60 false original not-attempted placeholder")
        return {"status":"not_attempted","count":len(names)}
    if fit["model"]!=model or fit["status"] not in ("accepted","refused"):
        raise ValueError("R60 original fit model/status inconsistent "+case_id)
    evaluated,eligible=[],[]
    for start in stages:
        val=start["negative_loglik"]
        if val is None:
            if start["status"]=="ok":
                raise ValueError("R60 optimizer labeled ok without NLL")
            continue
        if not math.isfinite(float(val)):
            raise ValueError("R60 nonfinite original NLL")
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
            raise ValueError("R60 claimed accepted without numerical start")
        return {"status":"refused","count":len(names)}
    best=min(s["negative_loglik"] for s in evaluated)
    assert_close(best,fit["best_observed_multistart_NLL"],
                 case_id+"/observed best NLL")
    candidates=[s for s in eligible
                if s["negative_loglik"]-best<=NLL_TOL+1e-8]
    if fit["status"]=="refused":
        if candidates:
            raise ValueError("R60 refusal despite eligible multistart fit")
        return {"status":"refused","count":len(names)}
    if not candidates:
        raise ValueError("R60 false accepted model")
    chosen=[s for s in candidates if s["label"]==fit["selected_start"]]
    if len(chosen)!=1:
        raise ValueError("R60 absent original selected start")
    selected=chosen[0]
    assert_close(selected["negative_loglik"],fit["selected_NLL"],
                 case_id+"/selected likelihood")
    assert_close(min(s["negative_loglik"] for s in candidates),
                 fit["selected_NLL"],case_id+"/eligible minimum")
    assert_close(selected["physical_projected_KKT"],
                 fit["selected_physical_KKT"],case_id+"/selected KKT")
    if fit["global_optimum_proven"] is not False:
        raise ValueError("R60 claimed proven REML global optimum")
    free=fit["selected_free_component_variance_ratios"]
    if len(free)!=3:
        raise ValueError("R60 original nuisance dimension")
    for actual,stored in zip(selected["ratios"][:3],free):
        assert_close(actual,stored,case_id+"/selected nuisance ratio")
    if model=="exact_zero":
        if (fit["selected_slope_ratio"]!=0. or
            fit["null_includes_exact_zero_variance"] is not True):
            raise ValueError("R60 exact zero null excluded zero")
    else:
        if fit["alternative_includes_structural_zero"] is not True:
            raise ValueError("R60 alternative does not nest zero")
        assert_close(selected["ratios"][3],fit["selected_slope_ratio"],
                     case_id+"/selected slope variance")
    return {"status":"accepted","count":len(names),
            "NLL":float(fit["selected_NLL"]),
            "slope":float(fit["selected_slope_ratio"]),
            "KKT":float(fit["selected_physical_KKT"])}


def wilson(k,n):
    if type(k) is not int or type(n) is not int or not 0<=k<=n:
        raise ValueError("R60 invalid independent Wilson inputs")
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



def audit_nested(nested,label):
    if nested["status"]=="not_attempted":
        # A missing numeric fit still requires explicit original start positions.
        a=audit_fit(nested["null_fit"],"exact_zero",label+"/H0")
        b=audit_fit(nested["alternative_fit"],"nonnegative",label+"/H1")
        if a["status"]!="not_attempted" or b["status"]!="not_attempted":
            raise ValueError("R60 missing bootstrap fit mislabeled as unattempted")
        return {"status":"not_attempted","starts":a["count"]+b["count"],
                "KKT":0.,"gap":None}
    a=audit_fit(nested["null_fit"],"exact_zero",label+"/H0")
    b=audit_fit(nested["alternative_fit"],"nonnegative",label+"/H1")
    count=a["count"]+b["count"]
    maximum=max(a.get("KKT",0.),b.get("KKT",0.))
    eligible=a["status"]=="accepted" and b["status"]=="accepted"
    if eligible:
        signed=float(2*(a["NLL"]-b["NLL"]))
        assert_close(signed,nested["raw_deviance"],label+"/nested signed NLL",atol=1e-7)
        if not math.isfinite(signed) or signed<-NEST_TOL:
            if nested["status"]!="refused":
                raise ValueError("R60 failed original nested monotonicity gate")
        else:
            if nested["status"]!="accepted":
                raise ValueError("R60 suppressed accepted Gaussian comparison")
            gap=max(0.,signed)
            assert_close(gap,nested["nonnegative_deviance"],
                         label+"/nested nonnegative deviance")
            return {"status":"accepted","starts":count,"KKT":maximum,
                    "gap":gap,"a":a,"b":b}
    if nested["status"]=="accepted":
        raise ValueError("R60 falsely accepted refused nested comparison")
    if nested["nonnegative_deviance"] is not None:
        raise ValueError("R60 refused bootstrap has populated statistic")
    return {"status":"refused","starts":count,"KKT":maximum,"gap":None}


def audit(folder):
    digest=verify_original(folder)
    root=Path(folder)
    rows=json.loads((root/"cases.json").read_text())
    original=json.loads((root/"summary.json").read_text())
    ids=[(v["block"],v["support"]) for v in rows]
    if len(ids)!=8 or set(ids)!=EXPECTED or len(set(ids))!=8:
        raise ValueError("R60 original independent source/pair denominator incomplete")
    frozen={
        "study":STUDY,"new_source_seed":SEED,"new_draw_seed":DRAW_SEED,
        "independent_Gaussian_source_blocks":BLOCKS,
        "participants_per_source":24,
        "leverage_cases_paired_not_independent":True,
        "planned_source_cases":8,"recorded_source_cases":8,
        "bootstrap_draws_per_source":B,
        "planned_H0_bootstrap_draw_slots":248,
        "recorded_H0_bootstrap_draw_slots":248,
        "planned_fitted_nested_model_slots":512,
        "planned_optimizer_start_slots":1536,
        "recorded_optimizer_start_slots":1536,
        "bootstrap_refits_both_H0_and_H1_with_new_nuisance":True,
        "bootstrap_conditioned_on_source_fitted_H0_and_original_design":True,
        "no_independent_evaluation_calibration_study":True,
        "no_validated_type_I_reference":True,
        "no_pointwise_or_simultaneous_90pct_CR2_inference":True,
        "release_authorized":False,
    }
    for field,val in frozen.items():
        if original.get(field)!=val:
            raise ValueError("R60 original frozen complete-source contract "+field)
    original_records={}
    start_count=0
    largest_KKT=0.
    for source in rows:
        block,support=source["block"],source["support"]
        label=f"{block}/{support}"
        if (source["study"]!=STUDY or source["true_slope_variance"]!=0. or
            source["planned_bootstrap_slots"]!=B or
            source["null_calibration_qualified"] is not False or
            source["pointwise_or_simultaneous_90pct_CR2_qualified"] is not False or
            source["release_authorized"] is not False):
            raise ValueError("R60 false generating truth or inferential claim "+label)
        observed=audit_nested(source["observed"],label+"/observed")
        start_count+=observed["starts"]
        largest_KKT=max(largest_KKT,observed["KKT"])
        theta=source["fitted_null_theta"]
        if observed["status"]=="accepted":
            if source["source_status"]!="ok":
                raise ValueError("R60 accepted fit despite source refusal")
            if not isinstance(theta,list) or len(theta)!=4:
                raise ValueError("R60 missing original fitted H0 theta")
            if not all(math.isfinite(float(z)) for z in theta):
                raise ValueError("R60 nonfinite fitted H0 theta")
            if theta[1]!=0. or not all(float(theta[k])>0 for k in (0,2,3)):
                raise ValueError("R60 fitted H0 has nonzero slope variance")
            observed_ref=source["observed"].get("observed_reference")
            nuisance=observed["a"]["NLL"]
            if observed_ref is None or observed_ref<=0:
                raise ValueError("R60 observed original H0 reference missing")
            fits=source["observed"]["null_fit"]["selected_free_component_variance_ratios"]
            for t,ratio in zip((theta[0],theta[2],theta[3]),fits):
                assert_close(t,float(observed_ref)*float(ratio),
                             label+"/fitted H0 physical covariance theta",
                             atol=1e-7)
            classical=bool(observed["gap"]>CRITICAL)
            if source["candidate_5pct_exceedance"] is not classical:
                raise ValueError("R60 original classical benchmark classified wrongly")
        else:
            if source["candidate_5pct_exceedance"] is not None or theta is not None:
                raise ValueError("R60 refused original classified or fitted theta")
        draws=source["bootstrap"]
        if not isinstance(draws,list) or len(draws)!=B:
            raise ValueError("R60 original Gaussian H0 bootstrap draw denominator lost")
        if [v["draw"] for v in draws]!=list(range(B)):
            raise ValueError("R60 bootstrap draw identities missing or shuffled")
        accepted=[]
        for draw in draws:
            j=draw["draw"]
            evidence=audit_nested(draw["nested"],label+f"/bootstrap/{j}")
            start_count+=evidence["starts"]
            largest_KKT=max(largest_KKT,evidence["KKT"])
            if draw["status"]!=evidence["status"]:
                raise ValueError("R60 bootstrap inner/outer status disagreement")
            if evidence["status"]=="accepted":
                expected_seed=DRAW_SEED+100003*block+739*SUPPORT.index(support)+j
                if draw["seed"]!=expected_seed:
                    raise ValueError("R60 original bootstrap seed or source ownership forged")
                accepted.append(evidence["gap"])
            elif draw["status"]=="not_attempted" and draw["seed"] is not None:
                raise ValueError("R60 never-attempted pseudo-draw has a seeded response")
        p=source["conditional_bootstrap_p"]
        if observed["status"]=="accepted" and len(accepted)==B:
            computed=(1+sum(gap>=observed["gap"] for gap in accepted))/(B+1)
            assert_close(p,computed,label+"/recomputed finite-draw add-one tail",
                         atol=1e-12)
            qualified=bool(computed<=.05)
            if source["bootstrap_5pct_exceedance"] is not qualified:
                raise ValueError("R60 bootstrap candidate rejection classification forged")
        elif p is not None or source["bootstrap_5pct_exceedance"] is not None:
            raise ValueError("R60 incomplete original bootstrap treated as valid")
        original_records[(block,support)]={
            "accepted_observed":observed["status"]=="accepted",
            "accepted_bootstrap":len(accepted),
            "conditional_p":p,
            "candidate":source["candidate_5pct_exceedance"],
            "bootstrap_005":source["bootstrap_5pct_exceedance"],
        }
    if start_count!=1536:
        raise ValueError("R60 original REML numerical start denominator violated")
    strata={}
    for support in SUPPORT:
        sample=[v for (block,s),v in original_records.items() if s==support]
        if len(sample)!=BLOCKS:
            raise ValueError("R60 independent-block source strata incomplete")
        full=[v for v in sample if v["conditional_p"] is not None]
        observed_cell={
            "independent_source_blocks":BLOCKS,
            "recorded_source_cases":len(sample),
            "original_sources_numerically_accepted":sum(
                v["accepted_observed"] for v in sample),
            "planned_bootstrap_draw_slots":BLOCKS*B,
            "recorded_bootstrap_draw_slots":BLOCKS*B,
            "accepted_bootstrap_draws":sum(v["accepted_bootstrap"] for v in sample),
            "fully_qualified_original_and_31_refit_bootstrap_sources":len(full),
            "classical_candidate_exceedances_all_sources":sum(
                v["candidate"] is True for v in sample),
            "bootstrap_p_le_005_all_sources":sum(
                v["bootstrap_005"] is True for v in sample),
            "calibrated_type_I_rate_or_power_qualified":False,
        }
        saved=original["strata"][support]
        for key,val in observed_cell.items():
            if saved[key]!=val:
                raise ValueError("R60 original source summary mismatch "+support+"/"+key)
        lookup={v["block"]:v for v in rows if v["support"]==support}
        values=[{"block":b,"p":original_records[(b,support)]["conditional_p"]}
                for b in range(BLOCKS)
                if original_records[(b,support)]["conditional_p"] is not None]
        if saved["conditional_bootstrap_p_values"]!=values:
            raise ValueError("R60 source-specific bootstrap p-values do not reproduce")
        strata[support]={**observed_cell,"conditional_bootstrap_p_values":values}
    return {
        "read_only_independent_original_R60_evidence_audit_passed":True,
        "original_run":ORIGINAL_RUN,
        "original_PR_merge_sha":SOURCE_CHECKOUT,
        "sha256_original_archive":digest,
        "original_independent_primitive_blocks":BLOCKS,
        "paired_original_source_variants":len(rows),
        "original_bootstrap_draw_slots":sum(len(r["bootstrap"]) for r in rows),
        "original_nested_model_fit_slots":512,
        "original_numerical_start_slots_recomputed":start_count,
        "maximum_selected_projected_physical_KKT":largest_KKT,
        "original_case_records_contain_no_raw_native_response_y":True,
        "original_H0_GLS_draw_covariance_not_independently_reconstructed":True,
        "conditional_bootstrap_reference_not_calibrated":True,
        "release_authorized":False,
        "strata":strata,
    }


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--original",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    result=audit(args.original)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(args.out.read_text())


if __name__=="__main__":
    main()
