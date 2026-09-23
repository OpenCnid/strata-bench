"""Export the implemented public contracts; do not export private schemas here."""

import json
from pathlib import Path

from mcbench.records import AGENT_RECORDS, EVALUATOR_RECORDS, OPERATOR_RECORDS
from mcbench.authorization import ExecutionAuthorization, ModelExecutionAuthorization
from mcbench.native import NativeLaunch
from mcbench.provisioning import (
    AcquisitionReceipt, LaunchProfile, VanillaLaunchProfile, ProvisioningCheck, ProvisioningEvidence, RoleInventoryInput,
)

OPERATOR_API_MODELS = (ExecutionAuthorization, ModelExecutionAuthorization, NativeLaunch, AcquisitionReceipt, LaunchProfile, VanillaLaunchProfile,
                       ProvisioningCheck, ProvisioningEvidence, RoleInventoryInput)

ROOT = Path(__file__).resolve().parents[1]
for domain, models in (("public", AGENT_RECORDS), ("operator", [*OPERATOR_RECORDS, *OPERATOR_API_MODELS]),
                      ("evaluator", EVALUATOR_RECORDS)):
    for model in models:
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        target = ROOT / "schemas" / "v1" / domain / f"{model.__name__}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8", newline="\n")
