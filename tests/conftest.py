import copy
import json
import re
from pathlib import Path

import pytest

from mcbench.records import AgentConfig, CampaignConfig
from mcbench.storage import CAS, Database, Principal


@pytest.fixture
def example():
    spec = (Path(__file__).resolve().parents[1] / "SPEC.md").read_text(encoding="utf-8")
    records = [json.loads(s) for s in re.findall(r"```json\s*(.*?)```", spec, re.S)]
    by_name = {r["schema"].split("/")[1]: r for r in records}
    return lambda name: copy.deepcopy(by_name[name])


@pytest.fixture
def database(tmp_path):
    database = Database(tmp_path / "operator.sqlite")
    yield database
    database.close()


@pytest.fixture
def cas(database, tmp_path):
    return CAS(database, tmp_path / "objects")


@pytest.fixture
def operator():
    return Principal("operator", "operator")


@pytest.fixture
def configs(example):
    def make(n=1, campaign="c1", admission="queue"):
        c = example("CampaignConfig") | {"is_example": False, "n": n,
            "agent_ids": [f"a{i}" for i in range(1, n + 1)], "campaign_id": campaign,
            "admission": admission}
        agents = [AgentConfig.model_validate(example("AgentConfig") | {"is_example": False,
                  "agent_id": agent, "account_ref": campaign + ":" + agent}) for agent in c["agent_ids"]]
        return CampaignConfig.model_validate(c), agents
    return make
