from __future__ import annotations

import json
import os
from pathlib import Path
import shutil

RC = "1.1.0rc1"


def replace(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if old not in text:
        if new in text:
            return
        raise SystemExit(f"expected token not found in {path}: {old!r}")
    target.write_text(text.replace(old, new), encoding="utf-8")


# Active qualification ledgers become literal-RC evidence. Historical 1.0 and
# R4 development ledgers are intentionally untouched.
replace("REFERENCE_VALIDATION.json", '"package_version": "1.0.0"', f'"package_version": "{RC}"')
replace("VALIDATION_TOLERANCES.json", '"package_version": "1.0.0"', f'"package_version": "{RC}"')

fresh = Path("performance-envelope.json")
if not fresh.exists():
    raise SystemExit("fresh performance-envelope.json was not generated")
raw = json.loads(fresh.read_text(encoding="utf-8"))
package_version = raw.get("environment", {}).get("packages", {}).get("eyetrajectoriespy")
if package_version != RC:
    raise SystemExit(f"performance evidence is not literal RC: {package_version!r}")
source_commit = raw.get("environment", {}).get("source_commit")
if not source_commit:
    raise SystemExit("performance evidence does not retain source_commit")

# run_performance_qualification.py emits raw observations. Promotion to the
# checked-in envelope schema adds qualification identity/status and nests the
# repeated measurements under `observed`, matching every historical envelope.
results = []
for row in raw.get("results", []):
    results.append(
        {
            "case": row["case"],
            "scale": row["scale"],
            "repeats": row["repeats"],
            "observed": {
                "runtime_seconds": row["runtime_seconds"],
                "peak_memory_mib": row["peak_memory_mib"],
            },
        }
    )

payload = {
    "schema_version": raw.get("schema_version", 1),
    "package_version": RC,
    "benchmark_kind": raw["benchmark_kind"],
    "comparative_benchmark": raw["comparative_benchmark"],
    "profile": raw["profile"],
    "status": "qualified",
    "qualification_commit": source_commit,
    "qualification_run_id": os.environ["GITHUB_RUN_ID"],
    "environment": raw["environment"],
    "results": results,
}
if "interpretation" in raw:
    payload["interpretation"] = raw["interpretation"]

Path("PERFORMANCE_ENVELOPE.json").write_text(
    json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
archive = Path("validation/performance") / f"PERFORMANCE_ENVELOPE-{RC}.json"
archive.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile("PERFORMANCE_ENVELOPE.json", archive)

replace("tests/test_qualification_ledgers.py", 'QUALIFIED_EVIDENCE_VERSION = "1.0.0"', f'QUALIFIED_EVIDENCE_VERSION = "{RC}"')
replace("tests/test_public_api.py", 'assert et.__version__=="1.1.0.dev0"', f'assert et.__version__=="{RC}"')
replace("scripts/validate_docs_contracts.py", 'LATEST_QUALIFIED_EVIDENCE_VERSION = "1.0.0"', f'LATEST_QUALIFIED_EVIDENCE_VERSION = "{RC}"')

hardening = Path("tests/test_release_hardening.py")
text = hardening.read_text(encoding="utf-8")
text = text.replace('CURRENT_DEVELOPMENT_VERSION = "1.1.0.dev0"', f'CURRENT_DEVELOPMENT_VERSION = "{RC}"')
text = text.replace('LATEST_QUALIFIED_EVIDENCE_VERSION = "1.0.0"', f'LATEST_QUALIFIED_EVIDENCE_VERSION = "{RC}"')
old = '''def test_development_line_is_not_production_eligible():
    module = _load_script("verify_release_version.py")
    with pytest.raises(RuntimeError, match="development versions"):
        module.verify_version_contract(
            tag=f"v{CURRENT_DEVELOPMENT_VERSION}",
            production=True,
        )
'''
new = '''def test_release_candidate_contract_is_production_eligible_after_exact_qualification():
    module = _load_script("verify_release_version.py")
    assert (
        module.verify_version_contract(
            tag=f"v{CURRENT_DEVELOPMENT_VERSION}",
            production=True,
        )
        == CURRENT_DEVELOPMENT_VERSION
    )
'''
if old in text:
    text = text.replace(old, new, 1)
elif new not in text:
    raise SystemExit("release-candidate production-eligibility test block not found")
text = text.replace("def test_development_line_inherits_latest_qualified_evidence():", "def test_release_candidate_requires_literal_exact_version_evidence():")
hardening.write_text(text, encoding="utf-8")

ledger = {
    "schema_version": 1,
    "programme": "1.1-r5-release-candidate-qualification",
    "decision": "approve_exact_version_rc_qualification",
    "r4_qualified_main_sha": "1f9b80701ba4d10c97836277e18d8a16abe0038a",
    "r4_merge_main_sha": "827c41b280250a71a7cd2fd4ac96c8a4ccaa54aa",
    "r4_eligible_for_rc_decision": True,
    "package_version": RC,
    "performance_run_id": int(os.environ["GITHUB_RUN_ID"]),
    "performance_qualification_commit": source_commit,
    "historical_r4_ledger": "ONE_DOT_ONE_DEVELOPMENT_READINESS.json",
    "historical_r4_ledger_relabelled": False,
    "frozen_one_dot_zero_evidence_mutated": False,
    "scientific_behavior_changed": False,
    "supported_api_changed": False,
    "publication_interlock": {
        "production_release_ready": False,
        "github_publication_ready": False,
        "pypi_publication_ready": False,
        "publication_arming_performed": False,
    },
    "status": "literal_rc_evidence_committed_pr_matrix_pending",
}
Path("ONE_DOT_ONE_RC_QUALIFICATION.json").write_text(
    json.dumps(ledger, indent=2) + "\n",
    encoding="utf-8",
)
