import runpy
from pathlib import Path

build = runpy.run_path(str(Path(__file__).parent.parent / "evals/promptfoo/checks.py"))[
    "build"
]


def kinds(config):
    defaults = [a["type"] for a in config["defaultTest"]["assert"]]
    own = {a["type"] for t in config["tests"] for a in t.get("assert", [])}
    return defaults, own


def test_static_keeps_assertions_without_the_judge():
    defaults, own = kinds(build("local", "tests", "static"))
    assert "llm-rubric" not in defaults and own


def test_judge_drops_the_static_assertions():
    defaults, own = kinds(build("local", "tests", "judge"))
    assert defaults == ["llm-rubric"] and not own


def test_both_keeps_all():
    config = build("local", "tests", "both")
    defaults, own = kinds(config)
    assert "llm-rubric" in defaults and "not-contains" in defaults and own
    assert config["providers"][0]["id"].startswith("file:///")


def test_the_judge_knows_the_system():
    for checks in ("judge", "both"):
        assert build("local", "tests", checks)["defaultTest"]["vars"]["system"]
