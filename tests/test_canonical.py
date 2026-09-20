import json
import shutil
import subprocess
from pathlib import Path

import pytest

from mcbench.storage import canonical, digest


def test_python_and_actual_worker_canonical_hashes_agree():
    root = Path(__file__).resolve().parents[1]
    module = (root / "backends/mineflayer/dist/src/protocol.js").as_uri()
    # Covers Python/JS mismatches: integer floats, negative zero, exponent formatting,
    # fixed-point cutoff, astral vs BMP UTF-16 property ordering, controls and Unicode.
    value = {"numbers": [1.0, -0.0, 1e-7, 1e-6, 1e20, 1e21, 333333333.3333333],
             "\U0001f600": "astral", "\ue000": "bmp", "text": "\n\t\u00e9"}
    script = f"import {{canonical,digest}} from {json.dumps(module)};" + (
        "let input=''; for await (const s of process.stdin) input+=s;"
        "const value=JSON.parse(input); console.log(JSON.stringify({canonical:canonical(value),digest:digest(value)}));")
    result = subprocess.run([shutil.which("node"), "--input-type=module", "-e", script],
        input=json.dumps(value), capture_output=True, text=True, encoding="utf-8", timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"canonical": canonical(value).decode(), "digest": digest(value)}


@pytest.mark.parametrize("value", [float("nan"), float("inf"), "\ud800", 2**53])
def test_invalid_canonical_values_rejected(value):
    with pytest.raises((ValueError, UnicodeError)):
        canonical(value)
