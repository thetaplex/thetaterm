import asyncio
import json
import subprocess
import sys
from pathlib import Path

import pytest
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import LATEST_PROTOCOL_VERSION

from thetaterm import mcp
from thetaterm.agent import Agent


def call(tool, **arguments):
    """The tool's structured result, as a client gets it."""
    return asyncio.run(mcp.server().call_tool(tool, arguments)).structured_content


def test_all_tools_are_offered_and_marked_read_only():
    tools = asyncio.run(mcp.server().list_tools())
    assert {t.name for t in tools} == {
        "system_info",
        "docs",
        "check",
        "suggest_command",
    }
    assert all(t.annotations.read_only_hint for t in tools)


def test_docs_rejects_options_and_unknown_programs_without_running_man(monkeypatch):
    ran = []
    monkeypatch.setattr(subprocess, "run", lambda args, **kw: ran.append(args))
    for program in ["-Pecho", "/bin/ls", "no-such-program-xyz", "ls; rm"]:
        with pytest.raises(ToolError, match="not an installed program"):
            call("docs", program=program, task="list files")
    assert ran == []


def test_docs_without_a_man_page_or_note_is_an_error(monkeypatch):
    monkeypatch.setattr(mcp, "reference", lambda program, task: "")
    with pytest.raises(ToolError, match="no man page"):
        call("docs", program="ls", task="list files")


def test_check_reports_problem_and_outside_or_none():
    assert call("check", command="ls -l") == {"problem": None, "outside": None}
    assert call("check", command="no-such-program-xyz .")["problem"] == (
        "no-such-program-xyz: command not found"
    )
    assert call("check", command="rm /tmp/x")["outside"] == "absolute path /tmp/x"
    unbalanced = call("check", command="echo 'x")
    assert unbalanced["problem"] and unbalanced["outside"] is None
    assert "null byte" in call("check", command="ls\x00 -l")["problem"]


def test_suggest_command_flags_outside_commands(monkeypatch):
    monkeypatch.setattr(Agent, "generate", lambda self, task: "ls -S .")
    assert call("suggest_command", task="t") == {"command": "ls -S .", "outside": None}
    monkeypatch.setattr(Agent, "generate", lambda self, task: "ls /tmp")
    assert call("suggest_command", task="t")["outside"] == "absolute path /tmp"


def test_suggest_command_turns_model_failures_into_tool_errors(monkeypatch):
    def unreachable(self, task):
        raise RuntimeError("cannot reach http://localhost:11434/v1/chat/completions")

    monkeypatch.setattr(Agent, "generate", unreachable)
    with pytest.raises(ToolError, match="cannot reach"):
        call("suggest_command", task="t")
    monkeypatch.setenv("THETATERM_BASE_URL", "file:///etc/passwd")
    with pytest.raises(ToolError, match="not an http"):
        call("suggest_command", task="t")


def test_installed_script_answers_with_nothing_but_json_on_stdout():
    """A stray print would corrupt the protocol for clients stricter than the SDK's."""
    messages = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": LATEST_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0"},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    ]
    server = subprocess.Popen(  # noqa: S603 our own script
        [Path(sys.executable).with_name("tterm-mcp")],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    for m in messages:
        server.stdin.write(json.dumps(m) + "\n")
    server.stdin.flush()
    # read before closing stdin: at EOF the server stops, maybe before answering
    replies = [json.loads(server.stdout.readline()) for _ in range(2)]
    server.stdin.close()
    assert server.wait(timeout=30) == 0
    assert server.stdout.read() == ""
    assert [r["id"] for r in replies] == [1, 2]
    assert "suggest_command" in {t["name"] for t in replies[1]["result"]["tools"]}
