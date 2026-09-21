"""Owned Python process death, synthetic checkpoints; no native/game claim."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from native_activation_fault_probe import PHASES, run_fault
from mcbench.native import NativeExec
from mcbench.native_skill_activation import NativeSkillSets
from mcbench.storage import CAS, Database, Fault
from test_native_skill_activation import activate, admitted as _admitted, stopped as _stopped

admitted = _admitted
stopped = _stopped


@pytest.mark.parametrize("phase", PHASES)
def test_owned_process_death_never_grants_partial_activation(stopped, tmp_path, phase):
    service, checkpoint = activate(stopped)
    before = service.runtime.budgets.status("a1")
    target = tmp_path / "interrupted-view"
    result = run_fault(service.db.path, service.cas.root, checkpoint, target, phase)
    assert result["returncode"] != 0 and result["costs_unchanged"]
    assert not result["observed_after_kill"]["view_registered"]
    assert result["observed_after_kill"]["target_exists"] is (phase in {"after_view_rename", "before_view_commit"})
    # Independent reopened services, never reuse the terminated process's state.
    db = Database(service.db.path)
    try:
        resumed = NativeSkillSets(NativeExec(db, CAS(db, service.cas.root), simulation=True))
        ref = resumed.create(checkpoint)
        body = resumed.load(ref)
        plan = stopped[1].model_copy(update={"job_id": "fresh", "epoch": 2, "workspace": str(target),
            "skill_activation_ref": ref, "helper_skill_activation_ref": ref})
        with pytest.raises(Fault, match="NATIVE_SKILL_VIEW_UNCOMMITTED"):
            resumed.validate_launch(plan)
        if target.exists():
            resumed._verify_files(target, resumed.view_files(body))
            with pytest.raises(Fault, match="TARGET_EXISTS"):
                resumed.materialize(ref, target)
        recovered = Path(resumed.materialize(ref, tmp_path / "fresh-view")["path"])
        resumed._verify_files(recovered, resumed.view_files(body))
        assert resumed.runtime.budgets.status("a1") == before
    finally:
        db.close()
