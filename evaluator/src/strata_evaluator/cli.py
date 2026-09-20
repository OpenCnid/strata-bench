"""Private, offline report reconstruction. No access to live gameplay channels."""

import argparse
import json
import os
import tempfile
from pathlib import Path

from mcbench.records import EvaluationResult
from mcbench.storage import canonical, digest, reject_links

from .analysis import paired_report


def publication_projection(report):
    """Explicit export allowlist: no fixture, lineage, protocol, or private CAS IDs."""
    keys = {"assigned_lineages", "complete_lineages", "experienced", "initial", "gain",
            "percentile_95_ci", "attrition_bounds", "bootstrap_seed", "bootstrap_replicates",
            "independent_unit", "confirmatory_claim", "qualification"}
    return {"schema": "strata/PublicAnalysis/1", **{k: report[k] for k in sorted(keys)},
            "missing_lineage_count": len(report["missing_lineages"]),
            "identity_unverified": "provider_version_unverified" in report["validity_flags"]}


def write_report(path, report):
    path = path.absolute()
    reject_links(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical(report)
    envelope = {"schema": "strata/ReportArtifact/1", "content_digest": digest(report), "report": report}
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".report-")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(envelope) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {"digest": digest(report), "report_bytes": len(payload)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--publication-output", type=Path)
    args = parser.parse_args(argv)
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    results = [EvaluationResult.model_validate_json(line) for line in
               args.results.read_text(encoding="utf-8").splitlines() if line.strip()]
    report = paired_report(plan["assignments"], plan["family_weights"], results,
                           protocol_id=plan["protocol_id"], checkpoint_id=plan["checkpoint_id"],
                           seed=plan["seed"], replicates=plan["replicates"],
                           invalidating_flags=set(plan["invalidating_flags"]) if "invalidating_flags" in plan else None)
    # Retain explicit fixture provenance in the private report. It can never become
    # a scientific observation by removing the marker from the publication view.
    report["synthetic"] = any(result.is_example for result in results) or plan.get("synthetic", False)
    receipt = write_report(args.output, report)
    if args.publication_output:
        public = publication_projection(report) | {"synthetic": report["synthetic"]}
        write_report(args.publication_output, public)
    print(json.dumps({"status": "built", "visibility": "evaluator", **receipt}))


if __name__ == "__main__":
    main()
