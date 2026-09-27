"""Export implemented contracts into separate public/operator/evaluator domains."""

import json
import sys
from pathlib import Path

from mcbench.records import AGENT_RECORDS, EVALUATOR_RECORDS, OPERATOR_RECORDS
from mcbench.authorization import ExecutionAuthorization, ModelExecutionAuthorization
from mcbench.native import NativeLaunch
from mcbench.native_probe_binding import NativeProbeArtifactBinding
from mcbench.native_checkpoint import NativeRetentionPolicy, NativeRetentionPolicyV2
from mcbench.provisioning import (
    AcquisitionReceipt, LaunchProfile, VanillaLaunchProfile, E9ELaunchProfile, FrozenE9ELaunchProfile,
    ProvisioningCheck, ProvisioningEvidence, RoleInventoryInput,
)

ROOT = Path(__file__).resolve().parents[1]


def evaluator_models():
    # Operator build only; the evaluator package stays outside gameplay tooling.
    sys.path.insert(0, str(ROOT / "evaluator/src"))
    from strata_evaluator.native_probe_projection import NativeProbeArtifactSelection, NativeProbeArtifactProjection
    from strata_evaluator.probe_pairs import ProbeFixture, ProbePairRequest
    return [*EVALUATOR_RECORDS, NativeProbeArtifactSelection, NativeProbeArtifactProjection, ProbeFixture, ProbePairRequest]

OPERATOR_API_MODELS = (ExecutionAuthorization, ModelExecutionAuthorization, NativeLaunch, NativeProbeArtifactBinding, NativeRetentionPolicy, NativeRetentionPolicyV2, AcquisitionReceipt, LaunchProfile, VanillaLaunchProfile,
                       E9ELaunchProfile, FrozenE9ELaunchProfile, ProvisioningCheck, ProvisioningEvidence, RoleInventoryInput)

for domain, models in (("public", AGENT_RECORDS), ("operator", [*OPERATOR_RECORDS, *OPERATOR_API_MODELS]),
                      ("evaluator", evaluator_models())):
    for model in models:
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        target = ROOT / "schemas" / "v1" / domain / f"{model.__name__}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8", newline="\n")
