"""Private selected Forge config evidence, never a gameplay observation or gate pass."""

import json
import math
from typing import Annotated, Any, Literal

from pydantic import Field, model_validator

from mcbench.contracts import Strict
from mcbench.storage import require

ConfigFile = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_.-]*\.toml$", max_length=128)]
ConfigKey = Annotated[str, Field(pattern=r"^[ -~]{1,128}$")]
ConfigPath = Annotated[list[ConfigKey], Field(min_length=1, max_length=16)]


class ConfigQuery(Strict):
    file_name: ConfigFile
    paths: list[ConfigPath] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def unique(self):
        require(len({tuple(p) for p in self.paths}) == len(self.paths), "TELEMETRY_CONFIG_QUERY")
        return self


def check_value(value, nodes, depth=0):
    nodes[0] += 1
    require(nodes[0] <= 4096 and depth <= 8, "TELEMETRY_CONFIG_QUOTA")
    if type(value) is str:
        require(len(value.encode("utf-8")) <= 4096, "TELEMETRY_CONFIG_QUOTA")
    elif type(value) is bool:
        pass
    elif type(value) is int:
        require(abs(value) <= 9007199254740991, "TELEMETRY_CONFIG_VALUE")
    elif type(value) is float:
        require(math.isfinite(value), "TELEMETRY_CONFIG_VALUE")
    elif type(value) is list:
        require(len(value) <= 4096, "TELEMETRY_CONFIG_QUOTA")
        for item in value:
            check_value(item, nodes, depth + 1)
    else:
        require(False, "TELEMETRY_CONFIG_VALUE")


class ConfigValue(Strict):
    path: ConfigPath
    declared: bool
    present: bool
    value: Any = None

    @model_validator(mode="after")
    def presence(self):
        require(("value" in self.model_fields_set) == self.present, "TELEMETRY_CONFIG_VALUE")
        return self


class ConfigSnapshot(Strict):
    file_name: ConfigFile
    status: Literal["unregistered", "unsupported_spec", "unloaded", "snapshot",
                    "unstable", "quota_exceeded", "unsupported_value", "read_failed"]
    mod_id: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{1,63}$")] | None = None
    config_type: Literal["CLIENT", "COMMON", "SERVER"] | None = None
    consistency: Literal["matching_consecutive_reads"] | None = None
    values: list[ConfigValue] | None = Field(default=None, min_length=1, max_length=32)

    @model_validator(mode="after")
    def shape(self):
        fields = self.model_fields_set
        registered = self.status != "unregistered"
        for field in ("mod_id", "config_type"):
            require((field in fields) == registered and (getattr(self, field) is not None) == registered,
                    "TELEMETRY_CONFIG_SHAPE")
        snapshot = self.status == "snapshot"
        for field in ("consistency", "values"):
            require((field in fields) == snapshot and (getattr(self, field) is not None) == snapshot,
                    "TELEMETRY_CONFIG_SHAPE")
        if snapshot:
            require(len({tuple(v.path) for v in self.values}) == len(self.values), "TELEMETRY_CONFIG_SHAPE")
            nodes = [0]
            for row in self.values:
                if row.present:
                    check_value(row.value, nodes)
        require(len(json.dumps(self.model_dump(exclude_unset=True), ensure_ascii=False,
                               separators=(",", ":")).encode("utf-8")) <= 65536,
                "TELEMETRY_CONFIG_QUOTA")
        return self
