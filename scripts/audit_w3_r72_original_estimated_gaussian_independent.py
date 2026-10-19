"""R72-A: independent reconstruction of ORIGINAL estimated-Gaussian band evidence.

READ ONLY. Imports neither the R72 source experiment nor its OLS/HC2
covariance/bootstrapping implementation, nor the eyetrajectoriespy package.
Rebuilds Gaussian HC2 and original W3 Rademacher maxima from archived
artificial X/Y, cross-checks exact source IDs, SHA256, source mean matching,
true-law SE, 90% maxima, Wilson bounds and paired inclusion outcomes.
Known Gaussian criticals are frozen R71 independently audited benchmarks.
This checks numerical fidelity, NOT 90% calibrated inference or real gaze
missingness, and must not authorize an API or release.
"""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
import math
from pathlib import Path

import numpy as np

STUDY="W3_R72_NEW_DATA_ESTIMATED_HC2_GAUSSIAN_SIMULTANEOUS_SLOPE_BAND"
ORIGINAL_CHECKOUT="02aeb7311d68830849a17047d458b69a52358f8d"
SOURCE_SEED=202610197272
GAUSSIAN_SEED=202610197273
WILD_SEED=202610197274
BLOCKS=32
B=999
DESIGNS=("curve","participant")
SUPPORT=("ordinary","extreme")
METHODS=("original_wild_HC1","estimated_HC2_Gaussian","known_Gaussian_law")
TRUE_LAW_CRITICAL={"curve":3.1316628143877114,
                   "participant":2.484611913363955}
Z=1.959963984540054
TOL=2e-8

def _near(a,b,description,atol=TOL,rtol=TOL):
    if not np.allclose(np.asarray(a,float),np.asarray(b,float),
                       atol=atol,rtol=rtol,equal_nan=False):
        raise ValueError("R72 independent source reconstruction differs: "+description)

def _wilson(k,n):
    if not 0<=k<=n or type(n) is not int or type(k) is not int:
        raise ValueError("R72 independent invalid source Monte Carlo count")
    if n==0:return None
    p=k/n
    d=1+Z**2/n
    m=(p+Z*Z/(2*n))/d
    w=Z*math.sqrt(p*(1-p)/n+Z*Z/(4*n*n))/d
    return [max(0.,m-w),min(1.,m+w)]

def verify_manifest(folder):
    folder=Path(folder)
    names={"cases.json","summary.json","source-commit.txt"}
    lines=(folder/"SHA256SUMS").read_text().splitlines()
    if len(lines)!=3:raise ValueError("R72-A source SHA256 manifest length")
    digests={}
    for line in lines:
        digest,sep,name=line.partition("  ")
        if (not sep or name not in names or name in digests
            or len(digest)!=64 or any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError("R72-A source SHA256 manifest invalid or duplicated")
        if sha256((folder/name).read_bytes()).hexdigest()!=digest:
            raise ValueError("R72-A original archive SHA256 digest changed")
        digests[name]=digest
    if set(digests)!=names:raise ValueError("R72-A original archive SHA256 incomplete")
    checkout=(folder/"source-commit.txt").read_text().strip()
    if checkout!=ORIGINAL_CHECKOUT:
        raise ValueError("R72-A original scientific source checkout not pinned")
    return digests

def _source_seed(block,design):
    return SOURCE_SEED+10007*block+DESIGNS.index(design)

def _wild_seed(block,design,support):
    return WILD_SEED+100003*block+10007*DESIGNS.index(design)+739*SUPPORT.index(support)

def _gauss_seed(block,design,support):
    return GAUSSIAN_SEED+100003*block+10007*DESIGNS.index(design)+739*SUPPORT.index(support)

def _known_diagonal(design):
    t=np.linspace(0.,1.,31)
    if design=="curve":
        return np.full(62,.04**2)
    if design=="participant":
        return np.repeat(.065**2*(1+.35*t)**2+.04**2/3,2)
    raise ValueError("R72-A unsupported Gaussian source law")

def reconstruct_case(case):
    block,design,support=case["block"],case["design"],case["support"]
    label=f"{block}/{design}/{support}"
    if (case["study"]!=STUDY or case["source_seed"]!=_source_seed(block,design)
        or case["wild_seed"]!=_wild_seed(block,design,support)
        or case["estimated_gaussian_seed"]!=_gauss_seed(block,design,support)
        or case["release_authorized"] is not False
        or case["calibrated_90pct_simultaneous_band"] is not False
        or case["source_law_not_a_real_data_covariance_estimator"] is not True):
        raise ValueError("R72-A frozen original source, seed, or release contract changed "+label)
    if not case["completed"]:
        if not case["refused"] or case["exception"] is None:
            raise ValueError("R72-A missing numerical refusal record")
        if any(case["coverage"][x] is not None for x in METHODS):
            raise ValueError("R72-A refused source falsely counted as truth inclusion")
        return {"complete":False,"coverage":None,"label":label}
    if case["refused"] or case["exception"] is not None:
        raise ValueError("R72-A accepted source falsely recorded as refusal")
    n=72 if design=="curve" else 36
    X=np.asarray(case["original_artificial_X"],float)
    Y=np.asarray(case["original_artificial_Y_unit_means"],float)
    truth=np.asarray(case["original_function_truth_slope"],float)
    if (X.shape!=(n,2) or Y.shape!=(n,31,2) or truth.shape!=(31,2)
        or np.any(~np.isfinite(X)) or np.any(~np.isfinite(Y))
        or np.any(~np.isfinite(truth)) or np.max(np.abs(X[:,0]-1))>1e-13):
        raise ValueError("R72-A missing/invalid complete original artificial design/response")
    if (support=="extreme" and (X[0,1]!=-4 or X[-1,1]!=4)):
        raise ValueError("R72-A original extreme source predictor overridden")
    flat=Y.reshape(n,-1)
    beta=np.linalg.lstsq(X,flat,rcond=None)[0]
    gram=np.linalg.inv(X.T@X)
    proj=gram@X.T
    residual=flat-X@beta
    hat=np.einsum("np,pn->n",X,proj,optimize=True)
    if np.any(hat<=0) or np.any(hat>=1-1e-9):
        raise ValueError("R72-A degenerate original independent unit leverage")
    slope_error=beta[1]-truth.reshape(-1)
    hc1=np.sqrt((n/(n-2))*np.sum(proj[1,:,None]**2*residual**2,axis=0))
    factor=residual/np.sqrt(1-hat)[:,None]/np.sqrt(n)
    Cdiag=np.sum(factor**2,axis=0)
    if np.any(Cdiag<=1e-14) or np.any(~np.isfinite(Cdiag)):
        raise ValueError("R72-A invalid original observed HC2 covariance")
    hc2=np.sqrt(gram[1,1]*Cdiag)
    true=np.sqrt(gram[1,1]*_known_diagonal(design))
    if np.any(hc1<=0) or np.any(hc2<=0):
        raise ValueError("R72-A nonpositive observed source slope uncertainty")

    # Completely separate implementations from R72 and original package:
    # independently generate *whole-unit* original Rademacher multipliers.
    wild_weights=np.random.default_rng(_wild_seed(block,design,support)).choice(
        np.array([-1.,1.]),size=(B,n))
    wild_delta=(wild_weights*proj[1][None,:])@residual
    wildmax=np.max(np.abs(wild_delta/hc1),axis=1)
    # Reconstruct full-grid Gaussian max draws from rectangular HC2 factor.
    normal=np.random.default_rng(_gauss_seed(block,design,support)).standard_normal((B,n))
    estimated_delta=normal@factor
    gaussmax=np.max(np.abs(estimated_delta/np.sqrt(Cdiag)),axis=1)
    if len(case["original_wild_999_maxima"])!=B or len(case["estimated_HC2_Gaussian_999_maxima"])!=B:
        raise ValueError("R72-A missing raw 999 original maxima from source")
    _near(wildmax,case["original_wild_999_maxima"],label+"/999 original wild maxima")
    _near(gaussmax,case["estimated_HC2_Gaussian_999_maxima"],label+"/999 HC2 Gaussian maxima")
    crit={
        "original_wild_HC1":float(np.quantile(wildmax,.9,method="higher")),
        "estimated_HC2_Gaussian":float(np.quantile(gaussmax,.9,method="higher")),
        "known_Gaussian_law":TRUE_LAW_CRITICAL[design],
    }
    pivot={
        "original_wild_HC1":float(np.max(np.abs(slope_error/hc1))),
        "estimated_HC2_Gaussian":float(np.max(np.abs(slope_error/hc2))),
        "known_Gaussian_law":float(np.max(np.abs(slope_error/true))),
    }
    cover={name:bool(pivot[name]<=crit[name]) for name in METHODS}
    for name in METHODS:
        _near(case["criticals"][name],crit[name],label+"/"+name+"/critical")
        _near(case["pivots"][name],pivot[name],label+"/"+name+"/pivot")
        if case["coverage"][name] is not cover[name]:
            raise ValueError("R72-A original source truth inclusion incorrect "+label+"/"+name)
    _near(case["mean_estimated_HC2_over_true_SE"],np.mean(hc2/true),
          label+"/HC2 source ratio")
    _near(case["mean_HC1_over_true_SE"],np.mean(hc1/true),label+"/HC1 source ratio")
    _near(case["maximum_unit_hat"],max(hat),label+"/maximum hat")
    _near(case["HC2_covariance_trace"],sum(Cdiag),label+"/HC2 covariance trace")
    if case["HC2_covariance_effective_rank_upper"]!=min(n-2,62):
        raise ValueError("R72-A original HC2 rank ledger changed")
    if case["package_HC1_OLS_max_error"]>2e-10 or case["package_wild_max_reference_error"]>2e-10:
        raise ValueError("R72-A original numerical package oracle check out of tolerance")
    return {"complete":True,"coverage":cover,"label":label,
            "mean_hc1_true_ratio":float(np.mean(hc1/true)),
            "mean_hc2_true_ratio":float(np.mean(hc2/true)),
            "estimated_gaussian_critical":crit["estimated_HC2_Gaussian"],
            "original_X":X,"original_Y":Y,"slope_truth":truth}

def audit_original(folder):
    digests=verify_manifest(folder)
    root=Path(folder)
    rows=json.loads((root/"cases.json").read_bytes())
    report=json.loads((root/"summary.json").read_bytes())
    ids=[(r["block"],r["design"],r["support"]) for r in rows]
    expected={(b,d,s) for b in range(BLOCKS) for d in DESIGNS for s in SUPPORT}
    if len(ids)!=128 or len(set(ids))!=128 or set(ids)!=expected:
        raise ValueError("R72-A 32-independent-block matched source IDs missing/duplicated")
    frozen={
        "study":STUDY,"source_seed":SOURCE_SEED,
        "estimated_Gaussian_seed":GAUSSIAN_SEED,"original_wild_seed":WILD_SEED,
        "new_independent_primitive_blocks":BLOCKS,
        "paired_design_and_support_cases":128,
        "Gaussian_reference_draws_per_original_case":B,
        "original_wild_draws_per_original_case":B,
        "method_labels":list(METHODS),
        "known_law_reference_from_frozen_R71":True,
        "estimated_covariance_is_HC2_unit_residual":True,
        "no_independent_original_ledger_audit_yet":True,
        "no_90pct_simultaneous_qualification":True,
        "no_missingness_or_MNAR_examined":True,
        "release_authorized":False,
    }
    for k,v in frozen.items():
        if report.get(k)!=v:
            raise ValueError("R72-A original source aggregate contract differs: "+k)
    rebuilt={(r["block"],r["design"],r["support"]):reconstruct_case(r) for r in rows}
    results={}
    matched={}
    for d in DESIGNS:
        results[d]={}
        for s in SUPPORT:
            collection=[rebuilt[(b,d,s)] for b in range(BLOCKS)]
            complete=[x for x in collection if x["complete"]]
            n=len(complete);refused=BLOCKS-n
            saved=report["per_cell"][d][s]
            if (saved["completed"]!=n or saved["refused"]!=refused
                or saved["independent_primitive_blocks"]!=BLOCKS):
                raise ValueError("R72-A source denominator mismatch")
            estimates={}
            for method in METHODS:
                observed=sum(x["coverage"][method] for x in complete)
                summary=saved["methods"][method]
                if summary["truth_inclusions_complete"]!=observed:
                    raise ValueError("R72-A source truth inclusion count not reproducible")
                if n:
                    _near(summary["Wilson95_complete"],_wilson(observed,n),
                          d+s+method+"/Wilson",atol=1e-10,rtol=1e-10)
                elif summary["Wilson95_complete"] is not None:
                    raise ValueError("R72-A source Wilson interval claimed with n=0")
                _near(summary["full_denominator_lower"],observed/BLOCKS,d+s+method+"/lower")
                _near(summary["full_denominator_upper"],(observed+refused)/BLOCKS,d+s+method+"/upper")
                estimates[method]=observed
            results[d][s]={"completed":n,"refused":refused,"inclusions":estimates,
                           "mean_HC1_over_true_SE":float(np.mean([
                               x["mean_hc1_true_ratio"] for x in complete])) if n else None,
                           "mean_HC2_over_true_SE":float(np.mean([
                               x["mean_hc2_true_ratio"] for x in complete])) if n else None}
            if n:
                _near(results[d][s]["mean_HC1_over_true_SE"],saved["mean_HC1_over_known_SE"],d+s+"/HC1 ratio")
                _near(results[d][s]["mean_HC2_over_true_SE"],saved["mean_HC2_over_known_SE"],d+s+"/HC2 ratio")
                _near(np.mean([x["estimated_gaussian_critical"] for x in complete]),
                      saved["mean_estimated_Gaussian_critical"],d+s+"/HC2 critical")

            for first,second in (
                ("estimated_HC2_Gaussian","original_wild_HC1"),
                ("known_Gaussian_law","estimated_HC2_Gaussian"),
            ):
                vals=[int(x["coverage"][first])-int(x["coverage"][second]) for x in complete]
                key=f"{d}/{s}/{first}_minus_{second}"
                original=report["paired_source_coverage_differences"][key]
                expected={
                    "completed_primitive_blocks":n,
                    "refused_primitive_blocks":refused,
                    "first_only_truth_included":sum(v==1 for v in vals),
                    "second_only_truth_included":sum(v==-1 for v in vals),
                    "agreement":sum(v==0 for v in vals),
                }
                for field,value in expected.items():
                    if original[field]!=value:
                        raise ValueError("R72-A original matched source discordance mismatch "+key+"/"+field)
                if n:
                    _near(original["mean_difference_complete"],sum(vals)/n,key+"/mean")
                _near(original["full_denominator_lower"],(sum(vals)-refused)/BLOCKS,key+"/lower")
                _near(original["full_denominator_upper"],(sum(vals)+refused)/BLOCKS,key+"/upper")
                matched[key]=expected
        for b in range(BLOCKS):
            ord_=rebuilt[(b,d,SUPPORT[0])]
            ext_=rebuilt[(b,d,SUPPORT[1])]
            if ord_["complete"] and ext_["complete"]:
                _near(ord_["original_Y"]-ext_["original_Y"],
                      (ord_["original_X"][:,1]-ext_["original_X"][:,1])[:,None,None]
                      *ord_["slope_truth"][None],f"{b}/{d}/paired Gaussian noise",
                      atol=5e-12,rtol=0)
    return {"original_R72_independent_numerical_evidence_reconstructed":True,
            "original_checkout":ORIGINAL_CHECKOUT,
            "source_SHA256_members_checked":len(digests),
            "independent_primitive_blocks":BLOCKS,
            "paired_original_cases":len(rows),
            "source_cases_completed":sum(x["complete"] for x in rebuilt.values()),
            "original_W3_wild_maxima_reconstructed":
                B*sum(x["complete"] for x in rebuilt.values()),
            "estimated_HC2_Gaussian_maxima_reconstructed":
                B*sum(x["complete"] for x in rebuilt.values()),
            "all_original_X_Y_unit_means_archived":True,
            "source_law_Gaussian_innovation_distribution_not_established_by_archive":True,
            "coverage":results,"matched_ledger":matched,
            "not_calibrated_90pct_real_data_simultaneous_inference":True,
            "release_authorized":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    out=audit_original(a.original)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(out,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"verified":out["original_R72_independent_numerical_evidence_reconstructed"],
                      "source_cases":out["paired_original_cases"],
                      "coverage":out["coverage"]},sort_keys=True))

if __name__=="__main__":
    main()
