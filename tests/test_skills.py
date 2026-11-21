import sys
from pathlib import Path

from thetaterm.agent import Agent
from thetaterm.skills import format_skills, load_skills, match_skills, parse_skill

SAMPLE_SKILL = """---
name: skill_bsd_sed_inplace
description: Edit files in place across BSD and GNU sed
metadata:
  category: text
  base_model: gemma4:e4b-mlx
  trigger_keywords: [replace, in place, sed, substitute]
  programs: [sed]
---

# Domain Knowledge
BSD sed on macOS requires an explicit empty backup suffix after -i.

# Step-by-Step
1. Check whether userland is BSD or GNU.
2. On BSD/macOS use `sed -i ''`, on GNU use `sed -i`.

# Feedback / Lessons
- Rule: Never pass bare `-i` on macOS.
"""


def test_parse_skill_extracts_frontmatter_and_body():
    skill = parse_skill(SAMPLE_SKILL)
    assert skill.name == "skill_bsd_sed_inplace"
    assert skill.category == "text"
    assert skill.base_model == "gemma4:e4b-mlx"
    assert "in place" in skill.trigger_keywords
    assert skill.programs == ("sed",)
    assert "# Domain Knowledge" in skill.body
    assert "---" not in skill.body


def test_match_skills_prefers_program_and_keyword_overlap():
    sed_skill = parse_skill(SAMPLE_SKILL)
    git_skill = parse_skill(
        "---\nname: skill_git_merged\ndescription: Delete merged git branches\n"
        "metadata:\n  category: git\n  trigger_keywords: [branch, merged, delete]\n"
        "  programs: [git]\n---\n\n# Domain Knowledge\nExclude main.\n"
    )
    matched = match_skills(
        "replace foo with bar in notes.txt in place", ["sed"], [git_skill, sed_skill]
    )
    assert [s.name for s in matched] == ["skill_bsd_sed_inplace"]
    assert match_skills("show disk usage", ["du"], [git_skill, sed_skill]) == []
    # umbrella program `git` alone must not fire an unrelated git skill
    assert match_skills("start a git bisect", ["git"], [git_skill, sed_skill]) == []
    # dotted extensions like `tar.gz` match inside filenames like `logs.tar.gz`
    tar_skill = parse_skill(
        "---\nname: skill_tar\nmetadata:\n  trigger_keywords: [tar.gz]\n"
        "  programs: [tar]\n---\n\n# Domain Knowledge\nUse tar -czf.\n"
    )
    assert [
        s.name
        for s in match_skills("compress logs into logs.tar.gz", ["tar"], [tar_skill])
    ] == ["skill_tar"]


def test_format_skills_loads_from_dir_and_respects_budget(tmp_path: Path):
    skill_dir = tmp_path / "text" / "skill_bsd_sed_inplace"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL, encoding="utf-8")

    loaded = load_skills(tmp_path)
    assert len(loaded) == 1
    out = format_skills(
        "replace foo in place", ["sed"], skills_dir=tmp_path, budget=180
    )
    assert "skill_bsd_sed_inplace" in out
    assert len(out) <= 180


def test_agent_injects_matching_skill_unless_disabled(tmp_path: Path):
    skill_dir = tmp_path / "text" / "skill_bsd_sed_inplace"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(SAMPLE_SKILL, encoding="utf-8")

    prompts: list[str] = []

    def make_agent(**kwargs):
        a = Agent("gemma4:e4b-mlx", "http://localhost:11434/v1", **kwargs)
        a.choose = lambda q: ["sed"]  # type: ignore[method-assign]
        a.ask = lambda p, max_tokens=None: prompts.append(p) or "sed -i '' 's/a/b/' x"  # type: ignore[method-assign]
        return a

    make_agent(skills_dir=tmp_path).generate("replace a with b in place")
    assert "<skill>" in prompts[-1]
    assert "skill_bsd_sed_inplace" in prompts[-1]

    make_agent(skills_dir=tmp_path, use_skills=False).generate(
        "replace a with b in place"
    )
    assert "<skill>" not in prompts[-1]


def test_upskill_extract_and_check_assertions():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from evals.upskill import check_assertion, extract_skill_md

    raw = f"Analysis...\n===BEGIN_FILE: SKILL.md===\n{SAMPLE_SKILL}\n===END_FILE: SKILL.md===\nDone."
    extracted = extract_skill_md(raw)
    assert extracted.startswith("---\nname: skill_bsd_sed_inplace")

    assert check_assertion(
        {"type": "regex", "value": r"\bsed\b"}, "sed -i '' 's/a/b/' f"
    )[0]
    assert not check_assertion({"type": "not-regex", "value": r"\brm\b"}, "rm -rf x")[0]
    assert check_assertion({"type": "contains", "value": "5"}, "head -n 5")[0]
    assert check_assertion(
        {"type": "python", "value": "return 'foo' in output"}, "echo foo"
    )[0]


def test_upskill_model_resolution_and_failures_jsonl(tmp_path: Path, monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from types import SimpleNamespace

    from evals.upskill import load_failures_log, resolve_models, save_failures_log

    monkeypatch.setenv("THETATERM_UPSKILL_STUDENT", "bonsai-2:9b")
    monkeypatch.setenv("THETATERM_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("THETATERM_UPSKILL_TEACHER_BACKEND", "openai")
    monkeypatch.setenv("THETATERM_UPSKILL_TEACHER", "qwen3.8:27b-mlx")
    monkeypatch.setenv(
        "THETATERM_UPSKILL_TEACHER_BASE_URL", "http://localhost:11434/v1"
    )

    empty_args = SimpleNamespace(
        student=None,
        base_url=None,
        teacher_backend=None,
        teacher=None,
        teacher_base_url=None,
        teacher_api_key=None,
    )
    student, base_url, teacher = resolve_models(empty_args)
    assert student == "bonsai-2:9b"
    assert base_url == "http://localhost:11434/v1"
    assert teacher.backend == "openai"
    assert teacher.model == "qwen3.8:27b-mlx"
    assert teacher.base_url == "http://localhost:11434/v1"

    # CLI flags override env vars
    override_args = SimpleNamespace(
        student="gemma4:e4b-mlx",
        base_url="http://localhost:8080/v1",
        teacher_backend="openrouter",
        teacher="anthropic/claude-opus-4",
        teacher_base_url=None,
        teacher_api_key="sk-test",
    )
    student, base_url, teacher = resolve_models(override_args)
    assert student == "gemma4:e4b-mlx"
    assert base_url == "http://localhost:8080/v1"
    assert teacher.backend == "openrouter"
    assert teacher.model == "anthropic/claude-opus-4"
    assert teacher.api_key == "sk-test"

    flog = tmp_path / "failures.jsonl"
    save_failures_log(flog, [{"query": "q1", "resolved": False}])
    loaded = load_failures_log(flog)
    assert loaded == [{"query": "q1", "resolved": False}]


def test_upskill_keeps_teacher_names_in_the_store_and_yes_needs_a_local_teacher():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from evals.upskill import TeacherConfig, _path_part, _teacher_is_local

    assert _path_part("../../etc", "x") == "etc"
    assert _path_part("..", "x") == "x"
    assert _path_part("skill_tar_gzip", "x") == "skill_tar_gzip"

    assert _teacher_is_local(TeacherConfig("openai", "m", "http://localhost:11434/v1"))
    assert not _teacher_is_local(
        TeacherConfig("openai", "m", "https://api.example.com/v1")
    )
    assert not _teacher_is_local(TeacherConfig("claude", "opus"))
    assert not _teacher_is_local(TeacherConfig("openrouter", "m"))


def test_upskill_brew_prompt_asks_to_revise_a_skill_that_already_matched():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from evals.upskill import EvalResult, build_brew_prompt

    fail = EvalResult("q", False, "cmd", "", ["regex failed"], ["sed"])
    assert "REVISE" not in build_brew_prompt(fail, "m", "env", "")
    prompt = build_brew_prompt(fail, "m", "env", "", SAMPLE_SKILL)
    assert "REVISE" in prompt and "skill_bsd_sed_inplace" in prompt
