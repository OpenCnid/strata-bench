"""Storage path checks retain ancestor, reparse and access-denial boundaries."""

import os
from pathlib import Path
import stat
import subprocess
from types import SimpleNamespace

import pytest

from mcbench.storage import Fault, reject_links


@pytest.mark.parametrize("change", ["symlink", "reparse", "denied"])
def test_missing_descendant_does_not_hide_changed_ancestor(tmp_path, monkeypatch, change):
    path = tmp_path / "new" / "missing" / "leaf"
    reject_links(path)
    original = Path.lstat

    def changed(part, *args, **kwargs):
        if part.name == "new":
            if change == "denied":
                raise PermissionError("unreadable ancestor")
            return SimpleNamespace(st_mode=stat.S_IFLNK if change == "symlink" else stat.S_IFDIR,
                                   st_file_attributes=0x400 if change == "reparse" else 0)
        return original(part, *args, **kwargs)

    monkeypatch.setattr(Path, "lstat", changed)
    with pytest.raises(PermissionError if change == "denied" else Fault,
                       match="unreadable ancestor" if change == "denied" else "UNSAFE_PATH"):
        reject_links(path)


@pytest.mark.skipif(os.name != "nt", reason="actual Windows junction")
def test_native_junction_rejects_existing_and_missing_children(tmp_path):
    target, link = tmp_path / "target", tmp_path / "junction"
    target.mkdir()
    child = target / "retained"
    child.write_bytes(b"unchanged")

    def quote(value):
        return "'" + str(value).replace("'", "''") + "'"

    subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
        f"New-Item -ItemType Junction -Path {quote(link)} -Target {quote(target)} -ErrorAction Stop | Out-Null"],
        capture_output=True, check=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        assert link.lstat().st_file_attributes & 0x400
        for path in (link, link / "retained", link / "missing" / "nested"):
            with pytest.raises(Fault, match="UNSAFE_PATH"):
                reject_links(path)
    finally:
        link.rmdir()  # Remove only the junction, never its target.
    assert child.read_bytes() == b"unchanged"
