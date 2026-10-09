"""Fail-closed aggregation of independent scientific-calibration SHARDS.

This does not run simulations and NEVER certifies statistical operating
characteristics. It verifies content hashes, consistent master seed and
programme, unique shard/replicate IDs, and absence of observed seed collisions.
All failed estimator refits remain in outputs and summaries.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest


CASES = {
    "B6": {"cases.csv": ("scenario",)},
    "B7": {"cases.csv": ("rank","asynchronous")},
    "F1_F5": {
        "f1-cases.csv": ("design","scenario"),
        "f5-cases.csv": ("scenario","block_length","change"),
    },
}


def _verify_hashes(directory: Path) -> None:
    checksum=directory/"sha256.txt"
    if not checksum.is_file():
        raise ValueError(f"missing sha256.txt: {directory}")
    hashed=set()
    for line in checksum.read_text().splitlines():
        pieces=line.split("  ",1)
        if len(pieces)!=2 or len(pieces[0])!=64:
            raise ValueError(f"invalid checksum record: {directory}")
        digest,filename=pieces
        if filename in hashed or Path(filename).name != filename:
            raise ValueError(f"duplicate/unsafe checksum record: {directory}")
        hashed.add(filename)
        p=directory/filename
        if not p.is_file() or sha256(p.read_bytes()).hexdigest()!=digest:
            raise ValueError(f"checksum mismatch or missing file: {p}")
    if not hashed:
        raise ValueError("empty checksum manifest")


def _scenario_key(row: pd.Series, group: tuple[str,...]) -> str:
    return json.dumps([
        None if pd.isna(row[col]) else row[col].item()
        if isinstance(row[col],np.generic) else row[col]
        for col in group
    ],separators=(",",":"),default=str)


def aggregate(inputs: list[Path]) -> tuple[pd.DataFrame,dict]:
    if not inputs:
        raise ValueError("at least one independent calibration shard required")
    manifests=[]
    frames=[]
    for directory in inputs:
        directory=Path(directory)
        _verify_hashes(directory)
        manifest=json.loads((directory/"manifest.json").read_text())
        programme=manifest["programme"]
        if programme not in CASES:
            raise ValueError(f"unknown calibration programme: {programme}")
        if sorted(manifest["case_files"])!=sorted(CASES[programme]):
            raise ValueError("unexpected case file contract")
        if manifest["scientific_inference_qualified"] or manifest["release_authorized"]:
            raise ValueError("cannot aggregate promoted research evidence")
        for case_file, group_columns in CASES[programme].items():
            path=directory/case_file
            # Pandas' default NA vocabulary includes the literal string
            # "null": that is the science runner's actual null-hypothesis
            # scenario label for both F1 and F5. Preserve it as a category;
            # represent genuinely empty CSV cells as missing values.
            df=pd.read_csv(path,keep_default_na=False,na_values=[""])
            # Historical F1 shards from wave #250 wrote `iteration` before
            # the unified `replicate` key was added. Preserve archived
            # original case CSV/checksums; normalize only in memory.
            if case_file=="f1-cases.csv":
                if "replicate" not in df.columns and "iteration" in df.columns:
                    df["replicate"]=df["iteration"]
                if "iteration" in df.columns and "replicate" in df.columns:
                    if not df["iteration"].equals(df["replicate"]):
                        raise ValueError("F1 iteration/replicate identifiers disagree")
            required=set(group_columns)|{"seed","replicate","shard_id","status"}
            if not required.issubset(df.columns):
                raise ValueError(f"missing required case columns: {path}")
            if len(df)<1 or df[["seed","replicate","shard_id"]].isna().any().any():
                raise ValueError(f"empty/invalid case records: {path}")
            if not df.shard_id.eq(manifest["shard_id"]).all():
                raise ValueError(f"mismatched shard id in case file: {path}")
            if not df.status.isin(["ok","failed"]).all():
                raise ValueError("unknown fit status")
            sub=df.copy()
            sub["calibration_method"]=case_file
            sub["scenario_key"]=sub.apply(
                lambda row:_scenario_key(row,group_columns),axis=1)
            frames.append(sub)
        manifests.append(manifest)
    first=manifests[0]
    if any(m["programme"]!=first["programme"] or
           m["master_seed"]!=first["master_seed"] for m in manifests):
        raise ValueError("mismatched programme or master seed")
    shards=[m["shard_id"] for m in manifests]
    if len(set(shards))!=len(shards):
        raise ValueError("duplicate shard id; refusing pseudoreplication")
    # Case files can have different column sets (F1 versus F5).
    all_cases=pd.concat(frames,ignore_index=True,sort=False)
    if all_cases["seed"].duplicated().any():
        raise ValueError("observed random-seed collision or duplicated simulation")
    key=["calibration_method","scenario_key","shard_id","replicate"]
    if all_cases.duplicated(subset=key).any():
        raise ValueError("duplicate scenario/replicate key")
    evidence=[]
    for (method,scenario),group in all_cases.groupby(
        ["calibration_method","scenario_key"],dropna=False):
        ok=group.loc[group.status=="ok"]
        result={
            "case_file":method,"scenario_key":scenario,
            "n_attempted":len(group),"n_successful":len(ok),
            "n_failed":int((group.status=="failed").sum()),
            "success_only_rates_are_conditional_on_fitting":True,
        }
        for key in ("p_value","population_mean_mid_90_included",
                    "population_covariance_mid_90_included",
                    "x_mean_mid_90_covered","y_mean_mid_90_covered",
                    "xy_crosscov_mid_90_covered",
                    "new_participant_all_points_within_marginal_bands"):
            if key not in ok.columns or ok[key].isna().all():
                continue
            values=ok[key].dropna()
            if key=="p_value":
                result["rejection_rates_by_alpha"]={
                    str(alpha):_binomial_rate(int((values<=alpha).sum()),len(values))
                    for alpha in (.01,.05,.10)
                }
            else:
                # CSV roundtrips may represent booleans as str or bool.
                truth=values.astype(str).str.lower()
                if not truth.isin(["true","false"]).all():
                    raise ValueError("invalid boolean coverage outcomes")
                result[key]=_binomial_rate(int((truth=="true").sum()),len(truth))
        for score in ("new_participant_average_pointwise_inclusion",):
            if score in ok.columns and not ok[score].isna().all():
                vals=ok[score].dropna().astype(float)
                if ((vals<0)|(vals>1)).any():
                    raise ValueError("invalid within-participant coverage fraction")
                result[score]={
                    "mean":float(vals.mean()),
                    "independent_participant_replicates":len(vals),
                    "mc_standard_error_across_replicates":float(vals.std(ddof=1)/np.sqrt(len(vals)))
                    if len(vals)>1 else None,
                    "within_participant_points_not_independent":True,
                }
        evidence.append(result)
    payload={
        "schema_version":1,
        "programme":first["programme"],
        "master_seed":first["master_seed"],
        "shard_ids":sorted(shards),
        "n_shards":len(shards),
        "total_attempts":len(all_cases),
        "total_fit_failures":int((all_cases.status=="failed").sum()),
        "data_integrity_hashes_verified":True,
        "duplicate_replicate_keys_rejected":True,
        "observed_duplicate_seeds_rejected":True,
        "rates_conditional_on_successful_fit":True,
        "multiple_testing_inference_adjusted":False,
        "scientific_inference_qualified":False,
        "publication_authorized":False,
        "scenario_summaries":evidence,
    }
    return all_cases,payload


def _binomial_rate(k: int,n: int) -> dict:
    if n==0:
        return {"n":0,"count":0,"fraction":None,"mc_exact_95_interval":None}
    ci=binomtest(k,n).proportion_ci(.95,method="exact")
    return {"n":n,"count":k,"fraction":k/n,
            "mc_exact_95_interval":[float(ci.low),float(ci.high)]}


def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--inputs",nargs="+",required=True,type=Path)
    ap.add_argument("--out",required=True,type=Path)
    args=ap.parse_args()
    combined,evidence=aggregate(args.inputs)
    args.out.mkdir(parents=True,exist_ok=True)
    csv=args.out/"cases-combined.csv"
    ledger=args.out/"evidence-combined.json"
    combined.to_csv(csv,index=False)
    ledger.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n")
    (args.out/"sha256.txt").write_text(
        sha256(csv.read_bytes()).hexdigest()+"  cases-combined.csv\n"+
        sha256(ledger.read_bytes()).hexdigest()+"  evidence-combined.json\n")
    print(json.dumps({
        "programme":evidence["programme"],
        "n_shards":evidence["n_shards"],
        "attempted":evidence["total_attempts"],
        "failed":evidence["total_fit_failures"],
        "scientific_inference_qualified":False},sort_keys=True))


if __name__=="__main__":
    main()
