"""E4: provenance-linked Markdown or HTML from actual fitted workflow results.

No p-value, significance claim, confidence interval, or effect region is
fabricated. Reports expose all analyst-declared choices and retained warnings.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import shutil
from typing import Any, Mapping

import pandas as pd

from ._core import (
    _jsonable, _validate_workflow_result, workflow_config_to_dict,
    workflow_decisions_frame, workflow_reporting_text, workflow_steps_frame,
    workflow_summary_frame,
)


@dataclass(frozen=True)
class WorkflowReportArtifact:
    report_path: Path
    provenance_path: Path
    manifest_path: Path
    files_sha256: Mapping[str, str]
    format: str


def _file_name(value: str) -> str:
    name = re.sub("[^a-zA-Z0-9_-]+", "-", value.strip()).strip("-")
    if not name:
        raise ValueError("Asset names must contain letters or digits")
    return name


def render_workflow_report(
    result: Any,
    directory: str | Path,
    *,
    title: str = "Scientific workflow analysis",
    format: str = "markdown",
    figures: Mapping[str, str | Path] | None = None,
    limitations: tuple[str, ...] = (),
    figure_captions: Mapping[str, str] | None = None,
) -> WorkflowReportArtifact:
    """Render real model reports, tables, diagnostics and SHA256 provenance.

    The destination must be empty. Figures must already exist; they are copied
    without model inference. Limitations and figure captions are supplied by
    the analyst, with explicit generic inferential caveats appended.
    """
    _validate_workflow_result(result)
    if format not in {"markdown", "html"} or not title.strip():
        raise ValueError("Choose a nonempty title and format='markdown' or 'html'")
    directory = Path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise FileExistsError("Refusing to overwrite a populated reporting directory")
    directory.mkdir(parents=True, exist_ok=True)
    evidence = directory / "evidence"
    evidence.mkdir()
    provenance = {
        "workflow_schema_version": result.workflow_schema_version,
        "workflow_contract": result.workflow_contract,
        "config": workflow_config_to_dict(result.config),
        "provenance": _jsonable(result.provenance, path="provenance"),
        "analyst_limitations": list(limitations),
        "generated_inference": False,
    }
    provenance_path = evidence / "provenance.json"
    provenance_path.write_text(json.dumps(provenance, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    summary = workflow_summary_frame(result)
    decisions = workflow_decisions_frame(result.decisions)
    steps = workflow_steps_frame(result.steps)
    for filename, dataframe in (
        ("summary.csv", summary), ("decisions.csv", decisions), ("steps.csv", steps)
    ):
        dataframe.to_csv(evidence / filename, index=False)

    tables = dict(getattr(result, "tables", {}) or {})
    names: set[str] = set()
    paths: dict[str, str] = {}
    for name, dataframe in sorted(tables.items()):
        if not isinstance(dataframe, pd.DataFrame):
            raise TypeError("Each result table must be a pandas DataFrame")
        filename = _file_name(name) + ".csv"
        if filename in names:
            raise ValueError("Table names collide after filename normalization")
        names.add(filename)
        dataframe.to_csv(evidence / filename, index=False)
        paths[name] = "evidence/" + filename

    assets: dict[str, str] = {}
    for name, source in sorted((figures or {}).items()):
        source = Path(source)
        if not source.is_file() or source.suffix.lower() not in {".svg", ".png", ".jpg", ".jpeg"}:
            raise ValueError("Figures must be existing SVG/PNG/JPG files")
        filename = _file_name(name) + source.suffix.lower()
        if filename in names:
            raise ValueError("Figure names collide with an existing file")
        names.add(filename)
        shutil.copyfile(source, evidence / filename)
        assets[name] = "evidence/" + filename

    caveats = (
        "Descriptive figures are not significance tests or time-region inference. "
        "The original estimator must provide valid uncertainty before making inferential claims.",
        "Interpret model output conditional on the declared sampling design, "
        "units, missingness, preprocessing, and model assumptions.",
    )
    reports = dict(getattr(result, "reports", {}) or {})
    if format == "markdown":
        text = [
            "# " + title, "", "## Methods and declared specification", "",
            workflow_reporting_text(result), "",
            "Full configuration, ordered steps and choices: [provenance](evidence/provenance.json), "
            "[decisions](evidence/decisions.csv), [steps](evidence/steps.csv).",
            "", "## Results (existing estimator outputs)", "",
        ]
        for name, output in sorted(reports.items()):
            text.extend(["### " + name, "", str(output), ""])
        text.extend(["## Tables", ""])
        text.extend(["- [" + name + "](" + path + ")" for name, path in paths.items()])
        if not paths:
            text.append("No tables supplied.")
        text.extend(["", "## Figures", ""])
        for name, path in assets.items():
            caption = (figure_captions or {}).get(name, "Analyst-provided figure; no automatic scientific interpretation.")
            text.extend(["![" + name + "](" + path + ")", "", "*Figure: " + caption + "*", ""])
        if not assets:
            text.append("No figures supplied.")
        text.extend(["", "## Diagnostics", "",
                     "[Summary](evidence/summary.csv) | [Audit decisions](evidence/decisions.csv) | "
                     "[Step warnings](evidence/steps.csv)", "",
                     "## Limitations", ""])
        text.extend("- " + str(caveat) for caveat in (*caveats, *limitations))
        text.extend(["", "## Reproducibility", "",
                     "SHA256 evidence is provided in manifest.json; no inferential analysis was invented.", ""])
        report = directory / "report.md"
        report.write_text("\n".join(text), encoding="utf-8")
    else:
        blocks = [
            "<h1>" + escape(title) + "</h1>",
            "<h2>Methods and declared specification</h2><p>" +
            escape(workflow_reporting_text(result)) + "</p>",
            "<h2>Results (existing estimator outputs)</h2>",
        ]
        for name, output in sorted(reports.items()):
            blocks.append("<h3>" + escape(name) + "</h3><pre>" + escape(str(output)) + "</pre>")
        blocks.append("<h2>Tables</h2>")
        for name, dataframe in sorted(tables.items()):
            blocks.append("<h3>" + escape(name) + "</h3>" + dataframe.to_html(index=False, escape=True))
        blocks.append("<h2>Figures</h2>")
        for name, path in assets.items():
            caption = (figure_captions or {}).get(name, "Analyst-provided figure; no automatic interpretation.")
            blocks.append("<figure><img src='" + escape(path, quote=True) +
                          "' alt='" + escape(name, quote=True) + "'><figcaption>" +
                          escape(caption) + "</figcaption></figure>")
        blocks.append("<h2>Diagnostics</h2>" + summary.to_html(index=False, escape=True))
        blocks.append("<h2>Limitations</h2><ul>" +
                      "".join("<li>" + escape(str(c)) + "</li>" for c in (*caveats, *limitations)) +
                      "</ul>")
        blocks.append("<p>See evidence/provenance.json and manifest.json for auditable evidence.</p>")
        report = directory / "report.html"
        report.write_text("<!doctype html><html><head><meta charset='utf-8'></head><body>" +
                          "\n".join(blocks) + "</body></html>\n", encoding="utf-8")

    checksums = {
        str(path.relative_to(directory)): sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.rglob("*")) if path.is_file()
    }
    manifest = directory / "manifest.json"
    manifest.write_text(json.dumps({
        "schema_version": 1, "workflow_contract": result.workflow_contract,
        "format": format, "file_sha256": checksums, "auto_inference": False,
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return WorkflowReportArtifact(
        report_path=report, provenance_path=provenance_path, manifest_path=manifest,
        files_sha256=checksums, format=format,
    )
