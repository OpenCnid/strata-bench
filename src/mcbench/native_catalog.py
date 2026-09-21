"""Pin native startup metadata without changing the selected model's contents.

This is an operator snapshot, not pricing, a provider hard limit, or proof of
immutable server-side model identity. Native execution still needs conformance.
"""

import hashlib
from pathlib import Path

from .inference_transport import strict_json
from .storage import canonical, reject_links, require

POLICY = "native-selected-model-startup-catalog/1"
MAX_BYTES = 2 * 1024 * 1024


def select_catalog(raw, expected_sha256, model):
    require(isinstance(raw, bytes) and 0 < len(raw) <= MAX_BYTES, "MODEL_CATALOG_SIZE")
    require(hashlib.sha256(raw).hexdigest() == expected_sha256, "MODEL_CATALOG_CHANGED")
    value = strict_json(raw)
    require(isinstance(value, dict) and set(value) == {"models"} and
            isinstance(value["models"], list) and 0 < len(value["models"]) <= 128,
            "MODEL_CATALOG_SHAPE")
    rows = value["models"]
    require(all(isinstance(row, dict) and isinstance(row.get("slug"), str) for row in rows),
            "MODEL_CATALOG_SHAPE")
    slugs = [row["slug"] for row in rows]
    require(len(set(slugs)) == len(slugs) and model in slugs, "MODEL_CATALOG_SELECTION")
    # Preserve every provider field of the selected model, including instructions,
    # tool flags and wire preferences. Do not guess defaults or rewrite limits.
    selected = next(row for row in rows if row["slug"] == model)
    return canonical({"models": [selected]})


def install_catalog(source, target, *, expected_sha256, model):
    source, target = Path(source), Path(target)
    reject_links(source)
    reject_links(target)
    require(source.is_absolute() and target.is_absolute() and not target.exists(),
            "MODEL_CATALOG_FRESH_PATH")
    require(source.stat().st_size <= MAX_BYTES, "MODEL_CATALOG_SIZE")
    raw = select_catalog(source.read_bytes(), expected_sha256, model)
    with target.open("xb") as stream:
        stream.write(raw)
    return {"schema": "strata/NativeModelCatalogPin/1", "policy": POLICY, "model": model,
            "source_sha256": expected_sha256, "selected_sha256": hashlib.sha256(raw).hexdigest(),
            "config_overrides": {"model_catalog_json": str(target)},
            "static_files": [str(target)], "production_qualified": False}
