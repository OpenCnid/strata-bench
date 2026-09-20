import hashlib
import json

import pytest

from mcbench.conformance import AcquisitionInputs, preflight
from mcbench.runtime import ExecUsageReader


def test_compact_e9e_suite_keeps_every_mandatory_mechanic_blocked():
    result = preflight("e9e")
    assert result["status"] == "blocked"
    assert result["gate_result"] == "not_run"
    assert result["candidate"]["server_file_id"] == 8161123
    assert len(result["cases"]) == 10
    assert all(case["result"] == "not_run" for case in result["cases"])
    assert "AWAITING_ARTIFACT" in result["blockers"]
    assert "MECHANIC_UNSUPPORTED" in result["blockers"]


def test_synthetic_distribution_hashes_cannot_establish_compatibility(tmp_path):
    fixture = tmp_path / "fixture.bin"
    fixture.write_bytes(b"public synthetic bytes; not Minecraft")
    inputs = AcquisitionInputs.model_validate(
        {
            "target": "e9e",
            "provider": "curseforge",
            "is_example": True,
            "artifacts": [
                {
                    "path": str(fixture),
                    "sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
                    "role": "client",
                    "file_id": 8161120,
                }
            ],
        }
    )
    result = preflight("e9e", inputs)
    assert len(result["verified_distribution_hashes"]) == 1
    assert result["status"] == "blocked"
    assert "EXAMPLE_NOT_EXECUTABLE" in result["blockers"]
    inputs.artifacts[0].sha256 = "0" * 64
    inputs.artifacts[0].file_id = 42
    result = preflight("e9e", inputs)
    assert "HASH_MISMATCH" in result["blockers"]
    assert "RELEASE_MISMATCH" in result["blockers"]


def test_usage_ingestion_deduplicates_source_cursor_but_not_actual_repeated_turns():
    reader = ExecUsageReader()
    line = json.dumps(
        {
            "type": "turn.completed",
            "usage": {"input_tokens": 12, "cached_input_tokens": 3, "output_tokens": 4},
        }
    )
    reader.ingest(1, line)
    reader.ingest(1, line)
    reader.ingest(2, line)
    result = reader.report()
    assert result["usage"]["input_tokens"] == 24
    assert result["completed_turns"] == 2
    assert result["model_calls"] is None
    assert result["spend_microusd"] is None
    assert not result["all_call_accounting_verified"]
    with pytest.raises(ValueError, match="IDEMPOTENCY_CONFLICT"):
        reader.ingest(1, '{"type":"turn.started"}')


@pytest.mark.parametrize(
    "line,code",
    [
        ('{"type":"new.event"}', "SCHEMA_UNSUPPORTED"),
        ('{"type":"turn.completed"}', "METERING_UNAVAILABLE"),
        (
            '{"type":"turn.completed","usage":{"input_tokens":1,"cached_input_tokens":2,"output_tokens":0}}',
            "METERING_UNAVAILABLE",
        ),
    ],
)
def test_unknown_schema_or_metering_is_never_zero(line, code):
    reader = ExecUsageReader()
    with pytest.raises(ValueError, match=code):
        reader.ingest(1, line)
    assert reader.report()["completed_turns"] == 0
