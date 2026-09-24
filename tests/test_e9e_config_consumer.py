"""Synthetic control-record validation; real getter execution remains separate."""

import json
import hashlib

import pytest

from mcbench.storage import Fault
from strata_evaluator import e9e_config_consumer as consumer
from strata_evaluator.e9e_config_consumer import MARKER, expected_values, inspect_control

ENTRIES = ["example:yes|true", "example:no|false", "example:vendor_typo|alse"]


def record():
    return {"schema": "strata/SophisticatedConsumerObservation/1", "before": ENTRIES,
            "after": list(ENTRIES), "rows": [
                {"item_id": item, "first": value, "second": value}
                for item, value in expected_values(ENTRIES).items()]}


def inspect(value):
    return inspect_control("ordinary log\n[server] " + MARKER + json.dumps(value), ENTRIES)


def test_consumer_boolean_semantics_and_qualification_limits():
    result = inspect(record())
    assert result["result"] == "pass" and result["getter_calls"] == 6
    assert result["observation"]["rows"][-1]["first"] is False
    assert result["cache_initialization_possible"] and result["raw_configuration_unchanged"]
    assert not result["source_authentication_qualified"] and not result["mechanics_qualified"]
    assert not result["scoring_eligible"] and result["gate_result"] == "not_run"


@pytest.mark.parametrize("change,code", [
    (lambda r: r["after"].append("example:inserted|true"), "CONFIG_CONSUMER_RAW_CHANGED"),
    (lambda r: r["rows"].pop(), "CONFIG_CONSUMER_ROWS"),
    (lambda r: r["rows"].reverse(), "CONFIG_CONSUMER_ROWS"),
    (lambda r: r["rows"][0].update(first=1), "CONFIG_CONSUMER_ROWS"),
    (lambda r: r["rows"][0].update(second=False), "CONFIG_CONSUMER_MISMATCH"),
    (lambda r: r["rows"][1].update(first=True, second=True), "CONFIG_CONSUMER_MISMATCH"),
    (lambda r: r.update(scoring_eligible=True), "CONFIG_CONSUMER_RECORD"),
])
def test_changed_cached_value_raw_configuration_or_forged_shape_rejected(change, code):
    value = record()
    change(value)
    with pytest.raises(Fault, match=code):
        inspect(value)


@pytest.mark.parametrize("entries", [[], ["example:yes|true"] * 2,
                                      ["example:yes|TRUE"], ["example:yes|true');evil()"]])
def test_invalid_or_duplicate_control_entries_reject(entries):
    with pytest.raises(Fault):
        expected_values(entries)


def test_missing_duplicate_and_duplicate_json_key_records_rejected():
    for log in ("", MARKER + json.dumps(record()) + "\n" + MARKER + json.dumps(record()),
                MARKER + '{"schema":1,"schema":2}'):
        with pytest.raises(Fault):
            inspect_control(log, ENTRIES)


def test_preparation_pins_both_artifacts_and_does_not_write(tmp_path, monkeypatch):
    entries = [f"example:item_{i}|true" for i in range(145)]
    files = {"mods/fixture.jar": b"synthetic-jar", consumer.COMMON:
             ('[common]\nenabledItems = ' + json.dumps(entries)).encode()}
    monkeypatch.setattr(consumer, "PINS", {name: hashlib.sha256(raw).hexdigest()
                                         for name, raw in files.items()})
    for name, raw in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    result = consumer.prepare_control(tmp_path)
    assert result["entries"] == entries and "__ENTRIES__" not in result["script"]
    assert all((tmp_path / name).read_bytes() == raw for name, raw in files.items())
    (tmp_path / "mods/fixture.jar").write_bytes(b"replacement")
    with pytest.raises(Fault, match="CONFIG_CONSUMER_ARTIFACT"):
        consumer.prepare_control(tmp_path)
