"""Owned local/URL media targets for actual native code-mode conformance.

No real media, account files or third-party endpoints are used. Output helpers
are a separate surface from the disabled view_image tool.
"""

import base64
import hashlib
import json
import os
import struct
import zlib

from mcbench.storage import canonical
from native_runtime_boundary import ACTORS, RuntimeBoundaryCanaries

MEDIA_DENIALS = {
    "image_path": "Tool call failed: invalid image output. Pass a base64 data URI instead",
    "image_file": "Tool call failed: invalid image output. Pass a base64 data URI instead",
    "image_http": "Tool call failed: remote image URLs are not supported in tool outputs. Pass a base64 data URI instead",
    "generated_image_http": "Tool call failed: remote image URLs are not supported in tool outputs. Pass a base64 data URI instead",
    "audio_path": "Tool call failed: invalid audio output. Pass a base64 data URI instead",
    "audio_http": "Tool call failed: invalid audio output. Pass a base64 data URI instead",
}


def tiny_png(rgb):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack(
            '>I', zlib.crc32(kind + data) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(b'\0' + rgb)) + chunk(b'IEND', b''))


PUBLIC_PNG = "data:image/png;base64," + base64.b64encode(tiny_png(b'\x11\x22\x33')).decode()


def inspect_output_boundary(outputs):
    """Strictly review captured tool results, including the actual image blocks.

    Request admission and native caller provenance are verified by the separate
    audit. Text saying image() returned does not establish the positive control.
    """
    unique, consistent = {}, True
    for item in outputs:
        if not isinstance(item, dict) or item.get("native_agent") not in ACTORS or not isinstance(
                item.get("call_id"), str) or not item["call_id"]:
            consistent = False
            continue
        key = (item["native_agent"], item["call_id"])
        if key in unique and canonical(unique[key]) != canonical(item):
            consistent = False
        unique[key] = item
    probes, images = {}, []
    for item in unique.values():
        output = item.get("output")
        # Existing broker calls may return a JSON string rather than content.
        if isinstance(output, str):
            continue
        if not isinstance(output, list):
            consistent = False
            continue
        for chunk in output:
            if not isinstance(chunk, dict):
                consistent = False
                continue
            if chunk.get("type") == "input_image":
                images.append((item["native_agent"], chunk))
            elif chunk.get("type") != "input_text":
                consistent = False
            try:
                value = json.loads(chunk.get("text", ""))
            except (TypeError, ValueError):
                continue
            if isinstance(value, dict) and str(value.get("probe", "")).startswith("output_boundary_"):
                probes.setdefault(value["probe"], []).append((item["native_agent"], value))

    def both(name, field, expected):
        rows = probes.get("output_boundary_" + name, [])
        return len(rows) == 2 and {actor for actor, _ in rows} == ACTORS and all(
            set(value) == {"probe", field} and value[field] == expected for _, value in rows)

    expected_names = {"output_boundary_" + name for name in (*MEDIA_DENIALS, "globals", "public_data_image")}
    checks = {
        "output_capture_consistent": consistent and set(probes) == expected_names,
        "output_helpers_present": both("globals", "result", dict.fromkeys(
            ("image", "audio", "generatedImage", "notify"), "function")),
        "output_public_image_returned": both("public_data_image", "result", "returned"),
        "output_exact_public_image_per_actor": len(images) == 2 and {actor for actor, _ in images} == ACTORS
        and all(chunk == {"type": "input_image", "image_url": PUBLIC_PNG} for _, chunk in images),
    }
    checks.update({"output_denied_" + name: both(name, "error", error)
                   for name, error in MEDIA_DENIALS.items()})
    return {"checks": checks, "probes": probes, "images": images}


class OutputBoundaryCanaries(RuntimeBoundaryCanaries):
    def __init__(self, output, **kwargs):
        super().__init__(output, **kwargs)
        self.private_png = output / "owned-private-pixel.png"
        self.private_png.write_bytes(tiny_png(os.urandom(3)))
        self.private_png_digest = hashlib.sha256(self.private_png.read_bytes()).hexdigest()
        self.public_png = PUBLIC_PNG

    def code(self, *, agent="/root"):
        script = super().code(agent=agent)
        cases = {
            "globals": "Object.fromEntries(['image','audio','generatedImage','notify'].map(k=>[k,typeof globalThis[k]]))",
            "public_data_image": "(()=>{image(" + json.dumps(self.public_png) + ");return 'returned';})()",
            "image_path": "(()=>{image(" + json.dumps(str(self.private_png)) + ");return 'returned';})()",
            "image_file": "(()=>{image(" + json.dumps(self.private_png.as_uri()) + ");return 'returned';})()",
            "image_http": "(()=>{image({image_url:" + json.dumps(self.url + '/unapproved-image.png') + "});return 'returned';})()",
            "generated_image_http": "(()=>{generatedImage({image_url:" + json.dumps(self.url + '/unapproved-generated.png') + "});return 'returned';})()",
            "audio_path": "(()=>{audio(" + json.dumps(str(self.protected)) + ");return 'returned';})()",
            "audio_http": "(()=>{audio({audio_url:" + json.dumps(self.url + '/unapproved-audio.wav') + "});return 'returned';})()",
        }
        for name, expression in cases.items():
            label = json.dumps("output_boundary_" + name)
            script += "\ntry { text({probe:" + label + ",result:await (" + expression + (
                ")}); } catch(e) { text({probe:" + label + ",error:String(e)}); }")
        return script

    def report(self, direct_calls, **kwargs):
        result = super().report(direct_calls, **kwargs)
        result["output_surface"] = {
            "status": "not_run", "reason": "independent captured-output review required",
            "private_png_sha256": self.private_png_digest, "public_png": self.public_png,
        }
        result["checks"].update({
            "output_surface_independently_reviewed": False,
            "output_private_png_unchanged": self.private_png.is_file() and
                hashlib.sha256(self.private_png.read_bytes()).hexdigest() == self.private_png_digest,
        })
        return result
