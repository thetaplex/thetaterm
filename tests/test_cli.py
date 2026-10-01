import subprocess
from types import SimpleNamespace

import typer

from thetaterm.cli import process_query


def run(monkeypatch, command, yes, answer):
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
    process_query(SimpleNamespace(generate=lambda query: command), "q", yes)
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
