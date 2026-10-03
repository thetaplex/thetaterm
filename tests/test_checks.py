import copy
import importlib.util
from pathlib import Path

import pytest

path = Path(__file__).parent.parent / "evals/promptfoo/checks.py"
spec = importlib.util.spec_from_file_location("checks", path)
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
build = checks.build


def kinds(config):
    defaults = [a["type"] for a in config["defaultTest"]["assert"]]
    own = {a["type"] for t in config["tests"] for a in t.get("assert", [])}
    return defaults, own


def test_static_keeps_assertions_without_the_judge():
    defaults, own = kinds(build("local", "tests", "static"))
    assert "llm-rubric" not in defaults and own


def test_judge_drops_the_static_assertions():
    defaults, own = kinds(build("local", "tests", "judge"))
    assert set(defaults) == {"llm-rubric"} and not own


def test_both_keeps_all():
    config = build("local", "git", "both")
    defaults, own = kinds(config)
    assert "llm-rubric" in defaults and "not-contains" in defaults and own
    assert config["providers"][0]["id"].startswith("file:///")
    assert Path(config["providers"][0]["id"].removeprefix("file://")).is_file()


def test_the_judge_knows_the_system():
    for mode in ("judge", "both"):
        assert build("local", "tests", mode)["defaultTest"]["vars"]["system"]


def fake_configs(monkeypatch, models, judges):
    real = checks.load
    files = {
        "configs/local.yaml": {"providers": models, "defaultTest": {"assert": []}},
        "configs/judges.yaml": {"rubric": "does {{query}}", "judges": judges},
    }
    # a fresh copy each time, like reading the file: build() changes what it loads
    monkeypatch.setattr(
        checks, "load", lambda p: copy.deepcopy(files[p]) if p in files else real(p)
    )


def model(label, on):
    return {"id": "file://../provider.py", "label": label, "enabled": on}


def judge(name, on):
    return {"name": name, "enabled": on, "provider": {"id": f"openrouter:{name}"}}


def test_disabled_models_and_judges_are_left_out(monkeypatch):
    fake_configs(
        monkeypatch,
        [model("a", True), model("b", False)],
        [judge("x", True), judge("y", False), judge("z", True)],
    )
    config = build("local", "tests", "judge")
    assert [p["label"] for p in config["providers"]] == ["a"]
    assert "enabled" not in config["providers"][0]
    rubrics = config["defaultTest"]["assert"]
    assert [r["metric"] for r in rubrics] == ["x", "z"]
    assert [r["provider"]["id"] for r in rubrics] == ["openrouter:x", "openrouter:z"]


def test_nothing_enabled_or_no_switch_is_an_error(monkeypatch):
    fake_configs(monkeypatch, [model("a", True)], [judge("x", False)])
    with pytest.raises(SystemExit, match="no judge enabled"):
        build("local", "tests", "judge")
    assert build("local", "tests", "static")  # judges aren't read without a judge
    fake_configs(monkeypatch, [model("a", False)], [])
    with pytest.raises(SystemExit, match="no model enabled"):
        build("local", "tests", "static")
    fake_configs(monkeypatch, [{"id": "file://p.py", "label": "a"}], [])
    with pytest.raises(SystemExit, match="a: enabled must be true or false"):
        build("local", "tests", "static")
