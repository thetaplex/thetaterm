"""ThetaTerm-native UpSkill pipeline (Ralph Loop).

Teacher (configurable: Claude CLI, OpenRouter, or any OpenAI-compatible endpoint
including local Ollama) diagnoses failures of a configurable local Student model
running thetaterm's real Agent pipeline, brews HKUDS/Upskill-format SKILL.md
files, and validates them in a closed loop until the student passes without
regressing other queries.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

import yaml
from dotenv import load_dotenv

from thetaterm.agent import Agent, environment, reference
from thetaterm.cli import CONFIG as USER_CONFIG
from thetaterm.cli import DEFAULT_BASE_URL, FAILURES_LOG
from thetaterm.skills import load_skills, match_skills, parse_skill, user_skills_dir

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "evals" / "promptfoo" / "tests"
DEFAULT_SKILLS_OUT = REPO_ROOT / "thetaterm" / "skills"
RUNS_DIR = REPO_ROOT / "evals" / "upskill-runs"

DEFAULT_STUDENT = "gemma4:e4b-mlx"
DEFAULT_CLAUDE_TEACHER = "opus"
DEFAULT_OPENROUTER_TEACHER = "anthropic/claude-opus-4"
DEFAULT_OPENAI_TEACHER = "qwen3.8:27b-mlx"

SKILL_BLOCK_RE = re.compile(
    r"===BEGIN_FILE:\s*SKILL\.md===\s*\n(.*?)\n===END_FILE:\s*SKILL\.md===",
    re.DOTALL,
)
FENCED_SKILL_RE = re.compile(r"```(?:markdown|md)?\s*\n(---\n.*?)```", re.DOTALL)


@dataclass(frozen=True)
class TeacherConfig:
    backend: str
    model: str
    base_url: str = ""
    api_key: str = ""


@dataclass
class EvalResult:
    query: str
    passed: bool
    command: str
    error: str
    failed_assertions: list[str]
    chosen_programs: list[str]


def load_configs() -> None:
    """Load user ~/.config/thetaterm/.env first, then repo .env without overriding."""
    load_dotenv(USER_CONFIG, override=False)
    load_dotenv(REPO_ROOT / ".env", override=False)


def resolve_models(args: argparse.Namespace) -> tuple[str, str, TeacherConfig]:
    """Resolve student + teacher settings: CLI flags > env vars > config files > defaults."""
    student = (
        args.student
        or os.getenv("THETATERM_UPSKILL_STUDENT")
        or os.getenv("THETATERM_MODEL")
        or DEFAULT_STUDENT
    )
    student_base_url = (
        args.base_url or os.getenv("THETATERM_BASE_URL") or DEFAULT_BASE_URL
    )

    backend = (
        args.teacher_backend or os.getenv("THETATERM_UPSKILL_TEACHER_BACKEND") or "auto"
    )
    if backend == "auto":
        if os.getenv("THETATERM_UPSKILL_TEACHER_BASE_URL") or args.teacher_base_url:
            backend = "openai"
        elif shutil.which("claude"):
            backend = "claude"
        else:
            backend = "openrouter"

    default_teacher = {
        "claude": DEFAULT_CLAUDE_TEACHER,
        "openrouter": DEFAULT_OPENROUTER_TEACHER,
        "openai": DEFAULT_OPENAI_TEACHER,
    }.get(backend, DEFAULT_CLAUDE_TEACHER)

    teacher_model = (
        args.teacher or os.getenv("THETATERM_UPSKILL_TEACHER") or default_teacher
    )
    teacher_base_url = (
        args.teacher_base_url
        or os.getenv("THETATERM_UPSKILL_TEACHER_BASE_URL")
        or (DEFAULT_BASE_URL if backend == "openai" else "")
    )
    teacher_api_key = (
        args.teacher_api_key
        or os.getenv("THETATERM_UPSKILL_TEACHER_API_KEY")
        or (os.getenv("OPENROUTER_API_KEY", "") if backend == "openrouter" else "")
    )
    return (
        student,
        student_base_url,
        TeacherConfig(
            backend=backend,
            model=teacher_model,
            base_url=teacher_base_url,
            api_key=teacher_api_key,
        ),
    )


def check_assertion(assertion: dict, output: str) -> tuple[bool, str]:
    """Evaluate a single promptfoo assertion against a generated command."""
    atype = assertion["type"]
    val = assertion["value"]

    if atype == "regex":
        ok = bool(re.search(val, output))
        return ok, "" if ok else f"regex did not match: {val}"
    if atype == "not-regex":
        ok = not bool(re.search(val, output))
        return ok, "" if ok else f"not-regex matched: {val}"
    if atype == "contains":
        ok = str(val) in output
        return ok, "" if ok else f"missing substring: {val}"
    if atype == "not-contains":
        ok = str(val) not in output
        return ok, "" if ok else f"forbidden substring present: {val}"
    if atype == "python":
        indented = "\n".join(f"    {line}" for line in str(val).splitlines())
        src = f"def _check(output):\n{indented}\n"
        ns: dict = {}
        exec(src, ns)  # noqa: S102 trusted in-repo promptfoo test assertions
        ok = bool(ns["_check"](output))
        return ok, "" if ok else f"python assertion returned False:\n{val.strip()}"
    return False, f"unsupported assertion type: {atype}"


def evaluate_case(
    case: dict,
    student: str,
    base_url: str,
    api_key: str | None = None,
    skills_dir: Path | None = None,
    use_skills: bool = True,
) -> EvalResult:
    """Run thetaterm's real Agent.generate on one test case and check assertions."""
    query = case["vars"]["query"]
    assertions = list(case.get("assert", []))
    assertions.append({"type": "not-contains", "value": "/path/to"})

    agent = Agent(
        student,
        base_url,
        api_key=api_key,
        thinking=False,
        skills_dir=skills_dir,
        use_skills=use_skills,
    )
    chosen: list[str] = []
    orig_choose = agent.choose

    def capture_choose(q: str) -> list[str]:
        res = orig_choose(q)
        chosen.extend(res)
        return res

    agent.choose = capture_choose  # type: ignore[method-assign]

    try:
        command = agent.generate(query)
    except RuntimeError as e:
        return EvalResult(
            query=query,
            passed=False,
            command="",
            error=str(e),
            failed_assertions=[f"agent.generate raised: {e}"],
            chosen_programs=chosen,
        )

    failures = []
    for assertion in assertions:
        ok, reason = check_assertion(assertion, command)
        if not ok:
            failures.append(reason)
    return EvalResult(
        query=query,
        passed=not failures,
        command=command,
        error="",
        failed_assertions=failures,
        chosen_programs=chosen,
    )


def extract_skill_md(text: str) -> str:
    """Extract SKILL.md content from teacher output."""
    match = SKILL_BLOCK_RE.search(text)
    if match:
        return match.group(1).strip() + "\n"
    fenced = FENCED_SKILL_RE.search(text)
    if fenced:
        return fenced.group(1).strip() + "\n"
    if text.lstrip().startswith("---\n"):
        return text.strip() + "\n"
    raise ValueError("teacher response did not contain a SKILL.md block")


def _call_openai_chat(
    url: str, model: str, prompt: str, api_key: str, timeout: int
) -> str:
    if urlsplit(url).scheme not in {"http", "https"}:
        raise ValueError(f"{url}: not an http(s) URL")
    endpoint = url.rstrip("/") + "/chat/completions"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": 2000,
    }
    req = urllib.request.Request(  # noqa: S310 scheme checked above
        endpoint, json.dumps(body).encode(), headers
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 scheme checked above
            data = json.load(resp)
    except (urllib.error.HTTPError, OSError, ValueError) as e:
        raise RuntimeError(f"teacher endpoint {endpoint} error: {e}") from e
    try:
        return data["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"unexpected teacher reply: {str(data)[:200]}") from e


def call_teacher(prompt: str, teacher: TeacherConfig, timeout: int = 300) -> str:
    """Invoke the configured Teacher model (claude CLI, openrouter, or openai-compatible)."""
    if teacher.backend == "claude":
        claude_bin = shutil.which("claude")
        if not claude_bin:
            raise RuntimeError(
                "`claude` CLI not found on PATH; set --teacher-backend openrouter or openai"
            )
        cmd = [
            claude_bin,
            "-p",
            "--model",
            teacher.model,
            "--output-format",
            "text",
            "--tools",
            "",
        ]
        result = subprocess.run(  # noqa: S603 argv list, no shell
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()[:400]
            raise RuntimeError(f"claude teacher exited {result.returncode}: {detail}")
        return result.stdout

    if teacher.backend == "openrouter":
        if not teacher.api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY (or THETATERM_UPSKILL_TEACHER_API_KEY) is not set"
            )
        return _call_openai_chat(
            "https://openrouter.ai/api/v1",
            teacher.model,
            prompt,
            teacher.api_key,
            timeout,
        )

    if teacher.backend == "openai":
        base_url = teacher.base_url or DEFAULT_BASE_URL
        return _call_openai_chat(
            base_url, teacher.model, prompt, teacher.api_key, timeout
        )

    raise ValueError(f"unknown teacher backend: {teacher.backend}")


def teacher_verify_command(
    query: str,
    command: str,
    env_str: str,
    hint: str,
    teacher: TeacherConfig,
) -> tuple[bool, str]:
    """Ask the teacher to judge a free-form command when no static assertion exists."""
    prompt = (
        f"You are judging a single shell command for this system: {env_str}.\n"
        f"Task: {query}\n"
        f"Candidate command: `{command}`\n"
        + (f"User note / expected behavior: {hint}\n" if hint else "")
        + "\nPass it ONLY if running it on this system does the exact task safely "
        "with valid flags for this OS and no placeholders.\n"
        "Reply on the first line with `PASS` or `FAIL: <short reason>`."
    )
    reply = call_teacher(prompt, teacher, timeout=120).strip()
    first_line = next((ln.strip() for ln in reply.splitlines() if ln.strip()), "")
    if first_line.upper().startswith("PASS"):
        return True, ""
    return False, first_line or "teacher rejected candidate command"


def build_brew_prompt(
    failure: EvalResult,
    student: str,
    env_str: str,
    ref_excerpts: str,
    existing_skills: str = "",
) -> str:
    if existing_skills:
        task = f"""Existing skills, also shown to the Student, that did NOT prevent this failure:
{existing_skills}

Your task:
If one of the existing skills covers this class of query, REVISE that skill: keep its exact `name` and `category` so it replaces the old file, keep what still applies, and fix what let the Student fail. Only if none covers it, brew a new skill with a new name."""
    else:
        task = "Your task:"
    return f"""You are the Teacher model in an UpSkill (AgentBrew) Ralph Loop for ThetaTerm (`tterm`).
ThetaTerm translates plain English into one shell command using a small local Student model (`{student}`).

The Student model FAILED on this system:
- Environment: {env_str}
- Query: {failure.query}
- Chosen programs: {failure.chosen_programs or ["(none)"]}
- Student command: `{failure.command or "(none — raised error)"}`
- Failure details:
{chr(10).join(f"  - {r}" for r in failure.failed_assertions)}

Existing reference already shown to the Student:
{ref_excerpts or "(none)"}

{task}
Brew a compact, generalizable HKUDS/Upskill-format `SKILL.md` that teaches `{student}` how to avoid this class of shell mistakes reliably (NOT hardcoded only to this single filename/number, but covering the underlying shell/OS pattern).

Requirements for `SKILL.md`:
1. Keep the body concise (<= 1100 characters) so a small local model follows every rule.
2. Include YAML frontmatter with:
   - `name`: lowercase slug starting with `skill_`
   - `description`: one concise line
   - `category`: one of `files`, `text`, `git`, `processes`, `network`, `archives`, `system`
   - `base_model`: `{student}`
   - `trigger_keywords`: 4–8 lowercase keywords/phrases that match this class of query
   - `programs`: 1–3 relevant Unix command names
3. Include three short sections:
   - `# Domain Knowledge` (key OS/BSD-vs-GNU facts & pitfalls)
   - `# Step-by-Step` (2–4 crisp mechanical steps the student model must follow)
   - `# Feedback / Lessons` (1–3 `Rule:` / `Why:` bullets directly addressing the student's mistake)

Output ONLY the skill wrapped in exact markers:
===BEGIN_FILE: SKILL.md===
---
name: skill_...
description: ...
metadata:
  category: ...
  base_model: {student}
  trigger_keywords: [...]
  programs: [...]
---

# Domain Knowledge
...

# Step-by-Step
...

# Feedback / Lessons
...
===END_FILE: SKILL.md===
"""


def build_revise_prompt(
    prev_skill: str,
    failure: EvalResult,
    regression_failures: list[EvalResult],
    student: str,
    round_num: int,
) -> str:
    reg_text = ""
    if regression_failures:
        lines = [
            f"  - Query `{r.query}` -> `{r.command}` failed: {'; '.join(r.failed_assertions)}"
            for r in regression_failures
        ]
        reg_text = (
            "\nAdditionally, the skill caused REGRESSIONS on previously passing queries:\n"
            + "\n".join(lines)
            + "\n"
        )

    return f"""Ralph Loop Round {round_num} revision for Student model `{student}`.

Your previous `SKILL.md` did NOT pass validation on `{student}`:

Previous `SKILL.md`:
```markdown
{prev_skill.strip()}
```

Latest Student result on target query `{failure.query}`:
- Passed target query: {failure.passed}
- Chosen programs: {failure.chosen_programs or ["(none)"]}
- Student command: `{failure.command or "(none — raised error)"}`
- Failure details:
{chr(10).join(f"  - {r}" for r in failure.failed_assertions) or "  - (none)"}
{reg_text}
Diagnose why `{student}` still failed or regressed:
1. Did `trigger_keywords` / `programs` fail to fire on the target query, or fire too broadly and cause a regression?
2. Was an instruction too abstract or buried? Make the rule shorter, sharper, and unambiguous.
3. Keep the body <= 1100 characters.

Output the complete revised skill wrapped in exact markers:
===BEGIN_FILE: SKILL.md===
...
===END_FILE: SKILL.md===
"""


def _path_part(raw: str, fallback: str) -> str:
    """One safe folder name from teacher output: `../..` must not leave the store."""
    return re.sub(r"[^a-z0-9_]+", "_", raw.lower()).strip("_") or fallback


def _teacher_is_local(teacher: TeacherConfig) -> bool:
    host = urlsplit(teacher.base_url).hostname or ""
    return teacher.backend == "openai" and host in {"localhost", "127.0.0.1", "::1"}


def _copy_skills(src: Path, dst: Path) -> None:
    if not src.is_dir():
        return
    for skill_file in src.rglob("SKILL.md"):
        rel = skill_file.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(skill_file, target)


def ralph_brew_for_case(
    case: dict,
    baseline_failure: EvalResult,
    passing_cases: list[dict],
    student: str,
    base_url: str,
    api_key: str | None,
    teacher: TeacherConfig,
    store_dir: Path,
    ralph_rounds: int,
    check_regressions: bool,
    run_log_dir: Path,
    judge_hint: str = "",
    use_teacher_judge: bool = False,
) -> tuple[bool, Path | None, str]:
    """Run Teacher brew + up to `ralph_rounds` Student validation/revision cycles."""
    env_str = environment()
    refs = []
    for prog in baseline_failure.chosen_programs:
        ref = reference(prog, baseline_failure.query)
        if ref:
            refs.append(f"### {prog}\n{ref[:1000]}")
    ref_text = "\n\n".join(refs)

    slug = re.sub(r"[^a-z0-9]+", "_", baseline_failure.query.lower()).strip("_")[:36]
    # show the teacher the skills the student already had, so it revises one
    # in place instead of adding a second skill on the same topic
    stored = {s.name: s for s in load_skills(store_dir)} if store_dir.is_dir() else {}
    matched = match_skills(
        baseline_failure.query, baseline_failure.chosen_programs, list(stored.values())
    )
    existing_text = "\n\n".join(
        Path(s.source).read_text(encoding="utf-8") for s in matched
    )
    prompt = build_brew_prompt(
        baseline_failure, student, env_str, ref_text, existing_text
    )
    print(f"  [teacher:{teacher.model}] brewing initial SKILL.md...", flush=True)
    teacher_out = call_teacher(prompt, teacher)
    (run_log_dir / f"{slug}_round0_teacher.txt").write_text(
        teacher_out, encoding="utf-8"
    )
    skill_md = extract_skill_md(teacher_out)

    for r in range(1, ralph_rounds + 1):
        parsed = parse_skill(skill_md, fallback_name=f"skill_{slug}")
        skill_rel = Path(
            _path_part(parsed.category, "general"),
            _path_part(parsed.name, f"skill_{slug}"),
        )
        if parsed.name in stored:  # a revision replaces the old file, whatever category
            skill_rel = Path(stored[parsed.name].source).parent.relative_to(store_dir)
        with tempfile.TemporaryDirectory(prefix="upskill_ralph_") as tmp:
            cand_root = Path(tmp)
            _copy_skills(store_dir, cand_root)
            cand_dir = cand_root / skill_rel
            cand_dir.mkdir(parents=True, exist_ok=True)
            (cand_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

            print(
                f"  [ralph {r}/{ralph_rounds}] validating `{parsed.name}` on `{student}`...",
                flush=True,
            )
            res = evaluate_case(
                case,
                student=student,
                base_url=base_url,
                api_key=api_key,
                skills_dir=cand_root,
                use_skills=True,
            )
            if res.passed and use_teacher_judge:
                ok_judge, judge_reason = teacher_verify_command(
                    res.query, res.command, env_str, judge_hint, teacher
                )
                if not ok_judge:
                    res.passed = False
                    res.failed_assertions.append(judge_reason)

            reg_failures: list[EvalResult] = []
            if res.passed and check_regressions and passing_cases:
                cand_skills = [parsed]
                for pcase in passing_cases:
                    pquery = pcase["vars"]["query"]
                    if match_skills(pquery, [], cand_skills, max_skills=1):
                        pres = evaluate_case(
                            pcase,
                            student=student,
                            base_url=base_url,
                            api_key=api_key,
                            skills_dir=cand_root,
                            use_skills=True,
                        )
                        if not pres.passed:
                            reg_failures.append(pres)

            if res.passed and not reg_failures:
                dest_dir = store_dir / skill_rel
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest_file = dest_dir / "SKILL.md"
                dest_file.write_text(skill_md, encoding="utf-8")
                try:
                    shown = dest_file.relative_to(REPO_ROOT)
                except ValueError:
                    shown = dest_file
                print(
                    f"  [PASS round {r}] `{res.command}` -> saved {shown}",
                    flush=True,
                )
                return True, dest_file, res.command

            why = (
                f"regressions={len(reg_failures)}"
                if res.passed
                else "; ".join(res.failed_assertions)
            )
            print(f"  [FAIL round {r}] `{res.command}` ({why})", flush=True)

            if r < ralph_rounds:
                rev_prompt = build_revise_prompt(
                    skill_md, res, reg_failures, student, r + 1
                )
                print(f"  [teacher:{teacher.model}] revising SKILL.md...", flush=True)
                teacher_out = call_teacher(rev_prompt, teacher)
                (run_log_dir / f"{slug}_round{r}_teacher.txt").write_text(
                    teacher_out, encoding="utf-8"
                )
                skill_md = extract_skill_md(teacher_out)

    return False, None, ""


def load_failures_log(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except ValueError:
            continue
    return records


def save_failures_log(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(r) + "\n" for r in records)
    path.write_text(content, encoding="utf-8")


def run_from_failures(
    args: argparse.Namespace,
    student: str,
    base_url: str,
    api_key: str | None,
    teacher: TeacherConfig,
    store_dir: Path,
    run_log_dir: Path,
) -> int:
    """Interactively review, sanitize, and brew skills from failures.jsonl."""
    failures_path = args.failures
    records = load_failures_log(failures_path)
    if args.yes and not _teacher_is_local(teacher):
        # failures.jsonl holds real queries, commands and paths from this machine
        print(
            f"--yes sends failures unreviewed; refused for a non-local teacher "
            f"({teacher.backend}). Review them one by one, or use a local "
            "--teacher-backend openai.",
            file=sys.stderr,
        )
        return 2
    pending_idxs = [i for i, r in enumerate(records) if not r.get("resolved")]
    if not pending_idxs:
        print(f"No unresolved failures in {failures_path}")
        return 0

    reg_path = TESTS_DIR / "regression.yaml"
    passing_cases = (
        yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        if reg_path.is_file()
        else []
    )
    print(
        f"UpSkill (from failures) | {len(pending_idxs)} pending in {failures_path}\n"
        f"  student={student} ({base_url}) | teacher={teacher.model} ({teacher.backend}) | out={store_dir}"
    )

    brewed = 0
    for n, idx in enumerate(pending_idxs, 1):
        rec = records[idx]
        query = rec.get("query", "")
        command = rec.get("command", "")
        reason = rec.get("reason", "unknown")
        hint = rec.get("note", "")
        print(
            f"\n[{n}/{len(pending_idxs)}] {rec.get('ts', '')} | reason={reason} | model={rec.get('model', '')}\n"
            f"  query:   {query}\n"
            f"  command: {command or '(none)'}"
            + (f"\n  note:    {hint}" if hint else "")
        )

        if args.yes:
            action = "b"
        else:
            action = (
                input(
                    "Action: [b]rew / [e]dit & sanitize / [s]kip / [d]ismiss / [q]uit > "
                )
                .strip()
                .lower()
                or "s"
            )
        if action == "q":
            break
        if action == "s":
            continue
        if action == "d":
            records[idx]["resolved"] = True
            save_failures_log(failures_path, records)
            print("  dismissed.")
            continue
        if action == "e":
            new_q = input(f"  sanitized query [{query}]: ").strip()
            if new_q:
                query = new_q
            new_cmd = input(f"  sanitized failed command [{command}]: ").strip()
            if new_cmd:
                command = new_cmd
            new_hint = input(
                f"  expected behavior / fix hint [{hint or 'none'}]: "
            ).strip()
            if new_hint:
                hint = new_hint
        elif action != "b":
            continue

        failure_lines = [f"failure reason: {reason}"]
        if rec.get("error"):
            failure_lines.append(f"error: {rec['error']}")
        if hint:
            failure_lines.append(f"user hint / expected behavior: {hint}")

        baseline_failure = EvalResult(
            query=query,
            passed=False,
            command=command,
            error=rec.get("error", ""),
            failed_assertions=failure_lines,
            chosen_programs=[],
        )
        ok, path, _ = ralph_brew_for_case(
            case={"vars": {"query": query}, "assert": []},
            baseline_failure=baseline_failure,
            passing_cases=passing_cases,
            student=student,
            base_url=base_url,
            api_key=api_key,
            teacher=teacher,
            store_dir=store_dir,
            ralph_rounds=args.ralph_rounds,
            check_regressions=not args.skip_regression_check,
            run_log_dir=run_log_dir,
            judge_hint=hint,
            use_teacher_judge=True,
        )
        if ok:
            brewed += 1
            records[idx]["resolved"] = True
            records[idx]["skill_path"] = str(path)
            save_failures_log(failures_path, records)

    print(f"\nDone: {brewed} skill(s) validated and saved to {store_dir}")
    return 0


def main(argv: list[str] | None = None) -> int:
    load_configs()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--tests",
        default="regression",
        help="evals/promptfoo/tests/<name>.yaml (default: regression)",
    )
    p.add_argument(
        "--from-failures",
        action="store_true",
        help="Review, sanitize, and brew skills from ~/.config/thetaterm/failures.jsonl",
    )
    p.add_argument(
        "--failures",
        type=Path,
        default=FAILURES_LOG,
        help=f"Path to failures JSONL (default: {FAILURES_LOG})",
    )
    p.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="In --from-failures mode, brew all pending entries without prompting "
        "(local teacher only: entries are sent unreviewed)",
    )
    p.add_argument(
        "--student",
        default=None,
        help="Student model (overrides THETATERM_UPSKILL_STUDENT / THETATERM_MODEL)",
    )
    p.add_argument(
        "--base-url",
        default=None,
        help="OpenAI-compatible endpoint for Student (overrides THETATERM_BASE_URL)",
    )
    p.add_argument(
        "--teacher-backend",
        choices=("auto", "claude", "openrouter", "openai"),
        default=None,
        help="Teacher backend (overrides THETATERM_UPSKILL_TEACHER_BACKEND)",
    )
    p.add_argument(
        "--teacher",
        default=None,
        help="Teacher model id (overrides THETATERM_UPSKILL_TEACHER)",
    )
    p.add_argument(
        "--teacher-base-url",
        default=None,
        help="Teacher endpoint for --teacher-backend openai (overrides THETATERM_UPSKILL_TEACHER_BASE_URL)",
    )
    p.add_argument(
        "--teacher-api-key",
        default=None,
        help="Teacher API key (overrides THETATERM_UPSKILL_TEACHER_API_KEY / OPENROUTER_API_KEY)",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Skill store directory (default: thetaterm/skills for --tests, ~/.config/thetaterm/skills for --from-failures)",
    )
    p.add_argument(
        "--ralph-rounds",
        type=int,
        default=3,
        help="Max Ralph validation/revision rounds per failing task (default: 3)",
    )
    p.add_argument(
        "--max-tasks",
        type=int,
        default=0,
        help="Max failing tasks to brew skills for (0 = all failures)",
    )
    p.add_argument(
        "--eval-only",
        action="store_true",
        help="Only evaluate Student on the test suite without calling Teacher",
    )
    p.add_argument(
        "--no-skills",
        action="store_true",
        help="Evaluate Student with skills disabled (clean baseline)",
    )
    p.add_argument(
        "--skip-regression-check",
        action="store_true",
        help="Skip re-checking overlapping passing queries during Ralph validation",
    )
    args = p.parse_args(argv)

    student, base_url, teacher = resolve_models(args)
    api_key = os.getenv("THETATERM_API_KEY")
    store_dir = args.out or (
        user_skills_dir() if args.from_failures else DEFAULT_SKILLS_OUT
    )

    run_id = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    run_log_dir = RUNS_DIR / run_id
    run_log_dir.mkdir(parents=True, exist_ok=True)

    if args.from_failures:
        return run_from_failures(
            args, student, base_url, api_key, teacher, store_dir, run_log_dir
        )

    tests_path = TESTS_DIR / f"{args.tests}.yaml"
    if not tests_path.is_file():
        print(f"error: no such test suite: {tests_path}", file=sys.stderr)
        return 2
    cases = yaml.safe_load(tests_path.read_text(encoding="utf-8"))

    existing_skills = [] if args.no_skills else load_skills(store_dir)
    print(
        f"UpSkill | student={student} | teacher={teacher.model} ({teacher.backend}) | "
        f"suite={args.tests} ({len(cases)} tasks) | skills={len(existing_skills)}"
    )

    t0 = time.time()
    results: list[tuple[dict, EvalResult]] = []
    for i, case in enumerate(cases, 1):
        res = evaluate_case(
            case,
            student=student,
            base_url=base_url,
            api_key=api_key,
            skills_dir=store_dir if store_dir.is_dir() else None,
            use_skills=not args.no_skills,
        )
        results.append((case, res))
        status = "PASS" if res.passed else "FAIL"
        print(
            f"  [{i:2d}/{len(cases)}] {status}  {res.query}  ->  {res.command or res.error}",
            flush=True,
        )

    passed_before = sum(1 for _, r in results if r.passed)
    failures = [(c, r) for c, r in results if not r.passed]
    passing_cases = [c for c, r in results if r.passed]
    print(
        f"\nBaseline: {passed_before}/{len(cases)} passed "
        f"({100.0 * passed_before / max(1, len(cases)):.1f}%) in {time.time() - t0:.1f}s"
    )

    brewed: list[dict] = []
    if not args.eval_only and failures:
        targets = failures[: args.max_tasks] if args.max_tasks else failures
        store_dir.mkdir(parents=True, exist_ok=True)
        for idx, (case, fail) in enumerate(targets, 1):
            print(f"\n=== Brewing {idx}/{len(targets)}: {fail.query} ===", flush=True)
            ok, path, cmd = ralph_brew_for_case(
                case=case,
                baseline_failure=fail,
                passing_cases=passing_cases,
                student=student,
                base_url=base_url,
                api_key=api_key,
                teacher=teacher,
                store_dir=store_dir,
                ralph_rounds=args.ralph_rounds,
                check_regressions=not args.skip_regression_check,
                run_log_dir=run_log_dir,
            )
            brewed.append(
                {
                    "query": fail.query,
                    "validated": ok,
                    "skill_path": str(path) if path else None,
                    "new_command": cmd,
                }
            )
            if ok:
                passing_cases.append(case)

        validated_count = sum(1 for b in brewed if b["validated"])
        print(
            f"\nUpSkill complete: {validated_count}/{len(targets)} skills Ralph-validated "
            f"(projected {passed_before + validated_count}/{len(cases)})"
        )

    summary = {
        "run_id": run_id,
        "student": student,
        "teacher": teacher.model,
        "teacher_backend": teacher.backend,
        "suite": args.tests,
        "baseline_passed": passed_before,
        "total": len(cases),
        "results": [asdict(r) for _, r in results],
        "brewed": brewed,
    }
    (run_log_dir / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"Run log saved to {run_log_dir.relative_to(REPO_ROOT)}/summary.json")
    return (
        0
        if not failures or (not args.eval_only and all(b["validated"] for b in brewed))
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
