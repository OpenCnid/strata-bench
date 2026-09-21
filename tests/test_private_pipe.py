"""Actual Windows local pipe controls, without a game or model."""

import os
import threading
import time

import pytest

from mcbench.storage import Fault
from strata_evaluator.private_pipe import PrivatePipe

SCOPE = "S-1-5-21-123456789-123456789-123456789-123456789"


@pytest.fixture
def group():
    if os.name != "nt" or not os.environ.get("STRATA_WRITER_TEST_GROUP"):
        pytest.skip("Explicit existing Windows sandbox group required")
    return os.environ["STRATA_WRITER_TEST_GROUP"]


def test_pipe_has_one_instance_and_reads_actual_client_pid(group):
    import _winapi
    from multiprocessing.connection import Client
    pipe = PrivatePipe(group, SCOPE, time.monotonic() + 3)
    result = []
    def exchange():
        try:
            result.append(pipe.accept())
            result.append(pipe.receive(32))
            pipe.send(b"receipt")
        except BaseException as error:
            result.append(error)
    thread = threading.Thread(target=exchange, daemon=True)
    try:
        with pytest.raises(OSError):
            _winapi.CreateNamedPipe(pipe.name, 3 | 0x40000000 | 0x80000, 4 | 2 | 8,
                                   1, 4096, 4096, 0, 0)
        thread.start()
        with Client(pipe.name, family="AF_PIPE") as client:
            client.send_bytes(b"event")
            assert client.poll(2) and client.recv_bytes(32) == b"receipt"
        thread.join(2)
        assert not thread.is_alive() and result == [os.getpid(), b"event"]
    finally:
        pipe.close()


def test_idle_pipe_deadline_is_finite_and_close_is_idempotent(group):
    pipe = PrivatePipe(group, SCOPE, time.monotonic() + 0.25)
    began = time.monotonic()
    try:
        with pytest.raises(Fault, match="TELEMETRY_PIPE_DEADLINE"):
            pipe.accept()
        assert time.monotonic() - began < 1
    finally:
        pipe.close()
        pipe.close()


def test_close_cancels_an_outstanding_accept_without_waiting_for_its_deadline(group):
    pipe = PrivatePipe(group, SCOPE, time.monotonic() + 15)
    result = []
    def accept():
        try:
            pipe.accept()
        except (Fault, OSError) as error:
            result.append(type(error).__name__)
    thread = threading.Thread(target=accept, daemon=True)
    thread.start()
    time.sleep(0.05)
    pipe.close()
    thread.join(2)
    assert not thread.is_alive() and result
