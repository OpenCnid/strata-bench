"""Capacity must reject before paid dispatch and protect reserved receipt space."""
import hashlib
from types import SimpleNamespace

import pytest
import test_inference_transport as transport_tests
from mcbench import storage_capacity as capacity
from mcbench.inference_transport import MAX_RESPONSE_BYTES, SyntheticResponsesTransport
from mcbench.storage import CAS, Database, Fault, Principal

fixture_gateway, provider = transport_tests.fixture_gateway, transport_tests.provider
OP = Principal('operator', 'operator')


def test_separate_operator_allowance_and_unchanged_agent_quota():
    assert capacity.quota(OP, 'operator', 'operator') == 128 * 1024**2
    for principal, namespace, visibility in [(OP, 'agent:a', 'agent'),
            (Principal('operator', 'executor'), 'operator', 'agent'), (OP, 'operator', 'agent')]:
        assert capacity.quota(principal, namespace, visibility) == 20 * 1024**2


def test_reserved_capacity_blocks_other_connection_and_survives_restart(cas, database, monkeypatch):
    monkeypatch.setattr(capacity, 'OPERATOR_QUOTA', 100)
    capacity.reserve(cas, OP, 'operator', 'one', 60)
    db2 = Database(database.path)
    other = CAS(db2, cas.root)
    try:
        other.put(OP, 'operator', 'operator', b'x' * 40)
        with pytest.raises(Fault, match='ARTIFACT_QUOTA'):
            other.put(OP, 'operator', 'operator', b'z', quota_bytes=2**53-1)
        with pytest.raises(Fault, match='ARTIFACT_CAPACITY'):
            capacity.reserve(other, OP, 'operator', 'two', 1)
        ref = other.put(OP, 'operator', 'operator', b'y' * 60, reservation='one')
        row = db2.connection.execute('SELECT state,ref FROM artifact_reservations').fetchone()
        assert tuple(row) == ('CONSUMED', ref)
        with pytest.raises(Fault, match='ARTIFACT_RESERVATION_INVALID'):
            other.put(OP, 'operator', 'operator', b'y' * 60, reservation='one')
    finally:
        db2.close()


def test_file_import_honors_receipt_reservation(cas, tmp_path, monkeypatch):
    monkeypatch.setattr(capacity, 'OPERATOR_QUOTA', 100)
    capacity.reserve(cas, OP, 'operator', 'one', 60)
    source = tmp_path / 'asset'
    source.write_bytes(b'x' * 41)
    with pytest.raises(Fault, match='ARTIFACT_QUOTA'):
        cas.put_file(OP, 'operator', 'operator', source, hashlib.sha256(source.read_bytes()).hexdigest(),
                     quota_bytes=100, max_object_bytes=100)
    assert not list(cas.root.iterdir())


def test_write_failure_rolls_back_consumption(cas, database, monkeypatch):
    capacity.reserve(cas, OP, 'operator', 'one', 60)
    def fail(*args):
        raise OSError('synthetic full disk')
    monkeypatch.setattr('mcbench.storage.os.fsync', fail)
    with pytest.raises(OSError):
        cas.put(OP, 'operator', 'operator', b'x', reservation='one')
    assert database.connection.execute('SELECT state FROM artifact_reservations').fetchone()[0] == 'RESERVED'
    assert database.connection.execute('SELECT count(*) FROM objects').fetchone()[0] == 0
    assert not list(cas.root.iterdir())


def test_disk_margin_and_helper_cannot_reserve(cas, monkeypatch):
    monkeypatch.setattr(capacity.shutil, 'disk_usage', lambda _: SimpleNamespace(free=capacity.DISK_MARGIN))
    with pytest.raises(Fault, match='ARTIFACT_DISK_CAPACITY'):
        capacity.reserve(cas, OP, 'operator', 'one', 1)
    with pytest.raises(Fault, match='FORBIDDEN'):
        capacity.reserve(cas, Principal('operator', 'helper'), 'operator', 'one', 1)


def test_full_store_refuses_before_provider_or_charge(fixture_gateway, provider, monkeypatch):
    gate, attempt, reserve, raw = fixture_gateway
    used = gate.db.connection.execute('SELECT sum(bytes) FROM objects').fetchone()[0]
    monkeypatch.setattr(capacity, 'OPERATOR_QUOTA', used + MAX_RESPONSE_BYTES - 1)
    endpoint, requests = provider(transport_tests.stream(transport_tests.response()))
    delivered = []
    with pytest.raises(Fault, match='ARTIFACT_CAPACITY'):
        SyntheticResponsesTransport(gate, endpoint).execute('a1', attempt, reserve, raw,
            on_headers=lambda *a: delivered.append(a), on_chunk=delivered.append)
    assert requests == delivered == []
    assert gate.db.connection.execute('SELECT count(*) FROM inference_attempts').fetchone()[0] == 0
    assert gate.db.connection.execute('SELECT count(*) FROM operations').fetchone()[0] == 0


def test_near_full_store_delivers_only_durable_settled_receipt(fixture_gateway, provider, monkeypatch):
    gate, attempt, reserve, raw = fixture_gateway
    used = gate.db.connection.execute('SELECT sum(bytes) FROM objects').fetchone()[0]
    monkeypatch.setattr(capacity, 'OPERATOR_QUOTA', used + MAX_RESPONSE_BYTES)
    wire = transport_tests.stream(transport_tests.response())
    endpoint, requests = provider(wire)
    def receive(chunk):
        assert gate.status(reserve.operation_id)['state'] == 'SETTLED'
        ref = 'cas:sha256:' + hashlib.sha256(chunk).hexdigest()
        assert gate.cas.read(OP, 'operator', ref) == wire
        assert gate.db.connection.execute('SELECT state FROM artifact_reservations').fetchone()[0] == 'CONSUMED'
    assert SyntheticResponsesTransport(gate, endpoint).execute('a1', attempt, reserve, raw,
        on_headers=lambda *a: None, on_chunk=receive)['state'] == 'SETTLED'
    assert len(requests) == 1


def test_delivery_failure_preserves_settled_cost_and_never_redelivers(fixture_gateway, provider):
    gate, attempt, reserve, raw = fixture_gateway
    endpoint, requests = provider(transport_tests.stream(transport_tests.response()))
    adapter = SyntheticResponsesTransport(gate, endpoint)
    def broken(chunk):
        raise BrokenPipeError('private synthetic value')
    with pytest.raises(BrokenPipeError):
        adapter.execute('a1', attempt, reserve, raw, on_headers=lambda *a: None, on_chunk=broken)
    assert gate.status(reserve.operation_id)['state'] == 'SETTLED'
    assert not gate.budgets.status('a1')['uncertain']
    assert gate.budgets.status('a1')['committed_and_reserved']['spend_microusd'] == 46
    assert adapter.execute('a1', attempt, reserve, raw, on_headers=lambda *a: None, on_chunk=broken)['state'] == 'SETTLED'
    assert len(requests) == 1
    event = gate.db.connection.execute("SELECT body FROM outbox WHERE kind='inference.delivery_failure'").fetchone()[0]
    assert 'private synthetic value' not in event and 'receipt_settled' in event
