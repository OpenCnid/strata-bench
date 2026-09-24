"""Synthetic private journal consumption; no game or process authority claim."""

import pytest

from mcbench.runtime_data import inspect_runtime_data_journal
from mcbench.storage import Fault


@pytest.mark.parametrize("change", [None, "repeated_reads", "pid", "truncated", "missing", "unknown", "quota", "refused", "foreign_hash"])
def test_journal_requires_exact_scope_and_complete_bounded_records(tmp_path, change):
    report = {"policy": "e9e1270-runtime-data-snapshot/1", "jar_sha256": "a" * 64, "index_sha256": "b" * 64,
              "inputs": [{"name": n, "sha256": "c" * 64} for n in
                         ("whitelist.txt", "blacklist.txt", "contributorRevolvers.json")]}
    lines = ["STRATA_FIXED_DATA_READY/1 " + "b" * 64,
             "STRATA_FIXED_DATA_BOUND/1 com/portingdeadmods/cable_facades/CFConfig 1ab0dee01c531ff6a89fd85aee2109f5e8036d342e0c283e76a9101b0aab8092",
             "STRATA_FIXED_DATA_BOUND/1 blusunrize/immersiveengineering/ImmersiveEngineering$ThreadContributorSpecialsDownloader b47bfd98a885800760e9e7d7c24d60ec2d4e89da6cbc1ed9ad1e82a46283e2fb",
             *("STRATA_FIXED_DATA_READ/1 " + r["name"] + " " + r["sha256"] for r in report["inputs"])]
    if change == "repeated_reads":
        lines += lines[-3:-1]
    elif change == "missing":
        lines.pop()
    elif change == "unknown":
        lines.append("STRATA_FIXED_DATA_UNKNOWN/1")
    elif change == "quota":
        lines *= 6
    elif change == "refused":
        lines.append("STRATA_FIXED_DATA_JOURNAL_REFUSED/1")
    elif change == "foreign_hash":
        lines.append(lines[-1].replace("c" * 64, "d" * 64))
    raw = ("\n".join(lines) + ("" if change == "truncated" else "\n")).encode("ascii")
    path = tmp_path / "strata-fixed-17-00000000-0000-0000-0000-000000000000.log"
    path.write_bytes(raw)
    if change not in {None, "repeated_reads"}:
        with pytest.raises(Fault):
            inspect_runtime_data_journal(path, report, process_id=18 if change == "pid" else 17)
    else:
        result = inspect_runtime_data_journal(path, report, process_id=17)
        assert result["journal"]["process_id"] == 17
        assert result["journal"]["bytes"] == len(raw)
        assert len(result["read_inputs"]) == 3
        assert not result["all_runtime_downloads_qualified"]


@pytest.mark.parametrize("role", ["server", "client"])
@pytest.mark.parametrize("version", [2, 3])
@pytest.mark.parametrize("change", [None, "missing_added_class", "missing_added_read", "unknown_policy", "legacy_policy"])
def test_extended_snapshot_requires_all_added_classes_and_bodies(tmp_path, change, version, role):
    from mcbench.runtime_data import SNAPSHOTS, SERVER_REWARD_CLASSES
    policy = f"e9e1270-runtime-data-snapshot/{version}"
    _, sources, classes = SNAPSHOTS[policy]
    if version == 3 and role == "server":
        classes = classes | SERVER_REWARD_CLASSES
    report = {"policy": policy, "jar_sha256": "a" * 64, "index_sha256": "b" * 64,
              "inputs": [{"name": n, "sha256": "c" * 64} for n in sources]}
    lines = ["STRATA_FIXED_DATA_READY/1 " + report["index_sha256"],
             *("STRATA_FIXED_DATA_BOUND/1 " + n + " " + h for n, h in classes.items()),
             *("STRATA_FIXED_DATA_READ/1 " + r["name"] + " " + r["sha256"] for r in report["inputs"])]
    if change == "missing_added_class":
        del lines[4]
    elif change == "missing_added_read":
        lines.pop()
    elif change == "unknown_policy":
        report["policy"] = "unknown"
    elif change == "legacy_policy":
        report["policy"] = "e9e1270-runtime-data-snapshot/1"
    path = tmp_path / "strata-fixed-17-00000000-0000-0000-0000-000000000000.log"
    path.write_bytes(("\n".join(lines) + "\n").encode())
    if change:
        with pytest.raises(Fault, match="RUNTIME_DATA_EXECUTION"):
            inspect_runtime_data_journal(path, report, process_id=17, role=role)
    else:
        result = inspect_runtime_data_journal(path, report, process_id=17, role=role)
        assert len(result["bound_classes"]) == len(classes) and len(result["read_inputs"]) == len(sources)


@pytest.mark.parametrize("role", ["server", "client", "unknown"])
def test_reward_journal_rejects_other_role_class_bytes(tmp_path, role):
    from mcbench.runtime_data import POLICY, SNAPSHOTS, SERVER_REWARD_CLASSES
    _, sources, classes = SNAPSHOTS[POLICY]
    # Give the requested client a server journal, and vice versa. Every body
    # and marker is present, so only the class representation is wrong.
    if role == "client":
        classes = classes | SERVER_REWARD_CLASSES
    report = {"policy": POLICY, "jar_sha256": "a" * 64, "index_sha256": "b" * 64,
              "inputs": [{"name": n, "sha256": "c" * 64} for n in sources]}
    lines = ["STRATA_FIXED_DATA_READY/1 " + report["index_sha256"],
             *("STRATA_FIXED_DATA_BOUND/1 " + n + " " + h for n, h in classes.items()),
             *("STRATA_FIXED_DATA_READ/1 " + n + " " + "c" * 64 for n in sources)]
    path = tmp_path / "strata-fixed-17-00000000-0000-0000-0000-000000000000.log"
    path.write_text("\n".join(lines) + "\n", encoding="ascii")
    with pytest.raises(Fault, match="RUNTIME_DATA_ROLE" if role == "unknown" else "RUNTIME_DATA_EXECUTION"):
        inspect_runtime_data_journal(path, report, process_id=17, role=role)
