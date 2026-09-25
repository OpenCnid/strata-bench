"""Fresh selected-model synthetic seed; never relabel historical native evidence."""

import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

from mcbench.controller import Controller, READINESS
from mcbench.storage import Principal, canonical
from test_native_export import stopped
from test_native_revisions import admitted
from test_native_skill_activation import activate

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from native_team_channel_probe import POLICY

SCRIPT = '''const find=name=>ALL_TOOLS.find(t=>t.name.endsWith("__"+name)).name;
const read=await tools[find("artifact_read")]({path:"active/revisions.json"});
text({active_script_read:read});
const write=await tools[find("artifact_write")]({path:"notes/active-script.md",expected_ref:null,text:"Active JavaScript ran through the scoped broker.\\n"});
text({active_script_write:write});
'''


def selected_seed(database, cas, tmp_path, example, configs, *, clock=time.time):
    """Build before sealing, using normal synthetic contracts and controller APIs."""
    operator = Principal("operator", "operator")
    policy = cas.put(operator, "operator", "operator", canonical(POLICY))
    def selected_configs(*args, **kwargs):
        config, agents = configs(*args, **kwargs)
        return config.model_copy(update={"communication_policy": policy}), agents
    request = SimpleNamespace(param="full", node=SimpleNamespace(callspec=None))
    source = admitted.__wrapped__(database, cas, tmp_path, example, selected_configs, request,
                                  model="gpt-6-luna", script=SCRIPT)
    controller = Controller(database, simulation=True, clock=clock)
    proof = cas.put(operator, "operator", "operator", canonical({"is_example": True,
        "scope": "synthetic activation source readiness; no game or native execution"}))
    resources = {"bodies": 1, "memory_mib": 10, "disk_bytes": 1000, "model_slots": 1}
    controller.certify("synthetic", "fixture", resources, proof, simulation=True)
    owner = "synthetic-activation-source"
    epoch = controller.claim("c1", owner, 0)
    for state in ("PROVISIONING", "VALIDATING"):
        controller.transition("c1", owner, epoch, controller.status("c1")["revision"], state, "fixture")
    controller.admit("c1", owner, epoch, controller.status("c1")["revision"], "synthetic", "fixture", resources)
    controller.ready("c1", owner, epoch, controller.status("c1")["revision"], {"a1": dict.fromkeys(READINESS, proof)})
    source_stopped = stopped.__wrapped__(source)
    controller.transition("c1", owner, epoch, controller.status("c1")["revision"], "CHECKPOINTING", "fixture")
    service, checkpoint = activate(source_stopped)
    ref = service.create(checkpoint)
    return source_stopped, service, ref


def test_new_selected_source_complete_join_and_exact_executable_kind(database, cas, tmp_path, example, configs):
    source, service, ref = selected_seed(database, cas, tmp_path, example, configs)
    body = service.load(ref)
    row = database.connection.execute("SELECT * FROM campaigns").fetchone()
    assert row["epoch"] == body["source_epoch"] == 1 and row["state"] == "CHECKPOINTING"
    assert json.loads(row["agents"])[0]["requested_model"] == body["model_identity"] == source[1].model == "gpt-6-luna"
    skill = body["skills"]["learned-crafting"]
    assert skill["revision"]["kind"] == "executable" and skill["revision"]["status"] == "active"
    assert cas.read(Principal("operator", "operator"), "operator", skill["files"]["scripts/check.js"]).decode() == SCRIPT
    assert database.connection.execute("SELECT state FROM native_jobs").fetchone()[0] == "FINALIZED"
    assert service.runtime.budgets.status("a1")["committed_and_reserved"]["spend_microusd"] == 56
    for row in database.connection.execute("SELECT body FROM ledger"):
        assert json.loads(row[0])["model_identity"] == "gpt-6-luna"
    from native_activation_probe import ActivationProbe
    probe = object.__new__(ActivationProbe)
    probe.body, probe.reset = body, False
    code = probe.publish_code()
    assert 'kind:"executable"' in code and 'revision_id:"learned-crafting:2"' in code
