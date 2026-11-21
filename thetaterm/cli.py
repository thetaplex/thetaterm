import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from importlib.metadata import version as installed_version
from pathlib import Path
from typing import Annotated
from urllib.parse import urlsplit

import typer
from dotenv import load_dotenv
from rich.console import Console

from thetaterm.agent import SHELL, Agent, outside

# Per-user config only: a .env in the working directory could be a cloned repo's,
# and would get to pick the endpoint our API key is sent to.
CONFIG_DIR = Path(os.getenv("XDG_CONFIG_HOME") or Path.home() / ".config") / "thetaterm"
CONFIG = CONFIG_DIR / ".env"
FAILURES_LOG = CONFIG_DIR / "failures.jsonl"
load_dotenv(CONFIG)

app = typer.Typer()
console = Console()

DEFAULT_MODEL = "gemma4:e4b"
DEFAULT_BASE_URL = "http://localhost:11434/v1"  # Ollama
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def unencrypted(base_url: str, api_key: str | None) -> bool:
    """Whether the API key would cross the network in plain text."""
    url = urlsplit(base_url)
    return bool(api_key) and url.scheme == "http" and url.hostname not in LOCAL_HOSTS


def run(command: str) -> int:
    """Run the command in the user's shell, here. Returns its exit code."""
    try:
        return subprocess.run(  # noqa: S602 running the approved command is the point
            command, shell=True, executable=SHELL, check=False
        ).returncode
    except KeyboardInterrupt:  # Ctrl-C stops the command, not the session
        return 130


def log_failure(
    agent: Agent,
    query: str,
    command: str,
    reason: str,
    error: str = "",
    note: str = "",
) -> None:
    """Append one local failure record to failures.jsonl, for `just upskill-failures`."""
    FAILURES_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "model": agent.model,
        "env": agent.env,
        "query": query,
        "command": command,
        "reason": reason,
        "error": error,
        "note": note,
        "resolved": False,
    }
    with FAILURES_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def process_query(
    agent: Agent,
    query: str,
    yes: bool,
    log_failures: bool = False,
    last: dict[str, str] | None = None,
) -> int:
    """Generate a command for the query, confirm it, run it. Returns its exit code."""
    # `!cmd` is the user's own command, as in a shell: run as typed, no model, no question
    if query.startswith("!"):
        command = query[1:].strip()
        return run(command) if command else 0
    try:
        with console.status("thinking…"):
            command = agent.generate(query)
    except RuntimeError as e:
        console.print(str(e), style="red", markup=False)
        if log_failures:
            log_failure(agent, query, "", "generate_error", error=str(e))
        return 1
    except KeyboardInterrupt:  # back to the > prompt, no traceback
        return 130

    if last is not None:
        last["query"] = query
        last["command"] = command

    # markup=False: `grep [abc] f` must show its brackets, and `[conceal]` mustn't
    # hide words, or the command you approve isn't the one that runs
    console.print(f"$ {command}", style="cyan", markup=False)
    reason = outside(command)
    if reason:
        # never auto-run these, even with -y, and default to no
        console.print(
            f"leaves the current directory: {reason}", style="red", markup=False
        )
    if (reason or not yes) and not typer.confirm("Run it?", default=not reason):
        if log_failures:
            log_failure(agent, query, command, "declined")
        return 0
    rc = run(command)
    if log_failures and rc not in (0, 130):
        log_failure(agent, query, command, f"exit:{rc}")
    return rc


def show_version(value: bool):
    if value:
        print(f"thetaterm {installed_version('thetaterm')}")
        raise typer.Exit()


@app.command()
def tterm(
    query: Annotated[
        str | None,
        typer.Option(
            "--query", "-q", help="The request; without it, start interactive mode"
        ),
    ] = None,
    model: Annotated[
        str, typer.Option("--model", "-m", envvar="THETATERM_MODEL")
    ] = DEFAULT_MODEL,
    yes: Annotated[
        bool, typer.Option("--yes", "-y", help="Run without asking")
    ] = False,
    think: Annotated[
        bool, typer.Option("--think", help="Let the model reason first: slower")
    ] = False,
    log_failures: Annotated[
        bool,
        typer.Option(
            "--log-failures",
            envvar="THETATERM_LOG_FAILURES",
            help="Log declined/failed commands locally to ~/.config/thetaterm/failures.jsonl",
        ),
    ] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            is_eager=True,
            callback=show_version,
            help="Show the installed version and exit",
        ),
    ] = False,
):
    """
    Describe a task in plain words, get a shell command for this system, confirm, run it.
    """
    base_url = os.getenv("THETATERM_BASE_URL") or DEFAULT_BASE_URL
    api_key = os.getenv("THETATERM_API_KEY")
    if unencrypted(base_url, api_key):
        console.print(
            f"[yellow]warning: API key sent unencrypted to {base_url}[/yellow]"
        )
    try:
        agent = Agent(model, base_url, api_key, think)
    except ValueError as e:
        console.print(f"THETATERM_BASE_URL={e}", style="red", markup=False)
        sys.exit(2)
    if query is not None:
        sys.exit(process_query(agent, query, yes, log_failures=log_failures))

    console.print(f"[bold cyan]thetaterm[/bold cyan] · {model} · {agent.env}")
    console.print(
        "[dim]Describe what you want, !command to run one, ?bad [note] to log last command. Ctrl-D to exit.[/dim]"
    )
    last: dict[str, str] = {}
    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            return
        if line.startswith("?bad"):
            if not last:
                console.print("nothing to log yet", style="yellow")
            else:
                note = line[4:].strip()
                log_failure(
                    agent, last["query"], last["command"], "user_marked", note=note
                )
                console.print(f"logged failure to {FAILURES_LOG}", style="dim")
        elif line:
            process_query(agent, line, yes, log_failures=log_failures, last=last)


if __name__ == "__main__":
    app()
