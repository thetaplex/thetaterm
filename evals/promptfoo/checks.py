"""Print a promptfoo config: configs/<config>.yaml's enabled models on
tests/<tests>.yaml's queries.

checks: static runs each query's own assertions, judge only the enabled judges
in configs/judges.yaml, both runs all of them. promptfoo merges two -c configs,
but adds an empty prompt that runs every query twice, and it has no switch to
skip a model, so the config is built here.
"""

import sys
from pathlib import Path

import yaml

from thetaterm.agent import environment

HERE = Path(__file__).resolve().parent


def load(path: str):
    return yaml.safe_load((HERE / path).read_text())


def enabled(entries: list[dict], what: str) -> list[dict]:
    """The entries switched on, without the switch, which promptfoo doesn't know."""
    for entry in entries:
        if not isinstance(entry.get("enabled"), bool):
            name = entry.get("label") or entry.get("name")
            raise SystemExit(f"{what} {name}: enabled must be true or false")
    on = [
        {k: v for k, v in e.items() if k != "enabled"} for e in entries if e["enabled"]
    ]
    if not on:
        raise SystemExit(f"no {what} enabled")
    return on


def grader(judge: dict) -> dict:
    """The judge as a promptfoo provider: openrouter + some/model -> openrouter:some/model."""
    for key in ("provider", "model"):
        if not judge.get(key):
            raise SystemExit(f"judge {judge.get('name')}: no {key}")
    return {
        "id": f"{judge['provider']}:{judge['model']}",
        "config": judge.get("config", {}),
    }


def build(config_name: str, tests_name: str, checks: str) -> dict:
    if checks not in {"static", "judge", "both"}:
        raise SystemExit(f"checks: static, judge or both, not {checks}")
    config = load(f"configs/{config_name}.yaml")
    tests = load(f"tests/{tests_name}.yaml")
    config["providers"] = enabled(config["providers"], "model")
    # paths in the config are relative to it; the built one is written elsewhere
    for provider in config["providers"]:
        path = provider["id"].removeprefix("file://")
        provider["id"] = f"file://{(HERE / 'configs' / path).resolve()}"
    if checks != "static":
        judges = load("configs/judges.yaml")
        rubrics = [
            {
                "type": "llm-rubric",
                "value": judges["rubric"],
                "provider": grader(judge),
                "metric": judge["name"],
            }
            for judge in enabled(judges["judges"], "judge")
        ]
        # without it the judge assumes Linux: it passed `ps --sort` on macOS
        system = {"system": environment()}
        if checks == "judge":
            config["defaultTest"] = {"vars": system, "assert": rubrics}
            tests = [{k: v for k, v in t.items() if k != "assert"} for t in tests]
        else:
            config["defaultTest"]["vars"] = system
            config["defaultTest"]["assert"] += rubrics
    config["tests"] = tests
    return config


if __name__ == "__main__":
    yaml.safe_dump(build(*sys.argv[1:]), sys.stdout, sort_keys=False)
