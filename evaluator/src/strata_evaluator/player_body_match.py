"""Private whole save-format comparisons; no transient-state or admission claim."""

import hashlib
import re
import struct
import uuid

from mcbench.storage import require
from .saved_blocks import NbtReader, Tag, field

POLICY = "private-typed-player-save-format-match/1"
MAX_COMPARISON_BYTES = 8 * 1024**2
MAX_DIAGNOSTIC_FIELDS = 256


def _diagnostic_name(name):
    # Diagnostics are bounded ASCII; raw NBT remains the complete authority.
    shown = name.encode("unicode_escape").decode("ascii")
    if len(shown) > 128:
        return shown[:128] + "...#" + hashlib.sha256(name.encode("utf-8", "surrogatepass")).hexdigest()
    return shown


class ExactNbtReader(NbtReader):
    def number(self, fmt):
        # Python float equality merges signed zero and can alter NaN payloads.
        # Keep the original IEEE bits; all other parsing quotas remain inherited.
        if fmt in (">f", ">d"):
            return bytes(self.take(4 if fmt == ">f" else 8))
        return super().number(fmt)


def _string(h, value):
    raw = value.encode("utf-8", "surrogatepass")
    h.update(struct.pack(">I", len(raw)))
    h.update(raw)


def _feed(h, tag):
    kind, value = tag.kind, tag.value
    h.update(bytes([kind]))
    if kind <= 4:
        h.update(struct.pack({1: ">b", 2: ">h", 3: ">i", 4: ">q"}[kind], value))
    elif kind <= 6:
        h.update(value)
    elif kind in (7, 11, 12):
        h.update(struct.pack(">I", len(value)))
        h.update(value)
    elif kind == 8:
        _string(h, value)
    elif kind == 9:
        subtype, children = value
        h.update(bytes([subtype]))
        h.update(struct.pack(">I", len(children)))
        for child in children:
            _feed(h, child)
    else:
        h.update(struct.pack(">I", len(value)))
        # Compound iteration order is not state; list order and tag types are.
        for name in sorted(value):
            _string(h, name)
            _feed(h, value[name])


def body_fingerprint(raw, expected_uuid):
    root = ExactNbtReader(raw).root()
    identity = field(root, "UUID", 11)
    require(len(identity) == 16 and str(uuid.UUID(bytes=bytes(identity))) == expected_uuid,
            "BODY_MATCH_IDENTITY")
    fields = {}
    for name, tag in root.items():
        h = hashlib.sha256()
        _feed(h, tag)
        fields[name] = h.hexdigest()
    h = hashlib.sha256()
    _feed(h, Tag(10, root))
    return {"raw_sha256": hashlib.sha256(raw).hexdigest(), "typed_sha256": h.hexdigest(),
            "fields": fields}


def compare_player_bodies(first, second, roster):
    """Compare complete raw captured bodies already held by the private caller.

    read callbacks return exact raw NBT for the requested UUID, not projections.
    No field allowlist, ignored differences, source rewriting or float tolerance.
    The caller must authenticate producers and retain custody separately.
    """
    require(isinstance(roster, list) and 1 <= len(roster) <= 64
            and all(isinstance(v, str) and re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", v)
                    for v in roster)
            and len(set(roster)) == len(roster), "BODY_MATCH_ROSTER")
    members = {}
    for identity in roster:
        a, b = body_fingerprint(first(identity), identity), body_fingerprint(second(identity), identity)
        names = sorted(set(a["fields"]) | set(b["fields"]))
        changed = [name for name in names if a["fields"].get(name) != b["fields"].get(name)]
        members[identity] = {"first": {k: v for k, v in a.items() if k != "fields"} | {"field_count": len(a["fields"])},
                             "second": {k: v for k, v in b.items() if k != "fields"} | {"field_count": len(b["fields"])},
                             "changed_fields": [_diagnostic_name(n) for n in changed[:MAX_DIAGNOSTIC_FIELDS]],
                             "changed_field_count": len(changed), "diagnostics_truncated": len(changed) > MAX_DIAGNOSTIC_FIELDS,
                             "equal": not changed and a["typed_sha256"] == b["typed_sha256"]}
    return {"schema": "strata/PrivatePlayerBodyComparison/1", "policy": POLICY,
        "visibility": "evaluator", "members": members,
        "save_format_state_equal": all(v["equal"] for v in members.values()),
        "owned_producers_verified": False, "live_initial_state_verified": False,
        "transient_state_verified": False, "native_probe_admission": False}
