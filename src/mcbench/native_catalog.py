"""Pin native startup metadata without changing the selected model's contents.

This is an operator snapshot, not pricing, a provider hard limit, or proof of
immutable server-side model identity. Native execution still needs conformance.
"""

import hashlib
from pathlib import Path

from .inference_transport import strict_json
from .storage import canonical, reject_links, require

POLICY = "native-selected-model-startup-catalog/1"
NO_PATCH_POLICY = "native-selected-model-without-apply-patch/1"
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


def install_no_patch_catalog(source, target, *, expected_sha256, model):
    """Explicit capability restriction; preserve all other selected provider fields.

    Native conformance must prove null disables dispatch, not just discovery.
    This is deliberately distinct from the unchanged catalog snapshot policy.
    """
    source, target = Path(source), Path(target)
    reject_links(source)
    reject_links(target)
    require(source.is_absolute() and target.is_absolute() and not target.exists(),
            "MODEL_CATALOG_FRESH_PATH")
    require(source.stat().st_size <= MAX_BYTES, "MODEL_CATALOG_SIZE")
    original = select_catalog(source.read_bytes(), expected_sha256, model)
    value = strict_json(original)
    selected = value["models"][0]
    require(selected.get("apply_patch_tool_type") == "freeform", "MODEL_CATALOG_TOOL_TYPE")
    selected["apply_patch_tool_type"] = None
    raw = canonical(value)
    with target.open("xb") as stream:
        stream.write(raw)
    return {"schema": "strata/NativeModelCatalogRestriction/1", "policy": NO_PATCH_POLICY,
        "model": model, "source_sha256": expected_sha256,
        "original_selected_sha256": hashlib.sha256(original).hexdigest(),
        "selected_sha256": hashlib.sha256(raw).hexdigest(),
        "changed_fields": {"apply_patch_tool_type": {"from": "freeform", "to": None}},
        "config_overrides": {"model_catalog_json": str(target)},
        "static_files": [str(target)], "production_qualified": False}


def require_no_patch_catalog(plan):
    path = plan.config_overrides.get("model_catalog_json")
    require(isinstance(path, str) and Path(path).is_absolute(), "MODEL_CATALOG_REQUIRED")
    path = Path(path)
    reject_links(path)
    require(path.is_file() and path.stat().st_size <= MAX_BYTES, "MODEL_CATALOG_SIZE")
    value = strict_json(path.read_bytes())
    require(isinstance(value, dict) and set(value) == {"models"} and
            isinstance(value["models"], list) and len(value["models"]) == 1,
            "MODEL_CATALOG_SHAPE")
    row = value["models"][0]
    require(isinstance(row, dict) and row.get("slug") == plan.model and
            "apply_patch_tool_type" in row and row["apply_patch_tool_type"] is None,
            "MODEL_CATALOG_TOOL_TYPE")
