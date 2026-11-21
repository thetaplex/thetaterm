import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import typer

from thetaterm import cli
from thetaterm.cli import process_query, unencrypted


def run(monkeypatch, command, yes, answer, log_failures=False):
    """process_query on a fake agent; returns (confirm defaults asked, commands run)."""
    asked, ran = [], []

    def confirm(text, default):
        asked.append(default)
        return answer

    def fake_run(cmd, **kwargs):
        ran.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(typer, "confirm", confirm)
    monkeypatch.setattr(subprocess, "run", fake_run)
    agent = SimpleNamespace(generate=lambda query: command, model="m", env="e")
    process_query(agent, "q", yes, log_failures=log_failures)
    return asked, ran


def test_inside_commands_ask_defaulting_to_yes_unless_y(monkeypatch):
    assert run(monkeypatch, "ls", yes=False, answer=True) == ([True], ["ls"])
    assert run(monkeypatch, "ls", yes=False, answer=False) == ([True], [])
    assert run(monkeypatch, "ls", yes=True, answer=False) == ([], ["ls"])


def test_command_is_shown_exactly_as_it_will_run(monkeypatch, capsys):
    command = "grep [abc] [conceal]x[/conceal] notes.txt [/cyan]"
    run(monkeypatch, command, yes=False, answer=False)
    assert f"$ {command}" in capsys.readouterr().out


def test_ctrl_c_while_running_returns_to_the_prompt(monkeypatch):
    def interrupted(cmd, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(subprocess, "run", interrupted)
    agent = SimpleNamespace(generate=lambda query: "sleep 100")
    assert process_query(agent, "q", yes=True) == 130


def test_outside_commands_always_ask_defaulting_to_no_even_with_y(monkeypatch):
    for yes in (False, True):
        assert run(monkeypatch, "rm -rf /tmp/x", yes, answer=False) == ([False], [])
        assert run(monkeypatch, "cd && ls", yes, answer=True) == (
            [False],
            ["cd && ls"],
        )


def test_bang_runs_the_users_own_command_without_the_model_or_a_question(monkeypatch):
    def no_model(query):
        raise AssertionError("the model was asked")

    asked, ran = [], []
    monkeypatch.setattr(typer, "confirm", lambda *a, **k: asked.append(a) or False)
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda cmd, **k: ran.append(cmd) or SimpleNamespace(returncode=3),
    )
    agent = SimpleNamespace(generate=no_model)
    # outside the current directory too: the user wrote it, so there's nothing to approve
    assert process_query(agent, "! ls ~/Downloads", yes=False) == 3
    assert process_query(agent, "!", yes=False) == 0
    assert ran == ["ls ~/Downloads"] and asked == []


def test_only_a_key_sent_over_plain_http_to_another_host_is_unencrypted():
    assert unencrypted("http://example.com/v1", "k")
    assert not unencrypted("https://example.com/v1", "k")
    assert not unencrypted("http://localhost:11434/v1", "k")
    assert not unencrypted("http://example.com/v1", None)


def test_failure_logging_is_opt_in_and_captures_declines_errors_and_nonzero(
    tmp_path: Path, monkeypatch
):
    log_path = tmp_path / "failures.jsonl"
    monkeypatch.setattr(cli, "FAILURES_LOG", log_path)

    # Off by default: nothing written on decline
    run(monkeypatch, "ls -z", yes=False, answer=False)
    assert not log_path.exists()

    # On: records decline, non-zero exit (not 130), and generate error
    run(monkeypatch, "ls -z", yes=False, answer=False, log_failures=True)

    monkeypatch.setattr(
        subprocess, "run", lambda cmd, **k: SimpleNamespace(returncode=2)
    )
    process_query(
        SimpleNamespace(generate=lambda q: "badcmd", model="m", env="e"),
        "q2",
        yes=True,
        log_failures=True,
    )

    monkeypatch.setattr(
        subprocess, "run", lambda cmd, **k: SimpleNamespace(returncode=130)
    )
    process_query(
        SimpleNamespace(generate=lambda q: "sleep 9", model="m", env="e"),
        "q3",
        yes=True,
        log_failures=True,
    )

    def boom(q):
        raise RuntimeError("no working command")

    process_query(
        SimpleNamespace(generate=boom, model="m", env="e"),
        "q4",
        yes=True,
        log_failures=True,
    )

    rows = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert [r["reason"] for r in rows] == ["declined", "exit:2", "generate_error"]
    assert all(r["resolved"] is False for r in rows)
