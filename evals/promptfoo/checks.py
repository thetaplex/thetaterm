"""Print a promptfoo config: <config>.yaml's models on <tests>.yaml's queries.

checks: static runs each query's own assertions, judge only judge.yaml's model,
both runs all of them. promptfoo merges two -c configs, but adds an empty
prompt that runs every query twice, so the config is built here.
"""

import sys
from pathlib import Path

import yaml

from thetaterm.agent import environment

HERE = Path(__file__).resolve().parent


def load(name: str):
    return yaml.safe_load((HERE / f"{name}.yaml").read_text())


def build(config_name: str, tests_name: str, checks: str) -> dict:
    if checks not in {"static", "judge", "both"}:
        raise SystemExit(f"checks: static, judge or both, not {checks}")
    config, tests = load(config_name), load(tests_name)
    judge = load("judge")
    # without it the judge assumes Linux: it passed `ps --sort` on macOS
    judge["vars"] = {"system": environment()}
    # paths in the config are relative to it; the built one is written to a temporary file
    for provider in config["providers"]:
        provider["id"] = provider["id"].replace("file://", f"file://{HERE}/")
    if checks == "judge":
        config["defaultTest"] = judge
        tests = [{k: v for k, v in t.items() if k != "assert"} for t in tests]
    elif checks == "both":
        config["defaultTest"]["options"] = judge["options"]
        config["defaultTest"]["vars"] = judge["vars"]
        config["defaultTest"]["assert"] += judge["assert"]
    config["tests"] = tests
    return config


if __name__ == "__main__":
    yaml.safe_dump(build(*sys.argv[1:]), sys.stdout, sort_keys=False)
