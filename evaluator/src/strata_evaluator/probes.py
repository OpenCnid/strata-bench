"""Matched fresh-clone manifests and explicit identity quarantine decisions."""

from mcbench.storage import digest, require

BASE_FIELDS = {"system_digest", "pack_lock", "world", "equipment", "keymap", "tools", "budget",
               "public_goal", "backend_initial_state", "runtime_initial_state", "information_policy"}


def matched_pair(base: dict, initial: dict, experienced: dict, *, allowed_kinds: set[str], t0=False):
    require(set(base) == BASE_FIELDS, "CLONE_FIELDS")
    require(set(initial) == set(experienced) <= allowed_kinds, "PROJECTION_POLICY")
    for artifacts in (initial, experienced):
        for item in artifacts.values():
            require(set(item) == {"content", "origin"} and item["origin"] in
                    {"initial", "campaign", "practice"}, "PROBE_IMPORT_FORBIDDEN")
    require(all(a["origin"] == "initial" for a in initial.values()), "INITIAL_ARTIFACT_CHANGED")
    if t0:
        require(initial == experienced, "T0_NOT_MATCHED")
    arms = {"experienced": dict(base) | {"artifacts": experienced},
            "initial": dict(base) | {"artifacts": initial}}
    require(all(arms["experienced"][k] == arms["initial"][k] for k in BASE_FIELDS), "UNMATCHED_CLONE")
    return {"schema": "strata/ProbePairPlan/1", "arms": arms, "base_digest": digest(base),
            "fresh_processes_required": True, "disposable_namespaces_required": True,
            "campaign_feedback_allowed": False, "executed": False}


def identity_decision(expected_system, returned_system, expected_model, returned_model,
                      *, immutable, last_verified_cursor, current_cursor):
    require(0 <= last_verified_cursor <= current_cursor, "IDENTITY_CURSOR")
    changed = expected_system != returned_system or (
        expected_model is not None and returned_model is not None and expected_model != returned_model)
    if changed:
        return {"status": "drift", "quarantine_after": last_verified_cursor,
                "quarantine_through": current_cursor, "revoke_grants": True,
                "fresh_cohort_and_anchors": True, "retain_costs": True}
    if not immutable or expected_model is None or returned_model is None:
        return {"status": "provider_version_unverified", "fixed_model_claim": False,
                "last_verified_cursor": last_verified_cursor}
    return {"status": "verified", "last_verified_cursor": current_cursor}
