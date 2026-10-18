"""Read-only independent audit of R64's immutable fitted-H0 Gaussian bootstrap.

Uses only Python standard library and the ORIGINAL completed Actions artifact,
not imports from the R57/R60/R64 generators, REML fitters or source summary.
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

STUDY = "W3_R64_ZERO_VS_POSITIVE_SLOPE_GAUSSIAN_DETECTION_PILOT"
SOURCE_SEED = 202610186464
DRAW_SEED = 202610186465
BLOCKS, B = 32, 63
SUPPORT = ("ordinary_dependent", "extreme_dependent")
ALPHA = .05
BOUNDARY_CUTOFF = 2.70554345409542
KKT_TOL, NLL_TOL, RECON_TOL, NEST_TOL = .001, .001, 1e-6, 1e-5
LOW, HIGH = math.exp(-13.8), math.exp(7.)
NULL_STARTS = ("null_compact", "null_spread")
ALT_STARTS = ("alt_at_exact_zero", "alt_tiny_positive", "alt_positive", "alt_wide")


def _same(a, b, label, *, atol=2e-7, rtol=1e-7):
    if a is None or b is None or not math.isfinite(float(a)) or not math.isfinite(float(b)):
        raise ValueError("R64 independent missing/nonfinite value: " + label)
    if not math.isclose(float(a), float(b), abs_tol=atol, rel_tol=rtol):
        raise ValueError("R64 independent discrepancy: " + label)


def _wilson(count, number):
    if not isinstance(count, int) or not isinstance(number, int) or not 0 <= count <= number:
        raise ValueError("R64 invalid Wilson independent-unit count")
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
        raise ValueError("R64 original aggregate requires exactly three SHA256 entries")
    verified = {}
    for line in lines:
        digest, sep, name = line.partition("  ")
        if not sep or name not in expected or name in verified or len(digest) != 64:
            raise ValueError("R64 malformed or duplicate checksum entry")
        try:
            int(digest,16)
        except ValueError as exc:
            raise ValueError("R64 checksum digest is not hexadecimal") from exc
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
            raise ValueError("R64 original SHA256 mismatch: " + name)
        verified[name] = digest
    if set(verified) != expected:
        raise ValueError("R64 original aggregate checksum member missing")
    checkout = (root/"source-commit.txt").read_text().strip()
    if len(checkout)!=40 or not all(c in "0123456789abcdef" for c in checkout):
        raise ValueError("R64 malformed archived original checkout SHA")
    return verified, checkout


def _projected_kkt(start, model):
    bounds = [(LOW,HIGH)]*3 + ([(0.,100.)] if model=="nonnegative" else [])
    x, g = start.get("ratios"), start.get("physical_score")
    if not isinstance(x,list) or not isinstance(g,list) or len(x)!=len(bounds) or len(g)!=len(bounds):
        raise ValueError("R64 original physical score or component-ratio dimensions missing")
    residual = 0.
    for value, score, (lo,hi) in zip(x,g,bounds):
        value,score=float(value),float(score)
        if not math.isfinite(value) or not math.isfinite(score) or value < lo-1e-9 or value > hi+1e-9:
            raise ValueError("R64 original physical component or score invalid")
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
        raise ValueError("R64 original nested optimizer start identities changed: " + where)
    if fit["status"]=="not_attempted":
        if any(x["status"]!="not_attempted" for x in starts):
            raise ValueError("R64 fake unattempted fit: " + where)
        return {"status":"not_attempted","slots":len(expected),"max_kkt":0.}
    if fit.get("model")!=model or fit["status"] not in ("accepted","refused"):
        raise ValueError("R64 nested model/status inconsistent: " + where)
    measured = []
    eligible = []
    for start in starts:
        objective = start["negative_loglik"]
        if objective is None:
            if start["status"]=="ok":
                raise ValueError("R64 reported successful optimizer without NLL")
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
            raise ValueError("R64 accepted nested model without finite start")
        return {"status":"refused","slots":len(expected),"max_kkt":0.}
    best = min(s["negative_loglik"] for s in measured)
    _same(best,fit["best_observed_multistart_NLL"],where+"/best observed NLL")
    candidates = [s for s in eligible if s["negative_loglik"]-best<=NLL_TOL+1e-8]
    if fit["status"]=="refused":
        if candidates:
            raise ValueError("R64 refused model with eligible start: " + where)
        return {"status":"refused","slots":len(expected),"max_kkt":0.}
    if not candidates:
        raise ValueError("R64 accepted model with no eligible optimizer start: " + where)
    selected = [s for s in candidates if s["label"]==fit["selected_start"]]
    if len(selected)!=1:
        raise ValueError("R64 accepted start not in eligible multistart set: " + where)
    selected=selected[0]
    _same(selected["negative_loglik"], fit["selected_NLL"], where+"/selected NLL")
    _same(min(s["negative_loglik"] for s in candidates), fit["selected_NLL"],
          where+"/best eligible NLL")
    _same(selected["physical_projected_KKT"],fit["selected_physical_KKT"],
          where+"/selected KKT")
    if fit["global_optimum_proven"] is not False:
        raise ValueError("R64 claimed a proven global nuisance optimum")
    if model=="exact_zero":
        if fit["selected_slope_ratio"]!=0. or fit["null_includes_exact_zero_variance"] is not True:
            raise ValueError("R64 H0 does not contain exact zero variance")
    elif fit["alternative_includes_structural_zero"] is not True:
        raise ValueError("R64 H1 does not nest structural zero")
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
            raise ValueError("R64 original not-attempted nested fit has attempt records")
        return {"status":"not_attempted","slots":slots,"kkt":max_kkt,"gap":None}
    if a["status"]=="accepted" and b["status"]=="accepted":
        raw=2*(a["nll"]-b["nll"])
        _same(raw,nested["raw_deviance"],where+"/deviance",atol=1e-7)
        if math.isfinite(raw) and raw>=-NEST_TOL:
            if nested["status"]!="accepted":
                raise ValueError("R64 concealed accepted nested likelihood comparison")
            gap=max(0.,raw)
            _same(gap,nested["nonnegative_deviance"],where+"/clipped deviance")
            return {"status":"accepted","slots":slots,"kkt":max_kkt,"gap":gap}
    if nested["status"]!="refused" or nested["nonnegative_deviance"] is not None:
        raise ValueError("R64 invalid failed nested likelihood state")
    return {"status":"refused","slots":slots,"kkt":max_kkt,"gap":None}


LEVELS = ("zero","half","full")
MULTIPLIER = {"zero":0.0,"half":0.5,"full":1.0}
TRUE_SLOPE_SD = 0.045
SOURCE_CASES = 192
SOURCE_DRAWS = 12096
SOURCE_MODELS = 24576
SOURCE_STARTS = 73728


def _variance(level):
    return (MULTIPLIER[level] * TRUE_SLOPE_SD) ** 2


def audit_original(folder, *, expected_original_checkout=None):
    """Reconstruct frozen R64 original archive; never call R64 simulator."""
    checked, checkout = _audit_sha(folder)
    if expected_original_checkout is not None and checkout != expected_original_checkout:
        raise ValueError("R64 immutable original source checkout does not match pinned SHA")
    root=Path(folder)
    cases=json.loads((root/"cases.json").read_bytes())
    stored=json.loads((root/"summary.json").read_bytes())
    expected={(b,s,l) for b in range(BLOCKS) for s in SUPPORT for l in LEVELS}
    ids=[(r["block"],r["support"],r["level"]) for r in cases]
    if len(ids)!=SOURCE_CASES or len(set(ids))!=SOURCE_CASES or set(ids)!=expected:
        raise ValueError("R64 original full independent primitive source-level grid missing or duplicated")
    fixed={
        "study":STUDY,
        "new_independent_primitive_block_source_seed":SOURCE_SEED,
        "new_conditional_Gaussian_draw_seed":DRAW_SEED,
        "independent_Gaussian_primitive_blocks":BLOCKS,
        "participants_per_primitive_source":24,
        "leverage_supports":list(SUPPORT),
        "structural_slope_multipliers":list(LEVELS),
        "support_and_level_paired_within_independent_block":True,
        "planned_source_cases":SOURCE_CASES,
        "recorded_source_cases":SOURCE_CASES,
        "draws_per_original_source":B,
        "planned_gaussian_conditional_H0_draw_slots":SOURCE_DRAWS,
        "recorded_gaussian_conditional_H0_draw_slots":SOURCE_DRAWS,
        "nested_H0_H1_model_fit_slots":SOURCE_MODELS,
        "optimizer_start_records":SOURCE_STARTS,
        "fitted_null_nuisance_reestimated_for_each_bootstrap_draw":True,
        "conditional_candidate_p_grid_denominator":B+1,
        "exploratory_detection_not_validated_power":True,
        "no_validated_null_type_I_calibration":True,
        "no_fitted_CR2_pointwise_or_simultaneous_90pct_qualification":True,
        "release_authorized":False,
    }
    for k,v in fixed.items():
        if stored.get(k)!=v:
            raise ValueError("R64 frozen original aggregate provenance or denominator changed: "+k)
    for level in LEVELS:
        _same(stored["true_slope_variances"][level],_variance(level),level+"/source true random slope variance",atol=1e-14,rtol=1e-12)
    records={}
    starts=0
    max_kkt=0.
    for row in cases:
        block,support,level=row["block"],row["support"],row["level"]
        label=f"{block}/{support}/{level}"
        m=MULTIPLIER[level]
        if (row["study"]!=STUDY or
            row["structural_slope_multiplier"] != m or
            row["null_size_or_power_qualified"] is not False or
            row["fitted_CR2_90pct_qualified"] is not False or
            row["release_authorized"] is not False or
            row["planned_bootstrap_slots"]!=B):
            raise ValueError("R64 source matched-level or scientific qualification gate changed")
        _same(row["true_slope_variance"],_variance(level),label+"/true slope variance",atol=1e-14,rtol=1e-12)
        if row["source_status"]=="ok":
            full=row["full_slope_component_L2"]
            retained=row["retained_slope_component_L2"]
            if full<=0 or not math.isfinite(full):
                raise ValueError("R64 source had no positive full slope innovation")
            _same(retained,m*full,label+"/matched slope innovation norm",atol=1e-9)
        elif row["source_status"]!="refused":
            raise ValueError("R64 unregistered original source status")
        seen=_nested(row["observed"],label+"/observed")
        starts+=seen["slots"]
        max_kkt=max(max_kkt,seen["kkt"])
        theta=row["fitted_null_theta"]
        if seen["status"]=="accepted":
            if row["source_status"]!="ok" or not isinstance(theta,list) or len(theta)!=4:
                raise ValueError("R64 accepted original H0 lacks covariance components")
            if theta[1]!=0 or not all(math.isfinite(float(theta[i])) and float(theta[i])>0 for i in (0,2,3)):
                raise ValueError("R64 H0 covariance must exclude exact slope variance")
            ratio=row["observed"]["null_fit"]["selected_free_component_variance_ratios"]
            ref=row["observed"].get("observed_reference")
            if ref is None or float(ref)<=0 or len(ratio)!=3:
                raise ValueError("R64 missing H0 observed covariance reference")
            for a,b in zip((theta[0],theta[2],theta[3]),ratio):
                _same(a,float(ref)*float(b),label+"/H0 nuisance covariance")
            if row["candidate_5pct_exceedance"] is not bool(seen["gap"]>BOUNDARY_CUTOFF):
                raise ValueError("R64 original classical candidate LRT mismatch")
        else:
            if theta is not None or row["candidate_5pct_exceedance"] is not None:
                raise ValueError("R64 refused observed model reported classical result")
        draws=row["bootstrap"]
        if not isinstance(draws,list) or [v["draw"] for v in draws]!=list(range(B)):
            raise ValueError("R64 original consecutive 63 draw positions missing")
        accepted=[]
        for d in draws:
            j=d["draw"]
            nested=_nested(d["nested"],label+f"/bootstrap/{j}")
            starts+=nested["slots"]
            max_kkt=max(max_kkt,nested["kkt"])
            if d["status"]!=nested["status"]:
                raise ValueError("R64 inner/outer Gaussian pseudo-fit status mismatch")
            if nested["status"]=="accepted":
                seeded=DRAW_SEED + 100003*block + 739*SUPPORT.index(support) + 1009*LEVELS.index(level) + j
                if d["seed"]!=seeded:
                    raise ValueError("R64 conditional H0 Gaussian draw seed identity mismatch")
                accepted.append(nested["gap"])
            elif nested["status"]=="not_attempted" and d["seed"] is not None:
                raise ValueError("R64 not attempted pseudodraw reported an RNG seed")
        p=row["conditional_bootstrap_p"]
        if seen["status"]=="accepted" and len(accepted)==B:
            calc=(1+sum(v>=seen["gap"] for v in accepted))/(B+1)
            _same(p,calc,label+"/conditional add-one p",atol=1e-12,rtol=0)
            if row["bootstrap_5pct_exceedance"] is not bool(calc<=ALPHA):
                raise ValueError("R64 original candidate detection decision altered")
        elif p is not None or row["bootstrap_5pct_exceedance"] is not None:
            raise ValueError("R64 incomplete 63-draw source incorrectly reported detection")
        records[(block,support,level)]={
            "source_accepted":seen["status"]=="accepted",
            "accepted_draws":len(accepted),
            "p":p,
            "bootstrap":row["bootstrap_5pct_exceedance"],
            "classical":row["candidate_5pct_exceedance"],
            "full_norm":row.get("full_slope_component_L2"),
        }
    if starts!=SOURCE_STARTS:
        raise ValueError("R64 complete original optimizer-start denominator changed")
    # R64 generator's original latent innovations are not archived, so
    # this matched-L2 check verifies recorded numerical intent only.
    for block in range(BLOCKS):
        for support in SUPPORT:
            evidence=[records[(block,support,level)]["full_norm"] for level in LEVELS]
            if all(x is not None for x in evidence):
                for x in evidence[1:]:
                    _same(x,evidence[0],f"{block}/{support}/matched full-slope norm",atol=1e-12)
    strata={}
    for support in SUPPORT:
        for level in LEVELS:
            key=f"{support}/{level}"
            cell=[records[(b,support,level)] for b in range(BLOCKS)]
            original_accept=sum(x["source_accepted"] for x in cell)
            complete=[x for x in cell if x["p"] is not None]
            n=len(complete)
            rejects=sum(x["bootstrap"] is True for x in complete)
            classical=sum(x["classical"] is True for x in cell)
            draws=sum(x["accepted_draws"] for x in cell)
            refused=BLOCKS-n
            expected_cell={
                "independent_source_blocks":BLOCKS,
                "true_slope_variance":_variance(level),
                "original_source_cases":BLOCKS,
                "accepted_original_nested_fits":original_accept,
                "planned_gaussian_bootstrap_draw_slots":BLOCKS*B,
                "recorded_gaussian_bootstrap_draw_slots":BLOCKS*B,
                "accepted_nuisance_refitted_bootstrap_draws":draws,
                "complete_63_draw_sources":n,
                "refused_incomplete_sources":refused,
                "bootstrap_candidate_rejections":rejects,
                "refusal_as_nonrejection_all_source_lower":rejects/BLOCKS,
                "refusal_as_rejection_all_source_upper":(rejects+refused)/BLOCKS,
                "classical_candidate_rejections":classical,
                "null_size_or_power_qualified":False,
            }
            stored_cell=stored["strata"][key]
            for field,value in expected_cell.items():
                if field=="true_slope_variance":
                    _same(stored_cell[field],value,key+"/true variance",atol=1e-14,rtol=1e-12)
                elif stored_cell.get(field)!=value:
                    raise ValueError("R64 original support/level summary mismatch "+key+"/"+field)
            if n:
                _same(stored_cell["bootstrap_candidate_detection_fraction_complete"],rejects/n,key+"/detection fraction")
            elif stored_cell["bootstrap_candidate_detection_fraction_complete"] is not None:
                raise ValueError("R64 invalid detection rate with no complete original cases")
            ci=_wilson(rejects,n)
            classical_ci=_wilson(classical,original_accept)
            for k,expected_ci in (("bootstrap_Wilson95_complete",ci),("classical_Wilson95_accepted",classical_ci)):
                given=stored_cell[k]
                if expected_ci is None:
                    if given is not None:
                        raise ValueError("R64 Wilson interval with zero complete cases")
                else:
                    if len(given)!=2:
                        raise ValueError("R64 malformed Wilson interval")
                    for recorded,computed in zip(given,expected_ci):
                        _same(recorded,computed,key+"/"+k,atol=1e-8,rtol=1e-8)
            strata[key]={**expected_cell,"bootstrap_rate_complete":rejects/n if n else None,
                         "bootstrap_Wilson95_complete":ci,
                         "classical_rate_accepted":classical/original_accept if original_accept else None}
    # Matched within-block detection transitions preserve dependence.
    transitions={}
    for support in SUPPORT:
        matched=[tuple(records[(b,support,l)]["bootstrap"] for l in LEVELS)
                 for b in range(BLOCKS)
                 if all(records[(b,support,l)]["p"] is not None for l in LEVELS)]
        transitions[support]={
            "complete_matched_primitive_blocks":len(matched),
            "candidate_nonmonotone_detection_blocks":sum(
                (int(t[0])>int(t[1]) or int(t[1])>int(t[2])) for t in matched),
            "zero_and_full_reject":sum(t[0] and t[2] for t in matched),
            "zero_only_relative_to_full":sum(t[0] and not t[2] for t in matched),
            "full_only_relative_to_zero":sum(t[2] and not t[0] for t in matched),
        }
    return {
        "R64_independent_original_numerical_archive_reproduced":True,
        "original_sha256_entries_verified":len(checked),
        "original_source_checkout":checkout,
        "independent_Gaussian_primitive_blocks":BLOCKS,
        "paired_source_cases":len(cases),
        "bootstrap_draw_slots":SOURCE_DRAWS,
        "nested_model_fit_positions":SOURCE_MODELS,
        "optimizer_start_positions":starts,
        "largest_selected_projected_KKT":max_kkt,
        "strata":strata,
        "matched_source_detection_transitions":transitions,
        "original_latent_Gaussian_source_responses_not_archived":True,
        "not_validated_size_or_true_5pct_power":True,
        "not_fitted_CR2_90pct_interval_coverage":True,
        "release_authorized":False,
    }


def main():
    cli=argparse.ArgumentParser()
    cli.add_argument("--original",required=True,type=Path)
    cli.add_argument("--out",required=True,type=Path)
    cli.add_argument("--expected-original-checkout",default=None)
    arg=cli.parse_args()
    outcome=audit_original(arg.original,
        expected_original_checkout=arg.expected_original_checkout)
    arg.out.parent.mkdir(parents=True,exist_ok=True)
    arg.out.write_bytes((json.dumps(outcome,sort_keys=True,indent=2)+"\n").encode())
    print(json.dumps(outcome,sort_keys=True))


if __name__=="__main__":
    main()
