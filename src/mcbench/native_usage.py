"""Strict observed native usage attribution; totals are never added twice."""

from .storage import require

POLICY = "native-responses-cache-write-attribution/1"
COUNTERS = {"input_tokens", "output_tokens", "cached_tokens", "cache_write_tokens"}


def validate_no_hosted_usage(value):
    """Accept only absent usage or the exact observed all-zero native shape."""
    if value is None or value == {}:
        return
    zero = {"image_gen": {"input_tokens": 0, "input_tokens_details": {"image_tokens": 0, "text_tokens": 0},
            "output_tokens": 0, "output_tokens_details": {"image_tokens": 0, "text_tokens": 0}, "total_tokens": 0},
            "web_search": {"num_requests": 0}}
    def exact(actual, expected):
        if isinstance(expected, dict):
            return (isinstance(actual, dict) and set(actual) == set(expected) and
                    all(exact(actual[k], v) for k, v in expected.items()))
        return type(actual) is int and actual == 0
    require(exact(value, zero), "HOSTED_TOOL_USAGE_UNSUPPORTED")


def validate_attribution(value, totals):
    from .inference_transport import count
    require(isinstance(value, dict) and set(value) == {"items"} and
            isinstance(value["items"], dict) and 0 < len(value["items"]) <= 4096,
            "USAGE_ATTRIBUTION_UNSUPPORTED")
    summed = dict.fromkeys(COUNTERS, 0)
    for key, item in value["items"].items():
        require(isinstance(key, str) and 0 < len(key) <= 256 and
                isinstance(item, dict) and set(item) in (COUNTERS, COUNTERS | {"content"}),
                "USAGE_ATTRIBUTION_UNSUPPORTED")
        fields = {k: count(item[k]) for k in COUNTERS}
        require(fields["cached_tokens"] + fields["cache_write_tokens"] <= fields["input_tokens"],
                "USAGE_TOTAL_MISMATCH")
        if "content" in item:
            require(isinstance(item["content"], list) and 0 < len(item["content"]) <= 4096,
                    "USAGE_ATTRIBUTION_UNSUPPORTED")
            parts = dict.fromkeys(COUNTERS, 0)
            for part in item["content"]:
                require(isinstance(part, dict) and set(part) == COUNTERS, "USAGE_ATTRIBUTION_UNSUPPORTED")
                for field in COUNTERS:
                    parts[field] += count(part[field])
                require(part["cached_tokens"] + part["cache_write_tokens"] <= part["input_tokens"],
                        "USAGE_TOTAL_MISMATCH")
            require(parts == fields, "USAGE_ATTRIBUTION_TOTAL_MISMATCH")
        for field in COUNTERS:
            summed[field] += fields[field]
    require(summed == totals, "USAGE_ATTRIBUTION_TOTAL_MISMATCH")
