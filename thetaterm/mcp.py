"""MCP server: thetaterm's knowledge of this system, for other agents (ADR 0008).

No tool runs a command. The calling agent runs what it decides to, through its
own shell and permission prompts.
"""

import os
import re
import shutil
import sys

from thetaterm.agent import Agent, environment, outside, problem, reference
from thetaterm.cli import DEFAULT_BASE_URL, DEFAULT_MODEL  # importing loads CONFIG

# a name that starts with - would reach man as an option, and `man -P` runs a pager
PROGRAM = re.compile(r"[A-Za-z0-9][\w.+-]*")


def server():
    """The MCP server with thetaterm's tools. Needs the mcp extra."""
    from mcp.server.mcpserver import MCPServer
    from mcp.server.mcpserver.exceptions import ToolError
    from mcp.types import ToolAnnotations

    app = MCPServer(
        "thetaterm",
        instructions="Shell commands that are correct for this machine: its OS, "
        "whether its tools are GNU, BSD or BusyBox, and their installed man pages. "
        "Nothing here runs a command.",
    )
    read_only = ToolAnnotations(read_only_hint=True)

    @app.tool(annotations=read_only)
    def system_info() -> str:
        """The OS, whether its tools are GNU, BSD or BusyBox, and the user's shell."""
        return environment()

    @app.tool(annotations=read_only)
    def docs(program: str, task: str) -> str:
        """thetaterm's note on the installed program, then the parts of its man page
        relevant to the task. Read it before using an option you're unsure of here."""
        if not PROGRAM.fullmatch(program) or not shutil.which(program):
            raise ToolError(f"{program}: not an installed program")
        return reference(program, task)

    @app.tool(annotations=read_only)
    def check(command: str) -> dict[str, str | None]:
        """Check a shell command without running it. `problem`: why it would fail
        (bad syntax, a program not installed). `outside`: why it reaches outside the
        current directory (sudo, ~, an absolute path, ..). null means none found;
        it doesn't mean the command is safe."""
        return {"problem": problem(command), "outside": outside(command)}

    @app.tool(annotations=read_only)
    def suggest_command(task: str, think: bool = False) -> dict[str, str | None]:
        """Write one shell command for the task, for this system, using a small model
        that reads the installed man pages. Takes seconds to a minute; a capable agent
        may do better with `docs` and `check`. `outside` is as in `check`. Doesn't
        run the command."""
        try:
            agent = Agent(
                os.getenv("THETATERM_MODEL") or DEFAULT_MODEL,
                os.getenv("THETATERM_BASE_URL") or DEFAULT_BASE_URL,
                os.getenv("THETATERM_API_KEY"),
                think,
            )
            command = agent.generate(task)
        except (RuntimeError, ValueError) as e:
            raise ToolError(str(e)) from None
        return {"command": command, "outside": outside(command)}

    return app


def main():
    try:
        app = server()
    except ModuleNotFoundError as e:
        if not (e.name or "").startswith("mcp"):
            raise
        # stdout belongs to the protocol
        print(
            "install the MCP extra: uv tool install 'thetaterm[mcp]'", file=sys.stderr
        )
        sys.exit(1)
    app.run()  # stdio
