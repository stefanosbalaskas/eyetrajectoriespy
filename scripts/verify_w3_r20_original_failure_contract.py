"""Verify original R20 NEGATIVE scientific result without rewriting its evaluator.

The source script must still exit nonzero, retain all 256 records and exactly
41 of the originally failed case identifiers. A green verification job means
the historical failure was reproduced, NOT 90% coverage or numerical success.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

EXPECTED_SHA256="a75ffbf14fb632ffa7ce18ad0203e25141c3ff9d83bbb676ecf6ac55dbc0010e"
EXPECTED_FAILED=41
EXPECTED_COMPLETED=215
EXPECTED_TOTAL=256


def verify(out:Path):
    script=Path(__file__).with_name("run_w3_r20_estimated_target_pilot.py")
    result=subprocess.run([sys.executable,str(script),"--out",str(out)],
                          check=False,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                          text=True)
    print("Original evaluator exit code:",result.returncode)
    if result.returncode==0:
        raise RuntimeError("Original pilot unexpectedly passed; historic failure cannot be hidden")
    ledger=json.loads((out/"case-ledger.json").read_text())
    summary=json.loads((out/"summary.json").read_text())
    if (len(ledger)!=EXPECTED_TOTAL or summary["planned_evaluations"]!=EXPECTED_TOTAL
        or summary["completed_evaluations"]!=EXPECTED_COMPLETED
        or summary["failed_evaluations"]!=EXPECTED_FAILED
        or summary["missing_evaluations"]!=0):
        raise RuntimeError("Original R20 256-case failure count changed")
    failed=sorted(
        f'{x["block"]}|{x["n_participants"]}|{x["source_support"]}|'
        f'{x["mean_basis"]}|{x["working_family"]}'
        for x in ledger if x["status"]!="ok"
    )
    signature=hashlib.sha256(("\n".join(failed)+"\n").encode()).hexdigest()
    if len(failed)!=EXPECTED_FAILED or signature!=EXPECTED_SHA256:
        raise RuntimeError("Original R20 41 failure identities changed")
    for x in ledger:
        if x["status"]!="ok" and x["error"]!={
            "type":"ValueError","message":"nonpositive or ill-conditioned working covariance"}:
            raise RuntimeError("Original rejection cause changed")
    for entry in (out/"SHA256SUMS").read_text().splitlines():
        digest,name=entry.split("  ",1)
        if hashlib.sha256((out/name).read_bytes()).hexdigest()!=digest:
            raise RuntimeError(f"Original artifact checksum changed: {name}")
    print("EXPECTED NEGATIVE RESULT REPRODUCED:",
          json.dumps({"original_evaluator_failed":True,
                      "original_model_cases":EXPECTED_TOTAL,
                      "successful":EXPECTED_COMPLETED,
                      "failed":EXPECTED_FAILED,
                      "missing":0,
                      "failed_case_sha256":signature,
                      "pointwise_inference_qualified":False,
                      "release_authorized":False}))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--out",required=True,type=Path)
    verify(p.parse_args().out)
