"""R71-A independent exact Gaussian-law vs original W3 wild archive auditor.

NO R71 simulator, package W3 fitter, wild-bootstrap implementation or source
aggregator is imported. The original 32 block x two design x two leverage source
ledger, 999 wild maxima per source and BOTH known-law 32767-max arrays are
verified from the immutable original SHA256 archive.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

import numpy as np

AUDIT="W3_R71_A_INDEPENDENT_KNOWN_GAUSSIAN_LAW_AND_WILD_BAND_ARCHIVE_AUDIT"
STUDY="W3_R71_NEW_FIXED_TRUTH_KNOWN_GAUSSIAN_LAW_ORACLE_DIAGNOSTIC"
CHECKOUT="1102b57fe9605e46303921989842ee3f7a0e1f84"
SOURCE_SEED=202610197171
ORACLE_SEED=202610197172
WILD_SEED=202610197173
BLOCKS=32
DESIGNS=("curve","participant")
SUPPORT=("ordinary","extreme")
SOURCE_CASES=128
B=999
K=32767
CONF=.90
TOL=2e-10
SE_E=.04
SE_PART=.065
TRIALS=3
TIME=np.linspace(0.,1.,31)


def _equal(a,b,label,absolute=3e-9):
    if a is None or b is None:
        if a is not None or b is not None:
            raise ValueError("R71-A missing numerical reference "+label)
    elif isinstance(a,(float,int)) and not isinstance(a,bool) and isinstance(b,(float,int)) and not isinstance(b,bool):
        if not math.isclose(float(a),float(b),rel_tol=3e-9,abs_tol=absolute):
            raise ValueError("R71-A numerical source reference mismatch "+label)
    elif a!=b:
        raise ValueError("R71-A original source mismatch "+label)


def _higher(array,expected_size):
    if len(array)!=expected_size or any(
        type(x) not in (float,int) or not math.isfinite(x) or x<0 for x in array):
        raise ValueError("R71-A missing or nonfinite raw Gaussian/wild maximum statistics")
    return float(sorted(array)[math.ceil((expected_size-1)*CONF)])


def _wilson(k,n,z=1.95996398454):
    if not n:
        return None
    p=k/n;den=1+z*z/n
    mid=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return [max(0.,min(p,mid-half)),min(1.,max(p,mid+half))]


def _unit_var(design):
    if design=="curve":
        return np.full((31,2),SE_E**2)
    if design=="participant":
        val=SE_PART**2*(1.+.35*TIME)**2+SE_E**2/TRIALS
        return np.broadcast_to(val[:,None],(31,2)).copy()
    raise ValueError("R71-A missing original generating design")


def _rebuild_reference(design):
    """Independent algebraic sampling of the exact recorded Gaussian law."""
    rng=np.random.default_rng(ORACLE_SEED+DESIGNS.index(design))
    if design=="curve":
        sample=rng.standard_normal((K,31,2))
    elif design=="participant":
        subject=rng.standard_normal((K,1,2))
        trial=rng.standard_normal((K,31,2))
        time_loading=1+.35*TIME[None,:,None]
        sample=(SE_PART*time_loading*subject+(SE_E/math.sqrt(TRIALS))*trial)
        sample=sample/np.sqrt(_unit_var(design))[None]
    else:
        raise ValueError("R71-A unexpected design")
    return np.max(np.abs(sample),axis=(1,2))


def audit(original:Path,*,expected_checkout=CHECKOUT):
    file_names=("cases.json","summary.json","known_gaussian_reference.json","source-commit.txt")
    sums=(original/"SHA256SUMS").read_text().splitlines()
    if sums!=[sha256((original/n).read_bytes()).hexdigest()+"  "+n for n in file_names]:
        raise ValueError("R71-A immutable 4-member original SHA256 mismatch")
    checkout=(original/"source-commit.txt").read_text().strip()
    if checkout!=expected_checkout or len(checkout)!=40:
        raise ValueError("R71-A wrong original scientific source checkout")
    rows=json.loads((original/"cases.json").read_bytes())
    summary=json.loads((original/"summary.json").read_bytes())
    refs=json.loads((original/"known_gaussian_reference.json").read_bytes())
    ids=[(x["block"],x["design"],x["support"]) for x in rows]
    required={(b,d,s) for b in range(BLOCKS) for d in DESIGNS for s in SUPPORT}
    if len(ids)!=SOURCE_CASES or len(set(ids))!=SOURCE_CASES or set(ids)!=required:
        raise ValueError("R71-A incomplete or duplicated original primitive generating source grid")
    if set(refs)!=set(DESIGNS):
        raise ValueError("R71-A both original known-law designs required")
    rebuilt={}
    for design in DESIGNS:
        ref=refs[design]
        if (ref["design"]!=design or ref["reference_seed"]!=ORACLE_SEED+DESIGNS.index(design)
            or ref["reference_draws"]!=K):
            raise ValueError("R71-A original Gaussian reference seed and source identity mismatch")
        reconstructed=_rebuild_reference(design)
        actual=np.asarray(ref["raw_standardized_maxima"],float)
        if actual.shape!=(K,) or not np.isfinite(actual).all():
            raise ValueError("R71-A original Gaussian maximum draws absent/nonfinite")
        if not np.allclose(actual,reconstructed,atol=2e-11,rtol=0):
            raise ValueError("R71-A Gaussian source-law reference simulation does not reproduce")
        _equal(ref["critical"],_higher(actual.tolist(),K),design+"/Gaussian critical",absolute=5e-12)
        if not np.allclose(np.asarray(ref["true_unit_variance_grid"]),_unit_var(design),
                           rtol=0,atol=1e-15):
            raise ValueError("R71-A original known Gaussian covariance diagonal incorrect")
        rebuilt[design]=float(ref["critical"])

    source_count={}
    paired={}
    checked_wild=0
    checked_cells=0
    failures=[]
    for row in rows:
        block,design,support=row["block"],row["design"],row["support"]
        n=72 if design=="curve" else 36
        expected_wild=WILD_SEED+100003*block+10007*DESIGNS.index(design)+739*SUPPORT.index(support)
        if (row["study"]!=STUDY
            or row["source_seed"]!=SOURCE_SEED+10007*block+DESIGNS.index(design)
            or row["wild_seed"]!=expected_wild or row["independent_units"]!=n
            or row["observed_curves"]!=(n if design=="curve" else n*TRIALS)
            or row["no_nominal_90pct_wild_band_qualification"] is not True
            or row["known_covariance_not_observed_data_estimator"] is not True
            or row["release_authorized"] is not False):
            raise ValueError("R71-A original generating-source provenance/qualification invalid")
        if not row["completed"]:
            if row["exception"] is None:
                raise ValueError("R71-A original numerical refusal missing exception")
            failures.append({"block":block,"design":design,"support":support,"error":row["exception"]})
            continue
        if row["exception"] is not None:
            raise ValueError("R71-A completed original source reports hidden exception")
        for field in ("OLS_oracle_max_error","HC1_oracle_max_error","package_wild_max_reference_error"):
            if row[field] is None or row[field]<0 or row[field]>TOL:
                raise ValueError("R71-A original W3 numerical contract not satisfied")
        beta_error=np.asarray(row["observed_slope_beta_error_grid"],float)
        original_se=np.asarray(row["observed_HC1_slope_SE_grid"],float)
        known_se=np.asarray(row["known_law_true_slope_SE_grid"],float)
        if any(x.shape!=(31,2) or not np.isfinite(x).all() for x in (beta_error,original_se,known_se)):
            raise ValueError("R71-A full original slope truth/SE array missing")
        if np.any(original_se<=0) or np.any(known_se<=0):
            raise ValueError("R71-A invalid positive slope SE arrays")
        law_unit_sd=np.sqrt(_unit_var(design))
        derived_scalar=known_se/law_unit_sd
        if not np.allclose(derived_scalar,derived_scalar[0,0],atol=2e-12,rtol=2e-11):
            raise ValueError("R71-A true source SE is inconsistent with exact Gaussian covariance shape")
        ratios=original_se/known_se
        for field,value in {
            "min_HC1_over_known_SE":float(np.min(ratios)),
            "mean_HC1_over_known_SE":float(np.mean(ratios)),
            "max_HC1_over_known_SE":float(np.max(ratios)),
            "known_law_slope_max_pivot":float(np.max(np.abs(beta_error/known_se))),
            "original_wild_HC1_slope_max_pivot":float(np.max(np.abs(beta_error/original_se))),
            "known_law_critical":rebuilt[design],
        }.items():
            _equal(row[field],value,f"{block}/{design}/{support}/{field}")
        maxes=row["wild_999_raw_slope_maxima"]
        critical=_higher(maxes,B)
        _equal(row["original_wild_critical"],critical,"wild 999 higher quantile")
        _equal(row["wild_critical_over_known_law_critical"],critical/rebuilt[design],"wild to known critical ratio")
        known_in=float(np.max(np.abs(beta_error/known_se)))<=rebuilt[design]
        wild_in=float(np.max(np.abs(beta_error/original_se)))<=critical
        if (row["known_law_slope_truth_included"] is not known_in
            or row["original_wild_HC1_slope_truth_included"] is not wild_in):
            raise ValueError("R71-A original truth inclusion not reproduced from archived pivots")
        if row["observed_max_hat"]<=0 or row["observed_max_hat"]>=1:
            raise ValueError("R71-A leverage diagonal incompatible with original independent-unit OLS")
        checked_wild+=B
        checked_cells+=2

    for design in DESIGNS:
        source_count[design]={}
        for support in SUPPORT:
            completed=[x for x in rows if x["design"]==design and x["support"]==support and x["completed"]]
            kknow=sum(x["known_law_slope_truth_included"] for x in completed)
            kwild=sum(x["original_wild_HC1_slope_truth_included"] for x in completed)
            attr={
                "attempted_primitive_blocks":BLOCKS,"complete":len(completed),
                "failed":BLOCKS-len(completed),
                "known_law_true_inclusions":kknow,
                "original_wild_HC1_inclusions":kwild,
                "known_law_Wilson95_complete":_wilson(kknow,len(completed)),
                "wild_HC1_Wilson95_complete":_wilson(kwild,len(completed)),
                "known_law_full_denominator_lower":kknow/BLOCKS,
                "known_law_full_denominator_upper":(kknow+BLOCKS-len(completed))/BLOCKS,
                "wild_HC1_full_denominator_lower":kwild/BLOCKS,
                "wild_HC1_full_denominator_upper":(kwild+BLOCKS-len(completed))/BLOCKS,
                "mean_min_HC1_over_known_SE":sum(x["min_HC1_over_known_SE"] for x in completed)/len(completed) if completed else None,
                "mean_average_HC1_over_known_SE":sum(x["mean_HC1_over_known_SE"] for x in completed)/len(completed) if completed else None,
                "mean_wild_critical_over_known_law_critical":sum(x["wild_critical_over_known_law_critical"] for x in completed)/len(completed) if completed else None,
            }
            prev=summary["per_design_and_support"][design][support]
            for key,value in attr.items():
                if isinstance(value,list):
                    if len(prev[key])!=len(value):
                        raise ValueError("R71-A independent Wilson interval format invalid")
                    for left,right in zip(prev[key],value):
                        _equal(left,right,design+"/"+support+"/"+key)
                else:
                    _equal(prev[key],value,design+"/"+support+"/"+key)
            source_count[design][support]={
                "complete":len(completed),"attempted":BLOCKS,
                "known_included":kknow,"wild_included":kwild,
                "mean_HC1_true_SE_ratio":attr["mean_average_HC1_over_known_SE"],
                "mean_wild_known_critical_ratio":attr["mean_wild_critical_over_known_law_critical"],
            }
            delta=[
                int(x["known_law_slope_truth_included"])-int(x["original_wild_HC1_slope_truth_included"])
                for x in completed]
            m=BLOCKS-len(completed)
            values={
                "complete_matched_primitive_blocks":len(completed),
                "refused_primitive_blocks":m,
                "known_only_truth_included":sum(v==1 for v in delta),
                "wild_only_truth_included":sum(v==-1 for v in delta),
                "both_agree":sum(v==0 for v in delta),
                "mean_difference_complete":sum(delta)/len(completed) if completed else None,
                "full_denominator_lower":(sum(delta)-m)/BLOCKS,
                "full_denominator_upper":(sum(delta)+m)/BLOCKS,
                "not_test_of_method_superiority":True,
            }
            key=f"{design}/{support}/known_minus_original_wild"
            for field,value in values.items():
                _equal(summary["paired_truth_inclusion_diagnostics"][key][field],
                       value,key+"/"+field)
            paired[key]=values
    for key,value in {
        "study":STUDY,"source_seed":SOURCE_SEED,"oracle_seed":ORACLE_SEED,
        "wild_seed":WILD_SEED,"new_independent_primitive_generating_blocks":BLOCKS,
        "source_cases":SOURCE_CASES,"original_Rademacher_wild_multiplier_draw_positions":B*SOURCE_CASES,
        "original_known_gaussian_reference_draws":K*len(DESIGNS),
        "oracle_reference_draws_per_design":K,
        "exact_unit_gaussian_variances":True,"original_W3_OLS_HC1_oracle_tolerance":TOL,
        "no_calibrated_90pct_estimated_simultaneous_band_claim":True,
        "known_law_is_not_estimable_real_data_reference":True,
        "no_response_dependent_gaze_missingness":True,
        "release_authorized":False,
    }.items():
        _equal(summary.get(key),value,key)
    return {
        "study":AUDIT,"original_checkout":checkout,
        "original_SHA256_members_verified":4,
        "new_primitive_independent_Gaussian_blocks":BLOCKS,
        "original_source_cases":SOURCE_CASES,
        "original_source_refusals":failures,
        "original_archived_gaussian_max_draws_independently_resimulated":2*K,
        "original_wild_maxima_independently_requantiled":checked_wild,
        "original_source_true_vs_HC1_slopes_reclassified":checked_cells,
        "independent_Gaussian_critical_by_design":rebuilt,
        "source_truth_inclusion":source_count,
        "paired_known_law_minus_wild_HC1":paired,
        "source_design_X_not_archived_cannot_independently_check_OLS_XtX_scalar":True,
        "source_gaussian_innovations_not_archived":True,
        "oracle_known_covariance_not_real_data_inference_method":True,
        "original_W3_90pct_simultaneous_coverage_unqualified":True,
        "release_authorized":False,
    }


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",required=True,type=Path)
    p.add_argument("--expected-checkout",default=CHECKOUT)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    result=audit(args.original,expected_checkout=args.expected_checkout)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({
        "study":AUDIT,"original_checkout":result["original_checkout"],
        "gaussian_draws":result["original_archived_gaussian_max_draws_independently_resimulated"],
        "wild_draw_maxima":result["original_wild_maxima_independently_requantiled"],
        "source_refusals":len(result["original_source_refusals"]),
        "known_law_criticals":result["independent_Gaussian_critical_by_design"],
        "source_truth_inclusions":result["source_truth_inclusion"],
        "paired":result["paired_known_law_minus_wild_HC1"],
        "release_authorized":False,
    },sort_keys=True))
if __name__=="__main__":
    main()
