"""Real Windows ACL/handle regressions on disposable directories; no game/model."""

import ctypes as c
import os

import pytest

from mcbench.storage import Fault
from strata_evaluator.windows_writer import WindowsSecurity, WriterTree, OperatorWorkspace, component


@pytest.mark.parametrize("name", ["", ".", "..", "a/b", "a\\b", "a:stream", "a.", "a ",
                                  "CON", "nul.dat", "LPT1.log", "COM0", " a", "a" * 121])
def test_ambiguous_or_escaping_components_reject(name):
    with pytest.raises(Fault, match="WRITER_COMPONENT_INVALID"):
        component(name)


@pytest.fixture
def security():
    if os.name != "nt":
        pytest.skip("Windows access boundary")
    return WindowsSecurity()


@pytest.fixture
def writer_sid():
    sid = os.environ.get("STRATA_WRITER_TEST_SID")
    if not sid:
        pytest.skip("Explicit existing separate test user SID required")
    return sid


@pytest.fixture
def writer_group():
    sid = os.environ.get("STRATA_WRITER_TEST_GROUP")
    if not sid:
        pytest.skip("Explicit existing sandbox group SID required")
    return sid


# Owned synthetic scope only; native positive/sibling evidence uses the actual
# profile SID discovered from a newly enrolled canary workspace.
SYNTHETIC_SCOPE = "S-1-5-21-123456789-123456789-123456789-123456789"


@pytest.fixture
def tree(tmp_path, writer_sid, writer_group):
    value = WriterTree(tmp_path / "guarded", writer_sid, writer_group, SYNTHETIC_SCOPE)
    try:
        yield value
    finally:
        value.close()
        # These fixtures stay empty. After the namespace lease closes the
        # writable parent permits removing the empty directory. Do not change
        # its ACL, recursively delete anything or imply crash-recovery authority.
        assert not list(value.path.iterdir())
        value.path.rmdir()


def test_same_user_has_read_but_cannot_gain_write_delete_or_acl_authority(tree):
    tree.verify()
    kernel = tree.security.kernel
    for access in (2, 4, 0x10000, 0x40000, 0x80000):
        handle = kernel.CreateFileW(str(tree.path), access, 7, None, 3, 0x02000000, None)
        assert handle == c.c_void_p(-1).value
        # Parent DELETE_CHILD can authorize root deletion; its held sharing
        # lease must deny that route with SHARING_VIOLATION instead.
        assert c.get_last_error() == (32 if access == 0x10000 else 5)
    assert list(tree.path.iterdir()) == []
    with pytest.raises(PermissionError):
        (tree.path / "world").mkdir()
    with pytest.raises(PermissionError):
        (tree.path / "injected").write_bytes(b"invalid")


def test_held_root_and_ancestors_cannot_be_replaced_even_when_empty(tree):
    for path in (tree.path, tree.path.parent):
        with pytest.raises(PermissionError):
            path.rename(path.with_name(path.name + "-replaced"))
    tree.verify()


def test_existing_tree_never_adopted_or_reinitialized(tree):
    before = tree.security.access(tree.path)
    with pytest.raises(Fault, match="WRITER_CREATE_DENIED"):
        WriterTree(tree.path, tree.writer_sid, tree.group_sid, tree.scope_sid)
    assert tree.security.access(tree.path) == before


@pytest.mark.parametrize("kind", ["current_user", "system", "everyone", "owner_rights", "unknown"])
def test_invalid_writer_identity_does_not_create_any_tree(tmp_path, security, kind):
    sid = {"current_user": security.current_sid, "system": "S-1-5-18", "everyone": "S-1-1-0",
           "owner_rights": "S-1-3-4", "unknown": "S-1-5-21-1-2-3-4294967295"}[kind]
    path = tmp_path / "never-created"
    with pytest.raises(Fault, match="WRITER_DISTINCT_USER_REQUIRED|WRITER_IDENTITY_UNAVAILABLE"):
        WriterTree(path, sid, "unused", SYNTHETIC_SCOPE)
    assert not path.exists()


def test_unprotected_directory_cannot_be_mistaken_for_protected_root(tree, tmp_path):
    other = tmp_path / "ordinary"
    other.mkdir()
    with pytest.raises(Fault, match="WRITER_ACL_CHANGED"):
        tree.security.verify(other, tree.writer_sid, tree.group_sid, tree.scope_sid,
                             directory=True, root=True)


def test_account_allowance_cannot_replace_scoped_group_grant(tmp_path, writer_sid):
    with pytest.raises(Fault, match="WRITER_PRINCIPAL_TYPE"):
        WriterTree(tmp_path / "never-created", writer_sid, writer_sid, SYNTHETIC_SCOPE)


def test_operator_or_local_account_sid_cannot_be_workspace_scope(tmp_path, writer_sid, writer_group):
    with pytest.raises(Fault, match="WRITER_SCOPE_SID_INVALID"):
        WriterTree(tmp_path / "never-created", writer_sid, writer_group, writer_sid)


def test_wrong_scope_cannot_validate_an_existing_tree(tree):
    with pytest.raises(Fault, match="WRITER_ACL_CHANGED"):
        tree.security.verify(tree.path, tree.writer_sid, tree.group_sid,
            "S-1-5-21-987654321-987654321-987654321-987654321", directory=True, root=True)


def test_close_is_idempotent_and_does_not_reset_acl(tree):
    before = tree.security.access(tree.path)
    tree.close()
    tree.close()
    assert tree.security.access(tree.path) == before
    with pytest.raises(PermissionError):
        (tree.path / "not-refunded").write_bytes(b"invalid")
    with pytest.raises(Fault, match="WRITER_PREPARATION_CLOSED"):
        tree.verify()


def test_failed_post_creation_validation_releases_all_namespace_handles(
        tmp_path, writer_sid, writer_group, monkeypatch):
    def fail(self):
        raise Fault("WRITER_ACL_CHANGED")
    monkeypatch.setattr(WriterTree, "verify", fail)
    path = tmp_path / "failed"
    with pytest.raises(Fault, match="WRITER_ACL_CHANGED"):
        WriterTree(path, writer_sid, writer_group, SYNTHETIC_SCOPE)
    assert not list(path.iterdir())
    path.rmdir()  # Still-held namespace handles would deny this.


def test_workspace_excludes_inheritance_and_keeps_namespace_until_close(tmp_path, security):
    path = tmp_path / "preparation"
    workspace = OperatorWorkspace(path)
    try:
        owner, protected, entries = security.access(path)
        assert owner == security.current_sid and protected
        assert len(entries) == 2
        assert {entry[2] for entry in entries} == {security.current_sid, "S-1-5-18"}
        with pytest.raises(PermissionError):
            path.rename(path.with_name("replaced"))
        with pytest.raises(Fault, match="WRITER_WORKSPACE_ACL"):
            workspace.verify_enrolled("absent-group", SYNTHETIC_SCOPE)
        with pytest.raises(Fault, match="WRITER_CREATE_DENIED"):
            OperatorWorkspace(path)
        before = security.access(path)
    finally:
        workspace.close()
    workspace.close()
    assert security.access(path) == before
    with pytest.raises(Fault, match="WRITER_WORKSPACE_CLOSED"):
        workspace.verify_enrolled("absent-group", SYNTHETIC_SCOPE)
    path.rmdir()
