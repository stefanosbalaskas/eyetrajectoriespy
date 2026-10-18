"""Read-only independent audit of R63's immutable fitted-H0 Gaussian bootstrap.

Uses only Python standard library and the ORIGINAL completed Actions artifact,
not imports from the R57/R60/R63 generators, REML fitters or source summary.
Reconstructs source-level p values from 63 archived likelihood deviances,
physical score/KKT gates, failure-inclusive full source denominators, Wilson
Monte Carlo uncertainty and paired ordinary/extreme rejection counts.
This checks numerical reporting, not the archived Gaussian random generator,
statistical calibration, Type-I error control, power, or any public API.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import NormalDist

STUDY = "W3_R63_INDEPENDENT_OUTER_NULL_NUISANCE_REFIT_GAUSSIAN_PILOT"
SOURCE_SEED = 202610186363
DRAW_SEED = 202610186364
BLOCKS, B = 128, 63
SUPPORT = ("ordinary_dependent", "extreme_dependent")
ALPHA = .05
BOUNDARY_CUTOFF = 2.70554345409542
KKT_TOL, NLL_TOL, RECON_TOL, NEST_TOL = .001, .001, 1e-6, 1e-5
LOW, HIGH = math.exp(-13.8), math.exp(7.)
NULL_STARTS = ("null_compact", "null_spread")
ALT_STARTS = ("alt_at_exact_zero", "alt_tiny_positive", "alt_positive", "alt_wide")


def _same(a, b, label, *, atol=2e-7, rtol=1e-7):
    if a is None or b is None or not math.isfinite(float(a)) or not math.isfinite(float(b)):
        raise ValueError("R63 independent missing/nonfinite value: " + label)
    if not math.isclose(float(a), float(b), abs_tol=atol, rel_tol=rtol):
        raise ValueError("R63 independent discrepancy: " + label)


def _wilson(count, number):
    if not isinstance(count, int) or not isinstance(number, int) or not 0 <= count <= number:
        raise ValueError("R63 invalid Wilson independent-unit count")
    if not number:
        return None
    z = NormalDist().inv_cdf(.975)
    p = count / number
    divisor = 1. + z*z/number
    center = (p + z*z/(2*number))/divisor
    half = z*math.sqrt(p*(1-p)/number + z*z/(4*number*number))/divisor
    return [max(0., center-half), min(1.,center+half)]


def _audit_sha(folder):
    root = Path(folder)
    expected = {"cases.json", "summary.json", "source-commit.txt"}
    lines = (root/"SHA256SUMS").read_text().splitlines()
    if len(lines) != 3:
        raise ValueError("R63 original aggregate requires exactly three SHA256 entries")
    verified = {}
    for line in lines:
        digest, sep, name = line.partition("  ")
        if not sep or name not in expected or name in verified or len(digest) != 64:
            raise ValueError("R63 malformed or duplicate checksum entry")
        try:
            int(digest,16)
        except ValueError as exc:
            raise ValueError("R63 checksum digest is not hexadecimal") from exc
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
            raise ValueError("R63 original SHA256 mismatch: " + name)
        verified[name] = digest
    if set(verified) != expected:
        raise ValueError("R63 original aggregate checksum member missing")
    checkout = (root/"source-commit.txt").read_text().strip()
    if len(checkout)!=40 or not all(c in "0123456789abcdef" for c in checkout):
        raise ValueError("R63 malformed archived original checkout SHA")
    return verified, checkout


def _projected_kkt(start, model):
    bounds = [(LOW,HIGH)]*3 + ([(0.,100.)] if model=="nonnegative" else [])
    x, g = start.get("ratios"), start.get("physical_score")
    if not isinstance(x,list) or not isinstance(g,list) or len(x)!=len(bounds) or len(g)!=len(bounds):
        raise ValueError("R63 original physical score or component-ratio dimensions missing")
    residual = 0.
    for value, score, (lo,hi) in zip(x,g,bounds):
        value,score=float(value),float(score)
        if not math.isfinite(value) or not math.isfinite(score) or value < lo-1e-9 or value > hi+1e-9:
            raise ValueError("R63 original physical component or score invalid")
        if value<=lo+1e-9:
            score=min(score,0.)
        elif value>=hi-1e-9:
            score=max(score,0.)
        residual=max(residual,abs(score))
    return residual


def _fit(fit, model, where):
    expected = NULL_STARTS if model=="exact_zero" else ALT_STARTS
    starts = fit["original_starts"]
    if len(starts)!=len(expected) or [x["label"] for x in starts]!=list(expected):
        raise ValueError("R63 original nested optimizer start identities changed: " + where)
    if fit["status"]=="not_attempted":
        if any(x["status"]!="not_attempted" for x in starts):
            raise ValueError("R63 fake unattempted fit: " + where)
        return {"status":"not_attempted","slots":len(expected),"max_kkt":0.}
    if fit.get("model")!=model or fit["status"] not in ("accepted","refused"):
        raise ValueError("R63 nested model/status inconsistent: " + where)
    measured = []
    eligible = []
    for start in starts:
        objective = start["negative_loglik"]
        if objective is None:
            if start["status"]=="ok":
                raise ValueError("R63 reported successful optimizer without NLL")
            continue
        _same(objective,start["reconstructed_loglik"],where+"/objective",atol=RECON_TOL+1e-8)
        kkt = _projected_kkt(start,model)
        _same(kkt,start["physical_projected_KKT"],where+"/physical KKT")
        measured.append(start)
        if (start["status"]=="ok" and start["optimizer_success"] is True
            and float(start["objective_reconstruction_error"])<=RECON_TOL
            and kkt<=KKT_TOL):
            eligible.append(start)
    if not measured:
        if fit["status"]=="accepted":
            raise ValueError("R63 accepted nested model without finite start")
        return {"status":"refused","slots":len(expected),"max_kkt":0.}
    best = min(s["negative_loglik"] for s in measured)
    _same(best,fit["best_observed_multistart_NLL"],where+"/best observed NLL")
    candidates = [s for s in eligible if s["negative_loglik"]-best<=NLL_TOL+1e-8]
    if fit["status"]=="refused":
        if candidates:
            raise ValueError("R63 refused model with eligible start: " + where)
        return {"status":"refused","slots":len(expected),"max_kkt":0.}
    if not candidates:
        raise ValueError("R63 accepted model with no eligible optimizer start: " + where)
    selected = [s for s in candidates if s["label"]==fit["selected_start"]]
    if len(selected)!=1:
        raise ValueError("R63 accepted start not in eligible multistart set: " + where)
    selected=selected[0]
    _same(selected["negative_loglik"], fit["selected_NLL"], where+"/selected NLL")
    _same(min(s["negative_loglik"] for s in candidates), fit["selected_NLL"],
          where+"/best eligible NLL")
    _same(selected["physical_projected_KKT"],fit["selected_physical_KKT"],
          where+"/selected KKT")
    if fit["global_optimum_proven"] is not False:
        raise ValueError("R63 claimed a proven global nuisance optimum")
    if model=="exact_zero":
        if fit["selected_slope_ratio"]!=0. or fit["null_includes_exact_zero_variance"] is not True:
            raise ValueError("R63 H0 does not contain exact zero variance")
    elif fit["alternative_includes_structural_zero"] is not True:
        raise ValueError("R63 H1 does not nest structural zero")
    return {"status":"accepted","slots":len(expected),
            "nll":float(fit["selected_NLL"]),
            "max_kkt":float(fit["selected_physical_KKT"])}


def _nested(nested, where):
    a = _fit(nested["null_fit"],"exact_zero",where+"/H0")
    b = _fit(nested["alternative_fit"],"nonnegative",where+"/H1")
    slots=a["slots"]+b["slots"]
    max_kkt=max(a["max_kkt"],b["max_kkt"])
    if nested["status"]=="not_attempted":
        if a["status"]!="not_attempted" or b["status"]!="not_attempted":
            raise ValueError("R63 original not-attempted nested fit has attempt records")
        return {"status":"not_attempted","slots":slots,"kkt":max_kkt,"gap":None}
    if a["status"]=="accepted" and b["status"]=="accepted":
        raw=2*(a["nll"]-b["nll"])
        _same(raw,nested["raw_deviance"],where+"/deviance",atol=1e-7)
        if math.isfinite(raw) and raw>=-NEST_TOL:
            if nested["status"]!="accepted":
                raise ValueError("R63 concealed accepted nested likelihood comparison")
            gap=max(0.,raw)
            _same(gap,nested["nonnegative_deviance"],where+"/clipped deviance")
            return {"status":"accepted","slots":slots,"kkt":max_kkt,"gap":gap}
    if nested["status"]!="refused" or nested["nonnegative_deviance"] is not None:
        raise ValueError("R63 invalid failed nested likelihood state")
    return {"status":"refused","slots":slots,"kkt":max_kkt,"gap":None}


def audit_original(folder, *, expected_original_checkout=None):
    """Verify original aggregated cases without calling original estimator code."""
    checked, checkout=_audit_sha(folder)
    if expected_original_checkout is not None and checkout != expected_original_checkout:
        raise ValueError("R63 immutable original PR-merge checkout differs from pinned reference")
    folder=Path(folder)
    cases=json.loads((folder/"cases.json").read_text())
    stored=json.loads((folder/"summary.json").read_text())
    expected={(i,s) for i in range(BLOCKS) for s in SUPPORT}
    keys=[(row["block"],row["support"]) for row in cases]
    if len(keys)!=256 or len(set(keys))!=256 or set(keys)!=expected:
        raise ValueError("R63 original 128 independent primitive blocks / paired cases missing")
    frozen={
        "study":STUDY,
        "new_source_seed":SOURCE_SEED,"new_draw_seed":DRAW_SEED,
        "independent_Gaussian_source_blocks":BLOCKS,
        "participants_per_source":24,
        "leverage_cases_paired_not_independent":True,
        "planned_source_cases":256,"recorded_source_cases":256,
        "bootstrap_draws_per_source":B,
        "planned_H0_bootstrap_draw_slots":16128,
        "recorded_H0_bootstrap_draw_slots":16128,
        "planned_fitted_nested_model_slots":32768,
        "planned_optimizer_start_slots":98304,
        "recorded_optimizer_start_slots":98304,
        "bootstrap_refits_both_H0_and_H1_with_new_nuisance":True,
        "bootstrap_conditioned_on_source_fitted_H0_and_original_design":True,
        "candidate_add_one_bootstrap_rank_grid_denominator":64,
        "no_prior_source_used_for_critical_tuning":True,
        "no_validated_type_I_reference":True,
        "no_pointwise_or_simultaneous_90pct_CR2_inference":True,
        "release_authorized":False,
    }
    for key, value in frozen.items():
        if stored.get(key)!=value:
            raise ValueError("R63 frozen original summary mismatch: "+key)
    largest_kkt=0.
    starts=0
    records={}
    for row in cases:
        key=(row["block"],row["support"])
        where=str(key)
        if (row["study"]!=STUDY or row["true_slope_variance"]!=0.
            or row["planned_bootstrap_slots"]!=B
            or row["null_calibration_qualified"] is not False
            or row["pointwise_or_simultaneous_90pct_CR2_qualified"] is not False
            or row["release_authorized"] is not False):
            raise ValueError("R63 original source changed its true null or release gates")
        seen=_nested(row["observed"],where+"/observed")
        starts+=seen["slots"]
        largest_kkt=max(largest_kkt,seen["kkt"])
        theta=row["fitted_null_theta"]
        if seen["status"]=="accepted":
            if row["source_status"]!="ok" or not isinstance(theta,list) or len(theta)!=4:
                raise ValueError("R63 accepted original fit missing fitted H0 covariance")
            if theta[1]!=0. or not all(
                math.isfinite(float(theta[i])) and float(theta[i])>0 for i in (0,2,3)
            ):
                raise ValueError("R63 fitted H0 nuisance covariance invalid")
            ratio=row["observed"]["null_fit"]["selected_free_component_variance_ratios"]
            ref=row["observed"].get("observed_reference")
            if ref is None or ref<=0 or len(ratio)!=3:
                raise ValueError("R63 fitted H0 reference/ratio missing")
            for physical,free in zip((theta[0],theta[2],theta[3]),ratio):
                _same(physical,float(ref)*float(free),where+"/fitted covariance component")
            if row["candidate_5pct_exceedance"] is not bool(seen["gap"]>BOUNDARY_CUTOFF):
                raise ValueError("R63 original classical mixture-candidate count altered")
        else:
            if theta is not None or row["candidate_5pct_exceedance"] is not None:
                raise ValueError("R63 rejected original fit reported a test result")
        draws=row["bootstrap"]
        if not isinstance(draws,list) or [d["draw"] for d in draws]!=list(range(B)):
            raise ValueError("R63 original Gaussian bootstrap slots not consecutive 0..62")
        accepted=[]
        for draw in draws:
            j=draw["draw"]
            fit=_nested(draw["nested"],where+f"/bootstrap/{j}")
            starts+=fit["slots"]
            largest_kkt=max(largest_kkt,fit["kkt"])
            if draw["status"]!=fit["status"]:
                raise ValueError("R63 bootstrap outer versus nested fit status differs")
            if fit["status"]=="accepted":
                expected_seed=DRAW_SEED+100003*row["block"]+739*SUPPORT.index(row["support"])+j
                if draw["seed"]!=expected_seed:
                    raise ValueError("R63 original Gaussian bootstrap draw seed not reproducible")
                accepted.append(fit["gap"])
            elif fit["status"]=="not_attempted" and draw["seed"] is not None:
                raise ValueError("R63 not-attempted Gaussian bootstrap with seed")
        conditional=row["conditional_bootstrap_p"]
        if seen["status"]=="accepted" and len(accepted)==B:
            calc=(1+sum(x>=seen["gap"] for x in accepted))/(B+1)
            _same(conditional,calc,where+"/original add-one bootstrap p",atol=1e-12,rtol=0)
            if row["bootstrap_5pct_exceedance"] is not bool(calc<=ALPHA):
                raise ValueError("R63 Gaussian bootstrap 5% rejection misreported")
        elif conditional is not None or row["bootstrap_5pct_exceedance"] is not None:
            raise ValueError("R63 incomplete bootstrap improperly assigned valid p")
        records[key]={
            "source_accepted":seen["status"]=="accepted",
            "accepted_draws":len(accepted),
            "p":conditional,
            "bootstrap_reject":row["bootstrap_5pct_exceedance"],
            "classical_reject":row["candidate_5pct_exceedance"],
        }
    if starts!=98304:
        raise ValueError("R63 independent optimizer-start denominator corrupted")
    strata={}
    for support in SUPPORT:
        originals=[records[(b,support)] for b in range(BLOCKS)]
        complete=[r for r in originals if r["p"] is not None]
        n=len(complete)
        rejects=sum(r["bootstrap_reject"] is True for r in complete)
        refused=BLOCKS-n
        accepted_originals=sum(r["source_accepted"] for r in originals)
        accepted_draws=sum(r["accepted_draws"] for r in originals)
        classical=sum(r["classical_reject"] is True for r in originals)
        expected_cell={
            "independent_source_blocks":BLOCKS,
            "recorded_source_cases":BLOCKS,
            "original_sources_numerically_accepted":accepted_originals,
            "planned_bootstrap_draw_slots":BLOCKS*B,
            "recorded_bootstrap_draw_slots":BLOCKS*B,
            "accepted_bootstrap_draws":accepted_draws,
            "source_cases_with_all_63_numerical_bootstrap_refits":n,
            "source_cases_with_refused_or_incomplete_bootstrap":refused,
            "bootstrap_candidate_nominal_005_rejections_complete_sources":rejects,
            "bootstrap_all_source_lower_refusals_as_nonrejection":rejects/BLOCKS,
            "bootstrap_all_source_upper_refusals_as_rejection":(rejects+refused)/BLOCKS,
            "classical_candidate_exceedances_accepted_sources":classical,
            "calibrated_type_I_rate_or_power_qualified":False,
        }
        original=stored["strata"][support]
        for field,v in expected_cell.items():
            if original.get(field)!=v:
                raise ValueError(f"R63 source summary count mismatch {support}/{field}")
        percent=rejects/n if n else None
        if percent is not None:
            _same(percent,original["bootstrap_candidate_nominal_005_fraction_complete_sources"],
                  support+"/success-only rejection")
        elif original["bootstrap_candidate_nominal_005_fraction_complete_sources"] is not None:
            raise ValueError("R63 source reports success-only rate with no accepted source")
        ci=_wilson(rejects,n)
        if ci is None:
            if original["bootstrap_candidate_nominal_005_Wilson95_complete_sources"] is not None:
                raise ValueError("R63 source Wilson when no complete source")
        else:
            for actual,ref in zip(original["bootstrap_candidate_nominal_005_Wilson95_complete_sources"],ci):
                _same(actual,ref,support+"/Wilson bootstrap",atol=1e-8)
        classical_n=accepted_originals
        observed_classical=_wilson(classical,classical_n)
        if observed_classical is not None:
            for actual,ref in zip(original["classical_candidate_Wilson95_accepted_sources"],observed_classical):
                _same(actual,ref,support+"/Wilson classical",atol=1e-8)
        expected_p=[{"block":b,"p":records[(b,support)]["p"]} for b in range(BLOCKS)
                    if records[(b,support)]["p"] is not None]
        if original["conditional_bootstrap_p_values"]!=expected_p:
            raise ValueError("R63 source-level conditional p-value list inconsistent")
        strata[support]={**expected_cell,
                         "bootstrap_rate_complete":percent,
                         "bootstrap_Wilson95_complete":ci,
                         "classical_rate_accepted":classical/classical_n if classical_n else None}
    joined=[(records[(b,SUPPORT[0])],records[(b,SUPPORT[1])]) for b in range(BLOCKS)]
    both_complete=[(a["bootstrap_reject"],b["bootstrap_reject"]) for a,b in joined
                   if a["p"] is not None and b["p"] is not None]
    expected_pairs={
        "paired_both_complete":len(both_complete),
        "paired_bootstrap_ordinary_only_exceedances":
            sum(a and not b for a,b in both_complete),
        "paired_bootstrap_extreme_only_exceedances":
            sum(b and not a for a,b in both_complete),
        "paired_bootstrap_both_exceedances":sum(a and b for a,b in both_complete),
        "paired_bootstrap_neither_exceedances":sum(not a and not b for a,b in both_complete),
    }
    for field,val in expected_pairs.items():
        if stored.get(field)!=val:
            raise ValueError("R63 original paired independent-block table differs: "+field)
    return {
        "original_R63_independent_numerical_evidence_reproduced":True,
        "original_sha256_entries_verified":len(checked),
        "original_source_checkout":checkout,
        "independent_blocks":BLOCKS,
        "paired_source_cases":len(cases),
        "original_bootstrap_draw_slots":256*B,
        "nested_model_slots":32768,
        "optimizer_start_slots":starts,
        "largest_selected_projected_KKT":largest_kkt,
        "paired":expected_pairs,
        "strata":strata,
        "source_arrays_not_in_aggregate":True,
        "not_a_test_of_5pct_size_or_global_REML_optimality":True,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--expected-original-checkout",default=None)
    args=p.parse_args()
    v=audit_original(args.original,expected_original_checkout=args.expected_original_checkout)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(v,sort_keys=True,indent=2)+"\n")
    print(json.dumps(v,sort_keys=True))


if __name__=="__main__":
    main()
